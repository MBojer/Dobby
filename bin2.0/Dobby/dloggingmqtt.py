#!/usr/bin/python3

import logging

import threading
import datetime


class Init:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):

        # Version number
        self.Version = 300000
        # Log event
        Dobby.Log.Info("Logging MQTT", "Version: " + str(self.Version))

        # Name of db we are logging to
        Agent_Info = Dobby.ddb.Run('SELECT `Name`, `Target` FROM Dobby_Config.`Logging MQTT`;', All=True)

        Agents = {}

        for Agent in Agent_Info:
            # Get values
            Name = Agent[0]
            Target = Agent[1]
            # Create and store agent
            Agents[Name] = self.Agent(Dobby, Name, Target)


    class Agent:

        # -------------------------------------------------------------------------------------------------------
        # Custom Exception
        class Error(Exception):
            pass

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Name, Target):

            # Log event
            Dobby.Log.Info("LoggingMQTT", "Starting agent: " + str(Name))

            self.Name = Name
            self.Target = Target

            self.Log = Dobby.Log
            self.ddb = Dobby.ddb

            # Subscribe to topic
            Dobby.MQTT.Subscribe(Target, self.On_Message, Build_Topic=False)




        # -------------------------------------------------------------------------------------------------------
        def Save_Message(self, message, Retry=False):

            Payload = str(message.payload.decode('utf-8'))

            if Retry == False:
                # Log to termin if verbose is set
                self.Log.Print("LoggingMQTT", message.topic + " - " + Payload)

            Retry = False

            db_Connection = self.ddb.Connect("Dobby_Logging_MQTT")

            self.ddb.Run("SET autocommit = 1;", Connection=db_Connection)
                
            # try to write message to db before any checks
            try:
                self.ddb.Run("INSERT INTO `" + self.Name + "` (`Value`) VALUES ('" + Payload + "');", Connection=db_Connection)
            except self.ddb.Error as e:
                if str(e) == "Missing table":
                    self.ddb.Run("CREATE TABLE `" + self.Name + "` (`id` int(11) NOT NULL AUTO_INCREMENT, `Value` varchar(95) NOT NULL, `DateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`), UNIQUE KEY `id_UNIQUE` (`id`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;", Connection=db_Connection)
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
