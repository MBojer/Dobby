#!/usr/bin/python

# ---------- Change log ----------
# See change log

# MySQL
import MySQLdb

# MQTT
import paho.mqtt.client as MQTT

# Threding
import threading

# Time
import time
import datetime
from datetime import timedelta
import random

# MQTT KeepAlive
import psutil

# MQTTFunctions
import subprocess
from subprocess import call

# json
import json

# Auto Update
# import urllib
import os

# Email Support
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# FTP
import ftplib
from StringIO import StringIO
# For unique file id
import uuid
import io

# For uDP Config
import socket

# System variables
Version = 101021
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number

Start_Time = datetime.datetime.now()

# MQTT Client
MQTT_Client = MQTT.Client(client_id="Dobby", clean_session=True)

# MQTT Topic list
MQTT_Topic_Dict = {}

# Message_Check
Mail_Trigger_Subscribe_List = []
# MonitorAgent_Subscribe_List = []

# Backup()
import schedule
import pipes


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


# ---------------------------------------- Logging ----------------------------------------
def Log(Log_Level, Log_Source, Log_Header, Log_Text):
    Log_Thread = threading.Thread(target=Write_Log, kwargs={"Log_Level": Log_Level, "Log_Source": Log_Source, "Log_Header": Log_Header, "Log_Text": Log_Text})
    Log_Thread.daemon = True
    Log_Thread.start()


def Write_Log(Log_Level, Log_Source, Log_Header, Log_Text):

    if Log_Level_Check(Log_Source, Log_Level) is False:
        return

    db_Log_Connection = Open_db(Log_db)
    db_Log_Curser = db_Log_Connection.cursor()

    try:
        db_Log_Curser.execute('INSERT INTO `' + Log_db + '`.`SystemLog` (LogLevel, Source, Header, Text) VALUES("' + Log_Level + '", "' + Log_Source + '", "' + Log_Header + '", "' + Log_Text + '");')
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # 1146 = Table is missing
        if e[0] == 1146:
            try:
                db_Log_Curser.execute("CREATE TABLE `" + Log_db + "`.`SystemLog` (`id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, `LogLevel` varchar(10) NOT NULL, `Source` varchar(75) NOT NULL, `Header` varchar(75) NOT NULL, `Text` varchar(250) NOT NULL, PRIMARY KEY (`id`))")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                print e
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    # FIX add some error handling here
                    print "DB WTF ERROR 2: " + str(e)
                    print e

            # Try to write log again
            db_Log_Curser.execute('INSERT INTO `' + Log_db + '`.`SystemLog` (LogLevel, Source, Header, Text) VALUES("' + Log_Level + '", "' + Log_Source + '", "' + Log_Header + '", "' + Log_Text + '");')
        else:
            # FIX add some error handling here
            print "DB WTF ERROR:" + str(e)
    finally:
        db_Log_Curser.execute("SELECT count(*) FROM SystemLog")
        Rows_Number_Of = db_Log_Curser.fetchone()

        if Rows_Number_Of[0] > Log_Length_System:
            Rows_To_Delete = Rows_Number_Of[0] - int(Log_Length_System)
            # Limit the max ammount of rows to delete to 250 to prevent the log from getting cleaned if a lot of log threads is spawned at the same time
            if Rows_To_Delete > 250:
                Rows_To_Delete = 250
            db_Log_Curser.execute("DELETE FROM `" + Log_db + "`.SystemLog ORDER BY id LIMIT " + str(Rows_To_Delete))
            Log("Debug", "Dobby", "db", "History Length reached, deleting " + str(Rows_To_Delete) + " rows for Table: SystemLog")

    Close_db(db_Log_Connection, db_Log_Curser)


def Log_Level_Check(Log_Source, Log_Level):

    Log_Level = Log_Level.lower()
    Check_Level = Log_Level_System

    Known_Levels_Dict = {'KeepAliveMonitor': Log_Level_KeepAliveMonitor, 'MQTTConfig': Log_Level_MQTTConfig, 'MQTTFunctions': Log_Level_MQTTFunctions, 'MQTT': Log_Level_MQTT, 'Log Trigger': Log_Level_Log_Trigger, 'Mail Trigger': Log_Level_Mail_Trigger, 'Spammer': Log_Level_Spammer, 'APC Monitor': Log_Level_APC_Monitor}

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


# ---------------------------------------- Database ----------------------------------------
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


# ---------------------------------------- MQTT ----------------------------------------
def MQTT_KeepAlive_Start(MQTT_Client):
    # FIX - Cahange keepalive source id db
    Log("Info", "Dobby", "MQTT KeepAlive", "Starting KeepAlive at interval: " + str(MQTT_KeepAlive_Interval))

    KeepAlive_Publish_Dict = {}

    while True:

        Uptime_MS = datetime.datetime.now() - Start_Time
        Uptime_MS = (Uptime_MS.days * 86400000) + (Uptime_MS.seconds * 1000) + (Uptime_MS.microseconds / 1000)

        KeepAlive_Publish_Dict["Hostname"] = "Dobby"
        KeepAlive_Publish_Dict["Uptime"] = Uptime_MS
        KeepAlive_Publish_Dict["FreeMemory"] = psutil.virtual_memory()[1]
        KeepAlive_Publish_Dict["Software"] = Version

        Log("Debug", "Dobby", "MQTT KeepAlive", "Ping")
        MQTT_Client.publish(System_Header + "/KeepAlive/Dobby", payload=json.dumps(KeepAlive_Publish_Dict), qos=0, retain=False)

        time.sleep(int(MQTT_KeepAlive_Interval))
        if MQTT_Client.Connected is False:
            Log("Warning", "Dobby", "MQTT KeepAlive", "MQTT Connection lost quitting")
            return


def MQTT_Subscribe_To(MQTT_Client, Topic):
    Log("Info", "Dobby", "MQTT", "Subscribing to topic: " + Topic)
    MQTT_Client.subscribe(Topic)


def MQTT_On_Connect(MQTT_Client, userdata, flags, rc):

    MQTT_Client.Connected = True
    Log("Debug", "Dobby", "MQTT", "Connected to broker " + MQTT_Broker + " with result code " + str(rc))

    for Topic, Callback in dict(MQTT_Topic_Dict).iteritems():
        MQTT_Subscribe_To(MQTT_Client, Topic)

        MQTT_Client.message_callback_add(Topic, MQTT_On_Message_Callback)

    # Monitor Agent
    # MonitorAgent_init()
    # MonitorAgent_Subscribe()

    # Mail_Trigger
    Mail_Trigger_Subscribe()

    # MQTT KeepAlive
    # FIX - CHANGE KEEPALIVE TIMER SOURCE IN DB
    KeepAlive_Thread = threading.Thread(target=MQTT_KeepAlive_Start, kwargs={"MQTT_Client": MQTT_Client})
    KeepAlive_Thread.daemon = True
    KeepAlive_Thread.start()


def MQTT_On_Disconnect(MQTT_Client, userdata, rc):
    MQTT_Client.Connected = False
    Log("Warning", "Dobby", "MQTT", "Disconnected from broker : " + str(MQTT_Broker))


def MQTT_On_Log(MQTT_Client, userdata, level, buf):

    # Log level check
    if level == 16:
        if Log_Level_MQTT == "debug":
            Log("Debug", "MQTT", "Message", buf)

    else:
        Log("Warning", "MQTT", "Message", buf)


# ---------------------------------------- Message_Check ----------------------------------------
def Message_Check(Topic, Payload, Retained):

    # Check for Mail_Trigger message
    for i in range(len(Mail_Trigger_Subscribe_List)):
        if Topic in Mail_Trigger_Subscribe_List[i]['Targets']:
            Trigger_Message_Check(Topic, Payload, Retained, Mail_Trigger_Subscribe_List[i]['id'])


# ---------------------------------------- On_MQTT_Message ----------------------------------------
def On_MQTT_Message(mosq, obj, msg):
    Msg_Thread = threading.Thread(target=Message_Check, kwargs={"Topic": msg.topic, "Payload": msg.payload, "Retained": msg.retain})
    Msg_Thread.daemon = True
    Msg_Thread.start()


# ---------------------------------------- MQTT_SQL ----------------------------------------
def MQTT_SQL(Payload):

    Payload = Payload.split("&")

    db_Connection = Open_db("")
    db_Curser = db_Connection.cursor()

    db_Curser.execute(Payload[1])
    db_Resoult = db_Curser.fetchone()

    Close_db(db_Connection, db_Curser)

    MQTT_Client.publish(Payload[0], str(db_Resoult[0]), qos=0, retain=False)


# ---------------------------------------- MQTT Commands ----------------------------------------
def MQTT_Commands(Topic, Payload):
    Topic = Topic.replace(System_Header + "/Commands/Dobby/", "")

    Log("Debug", "MQTTCommands", "Request", Topic + " - " + Payload)

    if "Settings" in Topic:
        MQTT_Config(Payload)
        return

    elif "Config" in Topic:
        MQTT_Config_New(Payload)
        # MQTT_Config(Payload)
        return

    # Rewrite for supervistor
    elif "Power" in Topic:
        # Power_Thread = threading.Thread(target=Power, kwargs={"Payload": Payload})
        # Power_Thread.daemon = True
        # Power_Thread.start()
        return

    elif "KeepAliveMonitor" in Topic:
        MQTT_Commands_KeepAliveMontor(Topic, Payload)
        return

    elif Topic in "Test":
        Log("Test", "MQTTCommands", "Executing", Topic + " - " + Payload)
        return

    elif Topic in "MQTTSQL":
        MQTT_SQL(Payload)
        return

    Log("Warning", "MQTTCommands", "Request", Topic + " - " + Payload + " - Not found")


def MQTT_Commands_KeepAliveMontor(Topic, Payload):
    if "Show" in Payload:
        Log("Info", "MQTTCommands", "Executing", Topic + " - " + Payload)
        MQTT_KeepAlive_Show()
        return


# ---------------------------------------- MQTT Config ----------------------------------------
def MQTT_Config_New(Payload):
    if ";" in Payload:
        Payload = Payload.replace(";", "")

    Payload = Payload.split(",")

    Request_Type = "MQTT"

    # Check if UDP config have been requested
    UDP_Request = False
    
    try:
        if Payload[2]:
            UDP_Request = True
            if Payload[2] == "FTP":
                Request_Type = "FTP"
            elif Payload[2] == "UDP":
                Request_Type = "UDP"
            else:
                Log("Warning", "MQTTConfig", "Request", "Unknown request type:" + Request_Type)
                return
    except ValueError and IndexError:
        pass

    db_FSCJ_Connection = Open_db("Dobby")
    db_FSCJ_Curser = db_FSCJ_Connection.cursor()

    Log("Debug", "MQTTConfig", "Request", Payload[0])

    try:
        db_FSCJ_Curser.execute("SELECT Config_ID FROM Dobby.DeviceConfig WHERE Hostname='" + Payload[0] + "';")
        Config_ID_Value = db_FSCJ_Curser.fetchone()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "MQTTConfig", "Missing", Payload[0])
        else:
            Log("Error", "MQTTConfig", "db error", str(e[0]))
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
            Log("Debug", "MQTTConfig", "Config up to date", Payload[0] + " id: " + Payload[1])
            return

    # Get config
    try:
        db_FSCJ_Curser.execute("SELECT DISTINCT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='Dobby' AND `TABLE_NAME`='DeviceConfig';")
        Config_Name_List = db_FSCJ_Curser.fetchall()

        db_FSCJ_Curser.execute("SELECT * FROM DeviceConfig WHERE Hostname='" + Payload[0] + "';")
        Config_Value_List = db_FSCJ_Curser.fetchall()

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "MQTTConfig", "Missing", Payload[0])
        else:
            Log("Error", "MQTTConfig", "db error", str(e[0]))
            Close_db(db_FSCJ_Connection, db_FSCJ_Curser)
            return

    Close_db(db_FSCJ_Connection, db_FSCJ_Curser)

    # Compare ConfigID
    if Config_Name_List is None:
        Log("Warning", "MQTTConfig", "Missing", "ConfigID for Hostname: " + Payload[0])

    Log("Debug", "MQTTConfig", "Config outdated", Payload[0] + " Device Config ID: " + Payload[1] + " Config ID: " + str(Config_ID_Value[0]))

    if Config_Name_List is () or Config_Value_List is ():
        Log("Error", "MQTTConfig", "Config Empthy", Payload[0])
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
        Log("Info", "MQTTConfig", "Publish Config", Payload[0])
        # Publish json
        MQTT_Client.publish(System_Header + "/Config/" + Payload[0], payload=json.dumps(Config_Dict) + ";", qos=0, retain=False)
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
        MQTT_Client.publish(System_Header + "/Commands/" + str(Payload[0]) + "/Power", payload="Reboot" + ";", qos=0, retain=False)


def MQTT_Config(Payload):
    if ";" in Payload:
        Payload = Payload.replace(";", "")

    Payload = Payload.split(",")

    db_MC_Connection = Open_db("Dobby")
    db_MC_Curser = db_MC_Connection.cursor()

    Config_ID_Value = 0

    Log("Debug", "MQTTConfig", "Request", Payload[0])

    try:
        db_MC_Curser.execute("SELECT Value FROM DeviceConfig WHERE Device='" + Payload[0] + "' AND Type='System' AND Name='ConfigID';")
        Config_ID_Resoult = db_MC_Curser.fetchone()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "MQTTConfig", "Missing", Payload[0])
        else:
            Log("Error", "MQTTConfig", "db error", str(e[0]))
        return

        # Compare ConfigID
    if Config_ID_Resoult is None:
        Log("Warning", "MQTTConfig", "Missing", "ConfigID for Hostname: " + Payload[0])
    else:
        if Config_ID_Resoult[0] == Payload[1]:
            Log("Debug", "MQTTConfig", "Config up to date", Payload[0] + " id: " + Payload[1])
            return

    Log("Debug", "MQTTConfig", "Config outdated", Payload[0])

    # Get config
    try:
        db_MC_Curser.execute("SELECT Type, Name, Value FROM DeviceConfig WHERE Device='" + Payload[0] + "';")
        Config_List = db_MC_Curser.fetchall()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "MQTTConfig", "Missing", Payload[0])
        else:
            Log("Error", "MQTTConfig", "db error", str(e[0]))
        return

    if Config_List is ():
        Log("Error", "MQTTConfig", "Config Empthy", Payload[0])
        return

    Log("Info", "MQTTConfig", "Publish Config", Payload[0])

    for Row in Config_List:
        # "System" is for system use and not config for the device
        if "System" in Row[0]:
            if "ConfigID" == Row[1]:
                Config_ID_Value = Row[2]
        else:
            MQTT_Config_Send(db_MC_Curser, Payload[0], Row[0], Row[1], Row[2])

        # FIX - Publish delay not working
        time.sleep(MQTT_Publish_Delay)

    MQTT_Config_Send(db_MC_Curser, Payload[0], "Config", "ID", Config_ID_Value)

    Close_db(db_MC_Connection, db_MC_Curser)


def MQTT_Config_Send(db_MC_Curser, Hostname, Type, Name, Value):

    Send_Value = Value
    MQTT_Topic = None

    try:
        db_MC_Curser.execute("SELECT Value FROM `Dobby`.`MQTTTargets` WHERE Type='" + Type + "' AND Name='" + Name + "';")
        MQTT_Topic = db_MC_Curser.fetchone()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print e
        return

    if MQTT_Topic is None:
        Log("Error", "MQTTTargets", "Unknown target", "Hostname: " + Hostname + "Type: " + Type + "Name: " + Name)
        return

    MQTT_Topic = MQTT_Topic[0]

    MQTT_Topic = MQTT_Topic.replace("{System_Header}", System_Header)
    MQTT_Topic = MQTT_Topic.replace("{Hostname}", Hostname)

    # Changing Pin Name to Pin Number
    if "Pins" in Name and "D" in Value:
        Send_Value = Send_Value.replace("D0", "16")
        Send_Value = Send_Value.replace("D1", "5")
        Send_Value = Send_Value.replace("D2", "4")
        Send_Value = Send_Value.replace("D3", "0")
        Send_Value = Send_Value.replace("D4", "2")
        Send_Value = Send_Value.replace("D5", "14")
        Send_Value = Send_Value.replace("D6", "12")
        Send_Value = Send_Value.replace("D7", "13")
        Send_Value = Send_Value.replace("D8", "15")
        Send_Value = Send_Value.replace("A0", "17")

    Send_Value = Send_Value.replace(", ", ",")

    MQTT_Client.publish(MQTT_Topic, payload=Send_Value + ";", qos=0, retain=False)


# ---------------------------------------- APC_Monitor ----------------------------------------
class APC_Monitor:

    # How often does esch APC_Monitor read write to the db (sec)
    db_Refresh_Rate = 1.5
    Loop_Delay = 0.500

    def __init__(self):
        # Log event
        Log("Info", "APC Monitor", "Checker", "Starting")

        self.APC_Monitor_Dict = {}

        # Start checker thread
        APC_Monitor_Thread = threading.Thread(target=self.Checker, kwargs={})
        APC_Monitor_Thread.daemon = True
        APC_Monitor_Thread.start()

    def Checker(self):

        while True:
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.APC_Monitor WHERE Enabled='1'")
            APC_Monitor_db = db_Curser.fetchall()

            Close_db(db_Connection, db_Curser)

            for i in APC_Monitor_db:
                # i[0] = APC_Monitor db id
                if i[0] not in self.APC_Monitor_Dict:
                    self.APC_Monitor_Dict[i[0]] = self.Agent(i[0])
                    Log("Debug", "APC Monitor", "Checker", "Starting: " + self.APC_Monitor_Dict[i[0]].Name)

                else:
                    # Change to APC_Monitor
                    if str(self.APC_Monitor_Dict[i[0]].Last_Modified) != str(i[1]):
                        Log("Debug", "APC Monitor", "Checker", "Change found in: " + self.APC_Monitor_Dict[i[0]].Name + " restarting agent")
                        # Wait for agent to close db connection
                        while self.APC_Monitor_Dict[i[0]].OK_To_Kill is False:
                            time.sleep(0.100)

                        # Delete agent
                        Log("Debug", "APC Monitor", "Checker", "Deleting: " + self.APC_Monitor_Dict[i[0]].Name)
                        del self.APC_Monitor_Dict[i[0]]
                        # Start agent again
                        self.APC_Monitor_Dict[i[0]] = self.Agent(i[0])
                        Log("Debug", "APC Monitor", "Checker", "Starting: " + self.APC_Monitor_Dict[i[0]].Name)

                # Some random delay not to kick off all the spammers at one
                time.sleep(random.uniform(0.150, 0.500))

            time.sleep(APC_Monitor.db_Refresh_Rate)
        Log("Debug", "APC Monitor", "Checker", "Stopped: " + self.APC_Monitor_Dict[i[0]].Name)

    class Agent:
        def __init__(self, id):

            self.id = int(id)

            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT Name, Enabled, Tags, Refresh_Rate, Max_Entries, FTP_URL, Next_Collect, Last_Modified FROM Dobby.APC_Monitor WHERE id='" + str(self.id) + "'")

            APC_Monitor_Info = db_Curser.fetchone()

            Close_db(db_Connection, db_Curser)

            self.Name = str(APC_Monitor_Info[0])

            # Canget log event before now if you want to use name
            Log("Debug", "APC Monitor", self.Name, 'Initializing')

            # Check if FTP URL is valid
            if 'ftp://' and ':' and '@' and "." in APC_Monitor_Info[5]:
                self.Enabled = bool(APC_Monitor_Info[1])
                self.Tags = APC_Monitor_Info[2]
                self.Refresh_Rate = float(APC_Monitor_Info[3] * 60)
                self.Max_Entries = APC_Monitor_Info[4]
                # self.FTP_URL = APC_Monitor_Info[5] -- No reason to save this to memory
                self.Next_Collect = APC_Monitor_Info[6]
                self.Last_Modified = APC_Monitor_Info[7]

                # [6:] removed 'ftp://'
                try:
                    self.Username = APC_Monitor_Info[5][6:].split(":", 1)[0]
                    self.Password = APC_Monitor_Info[5][6:].split("@", 1)[0].split(":", 1)[1]
                    self.FTP_Address = APC_Monitor_Info[5][6:].split("/", 1)[0].split("@", 1)[1]
                    self.File_Name = APC_Monitor_Info[5][6:].split("/", 1)[1]
                except IndexError or ValueError:
                    # FIX - Kill the agent here and make it retrn false so you can rmeove it from the dict above
                    Log("Error", "APC Monitor", self.Name, 'Invalid FTP URL: ' + str(APC_Monitor_Info[5]))
                    return

                self.OK_To_Kill = True
                self.Kill = False

                Log("Debug", "APC Monitor", self.Name, 'Initialization compleate')

                self.Start()

            else:
                Log("Error", "APC Monitor", self.Name, 'Invalid FTP URL: ' + str(APC_Monitor_Info[5]))

        # ========================= Agent - Start =========================
        def Start(self):
            APC_Monitor_Thread = threading.Thread(target=self.Run, kwargs={})
            APC_Monitor_Thread.daemon = True
            APC_Monitor_Thread.start()

        # ========================= Agent - Read Data =========================
        def Get_Data(self, db_Curser):
            Log("Debug", "APC Monitor", self.Name, "Starting date collection")

            # Create FTP Connection
            FTP_Connection = ftplib.FTP(self.FTP_Address)
            # Open FTP Connection
            FTP_Connection.login(self.Username, self.Password)
            # Create virtual file in memory
            FTP_Memory_File = StringIO()

            # Download file to memory
            try:
                FTP_Connection.retrbinary(str('RETR ' + str(self.File_Name)), FTP_Memory_File.write)
            except ftplib.all_errors as e:
                Log("Error", "APC Monitor", self.Name, "FTP error: " + str(e))
                return

            # Close FTP Connection
            FTP_Connection.quit()

            # Convert to string
            FTP_Memory_File = FTP_Memory_File.getvalue()

            # Remove \r
            FTP_Memory_File = FTP_Memory_File.replace("\r", "")

            # # Remove \t
            # FTP_Memory_File = FTP_Memory_File.replace("\t", "")

            # Split the data into Device Info and Data
            FTP_Memory_File = FTP_Memory_File.split('SrcSel(0=A,1=B)\n')

            # Store Device Info in variable
            Device_Info = FTP_Memory_File[0]
            # Convert device info to list
            Device_Info = Device_Info.split('\n')

            # Save the Data to FTP_Memory_File variable
            FTP_Memory_File = FTP_Memory_File[1]

            i = 0

            Device_Name = ''
            Last_Entry = ''

            # Remove the first lines that contains device information and collect the needed information
            for i in range(8):
                Info = Device_Info.pop(0)
                # Get device Name
                if i == 4:
                    Device_Name = Info.split('\t')
                    Device_Name = Device_Name[2]

            Last_Entry = ''

            # Find last entry for device
            try:
                db_Curser.execute("SELECT DateTime FROM `" + Log_db + "`.`APC_Monitor` WHERE `Name`='" + Device_Name + "' ORDER BY DateTime DESC LIMIT 1;")
                Last_Entry = db_Curser.fetchone()

            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # 1146 = Table missing
                if e[0] == 1146:
                    Log("Info", "APC Monitor", "db", "APC Monitor Table missing creating it")
                    try:
                        db_Curser.execute("CREATE TABLE `" + Log_db + "`.`APC_Monitor` ( `id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, `Name` varchar(45) NOT NULL, `Hertz A` decimal(2,0) NOT NULL, `Hertz B` decimal(2,0) NOT NULL, `Vin A` decimal(3,0) NOT NULL, `Vin B` decimal(3,0) NOT NULL, `I Out` decimal(3,1) NOT NULL, `IO Max` decimal(3,1) NOT NULL, `IO Min` decimal(3,1) NOT NULL, `Active Output` tinyint(2) NOT NULL, PRIMARY KEY (`id`), UNIQUE KEY `id_UNIQUE` (`id`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;")
                        # Try getting last entry for device again
                        db_Curser.execute("SELECT DateTime FROM `" + Log_db + "`.APC_Monitor WHERE `Name`='" + Device_Name + "' ORDER BY DateTime DESC LIMIT 1;")
                        Last_Entry = db_Curser.fetchone()

                    except (MySQLdb.Error, MySQLdb.Warning) as e:
                        # Error 1050 = Table already exists
                        if e[0] != 1050:
                            Log("Fatal", "APC Monitor", Device_Name, "Unable to create log db table, failed with error: " + str(e))
                            return
                        else:
                            Log("Error", "APC Monitor", Device_Name, "db error: " + str(e))

            if Last_Entry is not None:
                Last_Entry = Last_Entry[0]
            else:
                # Set some 'random' time to check against
                Last_Entry = datetime.datetime.strptime("09/24/1984 03:00:00", '%m/%d/%Y %H:%M:%S')

            # For log info later
            Entried_Added = 0

            # Check if last datetime from db is in file
            try:
                Last_Entry_Index = FTP_Memory_File.index(Last_Entry.strftime('%m/%d/%Y\t%H:%M:%S'))
            # If ValueError then the last entry is not in file
            except ValueError:
                Last_Entry_Index = len(FTP_Memory_File)

            # Remove everything up untill last matching datetime entry
            FTP_Memory_File = FTP_Memory_File[0:Last_Entry_Index]

            # Convert to list
            FTP_Memory_File = FTP_Memory_File.split("\n")

            # Remove empth line at beginning of file
            # FTP_Memory_File.pop(0)
            # print "after"
            # print FTP_Memory_File
            # return

            # Reverse the list so you stop when you find the entry thats in the db already
            for Line in reversed(FTP_Memory_File):

                # If empthy line do nothing
                if Line is "":
                    continue

                # Split the line into a list
                Entries = Line.split('\t')

                if Entries != ['']:
                    # Check if time string is as expected YYYY-MM-DD HH:MM:SS
                    if '/' in Entries[0] and ':' in Entries[1]:
                        Time_String = Entries[0] + str(" ") + Entries[1]
                    # If not then fuck it
                    else:
                        Log("Warning", "APC Monitor", self.Name, 'Invalid datetime detected make sure "Date Format" is set to " mm/dd/yyyy"')
                        return

                    Entry_Time = datetime.datetime.strptime(Time_String, '%m/%d/%Y %H:%M:%S')

                    if Entry_Time > Last_Entry:
                        Value_String = "'" + str(Entry_Time) + "', '" + str(Device_Name) + "' ,"

                        for x in range(2, 10):
                            Value_String = Value_String + "'" + str(Entries[x]) + "'"
                            if x != 9:
                                Value_String = Value_String + ", "

                        try:
                            db_Curser.execute("INSERT INTO `" + Log_db + "`.`APC_Monitor` (`DateTime`, `Name`, `Hertz A`, `Hertz B`, `Vin A`, `Vin B`, `I Out`, `IO Max`, `IO Min`, `Active Output`) VALUES (" + Value_String + ");")
                        except (MySQLdb.Error, MySQLdb.Warning) as e:
                            Log("Error", "APC Monitor", self.Name, "Unable to add entries - db error: " + str(e))
                            return

                        Entried_Added += 1

                    # The entries loaded is before last intry in db the quit
                    else:
                        print "Entry_Time"
                        print Entry_Time > Last_Entry
                        print "Entry_Time"
                        print Entry_Time
                        print type(Entry_Time)
                        print "Last_Entry"
                        print Last_Entry
                        print type(Last_Entry)
                        print "BREAK"
                        # break

                i = i + 1

            Log("Debug", "APC Monitor", self.Name, "Entried Added: " + str(Entried_Added))

        # ========================= Agent - Run =========================
        def Run(self):

            Log("Info", "APC Monitor", self.Name, "Running")
            # Start eternal loop
            while True:
                # Check if its time to get information
                if self.Next_Collect < datetime.datetime.now():
                    Log("Debug", "APC Monitor", self.Name, "Refresh Started")

                    self.Next_Collect = datetime.datetime.now() + timedelta(seconds=self.Refresh_Rate)

                    self.OK_To_Kill = False

                    db_Connection = Open_db("Dobby")
                    db_Curser = db_Connection.cursor()

                    self.Get_Data(db_Curser)

                    db_Curser.execute("UPDATE `Dobby`.`APC_Monitor` SET `Next_Collect`='" + str(self.Next_Collect) + "', `Last_Collect`='" + str(datetime.datetime.now()) + "' WHERE id = '" + str(self.id) + "';")

                    Close_db(db_Connection, db_Curser)

                    self.OK_To_Kill = True

                    Log("Debug", "APC Monitor", self.Name, "Refresh Compleate")
                    time.sleep(APC_Monitor.Loop_Delay)

                while self.Next_Collect >= datetime.datetime.now():
                    time.sleep(APC_Monitor.Loop_Delay)

                if self.Kill is True:
                    quit()


# ---------------------------------------- Log_Trigger ----------------------------------------
def Log_Trigger_Init():
    # Log("Info", "Log Trigger", "Fix CODE", 'Initialization compleate')

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


def Log_Trigger(Trigger_Info, Payload, Retained):

    if Retained is 0:
        # json value
        if Is_json(Payload) is True:
            # Create json
            root = json.loads(Payload)
            # Split headers into seperate topics
            for json_Log_Source, json_Log_Value in root.items():
                Log_Trigger_Log_Value(Trigger_Info, json_Log_Value, json_Tag=json_Log_Source)
                # None json value
        else:
            Log_Trigger_Log_Value(Trigger_Info, Payload)


def Log_Trigger_Log_Value(Trigger_Info, Value, json_Tag=''):

    Log("Debug", "Log Trigger", "Logging", "Value: " + str(Value) + " json_Tag: " + str(json_Tag))

    db_Connection = Open_db()
    db_Curser = db_Connection.cursor()

    # Make sure Log_Value is string
    Value = str(Value)
    # Remove the ";" at the end if there
    if Value[-1:] == ";":
        Value = Value[:-1]

    # Change Last_Trigger
    db_Curser.execute("UPDATE `Dobby`.`Log_Trigger` SET `Last_Trigger`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(Trigger_Info['id']) + "';")

    # Log Value
    try:
        db_Curser.execute("INSERT INTO `" + Log_db + "`.`Log_Trigger` (Name, json_Tag, Tags, Value) Values('" + Trigger_Info['Name'] + "','" + str(json_Tag) + "' , '" + str(Trigger_Info['Tags']) + "', '" + Value + "');")
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # Table missing, create it
        if e[0] == 1146:
            Log("Info", "Log Trigger", "db", "Log Trigger Table missing creating it")
            try:
                db_Curser.execute("CREATE TABLE `" + Log_db + "`.`Log_Trigger` (`id` int(11) NOT NULL AUTO_INCREMENT, `Name` varchar(75) NOT NULL, `json_Tag` varchar(75) NOT NULL, `Tags` varchar(75) DEFAULT NULL, `Value` varchar(75) NOT NULL, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`))ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;")
                # Try logging the message again
                db_Curser.execute("INSERT INTO `" + Log_db + "`.`Log_Trigger` (Name, json_Tag, Tags, Value) Values('" + Trigger_Info['Name'] + "','" + str(json_Tag) + "' , '" + str(Trigger_Info['Tags']) + "', '" + Value + "');")

            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    Log("Fatal", "Log Trigger", Trigger_Info['Name'], "Unable to create log db table, failed with error: " + str(e))
                    return
        else:
            Log("Critical", "Log Trigger", "db", "Unable to log message. Error: " + str(e))
            return

    # Delete rows > max
    db_Curser.execute("SELECT count(*) FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + Trigger_Info['Name'] + "' AND json_Tag='" + str(json_Tag) + "';")
    Rows_Number_Of = db_Curser.fetchall()

    if Rows_Number_Of[0][0] > int(Trigger_Info['Max_Entries']):
        Rows_To_Delete = Rows_Number_Of[0][0] - int(Trigger_Info['Max_Entries'])
        print ("DELETE FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + Trigger_Info['Name'] + "' AND json_Tag='" + str(json_Tag) + "' ORDER BY 'DateTime' LIMIT " + str(Rows_To_Delete) + ";")
        db_Curser.execute("DELETE FROM `" + Log_db + "`.`Log_Trigger` WHERE Name='" + Trigger_Info['Name'] + "' AND json_Tag='" + str(json_Tag) + "' ORDER BY 'DateTime' LIMIT " + str(Rows_To_Delete) + ";")
        Log("Debug", "Dobby", Trigger_Info['Name'], "History Length reached, deleting " + str(Rows_To_Delete))

    Log("Debug", "Log Trigger", Trigger_Info['Name'], "Valure capured: " + Value)

    Close_db(db_Connection, db_Curser)


# ---------------------------------------- Spammer ----------------------------------------
class Spammer:

    # How often does esch spammer read write to the db (sec)
    db_Refresh_Rate = 1.5
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

                    self.Next_Ping = datetime.datetime.now() + timedelta(seconds=self.Interval)

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


# ---------------------------------------- KeepAlive Monitor ----------------------------------------
def KeepAlive_Monitor(Topic, Payload):
    db_KL_Connection = Open_db(Log_db)
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

    if root_KL["Hostname"] != "Dobby":
        # Spawn thread for Auto Update Check
        AU_Thread = threading.Thread(target=Auto_Update, kwargs={"Hostname": root_KL["Hostname"], "IP": root_KL["IP"], "Current_SW": root_KL["Software"], "Hardware": root_KL.get("Hardware", "Unknown")})
        AU_Thread.daemon = True
        AU_Thread.start()

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
    db_KL_Curser.execute("SELECT COUNT(*) FROM `" + Log_db + "`.`KeepAliveMonitor` WHERE Device='" + root_KL["Hostname"] + "';")
    Current_Log_Length = db_KL_Curser.fetchone()

    if Current_Log_Length[0] > Log_Length_KeepAliveMonitor:
        Rows_To_Delete = Current_Log_Length[0] - Log_Length_KeepAliveMonitor
        Log("Debug", "KeepAliveMonitor", "db", "Log Length reached, deleting " + str(Rows_To_Delete))
        db_KL_Curser.execute("DELETE FROM `" + Log_db + "`.KeepAliveMonitor WHERE Device='" + root_KL["Hostname"] + "' ORDER BY id LIMIT " + str(Rows_To_Delete) + ";")

    Close_db(db_KL_Connection, db_KL_Curser)


def MQTT_KeepAlive_Show():
    db_KAM_Connection = Open_db(Log_db)
    db_KAM_Curser = db_KAM_Connection.cursor()

    db_KAM_Curser.execute("SELECT Distinct Device, MAX(LastKeepAlive), UpFor, FreeMemory, SoftwareVersion FROM `" + Log_db + "`.KeepAliveMonitor Group BY Device LIMIT 10000;")
    Device_List = db_KAM_Curser.fetchall()

    Payload = "Device\tStatus\t\tLast KeepAlive\tUp For\t\tFree Memory\t\tSoftware Version\n"

    for Device_Info in Device_List:

        # Name
        Payload = Payload + Device_Info[0] + "\t"

        # Status
        # # Dobby
        if Device_Info[0] == "Dobby":
            if datetime.timedelta(seconds=MQTT_KeepAlive_Interval) > datetime.datetime.now() - Device_Info[1]:
                Payload = Payload + "OK" + "\t\t"
            else:
                Payload = Payload + "Missing" + "\t\t"

        # # Devices
        else:
            Interval = ""
            State = ""
            try:
                db_KAM_Curser.execute('SELECT MQTT_KeepAlive_Interval FROM Dobby.DeviceConfig WHERE Hostname="' + Device_Info[0] + '";')
                Interval = db_KAM_Curser.fetchone()
            except (MySQLdb.Error, MySQLdb.Warning):
                State = "Config Error"

            if Interval is None:
                State = "Config Error"

            elif State != "Config Error":
                # Adding a 5 sec grace periode to acount for systel lag
                if datetime.timedelta(seconds=Interval[0] + 5) > datetime.datetime.now() - Device_Info[1]:
                    State = "OK"
                else:
                    State = "Missing"

            Payload = Payload + State + "\t"

        # Last KeepAlive
        Payload = Payload + str(datetime.datetime.strptime(str(Device_Info[1]), '%Y-%m-%d %H:%M:%S')) + "\t"

        # Up For
        Payload = Payload + str(Device_Info[2]) + "\t\t"

        # Free Memory
        Payload = Payload + str(Device_Info[3]) + "\t\t"

        # Software Version
        if str(Device_Info[4]) == "0.0":
            Payload = Payload + "Unknown" + "\n"
        else:
            Payload = Payload + str(Device_Info[4]) + "\n"

    Close_db(db_KAM_Connection, db_KAM_Curser)

    MQTT_Client.publish(System_Header + "/System/Dobby/KeepAliveMonitor", payload=Payload, qos=0, retain=False)


# ---------------------------------------- Action Trigger ----------------------------------------
class Action_Trigger():
    # How often the db is cheched for changes
    Refresh_Rate = 1.5

    Active_Triggers = {}

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

            # Close db connection
            Close_db(db_Connection, db_Curser)

            # Sleep till next check
            time.sleep(self.Refresh_Rate)
    

    def Start_Trigger(self, id):

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
        MQTT_Add_Sub_Topic(str(Trigger_Info[1]), 'Action Trigger')
        # Subscribe
        MQTT_Client.subscribe(str(Trigger_Info[1]))
        # Register callbacks
        MQTT_Client.message_callback_add(str(Trigger_Info[1]), MQTT_On_Message_Callback)


    def Restart_Trigger(self):
        print "GEN KYK"
        # Log("Debug", "Action Trigger", str(Action_Info[i][2]), "Change detected, restarting")


    @classmethod
    def On_Message(cls):
        print "MESSAGE"
        print cls
        
        
# ---------------------------------------- Build_Trigger_Message ----------------------------------------
def Build_Trigger_Message(Body, Trigger_Info, Payload):

    # Name = Trigger_Info[0]
    # Type = Trigger_Info[1]
    # Alert_State = Trigger_Info[2]
    MQTT_Payload_Clear = Trigger_Info[3]
    MQTT_Payload_Trigger = Trigger_Info[4]
    Alert_Target = Trigger_Info[5]
    Alert_Subject = Trigger_Info[6]
    Alert_Payload_Clear = Trigger_Info[7]
    Alert_Payload_Trigger = Trigger_Info[8]

    if Body == 0:
        Body = Alert_Payload_Clear
    if Body == 1:
        Body = Alert_Payload_Trigger

    Trigger_Message = MIMEMultipart()
    Trigger_Message['From'] = Mail_Trigger_SMTP_Sender
    Trigger_Message['To'] = Alert_Target
    Trigger_Message['Subject'] = Alert_Subject

    Body = str(Body)

    if "{Payload}" in Body:
        Body = Body.replace("{Payload}", str(Payload))

    if "{Clear}" in Body:
        Body = Body.replace("{Clear}", str(MQTT_Payload_Clear))

    if "{Trigger}" in Body:
        Body = Body.replace("{Trigger}", str(MQTT_Payload_Trigger))

    Trigger_Message.attach(MIMEText(Body, 'plain'))

    return Trigger_Message


def Send_Email(To, Message):

    # Remove any spaces
    To = To.replace(" ", "")

    Target_List = []

    # Multiple targets
    if "," in To:
        Target_List = To.split(",")

    # Single target
    else:
        Target_List.append(To)

    # Connect to mail server
    server = smtplib.SMTP(Mail_Trigger_SMTP_Server, Mail_Trigger_SMTP_Port)
    server.starttls()
    server.login(Mail_Trigger_SMTP_Username, Mail_Trigger_SMTP_Password)

    # Send Email
    for To_Email in Target_List:
        server.sendmail(Mail_Trigger_SMTP_Sender, To_Email, str(Message))

    # Disconnect from mail server
    server.quit()


def Trigger_Message_Check(Topic, Payload, Retained, Trigger_id):
    # Dont trigger Mail_Trigger on retained messages
    # PS: A message send after connecting is not counted as retained even if it is
    if Retained is 0:
        db_AMC_Connection = Open_db("Dobby")
        db_AMC_Curser = db_AMC_Connection.cursor()

        db_AMC_Curser.execute("set autocommit = 1")

        db_AMC_Curser.execute("SELECT Name, Type, Alert_State, MQTT_Payload_Clear, MQTT_Payload_Trigger, Alert_Target, Alert_Subject, Alert_Payload_Clear, Alert_Payload_Trigger FROM Dobby.Mail_Trigger WHERE id='" + str(Trigger_id) + "';")
        Trigger_Info = db_AMC_Curser.fetchone()

        Name = Trigger_Info[0]
        Type = Trigger_Info[1]
        Alert_State = Trigger_Info[2]
        MQTT_Payload_Clear = Trigger_Info[3]
        MQTT_Payload_Trigger = Trigger_Info[4]
        Alert_Target = Trigger_Info[5]
        # Alert_Subject = Trigger_Info[6]
        Alert_Payload_Clear = Trigger_Info[7]
        Alert_Payload_Trigger = Trigger_Info[8]

        # Find out what to do
        Action = 2
        # 0 = Clear
        # 1 = Trigger
        # 2 = In-between

        Trigger_Change = False

        if float(MQTT_Payload_Clear) == float(MQTT_Payload_Trigger):
            Log("Error", "Mail_Trigger", str(Name), 'Clear and Trigger payload is the same value')
            Close_db(db_AMC_Connection, db_AMC_Curser)
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

        # Email Alert
        if Type == "Email":

            # Clear
            if Action == 0:
                # Check agains current alert state
                if Action == Alert_State:
                    Log("Debug", "Mail_Trigger", str(Name), 'Already cleared ignoring new clear value: ' + str(Payload))
                else:
                    Trigger_Change = True

                    # Send Email
                    Send_Email(Alert_Target, Build_Trigger_Message(0, Trigger_Info, Payload))
                    Log("Info", "Mail_Trigger", str(Name), 'Cleared at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Clear))

            # Trigger
            elif Action == 1:
                # Check agains current alert state
                if Action == Alert_State:
                    Log("Debug", "Mail_Trigger", str(Name), 'Already triggered ignoring new trigger value: ' + str(Payload))
                else:
                    Trigger_Change = True

                    # Send Email
                    Send_Email(Alert_Target, Build_Trigger_Message(0, Trigger_Info, Payload))
                    Log("Info", "Mail_Trigger", str(Name), 'Triggered at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Trigger))

            # In-between value
            elif Action == 2:
                Log("Debug", "Mail_Trigger", str(Name), 'In-between value received: ' + str(Payload))

        # MQTT Alert
        elif Type == "MQTT":

            # Clear
            if Action == 0:
                # Check agains current alert state
                if Action == Alert_State:
                    Log("Debug", "Mail_Trigger", str(Name), 'Already cleared ignoring new clear value: ' + str(Payload))
                else:
                    Trigger_Change = True

                    # Publish Message
                    MQTT_Client.publish(Alert_Target, payload=str(Alert_Payload_Clear) + ";", qos=0, retain=False)
                    Log("Info", "Mail_Trigger", str(Name), 'Cleared at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Clear))

            # Trigger
            elif Action == 1:
                # Check agains current alert state
                if Action == Alert_State:
                    Log("Debug", "Mail_Trigger", str(Name), 'Already triggered ignoring new trigger value: ' + str(Payload))
                else:
                    Trigger_Change = True

                    # Publish Message
                    MQTT_Client.publish(Alert_Target, payload=str(Alert_Payload_Trigger) + ";", qos=0, retain=False)
                    Log("Info", "Mail_Trigger", str(Name), 'Triggered at: ' + str(Payload) + " Target: " + str(MQTT_Payload_Trigger))

            # In-between value
            elif Action == 2:
                Log("Debug", "Mail_Trigger", str(Name), 'In-between value received: ' + str(Payload))

        if Trigger_Change is True:
            # Change Alert_State
            db_AMC_Curser.execute("UPDATE `Dobby`.`Mail_Trigger` SET `Alert_State`='" + str(Action) + "' WHERE `id`='" + str(Trigger_id) + "';")
            # Update Triggered_DateTime
            db_AMC_Curser.execute("UPDATE `Dobby`.`Mail_Trigger` SET `Triggered_DateTime`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(Trigger_id) + "';")

        Close_db(db_AMC_Connection, db_AMC_Curser)


def Trigger_On_Msg(mosq, obj, msg):
    Trigger_Msg_Thread = threading.Thread(target=Trigger_Message_Check, kwargs={"Topic": msg.topic, "Payload": msg.payload, "Retained": msg.retain})
    Trigger_Msg_Thread.daemon = True
    Trigger_Msg_Thread.start()


# Subscribes to topics for active agents ment to be run at MQTT Connect
def Mail_Trigger_Subscribe():

    db_AlSub_Connection = Open_db("Dobby")
    db_AlSub_Curser = db_AlSub_Connection.cursor()

    db_AlSub_Curser.execute("SELECT id, Name, MQTT_Target FROM Dobby.Mail_Trigger WHERE Enabled='1';")
    Mail_Trigger_List = db_AlSub_Curser.fetchall()

    Close_db(db_AlSub_Connection, db_AlSub_Curser)

    if Mail_Trigger_List is None:
        # FIX add log message
        print 'None'
        return

    #     id = 0
    #   Name = 1
    # Target = 2

    for i in range(len(Mail_Trigger_List)):

        # Add id and targets to dict for later use
        Mail_Trigger_Subscribe_List.append({'id': Mail_Trigger_List[i][0], 'Name': Mail_Trigger_List[i][1], 'Targets': Mail_Trigger_List[i][2].replace(" ", "").split(",")})

        for Target in Mail_Trigger_Subscribe_List[i]["Targets"]:
            Log("Info", "Mail_Trigger", str(Mail_Trigger_Subscribe_List[i]["Name"]), "Subscribing to topic: " + str(Target))
            # Subscribe
            # MQTT_Client.subscribe(str(Target))
            # Register callbacks
            # MQTT_Client.message_callback_add(str(Target), MQTT_On_Message_Callback)
            
            # Log Event
            Log("Debug", "Mail Trigger", str(Target), "Subscribing to: '" + str(Target) + "'")
            # Add topic to topic tict
            MQTT_Add_Sub_Topic(str(Target), 'Mail Trigger')
            # Subscribe
            MQTT_Client.subscribe(str(Target))
            # Register callbacks
            MQTT_Client.message_callback_add(str(Target), MQTT_On_Message_Callback)


# ---------------------------------------- Auto Update ----------------------------------------
def Auto_Update(Hostname, IP, Current_SW, Hardware):

    # FIX - Add system software update
    if Hostname == "Dobby":
        return

    # FIX CHECK IP AND RETURN IF NOT VALID

    # Open the config table and read device config
    db_AU_Connection = Open_db(Log_db)
    db_AU_Curser = db_AU_Connection.cursor()

    try:
        db_AU_Curser.execute("SELECT Auto_Update FROM Dobby.DeviceConfig where Hostname='" + Hostname + "' and Config_Active=1;")
        Config_AU_Value = db_AU_Curser.fetchone()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        if e[0] == 1146:
            Log("Warning", "AutoUpdate", "Missing Config", Hostname)
        else:
            Log("Error", "AutoUpdate", "db error", str(e[0]))
            Close_db(db_AU_Connection, db_AU_Curser)
            return

    Close_db(db_AU_Connection, db_AU_Curser)

    if Config_AU_Value is None:
        Log("Warning", "AutoUpdate", "Missing Config", Hostname)
        return

    if Config_AU_Value[0] is 0:
        Log("Debug", "AutoUpdate", "Disabled", Hostname)
        return

    # Check FS for firmware versions
    try:
        Firmware_Dir_List = os.listdir("/etc/Dobby/Firmware/" + Hardware + "/")
    except OSError as OS_Error:
        Log("Debug", "AutoUpdate", "Firmware Files", "Missing firmware dir")
        return

    Firmware_List = []

    # Add all file names to list so the list can be sorted and the highest firmware number selected
    for Firmware_Name in Firmware_Dir_List:
        Firmware_List.append(int(Firmware_Name.replace(".bin", "")))

    if Current_SW < max(Firmware_List):
        Log("Info", "AutoUpdate", "Updating", Hostname + " From: " + str(Current_SW) + " To:" + str(max(Firmware_List)))

        # Upload firmware
        call(["python", "/etc/Dobby/Tools/espota.py", "-i", IP, "-a", "StillNotSinking", "-f", "/etc/Dobby/Firmware/" + Hardware + "/" + str(max(Firmware_List)) + ".bin"])

        Log("Debug", "AutoUpdate", "Update compleate", Hostname + " From: " + str(Current_SW) + " To:" + str(max(Firmware_List)))

    elif Current_SW == max(Firmware_List):
        Log("Debug", "AutoUpdate", "Up to date", Hostname)

    else:
        Log("Debug", "AutoUpdate", "Newer", Hostname + " Running: " + str(Current_SW) + " Newest is:" + str(max(Firmware_List)))


# ---------------------------------------- # On message callbacks - Spawns threads ----------------------------------------
def MQTT_On_Message_Callback(mosq, obj, msg):
    Message_Thread = threading.Thread(target=MQTT_On_Message, kwargs={"Topic": msg.topic, "Payload": msg.payload, "Retained": msg.retain})
    Message_Thread.daemon = True
    Message_Thread.start()
    return

# ---------------------------------------- Init ----------------------------------------
def MQTT_init(MQTT_Client):
    # MQTT Setup
    MQTT_Client.username_pw_set(MQTT_Username, MQTT_Password)
    # FIX - ADD MQTT Logging
    MQTT_Client.on_log = MQTT_On_Log

    # Callbacks
    MQTT_Client.on_connect = MQTT_On_Connect
    MQTT_Client.on_disconnect = MQTT_On_Disconnect

    # Connect to broker
    MQTT_Client.connect(MQTT_Broker, port=MQTT_Port, keepalive=60, bind_address="")

    # Boot message - MQTT
    MQTT_Client.publish(System_Header + "/System/Dobby/", payload="Booting Dobby - Version: " + str(Version), qos=0, retain=False)


def Dobby_init():
    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    # Fill Variables
    # From Dobby
    global System_Header
    System_Header = Get_System_Config_Value(db_Curser, "Dobby", "System", "Header")

    # Append Topics to subscribe to subscribe list
    # Log
    MQTT_Add_Sub_Topic(System_Header + "/Log/#", 'Device Logger')
    # KeepAlive
    MQTT_Add_Sub_Topic(System_Header + "/KeepAlive/#", 'KeepAlive')
    # Functions
    MQTT_Add_Sub_Topic(System_Header + "/Functions", 'Functions')
    # Dobby Commands
    MQTT_Add_Sub_Topic(System_Header + "/Commands/Dobby/#", 'Commands')

    global MQTT_Broker
    MQTT_Broker = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Broker")
    global MQTT_Port
    MQTT_Port = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Port")
    global MQTT_Username
    MQTT_Username = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Username")
    global MQTT_Password
    MQTT_Password = Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "Password")
    global MQTT_Publish_Delay
    MQTT_Publish_Delay = float(Get_System_Config_Value(db_Curser, "Dobby", "MQTT", "PublishDelay"))

    global MQTT_KeepAlive_Interval
    MQTT_KeepAlive_Interval = int(Get_System_Config_Value(db_Curser, "Dobby", "MQTTKeepAlive", "Interval"))

    # Mail_Trigger - Email
    global Mail_Trigger_SMTP_Server
    Mail_Trigger_SMTP_Server = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Server")
    global Mail_Trigger_SMTP_Port
    Mail_Trigger_SMTP_Port = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Port")
    global Mail_Trigger_SMTP_Sender
    Mail_Trigger_SMTP_Sender = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Sender")
    global Mail_Trigger_SMTP_Username
    Mail_Trigger_SMTP_Username = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Username")
    global Mail_Trigger_SMTP_Password
    Mail_Trigger_SMTP_Password = Get_System_Config_Value(db_Curser, "Mail_Trigger", "SMTP", "Password")

    global Log_db
    Log_db = Get_System_Config_Value(db_Curser, "Dobby", "Log", "db")
    global Log_Level_System
    Log_Level_System = Get_System_Config_Value(db_Curser, "Dobby", "Log", "Level").lower()

    global Log_Length_System
    Log_Length_System = int(Get_System_Config_Value(db_Curser, "Dobby", "Log", "Length"))

    # MQTT
    global Log_Level_MQTT
    Log_Level_MQTT = Get_System_Config_Value(db_Curser, "MQTT", "Log", "Level", QuitOnError=False).lower()

    # From KeepAliveMonitor
    global Log_Level_KeepAliveMonitor
    Log_Level_KeepAliveMonitor = Get_System_Config_Value(db_Curser, "KeepAliveMonitor", "Log", "Level", QuitOnError=False).lower()
    global Log_Length_KeepAliveMonitor
    Log_Length_KeepAliveMonitor = int(Get_System_Config_Value(db_Curser, "KeepAliveMonitor", "Log", "Length"))

    # From MQTTConfig
    global Log_Level_MQTTConfig
    Log_Level_MQTTConfig = Get_System_Config_Value(db_Curser, "MQTTConfig", "Log", "Level", QuitOnError=False).lower()

    # From MQTTFunctions
    global Log_Level_MQTTFunctions
    Log_Level_MQTTFunctions = Get_System_Config_Value(db_Curser, "MQTTFunctions", "Log", "Level", QuitOnError=False).lower()

    # Mail_Trigger
    global Log_Level_Mail_Trigger
    Log_Level_Mail_Trigger = Get_System_Config_Value(db_Curser, "Mail_Trigger", "Log", "Level", QuitOnError=False).lower()

    # Log_Trigger
    global Log_Level_Log_Trigger
    Log_Level_Log_Trigger = Get_System_Config_Value(db_Curser, "Log_Trigger", "Log", "Level", QuitOnError=False).lower()

    # Spammer
    global Log_Level_Spammer
    Log_Level_Spammer = Get_System_Config_Value(db_Curser, "Spammer", "Log", "Level", QuitOnError=False).lower()

    # APC_Monitor
    global Log_Level_APC_Monitor
    Log_Level_APC_Monitor = Get_System_Config_Value(db_Curser, "APC_Monitor", "Log", "Level", QuitOnError=False).lower()
    
    # Backup
    global Backup_URL_FTP
    Backup_URL_FTP = Get_System_Config_Value(db_Curser, "Backup", "URL", "FTP", QuitOnError=False).lower()

    # Check if the needed databases exists
    Create_db(db_Curser, Log_db)

    Close_db(db_Connection, db_Curser)


# ---------------------------------------- MQTT Functions ----------------------------------------
def Functions(Payload):
    if ";" in Payload:
        Payload = Payload.replace(";", "")

    Log("Debug", "MQTTFunctions", "Recieved", Payload)

    db_Func_Connection = Open_db("Dobby")
    db_Func_Curser = db_Func_Connection.cursor()

    try:
        db_Func_Curser.execute('SELECT Type, Command, DelayAfter FROM Dobby.MQTTFunctions WHERE Function="' + Payload + '" ORDER BY CommandNumber;')
        Command_List = db_Func_Curser.fetchall()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        Log("Critical", "MQTTFunctions", "db", "Error: " + str(e))
        Close_db(db_Func_Connection, db_Func_Curser)
        return

    Close_db(db_Func_Connection, db_Func_Curser)

    if Command_List is ():
        Log("Warning", "MQTTFunctions", "Unknown Function", Payload)
        return

    Log("Info", "MQTTFunctions", "Executing Function", Payload)

    for Command in Command_List:

        if "MQTT" in Command[0]:
            Publish_String = Command[1].split("&")

            if Publish_String[1][-1:] is not ";":
                MQTT_Client.publish(Publish_String[0], payload=Publish_String[1] + ";", qos=0, retain=False)
            else:
                MQTT_Client.publish(Publish_String[0], payload=Publish_String[1], qos=0, retain=False)

        elif "Audio" in Command[0]:
            # FIX - Add setting in db
            call(["sudo", "-S", "mpg123", "-a", "btSpeaker", "-g", "50", "/etc/Dobby/Audio/" + Command[1]])

        if Command[2] != 0:
            # Delay_For = Command[2]
            time.sleep(Command[2])


# ---------------------------------------- MQTT Add Sub Topic ----------------------------------------
def MQTT_Add_Sub_Topic(Topic, Function, Options={}):

    if Topic in MQTT_Topic_Dict:
        MQTT_Topic_Dict[Topic].append([Function, Options])
    else:
        MQTT_Topic_Dict[Topic] = [[Function, Options]]


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
                if Function[0] == "KeepAlive":
                    KeepAlive_Monitor(Topic, Payload)

                elif Function[0] == "Action Trigger":
                    # Action_Trigger(Function[1], Payload, Retained)
                    Action_Trigger.On_Message()

                elif Function[0] == "Log Trigger":
                    Log_Trigger(Function[1], Payload, Retained)

                elif Function[0] == "Mail Trigger":
                    Message_Check(Topic, Payload, Retained)

                elif Function[0] == "Functions":
                    Functions(Payload)

                elif Function[0] == "Device Logger":
                    Device_Logger(Topic, Payload, Retained)

                else:
                    print 'Function missing - ' + str(Function)
                    for Target_Topic, Target_Function in dict(MQTT_Topic_Dict).iteritems():
                        print Target_Topic
                        print Target_Function


# ---------------------------------------- Device Logger ----------------------------------------
def Device_Logger(Topic, Payload, Retained):

    if Retained is True:
        return

    db_Device_Log_Connection = Open_db(Log_db)
    db_Device_Log_Curser = db_Device_Log_Connection.cursor()

    Device_Log_Table = "DeviceLog"

    Device_Name = Topic.split("/")
    
    Device_Name = Device_Name[3]

    try:
        db_Device_Log_Curser.execute('INSERT INTO `' + Log_db + '`.`' + Device_Log_Table + '` (Device, Topic, Payload) VALUES("' + Device_Name + '","' + Topic + '", "' + Payload + '");')
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # 1146 = Table is missing
        if e[0] == 1146:
            try:
                db_Device_Log_Curser.execute("CREATE TABLE `" + Log_db + "`.`" + Device_Log_Table + "` (`id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, `Device` varchar(75) NOT NULL, `Topic` varchar(75) NOT NULL, `Payload` varchar(200) NOT NULL, PRIMARY KEY (`id`))")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                print e
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    # FIX add some error handling here
                    print "DB WTF ERROR 2: " + str(e)

                    # Try to write log again
                    db_Device_Log_Curser.execute('INSERT INTO `' + Log_db + '`.`' + Device_Log_Table + '` (Device, Topic, Payload) VALUES("' + Device_Name + '","' + Topic + '", "' + Payload + '");')
                else:
                    # FIX add some error handling here
                    print "DB WTF ERROR:" + str(e)

    # Check_db_Length(db_Device_Log_Connection, Device_Log_Table)

    Close_db(db_Device_Log_Connection, db_Device_Log_Curser)


# ---------------------------------------- File_Change_Checker() ----------------------------------------
# Checks if the script has chaged and if so quits assuming supervisor will start the script again
class File_Change_Checker:

    # 
    Refresh_Rate = 1.5

    def __init__(self):
        # Log event
        Log("Info", "File Change Checker", "Checker", "Starting")

        # Get current time stamp
        self.Last_Modified = os.path.getmtime('/etc/Dobby/bin/Dobby.py')
    
        # Start checker thread
        File_Change_Checker_Thread = threading.Thread(target=self.Checker, kwargs={})
        File_Change_Checker_Thread.daemon = True
        File_Change_Checker_Thread.start()

    def Checker(self):

        while True:
            if os.path.getmtime('/etc/Dobby/bin/Dobby.py') != self.Last_Modified:
                
                # Check if Dobby is starte by supervisor
                Dobby_Status = subprocess.check_output('sudo supervisorctl status Dobby', shell=True)

                # If started via supervisor then restart Dobby
                if "RUNNING" in Dobby_Status:
                    Log("Info", "File Change Checker", "Checker", "Script started via supervisor so restarting script")
                    os.system("sudo supervisorctl restart Dobby")
                else:
                    Log("Debug", "File Change Checker", "Checker", "Script not starting via supervisor no action taken")
                    self.Last_Modified = os.path.getmtime('/etc/Dobby/bin/Dobby.py')

            time.sleep(self.Refresh_Rate)
        

# ---------------------------------------- FTP_Upload_Dir() ----------------------------------------
def FTP_Upload_Dir(FTP_Connection, Local_Path, Remote_Path):

    # Find dir name so it can be added to remote path
    Upload_Dir_Name = Local_Path.split('/')
    Upload_Dir_Name = Upload_Dir_Name[len(Upload_Dir_Name) - 1]

    # Check if remote dir exists
    if FTP_Dir_Check(FTP_Connection, Remote_Path + '/' + Upload_Dir_Name) == False:
        Log("Debug", "System", "FTP Upload Dir", "Unable to create dir: " + Remote_Path + '/' + Upload_Dir_Name)
        return False
    
    for File_Name in os.listdir(Local_Path):

        FTP_Connection.set_pasv(False)

        Log("Debug", "System", "FTP Upload Dir", "Uploading: " + str(File_Name))

        with open(Local_Path + '/' + File_Name, 'rb'):
            FTP_Connection.storbinary('STOR ' + File_Name, open(Local_Path + '/' + File_Name, 'rb'))

    Log("Debug", "System", "FTP Upload Dir", "Upload of: '" + str(Upload_Dir_Name) + "' compleate")

# ---------------------------------------- FTP_Dir_Check() ----------------------------------------
def FTP_Dir_Check(FTP_Connection, Remote_Dir):

    if Remote_Dir != "":
        # Split Path
        Remote_Dir = Remote_Dir.split('/')
        Try_Path = ''
        for i in range(len(Remote_Dir)):
            Try_Path = Try_Path + Remote_Dir[i] + '/'
            try:
                FTP_Connection.cwd(Try_Path)
            except ftplib.error_perm as err:

                if str(err) == '550 Failed to change directory.':
                    FTP_Connection.mkd(Try_Path)
                    Log("Debug", "System", "FTP Dir Checker", "Created dir: " + str(Try_Path))
                    FTP_Connection.cwd(Try_Path)
                else:
                    Log("Debug", "System", "FTP Dir Checker", "Got error: " + str(err) + " trying to create dir: " + str(Try_Path))
                    return False
        return True


# ---------------------------------------- Backup() ----------------------------------------
# Backups up the following once a day to the URL set in SystemSettings
class Backup:

    # When to trigger daily db backup
    Backup_db_At = "04:20"

    # When to trigger weekly SD backup
    Backup_SD_At = "04:40"

    Backup_Path = '/etc/Dobby/Backup'

    def __init__(self):
        # Log event
        Log("Info", "Backup", "Checker", "Starting")

        # Schedule jobs
        # db
        schedule.every().day.at(self.Backup_db_At).do(self.Run_db_Backup)
        # SD
        schedule.every().tuesday.at(self.Backup_db_At).do(self.Run_SD_Backup)

        # Start checker thread
        File_Change_Checker_Thread = threading.Thread(target=self.Checker, kwargs={})
        File_Change_Checker_Thread.daemon = True
        File_Change_Checker_Thread.start()

    def Checker(self):

        while True:
            schedule.run_pending()
            time.sleep(5)
    
    def Run_db_Backup(self):
        DB_NAME = 'Dobby'

        Log("Info", "Backup", "Checker", "db Backup Starting")
        
        # Getting current DateTime to create the separate backup folder like "20180817-123433".
        DATETIME = time.strftime('%Y%m%d-%H%M%S')
        Backup_Path_Today = self.Backup_Path + '/' + DATETIME
        
        # Checking if backup folder already exists or not. If not exists will create it.
        try:
            os.stat(Backup_Path_Today)
        except:
            os.mkdir(Backup_Path_Today)
        
        # Code for checking if you want to take single database backup or assinged multiple backups in DB_NAME.
        if os.path.exists(DB_NAME):
            file1 = open(DB_NAME)
            multi = True
        else:
            multi = False
        
        # Log event
        Log("Debug", "Backup", "Checker", "Starting backup of db: " + str(DB_NAME))
        
        # Starting actual database backup process.
        if multi:
            in_file = open(DB_NAME,"r")
            flength = len(in_file.readlines())
            in_file.close()
            p = 1
            dbfile = open(DB_NAME,"r")
        
            while p <= flength:
                db = dbfile.readline()   # reading database name from file
                db = db[:-1]         # deletes extra line
                dumpcmd = "mysqldump -h localhost -u dobby -pHereToServe " + db + " > " + pipes.quote(Backup_Path_Today) + "/" + db + ".sql"
                os.system(dumpcmd)
                # gzipcmd = "gzip " + pipes.quote(Backup_Path_Today) + "/" + db + ".sql"
                # os.system(gzipcmd)
                p = p + 1
            dbfile.close()
        else:
            db = DB_NAME
            dumpcmd = "mysqldump -h localhost -u dobby -pHereToServe " + db + " > " + pipes.quote(Backup_Path_Today) + "/" + db + ".sql"
            os.system(dumpcmd)
            # gzipcmd = "gzip " + pipes.quote(Backup_Path_Today) + "/" + db + ".sql"
            # os.system(gzipcmd)

        Log("Debug", "Backup", "Checker", "Local db backup created")
        
        # Create temp string of system var
        # FIX - Load from dc each time
        Backup_URL_FTP_String = Backup_URL_FTP

        # Split URL it to verious parts
        # ftp://dobby:heretoserve@18.188.134.96/home/dobby/backup/
        Backup_URL_FTP_String = Backup_URL_FTP_String.replace('ftp://', '')

        # Username
        Backup_URL_FTP_String = Backup_URL_FTP_String.split(':')
        FTP_Username = Backup_URL_FTP_String[0]
        # Remove username from string
        Backup_URL_FTP_String = Backup_URL_FTP_String[1].split('@')

        # Password
        FTP_Password = Backup_URL_FTP_String[0]
        
        # FTP Host
        FTP_Host = Backup_URL_FTP_String[1].split('/')
        FTP_Host = FTP_Host[0]

        # FTP Remote Dir
        FTP_Remote_Dir = Backup_URL_FTP_String[1].replace(FTP_Host, '', 1)

        # Open a ftp connection
        FTP_Connection = ftplib.FTP(FTP_Host, FTP_Username, FTP_Password)

        # Check if dir exists on Backup FTP
        FTP_Upload_Dir(FTP_Connection, Backup_Path_Today, FTP_Remote_Dir)

        # Close FTP Connection
        FTP_Connection.quit()

        Log("Info", "Backup", "Checker", "db Backup Compleate")


    def Run_SD_Backup(self):
        Log("Info", "Backup", "Checker", "SD Backup Starting")
        Log("Warning", "Backup", "Checker", "System might be slow due to backup")
        
        # Getting current DateTime to create the separate backup folder like "20180817-123433".
        DATETIME = time.strftime('%Y%m%d-%H%M%S')
        Backup_Path_Today = self.Backup_Path + '/' + DATETIME
        
        # Checking if backup folder already exists or not. If not exists will create it.
        try:
            os.stat(Backup_Path_Today)
        except:
            os.mkdir(Backup_Path_Today)
        
        # Log event
        Log("Debug", "Backup", "Checker", "Starting backup SD Card")
        
        SD_Backup_String = "sudo dd if=/dev/mmcblk0p2 of=" + Backup_Path_Today + "/" + str(socket.gethostname() + "_" + time.strftime('%Y-%m-%d')) + ".img bs=1M"
        os.system(SD_Backup_String)
        
        Log("Debug", "Backup", "Checker", "Local backup created")
        
        # Create temp string of system var
        # FIX - Load from dc each time
        Backup_URL_FTP_String = Backup_URL_FTP

        # Split URL it to verious parts
        Backup_URL_FTP_String = Backup_URL_FTP_String.replace('ftp://', '')

        # Username
        Backup_URL_FTP_String = Backup_URL_FTP_String.split(':')
        FTP_Username = Backup_URL_FTP_String[0]
        # Remove username from string
        Backup_URL_FTP_String = Backup_URL_FTP_String[1].split('@')

        # Password
        FTP_Password = Backup_URL_FTP_String[0]
        
        # FTP Host
        FTP_Host = Backup_URL_FTP_String[1].split('/')
        FTP_Host = FTP_Host[0]

        # FTP Remote Dir
        FTP_Remote_Dir = Backup_URL_FTP_String[1].replace(FTP_Host, '', 1)

        # Open a ftp connection
        FTP_Connection = ftplib.FTP(FTP_Host, FTP_Username, FTP_Password)

        # Check if dir exists on Backup FTP
        FTP_Upload_Dir(FTP_Connection, Backup_Path_Today, FTP_Remote_Dir)

        # Close FTP Connection
        FTP_Connection.quit()

        Log("Info", "Backup", "Checker", "Backup Compleate")



# ---------------------------------------- Counters ----------------------------------------
class Counters:
    # How often does esch spammer read write to the db (sec)
    Loop_Delay = 2.500

    def __init__(self):

        
        print "WTF!!!"

        # Check if table exists
        db_Connection = Open_db("Dobby")
        db_Curser = db_Connection.cursor()

        try:
            db_Curser.execute("SELECT id FROM Dobby.Counters LIMIT 1;")
        # Log event
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            Log("Info", "Counters", "Value Calculator", "No entries in 'Counters' table not starting")
            # Close db connection
            Close_db(db_Connection, db_Curser)
            return
        else:
            Log("Info", "Counters", "Value Calculator", "Starting")

        # Close db connection
        Close_db(db_Connection, db_Curser)

        self.Checkers_Dict = {}

        print "WTF!!!"

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
            db_Curser.execute("SELECT Name, `Log Trigger Name`, `json Tag`, `Ticks`, `Math` FROM Dobby.Counters")
            Checkers_data = db_Curser.fetchall()

            # Calc values for each counter
            for Counter_Info in Checkers_data:
                # Get last reset id
                db_Curser.execute('SELECT id FROM DobbyLog.Log_Trigger where Name="' + Counter_Info[1] + '" and Value="Reset" order by id desc Limit 1;')
                Last_Reset_ID = db_Curser.fetchall()

                if (Last_Reset_ID == ()):
                    Last_Reset_ID = 0
                else:
                    Last_Reset_ID = Last_Reset_ID[0][0]

                # Get values since last reset
                db_Curser.execute('SELECT Value FROM DobbyLog.Log_Trigger where Name="' + Counter_Info[1] + '" and id > "' + str(Last_Reset_ID) + '" order by id desc;')
                db_Data = db_Curser.fetchall()

                Counter_State = 0

                print "HERE"

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
                    Found_Boot = False

                    for i in range(len(db_Data)):
                        # If Value == "Boot" add next value if not
                        if db_Data[i][0] == 'Boot':
                            Add_Next = True
                            Found_Boot = True
                        
                        elif Add_Next == True:
                            Counter_State = Counter_State + int(db_Data[i][0])
                            Add_Next = False
                    
                    if Found_Boot == True:
                        print "FOUND BOOT"
                    else:
                        print "Didnt find boot"
                        print db_Data[len(db_Data)]

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
                    MQTT_Client.publish(System_Header + '/Counters/Dobby/' + str(Counter_Info[0]) + "/Ticks", payload=Counter_State, qos=0, retain=True)
                    MQTT_Client.publish(System_Header + '/Counters/Dobby/' + str(Counter_Info[0]), payload=Math_Value, qos=0, retain=True)
            
            # Close db connection
            Close_db(db_Connection, db_Curser)

            # Sleep untill next calc
            time.sleep(self.Loop_Delay)



# ---------------------------------------- Main Script ----------------------------------------
# Fill variables
Dobby_init()

# Log a boot message
Log("Info", "Dobby", "System", "Booting Dobby - Version: " + str(Version))

MQTT_init(MQTT_Client)

# Start Spammer
Spammer()

# Start Action Trigger
Action_Trigger()

# Start Log Trigger
Log_Trigger_Init()

# Start APC Monitor
APC_Monitor()

# File change checked
File_Change_Checker()

# Backup
Backup()

# Counters
Counters()

# Start MQTT Loop
MQTT_Client.loop_forever()
