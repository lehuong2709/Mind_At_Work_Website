import streamlit as st
import plotly.express as px
import pandas as pd

# Sample data
data = {
    'X': [1, 2, 3, 4, 5],
    'Y1': [2, 3, 5, 7, 11],
    'Y2': [1, 4, 9, 16, 25],
    'Y3': [0, 1, 0, 1, 0],
    'group': ['Group1', 'Group2', 'Group3', 'Group4', 'Group1']
}

CB_color_cycle = ['#377eb8', '#ff7f00', '#4daf4a',
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Create a scatter plot with automatic marker shapes and colors
fig = px.scatter(df, x='X', y='Y1', color='group', symbol='group', size='Y1',
                 color_discrete_sequence=CB_color_cycle,
                 title='Scatter Plot with Automatic Marker Shapes and Colors',
                 labels={'Y1': 'Y-axis label', 'X': 'X-axis label'},
                 hover_data=['X', 'Y1', 'group'])

# Streamlit app
st.title('Streamlit App with Plotly Scatter Plot')

# Plot the Plotly figure
st.plotly_chart(fig)
