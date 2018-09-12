#!/usr/bin/python

# Version 0.4

import dash
import dash_auth

from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

# import plotly.graph_objs as go

# MQTT
import paho.mqtt.publish as MQTT

# Time
import datetime

# MySQL
import MySQLdb

# Pandas
import pandas as pd

# MISC
import collections
import ast

# MySQL
MySQL_Server = '192.168.1.2'
# MySQL_Server = '10.106.138.5'
MySQL_Username = 'dobby'
MySQL_Password = 'HereToServe'

db_Connection = MySQLdb.connect(host=MySQL_Server, user=MySQL_Username, passwd=MySQL_Password)

# Dobby
MQTT_Broker = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Broker';", con=db_Connection)
MQTT_Port = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Port';", con=db_Connection)
MQTT_Username = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Username';", con=db_Connection)
MQTT_Password = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Password';", con=db_Connection)
System_Header = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='System' AND Target='Dobby' AND Name='Header';", con=db_Connection)

MQTT_Broker.Value[0] = "192.168.1.111"   # RM
# MQTT_Broker.Value[0] = "10.106.138.5"   # RM


# Dropdown lists
MonitorAgent_Agent_List = pd.read_sql("SELECT DISTINCT Agent FROM DobbyLog.MonitorAgent;", con=db_Connection)
KeepAliveMonitor_Device_List = pd.read_sql("SELECT DISTINCT Device FROM DobbyLog.KeepAliveMonitor;", con=db_Connection)
Device_List = pd.read_sql("SELECT Hostname FROM Dobby.DeviceConfig WHERE Config_Active = '1';", con=db_Connection)
Bin_Device_List = pd.read_sql("SELECT DISTINCT Device FROM DobbyLog.KeepAliveMonitor WHERE INSTR(`Device`, 'Bin') > 0;", con=db_Connection)

# User auth list
db_User_List = pd.read_sql("SELECT Username, Password FROM Dobby.Users;", con=db_Connection)

User_List = []

for i in db_User_List.index:
    User_List.append([db_User_List.Username[i], db_User_List.Password[i]])

# Dash
app = dash.Dash()

# Dash auth
auth = dash_auth.BasicAuth(
        app,
        User_List
)


def String_To_Dict(Dict):
    return ast.literal_eval("{" + Dict + "}")


def Generate_Device_Config_String(Selected_Device):

    Device_Config = pd.read_sql("SELECT * FROM Dobby.DeviceConfig WHERE Hostname='" + Selected_Device + "' AND Config_Active=1;", con=db_Connection)

    Config_Dict = {}
    Config_Ignore_List = ['id', 'Date_Modified', 'Config_Active', 'Config_ID']

    for i in Device_Config:
        if Device_Config[i][0] is not None and i not in Config_Ignore_List:
            Config_Dict[str(i)] = str(Device_Config[i][0])

    return Config_Dict


app.config['suppress_callback_exceptions'] = True


# ======================================== Layout ========================================
app.layout = html.Div([
    html.Title('Dobby'),

    dcc.Tabs(id="tabs", value='Devices_Tab', children=[
        dcc.Tab(label='MonitorAgent', value='MonitorAgent_Tab'),
        dcc.Tab(label='KeepAliveMonitor', value='KeepAliveMonitor_Tab'),
        dcc.Tab(label='Devices', value='Devices_Tab'),
        dcc.Tab(label='Device Config', value='Device_Config', id='Device_Config_Tab_id', style={'display': 'none'}),
        ]),

    html.Div(id='Main_Tabs'),

    html.Div(id='System_Variable', children='', style={'display': 'none'})
])


# ======================================== Tabs ========================================
@app.callback(Output('Main_Tabs', 'children'), [Input('tabs', 'value')])
def render_content(tab):

    # ======================================== MonitorAgent Tab ========================================
    if tab == 'MonitorAgent_Tab':
        return html.Div([
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

    # ======================================== KeepAliveMonitor Tab ========================================
    elif tab == 'KeepAliveMonitor_Tab':
        return html.Div([
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

            dcc.Graph(id='KeepAliveMonitor_Graph'),
        ])

    # ======================================== Devices Tab ========================================
    elif tab == 'Devices_Tab':
        return html.Div([

            dcc.Dropdown(
                id='Devices_Dropdown',
                options=[{'label': Device, 'value': Device} for Device in Device_List.Hostname],
            ),

            html.Button('Update', id='Devices_Update_Button'),

            html.Div([
                html.Div([
                    html.H2('Config'),
                    # dcc.Textarea(
                    #     id='Devices_Config_Text',
                    #     placeholder='Press "Read" to load config',
                    #     value='Press "Read" to load config',
                    #     rows=50,
                    #     style={'width': '50%'},
                    # ),
                    # html.P('No config avalible', id='Devices_Config_Text'),
                    html.Button('Read', id='Devices_Read_Config', n_clicks=1),
                    html.Button('Reapply config', id='Devices_Reapply_Config', n_clicks=1),
                    html.P(id='Devices_Config_Buttons_Text'),
                    html.Div(id='Devices_Config_Variables', children='Reapply:0 Read:0 Last_Click:0', style={'display': 'none'})
                ]),

                html.Div([
                    html.H2('Power'),
                    html.Button('Reboot', id='Devices_Reboot_Button', n_clicks=1),
                    html.Button('Shutdown', id='Devices_Shutdown_Button', n_clicks=1),
                    html.P(id='Devices_Power_Text'),
                    html.Div(id='Device_Power_Variables', children='Reboot:0 Shutdown:0 Last_Click:0', style={'display': 'none'})
                ])
            ], id="Devices_Options", style={'display': 'block'})
        ])

    # ======================================== Device_Config_Tab ========================================
    elif tab == 'Device_Config':
        return html.Div([

            # dcc.Dropdown(
            #     id='Device_Config_Dropdown',
            #     options=[{'label': Device, 'value': Device} for Device in Device_List.Hostname],
            #     ),

            # Table(df),
            html.Table(
                id='Device_Config_Table',
                children=[
                    html.Tr([
                        html.Th(children="Setting"),
                        html.Th(children="Value"),
                    ]),
                ]),
            html.Button('Update', id='Test_Update_Button', n_clicks=1),
        ])


@app.callback(
    Output('Device_Config_Div', 'children'),
    [
        Input('Device_Config_Dropdown', 'value'),
        ],
    )
def Device_Config_Div_Update(Selected_Device):

    if Selected_Device is None:
        return

    Return_Div = []

    Device_Config = pd.read_sql("SELECT * FROM Dobby.DeviceConfig WHERE Hostname='" + Selected_Device + "' AND Config_Active=1;", con=db_Connection)

    Config_Ignore_List = ['id', 'Date_Modified', 'Config_Active', 'Config_ID']

    for i in collections.OrderedDict(sorted(Device_Config.items())):
        if Device_Config[i][0] is not None and i not in Config_Ignore_List:
            Return_Div.append(
                html.Button(
                    str(i).replace("_", " "),
                    id=str(i),
                    disabled=True,
                    ),
                )

            print i
            # Use dropdown if pin
            if '_Pins' in i:
                Return_Div.append(dcc.Dropdown(
                    clearable=True,
                    multi=True,
                    options=[
                        {'label': 'D0', 'value': 'D0'},
                        {'label': 'D1', 'value': 'D1'},
                        {'label': 'D2', 'value': 'D2'},
                        {'label': 'D3', 'value': 'D3'},
                        {'label': 'D4', 'value': 'D4'},
                        {'label': 'D5', 'value': 'D5'},
                        {'label': 'D6', 'value': 'D6'},
                        {'label': 'D7', 'value': 'D7'},
                        {'label': 'D8', 'value': 'D8'},
                        {'label': 'A0', 'value': 'A0'},
                        ],
                    value=str(Device_Config[i][0]),
                    )
                )

            else:
                Return_Div.append(dcc.Input(type='text', value=str(Device_Config[i][0])),)

    return Return_Div


# ======================================== Device Config ========================================
# Change Device Config tab name to indicate what settings is getting changeds
@app.callback(
    Output('Device_Config_Tab_id', 'label'),
    [
        Input('System_Variable', 'children'),
        ],
    )
def Device_Config_Update_Tab_Text(System_Variable):

    System_Variable = String_To_Dict(System_Variable)

    if System_Variable["Selected_Device"] is None:
        return "Device Config"
    else:
        return "Device Config: " + str(System_Variable["Selected_Device"])


# Load settings when the tab is clicked
@app.callback(
    Output('Device_Config_Table', 'children'),
    [
        Input('Device_Config_Tab_id', 'n_clicks'),
        ],
    [
        State('System_Variable', 'children')
        ]
    )
def Device_Config_Read_Config(clicks, System_Variable):

    System_Variable = String_To_Dict(System_Variable)

    if System_Variable['Selected_Device'] is None:
        return

    Device_Settings_Dict = Generate_Device_Config_String(System_Variable['Selected_Device'])

    Table_Row_List = [
        html.Tr([
            html.Th(children="Setting"),
            html.Th(children="Value"),
            ]),
        ]

    # for key, value in Device_Settings_Dict.iteritems():
    #     Table_Row_List.append(
    #         html.Tr([
    #             html.Td(children=key),
    #             html.Td(children=value),
    #             ]),
    #         )

    for key, value in Device_Settings_Dict.iteritems():

        if '_Pins' in key:
            Table_Row_List.append(
                html.Tr([
                    html.Td(children=key),
                    html.Td(children=dcc.Dropdown(
                        clearable=True,
                        multi=True,
                        value=str(value),
                        options=[
                            {'label': 'D0', 'value': 'D0'},
                            {'label': 'D1', 'value': 'D1'},
                            {'label': 'D2', 'value': 'D2'},
                            {'label': 'D3', 'value': 'D3'},
                            {'label': 'D4', 'value': 'D4'},
                            {'label': 'D5', 'value': 'D5'},
                            {'label': 'D6', 'value': 'D6'},
                            {'label': 'D7', 'value': 'D7'},
                            {'label': 'D8', 'value': 'D8'},
                            {'label': 'A0', 'value': 'A0'},
                            ],
                        )),
                    ]),
                )
        else:
            Table_Row_List.append(
                html.Tr([
                    html.Td(children=key),
                    html.Td(children=dcc.Input(type='text', value=value)),
                    ]),
                )

    return Table_Row_List


# ======================================== System_Variable ========================================
# Saves "global vairables" to a child in a hidden div table to allow sharing of values
@app.callback(
        Output('System_Variable', 'children'),
    [
        Input('Devices_Dropdown', 'value')
        ],
    [
        State('System_Variable', 'children')
        ]
)
def Save_Selected_Device(Selected_Device, System_Variable):

    System_Variable_Dict = {}

    if System_Variable != "":
        print "hit"
        System_Variable_Dict = ast.literal_eval("{" + System_Variable + "}")
        # System_Variable_Dict = dict([i.split(':') for i in System_Variable.split(';')])

    System_Variable_Dict['Selected_Device'] = str(Selected_Device)

    Return_String = ""

    for key, value in System_Variable_Dict.iteritems():
        Return_String = Return_String + key + ":" + value

    # if Devices_Reapply_Config != int(Devices_Config_Variables['Reapply']) and int(Devices_Config_Variables['Reapply']) != 0:
    #     Last_Click = "Reapply"
    #
    # if Devices_Read_Config != int(Devices_Config_Variables['Read']) and int(Devices_Config_Variables['Read']) != 0:
    #     Last_Click = "Read"

    # return ("Reapply:" + str(Devices_Reapply_Config) + " Read:" + str(Devices_Read_Config) + " Last_Click:" + Last_Click)
    return str(System_Variable_Dict)[1:-1]


# ############################################################################## working code below ##############################################################################
# ############################################################################## working code below ##############################################################################
# ############################################################################## working code below ##############################################################################


# ======================================== Devices_Config_Buttons_Text ========================================
@app.callback(
    Output('Devices_Config_Buttons_Text', 'children'),
    [
        Input('Devices_Config_Variables', 'children'),
        ],
    [
        State('Devices_Dropdown', 'value')
        ]
    )
def Devices_Config_Buttons(Device_Config_Variables, Selected_Device):

    Device_Config_Variables = dict([i.split(':') for i in Device_Config_Variables.split(' ')])

    if str(Device_Config_Variables['Last_Click']) == "None":
        return

    elif str(Device_Config_Variables['Last_Click']) == "Read":
        return str(datetime.datetime.now().strftime('Config read: %Y-%m-%d %H:%M:%S'))

    elif str(Device_Config_Variables['Last_Click']) == "Reapply":
        MQTT.single(System_Header.Value[0] + "/Commands/Dobby/Config", str(Selected_Device) + ",-1;", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})
        return str(datetime.datetime.now().strftime('Config reapplied: %Y-%m-%d %H:%M:%S'))


# ======================================== Devices_Config_Buttons_Clicked ========================================
# Used to store variabled to share between callbacks
@app.callback(
        Output('Devices_Config_Variables', 'children'),
    [
        Input('Devices_Reapply_Config', 'n_clicks'),
        Input('Devices_Read_Config', 'n_clicks')
        ],
    [
        State('Devices_Config_Variables', 'children')
        ]
)
def Devices_Power_Buttons_Ckicked(Devices_Reapply_Config, Devices_Read_Config, Devices_Config_Variables):

    Devices_Config_Variables = dict([i.split(':') for i in Devices_Config_Variables.split(' ')])

    Last_Click = "None"

    if Devices_Reapply_Config != int(Devices_Config_Variables['Reapply']) and int(Devices_Config_Variables['Reapply']) != 0:
        Last_Click = "Reapply"

    if Devices_Read_Config != int(Devices_Config_Variables['Read']) and int(Devices_Config_Variables['Read']) != 0:
        Last_Click = "Read"

    return ("Reapply:" + str(Devices_Reapply_Config) + " Read:" + str(Devices_Read_Config) + " Last_Click:" + Last_Click)


# ======================================== Devices_Power_Buttons ========================================
# Used to take action based on Last_Click comming from "Devices_Power_Buttons_State"
@app.callback(
    Output('Devices_Power_Text', 'children'),
    [
        Input('Device_Power_Variables', 'children'),
        ],
    [
        State('Devices_Dropdown', 'value')
        ]
    )
def Devices_Power_Buttons(Device_Power_Variables, Selected_Device):

    Device_Power_Variables = dict([i.split(':') for i in Device_Power_Variables.split(' ')])

    if str(Device_Power_Variables['Last_Click']) == "None":
        return

    elif str(Device_Power_Variables['Last_Click']) == "Reboot":
        MQTT.single(System_Header.Value[0] + "/Commands/" + Selected_Device + "/Power", "Reboot;", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})
        return str(datetime.datetime.now().strftime('Reboot triggered: %Y-%m-%d %H:%M:%S'))

    elif str(Device_Power_Variables['Last_Click']) == "Shutdown":
        MQTT.single(System_Header.Value[0] + "/Commands/" + Selected_Device + "/Power", "Shutdown;", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})
        return str(datetime.datetime.now().strftime('Shutdown triggered: %Y-%m-%d %H:%M:%S'))


# ======================================== Device_Power_Variables ========================================
# Used to store variabled to share between callbacks
@app.callback(
        Output('Device_Power_Variables', 'children'),
    [
        Input('Devices_Reboot_Button', 'n_clicks'),
        Input('Devices_Shutdown_Button', 'n_clicks')
        ],
    [
        State('Device_Power_Variables', 'children')
        ]
)
def Devices_Power_Buttons_State(Devices_Reboot_Button_Clicks, Devices_Shutdown_Button_Clicks, Device_Power_Variables):

    Device_Power_Variables = dict([i.split(':') for i in Device_Power_Variables.split(' ')])

    Last_Click = "None"

    if Devices_Reboot_Button_Clicks != int(Device_Power_Variables['Reboot']) and int(Device_Power_Variables['Reboot']) != 0:
        Last_Click = "Reboot"

    if Devices_Shutdown_Button_Clicks != int(Device_Power_Variables['Shutdown']) and int(Device_Power_Variables['Shutdown']) != 0:
        Last_Click = "Shutdown"

    return ("Reboot:" + str(Devices_Reboot_Button_Clicks) + " Shutdown:" + str(Devices_Shutdown_Button_Clicks) + " Last_Click:" + Last_Click)


# ======================================== Devices - Disable Options ========================================
# Removed the Div table containing all options untill a device is selected
@app.callback(Output('Devices_Options', 'style'), inputs=[Input('Devices_Dropdown', 'value')])
def Devices_Display_Options(Selected_Dropdown):

    if Selected_Dropdown is None:
        return {'display': 'none'}
    else:
        return {}
        # return {'display': 'block'}


@app.callback(Output('Device_Config_Tab_id', 'style'), inputs=[Input('Devices_Dropdown', 'value')])
def Devices_Displat_Config_Tab(Selected_Dropdown):

    if Selected_Dropdown is None:
        return {'display': 'none'}
    else:
        return {}


# ======================================== MonitorAgent ========================================
@app.callback(Output('MonitorAgent_Graph', 'figure'), inputs=[Input('MonitorAgent_Slider', 'value'), Input('MonitorAgent_Dropdown', 'value'), Input('MonitorAgent_Update_Button', 'n_clicks')])
def MonitorAgent_Update_Graph(Selected_Slider_Value, Selected_Dropdown, n_clicks):

    if Selected_Dropdown is None:
        return

    df = pd.read_sql("SELECT DateTime, Source, Value FROM DobbyLog.MonitorAgent WHERE Agent = '" + str(Selected_Dropdown) + "' ORDER BY id DESC LIMIT " + str(Selected_Slider_Value) + ";", con=db_Connection)

    Return_Data = {'data': [{}]}

    for i in df.Source.unique():
            Return_Data["data"].append({
                'x': df.DateTime[df['Source'] == i],
                'y': df.Value[df['Source'] == i], 'name': i,
                'line': {"shape": 'spline'}
            })

    return {'data': Return_Data, 'layout': 'ytest'}


# ======================================== KeepAliveMonitor ========================================
@app.callback(Output('KeepAliveMonitor_Graph', 'figure'), inputs=[Input('KeepAliveMonitor_Slider', 'value'), Input('KeepAliveMonitor_Dropdown', 'value'), Input('KeepAliveMonitor_Update_Button', 'n_clicks')])
def KeepAliveMonitor_Update_Graph(Selected_Slider_Value, Selected_Dropdown, n_clicks):

    if Selected_Dropdown is None:
        return

    df = pd.read_sql("SELECT LastKeepAlive, UpFor, FreeMemory, SoftwareVersion, IP, RSSI FROM DobbyLog.KeepAliveMonitor WHERE Device = '" + str(Selected_Dropdown) + "' ORDER BY id DESC LIMIT " + str(Selected_Slider_Value) + ";", con=db_Connection)

    Return_Data = {'data': [{}]}

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


# ======================================== External Components ========================================
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


if __name__ == '__main__':
    app.run_server(debug=True,  host='0.0.0.0')
