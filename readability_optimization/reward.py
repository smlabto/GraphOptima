import json
from decimal import Decimal, InvalidOperation

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

# Here are only default values, the weights of objectives being optimized will be updated to achieve scalarization. Here
# just need to make sure the unchanged weights are desirable, i.e. 0
CROSSLESSNESS_WEIGHT = CONFIG["reward"]["CROSSLESSNESS_WEIGHT"]
NUM_EDGE_CROSSINGS_WEIGHT = CONFIG["reward"]["NUM_EDGE_CROSSINGS_WEIGHT"]
EDGE_LENGTH_CV_WEIGHT = CONFIG["reward"]["EDGE_LENGTH_CV_WEIGHT"]
NORMALIZED_CV_WEIGHT = CONFIG["reward"]["NORMALIZED_CV_WEIGHT"]
MIN_ANGLE_WEIGHT = CONFIG["reward"]["MIN_ANGLE_WEIGHT"]
SHAPE_DELAUNAY_WEIGHT = CONFIG["reward"]["SHAPE_DELAUNAY_WEIGHT"]
SHAPE_GABRIEL_WEIGHT = CONFIG["reward"]["SHAPE_GABRIEL_WEIGHT"]


def update_weights(
    crosslessness_weight=CROSSLESSNESS_WEIGHT,
    num_edge_crossing_weight=NUM_EDGE_CROSSINGS_WEIGHT,
    normalized_cv_weight=NORMALIZED_CV_WEIGHT,
    min_angle_weight=MIN_ANGLE_WEIGHT,
    shape_delaunay_weight=SHAPE_DELAUNAY_WEIGHT,
    shape_gabriel_weight=SHAPE_GABRIEL_WEIGHT,
):
    global CROSSLESSNESS_WEIGHT
    global NUM_EDGE_CROSSINGS_WEIGHT
    global NORMALIZED_CV_WEIGHT
    global MIN_ANGLE_WEIGHT
    global SHAPE_DELAUNAY_WEIGHT
    global SHAPE_GABRIEL_WEIGHT
    CROSSLESSNESS_WEIGHT = crosslessness_weight
    NUM_EDGE_CROSSINGS_WEIGHT = num_edge_crossing_weight
    NORMALIZED_CV_WEIGHT = normalized_cv_weight
    MIN_ANGLE_WEIGHT = min_angle_weight
    SHAPE_DELAUNAY_WEIGHT = shape_delaunay_weight
    SHAPE_GABRIEL_WEIGHT = shape_gabriel_weight


def fix_negative_val_to_sci_notation_from_GLAM(current_glam_results: list):
    negative_index = []
    # 7 is the number of metrics returned by GLAM
    if 7 != len(current_glam_results):
        # 1. scan array to find the negative val
        # 2. check if the vals are after min angle
        # 3. concat val to previous val to make it sci notation
        for i in range(len(current_glam_results)):
            try:
                current_val = Decimal(current_glam_results[i])
                if current_val < 0:
                    if i > 5:
                        old_val = Decimal(current_glam_results[i - 1])
                        current_glam_results[i - 1] = old_val * (Decimal('10') ** current_val)
                        negative_index.append(i)
            except InvalidOperation:
                raise ValueError("Invalid value in the array" + str(current_glam_results[i]))

    current_copy = []
    for i in range(len(current_glam_results)):
        if i in negative_index:
            continue
        current_copy.append(float(current_glam_results[i]))
    return current_copy


def minimized_total_readability_reward(current_glam_results: list, echo: bool = False):
    current_glam_results = fix_negative_val_to_sci_notation_from_GLAM(
        current_glam_results
    )

    if echo:
        print("Current readability metrics: " + str(current_glam_results))

    # the current here is a glam readability metrics array so the naming is hardcoded
    crosslessness = current_glam_results[0]
    num_edge_crossings = current_glam_results[1]
    edge_length_cv = current_glam_results[2]
    normalized_cv = current_glam_results[3]
    min_angle = current_glam_results[4]
    shape_delaunay = current_glam_results[5]
    shape_gabriel = current_glam_results[6]

    # reward_val = CROSSLESSNESS_WEIGHT * (1 - crosslessness) + NORMALIZED_CV_WEIGHT * normalized_cv +
    # MIN_ANGLE_WEIGHT * (1 - min_angle)

    # todo: load it from config.js using eval?
    reward_val = (
        CROSSLESSNESS_WEIGHT * (1 - crosslessness)
        + NORMALIZED_CV_WEIGHT * normalized_cv
        + MIN_ANGLE_WEIGHT * (1 - min_angle)
    )

    if echo:
        print(
            str(CROSSLESSNESS_WEIGHT)
            + " * (1 - "
            + str(crosslessness)
            + ") + "
            + str(NORMALIZED_CV_WEIGHT)
            + " * "
            + str(normalized_cv)
            + " + "
            + str(MIN_ANGLE_WEIGHT)
            + " * (1 - "
            + str(min_angle)
            + ")= "
            + str(reward_val)
        )
    return reward_val
