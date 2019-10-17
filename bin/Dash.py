#!/usr/bin/python

# # Changelog
# See Changelog/Dash.txt

from pathlib import Path

import dash
import dash_auth

from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

# Neede to be able to shutdown dash
from flask import request

# MQTT
import paho.mqtt.publish as MQTT

# Time
import datetime

# MySQL
import MySQLdb

# Scacda
import plotly.graph_objs as go

# MISC
import os


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
    MQTT.single(Topic, Payload, hostname=MQTT_Broker, port=MQTT_Port, auth={'username': MQTT_Username, 'password': MQTT_Password})


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
    if Column_Name == 'EP Logger':
        Name_Field_String = 'Name'
    elif Column_Name == 'Users':
        Name_Field_String = 'Username'
    elif Column_Name == 'Users':
        Name_Field_String = 'Username'
    elif Column_Name == 'MQTT Functions':
        Name_Field_String = 'Function'

    return Name_Field_String


# ======================================== Generate_Config_List_System ========================================
def Generate_Config_List_System(Config_Dropdown, Config_Dropdown_Line, db_Curser=None):

    
    if Config_Dropdown is None or Config_Dropdown == 'None' or Config_Dropdown_Line is None or Config_Dropdown_Line == 'None':
        return [{'id': 'Header', 'name': 'Header'}, {'id': 'Name', 'name': 'Name'}, {'id': 'Value', 'name': 'Value'}]

    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()
    
    try:
        db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='" + Config_Dropdown.replace(" ", "_") + "';")
        Settings = db_Curser.fetchall()

        if Config_Dropdown_Line != "-- New Entry --":
            db_Curser.execute("SELECT * FROM Dobby." + Config_Dropdown.replace(" ", "_") + " WHERE `Target`='" + Config_Dropdown_Line + "';")
            Values = db_Curser.fetchall()

        # New Entry
        else:
            db_Curser.execute("SELECT Column_Default, IS_NULLABLE FROM Information_Schema.Columns WHERE table_schema='Dobby' AND table_name='" + Config_Dropdown.replace(" ", "_") + "';")
            Values = db_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning):
        Close_db(db_Connection, db_Curser)
        return []

    if Settings is None:
        Close_db(db_Connection, db_Curser)
        return [{}]

    Close_db(db_Connection, db_Curser)

    Config_Ignore_List = ['id', 'FuTarget', 'Last_Modified']

    Row_List = []

    # Generate value list
    for Value in Values:
        Row_Dict = {}
        # Split list into values
        for i in range(len(Value)):
            if Settings[i][0] not in Config_Ignore_List:
                Row_Dict[Settings[i][0]] = Value[i]
        Row_List.append(Row_Dict)

    return Row_List


# ======================================== Generate_Config_List_Functions ========================================
def Generate_Config_List_Functions(Config_Dropdown, Config_Dropdown_Line, db_Curser=None):

    if Config_Dropdown is None or Config_Dropdown == 'None' or Config_Dropdown_Line is None or Config_Dropdown_Line == 'None':
        return [{'CommandNumber': '', 'Function': '', 'Type': '', 'Command': '', 'DelayAfter': ''}]

    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()
    
    try:
        db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='" + Config_Dropdown.replace(" ", "_") + "';")
        Settings = db_Curser.fetchall()

        if Config_Dropdown_Line != "-- New Entry --":
            db_Curser.execute("SELECT * FROM Dobby." + Config_Dropdown.replace(" ", "_") + " WHERE `Function`='" + Config_Dropdown_Line + "';")
            Values = db_Curser.fetchall()

        # # New Entry
        # else:
        #     db_Curser.execute("SELECT Column_Default, IS_NULLABLE FROM Information_Schema.Columns WHERE table_schema='Dobby' AND table_name='" + Config_Dropdown.replace(" ", "_") + "';")
        #     Values = db_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
            
        Close_db(db_Connection, db_Curser)
        return []

    if Settings is None:
        Close_db(db_Connection, db_Curser)
        return [{}]

    Close_db(db_Connection, db_Curser)

    Config_Ignore_List = ['id', 'Function', 'Last_Modified']

    Row_List = []

    # Generate value list
    for Value in Values:
        Row_Dict = {}
        # Split list into values
        for i in range(len(Value)):
            if Settings[i][0] not in Config_Ignore_List:
                Row_Dict[Settings[i][0]] = Value[i]
        Row_List.append(Row_Dict)

    return Row_List
  

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

    except (MySQLdb.Error, MySQLdb.Warning) as e:
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

    Tabs_List.append(dcc.Tab(label='Buttons', value='Buttons_Tab'))

    Tabs_List.append(dcc.Tab(label='Counters', value='Counters_Tab'))

    Tabs_List.append(dcc.Tab(label='Config', value='Config_Tab'))

    Tabs_List.append(dcc.Tab(label='Devices', value='Devices_Tab'))

    Tabs_List.append(dcc.Tab(label='EP', value='EP_Tab'))

    Tabs_List.append(dcc.Tab(label='Live', value='Live_Tab'))

    Tabs_List.append(dcc.Tab(label='Log Graph', value='Log_Graph_Tab'))

    Tabs_List.append(dcc.Tab(label='System Log', value='System_Log_Tab'))

    Tabs_List.append(dcc.Tab(label='System', value='System_Tab'))

    return Tabs_List


def Config_Tab_Dropdown_List():

    return ['Alert Targets', 'Alert Trigger', 'Action Trigger', 'APC Monitor', 'DashButtons', 'DeviceConfig', 'Dobby Assistant', 'EP Logger', 'gBridge Trigger', 'Log Trigger', 'MQTT Functions', 'Push Trigger', 'Spammer', 'SystemConfig', 'Users']


def Log_Graph_Tab_Dropdown_List():

    Return_List = []
    db_Resoult = None

    db_Connection = Open_db(Log_db)
    db_Curser = db_Connection.cursor()

    Test_List = ['APC Monitor', 'EP Logger', 'Log Trigger', 'KeepAliveMonitor']

    for Table in Test_List:
        try:
            # Check if APC Monitor table exists and has content
            db_Curser.execute("SELECT id FROM " + Table.replace(" ", "_") + " order by id desc limit 1;")
            db_Resoult = db_Curser.fetchone()

            if db_Resoult is not None:
                Return_List.append(Table)

        # If and db error assume that the table is not there
        except:
            pass

    return Return_List


# MISC
# import collections
# import ast

# json
# import json

# MISC
Version = 102015
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number

# Dobby
# FIX - Find a better way to get the info below
# MQTT_Broker = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Broker';", con=db_pd_Connection)
# MQTT_Port = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Port';", con=db_pd_Connection)
# MQTT_Username = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Username';", con=db_pd_Connection)
# MQTT_Password = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='MQTT' AND Target='Dobby' AND Name='Password';", con=db_pd_Connection)
# System_Header = pd.read_sql("SELECT Value FROM Dobby.SystemConfig WHERE Header='System' AND Target='Dobby' AND Name='Header';", con=db_pd_Connection)
# Log_db = pd.read_sql("Select Value From Dobby.SystemConfig where Target='Dobby' AND Header='Log' AND `Name`='db';", con=db_pd_Connection)
MQTT_Broker = "localhost"
MQTT_Port = "1883"
MQTT_Username = "DasBoot"
MQTT_Password = "NoSinking"
System_Header = "/Boat"
Log_db = "DobbyLog"

# MySQL
MySQL_Server = 'localhost'
MySQL_Username = 'dobby'
MySQL_Password = 'HereToServe'

db_Connection = Open_db("Dobby")
db_Curser = db_Connection.cursor()

# Get number of buttons
db_Curser.execute("SELECT COUNT(id) FROM Dobby.DashButtons;")
db_DashButtons = db_Curser.fetchone()

# Add users and passwords
# User auth list
db_Curser.execute("SELECT Username, Password FROM Dobby.Users;")
db_User_Info = db_Curser.fetchall()

# Close db connection
Close_db(db_Connection, db_Curser)

# FIX - Move to global var its ok :-)
DashButtons_Number_Of = db_DashButtons[0]

# FIX - Find a betting solution, maybe make a dummy button
# If DashButtons_Number_Of == 0 the script will crash
if DashButtons_Number_Of == 0:
    DashButtons_Number_Of = 1

# Create user list
User_List = []

for i in range(len(db_User_Info)):
    User_List.append([db_User_Info[i][0], db_User_Info[i][1]])

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


    dcc.Tabs(id="tabs", value='Log_Graph_Tab', children=Tabs_List()),

    html.Div(id='Main_Tabs'),

    # Places to store variables
    html.Div([
        html.Div(id='Alerts_Tab_Variables', children=""),
        html.Div(id='Buttons_Tab_Variables', children=""),
        html.Div(id='Counters_Tab_Variables', children=""),
        html.Div(id='Config_Tab_Variables', children=""),
        html.Div(id='Devices_Tab_Variables', children=""),
        html.Div(id='EP_Tab_Variables', children=""),
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
        State('Counters_Tab_Variables', 'children'),
        State('Config_Tab_Variables', 'children'),
        State('Devices_Tab_Variables', 'children'),
        State('EP_Tab_Variables', 'children'),
        State('Live_Tab_Variables', 'children'),
        State('Log_Graph_Tab_Variables', 'children'),
        State('System_Log_Tab_Variables', 'children'),
        State('System_Tab_Variables', 'children'),
        ]
    )
def render_content(tab, Alerts_Tab_Variables, Buttons_Tab_Variables, Counters_Tab_Variables, Config_Tab_Variables, Devices_Tab_Variables, EP_Tab_Variables, Live_Tab_Variables, Log_Graph_Tab_Variables, System_Log_Tab_Variables, System_Tab_Variables):
    # ======================================== Alerts Tab ========================================
    # ======================================== Alerts Tab ========================================
    # ======================================== Alerts Tab ========================================
    if tab == 'Alerts_Tab':
        Alerts_Tab_Variables = Generate_Variable_Dict(Alerts_Tab_Variables)

        return html.Div([
            # Config table
        #     dt.DataTable(
        #         id='Alerts_Table',
        #         rows=[],
        #         columns=['Source', 'Text', 'Status', 'Timestamp'],
        #         min_height='72vh',
        #         resizable=True,
        #         editable=True,
        #         filterable=True,
        #         sortable=True,
        #         ),
            dt.DataTable(
                id='Alerts_Table',
                columns=['Source', 'Text', 'Status', 'Timestamp'],
                # columns=[Generate_System_Log_Table_Columns(System_Log_Tab_Variables.get('System_Log_Dropdown', "None"))],
                # min_height='72vh',
                # resizable=True,
                editable=True,
                sorting=True,
                data=[{}],
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

    # ======================================== Counters Tab ========================================
    # ======================================== Counters Tab ========================================
    # ======================================== Counters Tab ========================================
    elif tab == 'Counters_Tab':

        Counters_Tab_Variables = Generate_Variable_Dict(Counters_Tab_Variables)

        return html.Div([
            
            dt.DataTable(
                    id='Counters_Table',
                    columns=[{'id': 'Counter', 'name': 'Counter'}, {'id': 'Ticks', 'name': 'Ticks'}, {'id': 'Value', 'name':'Value'}],
                    # columns=[Generate_System_Log_Table_Columns(System_Log_Tab_Variables.get('System_Log_Dropdown', "None"))],
                    # min_height='72vh',
                    # resizable=True,
                    editable=False,
                    sorting=True,
                    data=[{}],
                ),
            html.Button('Read', id='Counters_Read', n_clicks=int(Counters_Tab_Variables.get('Counters_Read', 0)), style={'margin-top': '5px'}),
            
        ], id='Counters_Tab')

    # ======================================== Devices Tab ========================================
    # ======================================== Devices Tab ========================================
    # ======================================== Devices Tab ========================================
    elif tab == 'Devices_Tab':

        Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

        return html.Div([

            # Dropdown to selecte device
            dcc.Dropdown(
                id='Devices_Dropdown',
                options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT DISTINCT Name FROM `Dobby`.Log_Trigger;")],
                multi=True,
                value=Devices_Tab_Variables.get('Live_Dropdown', None),
            ),

            # Status Table
            dt.DataTable(
                id='Devices_Table_Config',
                columns=[{'id': 'Name', 'name': 'Name'}, {'id': 'Value', 'name':'Value'}],
                editable=True,
                sorting=True,
                data=[{}],
            ),

            html.Button('Refresh', id='Devices_Refresh', n_clicks=int(Devices_Tab_Variables.get('Devices_Refresh', 0)), style={'margin-top': '5px', 'margin-bottom': '5px'}),


            # Config Table
            dt.DataTable(
                id='Devices_Table_Status',
                columns=[{'id': 'Setting', 'name': 'Setting'}, {'id': 'Value', 'name':'Value'}],
                editable=True,
                sorting=True,
                data=[{}],
            ),

            html.Button('Read', id='Devices_Read', n_clicks=int(Devices_Tab_Variables.get('Devices_Read', 0)), style={'margin-top': '5px', 'margin-bottom': '5px'}),
            html.Button('Save', id='Devices_Save', n_clicks=int(Devices_Tab_Variables.get('Devices_Save', 0)), style={'margin-left': '10px', 'margin-top': '5px', 'margin-bottom': '5px'}),
            html.Button('Push Config', id='Devices_Push', n_clicks=int(Devices_Tab_Variables.get('Devices_Push', 0)), style={'margin-left': '10px', 'margin-top': '5px', 'margin-bottom': '5px'}),
            
        ], id='Devices_Tab_Variables')


    # ======================================== EP Tab ========================================
    # ======================================== EP Tab ========================================
    # ======================================== EP Tab ========================================
    elif tab == 'EP_Tab':

        EP_Tab_Variables = Generate_Variable_Dict(EP_Tab_Variables)

        return html.Div(
            id='EP_Tab',
            children=[

                # Dropdown to select logs
                dcc.Dropdown(
                    id='EP_Dropdown_Device',
                    options=[{'label': Debice, 'value': Debice} for Debice in SQL_To_List("SELECT DISTINCT Name FROM `Dobby`.`EP_Logger;")],
                    value=EP_Tab_Variables.get('EP_Dropdown_Device', None),
                    multi=True,
                    ),

                # Dropdown to select logs
                dcc.Dropdown(
                    id='EP_Dropdown_Entry',
                    options=[],
                    value=EP_Tab_Variables.get('EP_Dropdown_Entry', None),
                    multi=True,
                    ),

                # The graph
                dcc.Graph(
                    id='EP_Graph',
                    style={
                        'height': '70vh',
                        'width': '95vw',
                        'padding': 5,
                        }
                    ),

                html.Div(
                    id='EP_Tab_Slider',
                    style={
                        'width': '90vw',
                        'padding': 50,
                        'display': 'inline-block'
                        },
                    children=[
                        dcc.RangeSlider(
                            id='EP_Slider',
                            min=0,
                            max=100,
                            step=1,
                            value=[EP_Tab_Variables.get('Slider_Value_Low', 95), EP_Tab_Variables.get('Slider_Value_High', 100)],
                            allowCross=False,
                            marks={},
                        ),
                    ],
                ),
            ],
        )
            



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
                    options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT DISTINCT Name FROM `Dobby`.Log_Trigger;")],
                    multi=True,
                    value=Live_Tab_Variables.get('Live_Dropdown', None),
                ),

                # Dropdown to select json tags
                dcc.Dropdown(
                    id='Live_Dropdown_json',
                    options=[],
                    value=Live_Tab_Variables.get('Live_Dropdown_json', None),
                    multi=True,
                    ),

                # The graph
                dcc.Graph(
                    id='Live_Graph',
                    style={
                        'height': '70vh',
                        'width': '95vw',
                        'padding': 5,
                        }
                    ),

                # Auto update
                dcc.Interval(
                    id='Live_Interval_Component',
                    interval=2500, # in milliseconds
                    n_intervals=0
                ),

                html.Div(
                    id='Live_Tab',
                    style={
                        'width': '90vw',
                        'padding': 50,
                        'display': 'inline-block'
                        },
                    children=[
                        dcc.Slider(
                            id='Live_Slider',
                            min=1,
                            max=24,
                            step=1,
                            value=6,
                            marks={
                                1: '5m',
                                3: '15m',
                                6: '30m',
                                9: '45m',
                                12: '1h',
                                15: '1h15m',
                                18: '1h30m',
                                21: '1h45m',
                                24: '2h'
                            },
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
                    multi=False,
                    ),
                html.Button('Read', id='Config_Read', n_clicks=int(Config_Tab_Variables.get('Config_Read', 0)), style={'margin-top': '5px'}),
                html.Button('Delete Row', id='Config_Delete_Row', n_clicks=int(Config_Tab_Variables.get('Config_Delete_Row', 0)), style={'margin-left': '10px', 'margin-top': '5px'}),
                html.Button('Save', id='Config_Save', n_clicks=int(Config_Tab_Variables.get('Config_Save', 0)), style={'margin-left': '10px', 'margin-top': '5px'}),
                html.Button('Push Config', id='Config_Push', n_clicks=int(Config_Tab_Variables.get('Config_Push', 0)), style={'margin-left': '10px', 'margin-top': '5px'}),
                dt.DataTable(
                    id='Config_Table',
                    # columns=[{'id': 'Setting', 'name': 'Setting'}, {'id': 'Value', 'name':'Value'}],
                    columns=[{}],
                    editable=True,
                    sorting=True,
                    data=[{}],
                ),
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
                    options=[{'value': None, 'lable': None}],
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
                            value=[Log_Graph_Tab_Variables.get('Slider_Value_Low', 95), Log_Graph_Tab_Variables.get('Slider_Value_High', 100)],
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
                    # filtering=True,
                    sorting=True,
                    data=[{}],
                ),
                # Button to read logs
                html.Div(
                    style={'display': 'inline-block'},
                    children=[
                        html.Div(
                            children=[
                                html.Button(
                                    'Read log',
                                    id='System_Log_Read_Button',
                                    n_clicks=0,
                                    style={'margin-top': '5px', "margin-right": "5px"}
                                ),
                            ],
                            style={'display': 'inline-block'}
                        ),
                        # Input to enter number of lines to read
                        html.Div(
                            children=[
                                dcc.Input(
                                    id='System_Log_Number_Of_Input',
                                    placeholder='Number of lines to read',
                                    type='number',
                                    value='25',
                                    style={'margin-top': '5px', "margin-right": "5px"}
                                ),
                            ],
                            style={'display': 'inline-block'}
                        ),
                        html.Div(
                            children=[
                                dcc.Checklist(
                                    id='System_Log_Auto_Refresh',
                                    options=[{'label': 'Auto Refresh', 'value': 'AutoRefresh'}],
                                    values=[System_Log_Tab_Variables.get('System_Log_Auto_Refresh', "AutoRefresh")],
                                ),
                            ],
                            style={'display': 'inline-block'},
                        ),
                    ],
                ),
                # Auto update
                dcc.Interval(
                    id='System_Log_Interval_Component',
                    interval=1500, # in milliseconds
                    n_intervals=0
                ),
            ],
        )

    # ======================================== System Tab ========================================
    # ======================================== System Tab ========================================
    # ======================================== System Tab ========================================
    elif tab == 'System_Tab':
        System_Tab_Variables = Generate_Variable_Dict(System_Tab_Variables)

        return html.Div([
            html.Button('Test BT Speaker', id='System_Test_BT_Button', n_clicks=0, style={'margin-left': '5px', 'margin-top': '5px'}),
            html.Button('Restart Services', id='System_Restart_Services', n_clicks=0, style={'margin-left': '5px', 'margin-top': '5px'}),
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

# ======================================== Counters Tab - Callbacks ========================================
# Read content
@app.callback(
    Output('Counters_Table', 'data'),
    [
        Input('Counters_Tab_Variables', 'children')
    ],
    )
def Counters_Tab_Table_Rows(Counters_Tab_Variables):

    Counters_Tab_Variables = Generate_Variable_Dict(Counters_Tab_Variables)

    # get counter data
    Counter_Data = SQL_Read('SELECT Name, Ticks, `Calculated Value` FROM Dobby.Counters;')

    Return_List = []

    for Counter_Info in Counter_Data:
        Return_Dict = {}
        Return_Dict["Counter"] = Counter_Info[0]
        Return_Dict["Ticks"] = Counter_Info[1]
        Return_Dict["Value"] = Counter_Info[2]
        Return_List.append(Return_Dict)

    return Return_List


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
        Input('Config_Push', 'n_clicks'),
        ],
    [
        State('Config_Table', 'data'),
        State('Config_Tab_Variables', 'children'),
        ]
    )
def Config_Tab_Variables(Config_Dropdown, Config_Dropdown_Line, Config_Read, Config_Delete_Row, Config_Save, Config_Push, Config_Table, Config_Tab_Variables):

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
    # Push Config
    if int(Config_Tab_Variables.get('Config_Push', 0)) != int(Config_Push):
        if Config_Dropdown == 'DeviceConfig' and Config_Dropdown_Line != None:
            # FIX - Add Devices Tab

            # Open db connection to get Hostname
            db_Connection = Open_db(Log_db)
            db_Curser = db_Connection.cursor()

            # Get the latest IP from KeepAliveMonitor
            db_Curser.execute("SELECT IP FROM " + Log_db + ".KeepAliveMonitor WHERE Device='" + Config_Dropdown_Line + "' ORDER BY ID DESC LIMIT 1;")
            Device_IP = db_Curser.fetchone()

            # Close db connection
            Close_db(db_Connection, db_Curser)

            # Check if we got an IP
            if Device_IP is not None:
                MQTT_Publish(System_Header + "/Commands/Dobby/Config", Config_Dropdown_Line + ",-1,FTP," + str(Device_IP[0]))

    # Delete Row
    if int(Config_Tab_Variables.get('Config_Delete_Row', 0)) != int(Config_Delete_Row):
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT id FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY id DESC LIMIT 1;")
        Row_id = db_Curser.fetchone()
        Row_id = str(Row_id[0])

        # print "Uncomment below to enable Delete Row"
        
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

                # Field clear set cell to null
                if Config_Table[i]['Value'] == '':
                    # FIX - Find a wau to set db cell to null
                    Config_Changes[Config_Table[i]['Setting'][0]] = ''

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
                        elif value['Value'] == '':
                            Value_String = Value_String + "'', "
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

                    Config_List = ["DeviceConfig"]

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
    
    db_Fetch = ""

    if Config_Dropdown == "MQTT Functions":
        db_Curser.execute("SELECT DISTINCT Function FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY `Function`;")
    elif Config_Dropdown == "SystemConfig":
        db_Curser.execute("SELECT DISTINCT Target FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY `Target`;")
    else:
        db_Curser.execute("SELECT `" + Name_Field_String + "` FROM `Dobby`.`" + Config_Dropdown.replace(" ", "_") + "` ORDER BY `" + Name_Field_String + "`;")

    db_Fetch = db_Curser.fetchall()

    # Close db connection
    Close_db(db_Connection, db_Curser)

    Return_List = []

    Return_List.append({'label': '-- New Entry --', 'value': '-- New Entry --'})

    for Value in db_Fetch:
        Return_List.append({'label': Value[0], 'value': Value[0]})

    return Return_List


@app.callback(
    Output('Config_Table', 'data'),
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
        if Config_Dropdown == "MQTT Functions":
            return Generate_Config_List_Functions(Config_Dropdown, Config_Dropdown_Line)
        elif Config_Dropdown == "SystemConfig":
            return Generate_Config_List_System(Config_Dropdown, Config_Dropdown_Line)
        else:
            return Generate_Config_List(Config_Dropdown, Config_Dropdown_Line)


# Change column names
@app.callback(
    Output('Config_Table', 'columns'),
    [
        Input('Config_Dropdown', 'value'),
        Input('Config_Tab_Variables', 'children'),
        ],
    )
def Config_Tab_Table_Columns(Config_Tab_Dropdown, Config_Tab_Variables):
    
    Config_Tab_Variables = Generate_Variable_Dict(Config_Tab_Variables)
    
    # None
    if Config_Tab_Variables.get('Config_Dropdown', 'None') == "None" or Config_Tab_Variables.get('Config_Dropdown', None) is None:
        return [{}]

    elif Config_Tab_Variables.get('Config_Dropdown', 'None') == "MQTT Functions":
        return [{'id': 'CommandNumber', 'name': 'CommandNumber'}, {'id': 'Type', 'name': 'Type'}, {'id': 'Command', 'name': 'Command'}, {'id': 'DelayAfter', 'name': 'DelayAfter'}, ]

    elif Config_Tab_Variables.get('Config_Dropdown', 'None') == "SystemConfig":
        return [{'id': 'Header', 'name': 'Header'}, {'id': 'Name', 'name': 'Name'}, {'id': 'Value', 'name': 'Value'}]
        
    else:
        return [{'id': 'Setting', 'name': 'Setting'}, {'id': 'Value', 'name':'Value'}]



# ======================================== Device Config Tab - Callbacks ========================================
# Devices_Tab_Variables
@app.callback(
    Output('Devices_Tab_Variables', 'children'),
    [
        Input('Device_Config_Dropdown', 'value'),
        Input('Device_Config_Read', 'n_clicks'),
        Input('Device_Config_Save', 'n_clicks'),
        Input('Device_Config_Send', 'n_clicks'),
        Input('Device_Config_Reboot', 'n_clicks'),
        Input('Device_Config_Shutdown', 'n_clicks'),
        ],
    [
        State('Devices_Tab_Variables', 'children')
        ]
    )
def Devices_Tab_Variables(Device_Config_Dropdown, Device_Config_Read, Device_Config_Save, Device_Config_Send, Device_Config_Reboot, Device_Config_Shutdown, Devices_Tab_Variables):

    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    Devices_Tab_Variables['Device_Config_Dropdown'] = Device_Config_Dropdown

    Button_List = [Device_Config_Read, Device_Config_Save, Device_Config_Send, Device_Config_Reboot, Device_Config_Shutdown]
    Button_List_Text = ['Device_Config_Read', 'Device_Config_Save', 'Device_Config_Send', 'Device_Config_Reboot', 'Device_Config_Shutdown']

    # Check if buttons was presses
    for i in range(len(Button_List)):
        if Button_List[i] != int(Devices_Tab_Variables.get(Button_List_Text[i], 0)):
            Devices_Tab_Variables['Last_Click'] = Button_List_Text[i]

            # Shutdown / Reboot
            if Devices_Tab_Variables['Device_Config_Dropdown'] is not None or []:
                Action = None
                if Devices_Tab_Variables.get('Last_Click', None) == "Device_Config_Reboot":
                    if Devices_Tab_Variables.get('Device_Config_Reboot', 0) != Device_Config_Reboot:
                        Action = 'Reboot'
                elif Devices_Tab_Variables.get('Last_Click', None) == "Device_Config_Shutdown":
                    if Devices_Tab_Variables.get('Device_Config_Shutdown', 0) != Device_Config_Shutdown:
                        Action = 'Shutdown'
                if Action is not None:
                    # Set Last_Click to none to prevent repress when changing back to tab
                    Devices_Tab_Variables['Last_Click'] = None
                    MQTT.single(System_Header + "/Commands/" + str(Devices_Tab_Variables['Device_Config_Dropdown']) + "/Power", Action + ";", hostname=MQTT_Broker, port=MQTT_Port, auth={'username': MQTT_Username, 'password': MQTT_Password})

            Devices_Tab_Variables[Button_List_Text[i]] = Button_List[i]
            break

    return Generate_Variable_String(Devices_Tab_Variables)


# Update Device Config rows
@app.callback(
    Output('Device_Config_Table', 'rows'),
    [
        Input('Devices_Tab_Variables', 'children'),
        Input('Device_Config_Save', 'n_clicks'),
        ],
    [
        State('Device_Config_Table', 'rows'),
        ]
    )
def Device_Config_Tab_Config_Show(Devices_Tab_Variables, Device_Config_Save, Device_Config_Table):

    # Open db connection
    db_Write_Connection = Open_db('Dobby')
    db_Write_Curser = db_Write_Connection.cursor()

    # Import variables from div able
    Devices_Tab_Variables = Generate_Variable_Dict(Devices_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Devices_Tab_Variables['Device_Config_Dropdown'] == "None":
        Close_db(db_Write_Connection, db_Write_Curser)
        return [{'Setting': '', 'Value': ''}]

    # ======================================== Save Config ========================================
    elif Devices_Tab_Variables.get('Last_Click', "None") == "Device_Config_Save":
        Current_Config = Generate_Device_Config_Dict(Devices_Tab_Variables['Device_Config_Dropdown'], db_Write_Curser)

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
            db_Write_Curser.execute("SELECT id FROM Dobby.DeviceConfig WHERE Hostname='" + Devices_Tab_Variables['Device_Config_Dropdown'] + "';")
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

            Devices_Tab_Variables['Last_Click'] = None

    # ======================================== Send Config ========================================
    elif Devices_Tab_Variables.get('Last_Click', "None") == "Device_Config_Send":
        Devices_Tab_Variables['Last_Click'] = None
        MQTT.single(System_Header + "/Commands/Dobby/Config", Devices_Tab_Variables['Device_Config_Dropdown'] + ",-1;", hostname=MQTT_Broker, port=MQTT_Port, auth={'username': MQTT_Username, 'password': MQTT_Password})

    # ======================================== Return table ========================================
    Return_Dict = Generate_Device_Config_Dict(Devices_Tab_Variables['Device_Config_Dropdown'], db_Write_Curser)

    Close_db(db_Write_Connection, db_Write_Curser)

    return Return_Dict


# ======================================== Log Graph Tab - Callbacks ========================================
# EP_Tab_Variables
@app.callback(
    Output('EP_Tab_Variables', 'children'),
    [
        Input('EP_Dropdown_Device', 'value'),
        Input('EP_Dropdown_Entry', 'value'),
        Input('EP_Slider', 'value'),
        ],
    [
        State('EP_Tab_Variables', 'children')
        ]
    )
def EP_Tab_Variables(EP_Dropdown_Device, EP_Dropdown_Entry, EP_Slider, EP_Tab_Variables):

    EP_Tab_Variables = Generate_Variable_Dict(EP_Tab_Variables)

    # Dropdowns
    # Set device value
    EP_Tab_Variables['EP_Dropdown_Device'] = EP_Dropdown_Device
    # IF device value is not reset all others values
    if EP_Dropdown_Entry is None:
        EP_Tab_Variables['EP_Dropdown_Entry'] = "None"
    else:
        EP_Tab_Variables['EP_Dropdown_Entry'] = EP_Dropdown_Entry

    # Slider
    if EP_Dropdown_Device is not None and EP_Dropdown_Entry is not None and EP_Dropdown_Device != [] and EP_Dropdown_Entry != []:

        Slider_Name_String = ""
        i = 0
        # Find first entry
        for Selection in EP_Dropdown_Entry:
            if i != 0:
                Slider_Name_String = Slider_Name_String + " OR "
            Slider_Name_String = Slider_Name_String + "`Name`='" + str(Selection.replace("_", " ")) + "'"
            i = i + 1

        db_Connection = Open_db(Log_db)
        db_Curser = db_Connection.cursor()

        try:
            db_Curser.execute("SELECT DateTime FROM `" + Log_db + "`.`EP_Logger` WHERE " + Slider_Name_String + " ORDER BY id ASC LIMIT 1;")
            Min_Date = db_Curser.fetchone()

            db_Curser.execute("SELECT DateTime FROM `" + Log_db + "`.`EP_Logger` WHERE " + Slider_Name_String + " ORDER BY id DESC LIMIT 1;")
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
            if EP_Slider[0] == 0:
                EP_Tab_Variables['Slider_Value_Low'] = Min_Date
            elif EP_Slider[0] == 100:
                EP_Tab_Variables['Slider_Value_Low'] = Max_Date
            else:
                EP_Tab_Variables['Slider_Value_Low'] = Min_Date + Time_Jumps * EP_Slider[0]

            # removes ".######" from the datetime string
            if len(str(EP_Tab_Variables['Slider_Value_Low'])) > 19:
                EP_Tab_Variables['Slider_Value_Low'] = str(EP_Tab_Variables['Slider_Value_Low'])[:-7]

            # Save high value
            if EP_Slider[1] == 0:
                EP_Tab_Variables['Slider_Value_High'] = Min_Date
            elif EP_Slider[1] == 100:
                EP_Tab_Variables['Slider_Value_High'] = Max_Date
            else:
                EP_Tab_Variables['Slider_Value_High'] = Min_Date + Time_Jumps * EP_Slider[1]

            # removes ".######" from the datetime string
            if len(str(EP_Tab_Variables['Slider_Value_High'])) > 19:
                EP_Tab_Variables['Slider_Value_High'] = str(EP_Tab_Variables['Slider_Value_High'])[:-7]

    return Generate_Variable_String(EP_Tab_Variables)



@app.callback(
    Output('EP_Dropdown_Entry', 'options'),
    [
        Input('EP_Dropdown_Device', 'value'),
        Input('EP_Tab_Variables', 'children'),
        ],
    )
def EP_Dropdown_Entry(EP_Dropdown_Device, EP_Tab_Variables):

    EP_Tab_Variables = Generate_Variable_Dict(EP_Tab_Variables)

    if EP_Dropdown_Device is None or EP_Dropdown_Device == 'None':
        return []

    db_Connection = Open_db(Log_db)
    db_Curser = db_Connection.cursor()

    db_Curser.execute("SELECT DISTINCT Name FROM `" + Log_db + "`.`EP_Logger` ORDER BY Name;")
    db_Fetch = db_Curser.fetchall()

    # Close db connection
    Close_db(db_Connection, db_Curser)

    Return_List = []

    for Value in db_Fetch:
        Return_List.append({'label': Value, 'value': Value[0].replace(" ", "_")})

    return Return_List



# # Update Graph
# @app.callback(
#     Output('EP_Graph', 'figure'),
#     [
#         Input('EP_Tab_Variables', 'children'),
#         ],
#     )
# def EP_Graph(EP_Tab_Variables):

#     # Import variables from div able
#     EP_Tab_Variables = Generate_Variable_Dict(EP_Tab_Variables)

#     # Do nothing if no device have been selected in the dropdown
#     if EP_Tab_Variables['EP_Dropdown_Device'] == 'None' or EP_Tab_Variables['EP_Dropdown_Entry'] == 'None' or EP_Tab_Variables is {}:
#         return {'data': ''}

#     # ======================================== Read Logs ========================================
#     else:
#         db_Connection = Open_db(Log_db)
#         db_Curser = db_Connection.cursor()

#         Data = []

#         # APC Monitor
#         if EP_Tab_Variables['EP_Dropdown_Device'] == "APC Monitor" and EP_Tab_Variables['EP_Dropdown_Rj'] != "None":

#             for Name in EP_Tab_Variables['EP_Dropdown_Entry']:

#                 for Row in EP_Tab_Variables['EP_Dropdown_Rj']:
#                     Data.append(
#                         go.Scatter(
#                             x=SQL_To_List("SELECT DateTime FROM `" + Log_db + "`.`" + EP_Tab_Variables['EP_Dropdown_Device'].replace(" ", "_") + "` WHERE Name='" + str(Name) + "' AND datetime>'" + str(EP_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
#                             y=SQL_To_List("SELECT `" + Row + "` FROM `" + Log_db + "`.`" + EP_Tab_Variables['EP_Dropdown_Device'].replace(" ", "_") + "` WHERE Name='" + str(Name) + "' AND datetime>'" + str(EP_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
#                             name=str(Name + " - " + Row),
#                             mode='lines+markers',
#                         )
#                     )

#         # KeepAliveMonitor
#         elif EP_Tab_Variables['EP_Dropdown_Device'] == "KeepAliveMonitor":
#             print "HIT KeepAliveMonitor"
#             return {'data': ''}

#         # Log Trigger
#         elif EP_Tab_Variables['EP_Dropdown_Device'] == "Log Trigger" and EP_Tab_Variables['EP_Dropdown_Rj'] != "None" and EP_Tab_Variables['EP_Dropdown_Rj'] != ['']:

#             for Name in EP_Tab_Variables['EP_Dropdown_Entry']:

#                 # Create and style traces
#                 for Tag_Name in EP_Tab_Variables['EP_Dropdown_Rj']:

#                     Plot_Name = ''
#                     if Tag_Name == '-- No Tag --':
#                         Tag_Search_String = ''
#                         Plot_Name = Name
#                     else:
#                         Tag_Search_String = "AND json_Tag='" + str(Tag_Name) + "'"
#                         Plot_Name = str(Name + " - " + Tag_Name)

#                     Date_Search_String = " AND datetime>'" + str(EP_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(EP_Tab_Variables['Slider_Value_High']) + "'"

#                     Data.append(
#                             go.Scatter(
#                                 x=SQL_To_List("SELECT DateTime FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
#                                 y=SQL_To_List("SELECT Value FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
#                                 # x=[1, 2],
#                                 # y=[1, 2],
#                                 name=Plot_Name,
#                                 mode='lines+markers',
#                                 line=dict(
#                                     dash='dash',
#                                 )
#                             )
#                         )
#         Close_db(db_Connection, db_Curser)

#         # Edit the layout
#         layout = dict(
#             # title = 'Average High and Low Temperatures in New York',
#             # xaxis=dict(title='Timestamp'),
#             # yaxis = dict(title = 'Temperature (degrees F)'),
#         )

#         fig = dict(data=Data, layout=layout)

#         return fig


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
        State('Log_Graph_Tab_Variables', 'children'),
        State('Log_Graph_Dropdown_Entry', 'options')
        ]
    )
def Log_Graph_Tab_Variables(Log_Graph_Dropdown, Log_Graph_Dropdown_Entry, Log_Graph_Dropdown_Rj, Log_Graph_Slider, Log_Graph_Tab_Variables, Log_Graph_Dropdown_Entry_Options):

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

    # Slider - only adjust slier when all values is slected
    if Log_Graph_Dropdown is not None and Log_Graph_Dropdown_Entry is not None and Log_Graph_Dropdown != [] and Log_Graph_Dropdown_Entry != []:

        Slider_Name_String = ""
        i = 0
        # Find first entry
        Name_Column = 'Name'

        # EP Logger
        if Log_Graph_Dropdown == "EP Logger":
            Name_Column = 'Device'
            SQL_Base_String = "SELECT DateTime FROM `" + Log_db + "`.`" + Log_Graph_Dropdown.replace(" ", "_") + "` WHERE " + Slider_Name_String + " ORDER BY id"


        for Selection in Log_Graph_Dropdown_Entry:
            if i != 0:
                Slider_Name_String = Slider_Name_String + " OR "
            Slider_Name_String = Slider_Name_String + "`" + Name_Column + "`='" + str(Selection) + "'"
            i = i + 1
        
        # Log Trigger
        if Log_Graph_Dropdown == "Log Trigger":
            for Entry in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:            
                SQL_Base_String = "SELECT DateTime FROM `" + Log_db + "`.`Log_Trigger_" + str(Entry) + "` ORDER BY id"


        db_Connection = Open_db(Log_db)
        db_Curser = db_Connection.cursor()

        try:
            db_Curser.execute(SQL_Base_String + " ASC LIMIT 1;")
            Min_Date = db_Curser.fetchone()

            db_Curser.execute(SQL_Base_String + " DESC LIMIT 1;")
            Max_Date = db_Curser.fetchone()

        except (MySQLdb.Error, MySQLdb.Warning) as e:
            print "SQL ERROR: " + str(e)
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
        ]
    )
def Log_Graph_Dropdown_Entry(Log_Graph_Dropdown, Log_Graph_Tab_Variables):

    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    if Log_Graph_Dropdown is None or Log_Graph_Dropdown == 'None':
        return []

    Name_Field_String = Column_Name_Check(Log_Graph_Dropdown)

    SQL_String = "SELECT id, `" + Name_Field_String + "` FROM `Dobby`.`" + Log_Graph_Dropdown.replace(" ", "_") + "` ORDER BY `" + Name_Field_String + "`;"

    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    db_Curser.execute(SQL_String)
    db_Fetch = db_Curser.fetchall()

    # Close db connection
    Close_db(db_Connection, db_Curser)

    Return_List = []

    for Key, Value in db_Fetch:
        Return_List.append({'label': Value, 'value': Key})

    return Return_List


# ======================================== Log_Graph_Dropdown_Rj - Callback ========================================
@app.callback(
    Output('Log_Graph_Dropdown_Rj', 'options'),
    [
        Input('Log_Graph_Dropdown', 'value'),
        Input('Log_Graph_Tab_Variables', 'children'),
        ],
    [
        State('Log_Graph_Dropdown_Entry', 'options')
        ]
    )
def Log_Graph_Tab_Row_json_Dropdown(Log_Graph_Dropdown, Log_Graph_Tab_Variables, Log_Graph_Dropdown_Entry_Options):

    # Make variable dic from children
    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    if Log_Graph_Dropdown is None or Log_Graph_Dropdown == 'None' or Log_Graph_Dropdown == ['']:
        return {}

    elif Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] is None or Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] == 'None' or Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] == ['']:
        return {}

    # Create the return list
    Return_List = []

    # APC Monitor
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

    # EP Logger
    elif Log_Graph_Dropdown == "EP Logger":
        # Open DB commection
        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()

        # Get tags for each entry
        for Entry in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

            try:
                db_Curser.execute("SELECT distinct Name FROM DobbyLog.EP_Logger Where Device = '" + str(Entry) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(Log_Graph_Tab_Variables['Slider_Value_High']) + "' ORDER BY Name;")
                db_Fetch = db_Curser.fetchall()
            except:
                return {}

            for Value in db_Fetch:
                if Value[0] == "":
                    Return_List.append({'label': '-- No Tag --', 'value': '-- No Tag --'})
                else:
                    Return_List.append({'label': Value[0], 'value': Value[0]})

        # Close db connection
        Close_db(db_Connection, db_Curser)

    # Log Trigger
    elif Log_Graph_Dropdown == "Log Trigger":
        # Open db commection
        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()
      
        # Get tags for each entry
        for Entry in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

            SQL_String = "SELECT distinct json_Tag FROM DobbyLog.Log_Trigger_" + str(Entry) + " Where datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(Log_Graph_Tab_Variables['Slider_Value_High']) + "' ORDER BY json_Tag;"

            try:
                db_Curser.execute(SQL_String)
                db_Fetch = db_Curser.fetchall()
            except:
                return {}

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

    if Log_Graph_Tab_Variables.get('Log_Graph_Dropdown', 'None') == 'None' or Log_Graph_Tab_Variables.get('Log_Graph_Dropdown_Entry', 'None') == 'None' or Log_Graph_Tab_Variables.get('Slider_Value_High', 'None') == 'None':
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
        State('Log_Graph_Dropdown_Entry', 'options'),
        ]
    )
def Log_Graph_Graph(Log_Graph_Tab_Variables, Log_Graph_Dropdown_Entry_Options):

    # Import variables from div able
    Log_Graph_Tab_Variables = Generate_Variable_Dict(Log_Graph_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == 'None' or Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry'] == 'None' or Log_Graph_Tab_Variables is {}:
        return {'data': ''}
    
    # ======================================== Read Logs ========================================
    else:
        db_Connection = Open_db(Log_db)
        db_Curser = db_Connection.cursor()

        Data = []

        # APC Monitor
        if Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "APC Monitor" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != "None":

            for Name in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

                for Row in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']:
                    Data.append(
                        go.Scatter(
                            x=SQL_To_List("SELECT DateTime FROM `" + Log_db + "`.`" + Log_Graph_Tab_Variables['Log_Graph_Dropdown'].replace(" ", "_") + "` WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                            y=SQL_To_List("SELECT `" + Row + "` FROM `" + Log_db + "`.`" + Log_Graph_Tab_Variables['Log_Graph_Dropdown'].replace(" ", "_") + "` WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                            name=str(Name + " - " + Row),
                            mode='lines+markers',
                        )
                    )

        # EP Logger
        elif Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "EP Logger" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != "None":

            # Add values for each device
            for Device in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

                # Add values from device
                for Value_Name in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']:
                    print 'Value_Name: ' + Value_Name

                    Plot_Name = ''
                    if Value_Name == '-- No Tag --':
                        Tag_Search_String = ''
                        Plot_Name = Device
                    else:
                        Tag_Search_String = "AND Name='" + str(Value_Name) + "'"
                        Plot_Name = str(Device + " - " + Value_Name)

                    Date_Search_String = " AND datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(Log_Graph_Tab_Variables['Slider_Value_High']) + "'"


                    print "TEST123"
                    print "SELECT DateTime FROM `" + Log_db + "`.`EP_Logger` WHERE Device='" + str(Device) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"
                    print "SELECT Value FROM `" + Log_db + "`.`EP_Logger` WHERE Device='" + str(Device) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"

                    Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM `" + Log_db + "`.`EP_Logger` WHERE Device='" + str(Device) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM `" + Log_db + "`.`EP_Logger` WHERE Device='" + str(Device) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
                                # x=[1, 2],
                                # y=[1, 2],
                                name=Plot_Name,
                                mode='lines+markers',
                                line=dict(
                                    dash='dash',
                                )
                            )
                        )

        # KeepAliveMonitor
        elif Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "KeepAliveMonitor":
            print "HIT KeepAliveMonitor"
            return {'data': ''}

        # Log Trigger
        elif Log_Graph_Tab_Variables['Log_Graph_Dropdown'] == "Log Trigger" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != "None" and Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj'] != ['']:

            for id in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Entry']:

                # Find name
                for Entry in Log_Graph_Dropdown_Entry_Options:
                    # Find name in list
                    if Entry['value'] == int(id):
                        Name = Entry['label']

                # Create and style traces
                for Tag_Name in Log_Graph_Tab_Variables['Log_Graph_Dropdown_Rj']:

                    Plot_Name = ''
                    if Tag_Name == '-- No Tag --':
                        Tag_Search_String = ''
                        Plot_Name = Name
                    else:
                        Tag_Search_String = "AND json_Tag='" + str(Tag_Name) + "'"
                        Plot_Name = str(Name + " - " + Tag_Name)

                    Date_Search_String = " datetime>'" + str(Log_Graph_Tab_Variables['Slider_Value_Low']) + "' AND datetime<'" + str(Log_Graph_Tab_Variables['Slider_Value_High']) + "'"

                    Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM `" + Log_db + "`.`Log_Trigger_" + str(id) + "`  WHERE " + Date_Search_String + Tag_Search_String + "ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM `" + Log_db + "`.`Log_Trigger_" + str(id) + "`  WHERE " + Date_Search_String + Tag_Search_String + "ORDER BY id DESC;"),
                                # x=[1, 2],
                                # y=[1, 2],
                                name=Plot_Name,
                                mode='lines+markers',
                                line=dict(
                                    dash='dash',
                                )
                            )
                        )

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Edit the layout
        layout = dict(
            # title = 'Average High and Low Temperatures in New York',
            # xaxis=dict(title='Timestamp'),
            # yaxis = dict(title = 'Temperature (degrees F)'),
        )

        fig = dict(data=Data, layout=layout)

        return fig



# ======================================== Live Tab - Callbacks ========================================
@app.callback(
    Output('Live_Tab_Variables', 'children'),
    [
        Input('Live_Dropdown', 'value'),
        Input('Live_Dropdown_json', 'value'),
        Input('Live_Slider', 'value'),
        ],
    [
        State('Live_Tab_Variables', 'children'),
        ],
    )
def Live_Tab_Variables_Callback(Live_Dropdown, Live_Dropdown_json, Live_Slider, Live_Tab_Variables):

    Live_Tab_Variables = Generate_Variable_Dict(Live_Tab_Variables)

    # Main Dropdown
    if Live_Tab_Variables.get('Live_Dropdown', "None") is "None" or Live_Tab_Variables.get('Live_Dropdown', "None") is None or Live_Tab_Variables.get('Live_Dropdown', "None") == []:
        Live_Tab_Variables['Live_Dropdown'] = "None"
    else:
        Live_Tab_Variables['Live_Dropdown'] = Live_Dropdown

    # json dropdown
    if Live_Tab_Variables.get('Live_Dropdown_json', ["None"]) is "None" or Live_Tab_Variables.get('Live_Dropdown_json', ["None"]) is None or Live_Tab_Variables.get('Live_Dropdown_json', ["None"]) == []:
        Live_Tab_Variables['Live_Dropdown_json'] = "None"
    else:
        Live_Tab_Variables['Live_Dropdown_json'] = Live_Dropdown_json

    # Check if someting is selected in main if not set json to none
    if Live_Tab_Variables['Live_Dropdown'] is "None" or Live_Tab_Variables['Live_Dropdown'] is None or Live_Tab_Variables['Live_Dropdown'] == []:
        Live_Tab_Variables['Live_Dropdown_json'] = "None"
  
    Live_Tab_Variables['Live_Slider'] = Live_Slider

    return Generate_Variable_String(Live_Tab_Variables)



# ================================================================================
@app.callback(
    Output('Live_Graph', 'figure'),
    [
        Input('Live_Interval_Component', 'n_intervals'),
        ],
    [
        State('Live_Tab_Variables', 'children'),
        ],
    )
def Live_Tab_Auto_Update(Live_Interval_Component, Live_Tab_Variables):

    Live_Tab_Variables = Generate_Variable_Dict(Live_Tab_Variables)

    if Live_Tab_Variables.get('Live_Dropdown_json', "None") == 'None':
        return {'data': ''}

    
    # ======================================== Read Logs ========================================
    # Open db connection
    db_Connection = Open_db(Log_db)
    db_Curser = db_Connection.cursor()

    Data = []

    # Log Trigger
    for Name in Live_Tab_Variables.get('Live_Dropdown', ''):

        # Create and style traces
        for Tag_Name in Live_Tab_Variables['Live_Dropdown_json']:

            Plot_Name = ''
            if Tag_Name == '-- No Tag --':
                Tag_Search_String = ''
                Plot_Name = Name
            else:
                Tag_Search_String = "AND json_Tag='" + str(Tag_Name) + "'"
                Plot_Name = str(Name + " - " + Tag_Name)

            # Get how far back to sow logs
            # Get Slider value
            Min_Int = Live_Tab_Variables.get('Live_Slider', 30)
            # Convert to int
            Min_Int = int(Min_Int)
            # Multiply by 5
            Min_Int = Min_Int * 5

            Date_Search_String = " AND datetime>'" + str(datetime.datetime.now() - datetime.timedelta(minutes=Min_Int)) + "'"

            # # print "PIK:" + Tag_Search_String
            # # print "SELECT DateTime FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"

            # db_Curser.execute("SELECT DateTime FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;")
            # temp = db_Curser.fetchall()

            # # print "s"
            # # print temp

            Data.append(
                    go.Scatter(
                        x=SQL_To_List("SELECT DateTime FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
                        y=SQL_To_List("SELECT Value FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + str(Name) + "' " + Tag_Search_String + Date_Search_String + "ORDER BY id DESC;"),
                        # x=[1, 2],
                        # y=[1, 2],
                        name=Plot_Name,
                        mode='lines+markers',
                        line=dict(
                            dash='dash',
                        )
                    )
                )
    Close_db(db_Connection, db_Curser)

    # Edit the layout
    layout = dict(
        # title = 'Average High and Low Temperatures in New York',
        # xaxis=dict(title='Timestamp'),
        # yaxis = dict(title = 'Temperature (degrees F)'),
    )

    fig = dict(data=Data, layout=layout)

    return fig


# ================================================================================
@app.callback(
    Output('Live_Dropdown_json', 'options'),
    [
        Input('Live_Dropdown', 'value'),
        Input('Live_Tab_Variables', 'children'),
        ],
    )
def Live_Dropdown_json(Live_Dropdown, Live_Tab_Variables):

    # Make variable dic from children
    Live_Tab_Variables = Generate_Variable_Dict(Live_Tab_Variables)

    if Live_Dropdown is None or Live_Dropdown == 'None' or Live_Dropdown == ['']:
        return {}

    elif Live_Tab_Variables['Live_Dropdown'] is None or Live_Tab_Variables['Live_Dropdown'] == 'None' or Live_Tab_Variables['Live_Dropdown'] == ['']:
        return {}

    # Create the return list
    Return_List = []

    # Open DB commection
    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    for Selected in Live_Dropdown:

        db_Curser.execute("SELECT distinct json_Tag FROM DobbyLog.Log_Trigger Where Name = '" + str(Selected) + "' ORDER BY json_Tag;")
        db_Fetch = db_Curser.fetchall()

        for i in range(len(db_Fetch)):

            if db_Fetch[i][0] == "":
                Return_List.append({'label': '-- No Tag --', 'value': '-- No Tag --'})

            else:
                Return_List.append({'label': db_Fetch[i][0], 'value': db_Fetch[i][0]})

    # Close db connection
    Close_db(db_Connection, db_Curser)

    return Return_List


# ======================================== System Log Tab - Callbacks ========================================
@app.callback(
    Output('System_Log_Tab_Variables', 'children'),
    [
        Input('System_Log_Dropdown', 'value'),
        Input('System_Log_Read_Button', 'n_clicks'),
        Input('System_Log_Number_Of_Input', 'value'),
        Input('System_Log_Auto_Refresh', 'values'),
        ],
    [
        State('System_Log_Tab_Variables', 'children'),
        ],
    )
def System_Log_Tab_Dropdown(System_Log_Dropdown, System_Log_Read_Button, System_Log_Number_Of_Input, System_Log_Auto_Refresh, System_Log_Tab_Variables):

    # Import variables from div able
    System_Log_Tab_Variables = Generate_Variable_Dict(System_Log_Tab_Variables)

    # Dropdown
    System_Log_Tab_Variables['System_Log_Dropdown'] = System_Log_Dropdown

    if System_Log_Dropdown is None:
        System_Log_Tab_Variables['System_Log_Dropdown'] = "None"

    # Set columns in var for later use
    System_Log_Tab_Variables['System_Log_Read_Button'] = System_Log_Read_Button
    
    System_Log_Tab_Variables['System_Log_Number_Of_Input'] = System_Log_Number_Of_Input

    System_Log_Tab_Variables['System_Log_Auto_Refresh'] = System_Log_Auto_Refresh

    return Generate_Variable_String(System_Log_Tab_Variables)


# Change column names
@app.callback(
    Output('System_Log_Tab_Table', 'columns'),
    [
        Input('System_Log_Tab_Variables', 'children'),
        Input('System_Log_Read_Button', 'n_clicks'),
        Input('System_Log_Number_Of_Input', 'values'),
        ],
    [
        # State('System_Log_Tab_Table', 'columns'),
        ]
    )
def System_Log_Tab_Table_Comumns(System_Log_Tab_Variables, System_Log_Read_Button, System_Log_Number_Of_Input):

    System_Log_Tab_Variables = Generate_Variable_Dict(System_Log_Tab_Variables)

    return Generate_System_Log_Table_Columns(System_Log_Tab_Variables.get('System_Log_Dropdown', ["None"]))


# Disable auto update
@app.callback(
    Output('System_Log_Interval_Component', 'interval'),
    [
        Input('System_Log_Auto_Refresh', 'values'),
    ],
    )
def System_Log_Auto_Refresh_Check(System_Log_Auto_Refresh):
    
    if str(System_Log_Auto_Refresh) == "[u'AutoRefresh']":
        return 1500
    else:
        return 3600000



# Read content
@app.callback(
    Output('System_Log_Tab_Table', 'data'),
    [
        Input('System_Log_Tab_Variables', 'children'),
        Input('System_Log_Interval_Component', 'n_intervals'),
    ],
    )
def System_Log_Tab_Table_Rows(System_Log_Tab_Variables, System_Log_Interval_Component):

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
        Input('System_Test_BT_Button', 'n_clicks'),
        Input('System_Restart_Services', 'n_clicks'),
        ],
    [
        State('System_Tab_Variables', 'children'),
        ],
    )
def System_Tab_Buttons(System_Quit_Button, System_Test_BT_Button, System_Restart_Services, System_Tab_Variables):

    System_Tab_Variables = Generate_Variable_Dict(System_Tab_Variables)

    if int(System_Tab_Variables.get('System_Quit_Button', 0)) != int(System_Quit_Button):
        System_Tab_Variables['System_Quit_Button'] = System_Quit_Button

        print "System shutdown requested, shutting down"
        Server_Shutdown()

    elif int(System_Tab_Variables.get('System_Restart_Services', 0)) != int(System_Restart_Services):
        System_Tab_Variables['System_Restart_Services'] = System_Restart_Services

        # Dash needs to be shotdown before restarting the service for it work proberly
        Server_Shutdown()

        print "System service restart requested, restarting services"

        print "MARKER 456"
        

    elif int(System_Tab_Variables.get('System_Test_BT_Button', 0)) != int(System_Test_BT_Button):
        System_Tab_Variables['System_Test_BT_Button'] = System_Test_BT_Button

        myCmd = "mpg321 -g 50 /etc/Dobby/Audio/Ping.mp3"
        os.system(myCmd)


    return Generate_Variable_String(System_Tab_Variables)


# FIX - Move css to local storage
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
# Removed undo/redo
app.css.append_css({'external_url': 'https://rawgit.com/lwileczek/Dash/master/undo_redo5.css'})

print "Dash Core Components: " + str(dcc.__version__)
print "Dash HTML Components: " + str(html.__version__)
print "Dash Table: " + str(dt.__version__)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', ssl_context=('/etc/Dobby/Cert/cert.pem', '/etc/Dobby/Cert/key.pem'))
