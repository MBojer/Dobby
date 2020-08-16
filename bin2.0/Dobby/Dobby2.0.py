#!/usr/bin/python3

import os
import argparse
import time
import json

# Dobby modules
import dlogging as Log
import ddb
import dmqtt

# Script version
Version = 0.01

# Execution options
# Instantiate the parser
parser = argparse.ArgumentParser(description='Serving the master')

parser.add_argument('--verbose', action='store_true',
                    help='Prints ALL Log output to terminal')
        
parser.add_argument("--version", help="prints the script version and quits",
                    action="store_true")

# Save or act on arugments
# Parse arguemnts
Dobby_Arugments = vars(parser.parse_args())

# Save or act on arugments
# Verbose
if Dobby_Arugments.get('verbose', False) is True: 
    Verbose = True
else:
    Verbose = False

# Version
if Dobby_Arugments.get('version', False) is True:
    print("Dobby script version: " + str(Version))
    quit()

# Remove vars from argues from memory
del parser
del Dobby_Arugments


class Main:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Verbose):

        self.Version = Version

        # Init ddb aka database interface
        # Needs to be up before we init log
        self.ddb = ddb.Init('dobby', 'HereToServe')

        # Init logging
        self.Log = Log.Init(self, Verbose)

        # Createa a dict to hold the config
        self.Config = dict()

        # Load Dobby config
        try:
            with open("../../Config/System/Dobby.json", 'r') as f:
                Config = json.load(f)

        except json.decoder.JSONDecodeError as e:
            self.Log.Fatal("System", "Json error in Dobby.json, unable to start. Quitting...")
            quit()

        # Config loaded and prased
        else:
            self.Config = Config

        # List to hold missing config entries
        Missing = list()
        # Loop over needed list
        for Check in ['System Header', 'MQTT Broker']:
            if Check not in self.Config:
                Missing.append(Check)

        # Check if we got needed config
        if Missing != list():
            self.Log.Fatal("System", "Missing config entries: " + str(Missing) + " in Dobby.json, unable to start. Quitting...")
            quit()

        # MQTT
        self.MQTT = dmqtt.Init(self)

        # Device Logging
        self.Logging_Device = None

        # System modules aka modules loaded based on configs present in ../../Config/System/ relative to this path
        self.System_Modules = {}

        # True if we are logging device messages
        if self.Config.get('Device Logging', False) == True:
            self.Log.Info("System", "Loading: Logging Device")
            # Import dloggingdevice so we can init it
            import dloggingdevice
            # init dloggingdevice to make it run as requested
            self.Logging_Device = dloggingdevice.Init(self)


        # ++++++++++++++++++++++++++++++ logging mqtt ++++++++++++++++++++++++++++++
        self.Log.Info("System", "Loading: Logging MQTT")
        # Import dloggingdevice so we can init it
        import dloggingmqtt
        # init dloggingmqtt to make it run as requested
        self.Logging_MQTT = dloggingmqtt.Init(self)


        # ++++++++++++++++++++++++++++++ Load modules ++++++++++++++++++++++++++++++
        # init modules based on config files
        for Config_Name in os.listdir('../../Config/System'):

            # strip .json
            Config_Name = Config_Name.replace('.json', '')

            # Skip if config is Dobby.json
            if Config_Name == "Dobby":
                continue
            
            # Load config
            try:
                with open("../../Config/System/" + Config_Name + ".json", 'r') as f:
                    Config = json.load(f)

            except KeyboardInterrupt as e:
                self.Log.Error("System", "Config: " + Config_Name + " os error: " + str(e))
            
            except json.decoder.JSONDecodeError as e:
                self.Log.Error("System", "Config: " + Config_Name + " contains json error: " + str(e))

            # Config loaded and prased
            else:
                # Try to import
                Module = __import__(Config_Name)
                # Store objevt in self.Modules
                # Pass config and get perifical object
                # Remember to pass Shared aka self so we can log in Button and use dobby variables
                self.System_Modules[Config_Name] = Module.Init(self, Config)


    # -------------------------------------------------------------------------------------------------------
    def Loop(self):

        print("STARTING LOOP")
        print("STARTING LOOP")
        print("STARTING LOOP")
        
        while True:
            time.sleep(0.01)


# -------------------------------------------------------------------------------------------------------
# Init main script
Dobby = Main(Verbose)

# Del Verbose since we are done using it
del Verbose

# Start Dobby aka main loop
Dobby.Loop()

print("FIX - ADD CLEANUP")
print("FIX - ADD CLEANUP")
print("FIX - ADD CLEANUP")
print("FIX - ADD CLEANUP")