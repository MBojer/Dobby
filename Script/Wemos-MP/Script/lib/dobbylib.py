# Library for dobby on wemos d1 mini using micropython

import ujson
import sys
import os
import network
import gc
from umqtt.robust import MQTTClient
import dobbyconfigload
import machine

#Version = 300000
## First didget = Software type 1-Production 2-Beta 3-Alpha
## Secound and third didget = Major version number
## Fourth to sixth = Minor version number

# -------------------------------------------------------------------------------------------------------
class Dobby:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self):
        
        # Needed Variables
        ## Dict holding all configs
        ### Fill with config from device.json if it failes self.Config will = False
        self.Config = dobbyconfigload.Config_Load("/conf/device.json")
        ## Log Queue
        self.Log_Queue = list()
        ## Variable for Pin Monitor
        self.Pin_Monitor = self.Dobby_Pin_Monitor(self)
 
        # MQTT Connection status
        self.MQTT_State = 'init'
        self.MQTT_Subscribe_To = [self.Config['System_Header'] + "/Commands/" + self.Config['Hostname']]

        # Read local config to variables
        if self.Config is False:
            print()
            print()
            print()
            print("   device.json not found unable to start entering Command Line Interface")
            print()
            print()
            print()
            # Start CLI
            import dobbycli
            dobbycli.CLI()

        # Init message
        self.Log(1, 'System', 'Initializing Dobby Lib')


        # ++++++++++++++++++++++++++++++++++++++++ WiFi ++++++++++++++++++++++++++++++++++++++++
        # FIX - Handle wifi not connnected
        # Setup WiFi
        ## Log event
        self.Log(1, 'System', 'Connecting to WiFi SSID: ' + self.Config['WiFi_SSID'])
        ## Connect
        self.wlan0 = network.WLAN(network.STA_IF)
        self.wlan0.active(True)
        self.wlan0.connect(self.Config['WiFi_SSID'], self.Config['WiFi_Password'])
        # Log ip
        self.Log(0, 'WiFi', 'Got IP: ' + str(self.wlan0.ifconfig()[0]))


        # ++++++++++++++++++++++++++++++++++++++++ MQTT ++++++++++++++++++++++++++++++++++++++++
        # Remember to add something raondom after the hostname so the borker see a new connecton
        # Check if we got a user and pass for mqtt
        # Generate Unique Post Hostname
        Post_Hostname = str(os.urandom(1)[0] %1000)
        # Log event
        self.Log(0, 'MQTT', 'Using hostname: ' + self.Config['Hostname'] + "-" + Post_Hostname)

        ## No username or password
        if self.Config.get('MQTT_Username', None) is None or self.Config.get('MQTT_Password', None) is None:
            self.MQTT_Client = MQTTClient(self.Config['Hostname'] + "-" + Post_Hostname, self.Config['MQTT_Broker'])
        ## we got a username or password
        else:
            self.MQTT_Client = MQTTClient(self.Config['Hostname'] + "-" + Post_Hostname, self.Config['MQTT_Broker'], user=self.Config['MQTT_Username'], password=self.Config['MQTT_Password'])
        # Set last will
        ## Set will
        self.MQTT_Client.set_last_will(self.Config['System_Header'] + "/Log/" + self.Config['Hostname'] + "/Will", "Disconnected")
        # try to connect to mqtt
        # FIX - Handle MQTT ERRORS on connect
        try:
            self.MQTT_Client.connect()
            self.MQTT_State = 'Connected'
            # Log event
            self.Log(1, 'MQTT', 'Connected to MQTT Broker: ' + self.Config['MQTT_Broker'])
        except OSError as e:
            self.MQTT_Error_Handler(e)

        # if we connected to mqtt empyth the log checks the connection state
        self.Log_Queue_Empyhy()

        # Register on mqtt message callback
        self.MQTT_Client.set_callback(self.MQTT_On_Message)

        # Subscribe to topics
        for Topic in self.MQTT_Subscribe_To:
            # Log event
            self.Log(0, 'MQTT', 'Subscribing to topic: ' + Topic)
            # Subscribe
            self.MQTT_Client.subscribe(Topic)


        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++ Setup peripherals ++++++++++++++++++++++++++++++++++++++++
        # Var to hold loaded configs from peripherals
        # ++++++++++++++++++++++++++++++++++++++++ DHT ++++++++++++++++++++++++++++++++++++++++
        # Load config is False if no config is found
        self.DHT = dobbyconfigload.Config_Load('/conf/dht.json', Print=False)
        # Config exists
        if self.DHT is not False:
            # Try to import dobbydht
            try:
                import dobbydht
            except (SyntaxError, ImportError, MemoryError) as e:
                # Log event
                self.Log(3, "DHT", "Unable to load Dobby DHT Lib - Error: " + str(e))
                # Set self.DHT to none to indicate DHT isent configured
                self.DHT = False
            # Lib import ok setup devices
            else:
                # Pass config and get dht object
                # Remember to pass Dobby aka self so we can log in DHT and use dobby variables
                self.DHT = dobbydht.DHT(self, self.DHT)
        else:
            self.Log(0, 'DHT', 'No config found')


        # ++++++++++++++++++++++++++++++++++++++++ Button ++++++++++++++++++++++++++++++++++++++++
        # Load config is False if no config is found
        self.Button = dobbyconfigload.Config_Load('/conf/button.json', Print=False)

        # Load config is False if no config is found
        if self.Button is not False:
            # Try to import dobbydutton
            try:
                import dobbybutton
            except (SyntaxError, ImportError, MemoryError) as e:
                # Log event
                self.Log(3, "Button", "Unable to load Dobby Button Lib - Error: " + str(e))
                # Set self.Button to none to indicate Button isent configured
                self.Button = False
            # Lib import ok setup devices
            else:
                # Pass config and get Button object
                # Remember to pass Dobby aka self so we can log in Button and use dobby variables
                self.Button = dobbybutton.Dobby_Button(self, self.Button)
        else:
            self.Log(0, 'Button', 'No config found')














        # Boot done message
        self.Log(0, 'System', 'Dobby Lib initialization complete - Free memory: ' + str(gc.mem_free()))

    # -------------------------------------------------------------------------------------------------------
    class Dobby_Pin_Monitor:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby):
            # Create needed vars
            ## Referance to dobby
            self.Dobby = Dobby
            ## Dict holding reserved pins
            ### Format <Wemos Pin Name>: {'Used by': "DHT"} 
            self.Pins = {}

    #     def Is_Free(self, Pin):
    #         # Check if pin is valid
    #         if self.Valid_Pin(Pin) is False:
    #             return
    #         # Check if pin is free
    #         if 
    #         self.Dobby.Log(0, "PinMonitor", "Valid Wemos Pin Name: " + Pin)

    #     def Reserve(self, Pin):

    #     def To_Wemos_Pin(self, Pin):
    #         # Check if already wemos pin
    #         if Pin.lower() in ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "a0"]:
    #             return Pin
            
    #         for Pin_Name, GPIO_Pin_Number in {
    #             16 = "D0"
    #             5 = "D1"
    #             4 = "D2"
    #             0 = "D3"
    #             2 = "D4"
    #             14 = "D5"
    #             12 = "D6"
    #             13 = "D7"
    #             15 = "D8"
    #             0 = "A0"

    #         }
            
    #         # Check of pin is valid
    #         if "d0" in Pin:
    #             GPIO_Pin = 16
    #         elif "d1" in Pin:
    #             GPIO_Pin = 5
    #         elif "d2" in Pin:
    #             GPIO_Pin = 4
    #         elif "d3" in Pin:
    #             GPIO_Pin = 0
    #         elif "d4" in Pin:
    #             GPIO_Pin = 2
    #         elif "d5" in Pin:
    #             GPIO_Pin = 14
    #         elif "d6" in Pin:
    #             GPIO_Pin = 12
    #         elif "d7" in Pin:
    #             GPIO_Pin = 13
    #         elif "d8" in Pin:
    #             GPIO_Pin = 15
    #         # Note A0 is pin 0 as well as D3
    #         elif "d0" in Pin:
    #             GPIO_Pin = 0
    #         # if invalid string return false
    #         else:
    #             return False
    #         # else return GPIO string
    #         return machine.Pin(GPIO_Pin)
        
        def To_GPIO_Pin(self, Pin):
            # Check if already valid pin
            if Pin in [0, 2, 4, 5, 12, 13, 14, 15, 16]:
                return Pin
            # Convert wemos pin name string to goip pin int
            # Convert pin name string to lover case
            Pin = Pin.lower()
            # Check of pin is valid
            if "d0" in Pin:
                GPIO_Pin = 16
            elif "d1" in Pin:
                GPIO_Pin = 5
            elif "d2" in Pin:
                GPIO_Pin = 4
            elif "d3" in Pin:
                GPIO_Pin = 0
            elif "d4" in Pin:
                GPIO_Pin = 2
            elif "d5" in Pin:
                GPIO_Pin = 14
            elif "d6" in Pin:
                GPIO_Pin = 12
            elif "d7" in Pin:
                GPIO_Pin = 13
            elif "d8" in Pin:
                GPIO_Pin = 15
            # Note A0 is pin 0 as well as D3
            elif "a0" in Pin:
                GPIO_Pin = 0
            # if invalid string return false
            else:
                return False
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
            self.Dobby.Log(0, "PinMonitor", "Invalid pin: " + str(Pin))
            return False


    # -------------------------------------------------------------------------------------------------------
    def Pin_Monitor_Reserve_Pin(self, Pin):
        # Check if pin string is valid
        GPIO_Pin = self.Wemos_Pin_To_GPIO_Pin(Pin)
        if GPIO_Pin is False:
            # Return false if invalid in string is recived
            return False
        # Check if pin is in use
        ## Pin is free if present Pin_Monitor
        if self.Pin_Monitor.get(GPIO_Pin, None) is None:
            # Reserve pin
            self.Pin_Monitor[GPIO_Pin] = True
            return True
        # Pin is in use
        else:
            return False

    # -------------------------------------------------------------------------------------------------------
    # Converts a Wemos pin string AKA "D#" to a GPIO pin string
    def Wemos_Pin_To_GPIO_Pin(self, Pin):

        # Check of pin is valid
        if "D0" in Pin:
            GPIO_Pin = 16
        elif "D1" in Pin:
            GPIO_Pin = 5
        elif "D2" in Pin:
            GPIO_Pin = 4
        elif "D3" in Pin:
            GPIO_Pin = 0
        elif "D4" in Pin:
            GPIO_Pin = 2
        elif "D5" in Pin:
            GPIO_Pin = 14
        elif "D6" in Pin:
            GPIO_Pin = 12
        elif "D7" in Pin:
            GPIO_Pin = 13
        elif "D8" in Pin:
            GPIO_Pin = 15
        # Note A0 is pin 0 as well as D3
        elif "A0" in Pin:
            GPIO_Pin = 0
        # if invalid string return false
        else:
            return False
        # else return GPIO string
        return machine.Pin(GPIO_Pin)


    # -------------------------------------------------------------------------------------------------------
    def Log_Queue_Empyhy(self):
        # Check if we are connected if not do nothing
        if self.MQTT_State != 'Connected':
            return

        # for loop over Entries in Log_Queue
        for Message in self.Log_Queue:
            # Publish message - 0 = Topic 1 = Payload
            self.MQTT_Client.publish(Message[0], Message[1])

        # Clear the queue
        self.Log_Queue = []

    # -------------------------------------------------------------------------------------------------------
    def MQTT_Commands(self, Topic, Payload):
        # Check if its a message for MQTT_Commands
        if self.Config['System_Header'] + "/Commands/" + self.Config['Hostname'] not in Topic:
            return

        # ++++++++++++++++++++++++++++++++++++++++ Reboot ++++++++++++++++++++++++++++++++++++++++
        # Reboots the device
        elif Payload.lower() == 'reboot':
            # Log event
            self.Log(1, "System", "Rebooting - Triggered from MQTT Commands")
            # Disconnect from MQTT
            self.MQTT_Client.disconnect()
            # reboot
            machine.reset()
            return
        # ++++++++++++++++++++++++++++++++++++++++ Memory ++++++++++++++++++++++++++++++++++++++++
        # Lists free memory - For some odd reason you cant use "free memory" as trigger
        elif Payload.lower() == 'memory':
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
            # Check if we got a json string
            if Payload.find('{') is -1 or Payload.find('}') is -1:
                self.Log(2, 'Commands', "Config: Invalid json config string recived")
                return
            # Get config name
            Config_Name = str(Payload.split(' ')[2])
            # Save config dict to fs
            f = open('/conf/' + Config_Name + ".json", 'w')
            f.write(Payload[Payload.find("{"):Payload.find("}") + 1])
            f.close()
            # Log event
            self.Log(1, 'System', "Config saved: " + str(Config_Name))
            return
        
        else:
            self.Log(1, 'System', "Unknown command: " + Payload)
            return

    
    # -------------------------------------------------------------------------------------------------------
    def MQTT_On_Message(self, topic, msg):
        # Pass message to device or configured perifials
        Topic = topic.decode('utf8')
        Payload = msg.decode('utf8')
        # Print to serial
        print('<- ' + str(Topic) + " - " + str(Payload))
        ## MQTT Commands
        self.MQTT_Commands(Topic, Payload)
        ## DHT
        ### Remember to check if dht is enabeled
        if self.DHT is not False:
            self.DHT.On_Message(Topic, Payload)


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Loop(self):
        # Check if we are connected
        if self.MQTT_State is 'Connected':
            # Check for messages, this triggers the callback
            self.MQTT_Client.check_msg()
            # Empthy Log_Queue
            self.Log_Queue_Empyhy()


    # -------------------------------------------------------------------------------------------------------
    def MQTT_Error_Handler(self, Error):
        # Convert error to string
        Error = str(Error)

        # if str(Error) == '[Errno 104] ECONNRESET' or str(Error) == '[Errno 104] ECONNRESET':
        if 'ECONNRESET' in Error or 'ECONNABORTED' in Error:
            self.MQTT_State = 'Disconnected'
            self.Log(2, 'System', 'Unable to connect to broker')
        else:
            print("ERROR fix this")
            print(Error)
    
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
        if Level < int(self.Config['Log_Level']):
            return

        # Add message to Log Queue
        # It will be published later by the MQTT Loop
        self.Log_Queue.append([Topic, Payload])


    # -------------------------------------------------------------------------------------------------------
    def Log_Peripheral(self, Topic, Payload, Retained=False):
        # Sends payload to the Topic as retained if requested
        # Used for logging from peripherals
        
        # Always print message to serial
        print("-> " + Topic + " - " + Payload)

        # Publish message
        self.MQTT_Client.publish(Topic, Payload, Retained)

        
        
    # -------------------------------------------------------------------------------------------------------
    # This should be used to write messsages both to serial and mqtt
    def Loop(self):
        # handle mqtt
        self.MQTT_Loop()
        # handle Button
        if self.Button is not False:
            self.Button.Loop()
        # handle DHT
        if self.DHT is not False:
            self.DHT.Loop()
