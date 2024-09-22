"""
This script hosts the main layout evaluator of the GraphOptima
The main function of the script will constantly scan for new .dot files produced by the cuGraph_to_pos_df.py.
Once detected, the script will lock the file and process the .dot file. The layout evaluator will then generate the
layout and save it as a readability score txt file that can be processed by the optimizer.py
"""

import time
from filelock import FileLock, Timeout
import subprocess
import tempfile
import utils
from utils import *

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

DEBUG = CONFIG["dot_to_readability_score"][
    "DEBUG"
]  # Set this to True to enable debug output
GLAM_PATH = CONFIG["dot_to_readability_score"]["GLAM_PATH"]


def debug_print(*args, **kwargs):
    global DEBUG
    if DEBUG:
        print(*args, **kwargs)


def process_dot_file(dot_file_name: str, echo: bool = False):
    print(f"{utils.get_timestamp()}: Processing file in subprocess: " + dot_file_name)

    uuid = dot_file_name[:-4]

    r = subprocess.getoutput(
        GLAM_PATH
        + " "
        + dot_file_name
        + " -m "
        + "crosslessness edge_length_cv min_angle shape_gabriel shape_delaunay"
    )

    if echo:
        print(f"{utils.get_timestamp()}: echoing result directly from GLAM: " + r)

    # Create and write to a temporary file first
    destination_path = os.getcwd() + "/readability_score_results/"
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=destination_path
    ) as tmpfile:
        tmpfile.write(r)

    # Rename the temporary file to the final destination (atomic operation)
    os.rename(tmpfile.name, os.path.join(destination_path, uuid + ".txt"))


def main():
    while True:
        dot_list = retrieve_file_list(
            startswith="", not_startswith="to_check_", endswith=".dot"
        )
        debug_print(f"{utils.get_timestamp()}: Retrieved file list: {dot_list}")
        if dot_list:
            for dot_file in sorted(dot_list):
                if not os.path.exists(dot_file):
                    print(
                        f"{utils.get_timestamp()}: File "
                        + str(dot_file)
                        + " does not exist, skipping..."
                    )
                    time.sleep(1)
                    continue
                else:
                    lock = FileLock(dot_file + ".lock")
                    try:
                        lock.acquire(timeout=0)  # try to lock the file
                        debug_print(
                            f"{utils.get_timestamp()}: Trying to open and lock: {dot_file}"
                        )
                        debug_print(
                            f"{utils.get_timestamp()}: Processing file: {dot_file}"
                        )

                        # Call process_dot_file function here
                        process_dot_file(dot_file, echo=True)

                        debug_print(
                            f"{utils.get_timestamp()}: Finished processing file: {dot_file}"
                        )
                        # unlock and remove the dot file
                        debug_print(
                            f"{utils.get_timestamp()}: Releasing lock for: {dot_file}"
                        )

                        # Temporarily rename the file to a .dot_processed extension
                        os.rename(dot_file, dot_file + ".dot_processed")

                        # Now we can safely release the lock
                        lock.release()

                        # And finally delete the .dot_processed file
                        os.remove(dot_file + ".dot_processed")
                        debug_print(
                            f"{utils.get_timestamp()}: Removed file: {dot_file + '.dot_processed'}"
                        )

                        # Remove the lock file
                        os.remove(dot_file + ".lock")

                    except Timeout:
                        # If the file is locked and cannot be opened immediately, we skip it for this round
                        debug_print(
                            f"{utils.get_timestamp()}: File {dot_file} is locked, skipping for this file..."
                        )
                        time.sleep(1)
                        continue
                    except FileNotFoundError:
                        debug_print(
                            f"{utils.get_timestamp()}: File {dot_file} not found, skipping for this file..."
                        )
                        time.sleep(1)
                        continue
        else:
            debug_print(
                f"{utils.get_timestamp()}: No dot files found after scanning through the entire list, sleeping for a "
                f"second..."
            )
            time.sleep(1)


if __name__ == "__main__":
    main()
