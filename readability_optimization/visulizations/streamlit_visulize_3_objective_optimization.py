import scipy.io
import streamlit as st
import pandas as pd
from streamlit_plotly_events import plotly_events
import plotly.graph_objects as go
import plotly.express as px


# take the user input of the mat file
mat_file = input("Enter the mat file path: ")

# Load the data from the .mat file
mat_data = scipy.io.loadmat(mat_file)
# remove all the unnecessary attributes
mat_data.pop("__header__")
mat_data.pop("__version__")
mat_data.pop("__globals__")

# extract the keys
keys = list(mat_data.keys())

for key in keys:
    if key != "weights":
        mat_data[key] = mat_data[key][0]
    else:
        mat_data[key] = mat_data[key].tolist()

# add columns to the dataframe one by one
df = pd.DataFrame()
for key in keys:
    df[key] = mat_data[key]

# extract all unique weights
df["weight_str"] = df["weights"].apply(lambda x: str(x))
unique_weights = df["weight_str"].unique()
df["color"] = df["weight_str"].apply(lambda x: unique_weights.tolist().index(x))

# generate unique_weights number of RGB colors
colors = px.colors.qualitative.Light24
colors = [colors[i] for i in range(len(unique_weights))]
df["color"] = df["color"].apply(lambda x: colors[x])

# # create a scatter plot
# scatter = go.Scatter3d(
#     x=df["crosslessness"],
#     y=df["normalized_edge_length_variance"],
#     z=df["min_angle"],
#     mode="markers",
#     marker=dict(color=df["color"]),
#     showlegend=True,
# )
# fig = go.Figure(scatter)


traces = []

# add trace for each unique color
for weight in unique_weights:
    df_weight = df[df["weight_str"] == weight]
    hover_texts = []
    for i in range(len(df_weight)):
        hover_text = ""

        # add weight
        hover_text += f"weight: {df_weight['weights'].iloc[i]}<br>"
        # add parameters
        for key in keys:
            if key != "weights":
                hover_text += f"{key}: {df_weight[key].iloc[i]}<br>"
        hover_texts.append(hover_text)

    trace = go.Scatter3d(
        x=df_weight["crosslessness"],
        y=df_weight["normalized_edge_length_variance"],
        z=df_weight["min_angle"],
        mode="markers",
        marker=dict(color=df_weight["color"]),
        showlegend=True,
        name=weight,
        hovertext=hover_texts,
        hoverinfo="text",
    )
    traces.append(trace)

fig = go.Figure(
    traces,
    layout=go.Layout(
        uirevision="foo",
        title="3D Scatter Plot of Readability Optimization",
        scene=dict(
            xaxis_title="crosslessness",
            yaxis_title="normalized_edge_length_variance",
            zaxis_title="min_angle",
            aspectmode="cube",
        ),
    ),
)

# st.plotly_chart(fig, use_container_width=True)

# fig = go.Figure(scatter)

# fig.update_scenes(aspectmode="cube")

# convert scatter to plotly.graph_objs.Figure

selected_points = plotly_events(fig)

# get the 125 line of df
if selected_points != []:
    corresponding_df = df[
        (df["crosslessness"] == float(selected_points[0]["x"]))
        & (df["normalized_edge_length_variance"] == float(selected_points[0]["y"]))
    ]
    corresponding_weights = corresponding_df["weights"]
    # extract the weight list from the corresponding_weights
    corresponding_weights = corresponding_weights.tolist()
    corresponding_weights = corresponding_weights[0]
    # convert the float list to a _ seperated string
    corresponding_weights_str = "_".join([str(i) for i in corresponding_weights])
    st.image("optimized_layout_weighted_" + corresponding_weights_str + ".png")

    # st.write(corresponding_weights)
    st.markdown(corresponding_df.to_markdown())
    # st.write(float(selected_points[0]["x"]))
    # st.write(float(selected_points[0]["y"]))

if __name__ == "__main__":
    pass
