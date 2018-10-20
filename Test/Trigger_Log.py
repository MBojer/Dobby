#!/usr/bin/python

# MySQL
import MySQLdb

# MQTT
import paho.mqtt.client as MQTT

# # Threding
import threading

# # Time
import time
# import datetime
# from datetime import timedelta

# json
import json

import datetime

import random

MQTT_Client = MQTT.Client(client_id="Log Trigger", clean_session=True)

# Do not transfer
Log_db = 'DobbyLog'


def Log(Log_Level, Log_Source, Log_Header, Log_Text):
    print "Log_Level: " + str(Log_Level) + " Log_Source: " + str(Log_Source) + " Log_Header: " + str(Log_Header) + " Log_Text: " + str(Log_Text)


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


# ---------------------------------------- Log_Trigger ----------------------------------------
# ---------------------------------------- Spammer ----------------------------------------
class Log_Trigger:

    db_Refresh_Rate = 1.5
    Loop_Delay = 0.500

    def __init__(self):
        # Log event
        Log("Info", "Log Trigger", "Checker", "Starting")

        self.Spammer_Dict = {}

        # Sart checker thread
        Spammer_Thread = threading.Thread(target=self.Checker, kwargs={})
        Spammer_Thread.daemon = True
        Spammer_Thread.start()

    def Checker(self):

        while True:
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.Spammer WHERE Enabled='1'")
            Spammer_db = db_Curser.fetchall()

            Close_db(db_Connection, db_Curser)

            for i in Spammer_db:
                # i[0] = Spammer db id
                if i[0] not in self.Spammer_Dict:
                    self.Spammer_Dict[i[0]] = self.Agent(i[0])
                    Log("Debug", "Log Trigger", "Checker", "Starting: " + self.Spammer_Dict[i[0]].Name)

                else:
                    # Change to spammer
                    if str(self.Spammer_Dict[i[0]].Last_Modified) != str(i[1]):
                        Log("Debug", "Log Trigger", "Checker", "Change found in: " + self.Spammer_Dict[i[0]].Name + " restarting agent")
                        # Wait for agent to close db connection
                        while self.Spammer_Dict[i[0]].OK_To_Kill is False:
                            time.sleep(0.100)

                        # Delete agent
                        Log("Debug", "Log Trigger", "Checker", "Deleting: " + self.Spammer_Dict[i[0]].Name)
                        del self.Spammer_Dict[i[0]]
                        # Start agent again
                        self.Spammer_Dict[i[0]] = self.Agent(i[0])
                        Log("Debug", "Log Trigger", "Checker", "Starting: " + self.Spammer_Dict[i[0]].Name)

                time.sleep(random.uniform(0.10, 0.150))

            time.sleep(Log_Trigger.db_Refresh_Rate)

    class Agent:
        def __init__(self, id):

            self.id = int(id)

            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT Name, Enabled, State, `Interval`, Topic, Payload, Next_Ping, Last_Modified FROM Dobby.Spammer WHERE id='" + str(self.id) + "'")
            Spammer_Info = db_Curser.fetchone()

            Close_db(db_Connection, db_Curser)

            self.Name = str(Spammer_Info[0])

            # Canget log event before now if you want to use name
            Log("Debug", "Log Trigger", self.Name, 'Initializing')

            self.Enabled = bool(Spammer_Info[1])
            self.State = Spammer_Info[2]
            self.Interval = float(Spammer_Info[3])
            self.Topic = Spammer_Info[4]
            self.Payload = Spammer_Info[5]
            self.Next_Ping = Spammer_Info[6]
            self.Last_Modified = Spammer_Info[7]

            self.OK_To_Kill = True

            Log("Debug", "Log Trigger", self.Name, 'Initialization compleate')

            self.Start()

        # ========================= Agent - Start =========================
        def Start(self):
            Spammer_Thread = threading.Thread(target=self.Run, kwargs={})
            Spammer_Thread.daemon = True
            Spammer_Thread.start()

        # ========================= Agent - Run =========================
        def Run(self):

            Log("Info", "Log Trigger", self.Name, "Running")
            # Start eternal loop
            while True:
                # Check if its time to ping
                if self.Next_Ping < datetime.datetime.now():
                    Log("Debug", "Log Trigger", self.Name, "Ping")

                    self.Next_Ping = datetime.datetime.now() + timedelta(seconds=self.Interval)

                    self.OK_To_Kill = False

                    db_Connection = Open_db("Dobby")
                    db_Curser = db_Connection.cursor()

                    db_Curser.execute("UPDATE `Dobby`.`Spammer` SET `Next_Ping`='" + str(self.Next_Ping) + "', `Last_Ping`='" + str(datetime.datetime.now()) + "' WHERE id = '" + str(self.id) + "';")

                    Close_db(db_Connection, db_Curser)

                    self.OK_To_Kill = True

                    MQTT_Client.publish(self.Topic, payload=self.Payload, qos=0, retain=False)

                while self.Next_Ping > datetime.datetime.now():
                    time.sleep(self.Loop_Delay)

# ---------------------------------------- Init ----------------------------------------
def MQTT_init(MQTT_Client):
    # MQTT Setup
    MQTT_Client.username_pw_set('DasBoot', 'NoSinking')
    # FIX - ADD MQTT Logging

    # Callbacks
    # MQTT_Client.on_connect = MQTT_On_Connect
    # MQTT_Client.on_disconnect = MQTT_On_Disconnect

    # Message calbacks
    # KeepAliveMonitor
    # MQTT_Client.message_callback_add(System_Header + "/KeepAlive/#", MQTT_KeepAlive_On_Msg)
    #
    # # MQTTFunctions
    # MQTT_Client.message_callback_add(System_Header + "/Functions", MQTT_Functions_On_Msg)
    # MQTT_Client.message_callback_add(System_Header + "/MQTTFunctions", MQTT_Functions_On_Msg)
    #
    # # Device Logger
    # MQTT_Client.message_callback_add(System_Header + "/System/#", MQTT_Device_Logger_On_Msg)
    #
    # # MQTTCommands
    # MQTT_Client.message_callback_add(System_Header + "/Commands/Dobby/#", MQTT_Commands_On_Msg)

    MQTT_Client.connect('192.168.1.2', port=1883, keepalive=60, bind_address="")

    # Boot message - MQTT
    MQTT_Client.publish('/Test', payload="Booting Dobby - Version: Log_Trigger Test", qos=0, retain=False)


MQTT_init(MQTT_Client)

Log_Trigger()

MQTT_Client.loop_forever()
