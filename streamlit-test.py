import pandas as pd
import plotly.graph_objects as go
import numpy as np
import streamlit as st
from src.constants import scatter_palette
from plotly.subplots import make_subplots
import plotly.express as px
from src.usa.constants import racial_label_dict


def get_percentages(data):
    sum_of_values = sum(data.values())
    return {key: 100 * value/sum_of_values for key, value in data.items()}


def get_integer_percentages(data):
    percentages = get_percentages(data)
    fractional_parts = {key: value % 1 for key, value in percentages.items()}
    integer_parts = {key: int(value) for key, value in percentages.items()}
    remaining = 100 - sum(integer_parts.values())
    for key in sorted(fractional_parts, key=fractional_parts.get, reverse=True)[:remaining]:
        integer_parts[key] += 1

    return integer_parts

    # return {k: v for k, v in sorted(integer_parts.items(), key=lambda item: item[1], reverse=True)}


racial_labels = ['white_alone', 'black_alone', 'aian_alone',
                 'asian_alone', 'nhopi_alone', 'hispanic', 'other']
colors = {racial_labels[i]: scatter_palette[i] for i in range(len(racial_labels))}

data_old = {
    'white_alone': 59,
    'black_alone': 20,
    'aian_alone': 10,
    'asian_alone': 10,
    'nhopi_alone': 5,
    'hispanic': 5,
    'other': 25,
}

data_new = {
    'white_alone': 30,
    'black_alone': 15,
    'aian_alone': 10,
    'asian_alone': 0,
    'nhopi_alone': 0,
    'hispanic': 5,
    'other': 20,
}

colors_old = [[i/(len(racial_labels)), scatter_palette[i]] for i in range(len(racial_labels) + 1)]

data_integer_percentages_old = get_integer_percentages(data_old)
data_integer_percentages_new = get_integer_percentages(data_new)

n = 10
color_values_old = np.zeros((n, n), dtype=float)
color_values_new = np.zeros((n, n), dtype=float)
names = []

i = 0
j = 0
j_state = 0

for racial_label in racial_labels:
    n_items = data_integer_percentages_old[racial_label]
    for _ in range(n_items):
        color_values_old[i, j] = racial_labels.index(racial_label)
        names.append(racial_label)
        if j == n - 1 and j_state == 0:
            i += 1
            j_state = 1 - j_state
        elif j == 0 and j_state == 1:
            i += 1
            j_state = 1 - j_state
        else:
            j = j + ((-1) ** j_state)

i = 0
j = 0
j_state = 0

for racial_label in racial_labels:
    n_items = data_integer_percentages_new[racial_label]
    for _ in range(n_items):
        color_values_new[i, j] = racial_labels.index(racial_label)
        names.append(racial_label)
        if j == n - 1 and j_state == 0:
            i += 1
            j_state = 1 - j_state
        elif j == 0 and j_state == 1:
            i += 1
            j_state = 1 - j_state
        else:
            j = j + ((-1) ** j_state)

# fig = go.Figure()
fig = make_subplots(rows=1, cols=2)

fig.add_trace(
    go.Heatmap(z=color_values_old, xgap=0, ygap=0, colorscale=colors_old, showscale=False, zmin=0, zmax=len(racial_labels),
               customdata=names, hovertemplate='Value: %{customdata}<extra></extra>',
               colorbar=dict(
                   title='Old',
                   tickvals=[0, len(data_old)],
                   ticktext=[0, len(data_old)],
               )),
    row=1, col=1,
)

fig.add_trace(
    go.Heatmap(z=color_values_new, xgap=0, ygap=0, colorscale=colors_old, showscale=False, zmin=0, zmax=len(data_old),
               customdata=names,
               colorbar=dict(
                   title='Old',
                   tickvals=[0, len(data_old)],
                   ticktext=[0, len(data_old)],
               )),
    row=1, col=2,
)

# fig.add_trace(
#     px.imshow(z=color_values_new, xgap=1, ygap=1, colorscale=colors_old, showscale=False, zmin=0, zmax=len(data_old),
#                          customdata=names, hovertemplate='Value: %{customdata}<extra></extra>'),
#     row=1, col=2
# )


# Add scatter plot for the discrete legend
for i in range(len(data_old)):
    fig.add_trace(go.Scatter(
        x=[None], y=[None],  # Dummy data
        mode='markers',
        marker=dict(size=10, color=colors_old[i][1]),
        name=racial_label_dict[i + 1]
    ))


fig.update_layout(yaxis1_scaleanchor="x",
                  yaxis2_scaleanchor="x",
                  xaxis1_showgrid=False,
                  xaxis2_showgrid=False,
                  yaxis1_showgrid=False,
                  yaxis2_showgrid=False,
                  xaxis1_showticklabels=False,
                  xaxis2_showticklabels=False,
                  yaxis1_showticklabels=False,
                  yaxis2_showticklabels=False,
                  legend=dict(
                      orientation='h',
                      yanchor='bottom',
                      y=0.90,
                      xanchor='center',
                      x=0.5
                  ),
                  margin=dict(t=0, l=0, b=0, r=0))

st.plotly_chart(fig, use_container_width=True)

