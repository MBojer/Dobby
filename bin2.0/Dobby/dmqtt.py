#!/usr/bin/python3

import os

# MQTT
import paho.mqtt.client as MQTT

class Init:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exc
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):

        self.Version = 300000

        # Referance to dobby
        self.Dobby = Dobby
        # Referance to ddb
        self.ddb = Dobby.ddb
        # Referance to Dobby.Log
        self.Log = Dobby.Log

        # self.Dobby.Config["MQTT Broker"] = self.ddb.Run('SELECT Value FROM Dobby_Config.Main WHERE Name="MQTT Broker";')
        # Username = self.ddb.Run('SELECT Value FROM Dobby_Config.Main WHERE Name="MQTT Username";')
        # Password = self.ddb.Run('SELECT Value FROM Dobby_Config.Main WHERE Name="MQTT Password";')
        
        # Create the client
        self.Client = MQTT.Client(client_id="Dobby-" + str(os.urandom(1)[0] %1000), clean_session=True)        

        # Set callbacks
        self.Client.on_connect = self.On_Connect

        # Check if password is configured
        if self.Dobby.Config.get('Password', None) != None:
            # If password is not set will get None and thats ok :-)
            self.Client.username_pw_set(self.Dobby.Config["Username"], password=self.Dobby.Config["Password"])

        # connect
        self.Client.connect_async(self.Dobby.Config["MQTT Broker"], port=1883, keepalive=60, bind_address="")
        # Start loop
        self.Client.loop_start()

        # True if connected
        self.Connected = False

        # Dict of topics we need to subscribe to on connect
        # with callback as value
        # Add commands
        self.Subscribe_To = {
                self.Dobby.Config['System Header'] + "/Dobby/Commands": self.Commands,
            }


    # -------------------------------------------------------------------------------------------------------
    def On_Disconnect(self, client, userdata, rc):
        if self.Connected != False:
            # Note we are NOT connected
            self.Connected = False
            if rc != 0:
                # Log event
                self.Log.Error("MQTT", "Unexpect disconnect from broker: " + str(self.Dobby.Config["MQTT Broker"]) + " Error: " + str(rc))
            else:
                # Log event
                self.Log.Debug("MQTT", "Disconnect from broker: " + str(self.Dobby.Config["MQTT Broker"]) + " Error: " + str(rc))
        
        
    # -------------------------------------------------------------------------------------------------------
    def On_Connect(self, client, userdata, flags, rc):
        
        if rc == 0:
            pass
        elif rc == 1:
            Error_Text = 'Connection refused - incorrect protocol version'
        elif rc == 2:
            Error_Text = 'Connection refused - invalid client identifier'
        elif rc == 3:
            Error_Text = 'Connection refused - server unavailable'
        elif rc == 4:
            Error_Text = 'Connection refused - bad username or password'
        elif rc == 5:
            Error_Text = 'Connection refused - not authorised'
        else:
            Error_Text = 'Unknown rc code: ' + str(rc)

        # NOT connected to broker
        if rc != 0:
            # Log event
            self.Log.Error("MQTT", "Unable to connect to broker: " + str(self.Dobby.Config["MQTT Broker"]) + " Error: " + str(rc) + " - " + Error_Text)
            # Note we are NOT connected
            self.Connected = False

        # Connected to broker
        else:
            # Note that we are connected
            self.Connected = True
            # Log event
            self.Log.Info("MQTT", "Connect to broker: " + str(self.Dobby.Config["MQTT Broker"]))
            # Subscribe to topics
            for Topic, Callback in self.Subscribe_To.items():
                # Log event
                self.Log.Info("MQTT", "Subscribing to: " + Topic)
                # Subscribe to topic
                self.Client.subscribe(Topic, 0)
                # Register callback
                self.Client.message_callback_add(Topic, Callback)


    # -------------------------------------------------------------------------------------------------------
    def Publish(self, Owner, Payload, Retained=False, Build_Topic=True):
        
        if Build_Topic == True:
            Owner = self.Build_Topic(Owner)
        
        self.Client.publish(Owner, payload=Payload, retain=Retained)


    # -------------------------------------------------------------------------------------------------------
    def Subscribe(self, Topic, Callback, Build_Topic=True):
        
        if Build_Topic == True:
            Topic = self.Build_Topic(Topic)

        if Topic not in self.Subscribe_To:
            # Add to self.Subscribe_To
            self.Subscribe_To[Topic] = Callback

        if self.Connected == True:
            # Log event
            self.Log.Info("MQTT", "Subscribing to: " + str(Topic))
            # Subscribe to topic
            self.Client.subscribe(Topic, 0)
            # Register callback
            self.Client.message_callback_add(Topic, Callback)


    # -------------------------------------------------------------------------------------------------------
    def Build_Topic(self, Owner):
        Topic = self.Dobby.Config['System Header'] + "/Dobby" + Owner


    # -------------------------------------------------------------------------------------------------------
    def Commands(self, client, userdata, message):
        
        self.Log.Info("MQTT/Commands", str(message.payload))