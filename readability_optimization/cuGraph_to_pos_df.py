"""
This script hosts the main layout generator of the GraphOptima
The main function of the script will constantly scanning for new .param produced by the optimizer.py. Once detected, the
script will lock the file and process the .param file. The layout generator will then generate the layout and save it as
a .dot file. The .dot file will then be processed by the pos_to_readability_score.py to calculate the readability score
"""

import time

import cudf
import cugraph
import graph_tool.all as gt
import pos_to_readability_score
from filelock import FileLock, Timeout
import json
import utils
import input_graphs.csv2tsv
import os
import subprocess
from utils import *

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

# Extract configurations for cuGraph_to_pos_df
CONFIG = CONFIG["layout_generator"]

# Extract individual configurations
GRAPHML_FILE = CONFIG["GRAPHML_FILE"]
GRAPH_FILE_NAME = GRAPHML_FILE.split(".")[0]

# Separate the path and the filename without the extension from the GRAPH_FILE_NAME
GRAPH_FILE_PATH, GRAPH_FILE_NAME = os.path.split(GRAPH_FILE_NAME)

# Construct the CSV_FILE path correctly
CSV_FILE = GRAPH_FILE_PATH + '/fixed_' + GRAPH_FILE_NAME + "-edges.csv"

while True:
    # Check if the CSV version of the graph exists under the input_graphs folder
    if not os.path.exists(CSV_FILE):
        # Try to acquire lock for the GraphML file
        lock = FileLock(GRAPHML_FILE + ".lock")
        try:
            acquired = lock.acquire(timeout=0)
            if acquired:
                try:
                    # Convert the GraphML file to a CSV file
                    subprocess.run(["python", "input_graphs/graphml2csv.py", "-i", GRAPHML_FILE], check=True)
                    print("Conversion successful.")
                except Exception as e:
                    print(f"\n\nAn error occurred: {e}")
                    print("Falling back to graph-tool backend to retry...")
                    try:
                        # Retry by first loading the GraphML using graph-tool
                        g = gt.load_graph(GRAPHML_FILE)
                        print("Graph loaded by graph-tool. Saving it as a GraphML file...")
                        g.save(GRAPHML_FILE)
                        print("Graph saved as a GraphML file. Converting it to a CSV file...")
                        # Retry the conversion
                        subprocess.run(["python", "input_graphs/graphml2csv.py", "-i", GRAPHML_FILE], check=True)
                        print("Conversion successful.")
                    except Exception as retry_e:
                        print(f"Retry failed: {retry_e}")
                finally:
                    # Assuming the module and function for CSV to TSV conversion is correct
                    input_graphs.csv2tsv.csv2tsv(file_name=f"{GRAPH_FILE_PATH}/{GRAPH_FILE_NAME}-edges.csv",
                                                 directory="")

                    # Release the lock
                    lock.release()
                    break
        except Timeout:
            print("GraphML file is being converted to a CSV file, waiting for it to finish...")
            time.sleep(5)
    else:
        print("CSV file already exists, skipping conversion.")
        break

DEBUG = CONFIG["DEBUG"]

# Apply configurations
CUDF_EDGELIST = cudf.read_csv(
    CSV_FILE, names=["source", "target"], dtype=["string", "string"], sep="\t"
)

CUDF_EDGELIST = CUDF_EDGELIST[0:-1]

CUGRAPH_GRAPH = cugraph.Graph()
CUGRAPH_GRAPH.from_cudf_edgelist(CUDF_EDGELIST, source="source", destination="target")
GRAPH_TOOL_GRAPH = gt.load_graph(GRAPHML_FILE)


def debug_print(*args, **kwargs):
    global DEBUG
    if DEBUG:
        print(*args, **kwargs)


def cuGraph_to_pos_df(
        cuGraph_Graph: cugraph.Graph, param0, param1, param2
) -> cudf.DataFrame:
    # if param2 < 0.5:
    #     param2 = False
    # else:
    #     param2 = True

    # if param2 is not int, turn it into int
    if type(param2) is not int:
        param2 = int(param2)

    position_dff = cugraph.force_atlas2(
        cuGraph_Graph, scaling_ratio=param0, gravity=param1, max_iter=param2
    )
    return position_dff.to_pandas()


def process_params_file(param_file: str) -> bool:
    debug_print(f"{utils.get_timestamp()}: Processing the params file: " + param_file)
    # separate the file name from the extension
    layout_id = param_file[:-7]
    # read the file
    with open(param_file, "r") as f:
        params = f.readlines()
        # check if params is empty
        if not params:
            debug_print(
                f"{utils.get_timestamp()}: The file {param_file} is empty or could not be read."
            )
        else:
            try:
                # convert the content from a ',' seperated string into a list of params
                params = [float(x) for x in params[0].split(",")]
            except Exception as e:
                debug_print(
                    f"{utils.get_timestamp()}: An unexpected error occurred: {e}"
                )
                # display the content of the file
                debug_print(f"{utils.get_timestamp()}: Content of the file: {params}")
                return False

        debug_print(f"{utils.get_timestamp()}: params_to_test: {params}")
        pos_df = cuGraph_to_pos_df(
            cuGraph_Graph=CUGRAPH_GRAPH,
            param0=params[0],
            param1=params[1],
            param2=params[2],
        )
        debug_print(
            f"{utils.get_timestamp()}: Layout is generated, now converting to dot file..."
        )
        pos_to_readability_score.pos2dot(
            pos_df=pos_df,
            graph_tool_graph=GRAPH_TOOL_GRAPH,
            output_name=layout_id + ".dot",
            echo=False,
        )
        debug_print(
            f"{utils.get_timestamp()}: Dot file generated: {layout_id + '.dot'}"
        )

        return True


def main():
    while True:
        params_list = retrieve_file_list(
            startswith="", not_startswith=".", endswith=".params"
        )

        debug_print(f"{utils.get_timestamp()}: Retrieved file list: {params_list}")

        # two ways to go into wait: 1. no file in the list, 2. all files in the list are locked

        if params_list:
            for param_file in sorted(params_list):
                if not os.path.exists(param_file):
                    debug_print(
                        f"{utils.get_timestamp()}: File "
                        + str(param_file)
                        + " does not exist, skipping..."
                    )
                    time.sleep(1)
                    continue
                lock = FileLock(param_file + ".lock")
                try:
                    lock.acquire(timeout=0)  # try to lock the file
                    debug_print(
                        f"{utils.get_timestamp()}: Trying to open and lock: {param_file}"
                    )
                    # Call process_dot_file function here
                    # process_params_file only returns true if the file is processed successfully
                    if not process_params_file(param_file):
                        debug_print(
                            f"{utils.get_timestamp()}: Failed to process params file: {param_file}"
                        )

                    debug_print(
                        f"{utils.get_timestamp()}: Finished processing file: {param_file}"
                    )
                    # unlock and remove the dot file workflow starts:
                    debug_print(
                        f"{utils.get_timestamp()}: Releasing lock for: {param_file}"
                    )

                    # Temporarily rename the file to a .dot_processed extension through atomic operation
                    os.rename(param_file, param_file + ".params_processed")

                    # Now we can safely release the lock
                    lock.release()

                    # And finally delete the .dot_processed file
                    os.remove(param_file + ".params_processed")
                    debug_print(
                        f"{utils.get_timestamp()}: Removed file: {param_file + '.params_processed'}"
                    )

                    # Remove the lock file
                    os.remove(param_file + ".lock")

                except Timeout:
                    # If the file is locked and cannot be opened immediately, we skip it for this round
                    debug_print(
                        f"{utils.get_timestamp()}: File {param_file} is locked, skipping for this file..."
                    )
                    time.sleep(1)
                    continue
                except FileNotFoundError:
                    debug_print(
                        f"{utils.get_timestamp()}: File {param_file} not found, skipping for this file..."
                    )
                    time.sleep(1)
                    continue
        else:
            debug_print(
                f"{utils.get_timestamp()}: No params files found after scanning through the entire list, sleeping for "
                f"a second..."
            )
            time.sleep(1)


if __name__ == "__main__":
    main()
