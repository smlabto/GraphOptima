import scipy.io
import plotly
import dash
from dash import dcc
from dash import html
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
from skimage import io
import numpy as np
import re
from dash.dependencies import Input, Output, State

# Load the data from the .mat file
mat_data = scipy.io.loadmat(
    "youtube_scalarization_cuGraph_500_budget_6_generator_2_evaluator_paramRange_1000.mat"
)
# remove all the unnecessary attributes
mat_data.pop("__header__")
mat_data.pop("__version__")
mat_data.pop("__globals__")

# flatting the weight attribute into simply a list of lists
weight_list_of_lists = []
for i in range(len(mat_data["weights"])):
    list_to_append = mat_data["weights"][i]
    # convert the list to a normal list from a numpy array
    list_to_append = list(list_to_append)
    weight_list_of_lists.append(list_to_append)

mat_data["weights"] = weight_list_of_lists


# make a list of dictionaries, with each dictionary representing a data point with all fields from mat_data
def make_list_of_dicts(mat_data):
    list_of_dicts = []
    list_of_all_unique_weights = []
    all_attributes_list = list(mat_data.keys())
    for i in range(len(mat_data["crosslessness"][0])):
        observations = {}
        for attribute in all_attributes_list:
            # if the current attribute is weights, check if it is already in the list_of_all_unique_weights
            if attribute == "weights":
                observations[attribute] = mat_data[attribute][i]
                if observations[attribute] not in list_of_all_unique_weights:
                    list_of_all_unique_weights.append(observations[attribute])

                continue

            observations[attribute] = mat_data[attribute][0][i]

            # add the attributes associated for plotly display
            observations["if_display"] = True

            # add the color attribute, assign plotly default color blue
            observations["color"] = plotly.colors.DEFAULT_PLOTLY_COLORS[0]

        list_of_dicts.append(observations)
    return list_of_dicts, list_of_all_unique_weights


# make a list of colors, each color is associated with a unique weight
def make_list_of_colors(list_of_all_unique_weights: list):
    list_of_colors_weight_dict = []
    num_weights = len(list_of_all_unique_weights)

    # Use a continuous color scale (e.g., Viridis)
    color_scale = px.colors.sequential.Viridis

    # Generate colors by sampling the color scale
    for i, weight in enumerate(list_of_all_unique_weights):
        # Normalize the index to the range of the color scale
        color_index = int(np.floor(i / num_weights * (len(color_scale) - 1)))
        color = color_scale[color_index]
        list_of_colors_weight_dict.append({"color": color, "weight": weight})

    return list_of_colors_weight_dict


# update the color attribute of each data point in the list_of_dicts
def update_color_attribute(list_of_dicts: list, list_of_colors_weight_dict: list):
    for i in range(len(list_of_dicts)):
        for j in range(len(list_of_colors_weight_dict)):
            if list_of_dicts[i]["weights"] == list_of_colors_weight_dict[j]["weight"]:
                list_of_dicts[i]["color"] = list_of_colors_weight_dict[j]["color"]

    return list_of_dicts


# reset the figure by resetting the field of list_of_dicts to its original state
def reset_list_of_observation_dict_attr(
    list_of_dicts: list, list_of_colors_weight_dict: list
):
    for i in range(len(list_of_dicts)):
        list_of_dicts[i]["if_display"] = True

    list_of_dicts = update_color_attribute(list_of_dicts, list_of_colors_weight_dict)
    return list_of_dicts


# Parse the log file and return a list of dicts with the best params for each weight group
def parse_log_file(file_path: str):
    with open(file_path, "r") as file:
        lines = file.readlines()

    data_list = []
    weight_pattern = re.compile(r"Weights: ([\d.]+) ([\d.]+) ([\d.]+)")
    param_pattern = re.compile(
        r"The params that produced the best readability in the optimizer is :\[(.*)\]"
    )

    current_weight = None
    for line in lines:
        weight_match = weight_pattern.search(line)
        param_match = param_pattern.search(line)

        if weight_match:
            current_weight = tuple(map(float, weight_match.groups()))
        elif param_match and current_weight:
            params = list(map(float, param_match.group(1).split()))
            data_list.append({"weight": current_weight, "best_params": params})
            current_weight = None  # Reset current_weight for the next match

    return data_list


def is_close(list1: list, list2: list, tol: float = 1e-5):
    """
    Checks if two lists are approximately equal within a given tolerance.

    :param list1: First list of values.
    :param list2: Second list of values.
    :param tol: Tolerance for comparison.
    :return: True if lists are approximately equal, False otherwise.
    """
    if len(list1) != len(list2):
        return False

    for a, b in zip(list1, list2):
        if abs(a - b) > tol:
            return False

    return True


# Hide all the non-optimal points for each weight group
def hide_non_optimal_points(
    list_of_observation_dicts: list, best_param_found_for_each_weight_group: list
):
    # flatten the best param for each weight group into a dictionary of weight: best_params
    best_param_dict = {}
    for i in range(len(best_param_found_for_each_weight_group)):
        best_param_dict[best_param_found_for_each_weight_group[i]["weight"]] = (
            best_param_found_for_each_weight_group[i]["best_params"]
        )

    # iterate through each observation in the list_of_observation_dicts
    for i in range(len(list_of_observation_dicts)):
        # extract the params of gravity, scaling_factor, iteration_number
        gravity = list_of_observation_dicts[i]["gravity"]
        scaling_factor = list_of_observation_dicts[i]["scaling_factor"]
        iteration_number = list_of_observation_dicts[i]["max_iter"]
        param_list = [scaling_factor, gravity, iteration_number]

        # convert the weight list to a tuple
        current_weight = tuple(list_of_observation_dicts[i]["weights"])

        # check if the current observation's params is approximately the same as the best params for its weight group
        if not is_close(param_list, best_param_dict[current_weight]):
            list_of_observation_dicts[i]["if_display"] = False

    return list_of_observation_dicts


# Function to add scatter plot to the figure
def add_scatter_plot_to_fig(fig, list_of_observation_dicts: list):
    # Filter the list of dicts to include only those with 'if_display' set to True
    # list_of_observation_dicts here is a local variable, so it won't affect the global variable length
    list_of_observation_dicts = [
        i for i in list_of_observation_dicts if i["if_display"]
    ]

    # Add the 3D scatter plot to the first subplot
    scatter3d = go.Scatter3d(
        x=[i["crosslessness"] for i in list_of_observation_dicts],
        y=[i["normalized_edge_length_variance"] for i in list_of_observation_dicts],
        z=[i["min_angle"] for i in list_of_observation_dicts],
        hovertext=[
            "Crosslessness: {}<br>Min Angle: {}<br>Normalized Edge Length Variance: {}<br>"
            "Gravity: {}<br>Scaling Factor: {}<br>Iteration: {}".format(
                i["crosslessness"],
                i["min_angle"],
                i["normalized_edge_length_variance"],
                i["gravity"],
                i["scaling_factor"],
                i["iteration_number"],
            )
            for i in list_of_observation_dicts
        ],
        mode="markers",
        marker={
            "size": 5,
            "color": [i["color"] for i in list_of_observation_dicts],
            "opacity": 0.8,
        },
    )
    fig.add_trace(scatter3d, row=1, col=1)

    # Modify the scatter plot creation to include a trace for each weight
    for color_info in list_of_colors_weight_dict:
        weight = color_info["weight"]
        color = color_info["color"]

        # Filter the list of dicts for points with the current weight
        filtered_dicts = [
            d for d in list_of_observation_dicts if d["weights"] == weight
        ]

        # Add a trace for each unique weight
        fig.add_trace(
            go.Scatter3d(
                x=[d["crosslessness"] for d in filtered_dicts],
                y=[d["normalized_edge_length_variance"] for d in filtered_dicts],
                z=[d["min_angle"] for d in filtered_dicts],
                hovertext=[
                    "Crosslessness: {}<br>Min Angle: {}<br>Normalized Edge Length Variance: {}<br>"
                    "Gravity: {}<br>Scaling Factor: {}<br>Iteration: {}".format(
                        d["crosslessness"],
                        d["min_angle"],
                        d["normalized_edge_length_variance"],
                        d["gravity"],
                        d["scaling_factor"],
                        d["iteration_number"],
                    )
                    for d in filtered_dicts
                ],
                mode="markers",
                marker=dict(size=5, color=color, opacity=0.8),
                name=str(weight),  # Legend entry
            ),
            row=1,
            col=1,
        )

    # Configure the scene for the 3D scatter plot
    fig.update_layout(
        scene=dict(
            xaxis_title="crosslessness",
            yaxis_title="normalized_edge_length_variance",
            zaxis_title="min_angle",
        ),
        scene_aspectmode="cube",
    )


# Function to add images to the figure
def add_images_to_fig(image_path1: str, image_path2: str, image_path3: str, fig, app):
    img1 = io.imread(image_path1)
    img2 = io.imread(image_path2)
    img3 = io.imread(image_path3)

    # Create image plots and add them to the subplots
    image_fig1 = px.imshow(img1)
    image_fig2 = px.imshow(img2)
    image_fig3 = px.imshow(img3)

    for trace in image_fig1.data:
        fig.add_trace(trace, row=2, col=1)

    for trace in image_fig2.data:
        fig.add_trace(trace, row=2, col=2)

    for trace in image_fig3.data:
        fig.add_trace(trace, row=2, col=3)

    app.layout = html.Div([dcc.Graph(figure=fig)])

    fig.update_layout(height=1020, width=1200)


# output the formatted caption for the image
def extract_weight_from_file_name(file_name: str):
    weight_pattern = re.compile(
        r"optimized_layout_weighted_(\d.\d)_(\d.\d)_(\d.\d).png"
    )
    weight_match = weight_pattern.search(file_name)
    if weight_match:
        weight = weight_match.groups()
        weight = [float(i) for i in weight]
        return "Weights: {}".format(weight)
    else:
        return "Weights: None"


# create a plotly app
app = dash.Dash(__name__)
server = app.server

# Replace 'path_to_log_file.log' with the actual path to your log file
log_file_path = "verify_optimized_params_output.log"
best_param_found_for_each_weight_group = parse_log_file(log_file_path)

list_of_observation_dicts, list_of_all_unique_weights = make_list_of_dicts(mat_data)
list_of_colors_weight_dict = make_list_of_colors(list_of_all_unique_weights)
list_of_observation_dicts = update_color_attribute(
    list_of_observation_dicts, list_of_colors_weight_dict
)

image_path1 = "optimized_layout_weighted_1.0_0.0_0.0.png"
image_path2 = "optimized_layout_weighted_0.0_1.0_0.0.png"
image_path3 = "optimized_layout_weighted_0.0_0.0_1.0.png"

# Create the initial figure with scatter plot and images
fig = make_subplots(
    rows=2,
    cols=3,
    specs=[
        [{"type": "scatter3d", "colspan": 3}, None, None],
        [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
    ],
    subplot_titles=(
        "3D Scatter Plot",
        extract_weight_from_file_name(image_path1),
        extract_weight_from_file_name(image_path2),
        extract_weight_from_file_name(image_path3),
    ),
    vertical_spacing=0.05,
    horizontal_spacing=0.05,
)

# Add scatter plot and images to the figure
add_scatter_plot_to_fig(fig, list_of_observation_dicts)
add_images_to_fig(image_path1, image_path2, image_path3, fig, app)


# Convert tuple to string for dropdown value
def tuple_to_string(tup):
    return ",".join(map(str, tup))


app.layout = html.Div(
    [
        dcc.Dropdown(
            id="weight-selection-dropdown",
            options=[
                {"label": str(weight), "value": tuple_to_string(weight)}
                for weight in list_of_all_unique_weights
            ],
            multi=True,
            placeholder="Select up to 3 weights",
        ),
        # Add a button for rendering the selected weights
        html.Button("Render Selected Weights", id="render-button", n_clicks=0),
        # Div for buttons
        html.Div(
            [
                html.Button("Reset", id="reset-button", n_clicks=0),
                html.Button("Hide Non-Optimal", id="hide-button", n_clicks=0),
            ],
            style={"text-align": "center", "margin-bottom": "10px"},
        ),
        # Graph
        dcc.Graph(id="3d-scatter-plot", figure=fig),
    ]
)


@app.callback(
    Output("3d-scatter-plot", "figure"),
    [
        Input("render-button", "n_clicks"),
        Input("reset-button", "n_clicks"),
        Input("hide-button", "n_clicks"),
    ],
    [State("weight-selection-dropdown", "value")],
)
def update_figure_callback(render_clicks, reset_clicks, hide_clicks, selected_weights):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = "No clicks yet"
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    updated_list_of_observation_dicts = list_of_observation_dicts.copy()

    if button_id == "reset-button":
        updated_list_of_observation_dicts = reset_list_of_observation_dict_attr(
            list_of_observation_dicts, list_of_colors_weight_dict
        )
    elif button_id == "hide-button":
        updated_list_of_observation_dicts = hide_non_optimal_points(
            list_of_observation_dicts, best_param_found_for_each_weight_group
        )

    # Logic for handling the rendering of images based on selected weights
    image_paths = [
        "optimized_layout_weighted_1.0_0.0_0.0.png",
        "optimized_layout_weighted_0.0_1.0_0.0.png",
        "optimized_layout_weighted_0.0_0.0_1.0.png",
    ]
    if button_id == "render-button" and selected_weights:
        selected_weights = [
            tuple(map(float, weight.split(","))) for weight in selected_weights
        ]
        header = "optimized_layout_weighted_"
        image_paths = [
            header + "_".join(map(str, weight)) + ".png" for weight in selected_weights
        ]
        image_paths += ["placeholder.png"] * (3 - len(image_paths))

    # Rebuild the scatter plot and images
    new_fig = make_subplots(
        rows=2,
        cols=3,
        specs=[
            [{"type": "scatter3d", "colspan": 3}, None, None],
            [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
        ],
        subplot_titles=(
            "3D Scatter Plot",
            *[extract_weight_from_file_name(path) for path in image_paths],
        ),
        vertical_spacing=0.05,
        horizontal_spacing=0.05,
    )

    add_scatter_plot_to_fig(new_fig, updated_list_of_observation_dicts)
    add_images_to_fig(*image_paths, new_fig, app)
    return new_fig


if __name__ == "__main__":
    # # test the hide non-optimal points function
    # list_of_observation_dicts = hide_non_optimal_points(list_of_observation_dicts,
    #                                                     best_param_found_for_each_weight_group)
    #
    # # filter the list_of_observation_dicts to only include the points with if_display set to True
    # list_of_observation_dicts = [i for i in list_of_observation_dicts if i['if_display']]

    # print(list_of_observation_dicts)
    # for i in list_of_observation_dicts:
    #     print(i)

    app.run_server(debug=True)
    # pass
