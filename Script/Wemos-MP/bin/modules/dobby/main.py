# Module for dobby on wemos d1 mini using micropython

import ujson
import utime
# import uping
import sys
import os
import network
import gc
import umqtt.simple as MQTT
import machine

import dobby.config as DobbyConfig


# -------------------------------------------------------------------------------------------------------
class Run:

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
        self.Pin_Monitor = self.Dobby_Pin_Monitor(self)
        ## Holds all loaded modules
        self.Modules = {}
        # Holds loaded System Modules like WirePusher if enabeled
        self.Sys_Modules = {}
 
        # MQTT Connection status
        self.MQTT_State = 'init'
        self.MQTT_Reconnect_At = 0
        self.MQTT_Subscribe_To = [self.Config['System_Header'] + "/Commands/" + self.Config['Hostname']]

        # Init message
        self.Log(1, 'System', 'Initializing Dobby version: ' + str(Version))


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
        # Set wifi hostname
        self.wlan0.config(dhcp_hostname=str(self.Config['Hostname']))
        # Activate wlan0
        self.wlan0.active(True)
        # Connect to wifi
        self.wlan0.connect(self.Config['WiFi_SSID'], self.Config['WiFi_Password'], )

        # Check if we connected
        if self.wlan0.isconnected() == True:
            # Log ip
            self.Log(0, 'WiFi', 'Got IP: ' + str(self.wlan0.ifconfig()[0]))
        else:
            # Log ip
            self.Log(0, 'WiFi', "Not connected")


        # ++++++++++++++++++++++++++++++++++++++++ MQTT ++++++++++++++++++++++++++++++++++++++++
        # Remember to add something raondom after the hostname so the borker see a new connecton
        # Check if we got a user and pass for mqtt
        # Generate Unique Post Hostname
        Post_Hostname = str(os.urandom(1)[0] %1000)
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
        self.MQTT_Client.set_last_will(self.Config['System_Header'] + "/Log/" + self.Config['Hostname'] + "/Will", "Disconnected")
        
        # try to connect to mqtt
        self.MQTT_Connect()


        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # Loop over config names in /conf and import matching modules
        ## Get config names
        Config_List = os.listdir('/conf')
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

        ## Loop over names in config
        for Name in Config_List:
            
            # Import the config
            ## False = Config not found or error during import
            ## If not false the imported Module will be returned

            Config = DobbyConfig.Load(Config_Name=Name, Delete_On_Error=False)
            Error = None

            # Load config is False if no config is found
            if Config is not False:
                # Try to import dobbydutton
                Module_Name = str('dobby.' + Name.replace('.json', ''))
                try:
                    Module = __import__(Module_Name.replace(".", '/'))
                except (AttributeError, TypeError, SyntaxError, ImportError, KeyError) as e:
                    Error = str(e)
                except MemoryError as e:
                    Error = 'Not enough free memory. Free memory: ' + str(gc.mem_free())
                finally:
                    # Check if Module import ok
                    if Error is None:
                        # Log event
                        self.Log(0, "System", "Module loaded: " + str(Module_Name))
                        # Pass config and get perifical object
                        # Remember to pass Dobby aka self so we can log in Button and use dobby variables
                        self.Modules[Name.replace('.json', '')] = Module.Init(self, Config)
                    else:
                        # Log event
                        self.Log(3, "System", "Unable to load module: " + str(Module_Name) + " - Error: " + Error)
                        # Remove config file
                        os.remove("/conf/" + Name)
                        self.Log(1, "System", "Removed config file: /conf/" + Name)
            else:
                self.Log(0, 'System', "Invalid config: /conf/" + Name + "'")

        # Will be set to true if configured by a device 
        # self.Wire_Pusher = None
        # Wire_Pusher = self.WirePusher()

        self.IndicatorLED = None
        # Activate indicator led if D4 owned by IndicatorLED aka not used for something else
        if self.Pin_Monitor.Pins['D4']['Owner'] == 'IndicatorLED':
            # Import IndicatorLED
            import dobby.indicatorled
            # Init IndicatorLED and store in Sys_Modules to enable loop
            self.Sys_Modules['IndicatorLED'] = dobby.indicatorled.Init(self)
            # Do boot blink if IndicatorLED is configured
            self.Sys_Modules['IndicatorLED'].Enable('Booting')

        
        # Boot done message
        self.Log(0, 'System', 'Dobby - Initialization compleate - Free memory: ' + str(gc.mem_free()))

        # Start loop()
        self.Loop()


    # ++++++++++++++++++++++++++++++++++++++++++++++++++ MISC ++++++++++++++++++++++++++++++++++++++++++++++++++



    # -------------------------------------------------------------------------------------------------------
    def Timer_Init(self):
        # Loads dobby.timer if not already loaded
        if self.Sys_Modules.get('Timer', None) == None:        
            # Import Timer
            import dobby.timer
            # Init Timer and store in Sys_Modules to enable loop
            self.Sys_Modules['Timer'] = dobby.timer.Init(self)
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
            if "." in Value:
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
        finally:
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
    def MQTT_Commands(self, Topic, Payload):
        # Check if its a message for MQTT_Commands
        if self.Config['System_Header'] + "/Commands/" + self.Config['Hostname'] not in Topic:
            return

        # ++++++++++++++++++++++++++++++++++++++++ Reboot ++++++++++++++++++++++++++++++++++++++++
        # Reboots the device
        elif Payload.lower() == 'reboot':
            # Log event
            self.Log(1, "System", "Rebooting - Triggered by MQTT Commands")
            # Disconnect from MQTT
            self.MQTT_Client.disconnect()
            # reboot
            machine.reset()
            return
    
    
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
        elif Payload.lower().startswith('free memory') == True:
            # Log free memory
            self.Log(1, "Commands", "Free memory: " + str(gc.mem_free()))
            return

        # ++++++++++++++++++++++++++++++++++++++++ Config ++++++++++++++++++++++++++++++++++++++++
        elif Payload.lower() == 'config list':
            # publishes a list of all config files
            dir_String = os.listdir('/conf')
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
                os.remove("/conf/" + Config_Name.replace(".json", "") + ".json")
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

        self.MQTT_Incomming_Queue.append([topic.decode('utf8'), msg.decode('utf8')])


    # # -------------------------------------------------------------------------------------------------------
    def MQTT_Connect(self):

        # Check if Wifi is up
        if self.wlan0.isconnected() == False:
            return
        
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
            # Get Error number
            Error = int(str(e).split(" ")[1].replace("]", ""))
            # Check if it matches the current state, aka nothing changed
            if self.MQTT_State != Error:
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
                # Check if IndicatorLED is enabeled
                if self.Sys_Modules.get('IndicatorLED', None) != None:
                    # Turn on MQTT blink
                    self.Sys_Modules['IndicatorLED'].Enable('MQTT')

                # Set self.MQTT_State = Error so we can check if it changed later in life
                self.MQTT_State = Error
                # return after error
                return

        # print('self.MQTT_Client.ping()')
        # print(self.MQTT_Client.ping())

        # Check if IndicatorLED is enabeled
        if self.Sys_Modules.get('IndicatorLED', None) != None:
            # Turn off MQTT blink
            self.Sys_Modules['IndicatorLED'].Disable('MQTT')


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
    def MQTT_Subscribe(self, Topic):
        # Add to topic list if not in list
        if Topic not in self.MQTT_Subscribe_To:
            self.MQTT_Subscribe_To.append(str(Topic))
        # Log event
        self.Log(0, 'MQTT', 'Subscribing to topic: ' + Topic)
        # Check if we are connected
        if self.MQTT_State == True:
            # Subscribe
            self.MQTT_Client.subscribe(Topic)



    # -------------------------------------------------------------------------------------------------------
    def MQTT_Handle_Incomming(self, Message):
        # Referance variables
        Topic = Message[0]
        Payload = Message[1]
        
        # Print to serial
        print('<- ' + str(Topic) + " - " + str(Payload))
        ## MQTT Commands
        self.MQTT_Commands(Topic, Payload)
        ## Pass to loaded modules
        for Name in self.Modules:
            # Run module On_Message
            # if they return true the contine since we had a hit on the message
            if self.Modules[Name].On_Message(Topic, Payload) is True:
                return


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Loop(self):

        # Incomming
        # Check is queue is empthy
        if len(self.MQTT_Incomming_Queue) != 0:
            # Act on up to 5 incomming message
            for i in range(0, 5):
                # Check is queue is empthy
                if len(self.MQTT_Incomming_Queue) == 0:
                    # The queue is empthy so break so we can move on to outgoing messages
                    break
                
                # Remove and pass the first message in the queue to MQTT_Handle_Incomming
                self.MQTT_Handle_Incomming(self.MQTT_Incomming_Queue.pop(0))
                

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

        # Build topic string
        Topic = self.Config.get('System_Header', '/Unconfigured') + "/Log/" + self.Config.get('Hostname', 'ChangeMe') + "/" + Level_String + "/" + Topic

        # Always print message to serial
        print("-> " + Topic + " - " + Payload)
    
        # Log level check
        if Level < int(self.Config.get('Log_Level', 1)):
            return

        # Publish message, MQTT_Publish adds to queue if offline
        self.MQTT_Publish(Topic, Payload)


    def Peripherals_Topic(self, Peripheral, End=None):
        # Generate topic
        # System header first
        Return_String = self.Config['System_Header'] + "/"
        # Then Peripheral
        Return_String = Return_String + str(Peripheral) + "/"
        # Then Hostname
        Return_String = Return_String + self.Config['Hostname']
        # Then End if not none
        if End != None:
            # Remember to add a "/" her
            Return_String = Return_String + "/" + str(End)
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
                        Error = str(e)
                # If we get a timer error do something about it
                except self.Sys_Modules['Timer'].Timer_Error as e:
                    Error = str(e)
                finally:
                    # Check for errors
                    if Error != None:
                        # Log event
                        self.Log(3, "System", "Error in System Module " + Name + ": " + Error)
                        # FIX BETTER ERROR HANDLING




    # -------------------------------------------------------------------------------------------------------
    #Pin monitor
    class Dobby_Pin_Monitor:
        # -------------------------------------------------- Config exception --------------------------------------------------
        class Error(Exception):
            pass

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby):
            # Create needed vars
            ## Referance to dobby
            self.Dobby = Dobby
            ## Dict holding reserved pins
            ### Format <Wemos Pin Name>: {'Owner': "DHT"} 
            self.Pins = {"D4": {'Owner': "IndicatorLED"}}


        # -------------------------------------------------------------------------------------------------------
        def Is_Free(self, Pin):
            # Check if pin is valid
            # self.Valid_Pin will raise an error if not
            self.Valid_Pin(Pin)
            # Check if pin is free
            if Pin in self.Pins:
                # Check if its indicator led owning the pin if so we can overwrite it
                if Pin == "D4":
                    self.Dobby.Log(1, "PinMonitor", "Removed IndicatorLED as owner of pin: D4")
                    # dont return here since we want to reserve the pin
                # Any other owner then IndicatorLED is failed
                else:
                    # Log error
                    self.Dobby.Log(2, "PinMonitor", "Pin: " + Pin + " owned by: " + self.Pins[Pin]['Owner'])
                    # Raise error
                    raise self.Error("Pin: " + Pin + " owned by: " + self.Pins[Pin]['Owner'])
            # Pin Free
            else:    
                self.Dobby.Log(0, "PinMonitor", "Pin: " + Pin + " is free")
                return True


        # -------------------------------------------------------------------------------------------------------
        def Reserve(self, Pin, Owner, Pull=False):
            # Check if pin is free
            # GPIO 16 aka D0 cannot have pull activated so fail if pull is requested active on D0

            # If pull is false do nothing
            if Pull == True:
                # Check if we are dealing with pin D0
                if Pin.lower() == 'd0':
                    # Log event
                    self.Dobby.Log(2, "PinMonitor", "Pin: " + Pin + " cannot have pull active, unable to reserve pin")
                    # Raise error
                    raise self.Error("Pin: " + Pin + " cannot have pull active, unable to reserve pin")

            # Is free will raise an error if the pin is not free
            # IndicatorLED will be overwriten if set
            if self.Is_Free(Pin) == True:
                # Reserve pin
                self.Pins[str(Pin)] = {'Owner': str(Owner)}
                # log event
                self.Dobby.Log(0, "PinMonitor", "Pin: " + Pin + " reserved for: " + str(Owner))
                # return true after sucesfully reserving the pin
                return True
            

        # -------------------------------------------------------------------------------------------------------
        def To_Wemos_Pin(self, Pin):
            # Convert to upper case to make checking easier
            Pin = Pin.upper()
            # Dict where key is pin name and value is gpio number
            Pin_Dict = {
                'D0': 16,
                'D1': 5,
                'D2': 4,
                'D3': 0,
                'D4': 2,
                'D5': 14,
                'D6': 12,
                'D7': 13,
                'D8': 15,
                'A0': 0
            }
            
            # Get gpio number from fict if key is not in dict return False aka failed
            return machine.Pin(Pin_Dict.get(Pin, False))


        # -------------------------------------------------------------------------------------------------------
        def To_GPIO_Pin(self, Pin):
            # Check if already valid pin
            if Pin in [0, 2, 4, 5, 12, 13, 14, 15, 16]:
                return Pin
            # Convert wemos pin name string to goip pin int
            # Convert pin name string to lover case
            Pin = Pin.upper()
            # Check of pin is valid
            if Pin == "D0":
                GPIO_Pin = 16
            elif Pin == "D1":
                GPIO_Pin = 5
            elif Pin == "D2":
                GPIO_Pin = 4
            elif Pin == "D3":
                GPIO_Pin = 0
            elif Pin == "D4":
                GPIO_Pin = 2
            elif Pin == "D5":
                GPIO_Pin = 14
            elif Pin == "D6":
                GPIO_Pin = 12
            elif Pin == "D7":
                GPIO_Pin = 13
            elif Pin == "D8":
                GPIO_Pin = 15
            # Note A0 is pin 0 as well as D3
            elif "A0" in Pin:
                GPIO_Pin = 0
            # if invalid string return false
            else:
                # Log event
                self.Dobby.Log(2, "PinMonitor", "Invalid wemos Pin name: " + str(Pin))
                # Raise error
                raise self.Error("Invalid wemos Pin name: " + str(Pin))
            # Return value
            return GPIO_Pin


        def Valid_Pin(self, Pin):
            # Wemos Pin Name
            if type(Pin) is str:
                if Pin.lower() in ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "a0"]:
                    self.Dobby.Log(0, "PinMonitor", "Valid Wemos Pin Name: " + Pin)
                    return True
            # GPIO Pin
            else:
                if Pin in [0, 2, 4, 5, 12, 13, 14, 15, 16]:
                    self.Dobby.Log(0, "PinMonitor", "Valid GPIO number: " + str(Pin))
                    return True
            # Unknown pin
            # Log event
            self.Dobby.Log(2, "PinMonitor", "Invalid pin: " + str(Pin))
            # Raise error
            raise self.Error("Invalid pin: " + str(Pin))

