#!/usr/bin/python

# Module for dobby on wemos d1 mini using micropython

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
Version = 300014

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
            self.CLI()

        # Default log level = 1 aka Info
        self.Log_Level = 1
        # Log queue to hold logs untill we can pass it on to base
        self.Log_Queue = []

        # Log relies on this to check if we need to blink on errors
        # So needs to be set before log is used the first time
        self.Indicator = None

        # Disable AP if enabeled
        network.WLAN(network.AP_IF).active(False)
            
        # Create self.wlan0 reference
        self.wlan0 = network.WLAN(network.STA_IF)
        # Activate self.wlan0 regardless if it is no not
        self.wlan0.active(True)

        # System header added in front of log messages
        self.System_Header = "/Unconfigured"

        # Var to hold stat of MQTT Connection
        self.MQTT_State = 'init'

        # Used to download modules aka mqtt broker
        self.Server = Network_Config["MQTT Broker"]

        # List of modules avalible on server
        self.Module_Index = None
        self.Module_Index_Last_Get = None

        # Log start of script
        self.Log(1, "System", "Starting Dobby Loader - Version: " + str(Version))

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
            self.CLI()


        # Check if the right SSID and hostname is configured
        if self.wlan0.config('essid') != Network_Config['WiFi SSID'] or self.wlan0.config('dhcp_hostname') != Network_Config['Hostname']:
            # Disconnect from incorrect ssid
            self.wlan0.disconnect()
            # Hostname only works with version 4 +
            # Set wifi hostname
            self.wlan0.config(dhcp_hostname=Network_Config['Hostname'])
            # Connect to wifi
            self.wlan0.connect(Network_Config['WiFi SSID'], Network_Config['WiFi Password'])
            # Log event
            self.Log(1, "System", "WiFi config change")
            # Wait for wifi to reconnect
            self.Wait_For_WiFi(Print=True)

        # After wifi is connected run Get_Configs to download Config files if needed
        try:
            self.Get_Configs()
        except:
            # if we get an error here we could not get config from server
            # Check to see if we have needed config to boot
            # we know we got network config at this stage
            # so we only need network config
            try:
                uos.statvfs('/conf/network.json')
            except:
                # If we do not have network.json we cannot boot
                self.Log(5, "System", "Missing network config unable to boot")
                # exit to repl
                sys.exit()

        # Log event
        self.Log(0, "System", "Checking modules")

        # # After wifi is connected run Module_Get to download modules if needed
        self.Module_Get()

        # Log event
        self.Log(1, "System", "System check compleate, loading modules")


        # Create MQTT Object
        import umqttsimple as MQTT
        self.MQTT = MQTT

        # Load device config
        Device_Config = self.Config_Load('device')

        # Change log level if set in config
        self.Log_Level = Device_Config.get('Log Level', 1)
        # Change system header
        self.System_Header = Device_Config['System Header']

        # If this is set, all subscribe and publishes will be mirrored and topic replaced as folles
        # <System Header>/<Hostname>/ = <self.gBridge>
        # We have to load this before mqtt so we know if we need to mirror topics
        self.gBridge_Topic = Device_Config.get('gBridge Topic', None)

        # Variable for Pin Monitor
        # Remember to pass base aka self
        import pinmonitor
        self.Pin_Monitor = pinmonitor.Init(self)
        ## Holds all loaded modules
        self.Modules = {}
        # Holds loaded System Modules like WirePusher if enabeled
        self.Sys_Modules = {}

        # List of push messages that failed to send
        # we retry when online again
        self.Push_Queue = []

        # Change CPU frequancy if requested
        # if Config.get('CPU_16', False) == True:
        #     machine.freq(160000000)
        #     self.Log(1, 'System', 'CPU frequancy set to: 16MHz')

        # MQTT Connection status
        self.MQTT_State = 'init'
        self.MQTT_Reconnect_At = 0
        self.MQTT_Subscribe_To = []
        self.MQTT_Client = None
        self.MQTT_Ping_At = utime.ticks_ms()
        
        # Subscribe to Commands topic
        self.MQTT_Subscribe(self.Peripherals_Topic("Commands"))

        # Var to indicate of we have published the ip we got when wifi connected
        self.Published_Boot = False



        # ++++++++++++++++++++++++++++++++++++++++ MQTT ++++++++++++++++++++++++++++++++++++++++
        # Remember to add something raondom after the hostname so the borker see a new connecton
        # Check if we got a user and pass for mqtt
        # Generate Unique Post Hostname
        Post_Hostname = str(uos.urandom(1)[0] %1000)
        # Log event
        self.Log(0, 'MQTT', 'Using hostname: ' + self.wlan0.config('dhcp_hostname') + "-" + Post_Hostname)
        # Stores messages so we can act on them in MQTT Loop
        ## List containing Topic and payload
        ## [[<Topic>, <Payload>]]
        self.MQTT_Incomming_Queue = []
        # Create MQTT Client
        self.MQTT_Client = self.MQTT.MQTTClient(
            self.wlan0.config('dhcp_hostname') + "-" + Post_Hostname,
            self.Server,
            int(Device_Config.get('MQTT Port', 1883)),
            Device_Config.get('MQTT Username', None),
            Device_Config.get('MQTT Password', None)
        )
        # Set last will
        self.MQTT_Client.set_last_will(self.System_Header + "/" + self.wlan0.config('dhcp_hostname') + "/Log/Will", "Disconnected")
        
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
        Config_List.remove('network.json')
        
        # # Move relay to the front of the list if present
        # ## try to remove
        # for Entry in ['dimmer.json' , 'relay.json']:
        #     try:
        #         Config_List.remove(Entry)
        #     ## if it fails do nothing
        #     except ValueError as e:
        #         pass
        #     ## If we removed relay.json add it back at the beginning of the list
        #     else:
        #         Config_List.insert(0, Entry)

        ## Loop over names in config
        for Name in Config_List:

            # Strip .json from name
            Name = Name.replace('.json', '')

            # Import the config
            Config = self.Config_Load(Name)
            Error = None

            # Load config is False if no config is found
            if Config is not False:
                try:
                    # Try to import
                    Module = __import__(Name)
                    # Store objevt in self.Modules
                    # Pass config and get perifical object
                    # Remember to pass Shared aka self so we can log in Button and use dobby variables
                    self.Modules[Name] = Module.Init(self, Config)
                    
                except (AttributeError, TypeError, SyntaxError, KeyError) as e:
                    Error = str(e)
                # Incompatible mpy file
                # except ValueError:
                #     # remove module
                #     uos.remove('/lib/dobby/' + Name.replace('.json', '.mpy'))
                #     # Log event
                #     Error = "Removed Module: " + Name.replace('.json', '') + " due to incompatibility"
                except MemoryError:
                    Error = 'Not enough free memory. Free memory: ' + str(gc.mem_free())
                except self.Error as e:
                    Error = str(e)

                # No errors on import in creation of module object
                else:
                    # Log event
                    self.Log(0, "System", "Module loaded: " + str(Name))

                finally:
                    # Check if Module import ok
                    if Error != None:
                        # remove module from self.Modules if added
                        try:
                            del self.Modules[Name.replace('.json', '')]
                        except:
                            pass
                        # Dont remove config on "Missing module" we are trying to download it when we get wlan0 up
                        if Error.startswith("Missing module: ") != True:
                            # Log event
                            self.Log(4, "System", "Unable to load module: " + str(Name) + " - Error: " + Error)
                            # Remove config file
                            uos.remove("/conf/" + Name + '.json')
                            # Log removal of config file
                            self.Log(1, "System", "Removed config file: " + Name)
            else:
                self.Log(0, 'System', "Invalid config: " + Name)

        # Activate indicator if 'LED' owned by Indicator aka not used for something else
        # on esp32 its IO2
        # on esp8266 its D4
        if self.Pin_Monitor.Get_Owner(self.Pin_Monitor.LED) == 'Indicator':
            # check if indicator is already imported and init
            if self.Sys_Modules.get('indicator', None) == None:
                # Import Indicator
                import indicator
                # Init Indicator and store in Sys_Modules to enable loop
                self.Sys_Modules['indicator'] = indicator.Init(self, {"System": {"Pin": "LED"}})
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
        Topic = self.System_Header + "/" + self.wlan0.config('dhcp_hostname') + "/Log/" + Level_String + "/" + Topic

        # Always print message to serial
        print("-> " + Topic + " - " + Payload)
        
        # Log level check
        if Level < self.Log_Level:
            return

        # Publish to mqtt. MQTT_Publish will queue the message if not connected
        self.MQTT_Publish(Topic, Payload)


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
    def Peripherals_Topic(self, Peripheral, End=None, State=False):
        # Generate topic
        # System header first
        Return_String = self.System_Header + "/"
        # Then Hostname
        Return_String = Return_String + self.wlan0.config('dhcp_hostname')
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
    def MQTT_On_Message(self, topic, msg):
        # Stores the incomming message in self.MQTT_Incomming_Queue
        # They will be read in MQTT_Loop

        Topic = topic.decode('utf8')
        # Now strip everything up to and including hostname + /
        # The + 1 is for the / after hostname
        Topic = Topic[Topic.index(self.wlan0.config('dhcp_hostname')) + len(self.wlan0.config('dhcp_hostname')) + 1:]

        # Add message to queue
        self.MQTT_Incomming_Queue.append([Topic, msg.decode('utf8')])


    # -------------------------------------------------------------------------------------------------------
    def MQTT_First_Connect(self):

        # Will check if we publishe the ip here since we dont run a loop for wifi
        if self.Published_Boot == False:
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
            Error = str(e)
            # Check if it matches the current state, aka nothing changed
            if self.MQTT_State != Error:
                # No change since last connection attempt
                ## Warning since initial connection attempt failed
                if self.MQTT_State == 'init':
                    self.Log(2, 'System', 'Unable to connect to broker: ' + str(self.Server))
                elif '103' in Error or '104' in Error:
                    self.Log(2, 'System', 'Disconnected from broker: ' + str(self.Server))
                else:
                    self.Log(2, 'System', 'MQTT Error: ' + Error)
                    
        # MQTT Username and pass issue
        except self.MQTT.MQTTException as e:
            Error = str(e)
            # Check if it matches the current state, aka nothing changed
            if self.MQTT_State != Error:
                # Incorect useranem and password
                if Error == "5":
                    self.Log(2, 'System', 'Incorrect username and password')
                    Error = "5"
                else:
                    self.Log(2, 'System', "Unknown error - Exception: " + Error)
        # except:
        #     self.Log(2, 'System', 'Unknown error')
        #     Error = True
        finally:
            if Error != None:
                if Error != self.MQTT_State:
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

        # during first connect we need to replace System_Header in all topics
        if self.MQTT_State == 'init':
            # replace all "/Unconfigured" with system header
            for i in range(len(self.Log_Queue)):
                self.Log_Queue[i][0] = self.Log_Queue[i][0].replace("/Unconfigured", self.System_Header)

        # When we get to here we should be connected
        self.MQTT_State = True

        # if we connected to mqtt empyth the log checks the connection state
        self.Log_Queue_Empyhy()
        
        # Log event
        self.Log(1, 'MQTT', 'Connected to MQTT Broker: ' + str(self.Server))

        # Register on mqtt message callback
        self.MQTT_Client.set_callback(self.MQTT_On_Message)

        # Subscribe to topics
        for Topic in self.MQTT_Subscribe_To:
            # Subscribe
            self.MQTT_Subscribe(Topic)


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
                        self.System_Header + "/",
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
        print('<- ' + self.System_Header + "/" + self.wlan0.config('dhcp_hostname') + "/" + str(Topic) + " - " + str(Payload))

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

        Peripheral_Name = None

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
        except AttributeError as e:
            # Log event
            self.Log(3, "System", "Module: " + str(Module_Name) + " Error: " + str(e))
        # KeyError indicates unknown module or Peripheral_Name
        except KeyError as e:
            if Module_Name in str(e):
                self.Log(2, "System", "Unknown Module name: " + str(Module_Name))
            else:
                self.Log(2, "System", "Unknown Peripheral name: " + str(e))


    # -------------------------------------------------------------------------------------------------------
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
                # Ping once every 5 sec
                if utime.ticks_diff(utime.ticks_ms(), self.MQTT_Ping_At) > 5000:
                    # Ping to check connection is still up
                    self.MQTT_Client.ping()
                    # Reset ping timer
                    self.MQTT_Ping_At = utime.ticks_ms()
                # Check for messages
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
        # Publish to gbridge if configured
        try:
            self.MQTT_Publish_gBridge(Topic, Payload, Retained)
        except:
            pass

        return True

    # -------------------------------------------------------------------------------------------------------
    def MQTT_Commands(self, Payload):

        # ++++++++++++++++++++++++++++++++++++++++ Reboot ++++++++++++++++++++++++++++++++++++++++
        # Reboots the device
        if Payload.lower() == 'reboot':
            # Run self.Reboot is will do the rest
            self.Reboot("MQTT Commands")
            

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
                self.Log_Level = self.Is_Number(Payload[10:])
            except ValueError:
                self.Log(2, "Commands", "Invalid log level: " + Payload[10:])
            else:
                self.Log(1, "Commands", "Log level set to: " + str(self.Log_Level))
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

        else:
            self.Log(1, 'System', "Unknown command: " + Payload)
            return


    # -------------------------------------------------- Wait for WiFi --------------------------------------------------
    def Wait_For_WiFi(self, Print=False):

        if Print == True:
            # Print wait message
            print()
            print("Waiting for WiFi to reconnect")
            print()

        # int to hold 0.5 increments
        i = 0

        # Start while loop and wait for wifi to connect
        try:
            while self.wlan0.isconnected() == False:
                if Print == True:
                    # print Waiting message message
                    print('Press CTRL + C to interrupt WiFi reconnect. Trying for: ' + str(i) + " sec", end="\r")
                # Sleep for 0.5s
                utime.sleep_ms(500)
                # Add 0.5 to i
                i = i + 0.5
            if Print == True:
                print()
        except KeyboardInterrupt:
            if Print == True:
                # print() so we end the line above and the next print dont end up before the above text
                print()
                # Print event
                print("Waiting for WiFi interrupted after " + str(i) + " sec - Starting CLI")
                print()
            # raise self.Error
            raise self.Error("Wait_For_WiFi: KeyboardInterrupt after " + str(i) + " sec")
        else:
            if Print == True:
                # print() so we end the line above and the next print dont end up before the above text
                print()
                # Print event
                print("WiFi connected to SSID: " + str(self.wlan0.config('essid')))
                print("Got IP: " + str(self.wlan0.ifconfig()[0]))
                print()
            # return true when wifi is connected
            return True
    
    
    # -------------------------------------------------- Config Download --------------------------------------------------
    def Config_Download(self, Name):

        # Build config url
        URL = "http://" + self.Server + ":8000/Config/" + self.wlan0.config('dhcp_hostname') + "/" + Name + ".json"

        Server_Config = None

        # Try to get Config
        try:
            Server_Config = urequests.get(URL)
        except OSError as e:
            print("123123123 MARIKER")
            print("123123123 MARIKER")
            print("123123123 MARIKER")
            print("123123123 MARIKER")
            print(e)
            return False
        else:
            # Check for status code 200 to see if we got the file
            if Server_Config.status_code == 200:
                Local_Config = None
                # Check if downloaded config matches server config
                # Try to load local config
                try:
                    Local_Config = self.Config_Load(Name)
                # If we get Error we assume the file is missing
                # Just pass will save it below in finally
                except self.Error:
                    pass
                finally:
                    # Convert Server_Config to dict
                    Server_Config = Server_Config.json()
                    # Check if local config now check if it matches config on the server
                    if Local_Config != Server_Config:
                        try:
                            # Save and overwrite Config if existsw
                            with open('/conf/' + Name + '.json', 'w') as f:
                                # write Config to file
                                ujson.dump(Server_Config, f)
                        except:
                            # raise self.Error on failure to save to fs
                            raise self.Error('Download Config: Unable to save config: "' + Name + '.json" to fs')
                        else:
                            # Log event
                            self.Log(0, "System", "Config updated: " + Name)
                            # Return true when we saved the Config
                            # or if local config matches server config
                            return True
            # If status code is not 200 raise self.Error
            else:
                raise self.Error("Download Config: Did not get code 200 after get. Config: " + str(Name) + " URL: " + URL)


    # ---------------------------------------- Config Save ----------------------------------------
    def Config_Save(self, Config, File_Name):
        if type(Config) == str:
            # Try to parse json
            try:
                # parse json to config dict
                Config = ujson.loads(Config)
            # Error in json string
            except ValueError:
                raise self.Error("Config Save: Invalid json string provided")
        
        # Try to open config file for writing
        try:
            with open('/conf/' + File_Name + '.json', 'w') as f:
                # write config file to device
                ujson.dump(Config , f)
        except:
            raise self.Error("Config Save: Unable to save file")


    # ---------------------------------------- Config Load ----------------------------------------
    def Config_Load(self, File_Name):
        # Var to hold loaded config
        Config = None
        # Try to read device config file
        try:
            with open('/conf/' + File_Name + '.json', 'r') as f:
                Config = ujson.load(f)
        # OSError = Missing network.json
        except OSError:
            raise self.Error("Config not found: " + str(File_Name))
        except ValueError:
            # If the local config contains an error will delete it
            uos.remove('/conf/' + File_Name + '.json')
            # raise self.Error
            raise self.Error("Error in json: " + str(File_Name) + " - Local config removed")
        else:
            return Config


    # ---------------------------------------- Config Check ----------------------------------------
    def Config_Check(self, Config_Dict, Check_List):
        # Check if we got the needed config
        Failed = []

        for Entry in Check_List:
            if Config_Dict.get(Entry, None) == None:
                Failed.append(Entry)
                
        # Check if we failed
        if Failed != []:
            raise self.Error(Failed)
        else:
            return True


    # -------------------------------------------------- Get Config --------------------------------------------------
    # Downloads each config file from server for this device
    # and compares it to local config, if not same or none existing it server config will be saved
    def Get_Configs(self):
        # Build URL
        URL = "http://" + self.Server + ":8000/Config/" + self.wlan0.config('dhcp_hostname') + "/"
        try:
            # Get list of config files on server
            Server_Config_List = urequests.get(URL).text
        except OSError:
            # OSError = wifi up but server not responding aka webserver not running
            raise self.Error("Get_Configs: Webserver not responding: http://" + self.Server + ":8000")
        except:
            # raise self.Error when we cant get config dir
            raise self.Error("Get_Configs: Config dir not found: " + URL)
        
        # Split Config list to get config files
        Server_Config_List = Server_Config_List.split('href="')
        # pop(0) since this is garbage
        Server_Config_List.pop(0)

        Local_Config_List = uos.listdir('conf')

        # for loop over Server_Config_List 
        for Entry in Server_Config_List:

            # Split at '.json' and take [0] to remove garbage text from end of file name
            Entry = Entry.split('.json')[0]

            # Try to download Device_Config.
            # Config_Download will return true if local config matches server config or of server config was downloaded
            # else Config_Download will raise an error
            try:
                # download config
                self.Config_Download(Entry)
            # Error downloaning config
            except Error as e:
                # FIX BETTER ERROR HANDLING
                raise self.Error("Error downloading config: " + str(e))

            # remove from Local_Config_List
            # pass on all errors
            # might not be in local config
            try:
                Local_Config_List.remove(Entry + ".json")
            except:
                pass

        # Check if there is anything left if Local_Config_List
        # if there is delete the local config since it was removed from the server
        for Entry in Local_Config_List:
            self.Log(1, 'System', 'Local config for: ' + str(Entry) + " not found on server. Removing corosponding module and config")
            # remove local config
            # do not add .json
            uos.remove('conf/' + Entry)
            # Remove module
            # remember to replace .json with .mpy
            uos.remove('lib/' + Entry.replace('.json', '.mpy'))

        # Log event
        self.Log(1, "System", "Get config compleate")


    # -------------------------------------------------- Get Module Index --------------------------------------------------
    def Module_Index_Get(self, Force_Refresh=False):

        # when an if statement matches will pass so we dont trigger return in else
        # in other works pass = trigger code below
        if Force_Refresh == True:
            pass
        elif self.Module_Index == None:
            pass
        elif utime.ticks_diff(self.Module_Index_Last_Get, utime.ticks_ms()) > 5000:
            pass
        else:
            return

        # get index.json it contains a list of avalible modules and version numbers
        try:
            # get index.json from server
            self.Module_Index = urequests.get("http://" + self.Server + ":8000/Modules/index.json")
            # Pass json to dict
            self.Module_Index = self.Module_Index.json()
            # set ticks ms for when it downloaded to check against
            self.Module_Index_Last_Get = utime.ticks_ms()
            # log event
            self.Log(0, "System", "module index updated")
        except OSError:
            # os error = timeout
            self.Module_Index_Last_Get = utime.ticks_ms()
            # Convert to dict and not time so we dont try to download right away again
            raise self.Error('Module_Get_Index: No reply from server: ' + self.Server)
        except:
            # raise self.Error containing missing index.json
            # without it we cannot deturman module version numbers
            raise self.Error('Module_Get_Index: index.json not avalible on Server: ' + self.Server)


    # -------------------------------------------------- Download Module --------------------------------------------------
    def Module_Download(self, Name, Print=False):

        # Check that we got self.Module_Index aka index.json
        self.Module_Index_Get()

        URL = None

        # Check if module groupe is avalible
        if self.Module_Index.get(uos.uname().sysname, None) != None:
            # Check if module is avalible
            if self.Module_Index[uos.uname().sysname].get(Name, None) != None:
                # Build url
                URL = "http://" + self.Server + ":8000/Modules/" + uos.uname().sysname + "/" + Name + ".mpy"
        
        if URL == None:
            if Print == True:
                # Log event
                print('Module "' + Name + '" not avalible on Server: ' + self.Server)
            # raise self.Error on failure to fiond module on Server
            raise self.Error('Module_Download: Module "' + Name + '" not avalible on Server: ' + self.Server)

        # Try to get module
        try:
            Module = urequests.get(URL)
        except OSError as e:
            raise self.Error('Module_Download: OSError: ' + str(OSError) + ' during download of module: ' + Name)
        else:
            # Check for status code 200 to see if we got the file
            if Module.status_code == 200:
                try:
                    # Save and overwrite module if existsw
                    with open('/lib/' + str(Name) + '.mpy', 'w') as f:
                        # write module to file
                        f.write(Module.content)
                except:
                    if Print == True:
                        # Log error
                        print("Unable to save module to fs: " + Name)
                    # raise self.Error on failure to save to fs
                    raise self.Error('Module_Download: Unable to save "' + Name + '" to fs')
                else:
                    if Print == True:
                        # Log event
                        print("Module downloaded: " + str(Name) + " URL: " + URL)
                    # Return true when we saved the module
                    return True
            # If status code is not 200 raise self.Error
            else:
                if Print == True:
                    # Log event
                    print("Did not get code 200 after get. Module: " + str(Name) + " URL: " + URL)
                raise self.Error("Did not get code 200 after get. Module: " + str(Name) + " URL: " + URL)


    # -------------------------------------------------- Get Modules --------------------------------------------------
    def Module_Get(self):

        if self.wlan0.isconnected() == False:
            self.Wait_For_WiFi(Print=True)

        # Lists with names of modules we need to have
        System_Modules = None

        # Add modules only needed for esp32
        if uos.uname().sysname == 'esp32':
            System_Modules = ['base', 'timer', 'indicator', 'pinmonitor', 'umqttsimple']
        # Add modules only needed for esp32
        elif uos.uname().sysname == 'esp8266':
            System_Modules = ['base', 'timer']
        
        # Add System_Modules to Needed_Modules
        Needed_Modules = list(System_Modules)

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
        Lib_List = uos.listdir('/lib')

        # If a module is updated we need to reboot to load the new version
        Reboot_Required = False

        # Check if we got all the modules we need
        for Module_Name in Needed_Modules:
            # Check if modules is in lib folder
            # remember to add ".mpy" to Module_Name
            if Module_Name + '.mpy' not in Lib_List:
                # Log event
                self.Log(0, "System", "Trying to download module: " + Module_Name)
                # Module not in list try to download it
                try:
                    self.Module_Download(Module_Name)
                except self.Error as e:
                    if Module_Name in System_Modules:
                        self.Log(5, "System", "Unable to get system module: " + Module_Name + " - Cannot boot - " + str(e))
                        # Raise Loader error so we exit script to repl
                        raise self.Error("Unable to get system module: " + Module_Name + " - Cannot boot - " + str(e))
                    else:
                        # remove config so we dont load the module
                        uos.remove('/conf/' + Module_Name + '.json')
                        # log error
                        self.Log(3, "System", "Unable to get device module: " + Module_Name)
                        
                else:
                    # Log event
                    self.Log(1, "System", "Downloaded module: " + Module_Name)
                    continue

            # Module already on device, import so we can check version
            else:
                # Skip modules below, since they do not have version numbers
                if Module_Name in ['ntptime', 'umqttsimple']:
                    # Log event
                    self.Log(0, "System", "Cannot check version on Module: " + Module_Name)
                    continue

                try:
                    # Makre sure we got module index
                    self.Module_Index_Get()
                except self.Error:
                    self.Log(0, "System", "Cannot check version on Module: " + Module_Name + " - Module index not avalible")
                else:

                    # import module, this will not init it but only expose Version
                    try:
                        Module = __import__(Module_Name)
                    except ValueError as e:
                        if 'incompatible .mpy file' in str(e):
                            # Delete bad mpy file
                            uos.remove('/lib/' + Module_Name + '.mpy')
                            # FIX - FIND a way to break the reboot loop crated by this
                            Reboot_Required = True
                    else:
                        # Check where we have the module in device of shared
                        if self.Module_Index[uos.uname().sysname].get(Module_Name, None) != None:
                            
                            # Check if module has version var
                            try:
                                Module.Version
                            except AttributeError:
                                # Log event
                                self.Log(0, "System", "Module: " + Module_Name + " has no 'Version'")
                                continue

                            # Check if version is ok
                            if Module.Version == self.Module_Index[uos.uname().sysname][Module_Name]['Version']:
                                # Log event
                                self.Log(0, "System", "Module: " + Module_Name + " up to date")
                            # Module outdated
                            elif Module.Version > self.Module_Index[uos.uname().sysname][Module_Name]['Version']:
                                # Log event
                                self.Log(2, "System", "Module: " + Module_Name + " never than servers")
                                # Module outdated
                            elif Module.Version < self.Module_Index[uos.uname().sysname][Module_Name]['Version']:
                                # Log event
                                self.Log(1, "System", "Module: " + Module_Name + " out of date, downloading version: " + str(self.Module_Index[uos.uname().sysname][Module_Name]['Version']))
                                # Try to download
                                try:
                                    self.Module_Download(Module_Name)
                                except self.Error as e:
                                    if Module_Name in System_Modules:
                                        self.Log(5, "System", "Unable to get system module: " + Module_Name + " - Cannot boot - Download Module error: "+ str(e))
                                        # Raise Loader error so we exit script to repl
                                        raise self.Error("Unable to get system module: " + Module_Name + " - Cannot boot - Download Module error: "+ str(e))
                                    else:
                                        # Log event
                                        self.Log(1, "System", "Unable to get device module: " + Module_Name)
                                else:
                                    # Log event
                                    self.Log(1, "System", "Downloaded module: " + Module_Name)
                                    # Note that we need to reboot
                                    Reboot_Required = True
                                    # Break for loop so we dont trigger finally
                                    break

                        # Check if we found module in module index
                        else:
                            # if we get to here the module was not found in the Module_Index aka index.json
                            # Log event
                            self.Log(2, "System", "Module: " + Module_Name + " not in index.json")

        # Check if we need to reboot
        if Reboot_Required == True:
            self.Log(1, "System", "Modules updated rebooting")
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
        # Clear mqtt queue
        self.Log_Queue_Empyhy()
        # Little break to let system send
        utime.sleep_ms(750)
        # reboot
        machine.reset()


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
        # Loads timer if not already loaded
        if self.Sys_Modules.get('timer', None) == None:        
            # Import Timer
            import timer
            # Init Timer and store in Sys_Modules to enable loop
            self.Sys_Modules['timer'] = timer.Init(self)
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
        

    # -------------------------------------------------------------------------------------------------------
    def CLI(self):

        # Dict to hold config
        Config = {}
        # Try to load network.json to 'Config'
        # if failes create an empthy dict 
        try:
            # Try to load config
            Config = self.Config_Load('network')
        except:
            # Create empthy dict on failure
            Config = {}

        # print cli init message
        print("Starting cli")
        print("Please configure:")
        print("   Hostname")
        print("   WiFi SSID")
        print("   WiFi Password")
        print("   MQTT Broker")
        print("")

        # start eternal loop while getting user 
        while True:
            try:
                User_Entry = input("Dobby CLI: ")
            except (EOFError, KeyboardInterrupt):
                # If we got interrupted exit
                print("   Leaving CLI")
                sys.exit()

            # Check if the 200 pound gorilla pressed enter without entering a command
            if User_Entry == "":
                continue

            # ---------------------------------------- Help ----------------------------------------
            elif User_Entry.lower() == "help":
                print()
                print("Avalible commands:")
                print()
                print("   boot - boot the device")
                print("   json - past device config as a json string")
                print("   show - shows the loaded config")
                print("   module list - lists all installed modules")
                print("   module delete - delete a installed module")
                print("   set <config> <to> - sets 'Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker'")
                print()

            # ---------------------------------------- boot ----------------------------------------
            # reboots the device
            # if required settings is give
            # saves config to fs first
            elif User_Entry.lower() == "boot":
                # check if config is ok
                try:
                    self.Config_Check(Config, ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker'])
                except self.Error as e:
                    print("   Missing config: " + str(e))
                    continue
                    
                # save config to file
                if self.Config_Save(Config, 'network') == False:
                    print("   Unable to save config")
                    continue

                # Log event
                print("   Config saved rebooting")
                # Reboot the device
                machine.reset()


            # ---------------------------------------- set ----------------------------------------
            # prints the current config
            elif User_Entry.lower() == "set":

                # List of options user can change
                Config_Options = ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker']

                # print list with number in front
                for i in range(len(Config_Options)):
                    print("   " + str(i) + " - " + str(Config_Options[i]))

                # Get config option number from user
                try:
                    print()
                    print("Press CTRL + C to cancle")
                    print()
                    Selected_Option = input("Please select config to change: ")
                    # Convert selection to int
                    Selected_Option = int(Selected_Option)
                    # check config exists in list
                    Config_Options[Selected_Option]
                except (EOFError, KeyboardInterrupt):
                    print("   canceled")
                except (ValueError, IndexError):
                    print("   invalid config selected: " + str(Selected_Option))
                else:
                    
                    # Get config option number from user
                    try:
                        print()
                        New_Value = input("Please enter new value for " + Config_Options[Selected_Option] + ": ")
                    except (EOFError, KeyboardInterrupt):
                        print("   canceled")
                    else:
                        # change config value
                        Config[Config_Options[Selected_Option]] = New_Value
                        # Log event
                        print("   Config: " + str(Config_Options[Selected_Option]) + " set to: " + str(New_Value))


            # ---------------------------------------- show ----------------------------------------
            # prints the current config
            elif User_Entry.lower() == "show":
                print("Current config:")
                for Key in ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker']:
                    print("   " + Key + ": " + Config.get(Key, "Not configured"))


            # ---------------------------------------- json ----------------------------------------
            # past device config as a json string
            elif User_Entry.lower() == "json":
                # Get json string from user
                json_Config = input("Please paste device config json string: ")

                # Try to parse json
                try:
                    # parse json to config dict
                    json_Config = ujson.loads(json_Config)
                # Error in json string
                except ValueError:
                    print()
                    print("   Invalid json string")
                    print()
                    continue
                # Json loaded ok, check if we got the needed config
                else:
                    Check_List = ['Hostname', 'WiFi SSID', 'WiFi Password', 'MQTT Broker']
                    try:
                        self.Config_Check(json_Config, Check_List)
                    except self.Error as e:
                        # Log error
                        print("   Missing config entries: " + str(e))
                        continue
                    # if we got a large config for some reason only take what we need aka keys in the check list
                    for Key in Check_List:
                        # Save value from json_Config in Config var
                        Config[Key] = json_Config[Key]
                    # Log Event
                    print("   json config ok")
                    continue
            
            # ---------------------------------------- module list ----------------------------------------
            # lists all modules
            elif User_Entry.lower() == "module list":
                # print to give distance to above
                print()
                # get list of libs
                Lib_List = uos.listdir('lib')
                # print list with number in front
                for i in range(len(Lib_List)):
                    print("   " + str(i) + " - " + str(Lib_List[i]))
                # Print to give space to command below
                print()


            # ---------------------------------------- module delete ----------------------------------------
            # lists all modules with number in front and lets the user deside what to delete
            # ctrl + c to cancle
            elif User_Entry.lower() == "module delete":
                # print to give distance to above
                print()
                
                # get list of libs
                Lib_List = uos.listdir('lib')

                # print list with number in front
                for i in range(len(Lib_List)):
                    print("   " + str(i) + " - " + str(Lib_List[i]))

                # Get user input
                try:
                    print()
                    print("Press CTRL + C to cancle")
                    print()
                    User_Entry = input("Select module to delete: ")
                except (EOFError, KeyboardInterrupt):
                    print("   canceled")
                else:
                    try:
                        # delete selected lib aka module
                        uos.remove('lib/' + Lib_List[int(User_Entry)])
                    except TypeError:
                        print("   invalid module selected: " + User_Entry)
                    else:
                        print("   deleted module: " + Lib_List[int(User_Entry)])


            # ---------------------------------------- Unknown command ----------------------------------------
            else:
                print("unknown command: " + User_Entry)


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