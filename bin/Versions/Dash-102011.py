#!/usr/bin/python

# Improvements
# Add limit slider to live graph
# Get live graph working

# Changelog
# See Changelog/Dash.txt

from pathlib import Path

import dash
import dash_auth

from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dte
import dash_table as dt

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

# Scacda
import plotly.graph_objs as go


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

    try:
        db_SQL_Curser.execute(SQL_String)
        db_List = db_SQL_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning):
        Close_db(db_SQL_Connection, db_SQL_Curser)
        return []

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
    
    try:
        db_SQL_Curser.execute(SQL_String)
        db_Resoult = db_SQL_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print e
        return ['None']

    # Close db connection
    Close_db(db_SQL_Connection, db_SQL_Curser)

    return db_Resoult


def Column_Name_Check(Column_Name):

    Name_Field_String = 'Name'

    if Column_Name == 'DeviceConfig':
        Name_Field_String = 'Hostname'
    if Column_Name == 'Device Config Base':
        Name_Field_String = 'Hostname'
    elif Column_Name == 'Users':
        Name_Field_String = 'Username'

    return Name_Field_String


# ======================================== Generate_Config_List ========================================
def Generate_Config_List(Config_Dropdown, Config_Dropdown_Line, db_Curser=None):

    if Config_Dropdown is None or Config_Dropdown == 'None' or Config_Dropdown_Line is None or Config_Dropdown_Line == 'None':
        return [{'Setting': '', 'Value': ''}]

    Close_db_Connection = False

    if db_Curser is None:
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()
        Close_db_Connection = True

    Name_Field_String = Column_Name_Check(Config_Dropdown)

    # if dropdownline = -- New Entry -- then get row names and default values
    # and display then when you press save that should write the entry with no errors

    try:
        db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='" + Config_Dropdown.replace(" ", "_") + "';")
        Settings = db_Curser.fetchall()

        if Config_Dropdown_Line != "-- New Entry --":
            db_Curser.execute("SELECT * FROM Dobby." + Config_Dropdown.replace(" ", "_") + " WHERE `" + Name_Field_String + "`='" + Config_Dropdown_Line + "';")
            Values = db_Curser.fetchone()
            # New Entry
        else:
            db_Curser.execute("SELECT Column_Default, IS_NULLABLE FROM Information_Schema.Columns WHERE table_schema='Dobby' AND table_name='" + Config_Dropdown.replace(" ", "_") + "';")
            Values = db_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning):
        if Close_db_Connection is True:
            # Close db connection
            Close_db(db_Connection, db_Curser)
        return [{'Setting': '', 'Value': ''}]

    if Settings is None:
        if Close_db_Connection is True:
            # Close db connection
            Close_db(db_Connection, db_Curser)
        return [{'Setting': '', 'Value': ''}]

    Row_List = []
    Config_Ignore_List = ['id', 'Last_Modified']

    for i in range(len(Settings)):
        if Settings[i][0] not in Config_Ignore_List:
            if Config_Dropdown_Line != "-- New Entry --":
                Row_List.append({'Setting': [Settings[i][0]], 'Value': [Values[i]]})
            # New Entry
            else:
                # Field has to have a value
                if Values[i][1] == 'NO' and Values[i][0] is None:
                    Row_List.append({'Setting': [Settings[i][0]], 'Value': '-- Change me --'})
                else:
                    Row_List.append({'Setting': [Settings[i][0]], 'Value': [Values[i][0]]})

    if Close_db_Connection is True:
        # Close db connection
        Close_db(db_Connection, db_Curser)

    return Row_List


# ======================================== Generate_Device_Config_Dict ========================================
def Generate_Device_Config_Dict(Selected_Device, db_Curser):

    if Selected_Device is None:
        return None

    db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='DeviceConfig';")
    Device_Config_Setting = db_Curser.fetchall()

    db_Curser.execute("SELECT * FROM Dobby.DeviceConfig WHERE Hostname='" + Selected_Device + "';")
    Device_Config_Value = db_Curser.fetchone()

    Row_List = []
    Config_Ignore_List = ['id', 'Last_Modified', 'Config_Active', 'Config_ID']

    i = 0

    for Setting in Device_Config_Setting:
        if Setting[0] not in Config_Ignore_List:
            Row_List.append({'Setting': [Setting[0]], 'Value': [Device_Config_Value[i]]})
        i = i + 1

    return Row_List


# ======================================== Generate_Variable_Dict ========================================
def Generate_Variable_Dict(String):

    Return_Dict = {}

    # Do nothing if string en empthy
    if String == "" or String is None:
        pass

    else:
        String = str(String).replace("u'", "'")

        for i in String.split('<*>'):
            # Skip if line is ''
            if i == '':
                continue

            Dict_Entry = i.split('<;>')

            # I asume that 2 x - and 2  : = datetime
            if Dict_Entry[1].count('-') == 2 and Dict_Entry[1].count(':') == 2:
                # If 7th last char is . then the datetime has ms in it, it needs to be removed
                if Dict_Entry[1][19:-6] == ".":
                    Dict_Entry[1] = datetime.datetime.strptime(Dict_Entry[1][:-7], '%Y-%m-%d %H:%M:%S')
                else:
                    Dict_Entry[1] = datetime.datetime.strptime(Dict_Entry[1], '%Y-%m-%d %H:%M:%S')

            elif "[" and "]" in Dict_Entry[1]:
                # Remove "'"
                Dict_Entry[1] = Dict_Entry[1].replace("'", "")
                # Remove brackets
                Dict_Entry[1] = Dict_Entry[1].replace("[", "")
                Dict_Entry[1] = Dict_Entry[1].replace("]", "")
                # Convert to list
                Dict_Entry[1] = Dict_Entry[1].split(', ')

            Return_Dict[Dict_Entry[0]] = Dict_Entry[1]

    return Return_Dict


# ======================================== Generate_Variable_Dict ========================================
def Generate_Variable_String(Dict):

    Return_String = ''

    for Key, Value in Dict.iteritems():
        Return_String = Return_String + str(Key) + '<;>' + str(Value) + '<*>'

    return Return_String


# ======================================== Generate_Device_Config_Dict ========================================
def Generate_System_Log_Table_Columns(System_Log_Dropdown):

    if System_Log_Dropdown is None or System_Log_Dropdown == 'None':
        return [{}]

    elif System_Log_Dropdown == "Device Log":
        return [{'id': 'DateTime', 'name': 'DateTime'}, {'id': 'Device', 'name':'Device'}, {'id': 'Topic', 'name':'Topic'}, {'id': 'Payload', 'name': 'Payload'}]

    elif System_Log_Dropdown == "System Log":
        return [{'id': 'DateTime', 'name': 'DateTime'}, {'id': 'LogLevel', 'name': 'LogLevel'}, {'id': 'Source', 'name': 'Source'}, {'id': 'Header', 'name': 'Header'}, {'id': 'Text', 'name': 'Text'}]
    
    return None


# ======================================== Tabs_List ========================================
def Tabs_List():

    Tabs_List = []

    Tabs_List.append(dcc.Tab(label='Alerts', value='Alerts_Tab'))

    Tabs_List.append(dcc.Tab(label='Config', value='Config_Tab'))

    Tabs_List.append(dcc.Tab(label='Buttons', value='Buttons_Tab'))

    # Tabs_List.append(dcc.Tab(label='Devices', value='Config_Tab'))

    Tabs_List.append(dcc.Tab(label='Live', value='Live_Tab'))

    Tabs_List.append(dcc.Tab(label='Log Graph', value='Log_Graph_Tab'))

    Tabs_List.append(dcc.Tab(label='System Log', value='System_Log_Tab'))

    Tabs_List.append(dcc.Tab(label='System', value='System_Tab'))

    return Tabs_List


def Config_Tab_Dropdown_List():

    return ['APC Monitor', 'DashButtons', 'DeviceConfig', 'Device Config Base', 'Log Trigger', 'Mail Trigger', 'Spammer', 'Users']


def Log_Graph_Tab_Dropdown_List():

    return ['APC Monitor', 'Log Trigger', 'KeepAliveMonitor']


# MISC
# import collections
# import ast

# json
# import json

# MISC
Version = 102011
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number


# MySQL
MySQL_Server = 'localhost'
MySQL_Username = 'dobby'
MySQL_Password = 'HereToServe'

db_pd_Connection = MySQLdb.connect(host=MySQL_Server, user=MySQL_Username, passwd=MySQL_Password)

db_Connection = Open_db("Dobby")
db_Curser = db_Connection.cursor()

# db_Curser.execute("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Broker';")
# db_Fetch = db_Curser.fetchone()
# MQTT_Broker = db_Fetch[0]

db_Curser.execute("SELECT COUNT(id) FROM Dobby.DashButtons;")
db_Fetch = db_Curser.fetchone()
# FIX - Move to global var its ok :-)
DashButtons_Number_Of = db_Fetch[0]

# FIX - Find a betting solution, maybe make a dummy button
# If DashButtons_Number_Of == 0 the script will crash
if DashButtons_Number_Of == 0:
    DashButtons_Number_Of = 1



# Close db connection
Close_db(db_Connection, db_Curser)


# Dobby
MQTT_Broker = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Broker';", con=db_pd_Connection)
MQTT_Port = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Port';", con=db_pd_Connection)
MQTT_Username = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Username';", con=db_pd_Connection)
MQTT_Password = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Password';", con=db_pd_Connection)
System_Header = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='System' AND Target='Dobby' AND Name='Header';", con=db_pd_Connection)
Log_db = pd.read_sql("Select Value From Dobby.SystemConfig where Target='Dobby' AND Header='Log' AND `Name`='db';", con=db_pd_Connection)

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


# ======================================== Layout ========================================
# ======================================== Layout ========================================
# ======================================== Layout ========================================
app.layout = html.Div([


    dcc.Tabs(id="tabs", value='Buttons_Tab', children=Tabs_List()),

    html.Div(id='Main_Tabs'),

    # No idea why this needs to be here, if its not the tabs with datatables does not load
    html.Div([
        dte.DataTable(rows=[{}]),
        ], style={"display": "none"}),

    # Places to store variables
    html.Div([
        html.Div(id='Alerts_Tab_Variables', children=""),
        html.Div(id='Buttons_Tab_Variables', children=""),
        html.Div(id='Config_Tab_Variables', children=""),
        # html.Div(id='Device_Tab_Variables', children=""),
        html.Div(id='Live_Tab_Variables', children=""),
        html.Div(id='Log_Graph_Tab_Variables', children=""),
        html.Div(id='System_Log_Tab_Variables', children=""),
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
        State('Alerts_Tab_Variables', 'children'),
        State('Buttons_Tab_Variables', 'children'),
        State('Config_Tab_Variables', 'children'),
        # State('Device_Tab_Variables', 'children'),
        State('Live_Tab_Variables', 'children'),
        State('Log_Graph_Tab_Variables', 'children'),
        State('System_Log_Tab_Variables', 'children'),
        State('System_Tab_Variables', 'children'),
        ]
    )
def render_content(tab, Alerts_Tab_Variables, Buttons_Tab_Variables, Config_Tab_Variables, Live_Tab_Variables, Log_Graph_Tab_Variables, System_Log_Tab_Variables, System_Tab_Variables):
    # ======================================== Alerts Tab ========================================
    # ======================================== Alerts Tab ========================================
    # ======================================== Alerts Tab ========================================
    if tab == 'Alerts_Tab':
        Alerts_Tab_Variables = Generate_Variable_Dict(Alerts_Tab_Variables)

        return html.Div([
            # Config table
            dte.DataTable(
                id='Alerts_Table',
                rows=[],
                columns=['Source', 'Text', 'Status', 'Timestamp'],
                min_height='72vh',
                resizable=True,
                editable=True,
                filterable=True,
                sortable=True,
                ),
        ], style={'marginBottom': 50, 'marginTop': 25}, id='Alerts_Tab')

    # ======================================== Buttons Tab ========================================
    # ======================================== Buttons Tab ========================================
    # ======================================== Buttons Tab ========================================
    elif tab == 'Buttons_Tab':

        Buttons_Tab_Variables = Generate_Variable_Dict(Buttons_Tab_Variables)

        db_Resoult = SQL_Read('SELECT * FROM Dobby.DashButtons;')

        Button_List = []

        for Entry in db_Resoult:
            if Entry[2] == "Button":
                Button_List.append(html.Button(str(Entry[1]), id=str('DBTN_' + str(Entry[0])), n_clicks=0),)

        return html.Div([
            html.Div(
                id="Buttons_Tab_Div",
                children=Button_List,
                style={}
                )
        ], id='Buttons_Tab')

    # ======================================== Live Tab ========================================
    # ======================================== Live Tab ========================================
    # ======================================== Live Tab ========================================
    elif tab == 'Live_Tab':
        Live_Tab_Variables = Generate_Variable_Dict(Live_Tab_Variables)

        return html.Div(
            id='Live_Tab',
            children=[
                # Dropdown to select logs
                dcc.Dropdown(
                    id='Live_Dropdown',
                    options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT DISTINCT Name FROM `" + Log_db.Value[0] + "`.Log_Graph;")],
                    multi=True,
                    value=Live_Tab_Variables.get('Live_Dropdown', None),
                ),

                dcc.Graph(
                    id='Live_Graph',
                    style={
                        'height': '70vh',
                        'width': '95vw',
                        'padding': 5,
                        }
                    ),

                html.Div(
                    id='Live_Tab',
                    style={
                        'width': '90vw',
                        'padding': 50,
                        'display': 'inline-block'
                        },
                    children=[
                        dcc.RangeSlider(
                            id='Live_Slider',
                            min=0,
                            max=100,
                            step=1,
                            value=[95, 100],
                            allowCross=False,
                            marks={},
                        ),
                    ],
                ),
            ],
        )

    # ======================================== Config Tab ========================================
    # ======================================== Config Tab ========================================
    # ======================================== Config Tab ========================================
    elif tab == 'Config_Tab':
        Config_Tab_Variables = Generate_Variable_Dict(Config_Tab_Variables)

        return html.Div(
            id='Config_Tab',
            children=[
                # Dropdown to select What to configure
                dcc.Dropdown(
                    id='Config_Dropdown',
                    options=[{'label': Config_Option, 'value': Config_Option} for Config_Option in Config_Tab_Dropdown_List()],
                    value=Config_Tab_Variables.get('Config_Dropdown', None),
                    ),
                # Dropdown to select What LINE to configure
                dcc.Dropdown(
                    id='Config_Dropdown_Line',
                    options=[],
                    value=Config_Tab_Variables.get('Config_Dropdown_Line', None),
                    ),
                # Config table
                dte.DataTable(
                    id='Config_Table',
                    rows=[],
                    columns=['Setting', 'Value'],
                    min_height='72vh',
                    resizable=True,
                    editable=True,
                    filterable=True,
                    sortable=True,
                    ),
                html.Button('Read', id='Config_Read', n_clicks=int(Config_Tab_Variables.get('Config_Read', 0)), style={'margin-top': '5px'}),
                html.Button('Delete Row', id='Config_Delete_Row', n_clicks=int(Config_Tab_Variables.get('Config_Delete_Row', 0)), style={'margin-left': '10px', 'margin-top': '5px'}),
                html.Button('Save', id='Config_Save', n_clicks=int(Config_Tab_Variables.get('Config_Save', 0)), style={'margin-left': '10px', 'margin-top': '5px'}),
                ],
            ),

    # ======================================== Log Graph Tab ========================================
    # ======================================== Log Graph Tab ========================================
    # ======================================== Log Graph Tab ========================================
    elif tab == 'Log_Graph_Tab':

        Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

        return html.Div(
            id='Log_Graph_Tab',
            children=[

                dcc.Dropdown(
                    id='Log_Graph_Dropdown',
                    options=[{'label': Log_Graph_Option, 'value': Log_Graph_Option} for Log_Graph_Option in Log_Graph_Tab_Dropdown_List()],
                    value=Log_Graph_Tab_Variables.get('Log_Graph_Dropdown', None),
                    ),

                # Dropdown to select logs
                dcc.Dropdown(
                    id='Log_Graph_Dropdown_Entry',
                    options=[],
                    value=Log_Graph_Tab_Variables.get('Log_Graph_Dropdown_Entry', None),
                    multi=True,
                    ),

                # Dropdown to select json tags or rows
                dcc.Dropdown(
                    id='Log_Graph_Dropdown_Rj',
                    options=[],
                    value=Log_Graph_Tab_Variables.get('Log_Graph_Dropdown_Rj', None),
                    multi=True,
                    ),

                # The graph
                dcc.Graph(
                    id='Log_Graph_Graph',
                    style={
                        'height': '70vh',
                        'width': '95vw',
                        'padding': 5,
                        }
                    ),

                html.Div(
                    id='Log_Graph_Tab_Lider',
                    style={
                        'width': '90vw',
                        'padding': 50,
                        'display': 'inline-block'
                        },
                    children=[
                        dcc.RangeSlider(
                            id='Log_Graph_Slider',
                            min=0,
                            max=100,
                            step=1,
                            value=[95, 100],
                            allowCross=False,
                            marks={},
                        ),
                    ],
                ),
            ],
        )

    # ======================================== System Log Tab ========================================
    # ======================================== System Log Tab ========================================
    # ======================================== System Log Tab ========================================
    elif tab == 'System_Log_Tab':
        System_Log_Tab_Variables = Generate_Variable_Dict(System_Log_Tab_Variables)

        return html.Div(
            id='System_Log_Tab',
            children=[
                # Dropdown to select log
                dcc.Dropdown(
                    id='System_Log_Dropdown',
                    options=[{'label': System_Log_Tab_Option, 'value': System_Log_Tab_Option} for System_Log_Tab_Option in ["Device Log","System Log"]],
                    value=System_Log_Tab_Variables.get('System_Log_Dropdown', None),
                ),
                # Datatable to display log
                dt.DataTable(
                    id='System_Log_Tab_Table',
                    # columns=["test"],
                    columns=[Generate_System_Log_Table_Columns(System_Log_Tab_Variables.get('System_Log_Dropdown', "None"))],
                    # min_height='72vh',
                    # resizable=True,
                    # editable=True,
                    sorting=True,
                    data=[{}],
                ),
                # Button to read logs
                html.Button(
                    'Read log',
                    id='System_Log_Read_Button',
                    n_clicks=0,
                    style={'margin-top': '5px'}
                ),
                # Input to enter number of lines to read
                dcc.Input(
                    id='System_Log_Number_Of_Input',
                    placeholder='Number of lines to read',
                    type='number',
                    value='100',
                ),
                # Slider to slect timeframe
                # dcc.RangeSlider(
                #     id='System_Log_From_To_Slider',
                #     min=0,2
                #     max=100,
                #     step=1,
                #     value=[95, 100],
                #     allowCross=False,
                #     marks={},
                # ),
                # dcc.Dropdown(
                #     id='System_Log_Number_Of_Dropdown',
                #     options=[{'label': System_Log_Tab_Option, 'value': System_Log_Tab_Option} for System_Log_Tab_Option in [10, 100, 1000, 10000]],
                #     value=System_Log_Tab_Variables.get('System_Log_Dropdown', None),
                # ),
            ],
        )

    # ======================================== System Tab ========================================
    # ======================================== System Tab ========================================
    # ======================================== System Tab ========================================
    elif tab == 'System_Tab':
        System_Tab_Variables = Generate_Variable_Dict(System_Tab_Variables)

        return html.Div([
            html.Button('Check for updates', id='System_Update_Button', n_clicks=0, style={'margin-top': '5px'}),
            html.Button('Quit', id='System_Quit_Button', n_clicks=0, style={'margin-left': '5px', 'margin-top': '5px'}),
        ], id='System_Tab')


# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================


# ======================================== Button Tab - Callbacks ========================================
# Button Tabs
@app.callback(
    Output('Buttons_Tab_Variables', 'children'),
    [
        Input('DBTN_' + str(i), 'n_clicks') for i in range(DashButtons_Number_Of)
        ],
    [
        State('Buttons_Tab_Variables', 'children'),
        ],
    )
def Buttons_Tab_Buttons(*args):

    
    print "hit"

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

# ======================================== Config Tab - Callbacks ========================================
# Config_Tab_Variables
@app.callback(
    Output('Config_Tab_Variables', 'children'),
    [
        Input('Config_Dropdown', 'value'),
        Input('Config_Dropdown_Line', 'value'),
        Input('Config_Read', 'n_clicks'),
        Input('Config_Delete_Row', 'n_clicks'),
        Input('Config_Save', 'n_clicks'),
        ],
    [
        State('Config_Table', 'rows'),
        State('Config_Tab_Variables', 'children'),
        ]
    )
def Config_Tab_Variables(Config_Dropdown, Config_Dropdown_Line, Config_Read, Config_Delete_Row, Config_Save, Config_Table, Config_Tab_Variables):

    Config_Tab_Variables = Generate_Variable_Dict(Config_Tab_Variables)

    # Dropdowns
    Config_Tab_Variables['Config_Dropdown'] = Config_Dropdown
    if Config_Dropdown is None:
        Config_Tab_Variables['Config_Dropdown'] = "None"
        Config_Tab_Variables['Config_Dropdown_Line'] = "None"
    else:
        if Config_Dropdown_Line is None:
            Config_Tab_Variables['Config_Dropdown_Line'] = "None"
        else:
            Config_Tab_Variables['Config_Dropdown_Line'] = Config_Dropdown_Line

    # # Button
    if int(Config_Tab_Variables.get('Config_Delete_Row', 0)) != int(Config_Delete_Row):
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT id FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY id DESC LIMIT 1;")
        Row_id = db_Curser.fetchone()
        Row_id = str(Row_id[0])

        print "Delete Row"
        db_Curser.execute("DELETE FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` WHERE `id`='" + Row_id + "';")

        Close_db(db_Connection, db_Curser)

    # Save
    elif int(Config_Tab_Variables.get('Config_Save', 0)) != int(Config_Save):
        if Config_Tab_Variables['Config_Dropdown_Line'] != "None":
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            Current_Config = Generate_Config_List(Config_Dropdown, Config_Dropdown_Line, db_Curser)

            # Needed to refer between tables
            i = 0

            # Needed so you dont change the config id when no changes is made
            Config_Changes = {}

            for Current_Config_Row in Current_Config:

                # if -- Change me -- is value then a field that needs a value has not been set hence break and do nothing
                # FIX - Add error message for below

                if Config_Table[i]['Value'] == '-- Change me --':
                    break

                elif Config_Table[i]['Value'][0] != Current_Config_Row['Value'][0]:
                    # Add chnages to chnages dict
                    Config_Changes[Config_Table[i]['Setting'][0]] = Config_Table[i]['Value']

                i = i + 1

            if Config_Changes != {}:

                Name_Field_String = Column_Name_Check(Config_Dropdown)

                # if New Entry get last entry an add one to it and use that for id
                if Config_Dropdown_Line == '-- New Entry --':
                    db_Curser.execute("SELECT id FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY id DESC LIMIT 1;")
                    Row_id = db_Curser.fetchone()

                    # If none then there is not entries so set to 1
                    if Row_id is None:
                        Row_id = str(1)
                    else:
                        Row_id = str(Row_id[0] + 1)

                    Setting_String = ''
                    Value_String = ''

                    for value in Config_Table:
                        Setting_String = Setting_String + "`" + str(value['Setting'][0]) + "`, "
                        if "[u'" in str(value['Value']):
                            Value_String = Value_String + "'" + str(value['Value'][0]) + "', "
                        elif value['Value'] is None:
                            Value_String = Value_String + "NULL, "
                        elif value['Value'][0] is None:
                            Value_String = Value_String + "NULL, "
                        else:
                            Value_String = Value_String + "'" + str(value['Value']) + "', "

                    # Add id
                    Setting_String = "id, " + Setting_String
                    Value_String = "'" + Row_id + "', " + Value_String + "'"
                    # Add Last_Modified
                    # ", " is added in for loop above
                    Setting_String = Setting_String + "`Last_Modified`"
                    Value_String = Value_String[:-1] + "CURRENT_TIMESTAMP"

                    Value_String = Value_String.replace("'CURRENT_TIMESTAMP'", "CURRENT_TIMESTAMP")

                    db_Curser.execute("INSERT INTO `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` (" + Setting_String + ") VALUES (" + Value_String + ");")
                    # RM
                    print "INSERT INTO `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` (" + Setting_String + ") VALUES (" + Value_String + ");"

                # Get device id for use in sql changes below
                else:
                    db_Curser.execute("SELECT id FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` WHERE `" + Name_Field_String + "`='" + str(Config_Dropdown_Line) + "';")
                    Row_id = db_Curser.fetchone()
                    Row_id = str(Row_id[0])

                    # Apply changes
                    for key, value in Config_Changes.iteritems():
                        
                        # Not a 100% sure why a list apears here
                        if type(value) is list:
                            value = value[0]

                        if value is 'NULL':
                            # RM
                            # print "NULL - UPDATE `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` SET `" + str(key) + "`=NULL WHERE `id`='" + Row_id + "';"
                            db_Curser.execute("UPDATE `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` SET `" + str(key) + "`=NULL WHERE `id`='" + Row_id + "';")
                        else:
                            # RM
                            # print "UPDATE `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` SET `" + str(key) + "`='" + str(value) + "' WHERE `id`='" + Row_id + "';"
                            db_Curser.execute("UPDATE `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` SET `" + str(key) + "`='" + str(value) + "' WHERE `id`='" + Row_id + "';")

                    # Update Last modified
                    db_Curser.execute("UPDATE `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` SET `Last_Modified`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + Row_id + "';")

                    Config_List = ["DeviceConfig", "Device Config Base"]

                    if Config_Dropdown in Config_List:
                        # Get Current Config_ID
                        db_Curser.execute("SELECT Config_ID FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` WHERE `id`='" + Row_id + "';")
                        Current_Config_ID = db_Curser.fetchone()

                        # Update Config_ID
                        db_Curser.execute("UPDATE `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` SET `Config_ID`='" + str(Current_Config_ID[0] + 1) + "' WHERE `id`='" + Row_id + "';")

            # Close db connection
            Close_db(db_Connection, db_Curser)

    Config_Tab_Variables['Config_Read'] = Config_Read
    Config_Tab_Variables['Config_Delete_Row'] = Config_Delete_Row
    Config_Tab_Variables['Config_Save'] = Config_Save

    return Generate_Variable_String(Config_Tab_Variables)


# ======================================== Config Tab - Callbacks ========================================
@app.callback(
    Output('Config_Dropdown_Line', 'options'),
    [
        Input('Config_Dropdown', 'value'),
        Input('Config_Tab_Variables', 'children'),
        ],
    )
def Config_Tab_Line_Dropdown(Config_Dropdown, Config_Tab_Variables):

    Config_Tab_Variables = Generate_Variable_Dict(Config_Tab_Variables)

    if Config_Dropdown is None or Config_Dropdown == 'None':
        return {'label': '-- New Entry --', 'value': '-- New Entry --'}

    Name_Field_String = Column_Name_Check(Config_Dropdown)

    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    db_Curser.execute("SELECT id, `" + Name_Field_String + "` FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY `" + Name_Field_String + "`;")
    db_Fetch = db_Curser.fetchall()

    # Close db connection
    Close_db(db_Connection, db_Curser)

    Return_List = []

    Return_List.append({'label': '-- New Entry --', 'value': '-- New Entry --'})

    for Key, Value in db_Fetch:
        Return_List.append({'label': Value, 'value': Value})

    return Return_List


@app.callback(
    Output('Config_Table', 'rows'),
    [
        Input('Config_Dropdown', 'value'),
        Input('Config_Dropdown_Line', 'value'),
        Input('Config_Read', 'n_clicks'),
        Input('Config_Delete_Row', 'n_clicks'),
        ],
    [
        State('Config_Tab_Variables', 'children'),
    ]
    )
def Config_Tab_Table(Config_Dropdown, Config_Dropdown_Line, Config_Read, Config_Delete_Row, Config_Tab_Variables):

    Config_Tab_Variables = Generate_Variable_Dict(Config_Tab_Variables)

    try:
        if int(Config_Tab_Variables['Config_Delete_Row']) != Config_Delete_Row:
            return Generate_Config_List(Config_Dropdown, 'None')

        if Config_Tab_Variables['Config_Dropdown'] != Config_Dropdown:
            return Generate_Config_List(Config_Dropdown, 'None')

    except KeyError:
        return Generate_Config_List(Config_Dropdown, 'None')

    else:
        return Generate_Config_List(Config_Dropdown, Config_Dropdown_Line)


# ======================================== Device Config Tab - Callbacks ========================================
# Device_Config_Tab_Variables
@app.callback(
    Output('Device_Config_Tab_Variables', 'children'),
    [
        Input('Device_Config_Dropdown', 'value'),
        Input('Device_Config_Dropdown', 'value'),
        Input('Device_Config_Read', 'n_clicks'),
        Input('Device_Config_Save', 'n_clicks'),
        Input('Device_Config_Send', 'n_clicks'),
        Input('Device_Config_Reboot', 'n_clicks'),
        Input('Device_Config_Shutdown', 'n_clicks'),
        ],
    [
        State('Device_Config_Tab_Variables', 'children')
        ]
    )
def Device_Config_Tab_Variables(Device_Config_Dropdown, Device_Config_Read, Device_Config_Save, Device_Config_Send, Device_Config_Reboot, Device_Config_Shutdown, Device_Config_Tab_Variables):

    Device_Config_Tab_Variables = Generate_Variable_Dict(Device_Config_Tab_Variables)

    Device_Config_Tab_Variables['Device_Config_Dropdown'] = Device_Config_Dropdown

    Button_List = [Device_Config_Read, Device_Config_Save, Device_Config_Send, Device_Config_Reboot, Device_Config_Shutdown]
    Button_List_Text = ['Device_Config_Read', 'Device_Config_Save', 'Device_Config_Send', 'Device_Config_Reboot', 'Device_Config_Shutdown']

    # Check if buttons was presses
    for i in range(len(Button_List)):
        if Button_List[i] != int(Device_Config_Tab_Variables.get(Button_List_Text[i], 0)):
            Device_Config_Tab_Variables['Last_Click'] = Button_List_Text[i]

            # Shutdown / Reboot
            if Device_Config_Tab_Variables['Device_Config_Dropdown'] is not None or []:
                Action = None
                if Device_Config_Tab_Variables.get('Last_Click', None) == "Device_Config_Reboot":
                    if Device_Config_Tab_Variables.get('Device_Config_Reboot', 0) != Device_Config_Reboot:
                        Action = 'Reboot'
                elif Device_Config_Tab_Variables.get('Last_Click', None) == "Device_Config_Shutdown":
                    if Device_Config_Tab_Variables.get('Device_Config_Shutdown', 0) != Device_Config_Shutdown:
                        Action = 'Shutdown'
                if Action is not None:
                    # Set Last_Click to none to prevent repress when changing back to tab
                    Device_Config_Tab_Variables['Last_Click'] = None
                    MQTT.single(System_Header.Value[0] + "/Commands/" + str(Device_Config_Tab_Variables['Device_Config_Dropdown']) + "/Power", Action + ";", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})

            Device_Config_Tab_Variables[Button_List_Text[i]] = Button_List[i]
            break

    return Generate_Variable_String(Device_Config_Tab_Variables)


# Update Device Config rows
@app.callback(
    Output('Device_Config_Table', 'rows'),
    [
        Input('Device_Config_Tab_Variables', 'children'),
        Input('Device_Config_Save', 'n_clicks'),
        ],
    [
        State('Device_Config_Table', 'rows'),
        ]
    )
def Device_Config_Tab_Config_Show(Device_Config_Tab_Variables, Device_Config_Save, Device_Config_Table):

    # Open db connection
    db_Write_Connection = Open_db('Dobby')
    db_Write_Curser = db_Write_Connection.cursor()

    # Import variables from div able
    Device_Config_Tab_Variables = Generate_Variable_Dict(Device_Config_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Device_Config_Tab_Variables['Device_Config_Dropdown'] == "None":
        Close_db(db_Write_Connection, db_Write_Curser)
        return [{'Setting': '', 'Value': ''}]

    # ======================================== Save Config ========================================
    elif Device_Config_Tab_Variables.get('Last_Click', "None") == "Device_Config_Save":
        Current_Config = Generate_Device_Config_Dict(Device_Config_Tab_Variables['Device_Config_Dropdown'], db_Write_Curser)

        # Needed to refer between tables
        i = 0

        # Needed so you dont change the config id when no changes is made
        Config_Changes = {}

        for Current_Config_Row in Current_Config:

            # If value is '' set it to NULL
            if Device_Config_Table[i]['Value'] == '':
                Config_Changes[Device_Config_Table[i]['Setting'][0]] = 'NULL'

            elif Device_Config_Table[i]['Value'][0] != Current_Config_Row['Value'][0]:
                # Add chnages to chnages dict
                Config_Changes[Device_Config_Table[i]['Setting'][0]] = Device_Config_Table[i]['Value']

            i = i + 1

        if Config_Changes != {}:
            # Get device id for use in sql changes below
            db_Write_Curser.execute("SELECT id FROM Dobby.DeviceConfig WHERE Hostname='" + Device_Config_Tab_Variables['Device_Config_Dropdown'] + "';")
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
            db_Write_Curser.execute("UPDATE `Dobby`.`DeviceConfig` SET `Last_Modified`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + Device_id + "';")

            Device_Config_Tab_Variables['Last_Click'] = None

    # ======================================== Send Config ========================================
    elif Device_Config_Tab_Variables.get('Last_Click', "None") == "Device_Config_Send":
        Device_Config_Tab_Variables['Last_Click'] = None
        MQTT.single(System_Header.Value[0] + "/Commands/Dobby/Config", Device_Config_Tab_Variables['Device_Config_Dropdown'] + ",-1;", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})

    # ======================================== Return table ========================================
    Return_Dict = Generate_Device_Config_Dict(Device_Config_Tab_Variables['Device_Config_Dropdown'], db_Write_Curser)

    Close_db(db_Write_Connection, db_Write_Curser)

    return Return_Dict


# ======================================== Log Graph Tab - Callbacks ========================================
# Log_Graph_Tab_Variables
@app.callback(
    Output('Log_Graph_Tab_Variables', 'children'),
    [
        Input('Log_Graph_Dropdown', 'value'),
        Input('Log_Graph_Dropdown_Entry', 'value'),
        Input('Log_Graph_Dropdown_Rj', 'value'),
        Input('Log_Graph_Slider', 'value'),
        ],
    [
        State('Log_Graph_Tab_Variables', 'children')
        ]
    )
def Log_Graph_Tab_Variables(Log_Graph_Dropdown, Log_Graph_Dropdown_Entry, Log_Graph_Dropdown_Rj, Log_Graph_Slider, Log_Graph_Tab_Variables):

    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    # Dropdowns
    Log_Graph_Tab_Variables['Log_Graph_Dropdown'] = Log_Graph_Dropdown
    if Log_Graph_Dropdown is None:
        Log_Graph_Tab_Variables['Log_Graph_Dropdown'] = "None"
        Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] = "None"
        Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] = "None"
    else:
        if Log_Graph_Dropdown_Entry is None:
            Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] = "None"
        else:
            Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] = Log_Graph_Dropdown_Entry
            Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] = Log_Graph_Dropdown_Rj

    # Slider
    if Log_Graph_Dropdown is not None and Log_Graph_Dropdown_Entry is not None and Log_Graph_Dropdown != [] and Log_Graph_Dropdown_Entry != []:

        Slider_Name_String = ""
        i = 0
        # Find first entry
        for Selection in Log_Graph_Dropdown_Entry:
            if i != 0:
                Slider_Name_String = Slider_Name_String + " OR "
            Slider_Name_String = Slider_Name_String + "`Name`='" + str(Selection) + "'"
            i = i + 1

        db_Connection = Open_db(Log_db.Value[0])
        db_Curser = db_Connection.cursor()

        try:
            db_Curser.execute("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`" + Log_Graph_Dropdown.replace(" ", "_") + "` WHERE " + Slider_Name_String + " ORDER BY id ASC LIMIT 1;")
            Min_Date = db_Curser.fetchone()

            db_Curser.execute("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`" + Log_Graph_Dropdown.replace(" ", "_") + "` WHERE " + Slider_Name_String + " ORDER BY id DESC LIMIT 1;")
            Max_Date = db_Curser.fetchone()

        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print(e)
            return False

        # Close db connection
        Close_db(db_Connection, db_Curser)

        if Min_Date is not None or Max_Date is not None:
            # Save min/max
            Min_Date = Min_Date[0]
            Max_Date = Max_Date[0]

            Time_Span = Max_Date - Min_Date
            Time_Jumps = Time_Span / 100

            # Save Low value
            if Log_Graph_Slider[0] == 0:
                Log_Graph_Tab_Variables['Slider_Value_Low'] = Min_Date
            elif Log_Graph_Slider[0] == 100:
                Log_Graph_Tab_Variables['Slider_Value_Low'] = Max_Date
            else:
                Log_Graph_Tab_Variables['Slider_Value_Low'] = Min_Date + Time_Jumps * Log_Graph_Slider[0]

            # removes ".######" from the datetime string
            if len(str(Log_Graph_Tab_Variables['Slider_Value_Low'])) > 19:
                Log_Graph_Tab_Variables['Slider_Value_Low'] = str(Log_Graph_Tab_Variables['Slider_Value_Low'])[:-7]

            # Save high value
            if Log_Graph_Slider[1] == 0:
                Log_Graph_Tab_Variables['Slider_Value_High'] = Min_Date
            elif Log_Graph_Slider[1] == 100:
                Log_Graph_Tab_Variables['Slider_Value_High'] = Max_Date
            else:
                Log_Graph_Tab_Variables['Slider_Value_High'] = Min_Date + Time_Jumps * Log_Graph_Slider[1]

            # removes ".######" from the datetime string
            if len(str(Log_Graph_Tab_Variables['Slider_Value_High'])) > 19:
                Log_Graph_Tab_Variables['Slider_Value_High'] = str(Log_Graph_Tab_Variables['Slider_Value_High'])[:-7]

    return Generate_Variable_String(Log_Graph_Tab_Variables)


# ======================================== Log_Graph_Dropdown_Entry - Callback ========================================
@app.callback(
    Output('Log_Graph_Dropdown_Entry', 'options'),
    [
        Input('Log_Graph_Dropdown', 'value'),
        Input('Log_Graph_Tab_Variables', 'children'),
        ],
    )
def Log_Graph_Dropdown_Entry(Log_Graph_Dropdown, Log_Graph_Tab_Variables):

    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    if Log_Graph_Dropdown is None or Log_Graph_Dropdown == 'None':
        return []

    Name_Field_String = Column_Name_Check(Log_Graph_Dropdown)

    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    db_Curser.execute("SELECT id, `" + Name_Field_String + "` FROM `Dobby`.`" + Log_Graph_Dropdown.replace(" ", "_") + "` ORDER BY `" + Name_Field_String + "`;")
    db_Fetch = db_Curser.fetchall()

    # Close db connection
    Close_db(db_Connection, db_Curser)

    Return_List = []

    for Key, Value in db_Fetch:
        Return_List.append({'label': Value, 'value': Value})

    return Return_List


# ======================================== Log_Graph_Dropdown_Rj - Callback ========================================
@app.callback(
    Output('Log_Graph_Dropdown_Rj', 'options'),
    [
        Input('Log_Graph_Dropdown', 'value'),
        Input('Log_Graph_Tab_Variables', 'children'),
        ],
    )
def Log_Graph_Tab_Row_json_Dropdown(Log_Graph_Dropdown, Log_Graph_Tab_Variables):

    # Make variable dic from children
    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    if Log_Graph_Dropdown is None or Log_Graph_Dropdown == 'None' or Log_Graph_Dropdown == ['']:
        return {}

    elif Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] is None or Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] == 'None' or Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] == ['']:
        return {}

    # Create the return list
    Return_List = []

    if Log_Graph_Dropdown == "APC Monitor":

        # Open DB commection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'DobbyLog' AND TABLE_NAME = 'APC_Monitor';")
        db_Fetch = db_Curser.fetchall()

        # Close db connection
        Close_db(db_Connection, db_Curser)

        for Value in db_Fetch:
            if Value[0] not in ['id', 'DateTime', 'Name']:
                Return_List.append({'label': Value[0], 'value': Value[0]})

    elif Log_Graph_Dropdown == "Log Trigger":
        # Open DB commection
        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()

        # Get tags for each entry
        for Entry in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

            db_Curser.execute("SELECT distinct json_Tag FROM DobbyLog.Log_Trigger Where Name = '" + str(Entry) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(Log_Graph_Tab_Variables['Slider_Value_High']) + "' ORDER BY json_Tag;")
            db_Fetch = db_Curser.fetchall()

            for Value in db_Fetch:
                if Value[0] == "":
                    Return_List.append({'label': '-- No Tag --', 'value': '-- No Tag --'})
                else:
                    Return_List.append({'label': Value[0], 'value': Value[0]})

        # Close db connection
        Close_db(db_Connection, db_Curser)

    # elif Log_Graph_Dropdown is "Log Graph":
    else:
        print "HIT code the rest you fool"
        return {}

    # Name_Field_String = Column_Name_Check(Log_Graph_Dropdown)
    #
    # db_Connection = Open_db("Dobby")
    # db_Curser = db_Connection.cursor()
    #
    # db_Curser.execute("SELECT id, `" + Name_Field_String + "` FROM `Dobby`.`" + Log_Graph_Dropdown.replace(" ", "_") + "` ORDER BY `" + Name_Field_String + "`;")
    # db_Fetch = db_Curser.fetchall()
    #
    # # Close db connection
    # Close_db(db_Connection, db_Curser)
    #
    #
    # for Key, Value in db_Fetch:
    #     Return_List.append({'label': Value, 'value': Value})

    return Return_List


# ======================================== Log_Graph - Slider Marks ========================================
@app.callback(
    Output('Log_Graph_Slider', 'marks'),
    [
        Input('Log_Graph_Tab_Variables', 'children')
        ],
    [
        # State('Log_Graph_Tab_Variables', 'children'),
        ]
    )
def Log_Graph_Update_Slider_Marks(Log_Graph_Tab_Variables):

    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    if Log_Graph_Tab_Variables.get('Log_Graph_Dropdown', 'None') == 'None' or Log_Graph_Tab_Variables.get('Log_Graph_Dropdown_Entry', 'None') == 'None':
        return {}

    Time_Span = Log_Graph_Tab_Variables['Slider_Value_High'] - Log_Graph_Tab_Variables['Slider_Value_Low']
    Time_Jumps = Time_Span / 10

    Marks_Dict = {}

    # Add the first and last label
    Marks_Dict['0'] = {'label': Log_Graph_Tab_Variables['Slider_Value_Low']}
    Marks_Dict['100'] = {'label': Log_Graph_Tab_Variables['Slider_Value_High']}

    # Add the rest of the labels
    for i in range(1, 10):
        Name = str(i * 10)
        Label = str(Log_Graph_Tab_Variables['Slider_Value_Low'] + Time_Jumps * i)

        # The [:-7] removes the ms from the end of the string
        if "." in Label:
            Label = Label[:-7]

        Marks_Dict[Name] = {'label': Label}

    return Marks_Dict


# Update Graph
@app.callback(
    Output('Log_Graph_Graph', 'figure'),
    [
        Input('Log_Graph_Tab_Variables', 'children'),
        # Input('Log_Graph_Tab_Row_json_Dropdown', 'options'),
        ],
    [
        # State('Log_Graph_Tab_Variables', 'children'),
        # State('Log_Graph_Tab_Variables', 'children'),
        ]
    )
def Log_Graph_Graph(Log_Graph_Tab_Variables):

    # Import variables from div able
    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == 'None' or Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] == 'None' or Log_Graph_Tab_Variables is {}:
        return {'data': ''}

    # ======================================== Read Logs ========================================
    else:
        db_Connection = Open_db(Log_db.Value[0])
        db_Curser = db_Connection.cursor()

        Data = []

        # APC Monitor
        if Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "APC Monitor" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != "None":

            for Name in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

                for Row in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']:
                    Data.append(
                        go.Scatter(
                            x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`" + Log_Graph_Tab_Variables['Log_Graph_Dropdown'].replace(" ", "_") + "` WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                            y=SQL_To_List("SELECT `" + Row + "` FROM `" + Log_db.Value[0] + "`.`" + Log_Graph_Tab_Variables['Log_Graph_Dropdown'].replace(" ", "_") + "` WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                            name=str(Name + " - " + Row),
                            mode='lines+markers',
                        )
                    )

        # KeepAliveMonitor
        elif Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "KeepAliveMonitor":
            print "HIT KeepAliveMonitor"
            return {'data': ''}

        # Log Trigger
        elif Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "Log Trigger" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != "None" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != ['']:

            # RM
            # print "HIT Log_Graph_Dropdown"
            # return {'data': ''}

            # print "Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']"
            # print Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']
            # print "Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']"
            # print Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']

            for Name in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

                # Create and style traces
                for Tag_Name in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']:

                    Plot_Name = ''
                    if Tag_Name == '-- No Tag --':
                        Tag_Search_String = ''
                        Plot_Name = Name
                    else:
                        Tag_Search_String = "AND json_Tag='" + str(Tag_Name) + "'"
                        Plot_Name = str(Name + " - " + Tag_Name)

                    Date_Search_String = " AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(Log_Graph_Tab_Variables['Slider_Value_High']) + "'"

                    # print "PIK:" + Tag_Search_String
                    # print "SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"

                    db_Curser.execute("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;")
                    temp = db_Curser.fetchall()

                    # print "s"
                    # print temp

                    Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
                                # x=[1, 2],
                                # y=[1, 2],
                                name=Plot_Name,
                                mode='lines+markers',
                                line=dict(
                                    dash='dash',
                                )
                            )
                        )
                    # print "Data"
                    # print Data

                    # pass
                    # print "SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"

                    # fix json tags here something is up here is a -- No Tag -- is selected it will select all from the once that has tacs

                    # if "Min" in Tag_Name:
                    #     Data.append(
                    #         go.Scatter(
                    #             x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             y=SQL_To_List("SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             name=str(Name + " - " + Tag_Name),
                    #             mode='lines+markers',
                    #             line=dict(
                    #                 dash='dash',
                    #             )
                    #         )
                    #     )
                    #
                    # elif "Max" in Tag_Name:
                    #     Data.append(
                    #         go.Scatter(
                    #             x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             y=SQL_To_List("SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             name=str(Name + " - " + Tag_Name),
                    #             mode='lines+markers',
                    #             line=dict(
                    #                 dash='dot',
                    #             )
                    #         )
                    #     )
                    #
                    # elif "Current" in Tag_Name:
                    #     Data.append(
                    #         go.Scatter(
                    #             x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             y=SQL_To_List("SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             name=str(Name + " - " + Tag_Name),
                    #             mode='lines+markers',
                    #         )
                    #     )
                    #
                    # else:
                    #     Data.append(
                    #         go.Scatter(
                    #             x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             y=SQL_To_List("SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                    #             name=str(Name + " - " + Tag_Name),
                    #             mode='lines+markers',
                    #         )
                    #     )
                # else:
                #     # Create and style traces
                #     Data.append(
                #         go.Scatter(
                #             x=SQL_To_List("SELECT DateTime FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                #             y=SQL_To_List("SELECT Value FROM `" + Log_db.Value[0] + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                #             name=str(Name),
                #             mode='lines+markers',
                #         )
                    # )
        Close_db(db_Connection, db_Curser)

        # Edit the layout
        layout = dict(
            # title = 'Average High and Low Temperatures in New York',
            # xaxis=dict(title='Timestamp'),
            # yaxis = dict(title = 'Temperature (degrees F)'),
        )

        fig = dict(data=Data, layout=layout)

        return fig


# ======================================== System Log Tab - Callbacks ========================================
@app.callback(
    Output('System_Log_Tab_Variables', 'children'),
    [
        Input('System_Log_Dropdown', 'value'),
        Input('System_Log_Read_Button', 'n_clicks'),
        Input('System_Log_Number_Of_Input', 'value'),
        ],
    [
        State('System_Log_Tab_Variables', 'children'),
        ],
    )
def System_Log_Tab_Dropdown(System_Log_Dropdown, System_Log_Read_Button, System_Log_Number_Of_Input, System_Log_Tab_Variables):

    # Import variables from div able
    System_Log_Tab_Variables = Generate_Variable_Dict(System_Log_Tab_Variables)

    # Dropdown
    System_Log_Tab_Variables['System_Log_Dropdown'] = System_Log_Dropdown

    if System_Log_Dropdown is None:
        System_Log_Tab_Variables['System_Log_Dropdown'] = "None"

    # Set columns in var for later use
    System_Log_Tab_Variables['System_Log_Read_Button'] = System_Log_Read_Button
    
    System_Log_Tab_Variables['System_Log_Number_Of_Input'] = System_Log_Number_Of_Input

    return Generate_Variable_String(System_Log_Tab_Variables)


# Change column names
@app.callback(
    Output('System_Log_Tab_Table', 'columns'),
    [
        Input('System_Log_Tab_Variables', 'children')
        ],
    [
        State('System_Log_Tab_Table', 'columns'),
        ]
    )
def System_Log_Tab_Table_Comumns(System_Log_Tab_Variables, System_Log_Tab_Table):

    System_Log_Tab_Variables = Generate_Variable_Dict(System_Log_Tab_Variables)

    return Generate_System_Log_Table_Columns(System_Log_Tab_Variables.get('System_Log_Dropdown', ["None"]))


# Read content
@app.callback(
    Output('System_Log_Tab_Table', 'data'),
    [
        Input('System_Log_Tab_Variables', 'children')
    ],
    )
def System_Log_Tab_Table_Rows(System_Log_Tab_Variables):

    System_Log_Tab_Variables = Generate_Variable_Dict(System_Log_Tab_Variables)    

    if System_Log_Tab_Variables.get('System_Log_Dropdown', None) is None or System_Log_Tab_Variables.get('System_Log_Dropdown', "None") == "None":
        return []

    Row_List = Generate_System_Log_Table_Columns(System_Log_Tab_Variables.get('System_Log_Dropdown', []))
    Row_List_String = ''

    # Generate text string for db lookup
    for i in range(len(Row_List)):
        Row_List_String = Row_List_String + Row_List[i]['id'] + ", "

    # # Remove ", " from the end of the string
    if Row_List_String[-2:] == ", ":
        Row_List_String = Row_List_String[0:-2]

    db_Log = SQL_Read('SELECT ' + Row_List_String + ' FROM DobbyLog.' + System_Log_Tab_Variables.get('System_Log_Dropdown', []).replace(" ", "") + ' order by id desc limit ' + str(System_Log_Tab_Variables.get('System_Log_Number_Of_Input', '10')) + ';')

    Return_List = []

    # Split returned data into a row
    for db_Line in db_Log:
        i = 0
        # Create a Dict to hold row info for table
        Return_Dict = {}
        # Slipt each row into individual entries
        for db_Entry in db_Line:
            Return_Dict[Row_List[i]['id']] = db_Entry
            i = i + 1
        
        Return_List.append(Return_Dict)
    
    return Return_List


# ======================================== System Tab - Callbacks ========================================
@app.callback(
    Output('System_Tab_Variables', 'children'),
    [
        Input('System_Quit_Button', 'n_clicks'),
        Input('System_Update_Button', 'n_clicks'),
        ],
    [
        State('System_Tab_Variables', 'children'),
        ],
    )
def System_Tab_Buttons(System_Quit_Button, System_Update_Button, System_Tab_Variables):

    # Import variables from div able
    System_Tab_Variables = Generate_Variable_Dict(System_Tab_Variables)

    if int(System_Tab_Variables.get('System_Update_Button', 0)) != int(System_Update_Button):
        System_Tab_Variables['System_Update_Button'] = System_Update_Button

        print "working here"

    elif int(System_Tab_Variables.get('System_Quit_Button', 0)) != int(System_Quit_Button):
        System_Tab_Variables['System_Quit_Button'] = System_Quit_Button

        print "System shutdown requested, shutting down"
        Server_Shutdown()

    return Generate_Variable_String(System_Tab_Variables)


# FIX - Move css to local storage
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
# Removed undo/redo
app.css.append_css({'external_url': 'http://rawgit.com/lwileczek/Dash/master/undo_redo5.css'})

print "Dash Core Components: " + str(dcc.__version__)
print "Dash HTML Components: " + str(html.__version__)
print "Dash Table Experiments: " + str(dte.__version__)
print "Dash Table: " + str(dt.__version__)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', ssl_context=('/etc/Dobby/Cert/cert.pem', '/etc/Dobby/Cert/key.pem'))
