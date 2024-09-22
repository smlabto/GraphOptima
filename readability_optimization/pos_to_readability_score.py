import time
import pandas as pd
import os
import re
from utils import *


def pos2dot(pos_df: pd.DataFrame, graph_tool_graph, output_name, echo=False):
    g = graph_tool_graph

    x_pos = g.new_vertex_property("double")
    y_pos = g.new_vertex_property("double")

    # if the vertex name is a string like n1234, convert it to integer 1234
    if type(pos_df.iloc[0]["vertex"]) is str:
        pos_df["vertex"] = pos_df["vertex"].apply(
            lambda x: int(re.sub("[^0-9]", "", x))
        )

    for i in range(len(pos_df)):
        x_pos[pos_df.iloc[i]["vertex"]] = pos_df.iloc[i]["x"]
        y_pos[pos_df.iloc[i]["vertex"]] = pos_df.iloc[i]["y"]

    # add the x_pos and y_pos to the graph
    g.vertex_properties["x"] = x_pos
    g.vertex_properties["y"] = y_pos

    # remove all other properties
    properties_to_remove = list(g.vertex_properties)
    for p in properties_to_remove:
        if not (p == "x" or p == "y"):
            del g.vertex_properties[p]
    g.set_directed(False)

    properties_to_remove = list(g.edge_properties)
    for p in properties_to_remove:
        del g.edge_properties[p]

    g.save("to_check_" + output_name)

    # convert the last line of the to_check dot file into a string and print it
    # with open("to_check_" + output_name, 'rb+') as f:
    #     lines = f.readlines()
    #     last_line = lines[-1].decode("utf-8")
    #     print(f"The last line of 'to_check_{output_name}' is: {repr(last_line)}")
    #     time.sleep(10)

    with open("to_check_" + output_name, "rb+") as f:
        # print("Checking if the last line of 'to_check_" + output_name + "' has a '}'")
        # time.sleep(10)
        f.seek(-1, os.SEEK_END)  # Go to the end of file
        while f.tell() > 0:  # Ensure we haven't read past the start of the file
            char = f.read(1)
            if (
                char == b"\n" or char == b"\r" or char == b" "
            ):  # Skip newlines and spaces
                f.seek(-2, os.SEEK_CUR)
                continue
            f.seek(-1, os.SEEK_CUR)  # Step back one character
            break  # Stop loop, as we have found a non-space, non-newline character

        char = f.read(1)  # Read the non-space, non-newline character
        if char != b"}":  # If last non-whitespace char isn't "}", append "}"
            f.seek(0, os.SEEK_END)  # Go to the end of file
            f.write(b"}")

    # ------------------------------------------------------------------------------------

    # remove the "to_check_" prefix
    os.rename("to_check_" + output_name, output_name)

    # copy and rename the file
    # shutil.copyfile("to_check_" + output_name, output_name)

    if echo:
        print("Graph saved to " + output_name)


def retrieve_readability_score_and_cleanup(
    uuid: str,
    retrieve_directory: str = os.getcwd() + "/readability_score_results",
    echo: bool = False,
    cleanup: bool = True,
):
    # logic: keep scanning the target folder until specific uuid is found
    # Challenge: first in first out - ignore for now
    result = []
    while not result:
        if echo:
            # print("Retrieving readability scores for layout " + uuid + ' ......')
            # time.sleep(1)
            pass
        result = retrieve_file_list(
            retrieve_directory=retrieve_directory,
            endswith=uuid + ".txt",
            startswith="",
            not_startswith=".",
        )

    with open(retrieve_directory + "/" + result[0]) as f:
        content = f.read()
        # display the content of the file
        if echo:
            print("From the txt file: " + content)
        readability_metrics_string_list = content.split()

    readability_metrics = []

    if readability_metrics_string_list:
        for i in range(5, len(readability_metrics_string_list)):
            readability_metrics_string = readability_metrics_string_list[i]
            # find all the numbers in the string
            readability_metrics_num = re.findall(
                r"[-+]?(?:\d*\.\d+|\d+)", readability_metrics_string
            )
            for n in readability_metrics_num:
                readability_metrics.append(n)

    if echo or len(readability_metrics) != 7:
        print("retrieve_readability_score_and_cleanup: " + str(readability_metrics))

    if cleanup:
        os.remove(retrieve_directory + "/" + result[0])
    return readability_metrics


# return dataframe from csv
def csv_to_df(csv_file):
    df = pd.read_csv(csv_file)
    return df


# make dataframe into list of lists
def df_to_list(df):
    l = df.values.tolist()
    return l


if __name__ == "__main__":
    pos_file = "Feb-22-indegree.csv"
    pos_file = csv_to_df(pos_file)
    pos_list = df_to_list(pos_file)
    graphml_file = "twitter_network_clean_v1.0-edges-2-indegree-Gephi.graphml"
    output_name = "Feb-22-indegree.dot"
    pos2dot(pos_list, graphml_file, output_name)
