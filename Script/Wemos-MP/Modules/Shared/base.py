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
Version = 300020

# -------------------------------------------------------------------------------------------------------
class Run:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Loader_Log):

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
            # self.CLI()
            import cli
            cli.Run(self)

        # Default log level = 1 aka Info
        self.Log_Level = 1
        # Log queue to hold logs untill we can pass it on to base
        self.Log_Queue = Loader_Log

        # Log relies on this to check if we need to blink on errors
        # So needs to be set before log is used the first time
        self.Indicator = None
    
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

        self.Hostname = Network_Config["Hostname"]

        # Log start of script
        self.Log(1, "System", "Starting Dobby Base - Version: " + str(Version))

        # Create MQTT Object
        import umqttsimple as MQTT
        self.MQTT = MQTT

        # Import config
        import config as dConfig

        # Load device config
        Device_Config = dConfig.Load('device')

        # Change log level if set in config
        self.Log_Level = Device_Config.get('Log Level', 1)
        # Change system header
        self.System_Header = Device_Config['System Header']

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
        self.Log(0, 'MQTT', 'Using hostname: ' + self.Hostname + "-" + Post_Hostname)
        # Stores messages so we can act on them in MQTT Loop
        ## List containing Topic and payload
        ## [[<Topic>, <Payload>]]
        self.MQTT_Incomming_Queue = []
        # Create MQTT Client
        self.MQTT_Client = self.MQTT.MQTTClient(
            self.Hostname + "-" + Post_Hostname,
            self.Server,
            int(Device_Config.get('MQTT Port', 1883)),
            Device_Config.get('MQTT Username', None),
            Device_Config.get('MQTT Password', None)
        )
        # Set last will
        self.MQTT_Client.set_last_will(self.System_Header + "/" + self.Hostname + "/Log/Will", "Disconnected")
        
        # try to connect to mqtt
        self.MQTT_Connect()

        # Device_Config is no loger needed so will delete it to free up space
        del Device_Config

        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # Variable for Pin Monitor
        # Remember to pass base aka self
        import pinmonitor
        self.Pin_Monitor = pinmonitor.Init(self)

        # Loop over config names in /conf and import matching modules
        ## Get config names
        Config_List = uos.listdir('/conf')
        # Remove device.json since we dont want to use that again
        Config_List.remove('device.json')
        Config_List.remove('network.json')

        ## Loop over names in config
        for Name in Config_List:

            # Strip .json from name
            Name = Name.replace('.json', '')

            # DHT has to be in capital or else it will try to load the micropython module called dht
            if Name == 'dht':
                Name = 'DHT'

            # Import the config
            Config = dConfig.Load(Name)
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
                            # Remove config file
                            uos.remove("/lib/" + Name + '.mpy')
                            # Log removal of config file
                            self.Log(1, "System", "Removed config file and module for: " + Name)
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
        
        # Remove dconfig again since we are done with it
        del dConfig

        # Boot done message
        self.Log(0, 'System', 'Dobby - Initialization compleate - Free memory: ' + str(gc.mem_free()))


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
        Topic = self.System_Header + "/" + self.Hostname + "/Log/" + Level_String + "/" + Topic

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
        Return_String = Return_String + self.Hostname
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
        # Check if we got a Group message
        if '/Group/' in Topic:
            # Strip anything before 'Group/'
            # The + 1 is to remove the '/' before Group
            Topic = Topic[Topic.index('/Group/') + 1:]

            # Now the message will be handed off at like any other message to a sub module
            # the submodule will then trigger the configured devices with the payload from the message

        # Normal message
        else:
            # Now strip everything up to and including hostname + /
            # The + 1 is for the / after hostname
            Topic = Topic[Topic.index(self.Hostname) + len(self.Hostname) + 1:]

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

            # If topic is not in self.MQTT_Subscribe_To add it
            if Topic not in self.MQTT_Subscribe_To:
                self.MQTT_Subscribe_To.append(str(Topic))

            # Log event
            self.Log(0, 'MQTT', 'Subscribing to topic: ' + Topic)
            # Subscribe
            self.MQTT_Client.subscribe(Topic)

        # Not Connected
        else:
            if Topic not in self.MQTT_Subscribe_To:
                # If topic is not in self.MQTT_Subscribe_To add it
                if Topic not in self.MQTT_Subscribe_To:
                    self.MQTT_Subscribe_To.append(str(Topic))
                # Log evnet
                self.Log(0, 'MQTT', 'Not connected added Topic: ' + str(Topic) + ' to Subscription list')


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Handle_Incomming(self, Message):
        # Referance variables
        Topic = str(Message[0])
        Payload = str(Message[1])

        # Print to serial
        print('<- ' + self.System_Header + "/" + self.Hostname + "/" + str(Topic) + " - " + str(Payload))

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
        # except DHT
        if Module_Name == 'dht':
            Module_Name = Module_Name.upper()

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
        except TypeError as e:
            # Log event
            self.Log(3, "System", "Module: " + str(Module_Name) + " Error: " + str(e))
        # KeyError indicates unknown module or Peripheral_Name
        except KeyError as e:
            if Module_Name in str(e):
                self.Log(3, "System", "Unknown Module name: " + str(Module_Name) + " Error: " + str(e))
            elif Name in str(e):
                self.Log(3, "System", "Unknown Peripheral name: " + str(Name) + " Error: " + str(e))
            else:
                self.Log(3, "System", "Module: " + str(Module_Name) + " Error: " + str(e))
                

    # -------------------------------------------------------------------------------------------------------
    def MQTT_Loop(self):

        # Incomming
        # Check is queue is empthy
        if len(self.MQTT_Incomming_Queue) != 0:
            # Remove and pass the first message in the queue to MQTT_Handle_Incomming
            self.MQTT_Handle_Incomming(self.MQTT_Incomming_Queue.pop(0))

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
            try:
                # remember to add one to range to get 0-5
                if int(Payload[10:]) in range(6):
                    self.Log_Level = int(Payload[10:])
            except:
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
        # source - https://forum.micropython.org/viewtopic.php?t=3499
        elif Payload.lower() == 'free memory':
            # calc free memory
            gc.collect()
            F = gc.mem_free()
            A = gc.mem_alloc()
            T = F+A
            P = '{0:.2f}%'.format(F/T*100)
            # Log free memory
            self.Log(1, "Commands", "Free memory: " + str(('Total:{0} Free:{1} ({2})'.format(T,F,P))))
            return

        # ++++++++++++++++++++++++++++++++++++++++ File system ++++++++++++++++++++++++++++++++++++++++
        # Free space
        # source - https://forum.micropython.org/viewtopic.php?t=3499
        elif Payload.lower() == 'free space':
            # calc free space
            s = uos.statvfs('//')
            # Log free space
            self.Log(1, "Commands", "Free space: " + str(('{0} MB'.format((s[0]*s[3])/1048576))))
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
    # This should be used to write messsages both to serial and mqtt
    def Loop(self):
        # Log event
        self.Log(0, "System", "Starting loop")
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