import graph_tool.all as gt
import pos_to_readability_score
from filelock import FileLock, Timeout
from utils import *
import os
import time
import json

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

# Extract configurations for gt_to_pos_df
CONFIG = CONFIG["layout_generator"]

# Extract individual configurations
GRAPHML_FILE = CONFIG["GRAPHML_FILE"]
DEBUG = CONFIG["DEBUG"]

GRAPH_TOOL_GRAPH = gt.load_graph(GRAPHML_FILE)


def debug_print(*args, **kwargs):
    global DEBUG
    if DEBUG:
        print(*args, **kwargs)


def gt_to_pos_df(gt_Graph, param0, param1, param2) -> pd.DataFrame:
    if type(param2) is not int:
        param2 = int(param2)

    pos = gt.sfdp_layout(gt_Graph, r=param0, C=param1, max_iter=param2)
    gt_Graph.vertex_properties["pos"] = pos

    pos_array = [[v, *pos[v]] for v in gt_Graph.vertices()]
    pos_df = pd.DataFrame(pos_array, columns=["vertex", "x", "y"])
    return pos_df


def process_params_file(param_file: str):
    debug_print("Processing the params file: " + param_file)
    layout_id = param_file[:-7]
    with open(param_file, "r") as f:
        params = f.readlines()
        if not params:
            debug_print(f"The file {param_file} is empty or could not be read.")
        else:
            try:
                params = [float(x) for x in params[0].split(",")]
            except Exception as e:
                debug_print(f"An unexpected error occurred: {e}")
                debug_print(f"Content of the file: {params}")
                return False

        debug_print(f"params_to_test: {params}")
        pos_df = gt_to_pos_df(GRAPH_TOOL_GRAPH, params[0], params[1], params[2])
        debug_print("Layout is generated, now converting to dot file...")
        pos_to_readability_score.pos2dot(
            pos_df=pos_df,
            graph_tool_graph=GRAPH_TOOL_GRAPH,
            output_name=layout_id + ".dot",
            echo=False,
        )

        return True


def main():
    while True:
        params_list = retrieve_file_list(
            retrieve_directory=".", endswith="params", startswith="", not_startswith="."
        )
        debug_print(f"Retrieved file list: {params_list}")

        if params_list:
            for param_file in sorted(params_list):
                if not os.path.exists(param_file):
                    debug_print(
                        "File " + str(param_file) + "does not exist, skipping..."
                    )
                    continue
                lock = FileLock(param_file + ".lock")
                try:
                    lock.acquire(timeout=0)
                    debug_print(f"Trying to open and lock: {param_file}")
                    if not process_params_file(param_file):
                        debug_print(f"Failed to process params file: {param_file}")

                    debug_print(f"Finished processing file: {param_file}")
                    debug_print(f"Releasing lock for: {param_file}")
                    os.rename(param_file, param_file + ".params_processed")
                    lock.release()
                    os.remove(param_file + ".params_processed")
                    debug_print(f"Removed file: {param_file + '.params_processed'}")
                    os.remove(param_file + ".lock")
                except Timeout:
                    debug_print(
                        f"File {param_file} is locked, skipping for this file..."
                    )
                    time.sleep(1)
                    continue
                except FileNotFoundError:
                    debug_print(
                        f"File {param_file} not found, skipping for this file..."
                    )
                    time.sleep(1)
                    continue
        else:
            debug_print(
                "No params files found after scanning through the entire list, sleeping for a second..."
            )
            time.sleep(1)


if __name__ == "__main__":
    main()
