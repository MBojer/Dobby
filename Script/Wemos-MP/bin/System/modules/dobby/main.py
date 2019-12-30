#!/usr/bin/python

# Module for dobby on wemos d1 mini using micropython

import ujson
import utime
# import uping
import sys
import uos
import network
import gc
import umqtt.simple as MQTT
import machine
import urequests

import dobby.config as DobbyConfig
import dobby.pinmonitor as DobbyPinMonitor

# Import ntp time
import ntptime


# -------------------------------------------------------------------------------------------------------
class Run:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Module_Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Config):

        # Needed Variables
        ## Version
        Version = 300000
        ### First didget = Software type 1-Production 2-Beta 3-Alpha
        ### Secound and third didget = Major version number
        ### Fourth to sixth = Minor version number
        ## Dict holding all configs
        ### Fill with config from device.json if it failes self.Config will = False
        self.Config = Config
        ## Log Queue
        self.Log_Queue = list()
        ## Variable for Pin Monitor
        # Remember to pass Dobby aka self
        self.Pin_Monitor = DobbyPinMonitor.Init(self)
        ## Holds all loaded modules
        self.Modules = {}
        # Holds loaded System Modules like WirePusher if enabeled
        self.Sys_Modules = {}

        # If var contains a url it will be downloaded when connected to wifi
        self.Get_Modules = []

        # Log relies on this to check if we need to blink on errors
        # So needs to be set before log is used the first time
        self.Indicator = None

        # If this is set, all subscribe and publishes will be mirrored and topic replaced as folles
        # <System Header>/<Hostname>/ = <self.gBridge>
        # We have to load this before mqtt so we know if we need to mirror topics
        self.gBridge_Topic = self.Config.get('gBridge_Topic', None)
        
        # I havent found a good way to get hardware info.
        # will use machine.EXT0_WAKE in a try statement
        # if we get AttibuteError then we know its a ESP8266
        try:
            if machine.EXT0_WAKE == None:
                pass
        # ESP8266
        except AttributeError:
            self.ESP_Type = 8266
        # ESP32
        else:
            self.ESP_Type = 32
            # # import and Start webrepl if esp32
            # import webrepl
            # webrepl.start()
            # self.Log(0, "System/webrepl", "Starting")

        

        # List of push messages that failed to send
        # we retry when online again
        self.Push_Queue = []

        # MQTT Connection status
        self.MQTT_State = 'init'
        self.MQTT_Reconnect_At = 0
        self.MQTT_Subscribe_To = []

        # Init message
        self.Log(1, 'System', 'Initializing Dobby version: ' + str(Version))

        # Subscribe to Commands topic
        self.MQTT_Subscribe(self.Peripherals_Topic("Commands"))
                
        # Change CPU frequancy if requested
        if Config.get('CPU_16', False) == True:
            machine.freq(160000000)
            self.Log(1, 'System', 'CPU frequancy set to: 16MHz')

        # ++++++++++++++++++++++++++++++++++++++++ WiFi setup ++++++++++++++++++++++++++++++++++++++++
        # Setup WiFi
        # ## Log event
        self.Log(1, 'System', 'Connecting to WiFi SSID: ' + self.Config['WiFi_SSID'])

        ## Disable AP
        self.ap0 = network.WLAN(network.AP_IF)
        # Check if AP is active
        if self.ap0.active() == True:
            # Disable ap if active
            self.ap0.active(False)


        ## Setup wlan0
        self.wlan0 = network.WLAN(network.STA_IF)
        # Activate wlan0 regardless if it is no not
        self.wlan0.active(True)

        # Check if the right SSID is configured
        if self.wlan0.config('essid') != self.Config['WiFi_SSID']:
            # Disconnect from incorrect ssid
            self.wlan0.disconnect()
            # Hostname only works with version 4 +
            # Set wifi hostname
            self.wlan0.config(dhcp_hostname=str.encode(self.Config['Hostname']))
            # Connect to wifi
            self.wlan0.connect(self.Config['WiFi_SSID'], self.Config['WiFi_Password'])

        else:
            self.Log(0, 'WiFi', 'Config ok')

        # Var to indicate of we have published the ip we got when wifi connected
        self.Published_Boot = False

        # ++++++++++++++++++++++++++++++++++++++++ MQTT ++++++++++++++++++++++++++++++++++++++++
        # Remember to add something raondom after the hostname so the borker see a new connecton
        # Check if we got a user and pass for mqtt
        # Generate Unique Post Hostname
        Post_Hostname = str(uos.urandom(1)[0] %1000)
        # Log event
        self.Log(0, 'MQTT', 'Using hostname: ' + self.Config['Hostname'] + "-" + Post_Hostname)
        # Stores messages so we can act on them in MQTT Loop
        ## List containing Topic and payload
        ## [[<Topic>, <Payload>]]
        self.MQTT_Incomming_Queue = []
        # Create MQTT Client
        self.MQTT_Client = MQTT.MQTTClient(
            self.Config['Hostname'] + "-" + Post_Hostname,
            self.Config['MQTT_Broker'],
            int(self.Config.get('MQTT_Port', 1883)),
            self.Config.get('MQTT_Username', None),
            self.Config.get('MQTT_Password', None)
        )
        # Set last will
        self.MQTT_Client.set_last_will(self.Config['System_Header'] + "/" + self.Config['Hostname'] + "/Log/Will", "Disconnected")
        
        # try to connect to mqtt
        self.MQTT_Connect()

        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # Loop over config names in /conf and import matching modules
        ## Get config names
        Config_List = uos.listdir('/conf')
        # Remove device.json since we dont want to use that again
        Config_List.remove('device.json')
        # Move relay to the front of the list if present
        ## try to remove
        for Entry in ['dimmer.json' , 'relay.json']:
            try:
                Config_List.remove(Entry)
            ## if it fails do nothing
            except ValueError as e:
                pass
            ## If we removed relay.json add it back at the beginning of the list
            else:
                Config_List.insert(0, Entry)

        # Get list of modules
        Lib_List = uos.listdir('/lib/dobby')

        # Add default system modules so we dont try to download them
        Lib_List.append("indicator.mpy")
        
        ## Loop over names in config
        for Name in Config_List:

            # Check if module exists
            if Name.replace('.json', '.mpy') not in Lib_List:
                # Log evnet
                self.Log(1, "System", "Trying to download module: " + str(Name.replace('.json', '')))
                # Try to download module
                if self.Download_Module(Name.replace('.json', '')) != True:
                    # continue so we do not try to load the module
                    continue

            # Import the config
            ## False = Config not found or error during import
            ## If not false the imported Module will be returned

            Config = DobbyConfig.Load(Config_Name=Name, Delete_On_Error=False)
            Error = None

            # Load config is False if no config is found
            if Config is not False:
                Module_Name = str('dobby.' + Name.replace('.json', ''))
                try:
                    # Try to import
                    Module = __import__(Module_Name.replace(".", '/'))
                    # Store objevt in self.Modules
                    # Pass config and get perifical object
                    # Remember to pass Dobby aka self so we can log in Button and use dobby variables
                    self.Modules[Name.replace('.json', '')] = Module.Init(self, Config)
                    
                except (AttributeError, TypeError, SyntaxError, KeyError) as e:
                    Error = str(e)
                # Incompatible mpy file
                except ValueError:
                    # remove module
                    uos.remove('/lib/dobby/' + Name.replace('.json', '.mpy'))
                    # Log event
                    Error = "Removed Module: " + Name.replace('.json', '') + " due to incompatibility"
                # Missing module, try to download
                except ImportError:
                    Error = "Missing module: " + Module_Name + " trying to download it from: " + str(self.MQTT_Client.server) + " when WiFi is connected"
                except MemoryError:
                    Error = 'Not enough free memory. Free memory: ' + str(gc.mem_free())
                except self.Module_Error as e:
                    Error = str(e)

                # No errors on import in creation of module object
                else:
                    # Log event
                    self.Log(0, "System", "Module loaded: " + str(Module_Name))

                finally:
                    # Check if Module import ok
                    if Error != None:
                        # remove module from self.Modules if added
                        try:
                            del self.Modules[Name.replace('.json', '')]
                        except:
                            pass
                        # Dont remove config on "Missing module" we are trying to download it when we get wlan0 up½
                        if Error.startswith("Missing module: ") != True:
                            # Log event
                            self.Log(4, "System", "Unable to load module: " + str(Module_Name) + " - Error: " + Error)
                            # Remove config file
                            uos.remove("/conf/" + Name)
                            # Log removal of config file
                            self.Log(1, "System", "Removed config file: /conf/" + Name)
            else:
                self.Log(0, 'System', "Invalid config: /conf/" + Name + "'")

        # Activate indicator if 'LED' owned by Indicator aka not used for something else
        # on esp32 its IO2
        # on esp8266 its D4
        if self.Pin_Monitor.Get_Owner(self.Pin_Monitor.LED) == 'Indicator':
            # check if indicator is already imported and init
            if self.Sys_Modules.get('indicator', None) == None:
                # Import Indicator
                import dobby.indicator
                # Init Indicator and store in Sys_Modules to enable loop
                self.Sys_Modules['indicator'] = dobby.indicator.Init(self, {"System": {"Pin": "LED"}})
                # Create the indicator object
                self.Indicator = self.Sys_Modules['indicator'].Peripherals["System"]
            # indicator already imported to add an object in stead
            else:
                # Create the indicator object
                self.Indicator = self.Sys_Modules['indicator'].Add("System", {"Pin": "LED"})
                # On add the indicator will be blinked 3 times
                # will use this as boot blink

            # add wifi infication if disconnected
            if self.wlan0.isconnected() == False:
                self.Indicator.Add("WiFi", 4, "0.5s", "0.75s", True)

        else:
            # Log we could not enable indicator led
            self.Log(0, 'System/Indicator', "LED Pin in use, cannot enable system indicator")
        
        # Boot done message
        self.Log(0, 'System', 'Dobby - Initialization compleate - Free memory: ' + str(gc.mem_free()))

        # Start loop()
        self.Loop()


    # ++++++++++++++++++++++++++++++++++++++++++++++++++ MISC ++++++++++++++++++++++++++++++++++++++++++++++++++
    # ---------------------------------------------------------- Config check ---------------------------------------------    
    def Reboot(self, By):
        # Log event
        self.Log(1, "System", "Rebooting - Triggered by: " + str(By))
        # Clear mqtt queue
        self.Log_Queue_Empyhy()
        # Little break to let system send
        utime.sleep_ms(750)
        # reboot
        machine.reset()
        
    
    # ---------------------------------------------------------- Config check ---------------------------------------------    
    def Config_Check(self, Owner, Check_List, Config_Dict):
        #  Check if we got the needed config
        Failed = False
        for Entry in Check_List:
            if Config_Dict.get(Entry, None) == None:
                # Log faileure
                self.Log(3, Owner, "Missing config: " + Entry + " - Unable to initialize")
                # Mark failure and continue
                Failed = True
                
        # Check if we failed
        if Failed == True:
            # Since we already logged a blank error is fine
            # Raise error so who ever triggered this knows we failed
            raise self.Module_Error

    # ---------------------------------------------------------- Download Module ---------------------------------------------    
    def Download_Module(self, Name):

        # Check if we are connected to WiFi
        if self.wlan0.isconnected() == False:
            # If not add to modules queue aka Get_Modules
            if Name not in self.Get_Modules:
                self.Get_Modules.append(Name)
                self.Log(1, "System", "Module added to queue: " + str(Name))
            
            # return false when we add to queue
            return False

        # List of url base paths to try
        Try_List = [str(uos.uname().sysname), "Shared"]

        for Base_Path in Try_List:
            # Build URL
            URL = "http://" + self.MQTT_Client.server + ":8000/" + Base_Path + "/" + Name + ".mpy"
            # Try to get module
            Module = urequests.get(URL)
            # Check for status code 200 to see if we got the file
            if Module.status_code == 200:
                try:
                    # Save and overwrite module if existsw
                    with open('/lib/dobby/' + str(Name) + '.mpy', 'w') as f:
                        # write module to file
                        f.write(Module.content)
                except:
                    # Log error
                    self.Log(3, "System", "Unable to save module: " + Module_Name)
                    # return false since we were unable to save the module to fs
                    return False
                else:
                    # Log event
                    self.Log(1, "System", "Module downloaded: " + str(Name) + " URL: " + URL)
                    # Return true when we saved the module
                    return True

        # If we get to here we did not get a module when trying to download it
        self.Log(3, "System", "Unable to download module: " + str(Name))
        # return false on error
        return False
    

    # ---------------------------------------------------------- ms to time ---------------------------------------------    
    def ms_To_Time(self, ms):
        if ms <= 0:
            return "0h0m0s"
        else:
            millis = int(ms)
            seconds=(millis/1000)%60
            seconds = int(seconds)
            minutes=(millis/(1000*60))%60
            minutes = int(minutes)
            hours=(millis/(1000*60*60))%24
            hours=int(hours)

            return str(hours) + "h" + str(minutes) + "m" + str(seconds) + "s"

    
    # ----------------------------------------------------------Push---------------------------------------------
    def Push_URL(self, URL, Queue=False):
        # Queue = True - Message will be added to self.Push_Queue on failure
        Error = None

        # Check if we are connected to wifi before trying to send
        if self.wlan0.isconnected() == True:
            try:
                # Post message to id and get responce
                response = urequests.post(URL)
            # Not connector to wifi
            except OSError as e:
                Error = "OSError: " + str(e)
            except IndexError as e:
                Error = "IndexError: " + str(e)
            else:
                # if response.status_code == 200:
                # FIX BETTER ERROR HANDLING
                # Error while posting
                # print("MARKER", response.text)
                # return so we dont trigger finally, used for errors
                return True
        else:
            Error = "wlan0 not connected"

        # FIX - Add memory check here
        # Only add to queue if asked to do so
        if Queue == True:
            # Log event
            self.Log(0, "Push", "Unable to send message. Added to queue")
            # Append URL to self.Push_Queue
            self.Push_Queue.append(URL)
        # if Queue is false and we got an error
        # we dont need to check if we got an error since we return true in 'else' above
        else:
            # Log event
            self.Log(0, "Push", "Unable to send message. Error: " + Error)
        
        # return False on failure
        return False

    # -------------------------------------------------------------------------------------------------------
    def Push_Send(self, id, Title, Message, Type='Alert'):
 
        # Build URL
        URL = 'http://wirepusher.com/send?id=' + str(id) + '&title=' + str(Title) + '&message=' + str(Message) + '&type=' + str(Type)
        # Replace space with '%20'
        URL = URL.replace(" ", "%20")

        # Pass to Push_URL and ask to queue on failure
        self.Push_URL(URL, Queue=True)


    # -------------------------------------------------------------------------------------------------------
    def Timer_Init(self):
        # Loads dobby.timer if not already loaded
        if self.Sys_Modules.get('timer', None) == None:        
            # Import Timer
            import dobby.timer
            # Init Timer and store in Sys_Modules to enable loop
            self.Sys_Modules['timer'] = dobby.timer.Init(self)
            # Log event
            self.Log(0, "System", "System module Timer Enabeled")



    # -------------------------------------------------------------------------------------------------------
    def Bool_To_OnOff(self, Bool_State):
        # Returns On if Bool_State is 1 and Off if self.Pin.value() is 0
        # Any other value will give false
        # Try to convert to bool, this should cache all none bool values but accept: 0, 1, True, False
        try:
            Bool_State = bool(Bool_State)
        except:
            return False

        if Bool_State == True:
            return "On"
        else:
            return "Off"

    def OnOff_To_Bool(self, OnOff_String, Flip=False):
        # Returns None on error
        # Not's values if Flip=True
        # On = True
        # Off = False
        if OnOff_String.lower() == "on":
            if Flip == True:
                return False
            else:
                return True
        elif OnOff_String.lower() == "off":
            if Flip == True:
                return True
            else:
                return False

        else:
            return None
        

    def Is_Number(self, Value, Round=True, Percent=False):
        # if Round is true a int will be returned
        # if Percent is true false will be returned if value not between -100 and 100
        # Raises value error if not valid number

        # Well if we get 0 then lets return 0 shall we
        if str(Value) in ['0', '0.0']:
            return 0

        try:
            if "." in str(Value):
                # Check if we need to round the value and return a int
                if Round == True:
                    Value = round(float(Value))
                # not rounding returning float
                else:
                    Value = float(Value)
            else:
                # return int if possible
                Value = int(Value)
        except ValueError:
            # raise ValueError since string
            raise ValueError
        
        # Check percent value if reqested
        else:
            # is percent
            if Percent is True:
                # Check if number between -100 and 100
                if -100 <= Value <= 100:
                    # Return value if ok
                    return Value
                else:
                    # if not raise ValueError
                    raise ValueError
            # if we are not checking for percent return the value
            return Value


    # -------------------------------------------------------------------------------------------------------
    def Log_Queue_Empyhy(self):
        # Publishes all the messages in the log queue
        # if there is a mqtt connection

        # Check if we are connected if not do nothing
        if self.MQTT_State != True:
            return False

        # Check is queue is empthy
        if len(self.Log_Queue) == 0:
            # The queue is empthy so return true
            return True

        # Loop while queue not enpyhy
        while len(self.Log_Queue) > 0:

            # Check is queue is empthy
            if len(self.Log_Queue) == 0:
                # The queue is empthy so return true
                return True
   
            # Referance variables to make the code easier to read
            Topic =  self.Log_Queue[0][0]
            Payload =  self.Log_Queue[0][1]

            # If the try failed retained was not added aka false
            try:
                Retained = int(self.Log_Queue[0][2])
            except IndexError:
                Retained = 0
                

            # Try to publish the message, we get false if we fail
            if self.MQTT_Publish(str(Topic), str(Payload), Retained) is True:
                # Log to serial interface
                # * indicates offlince message send
                print("* -> " + str(Topic) + " - " + str(Payload))
                # Remove the message we just published from the queue
                self.Log_Queue.pop(0)
            # If false we could not send then message then might as well return since queue length will never get to 0
            else:
                # Log event
                self.Log(2, "System", "Unable to empthy log queue")
                # return false so we dont keep failing
                return False

        # return true since all ok
        return True


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Commands(self, Payload):

        # ++++++++++++++++++++++++++++++++++++++++ Reboot ++++++++++++++++++++++++++++++++++++++++
        # Reboots the device
        if Payload.lower() == 'reboot':
            # Run self.Reboot is will do the rest
            self.Reboot("MQTT Commands")

        # ++++++++++++++++++++++++++++++++++++++++ module download ++++++++++++++++++++++++++++++++++++++++
        # downloads a module from Dobby aka mqtt broker
        # overwrites existing module if present
        elif Payload.lower().startswith('module download ') == True:
            # Get module name
            try:
                Module_Name = Payload.split("module download ")[1]
            except:
                self.Log(1, "System", "Invalid module name specified")
            else:
                # Try to download module
                self.Download_Module(Module_Name)
        
        # ++++++++++++++++++++++++++++++++++++++++ Update delete ++++++++++++++++++++++++++++++++++++++++
        # deletes a module from lib/dobby/
        elif Payload.lower().startswith('module delete ') == True:
            try:
                # Get module name
                Module_Name = Payload.split("module delete ")[1]
                # Try to delete module
                uos.remove('/lib/dobby/' + Module_Name + ".mpy")
            except:
                # Log error
                self.Log(1, "System", "Unable to delete module: " + Module_Name)
            else:
                # Log event
                self.Log(1, "System", "Module deleted: " + Module_Name)
            

        # ++++++++++++++++++++++++++++++++++++++++ Hostname ++++++++++++++++++++++++++++++++++++++++
        # Publishes hostname used on Wifi
        elif Payload.lower() == 'hostname':
            
            self.Log(1, "System/WiFi", "Hostname: " + self.wlan0.config('dhcp_hostname'))
        
        # ++++++++++++++++++++++++++++++++++++++++ Find Me ++++++++++++++++++++++++++++++++++++++++
        # Blinks the indicator 20 times if configured
        elif Payload.lower() == 'find me':
            # Turn on FindMe blink
            self.Indicator.Add("Find me", 20, "0.5s", "0.75s")

        
        # ++++++++++++++++++++++++++++++++++++++++ Log level ++++++++++++++++++++++++++++++++++++++++
        # Reboots the device
        elif Payload.lower().startswith("log level ") == True:
            # self.Is_Number will raise a ValueError if supplied log level is not number
            try:
                self.Config['Log_Level'] = self.Is_Number(Payload[10:])
            except ValueError:
                self.Log(2, "Commands", "Invalid log level: " + Payload[10:])
            else:
                self.Log(1, "Commands", "Log level set to: " + str(self.Config['Log_Level']))
            return

        # ++++++++++++++++++++++++++++++++++++++++ Network ++++++++++++++++++++++++++++++++++++++++
        # # Pings a target
        # elif Payload.lower().startswith() == 'ping ':
        #     # Split payload into 'ping ' and target
        #     Payload = Payload.split(' ')
        #     # Payload not contains the target
        #     Payload = Payload[1]
        #     # Ping target and capture reply
        #     Resoult = uping.ping(Payload, timeout=500)
        #     print('Resoult')
        #     print(Resoult)
        #     # # Log resoult
        #     # self.Log(1, "Commands", "Ping: " + str(Resoult))
            
        
        # ++++++++++++++++++++++++++++++++++++++++ Memory ++++++++++++++++++++++++++++++++++++++++
        # Lists free memory
        elif Payload.lower() == 'free memory':
            # Log free memory
            self.Log(1, "Commands", "Free memory: " + str(gc.mem_free()))
            return

        # ++++++++++++++++++++++++++++++++++++++++ File system ++++++++++++++++++++++++++++++++++++++++
        # Free space
        elif Payload.lower() == 'free space':
            # Log free memory
            self.Log(1, "Commands", "Free space: " + str(uos.statvfs("/")))
            return
        
        # ++++++++++++++++++++++++++++++++++++++++ Push ++++++++++++++++++++++++++++++++++++++++
        # Sends a push message to id specified
        elif Payload.lower().startswith('push ') == True:
            # get id
            id = Payload.split(" ")[1]
            # Send a push with message "Test"
            self.Push_Send(id, "Push Test", "Test Message", Type="Test")
            # Log event
            self.Log(1, "Commands", "Message send to id: " + str(id))
            return

        # ++++++++++++++++++++++++++++++++++++++++ Config ++++++++++++++++++++++++++++++++++++++++
        elif Payload.lower() == 'config list':
            # publishes a list of all config files
            dir_String = uos.listdir('/conf')
            # Var to hold string we are returning
            Return_String = ' '
            # Convert list to string
            for Entry in dir_String:
                # split(".")[0] gives us the file name without the extention
                Return_String = Return_String + Entry.split(".")[0] + " "
            # Remove the last space added by the for loop
            Return_String = Return_String[:-1]
            # Log event
            self.Log(1, 'System', "Config list:" + Return_String)
            return


        elif Payload.lower().startswith('config show ') == True:

            # Only get the path
            Config_Path = Payload[12:]
            Config_Name = ""

            # Check if we got a / if so will asume we got the full path
            # if no .json at the end of full path then fail
            if "/" in Config_Path:
                # NO / in path, user gave a config name 
                # Check if we got .json at the end
                if Config_Path.lower().endswith('.json') == False:
                    # No json at the end return and report unknown file
                    self.Log(1, 'System', "Invalid full config path: " + Config_Path)
                    return
                
                # Generate config name
                Config_Name = Config_Path.split()
                Config_Name = Config_Name[-1]
                Config_Name = Config_Name.replace('json' , "")
        
            # Config name only
            else:
                # Generate config name
                Config_Name  = Config_Path
                # Add /confi/ to the beginning and .json to the end of Config_Path
                Config_Path = "/conf/" + Config_Path + ".json"

            # Read the content of the specified file
            try:
                f = open(Config_Path)
                Config_File = f.read()
                f.close()
            except OSError:
                self.Log(2, 'System', "Unable to read config: " + Config_Name + " path: " + Config_Path)
                return

            # Log event - aka publish config
            self.Log(1, 'System', "Config: " + Config_Name + "\nContent: " + str(Config_File))
            return



        elif Payload.lower().startswith('config remove ') is True:
            # removes a specified config file from the file system
            # Get config file name
            Config_Name = Payload.replace("config remove ", "")
            try:
                uos.remove("/conf/" + Config_Name.replace(".json", "") + ".json")
            except OSError:
                self.Log(1, 'System', "Config not found: " + Config_Name)
                return
            # If we get to here the file was removed
            # Log event
            self.Log(1, 'System', "Config removed: " + Config_Name)
            return



        elif Payload.lower().startswith('config save ') is True:
            ## Saves a given json config string to file
            ## format is "config save <config name> <json string>
            # Check if we got a name
            if len(Payload.split(' ')) < 4:
                self.Log(2, 'Commands', "Config save: Missing name")
                return

            # Var for of coding
            Config_Name = Payload.split(' ')[2]

            # Remove everything untill first '{'
            Config_String = Payload[Payload.index('{'):]

            try:
                # Pass to config module
                DobbyConfig.Save(
                    Config_Name,
                    Config_String
                )
            except DobbyConfig.Error:
                self.Log(3, 'System', "Unable to save config: " + Config_Name)
            # No errors
            else:
                # Log event
                self.Log(1, 'System', "Config saved: " + Config_Name)
        
        else:
            self.Log(1, 'System', "Unknown command: " + Payload)
            return

    
    # -------------------------------------------------------------------------------------------------------
    def MQTT_On_Message(self, topic, msg):
        # Stores the incomming message in self.MQTT_Incomming_Queue
        # They will be read in MQTT_Loop

        Topic = topic.decode('utf8')
        # Now strip everything up to and including hostname + /
        # The + 1 is for the / after hostname
        Topic = Topic[Topic.index(self.Config['Hostname']) + len(self.Config['Hostname']) + 1:]

        # Add message to queue
        self.MQTT_Incomming_Queue.append([Topic, msg.decode('utf8')])


    # -------------------------------------------------------------------------------------------------------
    def MQTT_First_Connect(self):

        # Will check if we publishe the ip here since we dont run a loop for wifi
        if self.Published_Boot == False:
            # Log ip
            self.Log(0, 'WiFi', 'Got IP: ' + str(self.wlan0.ifconfig()[0]))
            # Mark we did so
            self.Published_Boot = True
            # Remove wifi indicator if present
            if self.Indicator != None:
                self.Indicator.Remove("WiFi")

            # set time if possible
            try:
                ntptime.settime()
            except:
                pass

            # Download Modules
            Reboot_Needed = False
            for Entry in self.Get_Modules:
                # If self.Download_Module returns true we need to reboot
                if self.Download_Module(Entry) == True:
                    Reboot_Needed = True
            # We need to reboot if we downloaded a module
            if Reboot_Needed == True:
                # Self.Reboot handles logging and mqtt disconnect
                self.Reboot("System module change")


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Connect(self):

        # Check if Wifi is up
        if self.wlan0.isconnected() == False:
            return

        # Check if its first time we got connected
        self.MQTT_First_Connect()

        # Check if we are connected
        if self.MQTT_State == True:
            return

        # 5 sec between reconnect attepts
        if utime.ticks_diff(utime.ticks_ms(), self.MQTT_Reconnect_At) < 5000:
            return

        # Save when we last tried to connect so we can check agains it 
        self.MQTT_Reconnect_At = utime.ticks_ms()

        Error = None
        # Try to connect to MQTT
        try:
            self.MQTT_Client.connect()
        except OSError as e:
            # Check if it matches the current state, aka nothing changed
            if self.MQTT_State != e:
                # No change since last connection attempt
                ## Warning since initial connection attempt failed
                if self.MQTT_State == 'init':
                    self.Log(2, 'System', 'Unable to connect to broker: ' + str(self.Config['MQTT_Broker']))
                elif Error in [103, 104]:
                    self.Log(2, 'System', 'Disconnected from broker: ' + str(self.Config['MQTT_Broker']))
                else:
                    self.Log(2, 'System', 'MQTT Error: ' + str(e))
        # MQTT Username and pass issue
        except MQTT.MQTTException as e:
            Error = str(e)
            # Check if it matches the current state, aka nothing changed
            if self.MQTT_State != Error:
                # Incorect useranem and password
                if str(e) == "5":
                    self.Log(2, 'System', 'Incorrect username and password')
                    Error = "5"
                else:
                    self.Log(2, 'System', "Unknown error - Exception: " + str(e))
                    Error = True
        # except:
        #     self.Log(2, 'System', 'Unknown error')
        #     Error = True
        finally:
            if Error != None:
                # Check if Indicator is enabeled
                if self.Indicator != None:
                    # Turn on MQTT blink
                    self.Indicator.Add('MQTT', 2, "0.5s", "0.75s", True)

                # Set self.MQTT_State = Error so we can check if it changed later in life
                self.MQTT_State = Error
                # return after error
                return

        # print('self.MQTT_Client.ping()')
        # print(self.MQTT_Client.ping())

        # Check if Indicator is enabeled
        if self.Indicator != None:
            # Turn off MQTT blink
            self.Indicator.Remove('MQTT')

        # When we get to here we should be connected
        self.MQTT_State = True

        # if we connected to mqtt empyth the log checks the connection state
        self.Log_Queue_Empyhy()
        
        # Log event
        self.Log(1, 'MQTT', 'Connected to MQTT Broker: ' + self.Config['MQTT_Broker'])

        # Register on mqtt message callback
        self.MQTT_Client.set_callback(self.MQTT_On_Message)

        # Subscribe to topics
        for Topic in self.MQTT_Subscribe_To:
            # Subscribe
            self.MQTT_Subscribe(Topic)


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Publish(self, Topic, Payload, Retained=False):

        if self.MQTT_State != True:
            self.Log_Queue.append([Topic, Payload, Retained])
            return False

        try:
            # Publish message - 0 = Topic 1 = Payload 2 = Retained
            self.MQTT_Client.publish(str(Topic), str(Payload), retain=Retained)
            # Publish to gbridge if configured
            self.MQTT_Publish_gBridge(Topic, Payload, Retained)
        except OSError:
            # If publish failes then add the log queue
            # Add message to Log Queue
            # It will be published later by the MQTT Loop
            self.Log_Queue.append([Topic, Payload, Retained])
            # Only set to false if we are connected
            if self.MQTT_State == True:
                # If we get an error here we assube we are disconnected
                self.MQTT_State = False
            return False

        return True


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Publish_gBridge(self, Topic, Payload, Retained=False):
        # Missor publishes tp match self.gBridge_Topic by replacing to with <System Header>/<Hostname>
        # Does not add to log queue since we calc if we need to publish message every time

        # Return false if gBridge_Topic is not set
        if self.gBridge_Topic == None:
            return False
        
        # Ignore command topic
        elif Topic.startswith(self.Config['System_Header'] + "/" + self.Config['Hostname'] + "/Commands") == True:
            return False
        # Ignore log topic
        elif Topic.startswith(self.Config['System_Header'] + "/" + self.Config['Hostname'] + "/Log") == True:
            return False

        # Replace topic to macth gBridge topic
        Topic = Topic.replace(
            self.Config["System_Header"] + "/",
            self.gBridge_Topic
        )

        try:
            # Publish message - 0 = Topic 1 = Payload 2 = Retained
            # ALWAYS publish as NOT ratained here
            self.MQTT_Client.publish(str(Topic), str(Payload), retain=False)
        except OSError:
            # Only set to false if we are not connected
            if self.MQTT_State == True:
                # If we get an error here we assube we are disconnected
                self.MQTT_State = False
            return False

        return True
        

    # -------------------------------------------------------------------------------------------------------
    def MQTT_Subscribe(self, Topic):
        # Check if we are connected
        if self.MQTT_State == True:
            # Log event
            self.Log(0, 'MQTT', 'Subscribing to topic: ' + Topic)
            # Subscribe
            self.MQTT_Client.subscribe(Topic)

            # Check if self.gBridge is set if so, subscribe to the alterted topic
            if self.gBridge_Topic != None:
                # Ignore "Command topic"
                if Topic != self.Peripherals_Topic("Commands"):
                    # Change topic to match gbridge
                    Topic = Topic.replace(
                        self.Config["System_Header"] + "/",
                        self.gBridge_Topic
                        )
                    # Log event
                    self.Log(0, 'MQTT', 'Subscribing to gBridge topic: ' + Topic)
                    # Subscribe
                    self.MQTT_Client.subscribe(Topic)

        # Not Connected
        else:
            if Topic not in self.MQTT_Subscribe_To:
                # Log evnet
                self.Log(0, 'MQTT', 'Not connected added Topic: ' + str(Topic) + ' to Subscription list')
                # Add to list
                self.MQTT_Subscribe_To.append(str(Topic))
            
                # Set Log_Event = True so we log event
                Log_Event = True


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Handle_Incomming(self, Message):
        # Referance variables
        Topic = str(Message[0])
        Payload = str(Message[1])

        # Print to serial
        print('<- ' + self.Config['System_Header'] + "/" + self.Config['Hostname'] + "/" + str(Topic) + " - " + str(Payload))

        # Do nothing except log to serial if empyth payload
        if Payload == "":
            return

        # Now we can use startswith to see what to do the with message

        # Lets check if we got a command first
        if Topic == "Commands":
            # Nothing else then payload needed here
            self.MQTT_Commands(Payload)
            # return so we dont triggler the commands below
            return

        # Not lets split the topic to get Module_Name, Peripheral_Name and Sub_Topic if any
        Topic = Topic.split("/")
        # Remember module name is stored in lower case
        Module_Name = Topic[0].lower()

        # Try to get Peripheral_Name
        # if IndexError then hand off to module and not peripherials "On_Message"
        try:
            Peripheral_Name = Topic[1]
        # This excluds all so we hand off when we hit the indexerror
        except IndexError:
            try:
                self.Modules[Module_Name].On_Message(Payload)
            # AttributeError means no On_Message in module, just pass not an error
            except AttributeError:
                # Log event
                self.Log(2, "System", "Module: " + str(Module_Name) + " does not have On_Message")
            finally:
                # return so we dont trigger the code below, we already handed off the message
                return
            
        # we need to put the below in try to cache a IndexError if we got one set Sub_Topic_Text to none
        try:
            Sub_Topic_Text = Topic[2].lower()
        except IndexError:
            Sub_Topic_Text = None 

        # Check if we got Peripheral_Name = 'All'
        if Peripheral_Name.lower() == 'all':
            # Creat a list to hold module names
            Name_List = []
            # Add each Name from requested module to Modules_Name
            for Name in self.Modules[Module_Name].Peripherals:
                Name_List.append(Name)
        # Else only add Peripheral_Name to Name_List
        else:
            # Create a list with only the Peripheral_Name
            Name_List = [Peripheral_Name]

        try:
            # For loop over name in Name_List
            for Name in Name_List:
                self.Modules[Module_Name].Peripherals[Name].On_Message(Payload, Sub_Topic=Sub_Topic_Text)
        # AttributeError means no On_Message in module, just pass not an error
        except AttributeError:
            # Log event
            self.Log(2, "System", "Module: " + str(Module_Name) + " does not have On_Message")
        # KeyError indicates unknown module or Peripheral_Name
        except KeyError as e:
            if Module_Name in str(e):
                self.Log(2, "System", "Unknown Module name: " + str(Module_Name))
            else:
                self.Log(2, "System", "Unknown Peripheral name: " + str(e))
                    

    # -------------------------------------------------------------------------------------------------------
    def MQTT_Loop(self):

        # Incomming
        # Check is queue is empthy
        if len(self.MQTT_Incomming_Queue) != 0:
            # Remove and pass the first message in the queue to MQTT_Handle_Incomming
            self.MQTT_Handle_Incomming(self.MQTT_Incomming_Queue.pop(0))
            # # Act on up to 5 incomming message
            # # for i in range(0, 5):
            # # Check is queue is empthy
            # if len(self.MQTT_Incomming_Queue) == 0:
            #     # The queue is empthy so break so we can move on to outgoing messages
            #     break
                
                

        # Outgoing
        # Check if we are connected
        if self.MQTT_State == True:
            # Check for messages, this triggers the callback
            try:
                self.MQTT_Client.check_msg()
            except:
                # Mark we disconnected
                self.MQTT_State = False
                return
            # Empthy Log_Queue
            self.Log_Queue_Empyhy()
        else:
            self.MQTT_Connect()

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

        # blink Indicator if configured
        if self.Indicator != None:
            # Check if we got a blink for this log level aka anythign else then Debug and Info
            if Level > 1:
                # level = number of
                # On for = "0.5s"
                # delay = "1s"
                # Add ticks to name so we dont overwrite last error
                self.Indicator.Add("Log-" + Level_String + "-" + str(utime.ticks_ms()), Level, "0.5s", "0.5s")

        # Build topic string
        Topic = self.Config.get('System_Header', '/Unconfigured') + "/" + self.Config.get('Hostname', 'ChangeMe') + "/Log/" + Level_String + "/" + Topic

        # Always print message to serial
        print("-> " + Topic + " - " + Payload)
    
        # Log level check
        if Level < int(self.Config.get('Log_Level', 1)):
            return

        # Publish message, MQTT_Publish adds to queue if offline
        self.MQTT_Publish(Topic, Payload)


    # -------------------------------------------------------------------------------------------------------
    def Peripherals_Topic(self, Peripheral, End=None, State=False):
        # Generate topic
        # System header first
        Return_String = self.Config['System_Header'] + "/"
        # Then Hostname
        Return_String = Return_String + self.Config['Hostname']
        # Then Peripheral
        Return_String = Return_String + "/" + str(Peripheral)
        # Then End if not none
        if End != None:
            # Remember to add a "/" her
            Return_String = Return_String + "/" + str(End)
        # Add state if set to True
        if State == True:
            Return_String = Return_String + "/State"
        # Then return the pretty string we created
        return Return_String


    # -------------------------------------------------------------------------------------------------------
    def Log_Peripheral(self, Message, Retained=True):
        # Used for logging from peripherals
        # Sends payload to the Topic as retained if requested
        # Logs from this is usually set to retained so devices get info about the peripherals on commect to mqtt

        # Message Should be dict or list
        # List = [<Topic>, <Payload>]
        # Dict = {'Topic': <Topic>, 'Payload': <Payload>}

        # Custom Exception
        class Log_Peripheral_Error(Exception):
            pass

        # We need a try here in case Topic or Payload is not set
        # Check if list
        if type(Message) == list:
            try:
                # Publish the message, self.MQTT_Publish will queue of we are offline
                self.MQTT_Publish(
                    str(Message[0]),
                    str(Message[1]),
                    Retained
                )
            except IndexError:
                # Since we can tell if its topic or Payload we are missing just check the length if the list
                if len(Message) < 2:
                    raise Log_Peripheral_Error('Missing either Topic or Payload')
                if len(Message) > 2:
                    raise Log_Peripheral_Error('function takes 2 positional arguments but ' + str(len(Message)) +  ' were given')
            else:
                # Always print message to serial regardless of log level
                print("->", Message[0], "-", Message[1])


        # Check if dict
        elif type(Message) == dict:
            try:
                # Publish the message, self.MQTT_Publish will queue of we are offline
                self.MQTT_Publish(
                    str(Message['Topic']),
                    str(Message['Payload']),
                    Retained
                )
            except KeyError:
                for Entry in ['Topic', 'Payload']:
                    try:
                        Message[Entry] = Message[Entry]
                    except KeyError:
                        raise Log_Peripheral_Error('Missing ' + Entry)
            else:
                # Always print message to serial regardless of log level
                print("->", Message['Topic'], "-", Message['Payload'])

        # Type error
        else:
            # Raise a Type error since only dict and list is supported
            raise Log_Peripheral_Error("Unsupported type: " + str(type(Message)))


    # -------------------------------------------------------------------------------------------------------
    # This should be used to write messsages both to serial and mqtt
    def Loop(self):
        # Start eternal loop
        while True:
            # handle mqtt
            self.MQTT_Loop()
            
            # Run loop from imported modules
            for Name in self.Modules:
                Error = None
                # If loop not in module ignore that error
                try:
                    self.Modules[Name].Loop()
                except AttributeError as e:
                    if "'Init' object has no attribute 'Loop'" in str(e):
                        # If this happens it means that loop isent in the module
                        # thats ok noting to see here so might as well continue
                        continue
                    # Save the error to var and contine so we delete the module and log the event
                    else:
                        Error = str(e)
                # except:
                #         Error = "Unexpected error"
                finally:
                    if Error != None:
                        # Log event
                        self.Log(3, "System", "Disabling module: '" + Name + "' due to error: " + Error)
                        # If something happens when running a module
                        # disable it so we can keep running by deleting it
                        del self.Modules[Name]
            
            # System Loops if configured aka not None
            for Name in self.Sys_Modules:
                Error = None
                # Run loop if present
                try:
                    self.Sys_Modules[Name].Loop()
                except AttributeError as e:
                    if "'Init' object has no attribute 'Loop'" in str(e):
                        # If this happens it means that loop isent in the module
                        # thats ok noting to see here so might as well continue
                        continue
                    # Save the error to var and contine so we delete the module and log the event
                    else:
                        Error = "AttributeError:" + str(e)
                # If we get a timer error do something about it
                except self.Sys_Modules['timer'].Timer_Error as e:
                    Error = str(e)
                    
                finally:
                    # Check for errors
                    if Error != None:
                        # Log event
                        self.Log(3, "System", "Error in System Module " + Name + ": " + Error)
                        # FIX BETTER ERROR HANDLING

            # Check if we have push messages to send
            if len(self.Push_Queue) < 0:
                # Try to publish, if we get True the message was send
                if self.Push_URL(self.Push_Queue[0]) == True:
                    self.Log(0, "Push", "Send queued push")
                    # If the message was send then remove it from the queue
                    self.Push_Queue.pop(0)

            # # If we are running on a ESP32 then we need to time.sleep_ms(12)
            # # to allow webrepl to run
            # if self.ESP_Type == 32:
            #     utime.sleep_ms(12)