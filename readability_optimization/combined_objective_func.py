"""
This file defined the key logic of taking n layout params and returns a list of readability measurements
"""

from utils import *
import reward
import optimization_database
import json
import external_api
import pos_to_readability_score
import traceback
import time

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

print("try to establish connection")
CONN = optimization_database.open_optimized_connection(
    database_path=CONFIG["optimization_database"]["DATABASE_PATH"]
)
GLOBAL_CONN = optimization_database.open_optimized_connection(
    database_path=CONFIG["optimization_database"]["GLOBAL_DATABASE_PATH"]
)

print("connection established")

MAX_VAL = 999999

# Load configuration from JSON file
MAX_ALLOWABLE_ERROR_RETRY = CONFIG["optimizer"]["MAX_ALLOWABLE_ERROR_RETRY"]
GRAPH_FILE = CONFIG["layout_generator"]["GRAPHML_FILE"]
GRAPH_FILE_NAME = GRAPH_FILE.split("/")[-1]
OPTIMIZATION_METADATA = CONFIG["optimizer"]["METADATA"]
ALGORITHM_BEING_OPTIMIZED = OPTIMIZATION_METADATA["algorithm_being_optimized"]
OPTIMIZATION_ALGORITHM_USED = OPTIMIZATION_METADATA["optimization_algorithm_used"]
READABILITY_CALCULATION_METHOD = OPTIMIZATION_METADATA["readability_calculation_method"]
SINGLE_OBJECTIVE_FUNC = CONFIG["optimizer"]["SINGLE_OBJECTIVE_FUNC"]

EVAL_COUNTER = 0
CORE_DUMP = 0

DATABASE = optimization_database.read_database_file_to_object(conn=CONN)
GLOBAL_DATABASE = optimization_database.read_database_file_to_object(conn=GLOBAL_CONN)

METADATA = make_new_metadata(
    graph_file_name=GRAPH_FILE_NAME,
    algorithm_being_optimized=ALGORITHM_BEING_OPTIMIZED,
    optimization_algorithm_used=OPTIMIZATION_ALGORITHM_USED,
    readability_calculation_method=READABILITY_CALCULATION_METHOD,
    readability_calculation_weight_list=[
        reward.CROSSLESSNESS_WEIGHT,
        reward.NUM_EDGE_CROSSINGS_WEIGHT,
        reward.EDGE_LENGTH_CV_WEIGHT,
        reward.NORMALIZED_CV_WEIGHT,
        reward.MIN_ANGLE_WEIGHT,
        reward.SHAPE_DELAUNAY_WEIGHT,
        reward.SHAPE_GABRIEL_WEIGHT,
    ],
)

OPTIMIZATION_BUDGET = CONFIG["optimizer"]["OPTIMIZATION_BUDGET"]
SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM = CONFIG["optimizer"][
    "SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM"
]
SUBSTITUTION_BY_FINDING_EXACT_TESTED_ITERATION_NUM = CONFIG["optimizer"][
    "SUBSTITUTION_BY_FINDING_EXACT_TESTED_ITERATION_NUM"
]
DATABASE_CACHING_INTERVAL = CONFIG["optimizer"]["DATABASE_CACHING_INTERVAL"]

# scale, gravity, max_iterations
BOUNDS = CONFIG["optimizer"]["BOUNDS"]
INITIAL_GUESS = CONFIG["optimizer"]["INITIAL_GUESS"]

NUM_OF_DESIGN_PARAMS = CONFIG["optimizer"]["NUM_OF_DESIGN_PARAMS"]
NUM_OF_OBJECTIVE_PARAMS = CONFIG["optimizer"]["NUM_OF_OBJECTIVE_PARAMS"]


def combined_objective_func(params: list):
    global EVAL_COUNTER
    global DATABASE
    global GLOBAL_DATABASE

    layout_id = generate_layout_id()

    global CORE_DUMP

    readability = None
    multi_objective_results = None

    if not CORE_DUMP:
        print("\n\n\n")
        print("eval " + str(EVAL_COUNTER))
        print("Params: " + str(params))
        print("layout id:" + layout_id)
        print(
            "Weights: "
            + str(
                [
                    reward.CROSSLESSNESS_WEIGHT,
                    reward.NUM_EDGE_CROSSINGS_WEIGHT,
                    reward.EDGE_LENGTH_CV_WEIGHT,
                    reward.NORMALIZED_CV_WEIGHT,
                    reward.MIN_ANGLE_WEIGHT,
                    reward.SHAPE_DELAUNAY_WEIGHT,
                    reward.SHAPE_GABRIEL_WEIGHT,
                ]
            )
        )
        # check if the params is already in the database
        if SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM:
            query_start_time = time.time()
            if (
                DATABASE_CACHING_INTERVAL == 0
                or EVAL_COUNTER % DATABASE_CACHING_INTERVAL == 0
            ):
                DATABASE = optimization_database.read_database_file_to_object(conn=CONN)
                GLOBAL_DATABASE = optimization_database.read_database_file_to_object(
                    conn=GLOBAL_CONN
                )
            query_end_time = time.time()
            cosine_start_time = time.time()
            closest_params, closest_glam_results, cosine_similarity = (
                optimization_database.find_the_closest_param_using_cosine_similarity(
                    params=params, global_database_object=GLOBAL_DATABASE
                )
            )
            cosine_end_time = time.time()
            if closest_glam_results:
                # if a close enough params is found, print the close enough params and its cosine_similarity
                print(
                    "Close enough previous params found: "
                    + str(closest_params)
                    + " with cosine similarity: "
                    + str(cosine_similarity)
                    + " and error within "
                    + str(CONFIG["optimization_database"]["MAX_ERROR_PERCENTAGE"] * 100)
                    + "%"
                )
                if CONFIG["optimization_database"]["LOG_DATABASE_READ_TIME"]:
                    print(
                        "Database read time: " + str(query_end_time - query_start_time)
                    )
                    print(
                        "Cosine similarity calculation time: "
                        + str(cosine_end_time - cosine_start_time)
                    )
                EVAL_COUNTER += 1

                print("GLAM results: " + str(closest_glam_results))

                if SINGLE_OBJECTIVE_FUNC:
                    # calculate the closest_readability using the current weight
                    closest_readability = reward.minimized_total_readability_reward(
                        current_glam_results=closest_glam_results, echo=True
                    )
                    print("readability: " + str(closest_readability))
                    return closest_readability

                if not SINGLE_OBJECTIVE_FUNC:
                    fixed_results = reward.fix_negative_val_to_sci_notation_from_GLAM(
                        current_glam_results=closest_glam_results
                    )

                    crosslessness = fixed_results[0]
                    num_edge_crossings = fixed_results[1]
                    edge_length_cv = fixed_results[2]
                    normalized_cv = fixed_results[3]
                    min_angle = fixed_results[4]
                    shape_delaunay = fixed_results[5]
                    shape_gabriel = fixed_results[6]

                    multi_objective_results = [
                        1 - crosslessness,
                        normalized_cv,
                        1 - min_angle,
                    ]
                    # if multi_objective_results isn't just 3 numbers, raise error
                    if len(multi_objective_results) != 3:
                        raise ValueError(
                            "multi_objective_results is not just 3 numbers"
                        )

                    print("multi_objective_results: " + str(multi_objective_results))
                    return multi_objective_results

    """
    error prevention strategy:
    for the same layout, retry MAX_ALLOWED times
    if still error, returning the -inf reward 
    """
    error_counter = 0
    while error_counter <= MAX_ALLOWABLE_ERROR_RETRY:
        try:
            if error_counter:
                print("# error encounter for this layout: " + str(error_counter))

            make_params_file(params=params, uuid=layout_id)
            break
        except Exception as e:
            print(str(e))

            error_counter += 1

    if error_counter > MAX_ALLOWABLE_ERROR_RETRY:
        external_api.write_instruction(
            subject="Error encountered too many times!",
            message="Using "
            + str(params)
            + "has raise too many times ( "
            + str(MAX_ALLOWABLE_ERROR_RETRY)
            + " times ) of error, returning maximum penalty.",
            instruction_type="email_instruction",
        )
        print(
            str(params)
            + "has raise too many times of error, returning maximum penalty."
        )

        # returning maximum penalty as the params raise too many times of error
        results = [MAX_VAL, MAX_VAL, MAX_VAL, MAX_VAL, MAX_VAL, MAX_VAL]

    else:
        print("Layout generation order is send, gathering the readability result...")
        results = pos_to_readability_score.retrieve_readability_score_and_cleanup(
            uuid=layout_id, cleanup=True, echo=True
        )
    try:
        if SINGLE_OBJECTIVE_FUNC:
            readability = reward.minimized_total_readability_reward(
                current_glam_results=results, echo=True
            )
        else:
            fixed_results = reward.fix_negative_val_to_sci_notation_from_GLAM(
                current_glam_results=results
            )

            crosslessness = fixed_results[0]
            num_edge_crossings = fixed_results[1]
            edge_length_cv = fixed_results[2]
            normalized_cv = fixed_results[3]
            min_angle = fixed_results[4]
            shape_delaunay = fixed_results[5]
            shape_gabriel = fixed_results[6]

            multi_objective_results = [1 - crosslessness, normalized_cv, 1 - min_angle]
            # if multi_objective_results isn't just 3 numbers, raise error
            if len(multi_objective_results) != 3:
                raise ValueError("multi_objective_results is not just 3 numbers")

    except Exception as e:
        traceback.print_exc()
        EVAL_COUNTER = EVAL_COUNTER - 1
        CORE_DUMP += 1
        print("Core Dumped, recursively recalculate the readability ...")
        if SINGLE_OBJECTIVE_FUNC:
            readability = combined_objective_func(params)
        else:
            multi_objective_results = combined_objective_func(params)
        CORE_DUMP -= 1

    if not CORE_DUMP:
        EVAL_COUNTER += 1
        try:
            if SINGLE_OBJECTIVE_FUNC:
                optimization_database.log_and_save(
                    iteration=EVAL_COUNTER,
                    params=params,
                    glam_results=results,
                    readability=readability,
                    metadata=METADATA,
                    conn=CONN,
                    echo=True,
                )
                optimization_database.log_and_save(
                    iteration=EVAL_COUNTER,
                    params=params,
                    glam_results=results,
                    readability=readability,
                    metadata=METADATA,
                    conn=GLOBAL_CONN,
                    echo=True,
                )
            else:
                optimization_database.log_and_save(
                    iteration=EVAL_COUNTER,
                    params=params,
                    glam_results=results,
                    readability=multi_objective_results,
                    metadata=METADATA,
                    conn=CONN,
                    echo=True,
                )
                optimization_database.log_and_save(
                    iteration=EVAL_COUNTER,
                    params=params,
                    glam_results=results,
                    readability=multi_objective_results,
                    metadata=METADATA,
                    conn=GLOBAL_CONN,
                    echo=True,
                )
        except Exception as e:
            # display the error
            print("Error when saving to the database: " + str(e))
            time.sleep(5)

    # try to remove any core.* file exist under the current directory
    try:
        # if core.* file exists, remove it
        if os.path.isfile("core.*"):
            os.system("rm core.*")
    except Exception as e:
        # this means no core file exists, which is good.
        pass
    finally:
        if SINGLE_OBJECTIVE_FUNC:
            print("readability: " + str(readability))
            return readability
        else:
            print("multi_objective_results: " + str(multi_objective_results))
            return multi_objective_results
