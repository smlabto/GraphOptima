import time
import numpy as np
import logging
from pos_df_to_graph import pos_df_to_graph
import os
import pygraphviz as pgv
import pandas as pd
import uuid
import json
from utils import *
import graph_tool.all as gt

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

GRAPHML_FILE = CONFIG["layout_generator"]["GRAPHML_FILE"]
GRAPH_TOOL_GRAPH = gt.load_graph(GRAPHML_FILE)
REPEAT_EVAL_TIMES = CONFIG["verify_optimized_params"]["REPEAT_EVAL_TIMES"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("verify_optimized_params_output.log", mode="a"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


"""
The following 3 functions calculates the relationship between the optimal parameters found by the optimized, and the 
graph this set of parameter produces. we know from the optimized the best parameters and its best readability measures 
accordingly. Now i want to verify if this best set of parameters can consistently produce graph with similar readability 
measurements. I want generate new readability measurements n times using the optimal parameters, then calculate the 
correlation between the best readability and the new readability measurements.
"""


# make an array of the best readability and generated readability
def make_correlation_array(
    n: int,
    optimal_params_from_optimizer: list,
    best_readability_from_optimizer: list,
    initial_guess_params: list,
    func,
):
    best_readability_array = []
    reproduced_best_readability_array = []
    initial_readability_array = []

    for i in range(n):
        best_readability_array.append(best_readability_from_optimizer)
        reproduced_best_readability_array.append(func(optimal_params_from_optimizer))
        initial_readability_array.append(func(initial_guess_params))

    return (
        best_readability_array,
        reproduced_best_readability_array,
        initial_readability_array,
    )


# find correlation between 2 arrays
def get_correlate(array1: list, array2: list):
    return np.corrcoef(array1, array2)[0, 1]


def get_average_initial_and_optimized_readability(
    initial_readability_array: list, generated_readability_array: list
):
    return np.average(generated_readability_array), np.average(
        initial_readability_array
    )


# load a dot file into a position dataframe
def dot_to_pos_df(dot_file: str):
    # Load the dot file into a PyGraphviz graph
    # if the file doesn't exist, keep trying
    while True:
        try:
            graph = pgv.AGraph(dot_file)
            break
        except:
            pass

    # Prepare an empty list to hold the data
    data = []

    # Iterate over each node in the graph
    for node in graph.nodes():
        # Extract the x, y coordinates
        x = node.attr["x"]
        y = node.attr["y"]

        # Add the data to our list
        data.append([node, x, y])

    # Create a DataFrame from our data
    df = pd.DataFrame(data, columns=["vertex", "x", "y"])

    # remove the dot file
    try:
        os.remove(dot_file)
    except FileNotFoundError:
        pass

    return df


def display_average_improvement(
    average_optimized_readability, average_initial_readability
):
    logging.info("Average optimized readability: " + str(average_optimized_readability))
    logging.info("Average initial readability: " + str(average_initial_readability))

    improvement_percentage = (
        (average_initial_readability - average_optimized_readability)
        / average_initial_readability
        * 100
    )
    logging.info("Improvement: " + str(improvement_percentage) + "%")


def make_params_file_and_retrieve_pos_df(uuid, param0, param1, param2):
    make_params_file(uuid=uuid, params=[param0, param1, param2])
    return dot_to_pos_df(dot_file=uuid + ".dot")


def plot_initial_and_optimized_layout(
    graphml,
    initial_params,
    final_params,
    initial_layout_plot_name="initial_layout",
    optimized_layout_plot_name="optimized_layout",
):
    initial_pos_df = make_params_file_and_retrieve_pos_df(
        uuid=str(uuid.uuid4()),
        param0=initial_params[0],
        param1=initial_params[1],
        param2=initial_params[2],
    )

    optimized_pos_df = make_params_file_and_retrieve_pos_df(
        uuid=str(uuid.uuid4()),
        param0=final_params[0],
        param1=final_params[1],
        param2=final_params[2],
    )

    pos_df_to_graph(
        graphml=graphml,
        pos_df=initial_pos_df,
        name=initial_layout_plot_name,
        resolution=CONFIG["verify_optimized_params"]["PLOT_RESOLUTION"],
    )
    pos_df_to_graph(
        graphml=graphml,
        pos_df=optimized_pos_df,
        name=optimized_layout_plot_name,
        resolution=CONFIG["verify_optimized_params"]["PLOT_RESOLUTION"],
    )


def verify_optimized_params(
    initial_guess_params,
    func,
    best_params=None,
    best_readability=None,
    weight1=1,
    weight2=1,
    weight3=1,
):
    best_readability_array, generated_readability_array, initial_readability_array = (
        make_correlation_array(
            n=REPEAT_EVAL_TIMES,
            optimal_params_from_optimizer=best_params,
            best_readability_from_optimizer=best_readability,
            initial_guess_params=initial_guess_params,
            func=func,
        )
    )

    average_optimized_readability, average_initial_readability = (
        get_average_initial_and_optimized_readability(
            initial_readability_array, generated_readability_array
        )
    )

    # correlation = get_correlate(best_readability_array, generated_readability_array)
    logging.info("Weights: " + str(weight1) + " " + str(weight2) + " " + str(weight3))
    # logging.info(
    #     "The correlation between the returned readability and the readability generated using best params is :"
    #     + str(correlation)
    # )
    logging.info(
        "The best readability returned from the optimizer is :" + str(best_readability)
    )
    logging.info(
        "The params that produced the best readability in the optimizer is :"
        + str(best_params)
    )

    logging.info("Initial readability array: " + str(initial_readability_array))
    logging.info("Best readability array: " + str(best_readability_array))
    logging.info("Readability array: " + str(generated_readability_array))

    display_average_improvement(
        average_optimized_readability, average_initial_readability
    )

    plot_initial_and_optimized_layout(
        GRAPH_TOOL_GRAPH,
        initial_guess_params,
        best_params,
        "initial_layout_weighted_"
        + str(weight1)
        + "_"
        + str(weight2)
        + "_"
        + str(weight3),
        "optimized_layout_weighted_"
        + str(weight1)
        + "_"
        + str(weight2)
        + "_"
        + str(weight3),
    )


# read a DATABASE from the optimizer, return the value in the params column of the same row of the min readability
def get_best_params_from_database(database):
    best_readability = database.loc[database["readability"].idxmin()]["readability"]
    best_params = database.loc[database["readability"].idxmin()]["params"]
    return best_params, best_readability


if __name__ == "__main__":
    pass
"""
This script shall not be called from outside the optimizer, as the global variables must be imported from the 
optimizer to avoid importing the same variables twice in the memory
"""
