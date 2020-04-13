#!/usr/bin/python3

import os
import argparse
import time
import json

# Dobby modules
import dlogging as Log
import ddb
import dmqtt

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

        self.Version = 300000

        # Init ddb aka database interface
        # Needs to be up before we init log
        self.ddb = ddb.Init('dobby', 'HereToServe')

        # Init logging
        self.Log = Log.Init(self, Verbose)

        # Added in front of mqtt topics
        self.System_Header = self.ddb.Run('SELECT Value FROM Dobby_Config.Main WHERE Name="System Header";')

        # MQTT
        self.MQTT = dmqtt.Init(self)

        # Device Logging
        self.Logging_Device = None

        # System modules aka modules loaded based on configs present in ../../Config/System/ relative to this path
        self.System_Modules = {}

        # True if we are logging device messages
        if self.ddb.Run('SELECT Value FROM Dobby_Config.`Logging Device` WHERE Name="Enable";').lower() == 'true':
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

            # strip .jsonc
            Config_Name = Config_Name.replace('.json', '')
            
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