import datetime
import uuid
import os
import reward
import numpy as np
import matplotlib.pyplot as plt
from pymoo.visualization.scatter import Scatter
import json
import pandas as pd

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

# Extract configurations for external_api
CONFIG = CONFIG["external_api"]

# Set up configurations
INSTRUCTION_PATH = os.getcwd() + CONFIG["INSTRUCTION_PATH"]


# return string timestamp
def get_timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def generate_layout_id() -> str:
    layout_id = str(uuid.uuid4())
    return layout_id


def make_params_file(uuid: str, params: list):
    """
    make a .params file with the given params
    the .params file will be caught and locked by the layout generators, thus achieving async multiprocessing
    """
    # if param2 is not int, turn it into int
    if type(params[2]) is not int:
        params[2] = int(params[2])

    # save the params into a comma seperated .params_temp file
    # this is to ensure that the params file won't be caught before the writing is finished
    with open(uuid + ".params_temp", "w") as f:
        # loop through the params
        for param in params:
            # check, if the current param is the last one, don't add the comma
            if param == params[-1]:
                f.write(str(param))
                break
            # write the params into the file
            f.write(str(param) + ",")

    # rename the .params_temp file to .params using **atomic operation**
    os.rename(uuid + ".params_temp", uuid + ".params")


def make_new_metadata(
    graph_file_name: str,
    algorithm_being_optimized: str,
    optimization_algorithm_used: str,
    readability_calculation_method: str,
    readability_calculation_weight_list: list,
) -> dict:
    metafile_dict = {
        "graph_file_name": graph_file_name,
        "algorithm_being_optimized": algorithm_being_optimized,
        "optimization_algorithm_used": optimization_algorithm_used,
        "readability_calculation_method": readability_calculation_method,
        "readability_calculation_weight_list": readability_calculation_weight_list,
    }
    return metafile_dict


# generate n objective weight lists
def generate_n_objective_weights(
    n: int = 3,
    granularity: float = 0.25,
    weight_sum: float = 1.0,
    current_weights: list = None,
) -> list:
    if current_weights is None:
        current_weights = []
    weights_list = []

    if n == 1:
        # base case: only one weight left, so it gets the rest of the weight sum
        current_weights.append(weight_sum)
        weights_list.append(tuple(current_weights))
    else:
        # Iterate over possible values for the current weight
        for weight in np.arange(0, weight_sum + granularity, granularity):
            new_weights = current_weights.copy()
            new_weights.append(weight)
            # Recurse for remaining weights
            weights_list.extend(
                generate_n_objective_weights(
                    n - 1, granularity, weight_sum - weight, new_weights
                )
            )

    return weights_list


# try to remove all core dump files in the current directory
def remove_core_dump_files():
    # get the current working directory
    current_dir = os.getcwd()
    # get all the files in the current directory
    files = os.listdir(current_dir)
    # loop through the files
    for file in files:
        # check if the file is a core dump file
        if file.startswith("core."):
            # remove the file
            try:
                os.remove(file)
            except FileNotFoundError:
                # no core dump files found, good!
                pass


# remove all the txt files under the readability_score_results folder of the current directory
def remove_readability_score_results():
    # get the current working directory
    current_dir = os.getcwd()
    # get all the files under the readability_score_results folder
    current_dir = os.path.join(current_dir, "readability_score_results/")
    files = os.listdir(current_dir)
    # loop through the files
    for file in files:
        # check if the file is a core dump file
        if file.endswith(".txt"):
            # remove the file
            try:
                os.remove(file)
            except FileNotFoundError:
                pass


# remove all the .lock files under the current directory
def remove_lock_files():
    # get the current working directory
    current_dir = os.getcwd()
    # get all the files in the current directory
    files = os.listdir(current_dir)
    # loop through the files
    for file in files:
        # check if the file is a lock file
        if file.endswith(".lock"):
            # remove the file
            try:
                os.remove(file)
            except FileNotFoundError:
                pass


# write an optimization completed indicator file to the current directory
def write_optimization_completed_indicator_file():
    # get the current working directory
    current_dir = os.getcwd()
    # create a file named "optimization_completed_indicator_file.txt"
    with open(os.path.join(current_dir, "optimization_completed.txt"), "w") as f:
        f.write("optimization completed")


def write_optimization_result(optimal_params, optimal_readability, weights):
    # store results in a file
    with open(
        "results_"
        + str(reward.CROSSLESSNESS_WEIGHT)
        + "_"
        + str(reward.NORMALIZED_CV_WEIGHT)
        + "_"
        + str(reward.MIN_ANGLE_WEIGHT)
        + ".txt",
        "a",
    ) as f:
        f.write(f"Optimal params: {optimal_params}\n")
        f.write(f"Optimal value: {optimal_readability}\n")
        f.write(f"Weights: {weights}\n")
        f.write("\n\n")


# remove the optimization_completed.txt file from the current directory
def remove_optimization_completed_indicator_file():
    # get the current working directory
    current_dir = os.getcwd()
    # create a file named "optimization_completed_indicator_file.txt"
    try:
        os.remove(os.path.join(current_dir, "optimization_completed.txt"))
    except FileNotFoundError:
        pass


# plot the convergence of the multi-objective optimization algorithm under pymoo
def plot_convergence(results, labels):
    plt.figure()
    for res, label in zip(results, labels):
        ret = [np.min(e.pop.get("F")) for e in res.history]
        plt.plot(np.arange(len(ret)), ret, label=label)

    plt.title("Convergence")
    plt.xlabel("Generation")
    plt.ylabel("F")
    plt.legend()
    plt.savefig("convergence.png")


# plot the pareto front of the multi-objective optimization algorithm under pymoo
def plot_pareto_front(problem, res):
    plt.figure()
    Scatter().add(res.F).show()
    plt.savefig("pareto_front_1.png")

    plt.figure()
    plot = Scatter()
    plot.add(problem.pareto_front(), plot_type="line", color="black", alpha=0.7)
    plot.add(res.F, facecolor="none", edgecolor="red")
    plt.savefig("pareto_front_2.png")
    plot.show()


def retrieve_file_list(
    startswith: str,
    not_startswith: str,
    endswith: str,
    retrieve_directory: str = os.getcwd(),
):
    l = []
    for x in os.listdir(retrieve_directory):
        if (
            x.startswith(startswith)
            and not x.startswith(not_startswith)
            and x.endswith(endswith)
        ):
            l.append(x)
    return l


def pretty_print_dataframe(df: pd.DataFrame, max_cell_length: int = 10):
    headers = df.columns
    data = df.values.tolist()

    def truncate(cell):
        cell_str = str(cell)
        if len(cell_str) > max_cell_length:
            return cell_str[: max_cell_length - 3] + "..."
        return cell_str

    max_widths = [len(str(header)) for header in headers]
    for row in data:
        for i, cell in enumerate(row):
            max_widths[i] = max(max_widths[i], len(truncate(cell)))

    format_str = " | ".join([f"{{:<{width}}}" for width in max_widths])
    separator = "-+-".join(["-" * width for width in max_widths])

    print(format_str.format(*headers))
    print(separator)
    for row in data:
        print(format_str.format(*[truncate(cell) for cell in row]))


def get_db_files():
    db_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.endswith(".db"):
                db_files.append(os.path.join(root, file))
    return db_files
