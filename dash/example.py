## Example file of a dash framework to get used to the syntax
# Taken from https://towardsdatascience.com/python-for-data-science-a-guide-to-plotly-dash-interactive-visualizations-66a5a6ecd93e
# Original Author: Nicholas Leong
# Date: 2020-09-15

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input, Output
import random  # SHould be numpy.random, not the base random!
import numpy as np

df = pd.read_csv('data/dash_example_data_mpg.csv')

######### Hello World Example  ##############
# #initiating the app
# app = dash.Dash()#defining the layout
# app.layout = html.Div(children=[
#     html.H1(children='Hello World!')
# ])
#
# #running the app
# if __name__ == '__main__':
#     app.run_server()

########## Graph Example ###############

# # initiating the app
# app = dash.Dash()  # defining the layout
# app.layout = html.Div(children=[
#     html.H1(children='Hello World!'),  # Note this comma is missing from the webpage
#     html.Div(children='Dash: A web application framework for Python.'), dcc.Graph(
#         id='graphid',
#         figure={
#             'data': [
#                 {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Cats'},
#                 {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Dogs'},
#             ],
#             'layout': {
#                 'title': 'Cats vs Dogs'
#             }
#         }
#     )
# ])
#
# # running the app
# if __name__ == '__main__':
#     app.run_server()

# ######### More graphing, but now with interactivity! ##############
#
# app = dash.Dash()
# # Commented following line out before realizing I imported the wrong 'random' library. Should have been numpy.random!
# # df['year'] = random.randint(-4, 5, len(df)) * 0.10 + df['model_year']
# # Not sure why we're adding random noise into model year, but ¯\_(ツ)_/¯
# df['year'] = np.array([random.randint(-4, 5) for n in range(len(df))]) + df['model_year']
#
# app.layout = html.Div([
#     html.Div([
#         dcc.Graph(id='mpg-scatter',
#                   figure={
#                       'data': [go.Scatter(  # Probably more efficient to pass in the graph object for large graphs
#                           x=df['year'] + 1900,  # This is where df['year'] is used, so it is indeed plotted.
#                           y=df['mpg'],
#                           text=df['name'],
#                           mode='markers'
#                       )],
#                       'layout': go.Layout(
#                           title='MPG vs Model Year',
#                           xaxis={'title': 'Model Year'},
#                           yaxis={'title': 'MPG'},
#                           hovermode='closest'
#                       )}
#                   )
#     ],
#         style={'width': '50%', 'display': 'inline-block'}),
#     # Div for the interactivity portion
#     html.Div([
#         dcc.Markdown(id='hoverdata-text')
#     ])
# ])
#
#
#
# # Components:
# # * @app is referring to the app object that we're using here
# # * Output is connecting this to the interactivity div (by its id), and pointing to the 'children' property of that div
# # * Input is connecting this to the mpg-scatter div by its id property, and pointing to that div's hoverData property.
# # All told, this means the callback will modify the 'children' property of the 'hoverdata-text' div inside app.layout
# # whenever the hoverData property of 'mpg-scatter' changes.
# @app.callback(Output('hoverdata-text', 'children'), [Input('mpg-scatter', 'hoverData')])
# def callback_stats(hoverData):
#     return str(hoverData)  # children is the default property that a component will display
#
#
# if __name__ == '__main__':
#     app.run_server()

######## The meat and potatoes! ##########

# Note: Made some modifications in an effort to make it look nice

app = dash.Dash()

# df = pd.read_csv('Data/mpg.csv')
df['year'] = np.random.randint(-4, 5, len(df)) * 0.10 + df['model_year']  # Plays nice with code above

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='mpg-scatter',
                  figure={
                      'data': [go.Scatter(
                          x=df['year'] + 1900,
                          y=df['mpg'],
                          text=df['name'],
                          # hoverinfo='text',
                          mode='markers'
                      )],
                      'layout': go.Layout(
                          title='MPG vs Model Year',
                          xaxis={'title': 'Model Year'},
                          yaxis={'title': 'MPG'},
                          hovermode='closest'
                      )

                  }
                  )
    ], style={'width': '50%', 'display': 'inline-block'}),

    html.Div([
        dcc.Graph(id='mpg-acceleration',
                  figure={
                      'data': [go.Scatter(x=[0, 1],
                                          y=[0, 1],
                                          mode='lines')

                               ],
                      'layout': go.Layout(title='Acceleration', margin={'l': 0})
                  }
                  )
    ], style={'width': '20%', 'height': '50%', 'display': 'inline-block'}),

    html.Div([
        dcc.Markdown(id='mpg-metrics')
    ], style={'width': '20%', 'display': 'inline-block'})
])


@app.callback(Output('mpg-acceleration', 'figure'),
              [Input('mpg-scatter', 'hoverData')])
def callback_graph(hoverData):
    df_index = hoverData['points'][0]['pointIndex']
    figure = {'data': [go.Scatter(x=[0, 1],
                                  y=[0, 60 / df.iloc[df_index]['acceleration']],
                                  mode='lines', )],
              'layout': go.Layout(title='{} Acceleration'.format(df.iloc[df_index]['name']),
                                  xaxis={'visible': False},
                                  yaxis={'visible': False, 'range': [0, 60 / df['acceleration'].min()]},
                                  margin={'l': 0},
                                  height=300
                                  )}
    return figure


@app.callback(Output('mpg-metrics', 'children'),
              [Input('mpg-scatter', 'hoverData')])
def callback_stats(hoverData):
    df_index = hoverData['points'][0]['pointIndex']
    metrics = """
            {}cc displacement,
            0 to 60mph in {} seconds
            """.format(df.iloc[df_index]['displacement'],
                       df.iloc[df_index]['acceleration'])
    return metrics


if __name__ == '__main__':
    app.run_server()