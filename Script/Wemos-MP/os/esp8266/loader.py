#!/usr/bin/python3

# Module for dobby on 'wemos d1 mini' or 'wemos mini 32' using micropython

import ujson
import utime
import sys
import uos
import gc
import machine
import urequests
import network
import esp


## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300000

# -------------------------------------------------------------------------------------------------------
class Run:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self):

        # Try to load the network config file
        # if we cant start the cli
        try:
            with open('/conf/network.json', 'r') as f:
                Network_Config = ujson.load(f)
        # start the cli on Error
        except:
            print("Starting Dobby Loader - Version: " + str(Version))
            print("Missing network config starting CLI")
            # start the cli, it will trigger a reboot after getting a wifi config
            # .CLI()
            import cli
            # Remember to pass self
            cli.Run(self)

        # Lists with names of modules we need to have
        self.System_Modules = None

        # Used to download modules aka mqtt broker
        self.Server = Network_Config["MQTT Broker"]
        self.Server_Port = Network_Config.get("Port", "80")

        self.Hostname = Network_Config["Hostname"]

        # Add modules only needed for esp32
        if uos.uname().sysname == 'esp32':
            self.System_Modules = ['base', 'cli', 'config', 'loader', 'timer', 'indicator', 'pinmonitor', 'umqttsimple', 'waitforwifi']
        # Add modules only needed for esp32
        elif uos.uname().sysname == 'esp8266':
            self.System_Modules = []

        # List to hold log if we are returning it
        self.Log_Queue = []

        # Disable AP if enabeled
        network.WLAN(network.AP_IF).active(False)
            
        # Create self.wlan0 reference
        self.wlan0 = network.WLAN(network.STA_IF)
        # Activate self.wlan0 regardless if it is no not
        self.wlan0.active(True)

        # self.Log start of script
        self.Log(1, "System", "Starting Dobby Loader - Version: " + str(Version))

        Reconnect = False
        # Check if the right SSID and hostname is configured
        if self.wlan0.config('essid') != Network_Config['WiFi SSID']:
            # Disconnect from incorrect ssid
            self.wlan0.disconnect()
            # Note that we need to reconnect
            Reconnect = True

        # FIX - esp8266 crashes if this command is given
        if self.wlan0.config('dhcp_hostname') != self.Hostname and uos.uname().sysname != 'esp8266':
            # Disconnect from incorrect ssid
            self.wlan0.disconnect()
            # Set wifi hostname
            self.wlan0.config(dhcp_hostname=self.Hostname)
            # Note that we need to reconnect
            Reconnect = True
    
        if self.wlan0.isconnected() == False:
            # Connect to wifi
            self.wlan0.connect(Network_Config['WiFi SSID'], Network_Config['WiFi Password'])
            # self.Log event
            self.Log(1, "System/WiFi", "Reconfigured")

        # Start loop we can break via ctrl c to interrupt boot
        try:
            # run for loop from 3 to 0
            for i in reversed(range(4)):
                # if 0 then we timed out
                if i is 0:
                    # The 10 spaces is to clear " in: nnn"
                    print('Press CTRL + C to interrupt normal boot - Timeout          ', end="\n")
                else:
                    # print Timeout message
                    print('Press CTRL + C to interruselpt normal boot - Timeout in: ' + str(i), end="\r")
                    # Sleep for a sec
                    utime.sleep(1)
        except KeyboardInterrupt:
            # Log event
            print()
            print("      CTRL + C pressed")
            # .CLI()
            import cli
            # Remember to pass self
            cli.Run(self)


        # Check if we got wifi
        import waitforwifi
        try:
            # remember to pass self
            waitforwifi.Run(self, Timeout=3000, Print=True)
        except self.Error:
            # if we get an error it should already be logged
            # pass to Sys_Modules_Check, it will exit to repl on missing sys module
            self.Sys_Modules_Check()
        else:
            # Place below code in a try statement so we can cache self.Error
            # that way we dont try to download anything else if we fail on one
            try:
                # not we need to get config from server if missig
                # or check if local matches server config
                self.Get_Configs()

                # after config check we need to check if we got the right modules
                # and if the modules we got is up to date
                self.Module_Get()
            except self.Error as e:
                self.Log(3, "System", str(e))
            
        # delete waitforwifi since we are done with it
        del waitforwifi


    # -------------------------------------------------- Download Module --------------------------------------------------
    def Module_Download(self, Name, Module_json):

        # Check if the module we need is on the list
        if Name not in Module_json:
            raise self.Error('Module_Download: Module: ' + Name + ' not avalible on server')

        # Build url
        # remember not to add file postfix its done below
        URL = "http://" + self.Server + ":" + self.Server_Port + "/Modules/" + uos.uname().sysname + "/" + Name + "."

        # download both md5 and mpy files
        for Postfix in ['mpy', 'md5']:
            # Try to download the file
            try:
                get_Content = urequests.get(URL + Postfix)
            except OSError as e:
                raise self.Error('OSError: ' + str(OSError) + ' during download of file: ' + str(File) + " URL: " + str(URL))
            else:
                # Check for status code 200 to see if we got the file
                if get_Content.status_code == 200:
                    # Save and overwrite file if existsw
                    with open('/lib/' + str(Name) + '.' + Postfix, 'w') as f:
                        # write File to file
                        f.write(get_Content.content)
                    try:
                        pass
                    except OSError as e:
                        # raise self.Error on failure to save to fs
                        raise self.Error('Unable to save "' + '/lib/' + str(Name) + '.' + Postfix + '" to fs')
                        # just let the script end here
                # If status code is not 200 raise self.Error
                else:
                    raise self.Error("Did not get code 200 after get. File: " + str('/lib/' + str(Name) + '.' + Postfix) + " URL: " + str(URL + Postfix))



    # -------------------------------------------------- Module Version Check --------------------------------------------------
    def Module_Version_Check(self, Name):

        # get modules md5 file from server
        Server_md5 = urequests.get("http://" + self.Server + ":" + self.Server_Port + "/Modules/" + uos.uname().sysname + "/" + Name + ".md5")
        # Convert responce to text
        Server_md5 = Server_md5.text

        try:
            with open('/lib/' + Name + '.md5', 'r') as f:
                Local_md5 = f.read()
        # if we cant get local md5 fail check
        except:
            raise self.Error("Module_Version_Check: local md5 missing for module: " + Name)
        # Check if local and server md5 matches

        if Server_md5 == Local_md5:
            return
        else:
            raise self.Error("Module_Version_Check: Local and Server md5 not matching for module: " + Name)


    # -------------------------------------------------- Get Modules --------------------------------------------------
    def Module_Get(self):
        
        # Add self.System_Modules to Needed_Modules
        Needed_Modules = list(self.System_Modules)

        Config_List = uos.listdir('/conf')
        # For loop over names in config list
        for Config_Name in Config_List:
            # Remove json from name
            Config_Name = Config_Name.replace('.json', '')
            
            # No actions neede for network and device config
            if Config_Name in ['device', 'network']:
                continue

            # add name to Needed_Modules
            Needed_Modules.append(Config_Name)

        # get list of libs
        Local_Modules = []
        # loop over listdir of 'lib'
        for File in uos.listdir('/lib'):
            if File.endswith('.mpy'):
                Local_Modules.append(File.replace('.mpy', ''))

        # If a module is updated we need to reboot to load the new version
        Reboot_Required = False

        # get list of modules aka get holder from web server
        try:
            Module_json = urequests.get("http://" + self.Server + ":" + self.Server_Port + "/Modules/" + uos.uname().sysname + "/index.json")
            Module_json = Module_json.json()
        except KeyboardInterrupt:
            # Log error
            self.Log(3, "System/Module", 'Unable to get index.json from server: ' + self.Server)
            
            # Check if we got all system modules
            if set(self.System_Modules).issubset(Local_Modules) == False:
                # quit to repl
                raise self.Error('Module_Get: Unable to get index.json from server: ' + self.Server)
            else:
                # Log fatal error
                self.Log(3, "System/Module", "Got needed system modules trying to boot")
                # return so we dont trigger below code
                return

        # Check if we got all the modules we need
        for Module_Name in Needed_Modules:
            # before we start this lets try to free some memory, the esp8266 might run low
            gc.collect()

            # Check if modules is in lib folder
            # remember to add ".mpy" to Module_Name
            if Module_Name not in Local_Modules:
                # Log event
                self.Log(0, "System/Module", "Trying to download module: " + Module_Name)
                # Module not in list try to download it
                try:
                    self.Module_Download(Module_Name, Module_json)
                except self.Error as e:
                    if Module_Name in self.System_Modules:
                        self.Log(5, "System/Module", "Unable to get system module: " + Module_Name + " - Cannot boot - " + str(e))
                        # Raise Loader error so we exit script to repl
                        raise self.Error("Unable to get system module: " + Module_Name + " - Cannot boot - " + str(e))
                    else:
                        # remove config so we dont load the module
                        uos.remove('/conf/' + Module_Name + '.json')
                        # log error
                        self.Log(3, "System/Module", "Unable to get device module: " + Module_Name)
                else:
                    # Log event
                    self.Log(1, "System/Module", "Downloaded: " + Module_Name)
                    continue

            # Module already on device, import so we can check version
            else:
                # Check if we got the same module as on the server
                try:
                    # Check if software is up to date will raise an error if not
                    self.Module_Version_Check(Module_Name)
                except self.Error as e:
                    self.Log(1, "System/Module", str(e))
                    try:
                        # Not try to download the module again
                        self.Module_Download(Module_Name, Module_json)
                    except self.Error:
                        # If we updated a system module reboot 
                        if Module_Name in self.System_Modules:
                            # Log event
                            self.Log(5, "System/Module", "Unable to download system module: " + Module_Name + " cannot boot")
                        else:
                            # Log event
                            self.Log(3, "System/Module", "Unable to download: " + Module_Name)
                    else:
                        # Log event
                        self.Log(1, "System/Module", "Updated: " + Module_Name)
                        # If we updated a system module reboot
                        if Module_Name in self.System_Modules:
                            Reboot_Required = True
                else:
                    self.Log(0, "System/Module", Module_Name + " up to date")

        # Check if we need to reboot
        if Reboot_Required == True:
            self.Log(1, "System/Module", "System modules updated reboot required")
            # reboot
            self.Reboot("Module update")
        # Reboot not required
        else:
            # Log event
            self.Log(1, "System", "Get modules compleate")

    # ---------------------------------------------------------- Reboot ---------------------------------------------
    def Reboot(self, By):
        # Log event
        self.Log(1, "System", "Rebooting - Triggered by: " + str(By))
        
        # FIX - Write log to disk here and load publish it during next boot

        # Little break to let system send
        utime.sleep_ms(750)
        # reboot
        machine.reset()

    # -------------------------------------------------- Get Config --------------------------------------------------
    # Downloads each config file from server for this device
    # and compares it to local config, if not same or none existing it server config will be saved
    def Get_Configs(self):

        # Log event
        self.Log(1, "System/Config", "Checking")

        # Import config module
        import config as dConfig
            
        # Build URL
        URL = "http://" + self.Server + ":" + self.Server_Port + "/Config/" + self.Hostname + "/"
        try:
            # Get list of config files on server
            Server_Config_List = urequests.get(URL).text
        except OSError:
            # OSError = wifi up but server not responding aka webserver not running
            raise self.Error("Get_Configs: Webserver not responding: http://" + self.Server + ":" + self.Server_Port)
        except:
            # raise self.Error when we cant get config dir
            raise self.Error("Get_Configs: Config dir not found: " + URL)
        
        # Get file names from apacesh list dir
        Matches = []
        # Loop over lines in reply to find lines with config files in them
        for Line in Server_Config_List.split('href="'):
            # if we got .json in the line we got a config file
            if '.json' in Line:
                # take whats between href=" and .json aka file without .json
                try:
                    Line = Line.split(".json")[0]
                except:
                    pass
                else:
                    Matches.append(Line)
        
        Server_Config_List = Matches
        del Matches

        Local_Config_List = uos.listdir('conf')

        # for loop over Server_Config_List 
        for Entry in Server_Config_List:
            # Try to download Device_Config.
            # Config_Download will return true if local config matches server config or of server config was downloaded
            # else Config_Download will raise an error
            try:
                # download config
                dConfig.Download(Entry, self)
            # Error downloaning config
            except dConfig.Error as e:
                if 'Server not responding' == str(e):
                    # Log event
                    self.Log(1, 'System/Config', "Unable to get check config files " + str(e).lower())
                else:
                    self.Log(2, 'System/Config', "Error during check:  " + str(e))

            # remove from Local_Config_List
            # so we do not remove config and module below
            # pass on all errors
            # might not be in local config
            try:
                Local_Config_List.remove(Entry + ".json")
            except:
                pass

        # Check if there is anything left if Local_Config_List
        # if there is delete the local config since it was removed from the server
        for Entry in Local_Config_List:
            # remove .json at the end
            Entry = Entry.replace(".json", "")
            if Entry in ['device', 'network']:
                continue
            # Log event
            self.Log(1, 'System/Config', 'Local config for: ' + str(Entry) + " not found on server. Removing corosponding module and config")
            # remove local config, module and md5 file
            for Del_Info in [['conf/', '.json'], ['lib/', '.mpy'], ['lib/', '.md5']]:
                try:
                    uos.remove(Del_Info[0] + Entry + Del_Info[1])
                except:
                    pass

        # Log event
        self.Log(1, "System/Config", "Get compleate")

        # remove dConfig to save memory
        del dConfig




    # -------------------------------------------------------------------------------------------------------
    def Sys_Modules_Check(self):
     
        Local_Modules = []
        # loop over listdir of 'lib'
        for File in uos.listdir('/lib'):
            if File.endswith('.mpy'):
                Local_Modules.append(File.replace('.mpy', ''))
        
        # List to hold potential missing modules names
        Missing_List = []
        # Loop over entries in self.System_Modules
        for Entry in self.System_Modules:
            # Check if entry is in local modules list
            if Entry not in Local_Modules:
                Missing_List.append(Entry)

        if Missing_List != []:
            # Log error
            self.Log(3, "System", "Unable to boot missing the following system modules: " + str(Missing_List))
            # Raise error to quit to repl
            raise self.Error('Quitting to repl')
        # we got ths system modules we need
        else:
            # Log event
            self.Log(0, "System", "WiFi not up. System has needed modules")





    # -------------------------------------------------------------------------------------------------------
    # This should be used to write messsages both to serial and mqtt
    def Log(self, Level, Topic, Payload):

        # Needed vars
        Level_String = ''

        # Generate Level_String
        if Level == 0:
            Level_String = 'Debug'
        elif Level == 1:
            Level_String = 'Info'
        elif Level == 2:
            Level_String = 'Warning'
        elif Level == 3:
            Level_String = 'Error'
        elif Level == 4:
            Level_String = 'Critical'
        elif Level == 5:
            Level_String = 'Fatal'

        # Build topic string
        # System header is always "/Unconfigured" since this script should only ber called at boot
        Topic = "/Unconfigured/" + self.Hostname + "/Log/" + Level_String + "/" + Topic

        # Always print message to serial
        print("-> " + Topic + " - " + Payload)
        
        # Log level check
        if Level < 1:
            return

        # Append to log queue
        self.Log_Queue.append([Topic, Payload, False])
