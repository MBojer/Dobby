import ujson
import uos
import sys
import gc


# -------------------------------------------------- Config exception --------------------------------------------------
class DobbyConfigError(Exception):
    def __init__(self, Message, Errors):

        super().__init__(Message)

        # Should be a list of errors recived
        self.Errors = Errors


# -------------------------------------------------- Config load --------------------------------------------------
def Load(Config_Name=None, Delete_On_Error=True, Full_Path=None):
    # Reads config /<Path>/<Name>.json and returns a dict containing json from file
    # Unless Full_Path is specified, Full_Path has to contain the full path including file name
    # Returns false if unable to load config

    # Add .json to name if not already there
    if Config_Name.endswith(".json") == False:
        Config_Name = Config_Name + ".json"

    # Check if we got a path to load
    if Config_Name == None and Full_Path == None:
        return {}
    
    # Check if we got a config store on local fs
    try:
        if Full_Path != None:
            f = open(Full_Path)
        else:
            f = open("/conf/" + Config_Name)
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
        if Delete_On_Error == True:
            if Full_Path != None:
                uos.remove(Full_Path)
            else:
                uos.remove("/conf/" + Config_Name)
            # return false to indicate failure
        return False
    
    # return config dict    
    return return_json
    

# -------------------------------------------------------------------------------------------------------
def Save(Config_Name, Config_Dict, Path='/conf'):
    # Saves the provided config dict to a json /<Path>/<Config_Name>.json

    # Dont check path if its the default value
    if Path == "/conf":
        pass
    # "" = root
    elif Path == "":
        Path = "/"
    # Do nothing is path is "/"
    elif Path == "/":
        pass
    # Ends with / then remove it
    elif Path.endswith("/"):
        # Remove the last /
        Path[:-1]

    # Add .json if missing
    if Config_Name.endswith('.json') == False:
        Config_Name = Config_Name + ".json"

    # Try to write file
    try:
        f = open(str(Path) + "/" + str(Config_Name), 'w')
        f.write(ujson.dumps(Config_Dict))
        f.close()
    # PRoberly missing folder
    except OSError as e:
        Error_List = [e]
        # Missing dir
        if "Errno 2" in str(e):
            # Create missing dirs, we are not checking if they already exist just ignoreing the error
            Dir_Path = "/"
            for Dir_Name in Path.split('/'):
                # if "" aka "/" do nothing
                if Dir_Name == "":
                    continue
                # Create the dir
                uos.mkdir(Dir_Path + Dir_Name)
                # Save path string
                Dir_Path = Dir_Path + Dir_Name + '/'

            # Try to write file again after creating needed dirs
            try:
                # If it fails again return false
                f = open(str(Path) + "/" + str(Config_Name), 'w')
                f.write(ujson.dumps(Config_Dict))
                f.close()
            except:
                return False
            finally:
                # If we get to here we didnt fail so return True to indicate file saved
                return True
        
        # FIX - Better error handling
        return False
    
    # File save all ok return True
    return True

# -------------------------------------------------------------------------------------------------------
def Defaults_Device(Config_Dict):
    # Returns a dict containing the missing default settings
    # use: <dict>.update(Defaults_Device(<dict>))

    # Dict with default settings
    Default_Dict = {"Config_ID": "0", "Log_Level": "1", 'MQTT_Port': '1883'}
    
    # Check if we got passed false aka config not loaded
    if Config_Dict == False:
        return Default_Dict

    Missing_Config_Dict = {}

    for Setting, Value in Default_Dict.items():
        if Config_Dict.get(Setting, None) == None:
            Missing_Config_Dict[Setting] = Value

    # return the Missing_Config_Dict
    return Missing_Config_Dict


def Delete(Config_Name, Path='/conf'):
    # Check if ".json" is in Config_Name if we so assume that fill path was given
    try:
        if ".json" in Config_Name:
            uos.remove(Config_Name)
        else:
            uos.remove("/conf/" + Config_Name + ".json")
    # Dont thing we need to check a lot return, case if error to indicate the file does not exist
    except OSError:
        return False
    else:
        # return true if the file was deleted as expected
        return True


# -------------------------------------------------------------------------------------------------------
def Check_Device(Config_Dict):
    # Check if we got the needed settings return false if we are missing something
    Required_List = ["Hostname", "MQTT_Broker", "System_Header", "WiFi_Password", "WiFi_SSID", 'Config_ID', 'Log_Level', 'MQTT_Port']

    # Create a list we can add the missing entries to
    Missing_List = []
    # loop over required entries
    for Entry in Required_List:
        if Config_Dict.get(Entry, None) == None:
            Missing_List.append(Entry)                
    
    # Check if we are missing anything aka the Missing_List is empythy
    if Missing_List != []:
        Missing_String = ""
        for Entry in Missing_List:
            Missing_String = Missing_String + " " + Entry
        # return string containing the missing settings
        return 'Missing config entries:' + Missing_String
    
    # Return true if we got it all
    else:
        return True