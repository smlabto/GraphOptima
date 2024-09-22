"""
Visualizing the pareto front scatter plot of optimizing 3 readability measurements
Input: a mat file generated from `make_mat.py`
Output: a 3D scatter plot of readability optimization using plotly
"""

import chart_studio.plotly as py
import plotly.graph_objects as go
import scipy

# read mat data
mat = scipy.io.loadmat(
    "conspiracy_Aug-9_Aug-31_scalarization_cuGraph_500_budget_6_generator_2_evaluator_paramRange_100000.mat"
)

# delete the __header__ and __version__ and __globals__ field
del mat["__header__"]
del mat["__version__"]
del mat["__globals__"]

# get the keys
keys = list(mat.keys())

# names of the layout parameters (indepedent variables)
parameters_keys = ["scaling_factor", "gravity", "max_iter"]
parameters = [mat[key] for key in parameters_keys]

# names of the readability measurements (dependent variables)
readability_keys = [
    key for key in keys if key != "weights" and key not in parameters_keys
]
readabilities = [mat[key] for key in readability_keys]

# weights are the node category
weights = mat["weights"]


num_layouts = len(weights)
num_readability_measurements = len(readabilities)
num_parameters = len(parameters)

# turn a weight list into a list of color
colors = []
already_seen_weights = []
color_counter = 0

# assign a color counter to each unique weight
for i in range(len(weights)):
    already_seen = False
    for j in range(len(already_seen_weights)):
        if (weights[i] == already_seen_weights[j]).all() == True:
            already_seen = True
            break
    if not already_seen:
        already_seen_weights.append(weights[i])
        color_counter += 1
    colors.append(color_counter)


# make hover text for each node
hover_texts = []
for i in range(num_layouts):
    # add parameters
    hover_text = ""
    # add weight
    hover_text += f"weight: {weights[i]}<br>"
    for j in range(num_parameters):
        hover_text += f"{parameters_keys[j]}: {parameters[j][0][i]}<br>"
    # add readability measurements
    for j in range(num_readability_measurements):
        hover_text += f"{readability_keys[j]}: {readabilities[j][0][i]}<br>"
    hover_texts.append(hover_text)

# plot the 3D scatter plot, use readability measurements as x, y, z axis, weight as color, readability as properties
fig = go.Figure(
    data=go.Scatter3d(
        x=readabilities[0][0],
        y=readabilities[1][0],
        z=readabilities[2][0],
        mode="markers",
        marker=dict(
            color=colors,
            colorscale="Viridis",
            opacity=0.8,
        ),
        hovertext=hover_texts,
        hoverinfo="text",
    )
)

# add axis labels
fig.update_layout(
    scene=dict(
        xaxis_title="crosslessness",
        yaxis_title="normalized_edge_length_variance",
        zaxis_title="min_angle",
    )
)

# add title
fig.update_layout(title="3D scatter plot of readability optimization")

# show the figure
fig.show()

# # show the figure on Chart Stdio
# py.plot(fig, filename='3D scatter plot of readability optimization')


if __name__ == "__main__":
    pass
