"""
Generate sample graphs using graph_tool library
"""

import graph_tool.generation
import graph_tool.collection
import graph_tool.all as gt
import random
import os
import numpy as np


def generate_graph_with_gt(g, file_name: str = "graph.graphml"):
    # print how many nodes and edges are in the graph
    print("Number of nodes: " + str(g.num_vertices()))
    print("Number of edges: " + str(g.num_edges()))

    # label all parallel edges
    parallel_edges = gt.label_parallel_edges(g)
    gt.remove_labeled_edges(g, parallel_edges)

    # label all self loops
    self_loops = gt.label_self_loops(g)
    gt.remove_labeled_edges(g, self_loops)

    # label all 0 degree nodes
    zero_degree_nodes = []
    for v in g.vertices():
        if v.out_degree() == 0 and v.in_degree() == 0:
            zero_degree_nodes.append(v)

    # remove all 0 degree nodes
    g.remove_vertex(zero_degree_nodes)

    g.save(file_name)
    print(file_name + " is generated")


def prob(a, b):
    if a == b:
        return 0.999
    else:
        return 0.001


if __name__ == "__main__":
    generate_graph_with_gt(
        g=graph_tool.generation.price_network(10000),
        file_name="price_10000nodes.graphml",
    )
    generate_graph_with_gt(
        g=graph_tool.generation.price_network(1000000),
        file_name="price_1000000nodes.graphml",
    )
    g, bm = graph_tool.generation.random_graph(
        2000,
        lambda: np.random.poisson(10),
        directed=False,
        model="blockmodel",
        block_membership=lambda: np.random.randint(10),
        edge_probs=prob,
    )
    generate_graph_with_gt(g=g, file_name="blockmodel_2000nodes_10blocks.graphml")
    g, bm = graph_tool.generation.random_graph(
        200000,
        lambda: np.random.poisson(100),
        directed=False,
        model="blockmodel",
        block_membership=lambda: np.random.randint(100),
        edge_probs=prob,
    )
    generate_graph_with_gt(g=g, file_name="blockmodel_200000nodes_100blocks.graphml")
    generate_graph_with_gt(
        g=graph_tool.generation.complete_graph(30), file_name="complete_30nodes.graphml"
    )
    generate_graph_with_gt(
        g=graph_tool.generation.complete_graph(3000),
        file_name="complete_30000nodes.graphml",
    )
    generate_graph_with_gt(
        g=graph_tool.collection.data["dolphins"], file_name="dolphins.graphml"
    )
    generate_graph_with_gt(
        g=graph_tool.collection.data["email-Enron"], file_name="email-Enron.graphml"
    )
    generate_graph_with_gt(
        g=graph_tool.collection.data["polblogs"], file_name="polblogs.graphml"
    )
