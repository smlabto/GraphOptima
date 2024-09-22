import graph_tool.all as gt
import re
import pandas as pd


def pos_df_to_graph(graphml, pos_df: pd.DataFrame, name: str, resolution: int = 1000):
    g = graphml
    # given a position dataframe pos_df with columns ['vertex', 'x', 'y'], create a vector<double> property map of
    # positions 'pos'
    pos = g.new_vertex_property("vector<double>")

    # if the vertex name is a string like n1234, convert it to integer 1234
    pos_df["vertex"] = pos_df["vertex"].apply(lambda x: int(re.sub("[^0-9]", "", x)))

    for i in range(len(pos_df)):
        pos[pos_df.iloc[i]["vertex"]] = [pos_df.iloc[i]["x"], pos_df.iloc[i]["y"]]
    g.vertex_properties["pos"] = pos

    gt.graph_draw(
        g, pos=pos, output_size=(resolution, resolution), output=name + ".png"
    )
