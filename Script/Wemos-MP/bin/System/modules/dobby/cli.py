# Library for dobby on wemos d1 mini using micropython

import ujson
import sys
import uos
import gc
import machine

import dobby.config as DobbyConfig


# CLI - Allowing for basic config via serial interface
# Messages is done via print and not log since we are ofline at this stage
def Run():
    # Dict to hold config
    Config = {}
    # Print entry message
    print("\n   Dobby Command Line Interface\n")
    # Start eternal input loop
    while True:
        # Get_CLI_Input will break true when the user has requested we boot the system
        # After the needed settings is entered
        # This function is the CLI interface printing information and writing settings
        # Get user entry
        try:
            User_Entry = input("Dobby CLI: ")
        except (EOFError, KeyboardInterrupt):
            # If we got interrupted exit
            print("\n\n   Leaving CLI.\n")
            sys.exit()

        # Check if the 200 pound gorilla pressed enter without entering a command
        if User_Entry == "":
            continue

        # Check what we got from the user
        # ---------------------------------------- Help ----------------------------------------
        elif User_Entry.lower() == "help":
            print()
            print("Options marked with * is required configuration")
            print("Avalible commands:")
            print()
            print("   System:")
            print("      boot - Boots the system after neede settings have been entered")
            print("      cat <path> - Prints the content of a file from path")
            print("      config check - Lists all missing settings needed to start Dobby")
            print("      config delete <config name or path> - Deleted the config with the given name or path")
            print("      config dir - Lists all the config files in '/conf'")
            print("      config list - Lists all settings needed to start Dobby and the current value")
            print("      config load <path> - Default: /conf/device.json - Loads the given config")
            print("      config save - Saves the config to file system")
            print("      free memory - Prints the amount of free memory")
            print("      json - Paste a json config string")
            print("      ll <path> - Default: / - Lists content of path")
            print("      log level <1-5> - Default: 1 - 0: Debug - 1: Info - 2: Warning - 3: Error - 4: Critical - 5: Fatal")
            print()
            print("   Communication:")
            print("      wifi ssid <ssid> *")
            print("      wifi password <password> *")
            print()
            print("      mqtt broker <ip address> *")
            print("      mqtt port <port> - Default: 1883")
            print("      mqtt user <username> *")
            print("      mqtt password <password> *")
            print()
            print()
            continue


        # ---------------------------------------- Boot ----------------------------------------
        elif User_Entry.lower() == "boot":

            # Add default settings if needed
            Config.update(DobbyConfig.Defaults_Device(Config))

            # Check if we got all needed settings
            if DobbyConfig.Check_Device(Config) == True:
                # Save config to fs
                try:
                    DobbyConfig.Save('device.json', Config)
                except DobbyConfig.Error as e:
                    print("   " + str(e))
                else:
                    # Log event
                    print("   Base config OK. Rebooting")
                    # Reboot the device since there is not enough memory to load dobby
                    machine.reset()
            else:
                print("   Base config requirements not met unable to boot")
                continue
        

        # ---------------------------------------- cat ----------------------------------------
        elif User_Entry.lower().startswith("cat ") == True:
            # Check if we got a config store on local fs
            try:
        
                f = open(User_Entry[4:])
                cat_String = f.read()
                f.close()
            # No config store on fs or other error
            except OSError as e:
                print("   File: " + str[User_Entry[4:]])
                continue





        # ---------------------------------------- Config * ----------------------------------------
        elif User_Entry.lower().startswith("config ") == True:

            # User_Entry[7:] = remove "config " or "CONFIG " or any other combination there of
            User_Entry = User_Entry[7:]


            # ---------------------------------------- Config check ----------------------------------------
            if User_Entry.lower() == "check":
                # Check if we got all needed settings
                if DobbyConfig.Check_Device(Config) == True:
                    print("   Check passed")
                else:
                    print("   Check failed")
                # continue so we dont trigger unknown command
                continue


            # ---------------------------------------- Config delete ----------------------------------------
            elif User_Entry.lower().startswith("delete ") == True:
                User_Entry = User_Entry[7:]
                # Delete file and get resoult
                Resoult = DobbyConfig.Delete(User_Entry)
                if Resoult == True:
                    print("   Config file deleted: " + User_Entry)
                else:
                    print("   Unable to delete config file: " + User_Entry)
                continue
            

            # ---------------------------------------- Config dir ----------------------------------------
            elif User_Entry.lower() == "dir":

                # for loop to print files in config dir
                for Entry in uos.listdir('/conf'):
                    # print each line stripping ".json" from file name
                    print("   ", Entry.replace(".json", ""))
                continue


            # ---------------------------------------- Config list ----------------------------------------
            elif User_Entry.lower() == "list":
                List_String = ""

                # Add default if missing
                Config.update(DobbyConfig.Defaults_Device(Config))

                # Generate string
                Print_String = ""
                for Key, Value in Config.items():
                    Print_String = Print_String + "   " + str(Key.replace('_', " ")) + ": " + str(Value) + "\n"

                print("\n" + Print_String)
                continue

            
            # ---------------------------------------- Config load ----------------------------------------            
            elif User_Entry.lower().startswith("load") == True:
                # Load with no config specified defaulting to /conf/device.json
                if User_Entry.lower() == "config load":
                    # Load the config
                    Config = DobbyConfig.Load(Config_Name = 'device', Delete_On_Error=False)
                else:
                    # Load the config
                    Config = DobbyConfig.Load(Config_Name = None, Delete_On_Error = False, Full_Path=User_Entry[12:])
                # Check if we cloud load the config
                if Config == False:
                    Config = {}
                    print("   Unable to load config")
                    # Add defaults
                    Config.update(DobbyConfig.Defaults_Device(Config))
                else:
                    # Add defaults
                    Config.update(DobbyConfig.Defaults_Device(Config))
                    print("   Gonfig loaded")
                continue


            # ---------------------------------------- Config Save ----------------------------------------
            elif User_Entry.lower() == "save":
                # Try to save config
                try:
                    DobbyConfig.Save('device.json', Config)
                except DobbyConfig.Error as e:
                    print("   " + str(e))
                else:
                    # Log event
                    print("   Config saved to: /conf/device.json")
                    # Reboot the device since there is not enough memory to load dobby
                    machine.reset()

            # ---------------------------------------- Unknown command ----------------------------------------
            # Remember continue above so we dont trigger this
            else:
                print("Unknown config command: " + User_Entry)
                # since the 200 pound gorilla entered "config " and then someting incorrect
                # we need to continue because it was a config command and we dont need to check for other matchers
                continue

                


        # ---------------------------------------- Header ----------------------------------------
        elif User_Entry.lower().startswith("header ") == True:
            Config["Header"] = User_Entry
            continue
        # Hostname
        elif User_Entry.lower().startswith("hostname ") == True:
            Config["Hostname"] = User_Entry[9:]
            continue
        # Exit
        elif User_Entry.lower() == "exit":
            print("Quitting Dobby...")
            sys.exit()
        # free memory
        elif User_Entry.lower() == "free memory":
            print('   Free memory: ' + str(gc.mem_free()))
            continue

        # json
        elif User_Entry.lower() == "json":
            # Get json string from user
            json_Config = input("Please paste json config string: ")

            # Try to parse json
            try:
                # parse json to config dict
                Config = ujson.loads(json_Config)
            except ValueError:
                print()
                print("   Invalid json string")
                print()
                continue
            # Add default settings if needed
            Config.update(DobbyConfig.Defaults_Device(Config))
            # Log Event
            print("   json config ok")
            continue

        # log level
        elif User_Entry.lower().startswith("log level ") == True:
            # Check if the log level is valid
            ## Invalid level
            if int(User_Entry[10:]) not in range(0, 6):
                print()
                print("   Incorrect log level: " + User_Entry[10:])
                print()
            ## Valid level
            else:
                Config["Log_Level"] = int(User_Entry[10:])
            continue
        # ll
        elif User_Entry.lower().startswith("ll") == True:
            ll_Resoult = ""
            # ll /
            if User_Entry.lower() == "ll":
                ll_Resoult = uos.listdir()
            # ll <path>
            else:
                # Try to list path
                try:
                    ll_Resoult = uos.listdir(User_Entry[3:])
                # If failed report dir missing
                except OSError:
                    print()
                    print("   No sucth dir: " + User_Entry[3:])
                    print()
                    continue
            # Print listdir
            print()
            print(ll_Resoult)
            print()
            # continue so we dont trigger unknown command
            continue




        # ---------------------------------------- wifi ----------------------------------------
        elif User_Entry.lower().startswith("wifi ") == True:
            # User_Entry[5:] = remove "wifi " or "WIFI " or any other combination there of
            # wifi SSID
            if User_Entry[5:].lower().startswith("ssid ") == True:    
                Config["WiFi_SSID"] = User_Entry[10:]
                continue
            # wifi Password
            elif User_Entry[5:].lower().startswith("password ") == True:
                Config["WiFi_Password"] = User_Entry[14:]
                continue

        # ---------------------------------------- mqtt ----------------------------------------
        elif User_Entry.lower().startswith("mqtt ") == True:
            # User_Entry[5:] = remove "mqtt " or "MQTT " or any other combination there of
            # MQTT broker
            if User_Entry[5:].lower().startswith("broker ") == True:    
                Config["MQTT_Broker"] = User_Entry[12:]
                continue
            # MQTT Port
            elif User_Entry[5:].lower().startswith("port ") == True:    
                Config["MQTT_Port"] = User_Entry[10:]
                continue
            # MQTT Username
            elif User_Entry[5:].lower().startswith("user ") == True:    
                Config["MQTT_Username"] = User_Entry[10:]
                continue
            # MQTT Password
            elif User_Entry[5:].lower().startswith("password ") == True:
                Config["MQTT_Password"] = User_Entry[14:]
                continue


        # ---------------------------------------- Unknown command ----------------------------------------
        # Remember continue above so we dontr trigger this
        else:
            print("Unknown command: " + User_Entry)


    print()
    print("   Exitting Dobby Command Line Interface.")
    print()