#!/usr/bin/python3

import logging

import threading
import time

class Init:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):

        # Version number
        self.Version = 300000
        # Referance to dobby
        self.Dobby = Dobby
        # Referance to ddb
        self.ddb = Dobby.ddb
        # Referance to Log
        self.Log = Dobby.Log
        # Name of db we are logging to
        self.Log_db = self.ddb.Run('SELECT Value FROM `Dobby_Config`.`Logging Device` WHERE Name="Target";')
        # Log event
        self.Log.Info("Logging Device", "Version: " + str(self.Version))

        # Subscribe to topic
        self.Dobby.MQTT.Subscribe(self.Dobby.System_Header + "/+/Log/#", self.On_Message, Build_Topic=False)


    # -------------------------------------------------------------------------------------------------------
    def Save_Message(self, message, Retry=False):

        Payload = message.payload.decode('utf-8')

        if Retry == False:
            # Log to termin if verbose is set
            self.Log.Print("DeviceLog", message.topic + " - " + Payload)

        # Using Owner as temp var
        Owner = message.topic.replace(self.Dobby.System_Header + "/", '')
        Owner = Owner.split("/")

        Device_Name = Owner[0]
        Log_Level = Owner[2]
        Owner = Owner[3]

        Retry = False

        db_Connection = self.ddb.Connect(self.Log_db)

        self.ddb.Run("SET autocommit = 1;", Connection=db_Connection)
            
        # try to write message to db before any checks
        try:
            self.ddb.Run("INSERT INTO `" + Device_Name + "` (`Level`, `Owner`, `Message`) VALUES ('" + Log_Level + "', '" + Owner + "', '" + Payload + "');", Connection=db_Connection)
        except self.ddb.Error as e:
            if str(e) == "Missing table":
                self.ddb.Run("CREATE TABLE `" + Device_Name + "` (`id` int(11) NOT NULL AUTO_INCREMENT, `Level` varchar(8) NOT NULL, `Owner` varchar(95) NOT NULL, `Message` varchar(90) NOT NULL, `DateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`), UNIQUE KEY `id_UNIQUE` (`id`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;", Connection=db_Connection)
                Retry = True
            else:
                print("FIX THIS: " + str(e))
        finally:
            if Retry == True:
                self.Save_Message(message, Retry=True)

        self.ddb.Disconnect(db_Connection)


    # -------------------------------------------------------------------------------------------------------
    def On_Message(self, client, userdata, message):

        # Start a thread and pass message to Save_Message
        threading.Thread(target=self.Save_Message, args=(message,), daemon=True).start()
