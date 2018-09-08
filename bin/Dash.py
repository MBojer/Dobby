#!/usr/bin/python

# Version 0.2

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
# from datetime import datetime as dt

# MySQL
import MySQLdb

# Pandas
import pandas as pd


db_Connection = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")

MonitorAgent_Agent_List = pd.read_sql("SELECT DISTINCT Agent FROM DobbyLog.MonitorAgent;", con=db_Connection)

KeepAliveMonitor_Device_List = pd.read_sql("SELECT DISTINCT Device FROM DobbyLog.KeepAliveMonitor;", con=db_Connection)


app = dash.Dash()

app.layout = html.Div([
    html.H1('Dobby'),

    # html.Div([
    #     html.Div([
    #         dcc.Graph(id='g4', figure={'data': [{'y': [1, 2, 3]}]})
    #     ], className="three columns"),
    #
    #     html.Div([
    #         html.H3('Column 2'),
    #         dcc.Graph(id='g5', figure={'data': [{'y': [1, 2, 3]}]})
    #     ], className="three columns"),
    #
    #     html.Div([
    #         html.H3('Column 3'),
    #         dcc.Graph(id='g6', figure={'data': [{'y': [1, 2, 3]}]})
    #     ], className="three columns"),
    #
    #     html.Div([
    #         html.H3('Column 4'),
    #         dcc.Graph(id='g7', figure={'data': [{'y': [1, 2, 3]}]})
    #     ], className="three columns"),
    #
    #     ])
    #
    # ])



    # ======================================== KeepAliveMonitor ========================================
    html.Div([
        html.Div([
            html.H2('KeepAliveMonitor'),

            html.Button('Update', id='KeepAliveMonitor_Update_Button'),

            dcc.Dropdown(
                id='KeepAliveMonitor_Dropdown',
                options=[{'label': Device, 'value': Device} for Device in KeepAliveMonitor_Device_List.Device],
            ),

            dcc.Slider(
                id='KeepAliveMonitor_Slider',
                min=10,
                max=25000,
                step=10,
                value=50,
            ),
        ]),

        dcc.Graph(id='KeepAliveMonitor_Graph'),

    ]),

    # ======================================== MonitorAgent ========================================
    html.Div([
        html.H2('MonitorAgent'),

        html.Button('Update', id='MonitorAgent_Update_Button'),

        dcc.Dropdown(
            id='MonitorAgent_Dropdown',
            options=[{'label': Agents, 'value': Agents} for Agents in MonitorAgent_Agent_List.Agent],
            ),

        dcc.Slider(
            id='MonitorAgent_Slider',
            min=10,
            max=25000,
            step=10,
            value=50,
            ),

        dcc.Graph(id='MonitorAgent_Graph'),
    ], className="MonitorAgent"),



])


# ======================================== MonitorAgent ========================================
@app.callback(Output('MonitorAgent_Graph', 'figure'), inputs=[Input('MonitorAgent_Slider', 'value'), Input('MonitorAgent_Dropdown', 'value'), Input('MonitorAgent_Update_Button', 'n_clicks')])
def MonitorAgent_Update_Graph(Selected_Slider_Value, Selected_Dropdown, n_clicks):

    if Selected_Dropdown is None:
        return

    db_Connection2 = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")

    df = pd.read_sql("SELECT DateTime, Source, Value FROM DobbyLog.MonitorAgent WHERE Agent = '" + str(Selected_Dropdown) + "' ORDER BY id DESC LIMIT " + str(Selected_Slider_Value) + ";", con=db_Connection2)

    Return_Data = {'data': [{}]}

    for i in df.Source.unique():
            Return_Data["data"].append({
                'x': df.DateTime[df['Source'] == i],
                'y': df.Value[df['Source'] == i], 'name': i,
                'line': {"shape": 'spline'}
            })

    return {'data': Return_Data}


# ======================================== KeepAliveMonitor ========================================
@app.callback(Output('KeepAliveMonitor_Graph', 'figure'), inputs=[Input('KeepAliveMonitor_Slider', 'value'), Input('KeepAliveMonitor_Dropdown', 'value'), Input('KeepAliveMonitor_Update_Button', 'n_clicks')])
def KeepAliveMonitor_Update_Graph(Selected_Slider_Value, Selected_Dropdown, n_clicks):

    if Selected_Dropdown is None:
        return

    db_Connection2 = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")

    df = pd.read_sql("SELECT LastKeepAlive, UpFor, FreeMemory, SoftwareVersion, IP, RSSI FROM DobbyLog.KeepAliveMonitor WHERE Device = '" + str(Selected_Dropdown) + "' ORDER BY id DESC LIMIT " + str(Selected_Slider_Value) + ";", con=db_Connection2)

    Return_Data = {'data': [{}]}

    # for i in ["UpFor", "FreeMemory", "RSSI"]:
    Return_Data["data"].append({
        'x': df.LastKeepAlive,
        'y': df.UpFor, 'name': "Uptime in ms",
        'line': {"shape": 'spline'}
    })
    Return_Data["data"].append({
        'x': df.LastKeepAlive,
        'y': df.FreeMemory, 'name': "Free Memory",
        'line': {"shape": 'spline'}
    })
    Return_Data["data"].append({
        'x': df.LastKeepAlive,
        'y': df.RSSI, 'name': "WiFi Signal Strenght (RSSI)",
        'line': {"shape": 'spline'}
    })

    return {'data': Return_Data}


app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


if __name__ == '__main__':
    app.run_server(debug=True,  host='0.0.0.0')
