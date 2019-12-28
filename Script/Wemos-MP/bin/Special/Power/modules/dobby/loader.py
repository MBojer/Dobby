import utime
import gc
import sys
import esp

import dobby.config as DobbyConfig

# Disable os debugging on console
esp.osdebug(None)

def Run():

    # ++++++++++++++++++++++++++++++++++++++++ CLI Timeout ++++++++++++++++++++++++++++++++++++++++
    # 3 sec option to enter cli after timeout normal boot
    print()
    print()
    CLI_Timeout()

    # ++++++++++++++++++++++++++++++++++++++++ Import / Run Dobby ++++++++++++++++++++++++++++++++++++++++
    try:
        import dobby.main
    except MemoryError as e:
        print('\n\n\n   Unable to load Dobby - Not enough free memory - Free memory: ' + str(gc.mem_free()) + ' - Starting CLI\n\n\n')
        CLI_Run()
    except SyntaxError as e:
        print('\n\n\n   Unable to load Dobby - Syntax error: ' + str(e) + ' - Starting CLI\n\n\n')
        CLI_Run()
    # except:
    #     print('\n\n\n   Unable to load Dobby Lib - Unknown Error - Starting CLI\n\n\n')
    #     CLI_Run()
    
    # No errors on import
    else:
        # Try to load the config
        try:
            Config = DobbyConfig.Load(Config_Name = 'device', Delete_On_Error = False)        
        except DobbyConfig.Error as e:
            # On error run the cli
            print("\n\n\n   Unable to load Dobby - Missing 'device' config - Starting CLI\n\n\n")
            CLI_Run()

        # Add defaults if missing
        Config.update(DobbyConfig.Defaults_Device(Config))

        # Check if we got all the config se need
        Resoult = DobbyConfig.Check_Device(Config)
        # If not true Resoult contains a string with the missing settings
        if Resoult is not True:
            print('\n\n\n   Unable to load Dobby - Missing config setting: ' + Resoult + ' - Starting CLI\n\n\n')
            CLI_Run()
        else:
            # Run dobby and pass loaded config
            dobby.main.Run(Config)
        
def CLI_Timeout():
    try:
        # Start loop we can break via ctrl c to interrupt boot
        Print_Timeout(3, '   Press CTRL + C to interrupt normal boot -')
    except KeyboardInterrupt:
        # Log event
        print("      CTRL + C pressed")
        # Start the CLI
        CLI_Run()

def Print_Timeout(Timeout=5, Text_Prefix=""):

    for i in reversed(range(Timeout + 1)):
        # if 0 then we timed out
        if i is 0:
            # The 10 spaces is to clear " in: nnn"
            print (Text_Prefix + ' Timeout          ', end="\n")
        else:
            # print Timeout message
            print (Text_Prefix + ' Timeout in: ' + str(i), end="\r")
        # Sleep for a sec
        utime.sleep(1)

def CLI_Run():
    # Try to start cli
    try:
        # Start the CLI
        import dobby.cli
        dobby.cli.Run()
    except MemoryError:
        print("\n\n\n   Unable to start Dobby CLI - Not enough memory - Free memory: " + str(gc.mem_free()) + "\n\n\n")
        sys.exit()
    # except:
    #     print('\n\n\n   Unable to start Dobby CLI - Unknown Error\n\n\n')
    #     sys.exit()