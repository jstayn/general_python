"""
File to aid in graphing IV Curves along with their power values. Also a useful way to learn Dash and Plotly, following
along with the Plotly/Dash Tutorials here: https://dash.plotly.com/interactive-graphing

This is the semi-final version of this code. I'd like to spend more time on it eventually, but don't expect to have
the time to do so.

What does this code do? It takes in a dataframe full of IV data with columns 'voltage', 'current', 'power',  'time',
and 'mppt_id', and then displays it. It first scrapes the data to generate a new dataframe called iv_params that has
one row per IV curve containing all the relevant data for that IV curve. Then, it creates a Dash layout containing a
few useful tools to visualize the data.

How to use this: select which MPPT you want to use with the dropdown, then hover over any of the datapoints in the
power-time graph on the left to pull up that datapoints IV curve on the right. The hoverdata has customizable data that
should summarize the important characteristics of the IV curve. The full one-row entry for that IV curve is displayed
in the table at the bottom.

This is accomplished through Dash, a Python library that allows you to set up Plotly to easily make data dashboards.
The layout contains Python code that outputs HTML code referencing a stylesheet in the 'assets' folder. The callbacks
determine the interactivity and have all the code for creating the graphs.

Goal:
    * Row 1, full width: Dropdown for which mppt you want to plot
    * Row 2, left: Graph of power vs time for that mppt (each point corresponds to an IV Curve)
    * Row 2, right: Graph of IV Curve, selected by which datapoint you've hovered over most recently
    * Row 3: Table containing all metadata in the iv_params dataframe.
    * Overall: Make this look better
    * Features: Add a button to make IV Curves auto-resize, make a table with all IV curve characteristics

Verdict:
    * Looks pretty good! THe misalignment on the Autosize button is annoying, but not worth fixing until final version
    * This, to me, is what I would deliver to engineers to help them visualize data.
    * This would probably require more testing/stability if it was going to be used by external people.

References:
    * https://stackoverflow.com/questions/739654/how-to-make-function-decorators-and-chain-them-together/1594484#1594484
    * https://dash.plotly.com/basic-callbacks  (part of the plotly/dash tutorials)
    * https://community.plotly.com/t/css-and-html-stylesheet-resources/7440/2 (How to style Dash)


Author: John Stayner
2021-01-06

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
import dash_table
import dash_daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

############# Data Entry/Variables ##################################

# Load IV Curves
path_iv = 'data/sundae_day_5_iv_curves_short.xlsx'  # For development (faster loading)
# path_iv = 'data/sundae_day_5_iv_curves.xlsx'
iv_curves = pd.read_excel(path_iv)

# Graph params
# Parameters besides power/time that you want in hover text. Must match the names you give the columns in iv_params
power_hover_data = ['Curve #', 'Isc (A)', 'Voc (V)', 'Temperature (C)', 'Irradiance (W/m^2)']

# IV Graph Default V/I max
v_max = 40  # Volts
i_max = 7  # Amps

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

default_table_col_width = 10  # % Width of the screen for a default column.
table_float_precision = 2  # Digits after decimal that you want to display


# Get Isc, Voc, and Pmax from each IV Curve (Last thing we need to do before making this work)
# Note that this is hwhere we set the names that are used in power_hover_data
iv_params = iv_curves \
    .groupby(['mppt_id', 'curve_num']) \
    .aggregate({'time': np.min, 'current': np.max, 'voltage': np.max, 'power': np.max}) \
    .reset_index() \
    .rename(columns={
        'current': 'Isc (A)',
        'voltage': 'Voc (V)',
        'power': 'Power (W)',
        'time': 'Time (Australian)',
        'mppt_id': 'MPPT ID',
        'curve_num': 'Curve #'
    }) \
    .round(table_float_precision)  # Round all numeric values to the desired precision

# To show another possible usecase, I'm adding environmental data for the IV curve to show how it can be used
iv_params['Irradiance (W/m^2)'] = iv_params['Isc (A)'] * (1000/6.9)  # Rough approximation of irradiance
iv_params['Cloud Cover'] = False
iv_params['Temperature (C)'] = 55  # For simplicity
iv_params['Speed (km/h)'] = 59  # I think this was close to our average speed (RIP)
iv_params['Angle to Sun (Degrees)'] = 30  # Again, for simplicity.
# iv_params['unnecessarily long parameter name to check if overflow works'] = True  # If you want to see it work
iv_params = iv_params.round(table_float_precision)  # Only needed since I'm setting things artificially here

# Calculations based on inputs

# Table columns and width
table_cols = iv_params.columns.values

table_width = '{:.0f}%'.format(np.min([len(table_cols) * default_table_col_width, 100]))


################# Dash Layout  ###############################

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)  # Make the main app

app.layout = html.Div([
    html.H1('IV Curve Visualizer'),
    html.Hr(),

    # MPPT Dropdown
    html.Div(
        [html.Div(['MPPT ID: ', dcc.Dropdown(
            id='mppt-dropdown',
            options=[{'label': i, 'value': i} for i in iv_curves['mppt_id'].unique()],
            value='A0'
            )]),
        html.Div(['Maximum Voltage (V) for IV Graph: ', dcc.Input(id='vmax-input', type='text', value=str(v_max))]),
        html.Div(['Maximum Current (A) for IV Graph: ', dcc.Input(id='imax-input', type='text', value=str(i_max))]),
        html.Div([
            html.Div('Auto-Size IV Curve Graph: ', style={'display': 'inline-block', 'width': '40%'}),
            html.Div(
                dash_daq.BooleanSwitch(id='autosize-iv-graph', on=False),
                style={'display': 'inline-block', 'width': '50%', 'height': '5px'}  # Still some weirdness with layout.
            )], style={'display': 'inline-block'})
        ], style={'width': '40%', 'display': 'inline-block'}),

    # Horizontal Line
    html.Hr(),

    # Graphs. By setting display to 'inline-block' we allow them to be side-by-side if there's enough space.
    # Note that "enough space" required width to be less than 49%. I stopped after trying 40% since that's all I needed.
    html.Div([

        # Power Graph
        html.Div([dcc.Graph(id='power-time', hoverData=1)], style={'width': '45%', 'display': 'inline-block'}, className='column'),

        # IV Curve Graph
        html.Div([dcc.Graph(id='iv-curve')], style={'width': '45%', 'display': 'inline-block'}, className='column')
    ], className='row'),

    # Data Table
    html.H3('IV Curve Params'),
    html.Div([
        dash_table.DataTable(
            id='iv-param-data',
            columns=[{'name': i, 'id': i} for i in iv_params.columns.values],
            style_cell={  # This styles all cells (it's superseded by style_header for the header cells)
                'width': '180px',  # Cell width
                'fontSize': 14,  # Font size
                'height': 'auto',  # Allows cells to wrap if necessary
                'font-family': 'helvetica',  # Default font is not great
                'whitespace': 'normal'},  # Not totally sure what this does?
            style_table={'overflowX': 'auto'},  # Allows table itself to overflow off the side of the page if necessary
            style_header={'fontWeight': 'bold', 'fontSize': 18}  # Font stuff for header
        )
    ], style={'width': table_width})  # Set table width given input characteristics

])



##################### App Callbacks ########################################

# Define the callback. Every time the 'value' child of 'mppt-dropdown' changes, it will call this function with
# the new value of mppt-dropdown as the sole input.
@app.callback(Output('power-time', 'figure'), Input('mppt-dropdown', 'value'))
def update_power_graph(mppt_num):

    df = iv_params[iv_params['MPPT ID'] == mppt_num]
    fig = px.scatter(df, x='Time (Australian)', y='Power (W)', hover_name='Curve #', hover_data=power_hover_data)

    fig.update_layout(title_text='MPPT {} Power (W) Day 5'.format(mppt_num))
    fig.update_xaxes(title_text='Time (Australian)')
    fig.update_yaxes(title_text='Power (W)')

    return fig


# Four inputs this time: One for the hoverData on power-time (which point is being hovered on), two to set the max
# voltage/current in the IV Curve graph, and then another one for the state of the mppt selection dropdown.
# Using State instead of Input for the mppt-dropdown means this won't be automatically changed when that dropdown
# is changed.
@app.callback(
    Output('iv-curve', 'figure'),
    Input('power-time', 'hoverData'),
    Input('vmax-input', 'value'),
    Input('imax-input', 'value'),
    Input('autosize-iv-graph', 'on'),
    State('mppt-dropdown', 'value')
)
def update_iv_curve_graph(hoverData, vmax, imax, autosize, mppt_num):

    # print(hoverData)  # Uncomment to see the format of hoverData.
    try:
        # This gets you the 'hover_name' of the datapoint, which is set to Curve #. Not sure why it's called hovertext
        curve_num = hoverData['points'][0]['hovertext']
    except TypeError:
        curve_num = 1

    # Slice out the data, reset the index (to make it start at 0) and then use the index to give us the order in which
    # the data is taken.
    df = iv_curves[(iv_curves['mppt_id'] == mppt_num) & (iv_curves['curve_num'] == curve_num)].reset_index()
    df['point_order'] = ['Point {}'.format(x) for x in df.index.values]

    fig = px.scatter(df, x='voltage', y='current', hover_name='point_order', title='IV Curve')

    fig.update_xaxes(title_text='Voltage (V)')
    fig.update_yaxes(title_text='Current (A)')

    if not autosize:
        fig.update_xaxes(range=[0, vmax])
        fig.update_yaxes(range=[0, imax])


    return fig

# Data Table. This table displays all the data associated with the selected IV Curve by displaying all columns of
# the iv_params dataframe associated with this IV Curve.
@app.callback(Output('iv-param-data', 'data'), Input('power-time', 'hoverData'), Input('mppt-dropdown', 'value'))
def update_table(hoverData, mppt_num):

    # Use previous code to get curve_num
    try:
        curve_num = hoverData['points'][0]['hovertext']  # How we can slice into hover data
    except TypeError:
        curve_num = 1

    # Note that we're pulling from the params dataframe now so that we only get one row
    table_data = iv_params[(iv_params['MPPT ID'] == mppt_num) & (iv_params['Curve #'] == curve_num)]

    # Make sure we give right format (see https://dash.plotly.com/datatable)
    return table_data.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=False)
