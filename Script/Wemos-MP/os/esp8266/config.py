#!/usr/bin/python3

# Module for dobby on 'wemos d1 mini' or 'wemos mini 32' using micropython

import ujson
import uos
import urequests


## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300000
# -------------------------------------------------------------------------------------------------------
# Custom Exception
class Error(Exception):
    pass

# -------------------------------------------------- Config Download --------------------------------------------------
def Download(Name, Owner):

    # Build config url
    URL = "http://" + Owner.Server + ":" + Owner.Server_Port + "/Config/" + Owner.Hostname + "/" + Name + ".json"

    Server_Config = None

    # Try to get Config
    try:
        Server_Config = urequests.get(URL)
    except OSError as e:
        # if we got an os error the server is not responding
        raise Error("Server not responding")
    else:
        # Check for status code 200 to see if we got the file
        if Server_Config.status_code == 200:
            # Convert Server_Config to dict
            Server_Config = Server_Config.json()
            # Var to hold local config
            Local_Config = {}
            # Check if downloaded config matches server config
            # Try to load local config
            try:
                Local_Config = Load(Name)
            # If we get Error we assume the file is missing
            # Just pass will save it below in finally
            except Error:
                # Log event
                Owner.Log(0, "System/Config", "No local config found for: " + str(Name))
                # Save config
                Save(Server_Config, Name)
                # return true since we save Server_Config
                return True

            finally:
                # the dicts does not match if they are rearanged
                # so we need to loop over and Check each Entry
                # remove from local config on match
                # if local config is not empthy when done
                # then write Server_Config to fs
                for Key in Server_Config:
                    # check if they match
                    if Server_Config[Key] != Local_Config.get(Key, None):
                        # When we break local config will not be empthy and then be reweritten below
                        break
                    else:
                        # remove from local config on match
                        del Local_Config[Key]

                # Local config has something server config does not so will remove it
                if Local_Config != {}:
                    try:
                        Save(Server_Config, Name)
                    except Error as e:
                        # raise Error on failure to save to fs
                        raise Error('Unable to save config: "' + Name + '.json" to fs')
                    else:
                        # Log event
                        Owner.Log(0, "System/Config", "Updated: " + Name)
                        # Return true when we saved the Config
                        # or if local config matches server config
                        return True
                else:
                    # Log event
                    Owner.Log(0, "System/Config", "OK: " + Name)

        # If status code is not 200 raise Error
        else:
            raise Error("Did not get code 200 after get. Config: " + str(Name) + " URL: " + URL)
        

# ---------------------------------------- Config Save ----------------------------------------
def Save(Config, File_Name):
    if type(Config) == str:
        # Try to parse json
        try:
            # parse json to config dict
            Config = ujson.loads(Config)
        # Error in json string
        except ValueError:
            raise Error("Invalid json string provided")
    
    # Try to open config file for writing
    try:
        with open('/conf/' + File_Name + '.json', 'w') as f:
            # write config file to device
            ujson.dump(Config , f)
    except:
        raise Error("Unable to save file")


# ---------------------------------------- Config Load ----------------------------------------
def Load(File_Name):
    # Var to hold loaded config
    Config = None
    # Try to read device config file
    try:
        with open('/conf/' + File_Name + '.json', 'r') as f:
            Config = ujson.load(f)
    # OSError = Missing network.json
    except OSError:
        raise Error("Config not found: " + str(File_Name))
    except ValueError:
        # If the local config contains an error will delete it
        uos.remove('/conf/' + File_Name + '.json')
        # raise Error
        raise Error("Error in json: " + str(File_Name) + " - Local config removed")
    else:
        return Config


# ---------------------------------------- Config Check ----------------------------------------
def Check(Config_Dict, Check_List):
    # Check if we got the needed config
    Failed = []

    for Entry in Check_List:
        if Config_Dict.get(Entry, None) == None:
            Failed.append(Entry)
            
    # Check if we failed
    if Failed != []:
        raise Error(Failed)
    else:
        return True

