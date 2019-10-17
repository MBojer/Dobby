#!/usr/bin/python

from flask import Flask
from flask_assistant import ask, tell, event, build_item, Assistant

# MySQL
import MySQLdb

# MQTT
import paho.mqtt.client as MQTT

# System variables
Version = 102007
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number

import logging
logging.getLogger('flask_assistant').setLevel(logging.DEBUG)

# MQTT
MQTT_Client = MQTT.Client(client_id="DobbyAssistant", clean_session=True)

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

    return str(data[0])


def Get_SQL_Value(SQL_Query):
    
    # Open db connection
    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    print SQL_Query

    db_Curser.execute(SQL_Query)
    data = db_Curser.fetchone()

    # Close db connection
    Close_db(db_Connection, db_Curser)

    return str(data[0])


def Get_Assistant_Config_Values(Name):

    db_Connection = Open_db("Dobby")
    db_Curser = db_Connection.cursor()

    try:
        db_Curser.execute("SELECT SQL_Query FROM `Dobby`.`Dobby_Assistant` WHERE Name='" + Name + "'")
        data = db_Curser.fetchone()
    except (MySQLdb.Error, MySQLdb.Warning):
        pass

    # Close db connection
    Close_db(db_Connection, db_Curser)

    return str(data[0])


# Open db connection
db_Connection = Open_db("Dobby")
db_Curser = db_Connection.cursor()

Assistant_id = Get_System_Config_Value(db_Curser, "Dobby", "Assistant", "id")

# Close db connection
Close_db(db_Connection, db_Curser)

Dobby_Assitant_App = Flask(__name__)
Dobby_Assitant = Assistant(Dobby_Assitant_App, project_id=Assistant_id)


@Dobby_Assitant.action('Battery Voltage')
def Battery_Voltage():
    Battery_Voltage_Current = Get_SQL_Value(Get_Assistant_Config_Values("Battery Voltage"))
    speech = "The batteries is currently reading " + Battery_Voltage_Current + " volts"
    return tell(speech)


@Dobby_Assitant.action('Battery SOC')
def Battery_SOC():
    Battery_SOC = Get_SQL_Value(Get_Assistant_Config_Values("Battery SOC"))
    speech = "The batteries state of charge is: " + Battery_SOC + "%"
    return tell(speech)


@Dobby_Assitant.action('MQ7 Engine Room')
def MQ7_Engine_Room():
    Reading = Get_SQL_Value(Get_Assistant_Config_Values("MQ7 Engine Room"))

    if Reading < 350:
        speech = "ALARM! The MQ7 sensor in the engine room is currently reading " + Reading + " parts per milion"
    else:
        speech = "The MQ7 sensor in the engine room is currently reading " + Reading + " parts per milion"
    return tell(speech)


@Dobby_Assitant.action('Solar Watts')
def Solar_Watts():

    Reading = float(Get_SQL_Value(Get_Assistant_Config_Values("Solar Watts")))

    if Reading == 0:
        speech = "There is no sun at the moment master"
    elif Reading < 300:
        speech = "Currently we are getting " + str(Reading) + " watt's from the solar pannels"
    elif Reading >= 300:
        speech = "We are on fire, we are getting " + str(Reading) + " watt's from the solar pannels!"

    return tell(speech)



if __name__ == '__main__':
    Dobby_Assitant_App.run(debug=True)