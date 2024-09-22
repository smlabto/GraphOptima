import graph_tool.draw


def graph_tool_to_pos_list(graphml_file: str, param1: float, param2: float) -> list:
    g = graph_tool.load_graph(graphml_file)
    if not param1 or not param2:
        pos = graph_tool.draw.sfdp_layout(g)
    else:
        pos = graph_tool.draw.sfdp_layout(g, C=param1, r=param2)
    g.vertex_properties["pos"] = pos
    # print(list(pos))
    return list(pos)
