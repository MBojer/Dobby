#!/usr/bin/python

# Improvements
# Add limit slider to live graph

# Changelog
# See Changelog/Dash.txt

import dash
import dash_auth

from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

# Neede to be able to shutdown dash
from flask import request

# MQTT
import paho.mqtt.publish as MQTT

# Time
import datetime

# MySQL
import MySQLdb

# Pandas
import pandas as pd

# MISC
# import collections
# import ast

# json
import json

# MISC
Version = 101005
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number


# MySQL
MySQL_Server = 'localhost'
MySQL_Username = 'dobby'
MySQL_Password = 'HereToServe'

db_pd_Connection = MySQLdb.connect(host=MySQL_Server, user=MySQL_Username, passwd=MySQL_Password)

# Dobby
MQTT_Broker = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Broker';", con=db_pd_Connection)
MQTT_Port = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Port';", con=db_pd_Connection)
MQTT_Username = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Username';", con=db_pd_Connection)
MQTT_Password = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Password';", con=db_pd_Connection)
System_Header = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='System' AND Target='Dobby' AND Name='Header';", con=db_pd_Connection)
DashButtons_Number_Of = pd.read_sql("SELECT COUNT(id) FROM Dobby.DashButtons;", con=db_pd_Connection)

# Add users and passwords
# User auth list
db_User_List = pd.read_sql("SELECT Username, Password FROM Dobby.Users;", con=db_pd_Connection)

db_pd_Connection.close()

User_List = []

for i in db_User_List.index:
    User_List.append([db_User_List.Username[i], db_User_List.Password[i]])

del db_User_List


# Dash
app = dash.Dash()


# Dash auth
auth = dash_auth.BasicAuth(
        app,
        User_List
)

# Needed with taps
app.config['suppress_callback_exceptions'] = True


# ================================================================================ Functions ================================================================================
# ================================================================================ Functions ================================================================================
# ================================================================================ Functions ================================================================================

# ======================================== Server Shutdown ========================================
def Server_Shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


# ======================================== MQTT Publish ========================================
def MQTT_Publish(Topic, Payload):
    MQTT.single(Topic, Payload, hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})


# ======================================== SQL Open /Close ========================================
def Open_db(db=""):
    try:
        db = MySQLdb.connect(host=MySQL_Server,    # your host, usually localhost
                             user=MySQL_Username,         # your username
                             passwd=MySQL_Password,  # your password
                             db=db)        # name of the data base
        return db

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return False


def Close_db(conn, cur):
    try:
        conn.commit()
        cur.close()
        conn.close()
        return True

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return False


# ======================================== SQL_To_List ========================================
def SQL_To_List(SQL_String):
    # Open db connection
    db_SQL_Connection = Open_db('')
    db_SQL_Curser = db_SQL_Connection.cursor()

    db_SQL_Curser.execute(SQL_String)
    db_List = db_SQL_Curser.fetchall()

    # Close db connection
    Close_db(db_SQL_Connection, db_SQL_Curser)

    Return_List = []

    for i in db_List:
        Return_List.append(i[0])

    return Return_List


# ======================================== SQL_Read_df ========================================
def SQL_Read_df(SQL_String):
    # Open db connection
    db_SQL_Connection = Open_db('')

    df = pd.read_sql(SQL_String, con=db_SQL_Connection)

    # Close db connection
    db_SQL_Connection.close()

    return df


# ======================================== SQL_Read ========================================
def SQL_Read(SQL_String):
    # Open db connection
    db_SQL_Connection = Open_db('')
    db_SQL_Curser = db_SQL_Connection.cursor()

    db_SQL_Curser.execute(SQL_String)
    db_Resoult = db_SQL_Curser.fetchall()

    # Close db connection
    Close_db(db_SQL_Connection, db_SQL_Curser)

    return db_Resoult


# ======================================== Generate_Device_Config_Dict ========================================
def Generate_Device_Config_Dict(Selected_Device, db_Curser):

    if Selected_Device is None:
        return None

    db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='DeviceConfig';")
    Device_Config_Setting = db_Curser.fetchall()

    db_Curser.execute("SELECT * FROM Dobby.DeviceConfig WHERE Hostname='" + Selected_Device + "' AND Config_Active=1;")
    Device_Config_Value = db_Curser.fetchone()

    Row_List = []
    Config_Ignore_List = ['id', 'Date_Modified', 'Config_Active', 'Config_ID']

    i = 0

    for Setting in Device_Config_Setting:
        if Setting[0] not in Config_Ignore_List:
            Row_List.append({'Setting': [Setting[0]], 'Value': [Device_Config_Value[i]]})
        i = i + 1

    return Row_List


# ======================================== Generate_Variable_Dict ========================================
def Generate_Variable_Dict(String):

    Return_Dict = {}

    print "String"
    print String
    print type(String)

    # Do nothing if string en empthy
    if String == "" or String is None:
        pass

    else:
        for i in String.split('<*>'):
            # Skip if line is ''
            if i == '':
                continue

            Dict_Entry = i.split('<;>')

            # I asume that 2 x - and 2  : = datetime
            if Dict_Entry[1].count('-') == 2 and Dict_Entry[1].count(':') == 2:
                Dict_Entry[1] = datetime.datetime.strptime(Dict_Entry[1], '%Y-%m-%d %H:%M:%S')

            Return_Dict[Dict_Entry[0]] = Dict_Entry[1]

    return Return_Dict


# ======================================== Generate_Variable_Dict ========================================
def Generate_Variable_String(Dict):

    Return_String = ''

    for Key, Value in Dict.iteritems():
        Return_String = Return_String + str(Key) + '<;>' + str(Value) + '<*>'

    return Return_String


# ======================================== Generate_json_Config_String ========================================
def MQTT_Config_New(Selected_Device):

    # No reason to continue if no device is selected
    if Selected_Device is None:
        return

    db_FSCJ_Connection = Open_db("Dobby")
    db_FSCJ_Curser = db_FSCJ_Connection.cursor()

    # Get config
    try:
        db_FSCJ_Curser.execute("SELECT DISTINCT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='DeviceConfig';")
        Config_Name_List = db_FSCJ_Curser.fetchall()

        db_FSCJ_Curser.execute("SELECT * FROM DeviceConfig WHERE Hostname='" + Selected_Device + "';")
        Config_Value_List = db_FSCJ_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            print "Unable to build json Config for: " + str(Selected_Device)
        else:
            print "db error building json Config for: " + str(Selected_Device)
            Close_db(db_FSCJ_Connection, db_FSCJ_Curser)
            return

    Close_db(db_FSCJ_Connection, db_FSCJ_Curser)

    # Compare ConfigID
    if Config_Name_List is None:
        print "Unable to build json Config for: " + str(Selected_Device)

    if Config_Name_List is () or Config_Value_List is ():
        print "json Config empthy for: " + str(Selected_Device)
        return

    Config_Dict = {}

    Interation = 0

    for x in Config_Name_List:
        if str(x[0]) != "id" and str(x[0]) != "Config_Active" and str(x[0]) != "Date_Modified" and Config_Value_List[0][Interation] is not None:
            Config_Dict[str(x[0])] = str(Config_Value_List[0][Interation])
        Interation = Interation + 1

    return json.dumps(Config_Dict)


# ======================================== Layout ========================================
app.layout = html.Div([

    dcc.Tabs(id="tabs", value='Log_Trigger_Tab', children=[
        dcc.Tab(label='Buttons', value='Buttons_Tab'),
        dcc.Tab(label='MonitorAgent', value='MonitorAgent_Tab'),
        dcc.Tab(label='Log Trigger', value='Log_Trigger_Tab'),
        dcc.Tab(label='Alerts', value='Alerts_Tab'),
        dcc.Tab(label='Functions', value='Functions_Tab'),
        dcc.Tab(label='Devices', value='Devices_Tab'),
        dcc.Tab(label='Users', value='Users_Tab'),
        dcc.Tab(label='System', value='System_Tab'),
        ]),

    html.Div(id='Main_Tabs'),

    # No idea why this needs to be here, if its not the tabs with datatables does not load
    html.Div([
        dt.DataTable(rows=[{}]),
        ], style={"display": "none"}),

    # Places to store variables
    html.Div([

        html.Div(id='Devices_Tab_Variables', children=""),
        html.Div(id='MonitorAgent_Tab_Variables', children=""),
        html.Div(id='Log_Trigger_Tab_Variables', children=""),
        html.Div(id='Users_Tab_Variables', children=""),
        html.Div(id='Buttons_Tab_Variables', children=""),
        html.Div(id='System_Tab_Variables', children=""),

        ], style={'display': 'none'})
    ])


# ======================================== Tabs ========================================
@app.callback(
    Output('Main_Tabs', 'children'),
    [
        Input('tabs', 'value'),
        ],
    [
        State('Devices_Tab_Variables', 'children'),
        State('MonitorAgent_Tab_Variables', 'children'),
        State('Log_Trigger_Tab_Variables', 'children'),
        State('Users_Tab_Variables', 'children'),
        State('Buttons_Tab_Variables', 'children'),
        State('System_Tab_Variables', 'children'),
        ]
    )
def render_content(tab, Devices_Tab_Variables, MonitorAgent_Tab_Variables, Log_Trigger_Tab_Variables, Users_Tab_Variables, Buttons_Tab_Variables, System_Tab_Variables):

    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)
    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)
    Log_Trigger_Tab_Variables = Generate_Variable_Dict(Log_Trigger_Tab_Variables)
    Users_Tab_Variables = Generate_Variable_Dict(Users_Tab_Variables)
    Buttons_Tab_Variables = Generate_Variable_Dict(Buttons_Tab_Variables)

    # ======================================== MonitorAgent Tab ========================================
    if tab == 'MonitorAgent_Tab':
        return html.Div([

            # ================================================== Dropdown and live button ==================================================
            # Div for Dropdown and live button
            html.Div(
                style={
                    'width': '100%',
                    'display': 'table-cell',
                    'margin-right': 'auto',
                    'margin-left': 'auto',
                },
                children=[
                    html.Div(
                        style={
                            'width': '95vw',
                            'display': 'table-cell',
                        },
                        children=[
                            dcc.Dropdown(
                                id='MonitorAgent_Dropdown',
                                options=[{'label': Agents, 'value': Agents} for Agents in SQL_To_List("SELECT DISTINCT Agent_Name FROM Dobby.MonitorAgentConfig;")],
                                value=MonitorAgent_Tab_Variables.get('MonitorAgent_Dropdown')
                            ),
                        ],
                    ),
                    html.Div(
                        style={
                            'display': 'table-cell',
                        },
                        children=[
                            html.Button('Switch to Live', id='MonitorAgent_Button_Live', n_clicks=0),
                        ],
                    ),
                ],
            ),

            # ================================================== Graph ==================================================
            # Main graph
            html.Div(
                style={
                    # 'width': '100%',
                    # 'display': 'table-cell',
                    # 'margin-right': 'auto',
                    # 'margin-left': 'auto',
                },
                children=[
                    dcc.Graph(
                        id='MonitorAgent_Graph',
                        style={
                            'height': '70vh',
                            'width': '100%'
                        },
                    ),
                    dcc.Interval(
                        id='MonitorAgent_Graph_Live_Interval',
                        interval=int(MonitorAgent_Tab_Variables.get('Live_Graph_Interval', '7200000')),
                        n_intervals=0
                    ),

                    html.Div(
                        style={
                            'marginLeft': '75px',
                            'marginRight': '75px',
                        },
                        children=[
                            dcc.RangeSlider(
                                id='MonitorAgent_Slider',
                                min=0,
                                max=100,
                                step=1,
                                value=[95, 100],
                                marks={},
                            ),
                        ],
                    ),
                ],
            ),

            # ================================================== Configuration ==================================================
            # Main Div
            html.Div(
                id='MonitorAgent_Configuration_Main_Div',
                style={
                    # 'marginTop': '200px',
                    'marginLeft': '75px',
                    'marginRight': '75px',
                    'display': 'none',
                    # 'width': '100vw',
                },
                children=[

                    html.H2('Configuration'),

                    html.Div(
                        style={
                            # 'hight': '100px',
                            # 'width': '50vw',
                            'marginRight': '10px',
                            'display': 'inline',
                        },
                        children=[
                            html.Button('Current state: ', id='MonitorAgent_Current_State', style={'marginRight': '20px'}, n_clicks=0),
                            html.Button('Change state to: ', id='MonitorAgent_Change_State', n_clicks=0),
                        ],
                    ),
                    html.Div(
                        style={
                            'width': '200px',
                            'display': 'table-cell',
                        },
                        children=[
                            dcc.Dropdown(
                                id='MonitorAgent_Dropdown_Agent_State',
                                options=[{'label': State, 'value': State} for State in 'Running', 'Stopped', 'Disabled'],
                                value='',
                                clearable=False,
                            ),
                        ],
                    ),
                ],
            ),



        ], className="MonitorAgent", style={
            'height': '100%',
            'width': '100%'
            }),

    # ======================================== Devices Tab ========================================
    elif tab == 'Devices_Tab':
        return html.Div([

            dcc.Dropdown(
                id='Devices_Dropdown',
                options=[{'label': Device, 'value': Device} for Device in SQL_To_List("SELECT Hostname FROM `Dobby`.`DeviceConfig` WHERE Config_Active = '1' ORDER BY Hostname;")],
                value=Devices_Tab_Variables.get('Devices_Dropdown'),
                ),
            # KeepAlive info
            html.Div([
                html.H2('KeepAlive'),
                html.Button('Read', id='Devices_Read_KeepAlive_Button', n_clicks=0),
                dcc.Graph(
                    id='Devices_KeepAlive_Graph',
                    style={
                        'height': '375px',
                        'width': '100%'
                        }
                    ),
                dcc.Slider(
                    id='Devices_KeepAlive_Slider',
                    min=10,
                    max=25000,
                    step=60,
                    value=Devices_Tab_Variables.get('Devices_KeepAlive_Slider', 3600)
                    ),
                html.P(id='Devices_KeepAlive_Text'),
                ]),
            # Device Config
            html.Div([
                html.Div([
                    # Header text
                    html.H2('Config'),
                    # Buttons
                    html.Button('Read', id='Devices_Read_Config_Button', n_clicks=0),
                    html.Button('Save', id='Devices_Save_Config_Button', n_clicks=0),
                    html.Button('Send Config', id='Devices_Send_Config_Button', n_clicks=0),
                    # Button Text
                    html.P(id='Devices_Config_Buttons_Text'),
                    # Data Table
                    html.Div([
                        dt.DataTable(
                            id='Devices_Config_Table',
                            rows=[],
                            columns=['Setting', 'Value'],
                            min_height=500,
                            resizable=True,
                            editable=True,
                            filterable=True,
                            sortable=True,
                            )
                        ]),
                    # Data Table text
                    html.P(id='Devices_Config_Text'),

                    # Device Config copy field
                    html.Div([
                        html.H2('json Config'),
                        html.Textarea(
                            id='Devices_json_Config_String',
                            placeholder="Please select a device above to generate the json config string",
                            style={'width': '100%'},
                            disabled=True,
                            readOnly=True,
                            ),
                        html.P(id='Devices_json_Config_Text'),
                        ], style={'marginBottom': 50, 'marginTop': 25}),
                    ]),
                # Power
                html.Div([
                    html.H2('Power'),
                    html.Button('Reboot', id='Devices_Reboot_Button', n_clicks=1),
                    html.Button('Shutdown', id='Devices_Shutdown_Button', n_clicks=1),
                    html.P(id='Devices_Power_Text'),
                ])
            ], id="Devices_Options", style={'display': 'block'})
        ])

    # ======================================== Users Tab ========================================
    elif tab == 'Users_Tab':
        return html.Div([
            html.Button('Read', id='Users_Read_Button', n_clicks=0),
            html.Button('Save', id='Users_Save_Button', n_clicks=0),
            # Button Text
            html.P(id='Users_Buttons_Text'),
            # Data Table
            html.Div([
                dt.DataTable(
                    id='Users_Table',
                    rows=[],
                    columns=['Username', 'Password'],
                    min_height=300,
                    resizable=True,
                    editable=True,
                    filterable=True,
                    # sortable=True,
                    )
                ]),
            # Data Table text
            html.P(id='Users_Text'),
        ], id='Users_Tab')

    # ======================================== Buttons Tab ========================================
    elif tab == 'Buttons_Tab':

        db_Write_Connection = Open_db('Dobby')
        db_Write_Curser = db_Write_Connection.cursor()

        db_Write_Curser.execute("SELECT * FROM Dobby.DashButtons;")
        db_Resoult = db_Write_Curser.fetchall()

        Button_List = []

        for Entry in db_Resoult:
            if Entry[2] == "Button":
                Button_List.append(html.Button(str(Entry[1]), id=str('DBTN_' + str(Entry[0])), n_clicks=0),)

        Close_db(db_Write_Connection, db_Write_Curser)

        return html.Div([
            html.Div(
                id="Buttons_Tab_Div",
                children=Button_List,
                style={}
                )
        ], id='Buttons_Tab')

    # ======================================== System Tab ========================================
    elif tab == 'System_Tab':
        return html.Div([
            html.Button('Quit', id='System_Quit_Button', n_clicks=0),
        ], id='System_Tab')

    # ======================================== System Tab ========================================
    elif tab == 'Alerts_Tab':
        return html.Div([

        ], id='Alerts_Tab')
    # ======================================== System Tab ========================================
    elif tab == 'Functions_Tab':
        return html.Div([
        ], id='Functions_Tab')

    # ======================================== Log Trigger Tab ========================================
    elif tab == 'Log_Trigger_Tab':
        return html.Div([
            dcc.Dropdown(
                id='Log_Trigger_Dropdown',
                options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT DISTINCT Name FROM DobbyLog.Log_Trigger;")],
                multi=True,
                value=Log_Trigger_Tab_Variables.get('Log_Trigger_Dropdown')
            ),
        ], id='Log_Trigger_Tab')


# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================

# ======================================== Log Trigger Tab - Callbacks ========================================
# Log_Trigger_Tab_Variables
@app.callback(
    Output('Log_Trigger_Tab_Variables', 'children'),
    [
        Input('Log_Trigger_Dropdown', 'value'),
        # Input('Log_Trigger_Slider', 'value'),
        # Input('Log_Trigger_Button_Live', 'n_clicks'),
        # Input('Log_Trigger_Dropdown_Agent_State', 'value'),
        # Input('Log_Trigger_Current_State', 'value'),
        # Input('Log_Trigger_Change_State', 'value'),
        ],
    [
        State('Log_Trigger_Tab_Variables', 'children')
        ]
    )
def Log_Trigger_Tab_Variables(Log_Trigger_Dropdown, Log_Trigger_Tab_Variables):

    Log_Trigger_Tab_Variables = Generate_Variable_Dict(Log_Trigger_Tab_Variables)

    Log_Trigger_Tab_Variables['Log_Trigger_Dropdown'] = Log_Trigger_Dropdown

    # print "Log_Trigger_Tab_Variables['Log_Trigger_Dropdown']"
    # print Log_Trigger_Tab_Variables['Log_Trigger_Dropdown']
    # print Log_Trigger_Tab_Variables['Log_Trigger_Dropdown'][0]
    # print type(Log_Trigger_Tab_Variables['Log_Trigger_Dropdown'][0])

    return Generate_Variable_String(Log_Trigger_Tab_Variables)


# ======================================== Button Tab - Callbacks ========================================
# Button Tabs
@app.callback(
    Output('System_Tab_Variables', 'children'),
    [
        Input('System_Quit_Button', 'n_clicks')
        ],
    [
        State('System_Tab_Variables', 'children'),
        ],
    )
def System_Tab_Buttons(System_Quit_Button, System_Tab_Variables):

    # Import variables from div able
    System_Tab_Variables = Generate_Variable_Dict(System_Tab_Variables)

    # If n_clicks = 0 then the page has just been loaded so dont do anything
    if int(System_Quit_Button) == 0:
        System_Tab_Variables['System_Quit_Button'] = 0

    elif int(System_Tab_Variables.get('System_Quit_Button', 0)) != int(System_Quit_Button):
        System_Tab_Variables['System_Quit_Button'] = System_Quit_Button

        print "System shutdown requested, shutting down"
        Server_Shutdown()

    return Generate_Variable_String(System_Quit_Button)


# ======================================== Button Tab - Callbacks ========================================
# Button Tabs
@app.callback(
    Output('Buttons_Tab_Variables', 'children'),
    [
        Input('DBTN_' + str(i), 'n_clicks') for i in range(DashButtons_Number_Of['COUNT(id)'])
        ],
    [
        State('Buttons_Tab_Variables', 'children'),
        ],
    )
def Buttons_Tab_Buttons(*args):

    # Import variables from div able
    Buttons_Tab_Variables = Generate_Variable_Dict(args[len(args) - 1])

    # - 1 excludes Buttons_Tab_Variables
    for i in range(len(args) - 1):
        # If n_clicks = 0 then the page has just been loaded so dont do anything
        if int(args[i]) == 0:
            Buttons_Tab_Variables['DBTN_' + str(i)] = 0

        elif int(Buttons_Tab_Variables.get('DBTN_' + str(i), 0)) != int(args[i]):
            Buttons_Tab_Variables['DBTN_' + str(i)] = args[i]

            # Open db connection
            db_Write_Connection = Open_db('Dobby')
            db_Write_Curser = db_Write_Connection.cursor()

            # i is the id of the row in the db table
            db_Write_Curser.execute("SELECT Target_Topic, Target_Payload FROM Dobby.DashButtons WHERE id='" + str(i) + "';")
            Topic_Payload = db_Write_Curser.fetchone()

            # Close db connection
            Close_db(db_Write_Connection, db_Write_Curser)

            MQTT_Publish(Topic_Payload[0], Topic_Payload[1])

            break

    return Generate_Variable_String(Buttons_Tab_Variables)


# ======================================== Users Tab - Callbacks ========================================
# Users Tabs
@app.callback(
    Output('Users_Table', 'rows'),
    [
        Input('Users_Tab_Variables', 'children'),
        ],
    [
        State('Users_Table', 'rows'),
        ],
    )
def Users_Tab_DataTable(Users_Tab_Variables, Users_Table):

    # Open db connection
    db_Write_Connection = Open_db('Dobby')
    db_Write_Curser = db_Write_Connection.cursor()

    # Import variables from div able
    Users_Tab_Variables = Generate_Variable_Dict(Users_Tab_Variables)

    # ======================================== Load ========================================
    # Pass Last_Click if None so username mismatch does not trigger
    if Users_Tab_Variables.get('Last_Click', "None") == "None":
        pass

    # ======================================== Read Users ========================================
    if Users_Tab_Variables.get('Last_Click', "None") == "Users_Read_Button":
        pass

    # ======================================== Save Users ========================================
    elif Users_Tab_Variables.get('Last_Click', "None") == "Users_Save_Button":
        Current_Users = []

        db_Write_Curser.execute("SELECT Username, Password FROM Dobby.Users ORDER BY Username;")
        db_User_List = db_Write_Curser.fetchall()

        for Username, Password in db_User_List:
            Current_Users.append({'Username': Username, 'Password': Password})

        Config_Changes = []

        # Needed so you dont change the config id when no changes is made
        for i in range(len(Users_Table)):
            # Check usernames match just for good mesure
            if Current_Users[i]['Username'] != Users_Table[i]['Username']:
                print "ERROR: Username mismatch"
                return [{'Username': 'Error', 'Password': 'Username mismatch'}]

            elif Current_Users[i]['Password'] != Users_Table[i]['Password']:
                # Add chnages to chnages dict
                Config_Changes.append({'id': -1, 'Username': Current_Users[i]['Username'], 'Password': Users_Table[i]['Password']})

        # Get device id for use in sql changes below
        for i in range(len(Config_Changes)):
            db_Write_Curser.execute("SELECT id FROM Dobby.Users WHERE Username='" + Config_Changes[i]['''Username'''] + "';")
            User_id = db_Write_Curser.fetchone()
            Config_Changes[i]['id'] = str(User_id[0])

        # Write Changes
        for Change in Config_Changes:
            db_Write_Curser.execute("UPDATE `Dobby`.`Users` SET `Password`='" + str(Change['''Password''']) + "' WHERE `id`='" + Change['''id'''] + "';")

    # ======================================== Return table ========================================
    Return_Dict = []

    db_Write_Curser.execute("SELECT Username, Password FROM Dobby.Users ORDER BY Username;")
    db_User_List = db_Write_Curser.fetchall()

    for Username, Password in db_User_List:
        Return_Dict.append({'Username': Username, 'Password': Password})

    Close_db(db_Write_Connection, db_Write_Curser)

    return Return_Dict


# ======================================== Users Tab - Callbacks ========================================
# Users Tabs
@app.callback(
    Output('Users_Tab_Variables', 'children'),
    [
        Input('Users_Read_Button', 'n_clicks'),
        Input('Users_Save_Button', 'n_clicks'),
        ],
    [
        State('Users_Tab_Variables', 'children'),
        ]
    )
def Users_Tab_Buttons(Users_Read_Button, Users_Save_Button, Users_Tab_Variables):
    Users_Tab_Variables = Generate_Variable_Dict(Users_Tab_Variables)

    Button_List = [Users_Read_Button, Users_Save_Button]
    Button_List_Text = ['Users_Read_Button', 'Users_Save_Button']

    # Check if buttons was presses
    for i in range(len(Button_List)):
        if Button_List[i] != int(Users_Tab_Variables.get(Button_List_Text[i], 0)):
            Users_Tab_Variables[Button_List_Text[i]] = Button_List[i]
            Users_Tab_Variables['Last_Click'] = Button_List_Text[i]
            break

    return Generate_Variable_String(Users_Tab_Variables)


# ======================================== Devices Tab - Callbacks ========================================

# Text updates
# Text updates
# Text updates
# Update Device Config KeepAlive Text
@app.callback(
    Output('Devices_KeepAlive_Text', 'children'),
    [
        Input('Devices_KeepAlive_Graph', 'figure'),
        ],
    [
        State('Devices_Tab_Variables', 'children')
        ],
    )
def Devices_KeepAlive_Text(Devices_KeepAlive_Graph, Devices_Tab_Variables):
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    if Devices_Tab_Variables['Devices_Dropdown'] == 'None':
        return

    return str(datetime.datetime.now().strftime('Updated: %Y-%m-%d %H:%M:%S'))


@app.callback(
    Output('Devices_Config_Buttons_Text', 'children'),
    [
        Input('Devices_Tab_Variables', 'children'),
        ],
    )
def Devices_Config_Buttons_Text(Devices_Tab_Variables):
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    if Devices_Tab_Variables['Devices_Dropdown'] == 'None':
        return

    if "Devices_Read_Config_Button" in str(Devices_Tab_Variables['Last_Click']):
        return str(datetime.datetime.now().strftime('Updates: %Y-%m-%d %H:%M:%S'))
    elif "Devices_Save_Config_Button" in str(Devices_Tab_Variables['Last_Click']):
        return str(datetime.datetime.now().strftime('Saved: %Y-%m-%d %H:%M:%S'))
    elif "Devices_Send_Config_Button" in str(Devices_Tab_Variables['Last_Click']):
        return str(datetime.datetime.now().strftime('Send requested: %Y-%m-%d %H:%M:%S'))
    else:
        return

    # return str(datetime.datetime.now().strftime('Updated: %Y-%m-%d %H:%M:%S'))


# Update Device Config Text
@app.callback(
    Output('Devices_Config_Text', 'children'),
    [
        Input('Devices_Config_Table', 'rows'),
        ],
    [
        State('Devices_Tab_Variables', 'children')
        ],
    )
def Devices_Config_Text(Devices_Config_Table, Devices_Tab_Variables):
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    if Devices_Tab_Variables['Devices_Dropdown'] == 'None':
        return

    return str(datetime.datetime.now().strftime('Updated: %Y-%m-%d %H:%M:%S'))


# Update Device Config Text
@app.callback(
    Output('Devices_json_Config_Text', 'children'),
    [
        Input('Devices_json_Config_String', 'value'),
        ],
    [
        State('Devices_Tab_Variables', 'children')
        ],
    )
def Devices_json_Config_Text(Devices_json_Config_String, Devices_Tab_Variables):
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    if Devices_Tab_Variables['Devices_Dropdown'] == 'None':
        return

    return str(datetime.datetime.now().strftime('Updated: %Y-%m-%d %H:%M:%S'))


# Update Device Config Text AND send MQTT Message
@app.callback(
    Output('Devices_Power_Text', 'children'),
    [
        Input('Devices_Tab_Variables', 'children')
        ],
    )
def Devices_Power_Text(Devices_Tab_Variables):
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    if Devices_Tab_Variables['Devices_Dropdown'] == 'None':
        return

    if "Devices_Reboot_Button" in str(Devices_Tab_Variables['Last_Click']):
        Return_String = str(datetime.datetime.now().strftime('Reboot requested: %Y-%m-%d %H:%M:%S'))
        Action_Text = 'Reboot'
    elif "Devices_Shutdown_Button" in str(Devices_Tab_Variables['Last_Click']):
        Return_String = str(datetime.datetime.now().strftime('Shutdown requested: %Y-%m-%d %H:%M:%S'))
        Action_Text = 'Shutdown'
    else:
        return

    MQTT.single(System_Header.Value[0] + "/Commands/" + str(Devices_Tab_Variables['Devices_Dropdown']) + "/Power", Action_Text + ";", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})
    return Return_String


# Update Device Config variables
@app.callback(
    Output('Devices_Tab_Variables', 'children'),
    [
        Input('Devices_Dropdown', 'value'),
        Input('Devices_Read_Config_Button', 'n_clicks'),
        Input('Devices_Save_Config_Button', 'n_clicks'),
        Input('Devices_Send_Config_Button', 'n_clicks'),
        Input('Devices_Read_KeepAlive_Button', 'n_clicks'),
        Input('Devices_KeepAlive_Slider', 'value'),
        Input('Devices_Reboot_Button', 'n_clicks'),
        Input('Devices_Shutdown_Button', 'n_clicks'),
        ],
    [
        State('Devices_Tab_Variables', 'children')
        ],
    )
def Devices_Tab_Buttons(Devices_Dropdown, Devices_Read_Config_Button, Devices_Save_Config_Button, Devices_Send_Config_Button, Devices_Read_KeepAlive_Button, Devices_KeepAlive_Slider, Devices_Reboot_Button, Devices_Shutdown_Button, Devices_Tab_Variables):

    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    Button_List = [Devices_Read_Config_Button, Devices_Save_Config_Button, Devices_Send_Config_Button, Devices_Read_KeepAlive_Button, Devices_KeepAlive_Slider, Devices_Reboot_Button, Devices_Shutdown_Button]
    Button_List_Text = ['Devices_Read_Config_Button', 'Devices_Save_Config_Button', 'Devices_Send_Config_Button', 'Devices_Read_KeepAlive_Button', 'Devices_KeepAlive_Slider', 'Devices_Reboot_Button', 'Devices_Shutdown_Button']

    # Check if buttons was presses
    for i in range(len(Button_List)):
        if Button_List[i] != int(Devices_Tab_Variables.get(Button_List_Text[i], 0)):
            Devices_Tab_Variables[Button_List_Text[i]] = Button_List[i]
            Devices_Tab_Variables['Last_Click'] = Button_List_Text[i]
            break

    # Check if the slider moved

    # Reset Last_Click if dropdown changes to prevent issuen with clicks happening when the next device is selected
    if Devices_Tab_Variables.get('Devices_Dropdown', 'None') != Devices_Dropdown:
        Devices_Tab_Variables['Devices_Dropdown'] = Devices_Dropdown
        Devices_Tab_Variables['Last_Click'] = "None"

    return Generate_Variable_String(Devices_Tab_Variables)


# ======================================== Devices Tab - Callbacks ========================================
# Update Device json Config
@app.callback(
    Output('Devices_json_Config_String', 'value'),
    [
        Input('Devices_Tab_Variables', 'children'),
        ],
    )
def Devices_Tab_json_Config_Show(Devices_Tab_Variables):
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    return MQTT_Config_New(Devices_Tab_Variables.get('Devices_Dropdown', "None"))


# Update Device KeepAlive graph
@app.callback(
    Output('Devices_KeepAlive_Graph', 'figure'),
    [
        Input('Devices_Tab_Variables', 'children'),
        Input('Devices_KeepAlive_Slider', 'value'),
        ],
    )
def Devices_Tab_KeepAlive_Show(Devices_Tab_Variables, Devices_KeepAlive_Slider):

    # Import variables from div able
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Devices_Tab_Variables.get('Devices_Dropdown', "None") == "None":
        return {'data': ''}

    # ======================================== Read KeepAlive ========================================
    else:
        df = SQL_Read_df("SELECT LastKeepAlive, UpFor, FreeMemory, SoftwareVersion, IP, RSSI FROM DobbyLog.KeepAliveMonitor WHERE Device = '" + str(Devices_Tab_Variables['Devices_Dropdown']) + "' ORDER BY id DESC LIMIT " + str(Devices_Tab_Variables['Devices_KeepAlive_Slider']) + ";")

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
        Return_Data["data"].append({
            'x': df.LastKeepAlive,
            'y': df.SoftwareVersion, 'name': "Software Version",
            'line': {"shape": 'spline'}
        })

        return {'data': Return_Data}


# Update Device Config rows
@app.callback(
    Output('Devices_Config_Table', 'rows'),
    [
        Input('Devices_Tab_Variables', 'children'),
        ],
    [
        State('Devices_Config_Table', 'rows'),
        ]
    )
def Devices_Tab_Config_Show(Devices_Tab_Variables, Devices_Config_Table):

    # Open db connection
    db_Write_Connection = Open_db('Dobby')
    db_Write_Curser = db_Write_Connection.cursor()

    # Import variables from div able
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Devices_Tab_Variables['Devices_Dropdown'] == "None":
        Close_db(db_Write_Connection, db_Write_Curser)
        return [{'Setting': '', 'Value': ''}]

    # ======================================== Save Config ========================================
    elif Devices_Tab_Variables.get('Last_Click', "None") == "Devices_Save_Config_Button":
        Current_Config = Generate_Device_Config_Dict(Devices_Tab_Variables['Devices_Dropdown'], db_Write_Curser)

        # Needed to refer between tables
        i = 0

        # Needed so you dont change the config id when no changes is made
        Config_Changes = {}

        for Current_Config_Row in Current_Config:

            # If value is '' set it to NULL
            if Devices_Config_Table[i]['Value'] == '':
                Config_Changes[Devices_Config_Table[i]['Setting'][0]] = 'NULL'

            elif Devices_Config_Table[i]['Value'][0] != Current_Config_Row['Value'][0]:
                # Add chnages to chnages dict
                Config_Changes[Devices_Config_Table[i]['Setting'][0]] = Devices_Config_Table[i]['Value']

            i = i + 1

        if Config_Changes != {}:
            # Get device id for use in sql changes below
            db_Write_Curser.execute("SELECT id FROM Dobby.DeviceConfig WHERE Hostname='" + Devices_Tab_Variables['Devices_Dropdown'] + "' AND Config_Active='1';")
            Device_id = db_Write_Curser.fetchone()
            Device_id = str(Device_id[0])

            # Apply changes
            for key, value in Config_Changes.iteritems():
                if value is 'NULL':
                    db_Write_Curser.execute("UPDATE `Dobby`.`DeviceConfig` SET `" + str(key) + "`=NULL WHERE `id`='" + Device_id + "';")
                else:
                    db_Write_Curser.execute("UPDATE `Dobby`.`DeviceConfig` SET `" + str(key) + "`='" + str(value) + "' WHERE `id`='" + Device_id + "';")

            # Get Current Config_ID
            db_Write_Curser.execute("SELECT Config_ID FROM Dobby.DeviceConfig WHERE `id`='" + Device_id + "';")
            Current_Config_ID = db_Write_Curser.fetchone()

            # Update Config_ID
            db_Write_Curser.execute("UPDATE `Dobby`.`DeviceConfig` SET `Config_ID`='" + str(Current_Config_ID[0] + 1) + "' WHERE `id`='" + Device_id + "';")

            # Update Last modified
            db_Write_Curser.execute("UPDATE `Dobby`.`DeviceConfig` SET `Date_Modified`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + Device_id + "';")

    # ======================================== Send Config ========================================
    elif Devices_Tab_Variables.get('Last_Click', "None") == "Devices_Send_Config_Button":
        MQTT.single(System_Header.Value[0] + "/Commands/Dobby/Config", Devices_Tab_Variables['Devices_Dropdown'] + ",-1;", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})

    # ======================================== Return table ========================================
    Return_Dict = Generate_Device_Config_Dict(Devices_Tab_Variables['Devices_Dropdown'], db_Write_Curser)

    Close_db(db_Write_Connection, db_Write_Curser)

    return Return_Dict


# ======================================== MonitorAgent - MonitorAgent_Tab_Variables ========================================
@app.callback(
    Output('MonitorAgent_Tab_Variables', 'children'),
    [
        Input('MonitorAgent_Dropdown', 'value'),
        Input('MonitorAgent_Slider', 'value'),
        Input('MonitorAgent_Button_Live', 'n_clicks'),
        Input('MonitorAgent_Dropdown_Agent_State', 'value'),
        Input('MonitorAgent_Current_State', 'value'),
        Input('MonitorAgent_Change_State', 'value'),
        ],
    [
        State('MonitorAgent_Tab_Variables', 'children')
        ]
    )
def MonitorAgent_Tab_Buttons(MonitorAgent_Dropdown, MonitorAgent_Slider, MonitorAgent_Button_Live, MonitorAgent_Dropdown_Agent_State, MonitorAgent_Current_State, MonitorAgent_Change_State, MonitorAgent_Tab_Variables):

    # Convert children to dict
    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)

    # Check if buttons was presses
    if MonitorAgent_Button_Live != int(MonitorAgent_Tab_Variables.get('MonitorAgent_Button_Live', 0)):

        Currernt_State = MonitorAgent_Tab_Variables.get('Show_Live_Graph', 'False')

        if Currernt_State == 'False':
            MonitorAgent_Tab_Variables['Show_Live_Graph'] = 'True'
        elif Currernt_State == 'True':
            MonitorAgent_Tab_Variables['Show_Live_Graph'] = 'False'

        # Save n_clicks
        MonitorAgent_Tab_Variables['MonitorAgent_Button_Live'] = MonitorAgent_Button_Live

    # Save Dropdown selection
    MonitorAgent_Tab_Variables['MonitorAgent_Dropdown'] = MonitorAgent_Dropdown

    if MonitorAgent_Dropdown is not None:
        # MonitorAgent_Dropdown_Agent_State
        # Controls the MonitorAgent

        # Open db connection
        db_MTB_Connection = Open_db('')
        db_MTB_Curser = db_MTB_Connection.cursor()

        db_MTB_Curser.execute("set autocommit = 1")

        if MonitorAgent_Tab_Variables.get('MonitorAgent_Dropdown_Agent_State', 'None') != MonitorAgent_Dropdown_Agent_State:
            # Set current state
            MonitorAgent_Tab_Variables['MonitorAgent_Dropdown_Agent_State'] = MonitorAgent_Dropdown_Agent_State

            # Get current agent state
            db_MTB_Curser.execute("SELECT Agent_ID, Agent_Enabled, Agent_State FROM Dobby.MonitorAgentConfig WHERE Agent_Name='" + str(MonitorAgent_Dropdown) + "';")
            SQL_Return = db_MTB_Curser.fetchone()

            print "SQL_Return"
            print SQL_Return

            # Change Agent State
            # Check if agent is enabled
            # Disabled
            if MonitorAgent_Dropdown_Agent_State == 'Disabled':
                # Disable agent
                if SQL_Return[1] is not 0:
                    db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Agent_Enabled`='0' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")
                    db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Date_Modified`='" + str(datetime.datetime.now()) + "' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")

            # Start agent
            elif SQL_Return[2] == 'Running':
                # Enable agent if disabled
                if SQL_Return[1] is 0:
                    db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Agent_Enabled`='1' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")

                # Change state
                db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Agent_State`='Start' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")
                db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Date_Modified`='" + str(datetime.datetime.now()) + "' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")
                print 'MARKER runnnnniiiiiiiiiiiiiiiinnnnnnnnnnnnnnnnnnnnnnnngggggggggggggggggggg'

            elif SQL_Return[2] == 'Stopped':
                db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Agent_State`='Stop' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")
                db_MTB_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET `Date_Modified`='" + str(datetime.datetime.now()) + "' WHERE `Agent_ID`='" + str(SQL_Return[0]) + "';")
                print 'MARKER Stoppeeeeedddddddddddddddddddddddddddddddddddddddddddd'

            if MonitorAgent_Dropdown_Agent_State == 'Running':
                print "State changed to"
                print 'MARKER RUNNING'

            elif MonitorAgent_Dropdown_Agent_State == 'Stopped':
                print "State changed to"
                print 'MARKER STOPPED'

            elif MonitorAgent_Dropdown_Agent_State == 'Disabled':
                print "State changed to"
                print 'MARKER STOPPED'
                print 'MARKER DISABLE'

        # Get min/max dates for slider

        db_MTB_Curser.execute("SELECT DateTime FROM DobbyLog.MonitorAgent WHERE Agent = '" + str(MonitorAgent_Dropdown) + "' ORDER BY id ASC LIMIT 1;")
        Min_Date = db_MTB_Curser.fetchone()

        db_MTB_Curser.execute("SELECT DateTime FROM DobbyLog.MonitorAgent WHERE Agent = '" + str(MonitorAgent_Dropdown) + "' ORDER BY id DESC LIMIT 1;")
        Max_Date = db_MTB_Curser.fetchone()

        # Close db connection
        Close_db(db_MTB_Connection, db_MTB_Curser)

        if Min_Date is None or Max_Date is None:
            pass

        else:
            Min_Date = Min_Date[0]
            Max_Date = Max_Date[0]

            # Save min/max
            MonitorAgent_Tab_Variables['Slider_Min_Date'] = Min_Date
            MonitorAgent_Tab_Variables['Slider_Max_Date'] = Max_Date

            Time_Span = Max_Date - Min_Date
            Time_Jumps = Time_Span / 100

            # Save Low value
            if MonitorAgent_Slider[0] == 0:
                MonitorAgent_Tab_Variables['Slider_Value_Low'] = Min_Date
            elif MonitorAgent_Slider[0] == 100:
                MonitorAgent_Tab_Variables['Slider_Value_Low'] = Max_Date
            else:
                MonitorAgent_Tab_Variables['Slider_Value_Low'] = Min_Date + Time_Jumps * MonitorAgent_Slider[0]

                # removes ".######" from the datetime string
                if len(str(MonitorAgent_Tab_Variables['Slider_Value_Low'])) > 19:
                    MonitorAgent_Tab_Variables['Slider_Value_Low'] = str(MonitorAgent_Tab_Variables['Slider_Value_Low'])[:-7]

                    # Save high value
                    if MonitorAgent_Slider[1] == 0:
                        MonitorAgent_Tab_Variables['Slider_Value_High'] = Min_Date
                    elif MonitorAgent_Slider[1] == 100:
                        MonitorAgent_Tab_Variables['Slider_Value_High'] = Max_Date
                    else:
                        MonitorAgent_Tab_Variables['Slider_Value_High'] = Min_Date + Time_Jumps * MonitorAgent_Slider[1]

                        # removes ".######" from the datetime string
                        if len(str(MonitorAgent_Tab_Variables['Slider_Value_High'])) > 19:
                            MonitorAgent_Tab_Variables['Slider_Value_High'] = str(MonitorAgent_Tab_Variables['Slider_Value_High'])[:-7]

    # Convert dict to children
    return Generate_Variable_String(MonitorAgent_Tab_Variables)


# ======================================== MonitorAgent - MonitorAgent_Update_Dropdown_Agent_State ========================================
@app.callback(
    Output('MonitorAgent_Configuration_Main_Div', 'style'),
    [
        Input('MonitorAgent_Tab_Variables', 'children'),
        ],
    [
        # State('MonitorAgent_Configuration_Main_Div', 'hidden'),
    ]
    )
def MonitorAgent_Update_Dropdown_Agent_State(MonitorAgent_Tab_Variables):

    # Convert children to dict
    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)

    # MonitorAgent_Dropdown_Agent_State
    if MonitorAgent_Tab_Variables.get('MonitorAgent_Dropdown_Agent_State', 'None') == 'None' or None:
        return {'display': 'none'}
    else:
        return {'display': 'inline'}


# ======================================== MonitorAgent - MonitorAgent_Current_State ========================================
@app.callback(
    Output('MonitorAgent_Current_State', 'children'),
    [
        Input('MonitorAgent_Tab_Variables', 'children')
        ],
    [
        State('MonitorAgent_Dropdown', 'value'),
        ]
    )
def MonitorAgent_Update_State(MonitorAgent_Tab_Variables, MonitorAgent_Dropdown):

    # Do nothing if no agent is selected
    if MonitorAgent_Dropdown is None:
        return "Current State: "

    SQL_Return = SQL_Read("SELECT Agent_Enabled, Agent_State FROM Dobby.MonitorAgentConfig WHERE Agent_Name='" + str(MonitorAgent_Dropdown) + "';")

    Return_String = "Current State: "

    # Check if agent is enabled
    # Disabled
    if SQL_Return[0][0] is 0:
        Return_String = Return_String + 'Disabled'

    elif SQL_Return[0][1] == 'Running':
        Return_String = Return_String + 'Running'

    elif SQL_Return[0][1] == 'Stopped':
        Return_String = Return_String + 'Stopped'

    return Return_String


# ======================================== MonitorAgent - Live button text ========================================
@app.callback(
    Output('MonitorAgent_Button_Live', 'children'),
    [
        Input('MonitorAgent_Tab_Variables', 'children')
        ],
    [
        State('MonitorAgent_Button_Live', 'children'),
        ]
    )
def MonitorAgent_Update_Live_Button_Text(MonitorAgent_Tab_Variables, MonitorAgent_Button_Live):
    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)

    if MonitorAgent_Tab_Variables.get('Show_Live_Graph', 'False') == 'True':
        return 'Switch to History'
    else:
        return 'Switch to Live'


# ======================================== MonitorAgent ========================================
@app.callback(
    Output('MonitorAgent_Graph_Live_Interval', 'interval'),
    [
        Input('MonitorAgent_Tab_Variables', 'children'),
        ]
    )
def MonitorAgent_Update_Interval(MonitorAgent_Tab_Variables):
    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)

    if MonitorAgent_Tab_Variables.get('Show_Live_Graph', 'False') == 'False':
        # 3600000 ms = 1 hour aka disabled
        return 3600000
    else:
        return 1000


# ======================================== MonitorAgent ========================================
@app.callback(
    Output('MonitorAgent_Graph', 'figure'),
    [
        Input('MonitorAgent_Tab_Variables', 'children'),
        Input('MonitorAgent_Graph_Live_Interval', 'n_intervals'),
        ]
    )
def MonitorAgent_Update_Graph(MonitorAgent_Tab_Variables, MonitorAgent_Graph_Live_Interval):
    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)

    Return_Data = {'data': [{}]}

    # Do nothing untill a Agent is selected
    if MonitorAgent_Tab_Variables.get('MonitorAgent_Dropdown', 'None') == 'None':
        pass

    # Live graph
    elif MonitorAgent_Tab_Variables.get('Show_Live_Graph', 'False') == 'True':

        # FIX - Add update time adjustment
        # FIX - Move this to a slider
        Live_Graph_Limit = 50

        # db_SQL_Connection = Open_db('')
        df = SQL_Read_df("SELECT DateTime, Source, Value FROM DobbyLog.MonitorAgent WHERE Agent = '" + MonitorAgent_Tab_Variables['MonitorAgent_Dropdown'] + "' ORDER BY id DESC LIMIT " + str(Live_Graph_Limit) + ";")
        # db_SQL_Connection.close()

        for i in df.Source.unique():
                Return_Data["data"].append({
                    'x': df.DateTime[df['Source'] == i],
                    'y': df.Value[df['Source'] == i], 'name': i,
                    'line': {"shape": 'spline'}
                })

    # History graph
    elif MonitorAgent_Tab_Variables.get('Show_Live_Graph', 'False') == 'False':

        df = SQL_Read_df("SELECT DateTime, Source, Value FROM DobbyLog.MonitorAgent WHERE Agent = '" + MonitorAgent_Tab_Variables['MonitorAgent_Dropdown'] + "' AND DateTime >= '" + str(MonitorAgent_Tab_Variables['Slider_Value_Low']) + "' AND DateTime <= '" + str(MonitorAgent_Tab_Variables['Slider_Value_High']) + "' ORDER BY DateTime;")

        for i in df.Source.unique():
                Return_Data["data"].append({
                    'x': df.DateTime[df['Source'] == i],
                    'y': df.Value[df['Source'] == i], 'name': i,
                    'line': {"shape": 'spline'}
                })

    return {'data': Return_Data, 'layout': 'ytest'}


# ======================================== MonitorAgent - Slider Marks ========================================
@app.callback(
    Output('MonitorAgent_Slider', 'marks'),
    [
        Input('MonitorAgent_Tab_Variables', 'children')
        ],
    [
        # State('MonitorAgent_Tab_Variables', 'children'),
        ]
    )
def MonitorAgent_Update_Slider_Marks(MonitorAgent_Tab_Variables):

    MonitorAgent_Tab_Variables = Generate_Variable_Dict(MonitorAgent_Tab_Variables)

    if MonitorAgent_Tab_Variables.get('MonitorAgent_Dropdown', 'None') == 'None':
        return {}

    Time_Span = MonitorAgent_Tab_Variables['Slider_Max_Date'] - MonitorAgent_Tab_Variables['Slider_Min_Date']
    Time_Jumps = Time_Span / 10

    Marks_Dict = {}

    # Add the first and last label
    Marks_Dict['0'] = {'label': MonitorAgent_Tab_Variables['Slider_Min_Date']}
    Marks_Dict['100'] = {'label': MonitorAgent_Tab_Variables['Slider_Max_Date']}

    # Add the rest of the labels
    for i in range(1, 10):
        Name = str(i * 10)
        Label = str(MonitorAgent_Tab_Variables['Slider_Min_Date'] + Time_Jumps * i)

        # The [:-7] removes the ms from the end of the string
        if "." in Label:
            Label = Label[:-7]

        Marks_Dict[Name] = {'label': Label}

    return Marks_Dict


# FIX - Move css to local storage
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


if __name__ == '__main__':
    app.run_server(debug=True,  host='0.0.0.0')
