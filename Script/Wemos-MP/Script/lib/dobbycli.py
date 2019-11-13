# Library for dobby on wemos d1 mini using micropython

import ujson
import sys
import os
import gc

import dobbyconfig

# CLI - Allowing for basic config via serial interface
# Messages is done via print and not log since we are ofline at this stage
def CLI():
    # Dict to hold config
    Config = {}
    # Print entry message
    print()
    print("   Dobby Command Line Interface.")
    print()
    # Start eternal input loop
    while True:
        # Get_CLI_Input will break true when the user has requested we boot the system
        # After the needed settings is entered
        # This function is the CLI interface printing information and writing settings
        # Get user entry
        User_Entry = input("Dobby CLI: ")

        # Check what we got from the user
        # ---------------------------------------- Help ----------------------------------------
        if User_Entry.lower() is "help":
            print()
            print("Options marked with * is required configuration")
            print("Avalible commands:")
            print()
            print("   System:")
            print("      boot - Boots the system after neede settings have been entered")
            print("      cat <path> - Prints the content of a file from path")
            print("      config check - Lists all missing settings needed to start Dobby")
            print("      config list - Lists all settings needed to start Dobby and the current value")
            print("      config load <path> - Default: /Dobby.json - Loads the given config")
            print("      config save - Saves the config to file system")
            print("      memory - Prints the amount of free memory")
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

        # ---------------------------------------- System ----------------------------------------
        # Boot
        if User_Entry.lower() is "boot":
            # Add default settings if needed
            Config.update(dobbyconfig.Config_Defaults(Config))
            # Check if we got all needed settings
            if dobbyconfig.Config_Base_Check(Config) is True:
                # Save config to fs
                dobbyconfig.Config_Save('device.json', Config)
                # Log event
                print("   Base config OK. Booting")
                # Break to continue booting
                break
            else:
                print("   Base config requirements not met unable to boot")
                continue
        
        # cat
        elif User_Entry.lower().startswith("cat ") is True:
            # Check if we got a config store on local fs
            try:
                f = open(User_Entry[4:])
                cat_String = f.read()
                f.close()
            # No config store on fs or other error
            except OSError as e:
                print("No local config avalible")
                continue
            
            print()
            print(cat_String)
            print()
            continue

        # Config
        elif User_Entry.lower().startswith("config ") is True:
            # User_Entry[7:] = remove "config " or "CONFIG " or any other combination there of
            # List
            if User_Entry[7:].lower() is "list":    
                print()
                print("   hostname: " + str(Config.get("Hostname", "")))
                print("   mqtt broker: " + str(Config.get("MQTT_Broker", "")))
                print("   system header: " + str(Config.get("System_Header", "")))
                print("   wifi password: " + str(Config.get("WiFi_Password", "")))
                print("   wifi ssid: " + str(Config.get("WiFi_SSID", "")))
                print()
                continue
            # config load
            if User_Entry[7:].lower().startswith("load ") is True:
                Config = dobbyconfig.Config_Load(User_Entry[12:])
                continue
            
            # config check
            if User_Entry[7:].lower() is "check":
                # Check if we got all needed settings
                if dobbyconfig.Config_Base_Check(Config) is True:
                    print("   Check passed")
                # continue so we dont trigger unknown command
                continue
            # Save
            if User_Entry[7:].lower() is "save":
                # Try to save config
                dobbyconfig.Config_Save('device.json', Config)
                continue

        # Header
        elif User_Entry.lower().startswith("header ") is True:
            Config["Header"] = User_Entry[7:]
            continue
        # Hostname
        elif User_Entry.lower().startswith("hostname ") is True:
            Config["Hostname"] = User_Entry[9:]
            continue
        # Exit
        elif User_Entry.lower() is "exit":
            print("Quitting Dobby...")
            sys.exit()
        # Memory
        elif User_Entry.lower() is "memory":
            print('   Free memory: ' + str(gc.mem_free()))
            continue
        # json
        elif User_Entry.lower() is "json":
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
            Config.update(dobbyconfig.Config_Defaults(Config))
            # Log Event
            print("   json config applied")
            continue
        # log level
        elif User_Entry.lower().startswith("log level ") is True:
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
        elif User_Entry.lower().startswith("ll") is True:
            ll_Resoult = ""
            # ll /
            if User_Entry.lower() is "ll":
                ll_Resoult = os.listdir()
            # ll <path>
            else:
                # Try to list path
                try:
                    ll_Resoult = os.listdir(User_Entry[3:])
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
        elif User_Entry.lower().startswith("wifi ") is True:
            # User_Entry[5:] = remove "wifi " or "WIFI " or any other combination there of
            # wifi SSID
            if User_Entry[5:].lower().startswith("ssid ") is True:    
                Config["WiFi_SSID"] = User_Entry[10:]
                continue
            # wifi Password
            elif User_Entry[5:].lower().startswith("password ") is True:
                Config["WiFi_Password"] = User_Entry[14:]
                continue

        # ---------------------------------------- mqtt ----------------------------------------
        elif User_Entry.lower().startswith("mqtt ") is True:
            # User_Entry[5:] = remove "mqtt " or "MQTT " or any other combination there of
            # MQTT broker
            if User_Entry[5:].lower().startswith("broker ") is True:    
                Config["MQTT_Broker"] = User_Entry[12:]
                continue
            # MQTT Port
            elif User_Entry[5:].lower().startswith("port ") is True:    
                Config["MQTT_Port"] = User_Entry[10:]
                continue
            # MQTT Username
            elif User_Entry[5:].lower().startswith("user ") is True:    
                Config["MQTT_Username"] = User_Entry[10:]
                continue
            # MQTT Password
            elif User_Entry[5:].lower().startswith("password ") is True:
                Config["MQTT_Password"] = User_Entry[14:]
                continue


        # ---------------------------------------- Unknown command ----------------------------------------
        # Remember continue above so we dontr trigger this
        # Check if we got Enter and noting else if not print unknown command
        if User_Entry is not "":
            print("Unknown command: " + User_Entry)



    print()
    print("   Exitting Dobby Command Line Interface.")
    print()