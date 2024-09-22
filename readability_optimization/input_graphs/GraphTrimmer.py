import argparse
import graph_tool.all as gt
import pandas as pd
from collections import defaultdict


def filter_graph(input_file, output_file, threshold, filter_type):
    # Load the graph
    print("Loading the graph...")
    g = gt.load_graph_from_csv(
        file_name=input_file,
        directed=True,
        eprop_types=None,
        eprop_names=None,
        hashed=True,
        hash_type="string",
        skip_first=True,
        strip_whitespace=True,
        ecols=(0, 1),
        csv_options={"delimiter": ",", "quotechar": '"'},
    )

    if filter_type == "reciprocal":
        print("Calculating reciprocal interactions...")
        # Initialize the property and dictionary
        reciprocal_interactions_by_dict = g.new_edge_property("int")
        interaction_counts = defaultdict(int)

        # Populate the dictionary with interaction counts
        for edge in g.edges():
            src = edge.source()
            tgt = edge.target()
            interaction_counts[(src, tgt)] += 1

        # Calculate the reciprocal interactions
        for edge in g.edges():
            src = edge.source()
            tgt = edge.target()
            reciprocal_interactions_by_dict[edge] = min(
                interaction_counts[(src, tgt)], interaction_counts[(tgt, src)]
            )

        # Filter edges based on a reciprocal interaction threshold
        edges_to_keep = [
            (e.source(), e.target())
            for e in g.edges()
            if reciprocal_interactions_by_dict[e] >= threshold
        ]

        # filter out the vertex to add by using a reciprocal interaction threshold
        vertices_to_keep = set()
        for edge in edges_to_keep:
            vertices_to_keep.add(edge[0])
            vertices_to_keep.add(edge[1])
        vertices_to_remove = set(g.get_vertices()) - vertices_to_keep

        print("Filtering the graph...")
        # Create a new graph and add the filtered edges
        new_g = g.copy()
        new_g.clear_edges()
        # remove the vertices
        new_g.remove_vertex(vertices_to_remove, fast=True)
        new_g.add_edge_list(edges_to_keep)

    else:
        print("Calculating degree...")
        # Calculate degree based on a filter type
        if filter_type == "in":
            degree = g.get_in_degrees(g.get_vertices())
        elif filter_type == "out":
            degree = g.get_out_degrees(g.get_vertices())
        elif filter_type == "total":
            degree = g.get_total_degrees(g.get_vertices())
        else:
            raise ValueError(
                "Invalid filter type. Use 'reciprocal', 'in', 'out', or 'total'."
            )

        # Filter vertices based on a degree threshold
        vertices_to_keep = [v for v in g.vertices() if degree[v] >= threshold]
        vertices_to_remove = set(g.get_vertices()) - set(vertices_to_keep)

        edges_to_keep = [
            (e.source(), e.target())
            for e in g.edges()
            if e.source() in vertices_to_keep and e.target() in vertices_to_keep
        ]

        print("Filtering the graph...")

        # Create a new graph and add the filtered edges
        new_g = g.copy()
        new_g.clear_edges()
        # remove the vertices
        new_g.remove_vertex(vertices_to_remove, fast=True)
        new_g.add_edge_list(edges_to_keep)

    # Save the filtered graph
    print("Saving the filtered graph...")
    # read the csv into a pandas dataframe
    df = pd.read_csv(input_file, engine="pyarrow")
    # get the columns
    columns = df.columns

    # get the names of vertices to keep
    vertices_to_keep = set()
    for edge in new_g.edges():
        vertices_to_keep.add(new_g.vp.name[edge.source()])
        vertices_to_keep.add(new_g.vp.name[edge.target()])

    # filter the dataframe by the vertices
    df_filtered = df[
        df["source"].isin(vertices_to_keep) & df["target"].isin(vertices_to_keep)
    ]
    df_filtered = pd.DataFrame(df_filtered, columns=columns)
    # save the filtered dataframe
    df_filtered.to_csv(output_file, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="GraphTrimmer: Filter a graph based on reciprocal interactions or degree"
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input CSV file (Gephi compliance, with 'source' and 'target' columns)",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output CSV file (Gephi compliance, with 'source' and 'target' columns)",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        required=True,
        help="Minimum <filter_type> degree for keeping the vertices.",
    )
    parser.add_argument(
        "-f",
        "--filter_type",
        choices=["reciprocal", "in", "out", "total"],
        required=True,
        help="Type of filtering",
    )

    args = parser.parse_args()

    filter_graph(args.input, args.output, args.threshold, args.filter_type)


if __name__ == "__main__":
    main()
