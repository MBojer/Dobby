#!/usr/bin/python

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

# MQTT KeepAlive
import psutil

# MQTTFunctions
from subprocess import call

# json
import json

# Auto Update
# import urllib
import os

# System variables
Version = 101008
Start_Time = datetime.datetime.now()

# MQTT Client
MQTT_Client = MQTT.Client(client_id="Dobby", clean_session=True)


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

    Check_db_Length(db_Log_Curser, "SystemLog")

    Close_db(db_Log_Connection, db_Log_Curser)


def Check_db_Length(db_Log_Curser, Log_Table):
    db_Log_Curser.execute("SELECT count(*) FROM " + Log_Table)
    Rows_Number_Of = db_Log_Curser.fetchall()

    if Rows_Number_Of[0][0] > int(Log_Length_System):
        Rows_To_Delete = Rows_Number_Of[0][0] - int(Log_Length_System)
        db_Log_Curser.execute("DELETE FROM '" + Log_Table + "' ORDER BY 'LastKeepAlive' LIMIT " + str(Rows_To_Delete) + " OFFSET 0")
        Log("Debug", "Dobby", "db", "History Length reached, deleting " + str(Rows_To_Delete) + " rows for Hostname: " + Log_Table)


def Log_Level_Check(Log_Source, Log_Level):

    Log_Level = Log_Level.lower()
    Check_Level = Log_Level_System

    if Log_Source == "MonitorAgent" and Log_Level_MonitorAgent != "":
        Check_Level = Log_Level_MonitorAgent
    elif Log_Source == "KeepAliveMonitor" and Log_Level_KeepAliveMonitor != "":
        Check_Level = Log_Level_KeepAliveMonitor
    elif Log_Source == "MQTTConfig" and Log_Level_MQTTConfig != "":
        Check_Level = Log_Level_MQTTConfig
    elif Log_Source == "MQTTFunctions" and Log_Level_MQTTFunctions != "":
        Check_Level = Log_Level_MQTTFunctions
    elif Log_Source == "MQTT" and Log_Level_MQTT != "":
        Check_Level = Log_Level_MQTT

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


def Get_SystemConfig_Value(db_Curser, Target, Header, Name, QuitOnError=True):
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

    # Device Logger
    MQTT_Subscribe_To(MQTT_Client, System_Header + "/System/#")

    # KeepAliveMonitor
    MQTT_Subscribe_To(MQTT_Client, System_Header + "/KeepAlive/#")

    # MQTTFunctions
    MQTT_Subscribe_To(MQTT_Client, System_Header + "/Functions")

    # Commands & MQTTConfig
    MQTT_Subscribe_To(MQTT_Client, System_Header + "/Commands/Dobby/#")

    # Monitor Agent
    MonitorAgent_init()
    MonitorAgent_Subscribe()

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

    elif "MonitorAgent" in Topic:
        MQTT_Commands_MonitorAgent(Topic, Payload)
        return

    elif "KeepAliveMonitor" in Topic:
        MQTT_Commands_KeepAliveMontor(Topic, Payload)
        return

    elif Topic in "Test":
        Log("Test", "MQTTCommands", "Executing", Topic + " - " + Payload)

        return

    Log("Warning", "MQTTCommands", "Request", Topic + " - " + Payload + " - Not found")


def MQTT_Commands_MonitorAgent(Topic, Payload):
    if "Show" in Payload:
        Log("Info", "MQTTCommands", "Executing", Topic + " - " + Payload)
        MonitorAgent_Show()
        return

    if "Start" or "Stop" in Payload and " " in Payload:
        Payload = Payload.split(" ")
        if "Start" or "Stop" in Payload[0]:
            db_MCMAS_Connection = Open_db("Dobby")
            db_MCMAS_Curser = db_MCMAS_Connection.cursor()

            Log("Info", "MQTTCommands", "Executing", Payload[0] + " " + Payload[1])

            db_MCMAS_Curser.execute("SELECT Agent_ID FROM Dobby.MonitorAgentConfig WHERE Agent_Name='" + Payload[1] + "';")
            Agent_ID = db_MCMAS_Curser.fetchone()

            db_MCMAS_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET Agent_State = '" + Payload[0] + "' WHERE Agent_ID = '" + str(Agent_ID[0]) + "';")

            Log("Info", "MonitorAgent", Payload[1], Payload[0])

            Close_db(db_MCMAS_Connection, db_MCMAS_Curser)

    Log("Info", "MQTTCommands", "MonitorAgent", "Unknown Agent: " + Payload[1])
    return


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

    Log("Info", "MQTTConfig", "Publish Config", Payload[0])

    Config_Dict = {}

    Interation = 0

    for x in Config_Name_List:
        if str(x[0]) != "id" and str(x[0]) != "Config_Active" and str(x[0]) != "Date_Modified" and Config_Value_List[0][Interation] is not None:
            Config_Dict[str(x[0])] = str(Config_Value_List[0][Interation])
        Interation = Interation + 1

    # Publish json
    MQTT_Client.publish(System_Header + "/Config/" + Payload[0], payload=json.dumps(Config_Dict) + ";", qos=0, retain=False)

    return


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

    Log("Debug", "KeepAliveMonitor", "KeepAlive", "From: " + root_KL["Hostname"])

    if "IP" not in root_KL:
        root_KL["IP"] = "0.0.0.0"

    if "RSSI" not in root_KL:
        root_KL["RSSI"] = "0"

    if root_KL["Hostname"] != "Dobby":
        # Spawn thread for Auto Update Check
        AU_Thread = threading.Thread(target=Auto_Update, kwargs={"Hostname": root_KL["Hostname"], "IP": root_KL["IP"], "Current_SW": root_KL["Software"]})
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
        db_KL_Curser.execute("DELETE FROM DobbyLog.KeepAliveMonitor WHERE Device='" + root_KL["Hostname"] + "' ORDER BY id LIMIT " + str(Rows_To_Delete) + ";")

    Close_db(db_KL_Connection, db_KL_Curser)


def MQTT_KeepAlive_Show():
    db_KAM_Connection = Open_db(Log_db)
    db_KAM_Curser = db_KAM_Connection.cursor()

    db_KAM_Curser.execute("SELECT Distinct Device, MAX(LastKeepAlive), UpFor, FreeMemory, SoftwareVersion FROM DobbyLog.KeepAliveMonitor Group BY Device LIMIT 10000;")
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


# ---------------------------------------- Auto Update ----------------------------------------
def Auto_Update(Hostname, IP, Current_SW):

    # FIX - Add system software update
    if Hostname == "Dobby":
        return

    # FIX CHECK IP AND RETURN IF NOT VALID

    # Open the config table and read device config
    db_AU_Connection = Open_db(Log_db)
    db_AU_Curser = db_AU_Connection.cursor()

    try:
        db_AU_Curser.execute("SELECT Auto_Update, MQTT_Allow_Flash_Password FROM Dobby.DeviceConfig where Hostname='" + Hostname + "' and Config_Active=1;")
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
    Firmware_Dir_List = os.listdir("/etc/Dobby/Firmware/")

    Firmware_List = []

    for Firmware_Name in Firmware_Dir_List:
        if "B-" in Firmware_Name:
            # FIX - Add support for beta firmware
            pass
        else:
            Firmware_List.append(int(Firmware_Name.replace(".bin", "")))

    if Current_SW < max(Firmware_List):
        Log("Info", "AutoUpdate", "Updating", Hostname + "From: " + str(Current_SW) + " To:" + str(max(Firmware_List)))

        # FIX ADD FOLDER ROOT PATH BELOW
        call(["python", "/etc/Dobby/Tools/espota.py", "-i", IP, "-a", "StillNotSinking", "-f", "/etc/Dobby/Firmware/" + str(max(Firmware_List)) + ".bin"])

        Log("Debug", "AutoUpdate", "Update compleate", Hostname + "From: " + str(Current_SW) + " To:" + str(max(Firmware_List)))

    elif Current_SW == max(Firmware_List):
        Log("Debug", "AutoUpdate", "OK", Hostname + "Up to date")

    else:
        Log("Debug", "AutoUpdate", "Newer", Hostname + " Running: " + str(Current_SW) + " Newest is:" + str(max(Firmware_List)))


# ---------------------------------------- # On message callbacks - Spawns threads ----------------------------------------
def MQTT_Functions_On_Msg(mosq, obj, msg):
    Message_Thread = threading.Thread(target=Functions, kwargs={"Payload": msg.payload})
    Message_Thread.daemon = True
    Message_Thread.start()
    return


def MQTT_Commands_On_Msg(mosq, obj, msg):
    if "/Commands/Dobby/Config" or "/Commands/Dobby/Settings" not in msg.payload:
        Message_Thread = threading.Thread(target=MQTT_Commands, kwargs={"Topic": msg.topic, "Payload": msg.payload})
        Message_Thread.daemon = True
        Message_Thread.start()
        return
    else:
        print "MARKER"


def MQTT_KeepAlive_On_Msg(mosq, obj, msg):
    Message_Thread = threading.Thread(target=KeepAlive_Monitor, kwargs={"Topic": msg.topic, "Payload": msg.payload})
    Message_Thread.daemon = True
    Message_Thread.start()
    return


def MQTT_Device_Logger_On_Msg(mosq, obj, msg):
    Message_Thread = threading.Thread(target=Device_Logger, kwargs={"Topic": msg.topic, "Payload": msg.payload})
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

    # Message calbacks
    # KeepAliveMonitor
    MQTT_Client.message_callback_add(System_Header + "/KeepAlive/#", MQTT_KeepAlive_On_Msg)

    # MQTTFunctions
    MQTT_Client.message_callback_add(System_Header + "/Functions", MQTT_Functions_On_Msg)
    MQTT_Client.message_callback_add(System_Header + "/MQTTFunctions", MQTT_Functions_On_Msg)

    # Device Logger
    MQTT_Client.message_callback_add(System_Header + "/System/#", MQTT_Device_Logger_On_Msg)

    # MQTTCommands
    MQTT_Client.message_callback_add(System_Header + "/Commands/Dobby/#", MQTT_Commands_On_Msg)

    MQTT_Client.connect(MQTT_Broker, port=MQTT_Port, keepalive=60, bind_address="")

    # Boot message - MQTT
    MQTT_Client.publish(System_Header + "/System/Dobby/", payload="Booting Dobby - Version: " + str(Version), qos=0, retain=False)


def Dobby_init():
    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    # Fill Variables
    # From Dobby
    global System_Header
    System_Header = Get_SystemConfig_Value(db_Curser, "Dobby", "System", "Header")

    global System_Root_Dir
    System_Root_Dir = Get_SystemConfig_Value(db_Curser, "Dobby", "Dir", "Root")
    global System_Script_Dir
    System_Script_Dir = Get_SystemConfig_Value(db_Curser, "Dobby", "Dir", "Script")
    global System_Script_URL
    System_Script_URL = Get_SystemConfig_Value(db_Curser, "Dobby", "Dir", "URL")

    global MQTT_Broker
    MQTT_Broker = Get_SystemConfig_Value(db_Curser, "Dobby", "MQTT", "Broker")
    global MQTT_Port
    MQTT_Port = Get_SystemConfig_Value(db_Curser, "Dobby", "MQTT", "Port")
    global MQTT_Username
    MQTT_Username = Get_SystemConfig_Value(db_Curser, "Dobby", "MQTT", "Username")
    global MQTT_Password
    MQTT_Password = Get_SystemConfig_Value(db_Curser, "Dobby", "MQTT", "Password")
    global MQTT_Publish_Delay
    MQTT_Publish_Delay = float(Get_SystemConfig_Value(db_Curser, "Dobby", "MQTT", "PublishDelay"))
    global MQTT_KeepAlive_Interval
    MQTT_KeepAlive_Interval = int(Get_SystemConfig_Value(db_Curser, "Dobby", "MQTTKeepAlive", "Interval"))

    global Log_db
    Log_db = Get_SystemConfig_Value(db_Curser, "Dobby", "Log", "db")
    global Log_Level_System
    Log_Level_System = Get_SystemConfig_Value(db_Curser, "Dobby", "Log", "Level").lower()
    global Log_Length_System
    Log_Length_System = int(Get_SystemConfig_Value(db_Curser, "Dobby", "Log", "Length"))

    # MQTT
    global Log_Level_MQTT
    Log_Level_MQTT = Get_SystemConfig_Value(db_Curser, "MQTT", "Log", "Level", QuitOnError=False).lower()

    # From KeepAliveMonitor
    global Log_Level_KeepAliveMonitor
    Log_Level_KeepAliveMonitor = Get_SystemConfig_Value(db_Curser, "KeepAliveMonitor", "Log", "Level", QuitOnError=False).lower()
    global Log_Length_KeepAliveMonitor
    Log_Length_KeepAliveMonitor = int(Get_SystemConfig_Value(db_Curser, "KeepAliveMonitor", "Log", "Length"))

    # From MQTTConfig
    global Log_Level_MQTTConfig
    Log_Level_MQTTConfig = Get_SystemConfig_Value(db_Curser, "MQTTConfig", "Log", "Level", QuitOnError=False).lower()

    # From MQTTFunctions
    global Log_Level_MQTTFunctions
    Log_Level_MQTTFunctions = Get_SystemConfig_Value(db_Curser, "MQTTFunctions", "Log", "Level", QuitOnError=False).lower()

    # From MonitorAgent
    global Log_Level_MonitorAgent
    Log_Level_MonitorAgent = Get_SystemConfig_Value(db_Curser, "MonitorAgent", "Log", "Level", QuitOnError=False).lower()

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


# ---------------------------------------- Monitor Agent ----------------------------------------
def Agent_Message_Check(Topic, Payload, Retained):
    # Dont log retained messages
    if Retained is 0:

        db_MAC_Connection = Open_db()
        db_MAC_Curser = db_MAC_Connection.cursor()

        # FIX something is fishely at the %
        db_MAC_Curser.execute("SELECT Agent_Name FROM Dobby.MonitorAgentConfig WHERE Agent_Enabled='1' AND Agent_Sources LIKE '%" + Topic + "%';")
        Agent_Name = db_MAC_Curser.fetchone()

        Close_db(db_MAC_Connection, db_MAC_Curser)

        if Agent_Name is None:
            # FIX add error handling
            return

        Agent_Log_Source_Value(Agent_Name[0], Topic, Payload)


def Agent_Log_Source_Value(Agent_Name, Log_Source, Log_Value):
    db_ALSV_Connection = Open_db(Log_db)
    db_ALSV_Curser = db_ALSV_Connection.cursor()

    try:
        db_ALSV_Curser.execute("INSERT INTO `" + Log_db + "`.`MonitorAgent` (Agent, Source, Value) Values('" + Agent_Name + "', '" + Log_Source + "', '" + Log_Value + "');")
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        # Table missing, create it
        if e[0] == 1146:
            try:
                db_ALSV_Curser.execute("CREATE TABLE `" + Log_db + "`.`MonitorAgent` (`id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, `Agent` varchar(75) NOT NULL, `Source` varchar(75) NOT NULL, `Value` varchar(250), PRIMARY KEY (`id`))")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # Error 1050 = Table already exists
                if e[0] != 1050:
                    Log("Fatal", "MonitorAgent", Agent_Name, "Unable to create log db table, failed with error: " + str(e))
                    return

            Log("Info", "MonitorAgent", "db", "MonitorAgent Table missing creating it")
            # Try logging the message again
            db_ALSV_Curser.execute("INSERT INTO `" + Log_db + "`.`MonitorAgent` (Agent, Source, Value) Values('" + Agent_Name + "', '" + Log_Source + "', '" + Log_Value + "');")
        else:
            Log("Critical", "MonitorAgent", "db", "Unable to log message. Error: " + str(e))
            return

    Log("Debug", "MonitorAgent", Agent_Name, "Valure capured - Topic: " + Log_Source + " Value: " + Log_Value)

    # Delete rows > max
    db_ALSV_Curser.execute("SELECT count(*) FROM `" + Log_db + "`.`MonitorAgent` WHERE Agent='" + Agent_Name + "';")
    Rows_Number_Of = db_ALSV_Curser.fetchall()

    # Get max number of rows
    db_ALSV_Curser.execute("SELECT Agent_Log_Length FROM `Dobby`.`MonitorAgentConfig` WHERE Agent_Name='" + Agent_Name + "';")
    Max_Number_Of = db_ALSV_Curser.fetchone()

    if Rows_Number_Of[0][0] > int(Max_Number_Of[0]):
        Rows_To_Delete = Rows_Number_Of[0][0] - int(Max_Number_Of[0])
        db_ALSV_Curser.execute("DELETE FROM `" + Log_db + "`.`MonitorAgent` WHERE Agent='" + Agent_Name + "' ORDER BY 'DateTime' LIMIT " + str(Rows_To_Delete) + ";")
        Log("Debug", "Dobby", Agent_Name, "History Length reached, deleting " + str(Rows_To_Delete))

    Close_db(db_ALSV_Connection, db_ALSV_Curser)


def Agent_On_Msg(mosq, obj, msg):
    Agent_Msg_Thread = threading.Thread(target=Agent_Message_Check, kwargs={"Topic": msg.topic, "Payload": msg.payload, "Retained": msg.retain})
    Agent_Msg_Thread.daemon = True
    Agent_Msg_Thread.start()


def MonitorAgent_Show():
    Publish_String = "Agent - Enabled - State - Last Ping - Next Ping\n"

    db_MASh_Connection = Open_db("Dobby")
    db_MASh_Curser = db_MASh_Connection.cursor()

    db_MASh_Curser.execute("SELECT Agent_Name, Agent_Enabled, Agent_State, Agent_Last_Ping, Agent_Next_Ping FROM `Dobby`.`MonitorAgentConfig`;")
    Agent_List = db_MASh_Curser.fetchall()

    Close_db(db_MASh_Connection, db_MASh_Curser)

    for Agent_Info in Agent_List:
        # Name
        Publish_String = Publish_String + str(Agent_Info[0])
        Publish_String = Publish_String + " - "
        # Enabled
        Publish_String = Publish_String + str(Agent_Info[1])
        Publish_String = Publish_String + " - "
        # State
        Publish_String = Publish_String + str(Agent_Info[2])
        Publish_String = Publish_String + " - "
        # Last Ping
        Publish_String = Publish_String + str(Agent_Info[3])
        Publish_String = Publish_String + " - "
        # Next Ping
        Publish_String = Publish_String + str(Agent_Info[4])

        Publish_String = Publish_String + "\n"

    MQTT_Client.publish(System_Header + "/System/Dobby/MonitorAgent", payload=Publish_String, qos=0, retain=False)


# ---------------------------------------- Monitor Agent New ----------------------------------------
def MonitorAgent(Agent_ID):

    db_MAS_Connection = Open_db("Dobby")
    db_MAS_Curser = db_MAS_Connection.cursor()

    db_MAS_Curser.execute("set autocommit = 1")

    db_MAS_Curser.execute("SELECT Agent_Name, Agent_Targets, Agent_Targets_Payload FROM Dobby.MonitorAgentConfig WHERE Agent_ID='" + str(Agent_ID) + "';")
    Agent_Config = db_MAS_Curser.fetchall()

    if "," in Agent_Config[0][1]:
        Topic_List = Agent_Config[0][1].replace(" ", "")
        Topic_List = Agent_Config[0][1].split(",")
    else:
        Topic_List = [Agent_Config[0][1]]

    if "," in Agent_Config[0][2]:
        Payload_List = Agent_Config[0][2].replace(" ", "")
        Payload_List = Agent_Config[0][2].split(",")
    else:
        Payload_List = [Agent_Config[0][2]]

    # Change Agent_State to start
    db_MAS_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET Agent_State = 'Start' WHERE Agent_ID = '" + str(Agent_ID) + "';")

    while True:
        # Quit agent when MQTT Connection is lost
        if MQTT_Client.Connected is False:
            Log("Warning", "MonitorAgent", Agent_Config[0][0], "MQTT disconnected quitting")
            Close_db(db_MAS_Connection, db_MAS_Curser)
            return

        # Refresh agent info so agent can be controler
        db_MAS_Curser.execute("SELECT Agent_Enabled, Agent_State, Agent_Interval, Agent_Next_Ping  FROM Dobby.MonitorAgentConfig WHERE Agent_ID='" + str(Agent_ID) + "';")
        Agent_Info = db_MAS_Curser.fetchall()

        # Agent Enabled - Quits if changes to 0
        if Agent_Info[0][0] == "0":
            Log("Info", "MonitorAgent", Agent_Config[0][0], "Disabled quitting, bye bye ...")
            Close_db(db_MAS_Connection, db_MAS_Curser)
            return

        # Start Agent
        elif Agent_Info[0][1] == "Start":
            db_MAS_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET Agent_State = 'Running', Agent_Next_Ping = '" + str(datetime.datetime.now()) + "' WHERE Agent_ID = '" + str(Agent_ID) + "';")
            Log("Info", "MonitorAgent", Agent_Config[0][0], "Changed state to: Running")
            # Publish start message
            MQTT_Client.publish(System_Header + "/System/Dobby/MonitorAgent/" + Agent_Config[0][0], payload="Running", qos=0, retain=False)

        # Stop Agent
        elif Agent_Info[0][1] == "Stop":
            # Agent_State = "Stopped"
            db_MAS_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET Agent_State = 'Stopped' WHERE Agent_ID = '" + str(Agent_ID) + "';")
            Log("Info", "MonitorAgent", Agent_Config[0][0], "Changed state to: Stopped")
            # Publish stop message
            MQTT_Client.publish(System_Header + "/System/Dobby/MonitorAgent/" + Agent_Config[0][0], payload="Stopped", qos=0, retain=False)

        # Send Ping
        if Agent_Info[0][1] == "Running" and Agent_Info[0][3] < datetime.datetime.now():
            # Ping
            x = 0
            for Topic in Topic_List:
                MQTT_Client.publish(Topic, payload=Payload_List[x], qos=0, retain=False)
                Log("Debug", "MonitorAgent", Agent_Config[0][0], "Ping: " + Topic)

                # Update db
                db_MAS_Curser.execute("UPDATE `Dobby`.`MonitorAgentConfig` SET Agent_Last_Ping = '" + str(datetime.datetime.now()) + "', Agent_Next_Ping = '" + str(datetime.datetime.now() + timedelta(seconds=int(Agent_Info[0][2]))) + "' WHERE Agent_ID = '" + str(Agent_ID) + "';")

                x = x + 1

        # Sleep a little to prevent cpu drain
        # if (Agent_Info[0][3] - datetime.datetime.now()).seconds < 5:
        #     while Agent_Info[0][3] < datetime.datetime.now():
        #         time.sleep(0.1337)
        #
        # else:
        time.sleep(1)


def MonitorAgent_init():

    # Get values from db
    db_MAI_Connection = Open_db("Dobby")
    db_MAI_Curser = db_MAI_Connection.cursor()

    db_MAI_Curser.execute("SELECT Agent_ID FROM Dobby.MonitorAgentConfig WHERE Agent_Enabled='1';")
    Agent_List = db_MAI_Curser.fetchall()

    if Agent_List is ():
        Log("Fatal", "MonitorAgent", "db", "MonitorAgent db empthy, unable to continue")
        return

    # Swan MonitorAgents
    for Agent in Agent_List:
        MoA_Thread = threading.Thread(target=MonitorAgent, kwargs={"Agent_ID": Agent[0]})
        MoA_Thread.daemon = True
        MoA_Thread.start()

    Close_db(db_MAI_Connection, db_MAI_Curser)


# Subscribes to topics for active agents ment to be run at MQTT Connect
def MonitorAgent_Subscribe():

    db_AS_Connection = Open_db("Dobby")
    db_AS_Curser = db_AS_Connection.cursor()

    db_AS_Curser.execute("SELECT Agent_Sources FROM Dobby.MonitorAgentConfig WHERE Agent_Enabled='1';")
    Agent_Source_List = db_AS_Curser.fetchall()

    db_AS_Curser.execute("SELECT Agent_Name FROM Dobby.MonitorAgentConfig WHERE Agent_Enabled='1';")
    Agent_Name_List = db_AS_Curser.fetchall()

    Close_db(db_AS_Connection, db_AS_Curser)

    x = 0

    for Entry in Agent_Source_List:
        # Target List
        if "," in Entry[0]:
            Entry_List = Entry[0].replace(" ", "").split(",")
            for Target in Entry_List:
                Log("Debug", "MonitorAgent", str(Agent_Name_List[x][0]), "Subscribing to topic: " + str(Target))
                # Subscribe
                MQTT_Client.subscribe(str(Target))
                # Register callbacks
                MQTT_Client.message_callback_add(str(Target), Agent_On_Msg)

        # Single Target
        else:
            Log("Debug", "MonitorAgent", str(Agent_Name_List[x][0]), "Subscribing to topic: " + str(Entry[0]))
            # Subscribe
            MQTT_Client.subscribe(str(Entry[0]))
            # Register callbacks
            MQTT_Client.message_callback_add(str(Entry[0]), Agent_On_Msg)

        x = x + 1


# ---------------------------------------- Main Script ----------------------------------------
def Device_Logger(Topic, Payload):

    # Skip messages for Dobby
    if "/System/Dobby" in Topic:
        return

    db_Device_Log_Connection = Open_db(Log_db)
    db_Device_Log_Curser = db_Device_Log_Connection.cursor()

    Device_Log_Table = "DeivceLog"

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
                    print e

                    # Try to write log again
                    db_Device_Log_Curser.execute('INSERT INTO `' + Log_db + '`.`' + Device_Log_Table + '` (Device, Topic, Payload) VALUES("' + Device_Name + '","' + Topic + '", "' + Payload + '");')
                else:
                    # FIX add some error handling here
                    print "DB WTF ERROR:" + str(e)

    # Check_db_Length(db_Device_Log_Connection, Device_Log_Table)

    Close_db(db_Device_Log_Connection, db_Device_Log_Curser)


# ---------------------------------------- Main Script ----------------------------------------
# Fill variables
Dobby_init()

# Log a boot message
Log("Info", "Dobby", "System", "Booting Dobby - Version: " + str(Version))

MQTT_init(MQTT_Client)

MQTT_Client.loop_forever()
