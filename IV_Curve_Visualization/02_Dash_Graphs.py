"""
File to aid in graphing IV Curves along with their power values. Also a useful way to learn Dash and Plotly, following
along with the Plotly/Dash Tutorials here: https://dash.plotly.com/interactive-graphing

This initial file will be the minimum viable product that I'd write if everything is due yesterday and we just need
the bare minimum that will help us visualize/understand the data. Further work will include a nicely formatted version
(ideally with more features).

Goal:
    * Row 1, full width: Dropdown for which mppt you want to plot
    * Row 2, left: Graph of power vs time for that mppt (each point corresponds to an IV Curve)
    * Row 2, right: Graph of IV Curve, selected by which datapoint you've hovered over most recently

References:
    * https://stackoverflow.com/questions/739654/how-to-make-function-decorators-and-chain-them-together/1594484#1594484
    * https://dash.plotly.com/basic-callbacks  (part of the plotly/dash tutorials)

Author: John Stayner
2020-12-30

"""

# Imports
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

#### Data Entry/Variables

# Load IV Curves
path_iv = 'data/sundae_day_5_iv_curves.xlsx'
iv_curves = pd.read_excel(path_iv)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Get Isc, Voc, and Pmax from each IV Curve (Last thing we need to do before making this work)
iv_params = iv_curves \
    .groupby(['mppt_id', 'curve_num']) \
    .aggregate({'time': np.min, 'current': np.max, 'voltage': np.max, 'power': np.max}) \
    .reset_index()

# Plot IV Curves

app = dash.Dash(external_stylesheets=external_stylesheets)  # Make the main app

app.layout = html.Div([
    # MPPT Dropdown
    html.Div(
        [html.Div(['MPPT ID: ', dcc.Dropdown(
            id='mppt-dropdown',
            options=[{'label': i, 'value': i} for i in iv_curves['mppt_id'].unique()],
            value='A0'
            )]),
        html.Div(['Maximum Voltage (V) for IV Graph: ', dcc.Input(id='vmax-input', type='text', value='40')]),
        html.Div(['Maximum Current (A) for IV Graph: ', dcc.Input(id='imax-input', type='text', value='7')])
        ], style={'width': '40%', 'display': 'inline-block'}),


    # Power Graph
    html.Div([dcc.Graph(id='power-time', hoverData=1)], style={'width': '49%'}),

    # IV Curve Graph
    html.Div([dcc.Graph(id='iv-curve')], style={'width': '49%', 'display': 'inline-block'})
])

# Define the callback. Every time the 'value' child of 'mppt-dropdown' changes, it will call this function with
# the new value of mppt-dropdown as the sole input.
@app.callback(Output('power-time', 'figure'), Input('mppt-dropdown', 'value'))
def update_power_graph(mppt_num):

    df = iv_params[iv_params['mppt_id'] == mppt_num]
    fig = px.scatter(df, x='time', y='current', hover_name='curve_num')

    fig.update_layout(title_text='MPPT {} Power (W) Day 5'.format(mppt_num))
    fig.update_xaxes(title_text='Time (Australian)')
    fig.update_yaxes(title_text='Power (W)')

    return fig


# Four inputs this time: One for the hoverData on power-time (which point is being hovered on), two to set the max
# voltage/current in the IV Curve graph, and then another one for the state of the mppt selection dropdown.
# Using State instead of Input for the mppt-dropdown means this won't be automatically changed when that dropdown
# is changed.

# If you want the IV Curves to auto-size, take out the "range" parameter in fig.update_xaxes and fig.update_yaxes
@app.callback(
    Output('iv-curve', 'figure'),
    Input('power-time', 'hoverData'),
    Input('vmax-input', 'value'),
    Input('imax-input', 'value'),
    State('mppt-dropdown', 'value')
)
def update_iv_curve_graph(hoverData, vmax, imax, mppt_num):

    # print(hoverData)  # Uncomment to see the format of hoverData
    try:
        curve_num = hoverData['points'][0]['hovertext']  # How we can slice into hover data
    except TypeError:
        curve_num = 1
    df = iv_curves[(iv_curves['mppt_id'] == mppt_num) & (iv_curves['curve_num'] == curve_num)]

    fig = px.scatter(df, x='voltage', y='current', hover_name='curve_num', title='IV Curve')

    fig.update_xaxes(title_text='Voltage (V)', range=[0, vmax])
    fig.update_yaxes(title_text='Current (A)', range=[0, imax])


    return fig

if __name__ == '__main__':
    app.run_server(debug=False)