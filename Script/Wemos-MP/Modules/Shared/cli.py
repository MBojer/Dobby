#!/usr/bin/python

## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300000

import machine
import ujson
import uos
import sys
import config as dConfig

class Run:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):
        
        # Dict to hold config
        Config = {}
        # Try to load network.json to 'Config'
        # if failes create an empthy dict 
        try:
            # Try to load config
            Config = dConfig.Load('network')
        except:
            # Create empthy dict on failure
            Config = {}

        # print cli init message
        print("Starting cli")
        print("Please configure:")
        print("   Hostname")
        print("   WiFi SSID")
        print("   WiFi Password")
        print("   MQTT Broker")
        print("")

        # start eternal loop while getting user 
        while True:
            try:
                User_Entry = input("Dobby CLI: ")
            except (EOFError, KeyboardInterrupt):
                # If we got interrupted exit
                print("   Leaving CLI")
                sys.exit()

            # Check if the 200 pound gorilla pressed enter without entering a command
            if User_Entry == "":
                continue

            # ---------------------------------------- Help ----------------------------------------
            elif User_Entry.lower() == "help":
                print()
                print("Avalible commands:")
                print()
                print("   boot - boot the device")
                print("   json - past device config as a json string")
                print("   show - shows the loaded config")
                print("   module list - lists all installed modules")
                print("   module delete - delete a installed module")
                print("   set <config> <to> - sets 'Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker'")
                print()

            # ---------------------------------------- boot ----------------------------------------
            # reboots the device
            # if required settings is give
            # saves config to fs first
            elif User_Entry.lower() == "boot":
                # check if config is ok
                try:
                    dConfig.Check(Config, ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker'])
                except Dobby.Error as e:
                    print("   Missing config: " + str(e))
                    continue
                    
                # save config to file
                if dConfig.Save(Config, 'network') == False:
                    print("   Unable to save config")
                    continue

                # Log event
                print("   Config saved rebooting")
                # Reboot the device
                machine.reset()


            # ---------------------------------------- set ----------------------------------------
            # prints the current config
            elif User_Entry.lower() == "set":

                # List of options user can change
                Config_Options = ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker', 'Log Level']

                # print list with number in front
                for i in range(len(Config_Options)):
                    print("   " + str(i) + " - " + str(Config_Options[i]))

                # Get config option number from user
                try:
                    print()
                    print("Press CTRL + C to cancle")
                    print()
                    Selected_Option = input("Please select config to change: ")
                    # Convert selection to int
                    Selected_Option = int(Selected_Option)
                    # check config exists in list
                    Config_Options[Selected_Option]
                except (EOFError, KeyboardInterrupt):
                    print("   canceled")
                except (ValueError, IndexError):
                    print("   invalid config selected: " + str(Selected_Option))
                else:
                    
                    # Get config option number from user
                    try:
                        print()
                        New_Value = input("Please enter new value for " + Config_Options[Selected_Option] + ": ")
                    except (EOFError, KeyboardInterrupt):
                        print("   canceled")
                    else:
                        # change config value
                        Config[Config_Options[Selected_Option]] = New_Value
                        # Log event
                        print("   Config: " + str(Config_Options[Selected_Option]) + " set to: " + str(New_Value))


            # ---------------------------------------- show ----------------------------------------
            # prints the current config
            elif User_Entry.lower() == "show":
                print("Current config:")
                for Key in ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker', 'Log Level']:
                    print("   " + Key + ": " + Config.get(Key, "Not configured"))


            # ---------------------------------------- json ----------------------------------------
            # past device config as a json string
            elif User_Entry.lower() == "json":
                # Get json string from user
                json_Config = input("Please paste device config json string: ")

                # Try to parse json
                try:
                    # parse json to config dict
                    json_Config = ujson.loads(json_Config)
                # Error in json string
                except ValueError:
                    print()
                    print("   Invalid json string")
                    print()
                    continue
                # Json loaded ok, check if we got the needed config
                else:
                    Check_List = ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker']
                    try:
                        dConfig.Check(json_Config, Check_List)
                    except Dobby.Error as e:
                        # Log error
                        print("   Missing config entries: " + str(e))
                        continue
                    # if we got a large config for some reason only take what we need aka keys in the check list
                    for Key in Check_List:
                        # Save value from json_Config in Config var
                        Config[Key] = json_Config[Key]
                    # Log Event
                    print("   json config ok")
                    continue
            
            # ---------------------------------------- module list ----------------------------------------
            # lists all modules
            elif User_Entry.lower() == "module list":
                # print to give distance to above
                print()
                # get list of libs
                Lib_List = uos.listdir('lib')
                # print list with number in front
                for i in range(len(Lib_List)):
                    print("   " + str(i) + " - " + str(Lib_List[i]))
                # Print to give space to command below
                print()


            # ---------------------------------------- module delete ----------------------------------------
            # lists all modules with number in front and lets the user deside what to delete
            # ctrl + c to cancle
            elif User_Entry.lower() == "module delete":
                # print to give distance to above
                print()
                
                # get list of libs
                Lib_List = uos.listdir('lib')

                # print list with number in front
                for i in range(len(Lib_List)):
                    print("   " + str(i) + " - " + str(Lib_List[i]))

                # Get user input
                try:
                    print()
                    print("Press CTRL + C to cancle")
                    print()
                    User_Entry = input("Select module to delete: ")
                except (EOFError, KeyboardInterrupt):
                    print("   canceled")
                else:
                    try:
                        # delete selected lib aka module
                        uos.remove('lib/' + Lib_List[int(User_Entry)])
                    except TypeError:
                        print("   invalid module selected: " + User_Entry)
                    else:
                        print("   deleted module: " + Lib_List[int(User_Entry)])


            # ---------------------------------------- Unknown command ----------------------------------------
            else:
                print("unknown command: " + User_Entry)
