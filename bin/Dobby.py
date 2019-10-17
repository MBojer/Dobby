#!/usr/bin/python

# ---------- Change log ----------
# See change log

# Email
import smtplib

# MQTT
import paho.mqtt.client as MQTT

# MISC
import datetime
import sys
import time
import random
import os
import json

# FTP
import ftplib
from StringIO import StringIO
# For unique file id
import uuid
import io

# For udp config
import socket

# MySQL
import MySQLdb

# Threding
import threading

# EP Logger
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# For Push Notifications
import requests

# Used to calc uptime
Start_Time = datetime.datetime.now()

# System variables
Version = 102008
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number

# MySQL
MQTT_Topic_Dict = {}

# Used to store config from db
Dobby_Config = {}

# MQTT
MQTT_Client = MQTT.Client(client_id="Dobby", clean_session=True)

MQTT_Client_gBridge = ""

# ---------------------------------------- MISC ----------------------------------------
def Open_db(db=""):
    try:
        db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                             user="dobby",         # your username
                             passwd="HereToServe",  # your password
                             db=db)        # name of the data base
        return db

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return None


def Close_db(conn, cur):
    try:
        conn.commit()
        cur.close()
        conn.close()
        return True

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return None


def Create_db(db_Curser, db_Name):
    try:
        db_Curser.execute("CREATE DATABASE " + db_Name)
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # Error 1007 = db already exists
        if e[0] != 1007:
            print e
            print "CREATE DB ERROR"
            # ADD ME - Something


def Get_System_Config_Value(db_Curser, Target, Header, Name, QuitOnError=True):
    try:
        db_Curser.execute("SELECT Value FROM `Dobby`.`SystemConfig` WHERE Target='" + Target + "' AND Header='" + Header + "' AND Name='" + Name + "'")
        data = db_Curser.fetchone()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if QuitOnError is True:
            print "Error when getting setting fom SystemConfig db. Error: " + str(e)
            print "Unable to continue quitting"
            # FIX - Add error handling
            quit()
        else:
            return ""

    if data is None:
        print "Missing config line in SystemConfig db - Target: " + Target + " - Header: " + Header + " - Name: " + Name
        print "Unable to continue quitting"
        # FIX - Add error handling in stead of quit
        quit()

    return data[0]


# ---------------------------------------- Logging ----------------------------------------
def Log(Log_Level, Log_Source, Log_Header, Log_Text):
    Log_Thread = threading.Thread(target=Write_Log, kwargs={"Log_Level": Log_Level, "Log_Source": Log_Source, "Log_Header": Log_Header, "Log_Text": Log_Text})
    Log_Thread.daemon = True
    Log_Thread.start()


def Write_Log(Log_Level, Log_Source, Log_Header, Log_Text):

    if Log_Level_Check(Log_Source, Log_Level) is False:
        return

    db_Log_Connection = Open_db(Dobby_Config['Log_db'])
    db_Log_Curser = db_Log_Connection.cursor()

    try:
        db_Log_Curser.execute('INSERT INTO `' + Dobby_Config['Log_db'] + '`.`SystemLog` (LogLevel, Source, Header, Text) VALUES("' + Log_Level + '", "' + Log_Source + '", "' + Log_Header + '", "' + Log_Text + '");')
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # 1146 = Table is missing
        if e[0] == 1146:
            try:
                db_Log_Curser.execute("CREATE TABLE `" + Dobby_Config['Log_db'] + "`.`SystemLog` (`id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, `LogLevel` varchar(10) NOT NULL, `Source` varchar(75) NOT NULL, `Header` varchar(75) NOT NULL, `Text` varchar(250) NOT NULL, PRIMARY KEY (`id`))")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    # FIX add some error handling here
                    print "DB WTF ERROR 3: " + str(e)

            # Try to write log again
            db_Log_Curser.execute('INSERT INTO `' + Dobby_Config['Log_db'] + '`.`SystemLog` (LogLevel, Source, Header, Text) VALUES("' + Log_Level + '", "' + Log_Source + '", "' + Log_Header + '", "' + Log_Text + '");')
        else:
            # FIX add some error handling here
            print "DB WTF ERROR 4:" + str(e)
            print "Log_Level: " + str(Log_Level)
            print "Log_Source: " + str(Log_Source)
            print "Log_Header: " + str(Log_Header)
            print "Log_Text: " + str(Log_Text)

    finally:
        db_Log_Curser.execute("SELECT count(*) FROM SystemLog")
        Rows_Number_Of = db_Log_Curser.fetchone()

        if Rows_Number_Of[0] > Dobby_Config['Log_Length_System']:
            Rows_To_Delete = Rows_Number_Of[0] - int(Dobby_Config['Log_Length_System'])
            # Limit the max ammount of rows to delete to 250 to prevent the log from getting cleaned if a lot of log threads is spawned at the same time
            if Rows_To_Delete > 250:
                Rows_To_Delete = 250
            db_Log_Curser.execute("DELETE FROM `" + Dobby_Config['Log_db'] + "`.SystemLog ORDER BY id LIMIT " + str(Rows_To_Delete))
            # Log("Debug", "Dobby", "db", "History Length reached, deleting " + str(Rows_To_Delete) + " rows for Table: SystemLog")

    Close_db(db_Log_Connection, db_Log_Curser)


def Log_Level_Check(Log_Source, Log_Level):

    Log_Level = Log_Level.lower()
    Check_Level = Dobby_Config['Log_Level_System']

    Known_Levels_Dict = {'KeepAliveMonitor': Dobby_Config['Log_Level_KeepAliveMonitor'], 'MQTTConfig': Dobby_Config['Log_Level_MQTT_Config'], 'MQTT Functions': Dobby_Config['Log_Level_MQTT_Functions'], 'MQTT': Dobby_Config['Log_Level_MQTT'], 'Log Trigger': Dobby_Config['Log_Level_Log_Trigger'], 'Mail Trigger': Dobby_Config['Log_Level_Mail_Trigger'], 'Spammer': Dobby_Config['Log_Level_Spammer'], 'APC Monitor': Dobby_Config['Log_Level_APC_Monitor']}

    for Key, Variable in Known_Levels_Dict.iteritems():
        if Log_Source == Key and Variable != "":
            Check_Level = Variable

    if Log_Level in ["debug", "info", "warning", "error", "critical", "fatal"]:
        if Check_Level == "debug":
            return True

    if Log_Level in ["info", "warning", "error", "critical", "fatal"]:
        if Check_Level == "info":
            return True

    if Log_Level in ["warning", "error", "critical", "fatal"]:
        if Check_Level == "warning":
            return True

    if Log_Level in ["error", "critical", "fatal"]:
        if Check_Level == "error":
            return True

    if Log_Level in ["critical", "fatal"]:
        if Check_Level == "critical":
            return True

    if Log_Level in ["fatal"]:
        if Check_Level == "fatal":
            return True

    return False


def Check_db_Length(db_Log_Curser, Log_Table):
    db_Log_Curser.execute("SELECT count(*) FROM " + Log_Table)
    Rows_Number_Of = db_Log_Curser.fetchall()

    if Rows_Number_Of[0][0] > Dobby_Config['Log_Length_System']:
        Rows_To_Delete = Rows_Number_Of[0][0] - Dobby_Config['Log_Length_System']
        db_Log_Curser.execute("DELETE FROM '" + Log_Table + "' ORDER BY 'LastKeepAlive' LIMIT " + str(Rows_To_Delete) + " OFFSET 0")
        Log("Debug", "Dobby", "db", "History Length reached, deleting " + str(Rows_To_Delete) + " rows for Hostname: " + Log_Table)


# ---------------------------------------- Counters ----------------------------------------
class Counters:
    # Refresh rate
    Loop_Delay = 10.000

    def __init__(self):
        # Check if table exists
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        try:
            db_Curser.execute("SELECT id FROM Dobby.Counters LIMIT 1;")
        # Log event
        except (MySQLdb.Error, MySQLdb.Warning):
            Log("Info", "Counters", "Value Calculator", "No entries in 'Counters' table not starting")
            # Close db connection
            Close_db(db_Connection, db_Curser)
            return
        else:
            Log("Info", "Counters", "Value Calculator", "Starting")

        # Close db connection
        Close_db(db_Connection, db_Curser)

        self.Checkers_Dict = {}

        # Start checker thread
        Checkers_Thread = threading.Thread(target=self.Value_Calc, kwargs={})
        Checkers_Thread.daemon = True
        Checkers_Thread.start()

    def Value_Calc(self):
        # Start eternal loop
        while True:
            # Open db connection
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            # Get needed date needed to refresh values
            db_Curser.execute("SELECT Name, `Log Trigger id`, `json Tag`, `Ticks`, `Math` FROM Dobby.Counters")
            Checkers_data = db_Curser.fetchall()

            # Calc values for each counter
            for Counter_Info in Checkers_data:
                # Get last reset id

                try:
                    db_Curser.execute('SELECT id FROM DobbyLog.Log_Trigger_' + str(Counter_Info[1]) + ' where Value="Reset" order by id desc Limit 1;')
                    Last_Reset_ID = db_Curser.fetchall()
                except (MySQLdb.Error, MySQLdb.Warning) as e:
                    Log("Debug", "Counters", "db error", str(e[0]) + ": " + str(e[1]))
                    continue

                if (Last_Reset_ID == ()):
                    Last_Reset_ID = 0
                else:
                    Last_Reset_ID = Last_Reset_ID[0][0]

                # Get values since last reset
                db_Curser.execute('SELECT Value FROM DobbyLog.Log_Trigger_' + str(Counter_Info[1]) + ' where id > "' + str(Last_Reset_ID) + '" order by id desc;')
                db_Data = db_Curser.fetchall()

                Counter_State = 0

                # if db data is empyth set counter to 0
                if db_Data != ():
                    # Get the value before each boot message and add them together to the first value
                    try:
                        if db_Data[0][0] != "Boot":
                            Counter_State = int(db_Data[0][0])
                    except IndexError:
                        # Set Counter_State to 0 if not 
                        pass

                    Add_Next = False

                    for i in range(len(db_Data)):
                        # If Value == "Boot" add next value if not
                        if db_Data[i][0] == 'Boot':
                            Add_Next = True
                        
                        elif Add_Next == True:
                            Counter_State = Counter_State + int(db_Data[i][0])
                            Add_Next = False

                # Check if value has changed and needs to be published
                if Counter_State != int(Counter_Info[3]):
                    Math_Value = 0
                    # Do math
                    if Counter_Info[4] != "":
                        # Set string
                        Math_Value = Counter_Info[4]
                        # Replace value
                        Math_Value = Math_Value.replace("[Value]", str(Counter_State))
                        # Do math
                        Math_Value = eval(Math_Value)
                        # Round value
                        Math_Value = round(Math_Value,2)

                    # Write values to db
                    db_Curser.execute("UPDATE `Dobby`.`Counters` SET `Ticks` = '" + str(Counter_State) + "' WHERE (`Name` = '" + Counter_Info[0] + "');")
                    db_Curser.execute("UPDATE `Dobby`.`Counters` SET `Calculated Value` = '" + str(Math_Value) + "' WHERE (`Name` = '" + Counter_Info[0] + "');")

                    # Publish Values
                    MQTT_Client.publish(Dobby_Config['System_Header'] + '/Counters/Dobby/' + str(Counter_Info[0]) + "/Ticks", payload=Counter_State, qos=0, retain=True)
                    MQTT_Client.publish(Dobby_Config['System_Header'] + '/Counters/Dobby/' + str(Counter_Info[0]), payload=Math_Value, qos=0, retain=True)
            
            # Close db connection
            Close_db(db_Connection, db_Curser)

            # Sleep untill next calc
            time.sleep(self.Loop_Delay)


# ---------------------------------------- MQTT Commands ----------------------------------------
def MQTT_Commands(Topic, Payload):
    Topic = Topic.replace(Dobby_Config['System_Header'] + "/Commands/Dobby/", "")

    Log("Debug", "MQTT Commands", "Request", Topic + " - " + Payload)

    if "Config" in Topic:
        Device_Config(Payload)
        return

    # Rewrite for supervistor
    elif "Power" in Topic:
        # Power_Thread = threading.Thread(target=Power, kwargs={"Payload": Payload})
        # Power_Thread.daemon = True
        # Power_Thread.start()
        return

    # elif "KeepAliveMonitor" in Topic:
    #     MQTT_Commands_KeepAliveMontor(Topic, Payload)
    #     return

    elif Topic in "Test":
        Log("Test", "MQTTCommands", "Executing", Topic + " - " + Payload)
        return

    # elif Topic in "MQTTSQL":
    #     MQTT_SQL(Payload)
    #     return

    Log("Warning", "MQTTCommands", "Request", Topic + " - " + Payload + " - Not found")


# ---------------------------------------- Device Config ----------------------------------------
def Device_Config(Payload):
    if ";" in Payload:
        Payload = Payload.replace(";", "")

    Payload = Payload.split(",")

    Request_Type = "MQTT"

    # Check if UDP config have been requested
    UDP_Request = False

    try:
        if Payload[2]:
            if Payload[2] == "FTP":
                Request_Type = "FTP"
            elif Payload[2] == "UDP":
                Request_Type = "UDP"
                UDP_Request = True
            else:
                Log("Warning", "MQTT Config", "Request", "Unknown request type:" + Request_Type)
                return
    except ValueError or IndexError:
        pass

    db_FSCJ_Connection = Open_db("Dobby")
    db_FSCJ_Curser = db_FSCJ_Connection.cursor()

    Log("Info", "MQTT Config", "Request", Payload[0])

    # Get device's "config id" from db
    try:
        db_FSCJ_Curser.execute("SELECT Config_ID FROM Dobby.DeviceConfig WHERE Hostname='" + Payload[0] + "';")
        Config_ID_Value = db_FSCJ_Curser.fetchone()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "MQTT Config", "Missing", Payload[0])
        else:
            Log("Error", "MQTT Config", "db error", str(e[0]))
            Close_db(db_FSCJ_Connection, db_FSCJ_Curser)
            return

    # Check config id agents current and return if =
    if Config_ID_Value[0] == int(Payload[1]):
        if UDP_Request is True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto("OK".encode('utf-8'), (Payload[3], 8888))
            sock.close()
            return
        else:
            Log("Debug", "MQTT Config", "Config up to date", Payload[0] + " id: " + Payload[1])
            return

    # Get config
    try:
        db_FSCJ_Curser.execute("SELECT DISTINCT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='DeviceConfig';")
        Config_Name_List = db_FSCJ_Curser.fetchall()

        db_FSCJ_Curser.execute("SELECT * FROM DeviceConfig WHERE Hostname='" + Payload[0] + "';")
        Config_Value_List = db_FSCJ_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "MQTT Config", "Missing", Payload[0])
        else:
            Log("Error", "MQTT Config", "db error", str(e[0]))
            Close_db(db_FSCJ_Connection, db_FSCJ_Curser)
            return

    Close_db(db_FSCJ_Connection, db_FSCJ_Curser)

    # Compare ConfigID
    if Config_Name_List is None:
        Log("Warning", "MQTT Config", "Missing", "ConfigID for Hostname: " + Payload[0])

    Log("Debug", "MQTT Config", "Config outdated", Payload[0] + " Device Config ID: " + Payload[1] + " Config ID: " + str(Config_ID_Value[0]))

    if Config_Name_List is () or Config_Value_List is ():
        Log("Error", "MQTT Config", "Config Empthy", Payload[0])
        return

    # Create json config
    Config_Dict = {}
    Interation = 0
    for x in Config_Name_List:
        if str(x[0]) != "id" and str(x[0]) != "Config_Active" and str(x[0]) != "Last_Modified" and Config_Value_List[0][Interation] is not None:
            Config_Dict[str(x[0])] = str(Config_Value_List[0][Interation])
        Interation = Interation + 1

    # Check if MQTT or UDP
    # MQTT Request
    if Request_Type == "MQTT":
        Log("Info", "MQTT Config", "Publish Config", Payload[0])
        # Publish json
        MQTT_Client.publish(Dobby_Config['System_Header'] + "/Config/" + Payload[0], payload=json.dumps(Config_Dict) + ";", qos=0, retain=False)
        return

    # UDP Request
    elif Request_Type == "UPD":
        Log("Info", "UDPConfig", "Publish Config", Payload[0] + " - IP: " + Payload[3])

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(Config_Dict).encode('utf-8'), (Payload[3], 8888))
        sock.close()

    # FTP Request
    elif Request_Type == "FTP":
        Log("Info", "FTPConfig", "Upload Config", Payload[0] + " - IP: " + Payload[3])

        # Generate unique config id
        Config_File_Name = "/var/tmp/Dobby/" + str(Payload[0])

        # Check if temp dir exists
        if not os.path.exists("/var/tmp/Dobby/"):
            os.makedirs("/var/tmp/Dobby/")

        # Write json to file
        # NOTE - Cant get "with open" to work for some odd reason
        Config_File = open("%s.json" % Config_File_Name, "w")
        json.dump(Config_Dict, Config_File)
        Config_File.flush
        Config_File.close

        # Upload file
        # FIX - Change user and pass
        FTP_Connection = ftplib.FTP(Payload[3],'dobby','heretoserve')

        # Open and read file to send
        with open(Config_File_Name + ".json", 'r') as Config_File:
            FTP_Connection.storbinary('STOR Dobby.json', open(Config_File_Name + ".json", 'rb'))

        # close file and FTP
        FTP_Connection.quit()

        # Not deleting file so the last generated config is saved, uncomment below to delete file
        # os.remove(Config_File_Name)

        # 2 sec delay so the device can reconnect after ftp upload
        time.sleep(2.500)

        # Send reboot command to device
        MQTT_Client.publish(Dobby_Config['System_Header'] + "/Commands/" + str(Payload[0]) + "/Power", payload="Reboot;", qos=0, retain=False)


# ---------------------------------------- MISC ----------------------------------------
def Is_json(myjson):
    # A single entry is not consider a json sitring
    if "{" not in myjson:
        return False

    try:
        myjson = json.loads(myjson)
    except ValueError, e:
        myjson = e
        return False

    return True






# ---------------------------------------- Log Trigger ----------------------------------------
class Log_Trigger():
    
    # How often the db is cheched for changes
    Refresh_Rate = 5

    def __init__(self):
        # Log event
        Log("Info", "Log Trigger", "System", "Initializing")

        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT id, Name, Tags, Max_Entries, Topic FROM Dobby.Log_Trigger WHERE Enabled='1'")
        Log_Trigger_db = db_Curser.fetchall()

        for i in range(len(Log_Trigger_db)):
            # id =            0
            # Name =          1
            # Tags =          2
            # Max_Entries =   3
            # Topic =         4

            # Log Event
            Log("Debug", "Log Trigger", Log_Trigger_db[i][1], "Subscribing to: '" + Log_Trigger_db[i][4] + "'")
            # Add topic to topic tict
            MQTT_Add_Sub_Topic(str(Log_Trigger_db[i][4]), 'Log Trigger', {'id': Log_Trigger_db[i][0], 'Name': Log_Trigger_db[i][1], 'Tags': Log_Trigger_db[i][2], 'Max_Entries': Log_Trigger_db[i][3]})
            # Subscribe
            MQTT_Client.subscribe(str(Log_Trigger_db[i][4]))
            # Register callbacks
            MQTT_Client.message_callback_add(str(Log_Trigger_db[i][4]), MQTT_On_Message_Callback)

        Close_db(db_Connection, db_Curser)

    @classmethod
    def On_Message(cls, Trigger_Info, Payload, Retained):

        # Log only none retained messages
        if Retained is 0:
            # json value
            if Is_json(Payload) is True:
                # Create json
                root = json.loads(Payload)
                # Split headers into seperate topics
                for json_Log_Source, json_Log_Value in root.items():
                    Log_Trigger.Write_Value_To_db(Trigger_Info, json_Log_Value, json_Tag=json_Log_Source)
                    # None json value
            else:
                Log_Trigger.Write_Value_To_db(Trigger_Info, Payload)


    @classmethod
    def Write_Value_To_db(cls, Trigger_Info, Value, json_Tag=''):

        Log("Debug", "Log Trigger", "Logging", "Value: " + str(Value) + " json_Tag: " + str(json_Tag))

        db_Connection = Open_db()
        db_Curser = db_Connection.cursor()

        db_Curser.execute("set autocommit = 1")

        # Make sure Log_Value is string
        Value = str(Value)
        # Remove the ";" at the end if there
        if Value[-1:] == ";":
            Value = Value[:-1]

        SQL_Table_Name = Dobby_Config['Log_db'] + "`.`Log_Trigger_"  + str(Trigger_Info['id'])
        SQL_String = "INSERT INTO `" + SQL_Table_Name + "` (json_Tag, Value) Values('" + str(json_Tag) + "' , '" + Value + "');"
        
        # Log Value
        try:
            db_Curser.execute(SQL_String)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            # Table missing, create it
            if e[0] == 1146:
                Log("Info", "Log Trigger", "db table missing", "Creating: " + SQL_Table_Name)
                try:
                    # To create table
                    db_Curser.execute("CREATE TABLE `" + SQL_Table_Name + "` (`id` int(11) NOT NULL AUTO_INCREMENT, `json_Tag` varchar(75) NOT NULL, `Value` varchar(75) NOT NULL, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`))ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;")
                    # Try logging the message again
                    db_Curser.execute(SQL_String)

                except (MySQLdb.Error, MySQLdb.Warning) as e:
                    # Error 1050 = Table already exists
                    if e[0] != 1050:
                        Log("Fatal", "Log Trigger", Trigger_Info['Name'], "Unable to create log db table, failed with error: " + str(e))
                        return
            else:
                Log("Critical", "Log Trigger", "db", "Unable to log message. Error: " + str(e))
                return

        # Delete rows > max
        db_Curser.execute("SELECT count(*) FROM `" + SQL_Table_Name + "`;")
        Rows_Number_Of = db_Curser.fetchone()

        if Rows_Number_Of[0] > int(Trigger_Info['Max_Entries']):
            Rows_To_Delete = Rows_Number_Of[0] - int(Trigger_Info['Max_Entries'])
            
            db_Curser.execute("DELETE FROM `" + SQL_Table_Name + "` ORDER BY 'id' LIMIT " + str(Rows_To_Delete) + ";")
            
            Log("Debug", "Dobby", Trigger_Info['Name'], "History Length reached, deleting " + str(Rows_To_Delete))

        # Change Last_Trigger
        db_Curser.execute("UPDATE `Dobby`.`Log_Trigger` SET `Last_Trigger`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(Trigger_Info['id']) + "';")

        # Log event
        Log("Debug", "Log Trigger", Trigger_Info['Name'], "Valure capured: " + Value)

        Close_db(db_Connection, db_Curser)
















# ---------------------------------------- Action Trigger ----------------------------------------
class Action_Trigger():
    # How often the db is cheched for changes
    Refresh_Rate = 5

    Active_Triggers = {}
    Trigger_Timeouts = {}
    MQTT_Target_Checks = {}

    def __init__(self):
        # Log event
        Log("Info", "Action Trigger", "Checker", "Initializing")

        # Start checker thread
        File_Change_Checker_Thread = threading.Thread(target=self.Checker, kwargs={})
        File_Change_Checker_Thread.daemon = True
        File_Change_Checker_Thread.start()

    def Checker(self):
        # Start eternal loop
        while True:
            # Open db connection get id, Last Modified
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            # Get id and Last Modified to check if Action Triggers needs to be started
            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.`Action_Trigger` WHERE Enabled=1;")
            Action_Info = db_Curser.fetchall()

            # Close db connection
            Close_db(db_Connection, db_Curser)

            for i in range(len(Action_Info)):
                # Action_Info[i][0] - id
                # Action_Info[i][1] - Last Modified

                # Check if the trigger is in the Active_Triggers dict
                if Action_Info[i][0] in self.Active_Triggers:
                    
                    # Check if last modified changed
                    if self.Active_Triggers[Action_Info[i][0]] != Action_Info[i][1]:
                        self.Active_Triggers[Action_Info[i][0]] = Action_Info[i][1]
                        self.Restart_Trigger(Action_Info[i][0])
                        
                # If not add then to the list and start the trigger
                else:
                    self.Active_Triggers[Action_Info[i][0]] = Action_Info[i][1]
                    # Start the trigger
                    self.Start_Trigger(Action_Info[i][0])

            # Sleep till next check
            time.sleep(self.Refresh_Rate)
    

    def Start_Trigger(self, id):

        Trigger_Info = self.Get_Trigger_Info(id)
        # Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT Name, `MQTT Target` FROM Dobby.`Action_Trigger` WHERE id="+ str(id) + ";")
        Trigger_Info = db_Curser.fetchone()
        # Trigger_Info[0] - Name
        # Trigger_Info[1] - Target

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Log Event
        Log("Debug", "Action Trigger", str(Trigger_Info[0]), "Starting")
        Log("Debug", "Action Trigger", str(Trigger_Info[0]), "Subscribing to: '" + str(Trigger_Info[1]) + "'")
        # Add topic to topic tict
        MQTT_Add_Sub_Topic(str(Trigger_Info[1]), 'Action Trigger', id)
        # Subscribe
        MQTT_Client.subscribe(str(Trigger_Info[1]))
        # Register callbacks
        MQTT_Client.message_callback_add(str(Trigger_Info[1]), MQTT_On_Message_Callback)

        # Create Timeout Trigger
        self.Trigger_Timeouts[id] = Timeout_Trigger()

        print "CREATE target trigger here if timeout_set is set"


    def Stop_Trigger(self, id):

        Trigger_Info = self.Get_Trigger_Info(id)

         # Log Event
        Log("Debug", "Action Trigger", str(Trigger_Info[0]), "Stopping")
        Log("Debug", "Action Trigger", str(Trigger_Info[0]), "Unsubscribing from: '" + str(Trigger_Info[1]) + "'")

        MQTT_Del_Sub_Topic(Trigger_Info[1], 'Action Trigger', id)


    def Restart_Trigger(self, id):
        self.Start_Trigger(id)
        self.Stop_Trigger(id)


    def Get_Trigger_Info(self, id):
        # Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT Name, `MQTT Target` FROM Dobby.`Action_Trigger` WHERE id="+ str(id) + ";")
        Trigger_Info = db_Curser.fetchone()
        # Trigger_Info[0] - Name
        # Trigger_Info[1] - Target

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Return info
        return Trigger_Info

    @classmethod
    def On_Message(cls, id, Topic, Payload):

        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("set autocommit = 1")

        db_Curser.execute("SELECT Name, `Alert State`, `MQTT Payload Clear`, `MQTT Payload Trigger`, `Alert Target`, `Alert Payload Clear`, `Alert Payload Trigger`, Timeout, `Timeout Alert Target` FROM Dobby.Action_Trigger WHERE id=" + str(id) + ";")
        Trigger_Info = db_Curser.fetchone()

        Name = Trigger_Info[0]
        Alert_State = Trigger_Info[1]
        MQTT_Payload_Clear = Trigger_Info[2]
        MQTT_Payload_Trigger = Trigger_Info[3]
        Alert_Target = Trigger_Info[4]
        Alert_Payload_Clear = Trigger_Info[5]
        Alert_Payload_Trigger = Trigger_Info[6]
        Timeout_Sec =  Trigger_Info[7]
        Timeout_Alert_Target =  Trigger_Info[8]


        # Find out what to do
        Action = 2
        # 0 = Clear
        # 1 = Trigger
        # 2 = In-between

        Trigger_Change = False

        if float(MQTT_Payload_Clear) == float(MQTT_Payload_Trigger):
            Log("Error", "Action Trigger", str(Name), 'Clear and Trigger payload is the same value')
            Close_db(db_Connection, db_Curser)
            return

        # High / Low Check
        # Value moving from Low to High
        elif (float(MQTT_Payload_Clear) <= float(MQTT_Payload_Trigger)) is True:
            # Clear check
            if float(MQTT_Payload_Clear) >= float(Payload):
                Action = 0

            # Trigger check
            elif float(MQTT_Payload_Trigger) <= float(Payload):
                Action = 1

        # Value moving from High to Low
        else:
            # Clear check
            if float(MQTT_Payload_Clear) <= float(Payload):
                Action = 0

            # Trigger check
            elif float(MQTT_Payload_Trigger) >= float(Payload):
                Action = 1

        # Clear
        if Action == 0:
            # Check agains current alert state
            if Action == Alert_State:
                Log("Debug", "Action Trigger", str(Name), 'Already cleared ignoring new clear value: ' + str(Payload))
 
            else:
                Trigger_Change = True
                # Publish Message
                MQTT_Client.publish(Alert_Target, payload=str(Alert_Payload_Clear) + ";", qos=0, retain=False)
                Log("Info", "Action Trigger", str(Name), 'Cleared at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Clear))

        # Trigger
        elif Action == 1:
            # Check agains current alert state
            if Action == Alert_State:
                Log("Debug", "Action Trigger", str(Name), 'Already triggered ignoring new trigger value: ' + str(Payload))
            else:
                Trigger_Change = True
                # Publish Message
                MQTT_Client.publish(Alert_Target, payload=str(Alert_Payload_Trigger) + ";", qos=0, retain=False)
                Log("Info", "Action Trigger", str(Name), 'Triggered at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Trigger))

        # In-between value
        elif Action == 2:
            Log("Debug", "Action Trigger", str(Name), 'In-between value received: ' + str(Payload))

        if Trigger_Change is True:
            # Change Alert_State
            db_Curser.execute("UPDATE `Dobby`.`Action_Trigger` SET `Alert State`='" + str(Action) + "' WHERE `id`='" + str(id) + "';")
            # Update Triggered_DateTime
            db_Curser.execute("UPDATE `Dobby`.`Action_Trigger` SET `Triggered DateTime`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(id) + "';")

        # Close the db connection
        Close_db(db_Connection, db_Curser)

        
        # if Timeout_Sec is not None:
        #     # Start trigger timeout
        #     Action_Trigger.Trigger_Timeouts[id].Reset(Timeout_Sec, Timeout_Alert_Target)
            
            # If timeout is set the Target will be checked for state as well
            # the check is done at 2/3 of timepout to assure reply from target can time out
            # Action_Trigger.MQTT_Target_Checks[id].Reset(Timeout_Sec, Topic)
            
            #     MQTT_Target_Check(Topic, Action)
            
            # print 'Timeout_Sec' 
            # print Timeout_Sec




# ---------------------------------------- Timeout Trigger ----------------------------------------
def Send_Alert(id, Value=None, Subject=None, Text=None):

    # Get Alert into
    ## Open db connection
    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    db_Curser.execute("SELECT Name, `Mail Target`, `MQTT Target`, `Push Target` FROM Dobby.`Alert_Targets` WHERE id=" + str(id) + ";")
    Alert_Info = db_Curser.fetchone()

    ## Only get subject text if none is set
    if Subject is None:
        db_Curser.execute("SELECT Subject FROM Dobby.`Alert_Targets` WHERE id=" + str(id) + ";")
        Subject = db_Curser.fetchone()
        Subject = Subject[0]
    if Text is None:
        db_Curser.execute("SELECT Text FROM Dobby.`Alert_Targets` WHERE id=" + str(id) + ";")
        Text = db_Curser.fetchone()
        Text = Text[0]

    ## Close db connection
    Close_db(db_Connection, db_Curser)

    Alert_Name = Alert_Info[0]
    Mail_Target = Alert_Info[1]
    MQTT_Target = Alert_Info[2]
    Push_Target = Alert_Info[3]

    print "Mail_Target"
    print Mail_Target
    print type(Mail_Target)
    print "MQTT_Target"
    print MQTT_Target
    print type(MQTT_Target)
    print "Push_Target"
    print Push_Target
    print type(Push_Target)

    # Add value to Text if value is set
    if Value is not None and Value != "":
        Text = Text.replace('*value*', str(Value))


    # Mail Alerts
    if Mail_Target is not None and Mail_Target != "":
        Send_Mail(Mail_Target, Subject, Text)


    # MQTT Messages
    if MQTT_Target is not None and MQTT_Target != "":
        # Remove any spaces
        MQTT_Target = MQTT_Target.replace(" ", "")

        Target_List = []

        # Multiple targets
        if "," in MQTT_Target:
            Target_List = MQTT_Target.split(",")

        # Single target
        else:
            Target_List.append(MQTT_Target)

        # Publish MQTT Message 
        for Target_Topic in Target_List:
            # Publish message
            MQTT_Client.publish(Target_Topic, payload=Text, qos=0, retain=False)
            # Log event
            Log("Debug", "System", "MQTT", 'Publish - Topic: ' + str(Target_Topic) + " Payload: " + str(Text))
            

    if Push_Target is not None and Push_Target != "":
        print "Push_Target"
        print Push_Target
        Send_Push(Push_Target, Subject, Text)


# ---------------------------------------- Timeout Trigger ----------------------------------------
class Timeout_Trigger():

    Check_Delay = 0.500
    
    def __init__(self):
        # Log event
        Log("Debug", "System", "Timeout Trigger", "Initializing")

        # Create vars
        self.Timeout_At = datetime.datetime.now()
        self.Alert_Target_id = ""
        self.Delete_Me = False
        self.Triggered = True

        # Start timeout
        Timer_Thread = threading.Thread(target=self.Run)
        Timer_Thread.daemon = True
        Timer_Thread.start()

    def Reset(self, Timeout, Alert_Target_id):
        # Log event
        Log("Debug", "System", "Timeout Trigger", "Reset alert id: " + str(Alert_Target_id))
        
        # Save vars
        self.Alert_Target_id = Alert_Target_id
        ## Add timeout to current time to get Timeout_At
        self.Timeout_At = datetime.datetime.now() + datetime.timedelta(seconds=Timeout)
        ## Alert id
        self.Alert_Target_id = Alert_Target_id

        # Reset triggered
        self.Triggered = False
        

    def Delete(self):
        Log("Debug", "System", "Timeout Trigger", "Deleted alert id: " + str(self.Alert_Target_id))
        # Mark thread for deletions
        self.Delete_Me = True


    def Trigger_Timeout(self):
        if self.Triggered == True:
            return
        
        # Set var to prevent retrigger
        self.Triggered = True

        # Log event
        Log("Debug", "System", "Timeout Trigger", "Triggered alert id:" + str(self.Alert_Target_id))
        
        # Get alert information from db        
        ## Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()
        # Set autocommit so no delay on saving changes
        db_Curser.execute("set autocommit = 1")

        ## Get id and Last Modified to check if gBridge Triggers needs to be started
        db_Curser.execute("SELECT `Mail Target`, `MQTT Target`, `Push Target`, Subject, Body FROM Dobby.`Alert_Targets` WHERE id=" + str(self.Alert_Target_id) + ";")
        Alert_Info = db_Curser.fetchone()

        # Change Last_Trigger
        db_Curser.execute("UPDATE `Dobby`.`Alert_Targets` SET `Last_Trigger`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(id) + "';")

        ## Close db connection
        Close_db(db_Connection, db_Curser)

        # Send Alerts
        ## 0 = Mail Target
        ## 1 = MQTT Target
        ## 2 = Push Target
        ## 3 = Subject
        ## 4 = Body
        print "fix timout trigger"
        # Send_Alert(Alert_Info[3], Alert_Info[4], None, Alert_Info[0], Alert_Info[1], Alert_Info[2])


    def Run(self):
        # Just sleep untill id is set
        while self.Alert_Target_id == "" and self.Delete_Me == False:
            # Sleep untill next check
            time.sleep(self.Check_Delay)

        # When id is set start the timeout
        while self.Delete_Me == False:
 
            # Check if current time vs timeout at time
            if self.Timeout_At < datetime.datetime.now():
                self.Trigger_Timeout()

            # Sleep untill next check
            time.sleep(self.Check_Delay)


# ---------------------------------------- gBridge Trigger ----------------------------------------
# From local to gBridge
def gBridge_Trigger_Local(id, Topic, Payload):

    # Ignore "/set" messages to avoid message loops
    if "/set" in Topic:
        return

    MQTT_Client_gBridge.Publish_Reply(id, Topic, Payload)



# Form gBridge to local
class gBridge_Trigger():
    # How often the db is cheched for changes
    Refresh_Rate = 5

    Active_Triggers = {}

    # Create a MQTT client to connect to gBridge
    MQTT_Client = MQTT.Client(client_id="Dobby", clean_session=True)

    MQTT_Client_Connected = False

    MQTT_Broker = ""
    MQTT_Base_Topic = ""

    def Publish_Reply(self, id, Topic, Payload):
        
        Payload.replace(";", "")

        # Temperature
        if Topic.endswith("/Humidity"):
            # Round Payload to nearest 0.5 to make google understand
            Payload = round(float(Payload)*2)/2
            self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/tempset-humidity/set", payload=str(Payload), qos=0, retain=False)
        
        # Humidity
        elif Topic.endswith("/Temperature"):
            # Round Payload to nearest 0.5 to make google understand
            Payload = round(float(Payload)*2)/2
            self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/tempset-ambient/set", payload=str(Payload), qos=0, retain=False)
        
        # DS18B20
        elif "/DS18B20/" in Topic:
            # Round Payload to nearest 0.5 to make google understand
            Payload = round(float(Payload)*2)/2
            self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/tempset-ambient/set", payload=str(Payload), qos=0, retain=False)
        
        else:
            if str(Payload) == "0":
                # On Off
                self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/onoff/set", payload="0", qos=0, retain=False)
                # Brightness
                self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/brightness/set", payload="0", qos=0, retain=False)
            else:
                # On Off
                self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/onoff/set", payload="1", qos=0, retain=False)
                # Brightness
                self.MQTT_Client.publish(self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/brightness/set", payload=str(Payload), qos=0, retain=False)

    

    def __init__(self):
        # Log event
        Log("Info", "gBridge Trigger", "Checker", "Initializing")

        # Open db connection get id, Last Modified
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        MQTT_User = Get_System_Config_Value(db_Curser, "gBridge_Trigger", "MQTT", "Username", False)
        MQTT_Pass = Get_System_Config_Value(db_Curser, "gBridge_Trigger", "MQTT", "Password", False)
        self.MQTT_Broker = Get_System_Config_Value(db_Curser, "gBridge_Trigger", "MQTT", "Broker", False)
        MQTT_Port = Get_System_Config_Value(db_Curser, "gBridge_Trigger", "MQTT", "Port", False)
        self.MQTT_Base_Topic = Get_System_Config_Value(db_Curser, "gBridge_Trigger", "MQTT", "Base Topic", False)

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Setup the MQTT client for gBridge
        # User / Pass
        self.MQTT_Client.username_pw_set(MQTT_User, MQTT_Pass)
        
        # Enable SSL
        self.MQTT_Client.tls_set_context(context=None)

        # FIX - ADD MQTT Logging
        # self.MQTT_Client.on_log = MQTT_On_Log

        # Callbacks
        self.MQTT_Client.on_connect = self.MQTT_On_Connect
        self.MQTT_Client.on_disconnect = self.MQTT_On_Disconnect

        # Connect to broker
        self.MQTT_Client.connect(self.MQTT_Broker, port=MQTT_Port, keepalive=60, bind_address="")

        # Spawn thread for MQTT Client Loop
        MQTTC_Thread = threading.Thread(target=self.MQTT_Client_Loop)
        MQTTC_Thread.daemon = True
        MQTTC_Thread.start()

        # Start checker thread
        File_Change_Checker_Thread = threading.Thread(target=self.Checker, kwargs={})
        File_Change_Checker_Thread.daemon = True
        File_Change_Checker_Thread.start()


    def MQTT_Subscribe_To(self, MQTT_Client, Topic):
        Log("Debug", "gBridge Trigger", "MQTT", "Subscribing to topic: " + Topic)
        self.MQTT_Client.subscribe(Topic)


    def MQTT_On_Disconnect(self, MQTT_Client, userdata, rc):
        self.MQTT_Client.Connected = False
        Log("Warning", "gBridge", "MQTT", "Disconnected from broker : " + str(self.MQTT_Broker) + " with result code " + str(rc))


    def MQTT_On_Connect(self, MQTT_Client, userdata, flags, rc):

        self.MQTT_Client.Connected = True
        Log("Info", "gBridge Trigger", "MQTT", "Connected to broker " + str(self.MQTT_Broker) + " with result code " + str(rc))

        # # Restart trigger to resubscribe and register callbacks
        # for id in dict(self.Active_Triggers).keys():
        #     self.Restart_Trigger(id)
    
    # ---------------------------------------- # On message callbacks - Spawns threads ----------------------------------------
    def MQTT_On_Message_Callback(self, mosq, obj, msg):
 
        Message_Thread = threading.Thread(target=self.MQTT_On_Message, kwargs={"Topic": msg.topic, "Payload": msg.payload, "Retained": msg.retain})
        Message_Thread.daemon = True
        Message_Thread.start()
        return

    # ---------------------------------------- MQTT On Message ----------------------------------------
    def MQTT_On_Message(self, Topic, Payload, Retained):

        # Ignore "/set" messages to avoid message loops
        if "/set" in Topic:
            return

        # Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()
        db_Curser.execute("set autocommit = 1")

        gBridge_id = Topic.replace(self.MQTT_Base_Topic, "")
        gBridge_id = gBridge_id.split("/")
        gBridge_id = gBridge_id[0]

        # Get trigger id
        db_Curser.execute('SELECT id FROM Dobby.`gBridge_Trigger` WHERE `gBridge id`="' + str(gBridge_id) + '";')
        id = db_Curser.fetchone()
        id = id[0]

        # Change Last_Trigger
        db_Curser.execute("UPDATE `Dobby`.`gBridge_Trigger` SET `Triggered DateTime`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(id) + "';")

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Check what kind of message it is
        if "/onoff" in Topic:
            # If its a Dimmer, is 1 set value to 75% to get some light
            if "/Dimmer/" in self.Active_Triggers[id]["MQTT Target"]:
                if Payload == "1":
                    Payload = 75
        
        # Nothing to do here yet
        elif "/brightness" in Topic:
            pass

        elif "/tempset-mode" in Topic:
            print "tempset-mode"
        elif "/tempset-setpoint" in Topic:
            print "tempset-setpoint"
        elif "/tempset-ambient" in Topic:
            print "tempset-ambient"
        elif "/tempset-humidity" in Topic:
            print "tempset-humidity"

        else:
            print "UNKNOWN Command type"

        # Publish Message
        MQTT_Client.publish(self.Active_Triggers[id]["MQTT Target"], payload=str(Payload) + ";", qos=0, retain=False)
        

    def MQTT_Client_Loop(self):
        # Start MQTT Loop
        self.MQTT_Client.loop_forever()


    def Checker(self):
        # Start eternal loop
        while True:
            # Open db connection get id, Last Modified
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            # Get id and Last Modified to check if gBridge Triggers needs to be started
            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.`gBridge_Trigger` WHERE Enabled=1;")

            gBridge_Info = db_Curser.fetchall()
            
            # Close db connection
            Close_db(db_Connection, db_Curser)

            for i in range(len(gBridge_Info)):
                id = gBridge_Info[i][0]
                Last_Modified = gBridge_Info[i][1]

                # Check if the trigger is in the Active_Triggers dict
                if id in self.Active_Triggers:
                    
                    # Check if last modified changed
                    if self.Active_Triggers[id]["Last_Modified"] != Last_Modified:
                        # Deleting the trigger now and then i will get readded in next run, little delay between sub and unsub
                        self.Delete_Trigger(id)
                        
                # If not then add to the list and start the trigger
                else:
                    # Save trigger info
                    self.Add_Trigger(id)
                    # Start the trigger
                    self.Start_Trigger(id)

            # Sleep till next check
            time.sleep(self.Refresh_Rate)
    

    def Add_Trigger(self, id):

        # Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        # Get Name, gBridge id, MQTT Target, Last_Modified
        db_Curser.execute("SELECT Name, `gBridge id`, `MQTT Target`, Last_Modified FROM Dobby.`gBridge_Trigger` WHERE id=" + str(id) + ";")
        gBridge_Info = db_Curser.fetchone()
        
        # Close db connection
        Close_db(db_Connection, db_Curser)

        self.Active_Triggers[id] = {"Name": gBridge_Info[0], "gBridge id": gBridge_Info[1], "MQTT Target": gBridge_Info[2], "Last_Modified": gBridge_Info[3]}


    def Delete_Trigger(self, id):
        # Stop the trigger before deliting
        self.Stop_Trigger(id)

        # Remove triggre from Active_Triggers
        try:
            del self.Active_Triggers[id]
        except KeyError:
            pass


    def Start_Trigger(self, id):

        # Build source topic from base and gbridge id
        Source_Topic = self.MQTT_Base_Topic + self.Active_Triggers[id]["gBridge id"] + "/#"
        
        # Log Event
        Log("Debug", "gBridge Trigger", str(self.Active_Triggers[id]["Name"]), "Starting")
        Log("Debug", "gBridge Trigger", str(self.Active_Triggers[id]["Name"]), "Subscribing to: '" + str(Source_Topic) + "'")
        # Subscribe
        self.MQTT_Client.subscribe(str(Source_Topic))
        # Register callbacks
        self.MQTT_Client.message_callback_add(str(Source_Topic), self.MQTT_On_Message_Callback)

        # Subscribe - local
        Sub_Topic = str(self.Active_Triggers[id]["MQTT Target"])
        # Temp and humidity
        if "Temperature" in self.Active_Triggers[id]["MQTT Target"]:
            # Do nothing to target topic
            pass
        elif "Humidity" in self.Active_Triggers[id]["MQTT Target"]:
            # Do nothing to target topic
            pass

        # Dont add state if alread there
        elif Sub_Topic.endswith("/State"):
            pass

        # Anything else
        # Remember to add "/State" to get the devices state and not create a message loop
        else:
            Sub_Topic = Sub_Topic + "/State"

        # Add topic to topic tict
        MQTT_Add_Sub_Topic(Sub_Topic, 'gBridge Trigger', id)
        # Subscribe
        MQTT_Client.subscribe(Sub_Topic)
        # Register callbacks
        MQTT_Client.message_callback_add(Sub_Topic, MQTT_On_Message_Callback)


    def Stop_Trigger(self, id):
        # Build source topic from base and gbridge id
        Source_Topic = self.MQTT_Base_Topic + self.Active_Triggers[id][1] + "/#"

         # Log Event
        Log("Debug", "gBridge Trigger", str(id), "Stopping")
        Log("Debug", "gBridge Trigger", str(id), "Unsubscribing from: '" + str(Source_Topic) + "'")

        # Unsubscribe and remove callback
        self.MQTT_Client.unsubscribe(Source_Topic)
        self.MQTT_Client.message_callback_remove(Source_Topic)

        # Unsubscribe and remove callback - local
        MQTT_Del_Sub_Topic(str(self.Active_Triggers[id]["MQTT Target"]), 'Mail Trigger', id)



# ---------------------------------------- KeepAlive Monitor ----------------------------------------
def KeepAlive_Monitor(Topic, Payload):
    db_KL_Connection = Open_db(Dobby_Config['Log_db'])
    db_KL_Curser = db_KL_Connection.cursor()

    try:
        root_KL = json.loads(Payload)
    except ValueError:
        Log("Warning", "KeepAliveMonitor", "KeepAlive", "From unknown device")
        Log("Debug", "KeepAliveMonitor", "KeepAlive", "From unknown device - Topic: " + Topic + " Payload: " + Payload)
        return

    Log("Debug", "KeepAliveMonitor", "KeepAlive", " From: " + root_KL["Hostname"])

    if "IP" not in root_KL:
        if root_KL["Hostname"] is "Dobby":
            root_KL["IP"] = "127.0.0.1"
        else:
            root_KL["IP"] = "0.0.0.0"

    if "RSSI" not in root_KL:
        root_KL["RSSI"] = "0"

    # if root_KL["Hostname"] != "Dobby":
    #     # Spawn thread for Auto Update Check
    #     AU_Thread = threading.Thread(target=Auto_Update, kwargs={"Hostname": root_KL["Hostname"], "IP": root_KL["IP"], "Current_SW": root_KL["Software"]})
    #     AU_Thread.daemon = True
    #     AU_Thread.start()

    # Try writing message to log
    try:
        db_KL_Curser.execute("INSERT INTO `KeepAliveMonitor` (Device, UpFor, FreeMemory, SoftwareVersion, IP, RSSI) VALUES('" + root_KL["Hostname"] + "', '" + str(root_KL["Uptime"]) + "', '" + str(root_KL["FreeMemory"]) + "', '" + str(root_KL["Software"]) + "', '" + str(root_KL["IP"]) + "', '" + str(root_KL["RSSI"]) + "');")
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # Table missing, create it
        if e[0] == 1146:
            Log("Debug", "KeepAliveMonitor", "db", "Log table missing, creating it")
            try:
                db_KL_Curser.execute("CREATE TABLE `KeepAliveMonitor` (`id` INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL, `Device` VARCHAR(25) NOT NULL, `LastKeepAlive` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL, `UpFor` int(11) unsigned NOT NULL, `FreeMemory` DECIMAL(13,0) NOT NULL, `SoftwareVersion` int(6) NOT NULL, `IP` VARCHAR(16) NOT NULL, `RSSI` INT(5) NOT NULL);")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    # FIX add some error handling here
                    Log("Error", "KeepAliveMonitor", "db", "Error: " + str(e[0]))
                    Close_db(db_KL_Connection, db_KL_Curser)
                    return

        # Try to write log again
        db_KL_Curser.execute("INSERT INTO `KeepAliveMonitor` (Device, UpFor, FreeMemory, SoftwareVersion, IP, RSSI) VALUES('" + root_KL["Hostname"] + "', '" + str(root_KL["Uptime"]) + "', '" + str(root_KL["FreeMemory"]) + "', '" + str(root_KL["Software"]) + "', '" + str(root_KL["IP"]) + "', '" + str(root_KL["RSSI"]) + "');")

    # Check log length
    db_KL_Curser.execute("SELECT COUNT(*) FROM `" + Dobby_Config['Log_db'] + "`.`KeepAliveMonitor` WHERE Device='" + root_KL["Hostname"] + "';")
    Current_Log_Length = db_KL_Curser.fetchone()

    if Current_Log_Length[0] > Dobby_Config['Log_Length_KeepAliveMonitor']:
        Rows_To_Delete = Current_Log_Length[0] - Dobby_Config['Log_Length_KeepAliveMonitor']
        Log("Debug", "KeepAliveMonitor", "db", "Log Length reached, deleting " + str(Rows_To_Delete))
        db_KL_Curser.execute("DELETE FROM `" + Dobby_Config['Log_db'] + "`.KeepAliveMonitor WHERE Device='" + root_KL["Hostname"] + "' ORDER BY id LIMIT " + str(Rows_To_Delete) + ";")

    Close_db(db_KL_Connection, db_KL_Curser)


# ---------------------------------------- MQTT Functions ----------------------------------------
def MQTT_Functions(Payload):
    if ";" in Payload:
        Payload = Payload.replace(";", "")

    Log("Debug", "MQTT Functions", "Recieved", Payload)

    db_Func_Connection = Open_db("Dobby")
    db_Func_Curser = db_Func_Connection.cursor()

    try:
        db_Func_Curser.execute('SELECT Type, Command, DelayAfter FROM `Dobby`.`MQTT_Functions` WHERE Function="' + Payload + '" ORDER BY CommandNumber;')
        Command_List = db_Func_Curser.fetchall()
        Close_db(db_Func_Connection, db_Func_Curser)
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        Log("Critical", "MQTT Functions", "db", "Error: " + str(e[0]) + " - " + str(e[1]))
        return

    if Command_List is ():
        Log("Warning", "MQTT Functions", "Unknown Function", Payload)
        return

    Log("Info", "MQTT Functions", "Executing Function", Payload)

    for Command in Command_List:

        if "MQTT" in Command[0]:
            Publish_String = Command[1].split("&")

            if Publish_String[1][-1:] is not ";":
                MQTT_Client.publish(Publish_String[0], payload=Publish_String[1] + ";", qos=0, retain=False)
            else:
                MQTT_Client.publish(Publish_String[0], payload=Publish_String[1], qos=0, retain=False)

        elif "Audio" in Command[0]:
            # FIX - Add setting in db
            #call(["sudo", "-S", "mpg123", "-a", "btSpeaker", "-g", "50", "/etc/Dobby/Audio/" + Command[1]])
            pass

        if Command[2] != 0:
            # Delay_For = Command[2]
            time.sleep(Command[2])


# ---------------------------------------- # On message callbacks - Spawns threads ----------------------------------------
def MQTT_On_Message_Callback(mosq, obj, msg):
    Message_Thread = threading.Thread(target=MQTT_On_Message, kwargs={"Topic": msg.topic, "Payload": msg.payload, "Retained": msg.retain})
    Message_Thread.daemon = True
    Message_Thread.start()
    return


# ---------------------------------------- MQTT On Message ----------------------------------------
def MQTT_On_Message(Topic, Payload, Retained):

    for Target_Topic, Target_Function in dict(MQTT_Topic_Dict).iteritems():

        Do_Something = False

        if "#" in Target_Topic:
            # Check if incomming topic matches the beginning of target topic
            # Remove # from target topic
            Target_Topic = Target_Topic.replace("#", "")

            # if Topic == Target_Topic:
            if Topic[0:len(Target_Topic)] == Target_Topic:
                Do_Something = True

        elif "+" in Target_Topic:
            # Remove # from target topic
            Target_Topic = Target_Topic.replace("+", "")

            # The +1 is = to any char from the mqtt +
            if Topic[0:len(Target_Topic) + 1] == Target_Topic:
                Do_Something = True

        elif Topic == Target_Topic:
            Do_Something = True

        if Do_Something == True:
            # Run each function
            for Function in Target_Function:

                # Ignore retained messages
                if Retained is 0:

                    if Function[0] == "KeepAlive":
                        KeepAlive_Monitor(Topic, Payload)

                    elif Function[0] == "Log Trigger":
                        Log_Trigger.On_Message(Function[1], Payload, Retained)

                    elif Function[0] == "Alert Trigger":
                        Alert_Trigger.On_Message(Function[1], Payload)

                    elif Function[0] == "Action Trigger":
                        Action_Trigger.On_Message(Function[1], Topic, Payload)

                    elif Function[0] == "gBridge Trigger":
                        gBridge_Trigger_Local(Function[1], Topic, Payload)

                    elif Function[0] == "Functions":
                        MQTT_Functions(Payload)

                    elif Function[0] == "Commands":
                        MQTT_Commands(Topic, Payload)

                    elif Function[0] == "Device Logger":
                        Device_Logger(Topic, Payload, Retained)

                    else:
                        print 'Function missing - ' + str(Function)
                        for Target_Topic, Target_Function in dict(MQTT_Topic_Dict).iteritems():
                            print Target_Topic
                            print Target_Function


# ---------------------------------------- MQTT ----------------------------------------
def MQTT_Add_Sub_Topic(Topic, Function, Options={}):

    if Topic in MQTT_Topic_Dict:
        MQTT_Topic_Dict[Topic].append([Function, Options])
    else:
        MQTT_Topic_Dict[Topic] = [[Function, Options]]

def MQTT_Del_Sub_Topic(Topic, Function, Options={}):

    if Topic in MQTT_Topic_Dict:
        if [Function, Options] in MQTT_Topic_Dict[Topic]:
            MQTT_Topic_Dict[Topic].remove([Function, Options])

def MQTT_Subscribe_To(MQTT_Client, Topic):
    Log("Info", "Dobby", "MQTT", "Subscribing to topic: " + Topic)
    MQTT_Client.subscribe(Topic)


def MQTT_On_Connect(MQTT_Client, userdata, flags, rc):

    MQTT_Client.Connected = True
    Log("Debug", "Dobby", "MQTT", "Connected to broker " + str(Dobby_Config['MQTT_Broker']) + " with result code " + str(rc))

    for Topic, Callback in dict(MQTT_Topic_Dict).iteritems():
        Callback = Callback
        MQTT_Subscribe_To(MQTT_Client, Topic)

        MQTT_Client.message_callback_add(Topic, MQTT_On_Message_Callback)

    # MQTT KeepAlive
    # FIX - CHANGE KEEPALIVE TIMER SOURCE IN DB
    # KeepAlive_Thread = threading.Thread(target=MQTT_KeepAlive_Start, kwargs={"MQTT_Client": MQTT_Client})
    # KeepAlive_Thread.daemon = True
    # KeepAlive_Thread.start()


def MQTT_On_Disconnect(MQTT_Client, userdata, rc):
    MQTT_Client.Connected = False
    Log("Warning", "Dobby", "MQTT", "Disconnected from broker : " + str(Dobby_Config['MQTT_Broker']))


def MQTT_On_Log(MQTT_Client, userdata, level, buf):

    # Log level check
    if level == 16:
        if Dobby_Config['Log_Level_MQTT'] == "debug":
            Log("Debug", "MQTT", "Message", buf)

    else:
        Log("Warning", "MQTT", "Message", buf)


# ---------------------------------------- Init ----------------------------------------
def Dobby_init():
    # Open db connection
    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()
    
    # Get db config
    # Dobby
    Dobby_Config['System_Header'] = Get_System_Config_Value(db_Curser, "Dobby", "System", "Header")

    # MQTT
    Dobby_Config['MQTT_Broker'] = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Broker")
    Dobby_Config['MQTT_Port'] = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Port")
    Dobby_Config['MQTT_Username'] = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Username")
    Dobby_Config['MQTT_Password'] = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Password")
    Dobby_Config['MQTT_Publish_Delay'] = float(Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "PublishDelay"))
    Dobby_Config['MQTT_KeepAlive_Interval'] = int(Get_System_Config_Value(db_Curser, "Dobby", "MQTTKeepAlive", "Interval"))

    # Email
    Dobby_Config['Mail_Trigger_SMTP_Server'] = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Server")
    Dobby_Config['Mail_Trigger_SMTP_Port'] = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Port")
    Dobby_Config['Mail_Trigger_SMTP_Sender'] = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Sender")
    Dobby_Config['Mail_Trigger_SMTP_Username'] = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Username")
    Dobby_Config['Mail_Trigger_SMTP_Password'] = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Password")

    Dobby_Config['Log_db'] = Get_System_Config_Value(db_Curser, "Dobby", "Log", "db")
    Dobby_Config['Log_Level_System'] = Get_System_Config_Value(db_Curser, "Dobby", "Log", "Level").lower()

    Dobby_Config['Log_Length_System'] = int(Get_System_Config_Value(db_Curser, "Dobby", "Log", "Length"))

    # MQTT
    Dobby_Config['Log_Level_MQTT'] = Get_System_Config_Value(db_Curser, "MQTT", "Log", "Level", QuitOnError=False).lower()

    # From KeepAliveMonitor
    Dobby_Config['Log_Level_KeepAliveMonitor'] = Get_System_Config_Value(db_Curser, "KeepAliveMonitor", "Log", "Level", QuitOnError=False).lower()
    Dobby_Config['Log_Length_KeepAliveMonitor'] = int(Get_System_Config_Value(db_Curser, "KeepAliveMonitor", "Log", "Length"))

    # From MQTTConfig
    Dobby_Config['Log_Level_MQTT_Config'] = Get_System_Config_Value(db_Curser, "MQTT Config", "Log", "Level", QuitOnError=False).lower()

    # From MQTT Functions
    Dobby_Config['Log_Level_MQTT_Functions'] = Get_System_Config_Value(db_Curser, "MQTT Functions", "Log", "Level", QuitOnError=False).lower()

    # Mail_Trigger
    Dobby_Config['Log_Level_Mail_Trigger'] = Get_System_Config_Value(db_Curser, "Mail_Trigger", "Log", "Level", QuitOnError=False).lower()

    # Log_Trigger
    Dobby_Config['Log_Level_Log_Trigger'] = Get_System_Config_Value(db_Curser, "Log_Trigger", "Log", "Level", QuitOnError=False).lower()

    # Spammer
    Dobby_Config['Log_Level_Spammer'] = Get_System_Config_Value(db_Curser, "Spammer", "Log", "Level", QuitOnError=False).lower()

    # APC_Monitor
    Dobby_Config['Log_Level_APC_Monitor'] = Get_System_Config_Value(db_Curser, "APC_Monitor", "Log", "Level", QuitOnError=False).lower()
    
    # # Backup
    # Dobby_Config['Backup_URL_FTP'] = Get_System_Config_Value(db_Curser, "Backup", "URL", "FTP", QuitOnError=False).lower()
    
    # Append Topics to subscribe to subscribe list
    # Log
    MQTT_Add_Sub_Topic(Dobby_Config['System_Header'] + "/Log/#", 'Device Logger')
    # KeepAlive
    MQTT_Add_Sub_Topic(Dobby_Config['System_Header'] + "/KeepAlive/#", 'KeepAlive')
    # Functions
    MQTT_Add_Sub_Topic(Dobby_Config['System_Header'] + "/Functions", 'Functions')
    # Dobby Commands
    MQTT_Add_Sub_Topic(Dobby_Config['System_Header'] + "/Commands/Dobby/#", 'Commands')

    # Check if the needed databases exists
    Create_db(db_Curser, Dobby_Config['Log_db'])

    Close_db(db_Connection, db_Curser)


def MQTT_init():
    # MQTT Setup
    MQTT_Client.username_pw_set(Dobby_Config['MQTT_Username'], Dobby_Config['MQTT_Password'])
    # FIX - ADD MQTT Logging
    MQTT_Client.on_log = MQTT_On_Log

    # Callbacks
    MQTT_Client.on_connect = MQTT_On_Connect
    MQTT_Client.on_disconnect = MQTT_On_Disconnect

    # Connect to broker
    MQTT_Client.connect(Dobby_Config['MQTT_Broker'], port=Dobby_Config['MQTT_Port'], keepalive=60, bind_address="")

    # Boot message - MQTT
    MQTT_Client.publish(Dobby_Config['System_Header'] + "/Log/Dobby/Info/System", payload="Booting Dobby - Version: " + str(Version), qos=0, retain=False)



# ---------------------------------------- MQTT Target Check ----------------------------------------
class MQTT_Target_Check():

    Check_Delay = 0.500
    
    def __init__(self):
        # Log event
        Log("Debug", "System", "MQTT Target Check", "Initializing")

        # Create vars
        self.Check_At = datetime.datetime.now()
        self.MQTT_Target = ""
        self.Delete_Me = False
        self.Triggered = True

        # Start timeout
        Timer_Thread = threading.Thread(target=self.Run)
        Timer_Thread.daemon = True
        Timer_Thread.start()

    def Reset(self, MQTT_Target, Expected_Value, Force_Change=True):
        # Log event
        Log("Debug", "System", "MQTT Target Check", "Reset alert id: " + str(MQTT_Target))
        
        # Save vars
        self.MQTT_Target = MQTT_Target
        ## Add timeout to current time to get Timeout_At
        self.Timeout_At = datetime.datetime.now() + datetime.timedelta(seconds=self.Timeout)
        ## Alert id
        self.MQTT_Target = MQTT_Target

        # Reset triggered
        self.Triggered = False
        

    def Delete(self):
        Log("Debug", "System", "MQTT Target Check", "Deleted alert id: " + str(self.MQTT_Target))
        # Mark thread for deletions
        self.Delete_Me = True


    def Trigger_Timeout(self):
        if self.Triggered == True:
            return
        
        # Set var to prevent retrigger
        self.Triggered = True

        # Log event
        Log("Debug", "System", "MQTT Target Check", "Triggered alert id:" + str(self.Alert_Target_id))
        
        # Get alert information from db        
        ## Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()
        # Set autocommit so no delay on saving changes
        db_Curser.execute("set autocommit = 1")

        ## Get id and Last Modified to check if gBridge Triggers needs to be started
        db_Curser.execute("SELECT `Mail Target`, `MQTT Target`, `Push Target`, Subject, Body FROM Dobby.`Alert_Targets` WHERE id=" + str(self.Alert_Target_id) + ";")
        Alert_Info = db_Curser.fetchone()

        # Change Last_Trigger
        db_Curser.execute("UPDATE `Dobby`.`Alert_Targets` SET `Last_Trigger`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(id) + "';")

        ## Close db connection
        Close_db(db_Connection, db_Curser)

        # Send Alerts
        ## 0 = Mail Target
        ## 1 = MQTT Target
        ## 2 = Push Target
        ## 3 = Subject
        ## 4 = Body
        print "fix mqtt target check"
        # Send_Alert(Alert_Info[3], Alert_Info[4], None, Alert_Info[0], Alert_Info[1], Alert_Info[2])


    def Run(self):
        # Just sleep untill id is set
        while self.Alert_Target_id == "" and self.Delete_Me == False:
            # Sleep untill next check
            time.sleep(self.Check_Delay)

        # When id is set start the timeout
        while self.Delete_Me == False:
 
            # Check if current time vs timeout at time
            if self.Timeout_At < datetime.datetime.now():
                self.Trigger_Timeout()

            # Sleep untill next check
            time.sleep(self.Check_Delay)


    

# ---------------------------------------- Send Mail ----------------------------------------
def Send_Mail(To, Subject, Text):
    # Remove any spaces
    To = To.replace(" ", "")

    Target_List = []

    # Multiple targets
    if "," in To:
        Target_List = To.split(",")

    # Single target
    else:
        Target_List.append(To)

    Mail_Body = "\r\n".join([
        "From: " + str(Dobby_Config['Mail_Trigger_SMTP_Sender']),
        "To: " + To,
        "Subject: " + str(Subject),
        "",
        str(Text)
    ])


    # Connect to mail server
    Mail_Server = smtplib.SMTP(Dobby_Config['Mail_Trigger_SMTP_Server'], Dobby_Config['Mail_Trigger_SMTP_Port'])
    Mail_Server.ehlo()
    Mail_Server.starttls()
    Mail_Server.login(Dobby_Config['Mail_Trigger_SMTP_Username'], Dobby_Config['Mail_Trigger_SMTP_Password'])

    # Send Email
    for To_Email in Target_List:
        Mail_Server.sendmail(Dobby_Config['Mail_Trigger_SMTP_Sender'], To_Email, str(Mail_Body))
        Log("Debug", "System", "Mail", 'Send mail to: ' + str(To_Email))

    # Disconnect from mail server
    Mail_Server.quit()


# ---------------------------------------- Send Push ----------------------------------------
def Send_Push(Target, Subject, Message):
    # Remove any spaces
    Target = Target.replace(" ", "")

    Target_List = []

    # Multiple targets
    if "," in Target:
        Target_List = Target.split(",")

    # Single target
    else:
        Target_List.append(Target)

    # Generate the URL needed for the request
    URL_End = "&title=" + str(Subject) + "&message=" + str(Message) + "&type=Alert"
    URL_End = URL_End.replace(" ", "%20")

    # Send Push Notification 
    for Target_Push in Target_List:
        print "PIK"
        print "https://wirepusher.com/send?id=" + str(Target_Push) + URL_End
        
        r = requests.get("https://wirepusher.com/send?id=" + str(Target_Push) + URL_End)
        r.status_code
        
        Log("Debug", "System", "Push", 'Status: ' + str(r.status_code))


# ---------------------------------------- Alert Trigger ----------------------------------------
class Alert_Trigger():
    # How often the db is cheched for changes
    Refresh_Rate = 5

    Active_Triggers = {}

    def __init__(self):
        # Log event
        Log("Info", "Alert Trigger", "Checker", "Initializing")

        # Start checker thread
        File_Change_Checker_Thread = threading.Thread(target=self.Checker, kwargs={})
        File_Change_Checker_Thread.daemon = True
        File_Change_Checker_Thread.start()

    def Checker(self):
        # Start eternal loop
        while True:
            # Open db connection get id, Last Modified
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            # Get id and Last Modified to check if Alert Triggers needs to be started
            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.`Alert_Trigger` WHERE Enabled=1;")
            Alert_Info = db_Curser.fetchall()

            for i in range(len(Alert_Info)):
                # Alert_Info[i][0] - id
                # Alert_Info[i][1] - Last Modified

                # Check if the trigger is in the Active_Triggers dict
                if Alert_Info[i][0] in self.Active_Triggers:
                    
                    # Check if last modified changed
                    if self.Active_Triggers[Alert_Info[i][0]] != Alert_Info[i][1]:
                        self.Active_Triggers[Alert_Info[i][0]] = Alert_Info[i][1]
                        self.Restart_Trigger(Alert_Info[i][0])
                        
                # If not add then to the list and start the trigger
                else:
                    self.Active_Triggers[Alert_Info[i][0]] = Alert_Info[i][1]
                    # Start the trigger
                    self.Start_Trigger(Alert_Info[i][0])

            # Close db connection
            Close_db(db_Connection, db_Curser)

            # Sleep till next check
            time.sleep(self.Refresh_Rate)
    

    def Start_Trigger(self, id):

        Trigger_Info = self.Get_Trigger_Info(id)
        # Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT Name, `MQTT Target` FROM Dobby.`Alert_Trigger` WHERE id="+ str(id) + ";")
        Trigger_Info = db_Curser.fetchone()
        # Trigger_Info[0] - Name
        # Trigger_Info[1] - Target

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Log Event
        Log("Debug", "Alert Trigger", str(Trigger_Info[0]), "Starting")
        Log("Debug", "Alert Trigger", str(Trigger_Info[0]), "Subscribing to: '" + str(Trigger_Info[1]) + "'")
        # Add topic to topic tict
        MQTT_Add_Sub_Topic(str(Trigger_Info[1]), 'Alert Trigger', id)
        # Subscribe
        MQTT_Client.subscribe(str(Trigger_Info[1]))
        # Register callbacks
        MQTT_Client.message_callback_add(str(Trigger_Info[1]), MQTT_On_Message_Callback)


    def Stop_Trigger(self, id):

        Trigger_Info = self.Get_Trigger_Info(id)

         # Log Event
        Log("Debug", "Alert Trigger", str(Trigger_Info[0]), "Stopping")
        Log("Debug", "Alert Trigger", str(Trigger_Info[0]), "Unsubscribing from: '" + str(Trigger_Info[1]) + "'")

        MQTT_Del_Sub_Topic(Trigger_Info[1], 'Alert Trigger', id)


    def Restart_Trigger(self, id):
        self.Start_Trigger(id)
        self.Stop_Trigger(id)


    def Get_Trigger_Info(self, id):
        # Open db connection
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("SELECT Name, `MQTT Target` FROM Dobby.`Alert_Trigger` WHERE id="+ str(id) + ";")
        Trigger_Info = db_Curser.fetchone()
        # Trigger_Info[0] - Name
        # Trigger_Info[1] - Target

        # Close db connection
        Close_db(db_Connection, db_Curser)

        # Return info
        return Trigger_Info


    @classmethod
    def On_Message(cls, id, Payload):

        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        db_Curser.execute("set autocommit = 1")

        db_Curser.execute("SELECT Name, `Alert State`, `MQTT Payload Clear`, `MQTT Payload Trigger`, `Alert Target id`, `Alert Subject`, `Alert Payload Clear`, `Alert Payload Trigger` FROM Dobby.Alert_Trigger WHERE id=" + str(id) + ";")
        Trigger_Info = db_Curser.fetchone()
           
        Name = Trigger_Info[0]
        Alert_State = Trigger_Info[1]
        MQTT_Payload_Clear = Trigger_Info[2]
        MQTT_Payload_Trigger = Trigger_Info[3]
        Alert_Target_id = Trigger_Info[4]
        Alert_Subject = Trigger_Info[5]
        Alert_Payload_Clear = Trigger_Info[6]
        Alert_Payload_Trigger = Trigger_Info[7]

        # Find out what to do
        Action = 2
        # 0 = Clear
        # 1 = Trigger
        # 2 = In-between

        Trigger_Change = False

        if float(MQTT_Payload_Clear) == float(MQTT_Payload_Trigger):
            Log("Error", "Alert Trigger", str(Name), 'Clear and Trigger payload is the same value')
            Close_db(db_Connection, db_Curser)
            return

        # High / Low Check
        # Value moving from Low to High
        elif (float(MQTT_Payload_Clear) <= float(MQTT_Payload_Trigger)) is True:
            # Clear check
            if float(MQTT_Payload_Clear) >= float(Payload):
                Action = 0

            # Trigger check
            elif float(MQTT_Payload_Trigger) <= float(Payload):
                Action = 1

        # Value moving from High to Low
        else:
            # Clear check
            if float(MQTT_Payload_Clear) <= float(Payload):
                Action = 0

            # Trigger check
            elif float(MQTT_Payload_Trigger) >= float(Payload):
                Action = 1

        # Take action if needed
        # Clear
        if Action == 0:
            # Check agains current alert state
            if Action == Alert_State:
                Log("Debug", "Alert Trigger", str(Name), 'Already cleared ignoring new clear value: ' + str(Payload))
            else:
                Trigger_Change = True

                # Send Alert Notification
                Send_Alert(Alert_Target_id, Payload, Alert_Subject, Alert_Payload_Clear)
                Log("Info", "Alert Trigger", str(Name), 'Cleared at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Clear))

        # Trigger
        elif Action == 1:
            # Check agains current alert state
            if Action == Alert_State:
                Log("Debug", "Alert Trigger", str(Name), 'Already triggered ignoring new trigger value: ' + str(Payload))
            else:
                Trigger_Change = True

                # Send Alert Notification 
                Send_Alert(Alert_Target_id, Payload, Alert_Subject, Alert_Payload_Trigger)
                Log("Info", "Alert Trigger", str(Name), 'Triggered at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Trigger))

        # In-between value
        elif Action == 2:
            Log("Debug", "Alert Trigger", str(Name), 'In-between value received: ' + str(Payload))

        if Trigger_Change is True:
            # Change Alert_State
            db_Curser.execute("UPDATE `Dobby`.`Alert_Trigger` SET `Alert State`='" + str(Action) + "' WHERE `id`='" + str(id) + "';")
            # Update Triggered_DateTime
            db_Curser.execute("UPDATE `Dobby`.`Alert_Trigger` SET `Triggered DateTime`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(id) + "';")

        Close_db(db_Connection, db_Curser)

# ---------------------------------------- Spammer ----------------------------------------
class Spammer:

    # How often does esch spammer read write to the db (sec)
    db_Refresh_Rate = 5
    Loop_Delay = 0.500

    def __init__(self):
        # Log event
        Log("Info", "Spammer", "Checker", "Starting")

        self.Spammer_Dict = {}

        # Start checker thread
        Spammer_Thread = threading.Thread(target=self.Checker, kwargs={})
        Spammer_Thread.daemon = True
        Spammer_Thread.start()

    def Checker(self):

        while True:
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.Spammer")
            Spammer_db = db_Curser.fetchall()

            Close_db(db_Connection, db_Curser)

            for i in Spammer_db:
                # i[0] = Spammer db id
                if i[0] not in self.Spammer_Dict:
                    self.Spammer_Dict[i[0]] = self.Agent(i[0])
                    Log("Debug", "Spammer", "Checker", "Starting: " + self.Spammer_Dict[i[0]].Name)

                else:
                    # Change to spammer
                    if str(self.Spammer_Dict[i[0]].Last_Modified) != str(i[1]):
                        Log("Debug", "Spammer", "Checker", "Change found in: " + self.Spammer_Dict[i[0]].Name + " restarting agent")
                        # Wait for agent to close db connection
                        while self.Spammer_Dict[i[0]].OK_To_Kill is False:
                            time.sleep(0.100)

                        # Delete agent
                        Log("Debug", "Spammer", "Checker", "Deleting: " + self.Spammer_Dict[i[0]].Name)
                        del self.Spammer_Dict[i[0]]
                        # Start agent again
                        self.Spammer_Dict[i[0]] = self.Agent(i[0])
                        Log("Debug", "Spammer", "Checker", "Starting: " + self.Spammer_Dict[i[0]].Name)

                time.sleep(random.uniform(0.150, 0.500))

            time.sleep(Spammer.db_Refresh_Rate)

    class Agent:
        def __init__(self, id):

            self.id = int(id)

            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT Name, Enabled, `Interval`, Topic, Payload, Next_Ping, Last_Modified FROM Dobby.Spammer WHERE id='" + str(self.id) + "'")
            Spammer_Info = db_Curser.fetchone()

            Close_db(db_Connection, db_Curser)

            self.Name = str(Spammer_Info[0])

            # Can't log event before now if you want to use name
            Log("Debug", "Spammer", self.Name, 'Initializing')

            self.Enabled = bool(Spammer_Info[1])
            self.Interval = float(Spammer_Info[2])
            self.Topic = Spammer_Info[3]
            self.Payload = Spammer_Info[4]
            self.Next_Ping = Spammer_Info[5]
            self.Last_Modified = Spammer_Info[6]
            
            if self.Enabled == 0:
                Log("Debug", "Spammer", self.Name, 'Disabled - Not starting agent')
                quit()
            self.OK_To_Kill = True
            self.Kill = False

            Log("Debug", "Spammer", self.Name, 'Initialization compleate')

            self.Start()

        # ========================= Agent - Start =========================
        def Start(self):
            Spammer_Thread = threading.Thread(target=self.Run, kwargs={})
            Spammer_Thread.daemon = True
            Spammer_Thread.start()

        # ========================= Agent - Run =========================
        def Run(self):

            Log("Info", "Spammer", self.Name, "Running")
            # Start eternal loop
            while True:
                # Check if its time to ping
                if self.Next_Ping < datetime.datetime.now():
                    Log("Debug", "Spammer", self.Name, "Ping")

                    self.Next_Ping = datetime.datetime.now() + datetime.timedelta(seconds=self.Interval)

                    self.OK_To_Kill = False

                    db_Connection = Open_db("Dobby")
                    db_Curser = db_Connection.cursor()

                    db_Curser.execute("UPDATE `Dobby`.`Spammer` SET `Next_Ping`='" + str(self.Next_Ping) + "', `Last_Ping`='" + str(datetime.datetime.now()) + "' WHERE id = '" + str(self.id) + "';")

                    Close_db(db_Connection, db_Curser)

                    self.OK_To_Kill = True

                    MQTT_Client.publish(self.Topic, payload=self.Payload, qos=0, retain=False)

                    time.sleep(Spammer.Loop_Delay)

                while self.Next_Ping > datetime.datetime.now():
                    time.sleep(Spammer.Loop_Delay)

                if self.Kill is True:
                    quit()


# ---------------------------------------- Device Logger ----------------------------------------
def Device_Logger(Topic, Payload, Retained):

    if Retained is True:
        return

    db_Device_Log_Connection = Open_db(Dobby_Config['Log_db'])
    db_Device_Log_Curser = db_Device_Log_Connection.cursor()

    Device_Log_Table = "DeviceLog"

    Device_Name = Topic.split("/")
    
    Device_Name = Device_Name[3]

    try:
        db_Device_Log_Curser.execute('INSERT INTO `' + Dobby_Config['Log_db'] + '`.`' + Device_Log_Table + '` (Device, Topic, Payload) VALUES("' + Device_Name + '","' + Topic + '", "' + Payload + '");')
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # 1146 = Table is missing
        if e[0] == 1146:
            try:
                db_Device_Log_Curser.execute("CREATE TABLE `" + Dobby_Config['Log_db'] + "`.`" + Device_Log_Table + "` (`id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, `Device` varchar(75) NOT NULL, `Topic` varchar(75) NOT NULL, `Payload` varchar(200) NOT NULL, PRIMARY KEY (`id`))")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                print e
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    # FIX add some error handling here
                    print "DB WTF ERROR 1: " + str(e)

                    # Try to write log again
                    db_Device_Log_Curser.execute('INSERT INTO `' + Dobby_Config['Log_db'] + '`.`' + Device_Log_Table + '` (Device, Topic, Payload) VALUES("' + Device_Name + '","' + Topic + '", "' + Payload + '");')
                else:
                    # FIX add some error handling here
                    print "DB WTF ERROR 2:" + str(e)

    Check_db_Length(db_Device_Log_Curser, Device_Log_Table)

    Close_db(db_Device_Log_Connection, db_Device_Log_Curser)


# ---------------------------------------- EP Logger ----------------------------------------
class EP_Logger:

    # How often does esch EP_Logger read write to the db (sec)
    db_Refresh_Rate = 5
    Loop_Delay = 0.500

    def __init__(self):
        # Log event
        Log("Info", "EP Logger", "Checker", "Starting")

        self.EP_Logger_Dict = {}

        # Start checker thread
        EP_Logger_Thread = threading.Thread(target=self.Checker, kwargs={})
        EP_Logger_Thread.daemon = True
        EP_Logger_Thread.start()

    def Checker(self):

        while True:
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.EP_Logger")
            EP_Logger_db = db_Curser.fetchall()

            Close_db(db_Connection, db_Curser)

            for i in EP_Logger_db:
                # i[0] = EP_Logger db id
                if i[0] not in self.EP_Logger_Dict:
                    self.EP_Logger_Dict[i[0]] = self.Agent(i[0])
                    Log("Debug", "EP Logger", "Checker", "Starting: " + self.EP_Logger_Dict[i[0]].Name)

                else:
                    # Change to EP_Logger
                    if str(self.EP_Logger_Dict[i[0]].Last_Modified) != str(i[1]):
                        Log("Debug", "EP Logger", "Checker", "Change found in: " + self.EP_Logger_Dict[i[0]].Name + " restarting agent")
                        # Wait for agent to close db connection
                        while self.EP_Logger_Dict[i[0]].OK_To_Kill is False:
                            time.sleep(0.100)

                        # Delete agent
                        Log("Debug", "EP Logger", "Checker", "Deleting: " + self.EP_Logger_Dict[i[0]].Name)
                        del self.EP_Logger_Dict[i[0]]
                        # Start agent again
                        self.EP_Logger_Dict[i[0]] = self.Agent(i[0])
                        Log("Debug", "EP Logger", "Checker", "Starting: " + self.EP_Logger_Dict[i[0]].Name)

                time.sleep(random.uniform(0.150, 0.500))

            time.sleep(EP_Logger.db_Refresh_Rate)

    class Agent:
        def __init__(self, id):

            self.id = int(id)

            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT Name, Enabled, `Serial Port`, `Log Rate`, `Next Ping`, `Last Ping`, Last_Modified FROM Dobby.EP_Logger WHERE id='" + str(self.id) + "'")
            EP_Logger_Info = db_Curser.fetchone()

            Close_db(db_Connection, db_Curser)

            self.Name = str(EP_Logger_Info[0])
            self.Enabled = bool(EP_Logger_Info[1])
            self.Serial_Port = EP_Logger_Info[2]
            self.Log_Rate = EP_Logger_Info[3]
            self.Next_Ping = EP_Logger_Info[4]
            self.Last_Ping = EP_Logger_Info[5]
            self.Last_Modified = EP_Logger_Info[6]

            self.EP_Logger_Client = ModbusClient(method = 'rtu', port = self.Serial_Port, baudrate = 115200)
            
            # Can't log event before now if you want to use name
            Log("Debug", "EP Logger", self.Name, 'Initializing')
            
            if self.Enabled == 0:
                Log("Debug", "EP Logger", self.Name, 'Disabled - Not starting agent')
                quit()
            self.OK_To_Kill = True
            self.Kill = False

            Log("Debug", "EP Logger", self.Name, 'Initialization compleate')

            self.Start()

        # ========================= Agent - Start =========================
        def Start(self):
            EP_Logger_Thread = threading.Thread(target=self.Run, kwargs={})
            EP_Logger_Thread.daemon = True
            EP_Logger_Thread.start()


        # ========================= Agent - Read Input =========================
        def Read_Input(self, Address, Count=1):

            Address = int(str(Address), 16)

            Modbus_Value = self.EP_Logger_Client.read_input_registers(Address, Count, unit=1)

            # Got a valid value
            if "<class 'pymodbus.register_read_message.ReadInputRegistersResponse'>" == str(type(Modbus_Value)):
                return Modbus_Value
            # Something went wrong
            else:
                return "ERROR: " + str(Modbus_Value)


        # ========================= Agent - Run =========================
        def Run(self):

            Log("Info", "EP Logger", self.Name, "Running")
            self.EP_Logger_Client.connect()

            # Start eternal loop
            while True:
                # Check if its time to ping
                if self.Next_Ping < datetime.datetime.now():
                    Log("Debug", "EP Logger", self.Name, "Ping")

                    self.Next_Ping = datetime.datetime.now() + datetime.timedelta(seconds=self.Log_Rate)

                    self.OK_To_Kill = False

                    db_Connection = Open_db("Dobby")
                    db_Curser = db_Connection.cursor()

                    db_Curser.execute("set autocommit = 1")
                    
                    # Get row names
                    db_Curser.execute("SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='EP_Logger';")
                    EP_Logger_Info_Names = db_Curser.fetchall()
                
                    # Get row values
                    db_Curser.execute("SELECT * FROM Dobby.EP_Logger WHERE id = '" + str(self.id) + "';")
                    EP_Logger_Info_Values = db_Curser.fetchone()

                    # Update next / last ping
                    db_Curser.execute("UPDATE `Dobby`.`EP_Logger` SET `Next Ping`='" + str(self.Next_Ping) + "', `Last Ping`='" + str(datetime.datetime.now()) + "' WHERE id = '" + str(self.id) + "';")
                    
                    Close_db(db_Connection, db_Curser)

                    Ignore_List = ['id', 'Name', 'Enabled', 'Serial Port', 'Log Rate', 'Next Ping', 'Last Ping', 'Last_Modified']

                    # List containg lists with tree values name, modbus id, multiplier
                    Modbud_id_List = []

                    for i in range(len(EP_Logger_Info_Names)):

                        if EP_Logger_Info_Names[i][0] in Ignore_List:
                            continue

                        if EP_Logger_Info_Values[i] is 0:
                            continue

                        id_Dict = {}

                        id_Dict['Multiplier'] = 1

                        Test_List = ['Amp', 'Volt', "Watt", "Temperature"]

                        for Test_Name in Test_List:
                            if Test_Name in EP_Logger_Info_Names[i][0]:
                                id_Dict['Multiplier'] = 0.01
                                break

                        id_Dict['Name'] = EP_Logger_Info_Names[i][0][:-7]
                        id_Dict['id'] = EP_Logger_Info_Names[i][0][-6:]

                        Modbud_id_List.append(id_Dict)

                    # Request values
                    for Info in Modbud_id_List:


                        # Read input value
                        ## 0x3200 and 0x3201 needs to read two units
                        if Info['Name'] in {'Battery Status', 'Charger Status'}:
                            Modbus_Value = self.Read_Input(Info['id'], 2)
                        else:
                            Modbus_Value = self.Read_Input(Info['id'])

                        # Check for errors
                        if type(Modbus_Value) is str:
                            # FIX - ADD PROPER ERROR MESSAGE
                            print "Modbus error: " + Modbus_Value
                            print Info['Name']
                            continue

                        # Battery Status
                        if Info['Name'] == 'Battery Status':

                            # D3-D0: 
                            # 00H Normal 
                            # 01H Overvolt 
                            # 02H Under Volt
                            # 03H Low Volt Disconnect
                            # 04H Fault 

                            # D7-D4: 
                            # 00H Normal
                            # 01H Over Temp.(Higher than the warning settings)
                            # 02H Low Temp.( Lower than the warning settings), 

                            # D8: 
                            # normal 0 
                            # Battery inerternal resistance abnormal 1, 

                            # D15: 
                            # 1-Wrong identification for rated voltage
                            
                            # https://www.oipapio.com/question-5355673
                            # No clue how this works but it seems to do so will take it 

                            # Define each mask as a tuple with all the bit at 1 and distance from the right:
                            D3_D0_mask = (0b1111, 0)
                            D7_D4_mask = (0b1111, 4)
                            D8_mask = (0b1, 8)
                            D15_mask = (0b1, 15)

                            # Creating the json dict with all values as false
                            json_State = {}
                            json_State["Fault"] = False
                            json_State["Low Volt Disconnect"] = False
                            json_State["Under Volt"] = False
                            json_State["Overvolt"] = False
                            json_State["Normal Voltage"] = False
                            json_State["Low Temp"] = False
                            json_State["Over Temp"] = False
                            json_State["Normal Temp"] = False
                            json_State["Battery internal resistance abnormal"] = False
                            json_State["Wrong identification for rated voltage"] = False

                            # compare each mask to the value, after shifting to the right position:
                            # Update values to true if so
                            if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 4:
                                json_State["Fault"] = True
                            if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 3:
                                json_State["Low Volt Disconnect"] = True
                            if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 2:
                                json_State["Under Volt"] = True
                            if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 1:
                                json_State["Overvolt"] = True
                            if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 0:
                                json_State["Normal Voltage"] = True
                            if D7_D4_mask[0]&(Modbus_Value.registers[0]>>D7_D4_mask[1]) == 2:
                                json_State["Low Temp"] = True
                            if D7_D4_mask[0]&(Modbus_Value.registers[0]>>D7_D4_mask[1]) == 1:
                                json_State["Over Temp"] = True
                            if D7_D4_mask[0]&(Modbus_Value.registers[0]>>D7_D4_mask[1]) == 0:
                                json_State["Normal Temp"] = True
                            if D8_mask[0]&(Modbus_Value.registers[0]>>D8_mask[1]) == 1:
                                json_State["Battery internal resistance abnormal"] = True
                            if D15_mask[0]&(Modbus_Value.registers[0]>>D15_mask[1]) == 1:
                                json_State["Wrong identification for rated voltage"] = True

                            Modbus_Value = json.dumps(json_State)


                        elif Info['Name'] == 'Charger Status':

                            # D15-D14: Input volt status. 
                            #     00H normal
                            #     01H no power connected
                            #     02H Higher volt input
                            #     03H Input volt error.
                            # D13: Charging MOSFET is shorted.
                            # D12: Charging or Anti-reverse MOSFET is shorted.
                            # D11: Anti-reverse MOSFET is shorted.
                            # D10: Input is over current.
                            # D9: The load is Over current.
                            # D8: The load is shorted.
                            # D7: Load MOSFET is shorted.
                            # D4: PV Input is shorted.
                            # D3-2: Charging status.
                            #     00 No charging
                            #     01 Float
                            #     02 Boost
                            #     03 Equlization.
                            # D1: 0 Normal, 1 Fault.
                            # D0: 1 Running, 0 Standby


                            # Define each mask as a tuple with all the bit at 1 and distance from the right:
                            D0_mask = (0b1, 0)
                            D1_mask = (0b1, 1)
                            D3_D2_mask = (0b11, 2)
                            D4_mask = (0b1, 4)
                            D7_mask = (0b1, 7)
                            D8_mask = (0b1, 8)
                            D9_mask = (0b1, 9)
                            D10_mask = (0b1, 10)
                            D11_mask = (0b1, 11)
                            D12_mask = (0b1, 12)
                            D13_mask = (0b1, 13)
                            D15_D14_mask = (0b11, 14)

                            # Creating the json dict with all values as false
                            json_State = {}
                            json_State['Running'] = False
                            json_State['Standby'] = False
                            json_State['Normal'] = False
                            json_State['Fault'] = False
                            json_State['No charging'] = False
                            json_State['Float'] = False
                            json_State['Boost'] = False
                            json_State['Equlization'] = False
                            json_State['PV Input is shorted'] = False
                            json_State['Charging or Anti-reverse MOSFET is shorted'] = False
                            json_State['Anti-reverse MOSFET is shorted'] = False
                            json_State['Input is over current'] = False
                            json_State['The load is Over current'] = False
                            json_State['The load is shorted'] = False
                            json_State['Load MOSFET is shorted'] = False
                            json_State['Load MOSFET is shorted'] = False
                            json_State['Input voltage normal'] = False
                            json_State['No power connected'] = False
                            json_State['Higher volt input'] = False
                            json_State['Input volt error'] = False

                            # D0
                            if D0_mask[0]&(Modbus_Value.registers[0]>>D0_mask[1]) == 1:
                                json_State['Running'] = True
                            else:
                                json_State['Standby'] = True
                            # D1
                            if D1_mask[0]&(Modbus_Value.registers[0]>>D1_mask[1]) == 0:
                                json_State['Normal'] = True
                            else:
                                json_State['Fault'] = True
                            # D3-D2
                            if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 0:
                                json_State['No charging'] = True
                            if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 1:
                                json_State['Float'] = True
                            if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 2:
                                json_State['Boost'] = True
                            if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 3:
                                json_State['Equlization'] = True
                            # D4
                            if D4_mask[0]&(Modbus_Value.registers[0]>>D4_mask[1]) == 1:
                                json_State['PV Input is shorted'] = True
                            # D7
                            if D7_mask[0]&(Modbus_Value.registers[0]>>D7_mask[1]) == 1:
                                json_State['Charging or Anti-reverse MOSFET is shorted'] = True
                            # D8
                            if D8_mask[0]&(Modbus_Value.registers[0]>>D8_mask[1]) == 1:
                                json_State['Anti-reverse MOSFET is shorted'] = True
                            # D9
                            if D9_mask[0]&(Modbus_Value.registers[0]>>D9_mask[1]) == 1:
                                json_State['Input is over current'] = True
                            # D10
                            if D10_mask[0]&(Modbus_Value.registers[0]>>D10_mask[1]) == 1:
                                json_State['The load is Over current'] = True
                            # D11
                            if D11_mask[0]&(Modbus_Value.registers[0]>>D11_mask[1]) == 1:
                                json_State['The load is shorted'] = True
                            # D12
                            if D12_mask[0]&(Modbus_Value.registers[0]>>D12_mask[1]) == 1:
                                json_State['Load MOSFET is shorted'] = True
                            # D13
                            if D13_mask[0]&(Modbus_Value.registers[0]>>D13_mask[1]) == 1:
                                json_State['Load MOSFET is shorted'] = True
                            # D3-D2
                            if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 0:
                                json_State['Input voltage normal'] = True
                            if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 1:
                                json_State['No power connected'] = True
                            if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 2:
                                json_State['Higher volt input'] = True
                            if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 3:
                                json_State['Input volt error'] = True

                            Modbus_Value = json.dumps(json_State)
                            
                        else:
                            Modbus_Value = str(float(Modbus_Value.registers[0] * Info['Multiplier']))

                        # Publish
                        MQTT_Client.publish(Dobby_Config['System_Header'] + '/EP/' + str(self.Name) + '/' + str(Info['Name']), payload=str(Modbus_Value), qos=0, retain=True)
                        # Log event
                        Log("Debug", "EP Logger", "db", "Publish")

                        time.sleep(0.05)

                    self.OK_To_Kill = True

                    time.sleep(EP_Logger.Loop_Delay)

                while self.Next_Ping > datetime.datetime.now():
                    time.sleep(EP_Logger.Loop_Delay)

                if self.Kill is True:
                    quit()


# ---------------------------------------- Init ----------------------------------------
Dobby_init()

MQTT_init()

Alert_Trigger()

Action_Trigger()

MQTT_Client_gBridge = gBridge_Trigger()

Spammer()

Log_Trigger()

Counters()

EP_Logger()

# ---------------------------------------- Loop ----------------------------------------
# Start MQTT Loop
MQTT_Client.loop_forever()