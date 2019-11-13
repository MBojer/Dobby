import ujson
import os

# -------------------------------------------------------------------------------------------------------
# Reads config from Config_Path and stores vairables
def Config_Load(Config_Path, Print=True):
    # Check if we got a config store on local fs
    try:
        f = open(Config_Path)
        fs_Config = f.read()
        f.close()
    # No config store on fs or other error
    except OSError as e:
        # No config found
        if 'ENOENT' in str(e):
            if Print is True:
                print("   Unable to load config: " + Config_Path + " no sutch file")
            return False
        # Check if we are dealing with the device config or any other config
        ## Unknown error
        ## FIX - Add some error handling here
        elif Config_Path.endswith("device.json") is True:
            print("   Fatal OS Error: " + str(e) + " unable to boot - Halting !!!")
            while True:
                time.sleep(1337)
        else:
            return False
            
    # return config dict    
    return ujson.loads(fs_Config)