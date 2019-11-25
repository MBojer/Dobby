import ujson
import sys
import os
import gc
import dobbyconfigload


# -------------------------------------------------- Config load --------------------------------------------------
def Config_Load(Config_Path, Delete_On_Error=True):
        # Reads config from Config_Path and returns a dict containing json from file
        # Returns false if unable to load config
        
        # Check if we got a config store on local fs
        try:
            f = open(Config_Path)
            fs_Config = f.read()
            f.close()

        # No config store on fs or other error
        except:
            return False
        
        # Try to phrase json
        try:
            return_json = ujson.loads(fs_Config)
        except ValueError:
            # if fails, delete config file if told to do so
            if Delete_On_Error is True:
                os.remove(Config_Path)
                # return false to indicate failure
            return False
        
        # return config dict    
        return return_json
        

# -------------------------------------------------------------------------------------------------------
# Saves the current Config Dict to json string in /Dobby.json on the filesystem
def Config_Save(Config_File, Config):
    # Check if we got the minimim required config
    if Config_Base_Check(Config) is not True:
        print("   Unable to save config: Minimum config requirements not met")
        return False
    # Save config to fs
    f = open('/conf/' + str(Config_File), 'w')
    f.write(ujson.dumps(Config))
    f.close()
    # Log event
    print("   Config saved")


# -------------------------------------------------------------------------------------------------------
# Returns a dict containing the missing default settings
def Config_Defaults(Config_Dict):
    # Dict with default settings
    Default_Dict = {"Config_ID": "0", "Log_Level": "1", 'MQTT_Port': '1883'}

    Missing_Config_Dict = {}

    for Setting, Value in Default_Dict.items():
        if Config_Dict.get(Setting, None) is None:
            Missing_Config_Dict[Setting] = Value

    # return the Missing_Config_Dict
    return Missing_Config_Dict



# -------------------------------------------------------------------------------------------------------
def Config_Base_Check(Config_Dict):
    # Check if we got the needed settings return false if we are missing something
    Required_List = ["Hostname", "MQTT_Broker", "System_Header", "WiFi_Password", "WiFi_SSID", 'Config_ID', 'Log_Level', 'MQTT_Port']

    # Create a list we can add the missing entries to
    Missing_List = []
    # loop over required entries
    for Entry in Required_List:
        if Config_Dict.get(Entry, None) is None:
            Missing_List.append(Entry)                
    
    # Check if we are missing anything aka the Missing_List is empythy
    if Missing_List != []:
        Missing_String = ""
        for Entry in Missing_List:
            Missing_String = Missing_String + " " + Entry
        # Log event
        ## the missing space after : is already in Missing_String
        print("   Missing config entries:" + Missing_String)
        return False
    # Return true if we got it all
    else:
        return True