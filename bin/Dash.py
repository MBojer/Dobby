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


db_Connection = MySQLdb.connect(host="192.168.1.2", user="dobby", passwd="HereToServe", db="DobbyLog")

MonitorAgent_Agent_List = pd.read_sql("SELECT DISTINCT Agent FROM DobbyLog.MonitorAgent;", con=db_Connection)


app = dash.Dash()

app.layout = html.Div([
    html.H1('Dobby'),


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

])


@app.callback(Output('MonitorAgent_Graph', 'figure'), inputs=[Input('MonitorAgent_Slider', 'value'), Input('MonitorAgent_Dropdown', 'value'), Input('MonitorAgent_Update_Button', 'n_clicks')])
def DC_Voltmeter_Update_Graph(Selected_Slider_Value, Selected_Dropdown, n_clicks):

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


if __name__ == '__main__':
    app.run_server(debug=True,  host='0.0.0.0')
