"""
File to aid in graphing IV Curves along with their power values.

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
from dash.dependencies import Input, Output

#### Data Entry/Variables

# Load IV Curves
path_iv = 'data/sundae_day_5_iv_curves.xlsx'
iv_curves = pd.read_excel(path_iv)

# Plot IV Curves

app = dash.Dash()  # Make the main app



