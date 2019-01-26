#!/usr/bin/python

# json
import json

# OS
import os

# FTP
import ftplib

# UUID
import uuid

def Log(Log_Level, Log_Source, Log_Header, Log_Text):
    print ("Log_Level " + Log_Level + " Log_Source: " + Log_Source + " Log_Header: " + Log_Header + " Log_Text: " + Log_Text)
    
Payload = "Test,1,FTP,10.106.149.199"
Config_Dict = {"Hostname":"Test","System_Header":"/Dobby","System_Sub_Header":"","Config_ID":"0","WiFi_SSID":"wifi-iot","WiFi_Password":"103C8B0103C84C00950","MQTT_Broker":"10.106.138.60","MQTT_Port":"1883","MQTT_Username":"DasBoot","MQTT_Password":"NoSinking","MQTT_KeepAlive_Interval":60}

# rm
Log("Info", "UDPConfig", "Upload Config", Payload[0] + " - IP: " + Payload[3])

# Generate unique config id
Config_File_Name = "/var/tmp/Dobby/" + str(uuid.uuid4) + ".json"

# Write json to file
if not os.path.exists("/var/tmp/Dobby/"):
    os.makedirs("/var/tmp/Dobby/")

with open(Config_File_Name, 'w+') as Config_File:
    json.dump(Config_Dict, Config_File)

# Upload file
# FIX - Change user and pass
# session = ftplib.FTP(Payload[3],'esp8266','esp8266')
session = ftplib.FTP("192.168.0.2",'dobby','heretoserve')

# Read file to send
with open(Config_File_Name, 'rb') as Config_File:
    session.storbinary('STOR Dobby.json', open(Config_File_Name, 'rb'))

# upload the file

# close FTP

session.quit()

# Delete file
# os.remove(Config_File_Name)