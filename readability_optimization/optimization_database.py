import shutil

import pandas as pd
import time
import os
import numpy as np
import json
import sqlite3
import reward
from utils import get_timestamp
from numba import jit
from utils import pretty_print_dataframe

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

DATABASE_PATH = CONFIG["optimization_database"]["DATABASE_PATH"]
MAX_ERROR_PERCENTAGE = CONFIG["optimization_database"]["MAX_ERROR_PERCENTAGE"]
COSINE_SIMILARITY_THRESHOLD = CONFIG["optimization_database"][
    "COSINE_SIMILARITY_THRESHOLD"
]
DATABASE_PRINTOUT_LINES = CONFIG["optimization_database"]["DATABASE_PRINTOUT_LINES"]
LOG_DATABASE_READ_TIME = CONFIG["optimization_database"]["LOG_DATABASE_READ_TIME"]
DATABASE_READ_TIME = None


def dataframe_to_json(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function converts the 'params', 'glam_results', 'readability' and 'metadata' columns to JSON.
    """

    def ndarray_to_list(data):
        if isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data

    df_copy = df.copy()
    for column in ["params", "glam_results", "readability", "metadata"]:
        df_copy[column] = df_copy[column].apply(ndarray_to_list)
        df_copy[column] = df_copy[column].apply(json.dumps)
    return df_copy


def dataframe_from_json(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function converts the JSON in the 'params', 'glam_results', 'readability' and 'metadata' columns back to
    their original data types.
    """
    df_copy = df.copy()
    for column in ["params", "glam_results", "readability", "metadata"]:
        df_copy[column] = df_copy[column].apply(json.loads)
    return df_copy


def open_optimized_connection(database_path: str) -> sqlite3.Connection:
    """
    Open a new SQLite3 connection and optimize it for performance.
    """
    while True:
        try:
            if not os.path.exists(database_path):
                print(
                    f"Database does not exist at {database_path}. Initializing database."
                )
                # If the file does not exist, initialize the database
                initialize_database(database_path=database_path)
                continue

            print(f"Opening connection to database at {database_path}.")
            conn = sqlite3.connect(database_path)

            # Enable optimizations
            print("Enabling database optimizations.")
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode = wal")
            cursor.execute("PRAGMA synchronous = normal")
            cursor.execute("PRAGMA journal_mode = MEMORY")
            # cursor.execute("PRAGMA locking_mode = EXCLUSIVE")
            cursor.execute("PRAGMA temp_store = MEMORY")

            # Return the optimized connection
            print("Successfully opened and optimized connection.")
            return conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("Database is locked, retrying connection.")
                time.sleep(1)  # If the database is locked, wait a bit and try again
                return open_optimized_connection(database_path=database_path)
            else:
                print(f"Unexpected error while opening connection: {e}")
                raise


def close_connection(conn: sqlite3.Connection):
    """
    Close an SQLite3 connection.
    """
    try:
        conn.close()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            # time.sleep(0.01)  # If the database is locked, wait a bit and try again
            close_connection(conn=conn)
        else:
            raise


def initialize_database(database_path: str):
    # Initialize an empty DataFrame with the correct columns
    # Print debug message
    print("Initializing database...")

    while True:
        try:
            if not os.path.exists(database_path):
                # Create the database file if it doesn't exist
                with open(database_path, "w"):
                    continue
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS optimization_results (
                        rowid INTEGER PRIMARY KEY,
                        iteration_num INTEGER,
                        params TEXT,
                        glam_results TEXT,
                        readability TEXT,
                        metadata TEXT
                    )
                """
                )
            break  # If the operation is successful, break the loop
        except (sqlite3.OperationalError, pd.errors.DatabaseError) as e:
            if "database is locked" in str(e):
                # time.sleep(0.01)  # If the database is locked, wait a bit and try again
                continue
            else:
                raise  # If it's a different error, re-raise it


def log_and_save(
    iteration: int,
    params: list,
    glam_results: list,
    readability: list,
    metadata: dict,
    conn: sqlite3.Connection,
    echo: bool = False,
):
    try:
        # Create a new DataFrame with the row to append
        df_to_append = pd.DataFrame(
            {
                "iteration_num": [iteration],
                "params": [params],
                "glam_results": [glam_results],
                "readability": [readability],
                "metadata": [metadata],
            }
        )

        df_to_append = dataframe_to_json(df_to_append)
        # Append the DataFrame to the SQLite database
        start_time = 0
        if echo:
            start_time = time.time()
        df_to_append.to_sql(
            "optimization_results", conn, if_exists="append", index=False
        )
        if echo:
            end_time = time.time()
            print(f"Saving to database took {end_time - start_time} seconds.")
    except (sqlite3.OperationalError, pd.errors.DatabaseError) as e:
        if "database is locked" in str(e):
            # time.sleep(0.01)  # If the database is locked, wait a bit and try again
            log_and_save(iteration, params, glam_results, readability, metadata, conn)
        else:
            raise  # If it's a different error, re-raise it


def read_database_file_to_object(
    conn: sqlite3.Connection, lines_to_read: int = None, echo: bool = False
):
    while True:
        try:
            # Read the DataFrame from the SQLite database
            if lines_to_read is not None:
                query = f"SELECT * FROM (SELECT * FROM optimization_results ORDER BY rowid DESC LIMIT {lines_to_read}) ORDER BY rowid ASC"
            else:
                query = "SELECT * from optimization_results"

            # Log the start time
            start_time = 0
            if LOG_DATABASE_READ_TIME:
                start_time = time.time()

            # print the echo message
            if echo:
                print("Fetch data from database ...")
            df = pd.read_sql_query(query, conn)

            # Log the end time and append the time taken to DATABASE_READ_TIME
            if LOG_DATABASE_READ_TIME:
                end_time = time.time()
                global DATABASE_READ_TIME
                DATABASE_READ_TIME = end_time - start_time

            # Convert params, glam_results, readability (if it's a string representing a list), and metadata from
            # JSON to lists/dictionaries
            return dataframe_from_json(df)
        except (sqlite3.OperationalError, pd.errors.DatabaseError) as e:
            if "database is locked" in str(e):
                # time.sleep(0.01)  # If the database is locked, wait a bit and try again
                continue
            else:
                raise  # If it's a different error, re-raise it


# Take in two arrays with the same length, and return the cosine similarity between them
@jit(nopython=True)
def find_cosine_similarity(array1, array2, max_error_percentage=MAX_ERROR_PERCENTAGE):
    error_correction = 0
    # if any element in array1 is not within max_error_percentage difference of the corresponding element in array2,
    # subtract 999999 to the similarity
    for i in range(len(array1)):
        if abs(array1[i] - array2[i]) > max_error_percentage * array1[i]:
            error_correction = -999999

    return (
        np.dot(array1, array2) / (np.linalg.norm(array1) * np.linalg.norm(array2))
    ) + error_correction


# return the index and the cosine similarity of the highest correlation between one array and the 'params' column of the
# database
def find_highest_cosine_similarity_index_and_value(
    array: list, database_object: pd.DataFrame
) -> (int, float):
    # apply the find_cosine_similarity function once and store the results
    cosine_similarities = database_object["params"].apply(
        lambda x: find_cosine_similarity(array, np.array(x))
    )
    return cosine_similarities.idxmax(), cosine_similarities.max()


# Input: the index and the correlation of the highest correlation between one array and the 'params' column of the
# database. Output: if the highest correlation is above the threshold, return the readability of the corresponding
# row. Else, return None
def find_readability_if_above_threshold(
    index: int,
    cosine_similarity: float,
    database_object: pd.DataFrame,
    cosine_similarity_threshold: float = COSINE_SIMILARITY_THRESHOLD,
) -> (list, list):
    if cosine_similarity > cosine_similarity_threshold:
        return database_object["params"][index], database_object["glam_results"][index]
    else:
        return None, None


# Input: params. Output: if the params are close enough to the params in the database, return the readability and
# correlation
def find_the_closest_param_using_cosine_similarity(
    params: list, global_database_object: pd.DataFrame
):
    # check if the database is empty
    if global_database_object.empty:
        return None, None, None
    index, cosine_similarity = find_highest_cosine_similarity_index_and_value(
        params, global_database_object
    )
    closest_pram, closest_glam_results = find_readability_if_above_threshold(
        index, cosine_similarity, global_database_object
    )
    return closest_pram, closest_glam_results, cosine_similarity


def get_result_by_iteration(
    iteration_num: int, database_object: pd.DataFrame
) -> (list, list, list):
    result_row = database_object[database_object["iteration_num"] == iteration_num]
    if not result_row.empty:
        return (
            result_row.iloc[0]["params"],
            result_row.iloc[0]["glam_results"],
            result_row.iloc[0]["readability"],
        )
    else:
        return None, None, None


def rename_the_optimization_database_to_weighted_database(weights: list):

    database_file = (
        "database_"
        + str(reward.CROSSLESSNESS_WEIGHT)
        + "_"
        + str(reward.NORMALIZED_CV_WEIGHT)
        + "_"
        + str(reward.MIN_ANGLE_WEIGHT)
        + ".db"
    )
    try:
        os.rename(DATABASE_PATH, os.path.join("database", database_file))
        print(
            f"\n\n{get_timestamp()}: Optimization with weights {weights} finished. Database saved as {database_file}\n\n"
        )
    except OSError:
        print("Can't rename because the original file " + DATABASE_PATH + " is missing")


def remove_database():
    # remove the database/old_database.db
    try:
        os.remove(DATABASE_PATH)
    except OSError:
        pass


def copy_to_weighted_database(weights):
    # copy the database/old_database.db to database/database_{weights[0]}_{weights[1]}_{weights[2]}.db
    database_file = (
        "database_"
        + str(weights[0])
        + "_"
        + str(weights[1])
        + "_"
        + str(weights[2])
        + ".db"
    )
    shutil.copy(DATABASE_PATH, os.path.join("database", database_file))
    print(
        f"\n\n{get_timestamp()}: Optimization with weights {weights} finished. Database saved as {database_file}\n\n"
    )
    time.sleep(10)


def get_inode_number(file_path: str) -> int:
    return os.stat(file_path).st_ino


if __name__ == "__main__":
    conn = open_optimized_connection(database_path=DATABASE_PATH)
    last_inode_number = get_inode_number(DATABASE_PATH)
    try:
        while True:
            try:
                print(
                    r"""
 $$$$$$\            $$$$$$$\  $$$$$$$\  
$$  __$$\           $$  __$$\ $$  __$$\ 
$$ /  $$ | $$$$$$\  $$ |  $$ |$$ |  $$ |
$$ |  $$ |$$  __$$\ $$ |  $$ |$$$$$$$\ |
$$ |  $$ |$$ /  $$ |$$ |  $$ |$$  __$$\ 
$$ |  $$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |
 $$$$$$  |$$$$$$$  |$$$$$$$  |$$$$$$$  |
 \______/ $$  ____/ \_______/ \_______/ 
          $$ |                          
          $$ |                          
          \__|"""
                )
                # print the datetime
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                current_inode_number = get_inode_number(DATABASE_PATH)
                if current_inode_number != last_inode_number:
                    print("Database is re-created. Re-establishing connection...")
                    conn = open_optimized_connection(database_path=DATABASE_PATH)
                    last_inode_number = current_inode_number
                if DATABASE_READ_TIME is not None:
                    print(
                        "SQL Query Execution Time: "
                        + str(DATABASE_READ_TIME)
                        + " seconds"
                    )
                DATABASE = read_database_file_to_object(
                    conn=conn, lines_to_read=int(DATABASE_PRINTOUT_LINES)
                )
                pretty_print_dataframe(DATABASE)
                time.sleep(1)
                os.system("clear")
            except (sqlite3.OperationalError, pd.errors.DatabaseError):
                # re-establish the connection if it's lost
                print("Database connection lost. Re-establishing...")
                conn = open_optimized_connection(database_path=DATABASE_PATH)
                continue
            except FileNotFoundError:
                print("Database file is removed, waiting it to be re-created...")
                time.sleep(1)
                continue
            except Exception as e:
                raise e
    except KeyboardInterrupt:
        print("\nProgram interrupted by user...")
    except Exception as e:
        raise e
    finally:
        print("Closing database connection...")
        close_connection(conn)
