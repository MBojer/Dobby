#!/usr/bin/python

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
# from datetime import datetime as dt

# MySQL
import MySQLdb

# Pandas
import pandas as pd


app = dash.Dash()

app.layout = html.Div([
    html.H1('Dobby'),

    html.H2('DC Voltage'),
    html.Button('Update', id='DC_Voltage_Update_Button'),
    dcc.Slider(
        id='DC_Voltage_Slider',
        min=10,
        max=25000,
        step=10,
        value=100,
    ),
    dcc.Graph(id='DC_Voltage_Graph'),

    html.H2('Humidity & Temperature'),
    html.Button('Update', id='DHT_Update_Button'),
    dcc.Slider(
        id='DHT_Slider',
        min=10,
        max=25000,
        step=10,
        value=100,
    ),
    dcc.Graph(id='DHT_Graph'),

    html.H2('Bilge Level'),
    html.Button('Update', id='Bilge_Update_Button'),
    dcc.Slider(
        id='Bilge_Slider',
        min=10,
        max=25000,
        step=10,
        value=100,
    ),
    dcc.Graph(id='Bilge_Graph')
])


@app.callback(Output('DC_Voltage_Graph', 'figure'), inputs=[Input('DC_Voltage_Slider', 'value'), Input('DC_Voltage_Update_Button', 'n_clicks')])
def DC_Voltmeter_Update_Graph(Slider_Value, Number_Of_Clicks):

    db_Connection = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")
    df = pd.read_sql("SELECT DateTime, Value FROM DobbyLog.MonitorAgent WHERE Agent = 'DCVoltmeterWH' ORDER BY id DESC LIMIT " + str(Slider_Value) + ";", con=db_Connection)

    return {
        'data': [{
            'x': df.DateTime,
            'y': df.Value, 'name': "Wheelhouse",
            'line': {
                "shape": 'spline'}
            }]}


@app.callback(Output('DHT_Graph', 'figure'), inputs=[Input('DHT_Slider', 'value'), Input('DHT_Update_Button', 'n_clicks')])
def DHT_Update_Graph(Slider_Value, Number_Of_Clicks):

    db_Connection = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")

    df_Humidity = pd.read_sql("SELECT DateTime, Value FROM DobbyLog.MonitorAgent WHERE Source = '/1B/DHT/SternBilge/1/Humidity' ORDER BY id DESC LIMIT " + str(Slider_Value) + ";", con=db_Connection)
    df_Temperature = pd.read_sql("SELECT DateTime, Value FROM DobbyLog.MonitorAgent WHERE Source = '/1B/DHT/SternBilge/1/Temperature' ORDER BY id DESC LIMIT " + str(Slider_Value) + ";", con=db_Connection)

    return {
        'data': [{
            'x': df_Humidity.DateTime,
            'y': df_Humidity.Value, 'name': "Humidity",
            'line': {
                "shape": 'spline'}
            },
            {
            'x': df_Temperature.DateTime,
            'y': df_Temperature.Value, 'name': "Temperature",
            'line': {
                "shape": 'spline',
                'text': 'test'}
            }]}


@app.callback(Output('Bilge_Graph', 'figure'), inputs=[Input('Bilge_Slider', 'value'), Input('Bilge_Update_Button', 'n_clicks')])
def Bilge_Update_Graph(Slider_Value, Number_Of_Clicks):

    db_Connection = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")
    df = pd.read_sql("SELECT DateTime, Value FROM DobbyLog.MonitorAgent WHERE Agent = 'SternBilge' AND Value > 25 ORDER BY id DESC LIMIT " + str(Slider_Value) + ";", con=db_Connection)

    return {
        'data': [{
            'x': df.DateTime,
            'y': df.Value, 'name': "Stern Bilge",
            'line': {
                "shape": 'spline'}
            }]}


if __name__ == '__main__':
    app.run_server(debug=True,  host='0.0.0.0')
