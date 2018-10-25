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

# Scacda
import plotly.graph_objs as go


# MISC
# import collections
# import ast

# json
# import json

# MISC
Version = 102002
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


# ======================================== Generate_Spammer_Dict ========================================
def Generate_Spammer_Dict(Selected_Spammer, db_Curser):

    if Selected_Spammer is None:
        return None

    db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='Spammer';")
    Spammer_Setting = db_Curser.fetchall()

    db_Curser.execute("SELECT * FROM Dobby.Spammer WHERE `Name`='" + Selected_Spammer + "';")
    Spammer_Value = db_Curser.fetchone()

    Row_List = []
    Config_Ignore_List = ['id', 'Date_Modified']

    i = 0

    for Setting in Spammer_Setting:
        if Setting[0] not in Config_Ignore_List:
            Row_List.append({'Setting': [Setting[0]], 'Value': [Spammer_Value[i]]})
        i = i + 1

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


# ======================================== Layout ========================================
app.layout = html.Div([

    dcc.Tabs(id="tabs", value='APC_Tab', children=[
        dcc.Tab(label='APC Monitor', value='APC_Tab'),
        # dcc.Tab(label='Device', value='Device_Tab'),
        dcc.Tab(label='Device Config', value='Device_Config_Tab'),
        dcc.Tab(label='Log Trigger', value='Log_Trigger_Tab'),
        # dcc.Tab(label='Log Trigger Config', value='Log_Trigger_Config_Tab'),
        dcc.Tab(label='Spammer', value='Spammer_Tab'),
        dcc.Tab(label='System', value='System_Tab'),
        ]),

    html.Div(id='Main_Tabs'),

    # No idea why this needs to be here, if its not the tabs with datatables does not load
    html.Div([
        dt.DataTable(rows=[{}]),
        ], style={"display": "none"}),

    # Places to store variables
    html.Div([
        html.Div(id='APC_Tab_Variables', children=""),
        # html.Div(id='Device_Tab_Variables', children=""),
        html.Div(id='Device_Config_Tab_Variables', children=""),
        html.Div(id='Log_Trigger_Tab_Variables', children=""),
        # html.Div(id='Log_Trigger_Config_Tab_Variables', children=""),
        html.Div(id='Spammer_Tab_Variables', children=""),
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
        State('APC_Tab_Variables', 'children'),
        # State('Device_Tab_Variables', 'children'),
        State('Device_Config_Tab_Variables', 'children'),
        State('Log_Trigger_Tab_Variables', 'children'),
        # State('Log_Trigger_Config_Tab_Variables', 'children'),
        State('Spammer_Tab_Variables', 'children'),
        State('System_Tab_Variables', 'children'),
        ]
    )
def render_content(tab, APC_Tab_Variables, Device_Config_Tab_Variables, Log_Trigger_Tab_Variables, Spammer_Tab_Variables, System_Tab_Variables):
    # ======================================== APC Tab ========================================
    # ======================================== APC Tab ========================================
    # ======================================== APC Tab ========================================
    if tab == 'APC_Tab':
        APC_Tab_Variables = Generate_Variable_Dict(APC_Tab_Variables)

        return html.Div(
            id='APC_Tab_Tab',
            children=[

                dcc.Dropdown(
                    id='APC_Dropdown',
                    options=[{'label': Name, 'value': Name} for Name in SQL_To_List("SELECT DISTINCT Name FROM DobbyLog.APC_Monitor;")],
                    multi=True,
                    value=APC_Tab_Variables.get('APC_Dropdown', None),
                ),
                dcc.Graph(
                    id='APC_Graph',
                    style={
                        'height': '70vh',
                        'width': '95vw',
                        'padding': 5,
                    }
                ),
                html.Div(
                    style={
                        'width': '85vw',
                        'padding': 50,
                        'display': 'inline-block'
                        },
                    children=[
                        dcc.RangeSlider(
                            id='APC_Slider',
                            min=0,
                            max=100,
                            step=1,
                            value=[95, 100],
                            allowCross=False,
                            marks={},
                            ),
                        ],
                    ),

                html.Button('Read', id='APC_Read', n_clicks=0, style={'margin-top': '5px'}),
            ],

            #
        )

    # if tab == 'APC_Config_Tab':
    #     APC_Tab_Variables = Generate_Variable_Dict(APC_Tab_Variables)
    #
    #     return html.Div(
    #         id='APC_Tab',
    #         children=[
    #             # Dropdown to select APC
    #             dcc.Dropdown(
    #                 id='APC_Dropdown',
    #                 options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT Name FROM Dobby.APC_Monitor ORDER BY Name;")],
    #                 value=APC_Tab_Variables.get('APC_Dropdown', None),
    #                 ),
    #             # Config table
    #             dt.DataTable(
    #                 id='APC_Table',
    #                 rows=[],
    #                 columns=['Setting', 'Value'],
    #                 min_height=320,
    #                 resizable=True,
    #                 editable=True,
    #                 filterable=True,
    #                 sortable=True,
    #                 ),
    #             html.Button('Read', id='APC_Read', n_clicks=0, style={'margin-top': '5px'}),
    #         ],
    #     )

    # ======================================== Spammer Tab ========================================
    # ======================================== Spammer Tab ========================================
    # ======================================== Spammer Tab ========================================
    elif tab == 'Spammer_Tab':
        Spammer_Tab_Variables = Generate_Variable_Dict(Spammer_Tab_Variables)

        return html.Div(
            id='Spammer_Tab',
            children=[
                # Dropdown to select Spammer
                dcc.Dropdown(
                    id='Spammer_Dropdown',
                    options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT Name FROM Dobby.Spammer ORDER BY Name;")],
                    value=Spammer_Tab_Variables.get('Spammer_Dropdown', None),
                    ),
                # Config table
                dt.DataTable(
                    id='Spammer_Table',
                    rows=[],
                    columns=['Setting', 'Value'],
                    min_height=320,
                    resizable=True,
                    editable=True,
                    filterable=True,
                    sortable=True,
                    ),
                html.Button('Read', id='Spammer_Read', n_clicks=0, style={'margin-top': '5px'}),
                html.Button('Save', id='Spammer_Save', n_clicks=0, style={'margin-left': '5px', 'margin-top': '5px'}),
            ],
        )

    # ======================================== Log Trigger Tab ========================================
    # ======================================== Log Trigger Tab ========================================
    # ======================================== Log Trigger Tab ========================================
    elif tab == 'Log_Trigger_Tab':

        Log_Trigger_Tab_Variables = Generate_Variable_Dict(Log_Trigger_Tab_Variables)

        return html.Div(
            id='Log_Trigger_Tab',
            children=[
                # Dropdown to select logs
                dcc.Dropdown(
                    id='Log_Trigger_Dropdown',
                    options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT DISTINCT Name FROM DobbyLog.Log_Trigger;")],
                    multi=True,
                    value=Log_Trigger_Tab_Variables.get('Log_Trigger_Dropdown', None),
                ),

                dcc.Graph(
                    id='Log_Trigger_Graph',
                    style={
                        'height': '70vh',
                        'width': '95vw',
                        'padding': 5,
                        }
                    ),

                html.Div(
                    id='Log_Trigger_Tab',
                    style={
                        'width': '90vw',
                        'padding': 50,
                        'display': 'inline-block'
                        },
                    children=[
                        dcc.RangeSlider(
                            id='Log_Trigger_Slider',
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

    # ======================================== Log Trigger Tab ========================================
    # ======================================== Log Trigger Tab ========================================
    # ======================================== Log Trigger Tab ========================================
    elif tab == 'Device_Config_Tab':
        Device_Config_Tab_Variables = Generate_Variable_Dict(Device_Config_Tab_Variables)

        return html.Div(
            id='Device_Config_Tab',
            children=[
                # Dropdown to select device
                dcc.Dropdown(
                    id='Device_Config_Dropdown',
                    options=[{'label': Trigger, 'value': Trigger} for Trigger in SQL_To_List("SELECT Hostname FROM Dobby.DeviceConfig ORDER BY Hostname;")],
                    value=Device_Config_Tab_Variables.get('Device_Config_Dropdown', None),
                    ),
                # Config table
                dt.DataTable(
                    id='Device_Config_Table',
                    rows=[],
                    columns=['Setting', 'Value'],
                    min_height=500,
                    resizable=True,
                    editable=True,
                    filterable=True,
                    sortable=True,
                    ),
                html.Button('Read', id='Device_Config_Read', n_clicks=0, style={'margin-top': '5px'}),
                html.Button('Save', id='Device_Config_Save', n_clicks=0, style={'margin-left': '5px', 'margin-top': '5px'}),
                html.Button('Send Config', id='Device_Config_Send', n_clicks=0, style={'margin-left': '5px', 'margin-top': '5px'}),
                html.Button('Reboot', id='Device_Config_Reboot', n_clicks=0, style={'margin-left': '50px', 'margin-top': '5px'}),
                html.Button('Shutdown', id='Device_Config_Shutdown', n_clicks=0, style={'margin-left': '20px', 'margin-top': '5px'}),
                ],
            ),

    # ======================================== System Tab ========================================
    # ======================================== System Tab ========================================
    # ======================================== System Tab ========================================
    elif tab == 'System_Tab':
        System_Tab_Variables = Generate_Variable_Dict(System_Tab_Variables)

        return html.Div([
            html.Button('Quit', id='System_Quit_Button', n_clicks=0),
        ], id='System_Tab')


# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================
# ================================================================================ Callbacks ================================================================================

# ======================================== Spammer Tab - Callbacks ========================================
@app.callback(
    Output('APC_Tab_Variables', 'children'),
    [
        Input('APC_Dropdown', 'value'),
        Input('APC_Slider', 'value'),
        Input('APC_Read', 'n_clicks'),
        ],
    [
        State('APC_Tab_Variables', 'children')
        ]
    )
def APC_Tab_Variables(APC_Dropdown, APC_Slider, APC_Read, APC_Tab_Variables):

    APC_Tab_Variables = Generate_Variable_Dict(APC_Tab_Variables)

    # Dropdown
    APC_Tab_Variables['APC_Dropdown'] = APC_Dropdown

    # Button
    Button_List = [APC_Read]
    Button_List_Text = ['APC_Read']

    for i in range(len(Button_List)):
        if Button_List[i] != int(APC_Tab_Variables.get(Button_List_Text[i], 0)):
            APC_Tab_Variables['Last_Click'] = Button_List_Text[i]
            APC_Tab_Variables[Button_List_Text[i]] = Button_List[i]
            break

    # Slider
    if APC_Dropdown is not None and APC_Dropdown != []:
        Slider_Name_String = ""
        i = 0
        # Find first entry
        for Selection in APC_Dropdown:
            if i != 0:
                Slider_Name_String = Slider_Name_String + " OR "
            Slider_Name_String = Slider_Name_String + "`Name`='" + str(Selection) + "'"
            i = i + 1

        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT DateTime FROM DobbyLog.APC_Monitor WHERE " + Slider_Name_String + " ORDER BY id ASC LIMIT 1;")
        Min_Date = db_Curser.fetchone()

        db_Curser.execute("SELECT DateTime FROM DobbyLog.APC_Monitor WHERE " + Slider_Name_String + " ORDER BY id DESC LIMIT 1;")
        Max_Date = db_Curser.fetchone()

        # Close db connection
        Close_db(db_Connection, db_Curser)

        if Min_Date is not None or Max_Date is not None:
            Min_Date = Min_Date[0]
            Max_Date = Max_Date[0]

            # Save min/max
            APC_Tab_Variables['Slider_Min_Date'] = Min_Date
            APC_Tab_Variables['Slider_Max_Date'] = Max_Date

            Time_Span = Max_Date - Min_Date
            Time_Jumps = Time_Span / 100

            # Save Low value
            if APC_Slider[0] == 0:
                APC_Tab_Variables['Slider_Value_Low'] = Min_Date
            elif APC_Slider[0] == 100:
                APC_Tab_Variables['Slider_Value_Low'] = Max_Date
            else:
                APC_Tab_Variables['Slider_Value_Low'] = Min_Date + Time_Jumps * APC_Slider[0]

            # removes ".######" from the datetime string
            if len(str(APC_Tab_Variables['Slider_Value_Low'])) > 19:
                APC_Tab_Variables['Slider_Value_Low'] = str(APC_Tab_Variables['Slider_Value_Low'])[:-7]

            # Save high value
            if APC_Slider[1] == 0:
                APC_Tab_Variables['Slider_Value_High'] = Min_Date
            elif APC_Slider[1] == 100:
                APC_Tab_Variables['Slider_Value_High'] = Max_Date
            else:
                APC_Tab_Variables['Slider_Value_High'] = Min_Date + Time_Jumps * APC_Slider[1]

            # removes ".######" from the datetime string
            if len(str(APC_Tab_Variables['Slider_Value_High'])) > 19:
                APC_Tab_Variables['Slider_Value_High'] = str(APC_Tab_Variables['Slider_Value_High'])[:-7]

    return Generate_Variable_String(APC_Tab_Variables)


# Update Graph
@app.callback(
    Output('APC_Graph', 'figure'),
    [
        Input('APC_Tab_Variables', 'children'),
        ],
    )
def APC_Graph(APC_Tab_Variables):

    # Import variables from div able
    APC_Tab_Variables = Generate_Variable_Dict(APC_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if APC_Tab_Variables['APC_Dropdown'] == 'None' or APC_Tab_Variables is {}:
        return {'data': ''}

    # ======================================== Read Logs ========================================
    else:
        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()

        Data = []

        for Name in APC_Tab_Variables['APC_Dropdown']:

            for i in ['Hertz A', 'Hertz B', 'Vin A', 'Vin B', 'I Out', 'IO Max', 'IO Min', 'Active Output']:
                Data.append(
                    go.Scatter(
                        x=SQL_To_List("SELECT DateTime FROM DobbyLog.APC_Monitor WHERE Name='" + str(Name) + "' AND datetime>'" + str(APC_Tab_Variables['Slider_Value_Low']) + "' ORDER BY DateTime DESC;"),
                        y=SQL_To_List("SELECT `" + i + "` FROM DobbyLog.APC_Monitor WHERE Name='" + str(Name) + "' AND datetime>'" + str(APC_Tab_Variables['Slider_Value_Low']) + "' ORDER BY DateTime DESC;"),
                        name=str(Name) + " - " + i,
                        mode='lines+markers',
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


# ======================================== Spammer Tab - Callbacks ========================================
@app.callback(
    Output('Spammer_Tab_Variables', 'children'),
    [
        Input('Spammer_Dropdown', 'value'),
        Input('Spammer_Read', 'n_clicks'),
        Input('Spammer_Save', 'n_clicks'),
        ],
    [
        State('Spammer_Tab_Variables', 'children')
        ]
    )
def Spammer_Tab_Variables(Spammer_Dropdown, Spammer_Read, Spammer_Save, Spammer_Tab_Variables):

    Spammer_Tab_Variables = Generate_Variable_Dict(Spammer_Tab_Variables)

    Spammer_Tab_Variables['Spammer_Dropdown'] = Spammer_Dropdown

    Button_List = [Spammer_Read, Spammer_Save]
    Button_List_Text = ['Spammer_Read', 'Spammer_Save']

    for i in range(len(Button_List)):
        if Button_List[i] != int(Spammer_Tab_Variables.get(Button_List_Text[i], 0)):
            Spammer_Tab_Variables['Last_Click'] = Button_List_Text[i]
            Spammer_Tab_Variables[Button_List_Text[i]] = Button_List[i]
            break

    return Generate_Variable_String(Spammer_Tab_Variables)


# Update Device Config rows
@app.callback(
    Output('Spammer_Table', 'rows'),
    [
        Input('Spammer_Tab_Variables', 'children'),
        ],
    [
        State('Spammer_Table', 'rows'),
        ]
    )
def Spammer_Tab_Config_Show(Spammer_Tab_Variables, Spammer_Table):

    # Import variables from div able
    Spammer_Tab_Variables = Generate_Variable_Dict(Spammer_Tab_Variables)

    # Open db connection
    db_Write_Connection = Open_db('Dobby')
    db_Write_Curser = db_Write_Connection.cursor()

    Return_Dict = [{'Setting': '', 'Value': ''}]

    # Do nothing if no device have been selected in the dropdown
    if Spammer_Tab_Variables['Spammer_Dropdown'] == "None" or []:
        Close_db(db_Write_Connection, db_Write_Curser)
        return Return_Dict

    # ======================================== Save Config ========================================
    elif Spammer_Tab_Variables.get('Last_Click', "None") == "Spammer_Read":
        Spammer_Tab_Variables['Last_Click'] = "None"

    # ======================================== Save Config ========================================
    elif Spammer_Tab_Variables.get('Last_Click', "None") == "Spammer_Save":

        Spammer_Tab_Variables['Last_Click'] = "None"

        Current_Config = Generate_Spammer_Dict(Spammer_Tab_Variables['Spammer_Dropdown'], db_Write_Curser)

        # Needed to refer between tables
        i = 0

        # Needed so you dont change the config id when no changes is made
        Config_Changes = {}

        for Current_Config_Row in Current_Config:

            # For some odd reason "is datetime.datetime" does not work
            # If datetime convert to string to get == below to work
            if str(type(Current_Config_Row['Value'][0])) == "<type 'datetime.datetime'>":
                Current_Config_Row['Value'][0] = str(Current_Config_Row['Value'][0])

            # If value is '' set it to NULL
            if Spammer_Table[i]['Value'] == '':
                Config_Changes[Spammer_Table[i]['Setting'][0]] = 'NULL'

            elif Spammer_Table[i]['Value'][0] != Current_Config_Row['Value'][0]:
                # Add chnages to chnages dict
                Config_Changes[Spammer_Table[i]['Setting'][0]] = Spammer_Table[i]['Value']

            i = i + 1

        if Config_Changes != {}:

            # Get device id for use in sql changes below
            db_Write_Curser.execute("SELECT id FROM Dobby.Spammer WHERE Name='" + Spammer_Tab_Variables['Spammer_Dropdown'] + "';")
            Spammer_id = db_Write_Curser.fetchone()
            Spammer_id = str(Spammer_id[0])

            # Apply changes
            for key, value in Config_Changes.iteritems():
                if value is 'NULL':
                    db_Write_Curser.execute("UPDATE `Dobby`.`Spammer` SET `" + str(key) + "`=NULL WHERE `id`='" + Spammer_id + "';")
                else:
                    print value[0]
                    print type(value[0])
                    # db_Write_Curser.execute("UPDATE `Dobby`.`Spammer` SET `" + str(key) + "`='" + str(value) + "' WHERE `id`='" + Spammer_id + "';")

            # Update Last modified
            db_Write_Curser.execute("UPDATE `Dobby`.`Spammer` SET `Last_Modified`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + Spammer_id + "';")

    # ======================================== Return table ========================================
    Return_Dict = Generate_Spammer_Dict(Spammer_Tab_Variables['Spammer_Dropdown'], db_Write_Curser)

    Close_db(db_Write_Connection, db_Write_Curser)

    return Return_Dict


# ======================================== Device Config Tab - Callbacks ========================================
# Device_Config_Tab_Variables
@app.callback(
    Output('Device_Config_Tab_Variables', 'children'),
    [
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
            db_Write_Curser.execute("UPDATE `Dobby`.`DeviceConfig` SET `Date_Modified`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + Device_id + "';")

            Device_Config_Tab_Variables['Last_Click'] = None

    # ======================================== Send Config ========================================
    elif Device_Config_Tab_Variables.get('Last_Click', "None") == "Device_Config_Send":
        Device_Config_Tab_Variables['Last_Click'] = None
        MQTT.single(System_Header.Value[0] + "/Commands/Dobby/Config", Device_Config_Tab_Variables['Device_Config_Dropdown'] + ",-1;", hostname=MQTT_Broker.Value[0], port=MQTT_Port.Value[0], auth={'username': MQTT_Username.Value[0], 'password': MQTT_Password.Value[0]})

    # ======================================== Return table ========================================
    Return_Dict = Generate_Device_Config_Dict(Device_Config_Tab_Variables['Device_Config_Dropdown'], db_Write_Curser)

    Close_db(db_Write_Connection, db_Write_Curser)

    return Return_Dict


# ======================================== Log Trigger Tab - Callbacks ========================================
# Log_Trigger_Tab_Variables
@app.callback(
    Output('Log_Trigger_Tab_Variables', 'children'),
    [
        Input('Log_Trigger_Dropdown', 'value'),
        Input('Log_Trigger_Slider', 'value'),
        ],
    [
        State('Log_Trigger_Tab_Variables', 'children')
        ]
    )
def Log_Trigger_Tab_Variables(Log_Trigger_Dropdown, Log_Trigger_Slider, Log_Trigger_Tab_Variables):

    Log_Trigger_Tab_Variables = Generate_Variable_Dict(Log_Trigger_Tab_Variables)

    Log_Trigger_Tab_Variables['Log_Trigger_Dropdown'] = Log_Trigger_Dropdown

    # Slider
    if Log_Trigger_Dropdown is not None and Log_Trigger_Dropdown != []:

        Slider_Name_String = ""
        i = 0
        # Find first entry
        for Selection in Log_Trigger_Dropdown:
            if i != 0:
                Slider_Name_String = Slider_Name_String + " OR "
            Slider_Name_String = Slider_Name_String + "`Name`='" + str(Selection) + "'"
            i = i + 1

        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE " + Slider_Name_String + " ORDER BY id ASC LIMIT 1;")
        Min_Date = db_Curser.fetchone()

        db_Curser.execute("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE " + Slider_Name_String + " ORDER BY id DESC LIMIT 1;")
        Max_Date = db_Curser.fetchone()

        # Close db connection
        Close_db(db_Connection, db_Curser)

        if Min_Date is not None or Max_Date is not None:
            Min_Date = Min_Date[0]
            Max_Date = Max_Date[0]

            # Save min/max
            Log_Trigger_Tab_Variables['Slider_Min_Date'] = Min_Date
            Log_Trigger_Tab_Variables['Slider_Max_Date'] = Max_Date

            Time_Span = Max_Date - Min_Date
            Time_Jumps = Time_Span / 100

            # Save Low value
            if Log_Trigger_Slider[0] == 0:
                Log_Trigger_Tab_Variables['Slider_Value_Low'] = Min_Date
            elif Log_Trigger_Slider[0] == 100:
                Log_Trigger_Tab_Variables['Slider_Value_Low'] = Max_Date
            else:
                Log_Trigger_Tab_Variables['Slider_Value_Low'] = Min_Date + Time_Jumps * Log_Trigger_Slider[0]

            # removes ".######" from the datetime string
            if len(str(Log_Trigger_Tab_Variables['Slider_Value_Low'])) > 19:
                Log_Trigger_Tab_Variables['Slider_Value_Low'] = str(Log_Trigger_Tab_Variables['Slider_Value_Low'])[:-7]

            # Save high value
            if Log_Trigger_Slider[1] == 0:
                Log_Trigger_Tab_Variables['Slider_Value_High'] = Min_Date
            elif Log_Trigger_Slider[1] == 100:
                Log_Trigger_Tab_Variables['Slider_Value_High'] = Max_Date
            else:
                Log_Trigger_Tab_Variables['Slider_Value_High'] = Min_Date + Time_Jumps * Log_Trigger_Slider[1]

            # removes ".######" from the datetime string
            if len(str(Log_Trigger_Tab_Variables['Slider_Value_High'])) > 19:
                Log_Trigger_Tab_Variables['Slider_Value_High'] = str(Log_Trigger_Tab_Variables['Slider_Value_High'])[:-7]

    return Generate_Variable_String(Log_Trigger_Tab_Variables)


# ======================================== Log_Trigger - Slider Marks ========================================
@app.callback(
    Output('Log_Trigger_Slider', 'marks'),
    [
        Input('Log_Trigger_Tab_Variables', 'children')
        ],
    [
        # State('Log_Trigger_Tab_Variables', 'children'),
        ]
    )
def Log_Trigger_Update_Slider_Marks(Log_Trigger_Tab_Variables):

    Log_Trigger_Tab_Variables = Generate_Variable_Dict(Log_Trigger_Tab_Variables)

    if Log_Trigger_Tab_Variables.get('Log_Trigger_Dropdown', 'None') == 'None':
        return {}

    Time_Span = Log_Trigger_Tab_Variables['Slider_Max_Date'] - Log_Trigger_Tab_Variables['Slider_Min_Date']
    Time_Jumps = Time_Span / 10

    Marks_Dict = {}

    # Add the first and last label
    Marks_Dict['0'] = {'label': Log_Trigger_Tab_Variables['Slider_Min_Date']}
    Marks_Dict['100'] = {'label': Log_Trigger_Tab_Variables['Slider_Max_Date']}

    print "Log_Trigger_Tab_Variables"
    print Log_Trigger_Tab_Variables

    # Add the rest of the labels
    for i in range(1, 10):
        Name = str(i * 10)
        Label = str(Log_Trigger_Tab_Variables['Slider_Min_Date'] + Time_Jumps * i)

        # The [:-7] removes the ms from the end of the string
        if "." in Label:
            Label = Label[:-7]

        Marks_Dict[Name] = {'label': Label}

    return Marks_Dict


# Update Graph
@app.callback(
    Output('Log_Trigger_Graph', 'figure'),
    [
        Input('Log_Trigger_Tab_Variables', 'children'),
        ],
    )
def Log_Trigger_Graph(Log_Trigger_Tab_Variables):

    # Import variables from div able
    Log_Trigger_Tab_Variables = Generate_Variable_Dict(Log_Trigger_Tab_Variables)

    # Do nothing if no device have been selected in the dropdown
    if Log_Trigger_Tab_Variables['Log_Trigger_Dropdown'] == 'None' or Log_Trigger_Tab_Variables is {}:
        return {'data': ''}

    # ======================================== Read Logs ========================================
    else:
        db_Connection = Open_db("DobbyLog")
        db_Curser = db_Connection.cursor()

        Data = []

        for Name in Log_Trigger_Tab_Variables['Log_Trigger_Dropdown']:

            json_Tag_List = SQL_To_List("SELECT DISTINCT json_Tag FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY json_Tag;")

            if len(json_Tag_List) > 1:
                # Create and style traces
                for Tag_Name in json_Tag_List:

                    if "Min" in Tag_Name:
                        Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                name=str(Name + " - " + Tag_Name),
                                mode='lines+markers',
                                line=dict(
                                    dash='dash',
                                )
                            )
                        )

                    elif "Max" in Tag_Name:
                        Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                name=str(Name + " - " + Tag_Name),
                                mode='lines+markers',
                                line=dict(
                                    dash='dot',
                                )
                            )
                        )

                    elif "Current" in Tag_Name:
                        Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                name=str(Name + " - " + Tag_Name),
                                mode='lines+markers',
                            )
                        )

                    else:
                        Data.append(
                            go.Scatter(
                                x=SQL_To_List("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                y=SQL_To_List("SELECT Value FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND json_Tag='" + str(Tag_Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                                name=str(Name + " - " + Tag_Name),
                                mode='lines+markers',
                            )
                        )
            else:
                # Create and style traces
                Data.append(
                    go.Scatter(
                        x=SQL_To_List("SELECT DateTime FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                        y=SQL_To_List("SELECT Value FROM DobbyLog.Log_Trigger WHERE Name='" + str(Name) + "' AND datetime>'" + str(Log_Trigger_Tab_Variables['Slider_Value_Low']) + "' ORDER BY id DESC;"),
                        name=str(Name),
                        mode='lines+markers',
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


# ======================================== System Tab - Callbacks ========================================
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

    return Generate_Variable_String(System_Tab_Variables)


# FIX - Move css to local storage
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


if __name__ == '__main__':
    app.run_server(debug=True,  host='0.0.0.0')
