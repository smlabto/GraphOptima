from utils import get_db_files
import scipy.io
import numpy as np
import multiprocessing as mp
from numba import njit, prange
import optimization_database
import matplotlib.pyplot as plt


@njit
def dominance(a: list, b: list) -> bool:
    """
    This function receives two solutions a and b and returns True if a dominates b and False otherwise.
    """
    return np.all(
        np.array([a[0] >= b[0], a[1] <= b[1], a[2] >= b[2]])
    ) and not np.array_equal(a, b)


@njit
def nds_sort(points: list) -> list:
    """
    This function receives a list of points and returns a list of indices of the non-dominated points.
    Optimized to reduce unnecessary comparisons.
    """
    n_points = len(points)
    dominated = set()
    non_dominated = []

    # Sort points by one criterion (e.g., the first objective)
    sorted_indices = np.argsort(points[:, 0])

    for i in prange(n_points):
        if sorted_indices[i] in dominated:
            continue

        for j in prange(i + 1, n_points):
            if dominance(points[sorted_indices[i]], points[sorted_indices[j]]):
                dominated.add(sorted_indices[j])
            elif dominance(points[sorted_indices[j]], points[sorted_indices[i]]):
                dominated.add(sorted_indices[i])
                break

        if sorted_indices[i] not in dominated:
            non_dominated.append(sorted_indices[i])

    return non_dominated


def process_data(file_name: str) -> list:
    data = []
    conn = optimization_database.open_optimized_connection(file_name)
    df = optimization_database.read_database_file_to_object(conn=conn, echo=True)
    for index, row in df.iterrows():
        try:
            glam_results = row["glam_results"]
            crosslessness = float(glam_results[0])
            normalized_edge_length_variance = float(glam_results[3])
            min_angle = float(glam_results[4])

            if normalized_edge_length_variance < 0:
                continue

            scaling_factor = row["params"][0]
            gravity = row["params"][1]
            max_iter = row["params"][2]
            iteration_num = row["iteration_num"]

            readability_weight = row["metadata"]["readability_calculation_weight_list"]
            weights = (
                readability_weight[0],
                readability_weight[3],
                readability_weight[4],
            )

            # check if the crosslessness, normalized_edge_length_variance or min_angle is between 0 and 1, if not, skip
            if crosslessness < 0 or crosslessness > 1:
                continue
            if (
                normalized_edge_length_variance < 0
                or normalized_edge_length_variance > 1
            ):
                continue
            if min_angle < 0 or min_angle > 1:
                continue

            data.append(
                {
                    "crosslessness": crosslessness,
                    "normalized_edge_length_variance": normalized_edge_length_variance,
                    "min_angle": min_angle,
                    "scaling_factor": scaling_factor,
                    "gravity": gravity,
                    "max_iter": max_iter,
                    "weights": weights,
                    "iteration_num": iteration_num,
                }
            )
        except:
            pass
    optimization_database.close_connection(conn=conn)
    return data


def plot_distributions(combined_data, nds_data, parameter, axs, idx, title):
    # Calculate histograms
    combined_hist, bins = np.histogram(
        [d[parameter] for d in combined_data], bins="auto", density=True
    )
    nds_hist, _ = np.histogram(
        [d[parameter] for d in nds_data], bins=bins, density=True
    )

    # Normalize NDS histogram to ensure its density is not higher than combined data
    nds_hist = np.minimum(nds_hist, combined_hist)

    # Plot histograms
    axs[idx].bar(
        bins[:-1],
        combined_hist,
        width=np.diff(bins),
        align="edge",
        alpha=0.5,
        label="Combined data",
        color="blue",
    )
    axs[idx].bar(
        bins[:-1],
        nds_hist,
        width=np.diff(bins),
        align="edge",
        alpha=0.5,
        label="NDS data",
        color="red",
    )
    axs[idx].set_title(title)
    axs[idx].set_xlabel(parameter)
    axs[idx].set_ylabel("Density")
    axs[idx].legend(loc="upper right")


if __name__ == "__main__":
    db_files = get_db_files()
    pool = mp.Pool(mp.cpu_count())
    combined_data = pool.map(process_data, db_files)
    pool.close()

    combined_data = [item for sublist in combined_data for item in sublist]

    print(combined_data)

    print("Number of data points: ", len(combined_data))

    mat_data = {
        "crosslessness": [d["crosslessness"] for d in combined_data],
        "normalized_edge_length_variance": [
            d["normalized_edge_length_variance"] for d in combined_data
        ],
        "min_angle": [d["min_angle"] for d in combined_data],
        "scaling_factor": [d["scaling_factor"] for d in combined_data],
        "gravity": [d["gravity"] for d in combined_data],
        "max_iter": [d["max_iter"] for d in combined_data],
        "weights": [d["weights"] for d in combined_data],
        "iteration_number": [d["iteration_num"] for d in combined_data],
    }

    # FILE_NAME = "httpst.mechatDeepState_scalarization_cuGraph_500_budget_6_generator_2_evaluator_paramRange_1000"
    FILE_NAME = "database/result.mat"
    # get the user input of the filename. if no input then by default it is result.mat
    FILE_NAME_input = input(
        "Enter the name of the file to save the data (default: database/result.mat): "
    )
    if FILE_NAME_input:
        FILE_NAME = FILE_NAME_input

    print("Saving......")

    scipy.io.savemat(FILE_NAME + ".mat", mat_data)

    # print("Saving the second data to .mat file......")

    # # Below are code to create a dominated sorted data
    # # Create a matrix from the DataFrame
    # matrix = np.array(
    #     [
    #         mat_data["crosslessness"],
    #         mat_data["normalized_edge_length_variance"],
    #         mat_data["min_angle"],
    #     ]
    # ).T
    #
    # # Use non-dominated sorting to get the indices of non-dominated points
    # pareto_front_indices = nds_sort(matrix)
    #
    # print("Non-dominated sorting completed.")
    #
    # # Use these indices to filter your combined_data
    # nds_data = [combined_data[i] for i in pareto_front_indices]
    #
    # # Now save this non-dominated sorted data into another .mat file
    # mat_nds_data = {
    #     "crosslessness": [d["crosslessness"] for d in nds_data],
    #     "normalized_edge_length_variance": [
    #         d["normalized_edge_length_variance"] for d in nds_data
    #     ],
    #     "min_angle": [d["min_angle"] for d in nds_data],
    #     "scaling_factor": [d["scaling_factor"] for d in nds_data],
    #     "gravity": [d["gravity"] for d in nds_data],
    #     "max_iter": [d["max_iter"] for d in nds_data],
    #     "weights": [d["weights"] for d in nds_data],
    #     "iteration_number": [d["iteration_num"] for d in nds_data],
    # }
    #
    # scipy.io.savemat(FILE_NAME + "_nds.mat", mat_nds_data)
    #
    # # Plotting code
    # fig, axs = plt.subplots(3, figsize=(10, 10))
    #
    # plot_distributions(
    #     combined_data, nds_data, "scaling_factor", axs, 0, "Scaling Factor Distribution"
    # )
    # plot_distributions(
    #     combined_data, nds_data, "gravity", axs, 1, "Gravity Distribution"
    # )
    # plot_distributions(
    #     combined_data, nds_data, "max_iter", axs, 2, "Max Iteration Distribution"
    # )
    #
    # # save the plot to a file
    # plt.savefig(FILE_NAME + ".png", dpi=300)
    #
    # plt.tight_layout()
    # plt.show()
