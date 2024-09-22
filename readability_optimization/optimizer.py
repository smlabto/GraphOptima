"""
This script is the main optimizer of the GraphOptima. The idea is to optimize the combined_objective_function,
which is a function that takes n layout parameters and output a list of readability metrics.
In this function, we defined two optimization methods to explore all possible layouts of the given layout algorithm:

1. by using a scalarization approach, we combined the readability metrics into a single weighted value and optimize
it. By trying all weighting schema, we can explore the Pareto front of the readability metrics.

2. by using a multi-objective optimization algorithm (NSGA2), we can explore the Pareto front of the readability metrics
directly.

The way this function incorporated into the rest of the system is by producing a .params file, which contains the
parameters of the layout algorithm. The .params file is then processed by the cuGraph_to_pos_df.py script, which
generates the layout that can be further process by the layout evaluator
"""

from optimization_database import *
from utils import *
from scipy.optimize import differential_evolution
import numpy as np
import optimization_database
import reward
from multiprocessing import Pool
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.problem import StarmapParallelization
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from verify_optimized_params import verify_optimized_params
import json
import external_api
import combined_objective_func
import utils
import time
import shutil

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

MAX_VAL = 999999

# Load configuration from JSON file
GRAPH_FILE = CONFIG["layout_generator"]["GRAPHML_FILE"]
GRAPH_FILE_NAME = GRAPH_FILE.split("/")[-1]
OPTIMIZATION_METADATA = CONFIG["optimizer"]["METADATA"]
ALGORITHM_BEING_OPTIMIZED = OPTIMIZATION_METADATA["algorithm_being_optimized"]
OPTIMIZATION_ALGORITHM_USED = OPTIMIZATION_METADATA["optimization_algorithm_used"]
READABILITY_CALCULATION_METHOD = OPTIMIZATION_METADATA["readability_calculation_method"]
EMAIL_NOTIFICATION_SETTING = CONFIG["optimizer"]["email_notification"]

DIFFERENTIAL_OPTIMIZATION_PARAMS = CONFIG["optimizer"][
    "differential_evolution_optimization_params"
]
SINGLE_OBJECTIVE_FUNC = CONFIG["optimizer"]["SINGLE_OBJECTIVE_FUNC"]

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

# scale, gravity, max_iterations
BOUNDS = CONFIG["optimizer"]["BOUNDS"]
INITIAL_GUESS = CONFIG["optimizer"]["INITIAL_GUESS"]

NUM_OF_DESIGN_PARAMS = CONFIG["optimizer"]["NUM_OF_DESIGN_PARAMS"]
NUM_OF_OBJECTIVE_PARAMS = CONFIG["optimizer"]["NUM_OF_OBJECTIVE_PARAMS"]

# Lower bounds for the variables (xl)
LOWER_BOUNDS = np.array([bound[0] for bound in BOUNDS])

# Upper bounds for the variables (xu)
UPPER_BOUNDS = np.array([bound[1] for bound in BOUNDS])

WEIGHT_LIST = [
    [reward.CROSSLESSNESS_WEIGHT, reward.NORMALIZED_CV_WEIGHT, reward.MIN_ANGLE_WEIGHT]
]

if CONFIG["optimizer"]["SCALARIZATION"]:
    WEIGHT_LIST = generate_n_objective_weights(
        n=3, granularity=CONFIG["optimizer"]["SCALARIZATION_GRANULARITY"]
    )


class MyProblem(ElementwiseProblem):
    def __init__(self, **kwargs):
        super().__init__(
            n_var=NUM_OF_DESIGN_PARAMS,
            n_obj=NUM_OF_OBJECTIVE_PARAMS,
            xl=LOWER_BOUNDS,
            xu=UPPER_BOUNDS,
            elementwise_evaluation=True,
            **kwargs,
        )

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = combined_objective_func.combined_objective_func(x)


def get_problem_and_pool():
    pool = None
    # Create a pool of worker processes only when NSGA2 is true
    if CONFIG["optimizer"]["NSGA2"]:
        pool = Pool(
            CONFIG["optimizer"]["multi_objective_optimization_params"]["workers"]
        )
        runner = StarmapParallelization(pool.starmap)
        # Create the problem with the created pool
        problem = MyProblem(elementwise_runner=runner)
    else:
        # Create the problem without a pool
        problem = MyProblem()

    return problem, pool


# Set MULTI_OBJECTIVE_OPTIMIZATION_PROBLEM and pool
MULTI_OBJECTIVE_OPTIMIZATION_PROBLEM, pool = get_problem_and_pool()


def optimize_global_cuGraph():
    global_optimization_result = differential_evolution(
        func=combined_objective_func.combined_objective_func,
        bounds=BOUNDS,
        strategy=DIFFERENTIAL_OPTIMIZATION_PARAMS["strategy"],
        maxiter=int(OPTIMIZATION_BUDGET),
        disp=DIFFERENTIAL_OPTIMIZATION_PARAMS["disp"],
        x0=INITIAL_GUESS,
        seed=DIFFERENTIAL_OPTIMIZATION_PARAMS["seed"],
        workers=DIFFERENTIAL_OPTIMIZATION_PARAMS["workers"],
    )
    return global_optimization_result


def set_substitution_by_finding_similar_tested_param(substitution: bool):
    global SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM
    SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM = substitution
    combined_objective_func.SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM = substitution


def set_substitution_by_finding_exact_tested_iteration_num(substitution: bool):
    global SUBSTITUTION_BY_FINDING_EXACT_TESTED_ITERATION_NUM
    SUBSTITUTION_BY_FINDING_EXACT_TESTED_ITERATION_NUM = substitution
    combined_objective_func.SUBSTITUTION_BY_FINDING_EXACT_TESTED_ITERATION_NUM = (
        substitution
    )


def main():
    # reset the substitution
    set_substitution_by_finding_similar_tested_param(True)

    if EMAIL_NOTIFICATION_SETTING["send_email"]:
        external_api.write_instruction(
            subject=EMAIL_NOTIFICATION_SETTING["start_optimization_subject"],
            message=EMAIL_NOTIFICATION_SETTING["start_optimization_email_body"],
            instruction_type="email_instruction",
        )
    result = optimize_global_cuGraph()

    # set the substitution to False during the verification
    set_substitution_by_finding_similar_tested_param(False)

    if EMAIL_NOTIFICATION_SETTING["send_email"]:
        external_api.write_instruction(
            subject=EMAIL_NOTIFICATION_SETTING["end_optimization_subject"],
            message=EMAIL_NOTIFICATION_SETTING["end_optimization_email_body"],
            instruction_type="email_instruction",
        )
    return result


def explore_pareto_front_with_weighted_sum_scalarization(weights_list: list):
    global METADATA

    for weights in weights_list:
        # Check if the db file for these weights already exists
        filename = f"database/database_{weights[0]}_{weights[1]}_{weights[2]}.db"
        if os.path.exists(filename):
            if CONFIG["optimizer"]["BREAKPOINT_SKIP"]:
                print(
                    f"{utils.get_timestamp()}: Skipping weights {weights} as they have already been tested."
                )
                continue

            else:
                # copy the database/database_{weights[0]}_{weights[1]}_{weights[2]}.db to old_database.db
                # verify the tested results by rerun the optimization under the same weighting schema
                shutil.copy(filename, optimization_database.DATABASE_PATH)
                print(
                    f"\n\n{utils.get_timestamp()}: Previous optimization with weights {weights} found. Verifying the "
                    f"results with substitution.\n\n"
                )

        combined_objective_func.CORE_DUMP = 0
        combined_objective_func.EVAL_COUNTER = 0
        reward.update_weights(
            crosslessness_weight=weights[0],
            normalized_cv_weight=weights[1],
            min_angle_weight=weights[2],
        )
        METADATA["readability_calculation_weight_list"] = [
            reward.CROSSLESSNESS_WEIGHT,
            reward.NUM_EDGE_CROSSINGS_WEIGHT,
            reward.EDGE_LENGTH_CV_WEIGHT,
            reward.NORMALIZED_CV_WEIGHT,
            reward.MIN_ANGLE_WEIGHT,
            reward.SHAPE_DELAUNAY_WEIGHT,
            reward.SHAPE_GABRIEL_WEIGHT,
        ]
        combined_objective_func.METADATA = METADATA
        print(
            f"\n\n{utils.get_timestamp()}: Running optimization with weights: {weights}\n\n"
        )
        time.sleep(5)

        result = main()

        # from the result, store the optimal params and the optimal value
        optimal_params = result.x
        optimal_readability = result.fun

        # display the result
        print(f"{utils.get_timestamp()}: result from the optimization: {str(result)}")
        print(f"{utils.get_timestamp()}: optimal_params: {str(optimal_params)}")
        print(f"{utils.get_timestamp()}:optimal_readability {str(optimal_readability)}")

        write_optimization_result(
            optimal_params=optimal_params,
            optimal_readability=optimal_readability,
            weights=weights,
        )

        verify_optimized_params(
            initial_guess_params=INITIAL_GUESS,
            func=combined_objective_func.combined_objective_func,
            best_params=optimal_params,
            best_readability=optimal_readability,
            weight1=weights[0],
            weight2=weights[1],
            weight3=weights[2],
        )

        optimization_database.close_connection(combined_objective_func.CONN)

        copy_to_weighted_database(weights)

        remove_database()

        remove_core_dump_files()

        remove_readability_score_results()

        remove_lock_files()

        rename_the_optimization_database_to_weighted_database(weights)

        combined_objective_func.CONN = optimization_database.open_optimized_connection(
            optimization_database.DATABASE_PATH
        )


def multi_objective_optimize_with_NSGA2(problem=MULTI_OBJECTIVE_OPTIMIZATION_PROBLEM):
    if EMAIL_NOTIFICATION_SETTING["send_email"]:
        external_api.write_instruction(
            subject="Optimization starts!",
            message="A multi objective NSGA2 optimization has been started on Cedar.",
            instruction_type="email_instruction",
        )

    set_substitution_by_finding_similar_tested_param(False)
    set_substitution_by_finding_exact_tested_iteration_num(True)

    global SINGLE_OBJECTIVE_FUNC
    SINGLE_OBJECTIVE_FUNC = False

    algorithm = NSGA2(
        pop_size=CONFIG["optimizer"]["multi_objective_optimization_params"][
            "population_size"
        ],
        eliminate_duplicates=True,
    )

    res = minimize(
        problem=problem,
        algorithm=algorithm,
        termination=(
            "n_gen",
            CONFIG["optimizer"]["multi_objective_optimization_params"]["generations"],
        ),
        verbose=True,
        seed=CONFIG["optimizer"]["multi_objective_optimization_params"]["seed"],
    )

    if EMAIL_NOTIFICATION_SETTING["send_email"]:
        external_api.write_instruction(
            subject="Optimization finished!",
            message="A multi objective NSGA2 optimization has been finished on Cedar.",
            instruction_type="email_instruction",
        )

    # Plotting 3D Pareto front
    plot_pareto_front(problem, res)

    # Plotting convergence
    plot_convergence([res], ["NSGA2"])

    global pool
    if pool is not None:
        pool.close()
        pool.join()

    return res


if __name__ == "__main__":
    remove_optimization_completed_indicator_file()
    if CONFIG["optimizer"]["SCALARIZATION"]:
        explore_pareto_front_with_weighted_sum_scalarization(weights_list=WEIGHT_LIST)
    if CONFIG["optimizer"]["NSGA2"]:
        multi_objective_optimize_with_NSGA2()
    write_optimization_completed_indicator_file()
