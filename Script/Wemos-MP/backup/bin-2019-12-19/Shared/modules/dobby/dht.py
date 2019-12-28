import dht
import machine
import ujson

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "DHT", "Initializing")

        # Loop over Peripherals in config
        for Name, DHT_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the DHT to the DHT dict
            self.Peripherals[Name] = self.DHT(self.Dobby, Name, DHT_Config)
            # Check if the DHT is ok
            if self.Peripherals[Name].OK is False:
                # Issue with DHT detected disabling it
                self.Dobby.Log(2, "DHT/" + Name, "Issue during setup, disabling the DHT")
                # Delete the DHT from Peripherals
                del self.Peripherals[Name]
            # DHT ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("DHT", End="+"))
        
        # Log event
        self.Dobby.Log(0, "DHT", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    class DHT:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # OK
            ## False = lError/Unconfigured
            ## True = Running
            self.OK = False

            # Name - This will be added to the end of the topic
            self.Name = str(Name)

            # Var to hold the DHT object
            self.Sensor = None

            # Check if we got the needed config
            for Entry in ['Pin', 'Type']:
                if Config.get(Entry, None) is None:
                    self.Dobby.Log(2, "DHT/" + self.Name, "Missing config: " + Entry + " - Unable to initialize")
                    return

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(Config['Pin'], "DHT-" + self.Name)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure DHT
                self.Dobby.Log(2, "DHT/" + Name, "Pin in use - Unable to initialize")
                # return so we dont set State to true aka mark the DHT as configured
                return

            # Create DHT sensor object
            if Config["Type"] is 11:
                self.Sensor = dht.DHT11(machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])))
            elif Config["Type"] is 22:
                self.Sensor = dht.DHT22(machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])))
            # Unknown type
            else:
                self.Dobby.Log(2, "DHT/" + self.Name, "Unknown sensor type: " + Config["Type"] + "- Unable to initialize sensor")
                return
            
            # Error counter
            ## every time a read fails the error counter will get ++
            ## when = 10 the sensor will be disabeled
            ## it will be reset after a sucessfull read 
            self.Error_Count = 0
           
            self.Round_To = Config.get('Round', None)
            # Check if we need to round return value
            if self.Round_To != None:
                self.Dobby.Log(0, "DHT/" + self.Name, "Rounding to didgets: " + str(self.Round_To))
                # Convert self.Round_To to int
                self.Round_To = int(self.Round_To)
                       
            Publish = Config.get('Publish' , None)
            # Check if we need to create a Publish timer
            # self.Sensors[self.Name]['Publish'] contains the RunningVarage object if enabled
            if Publish is not None:
                # Create a dict to hold the timers
                self.Publish_Timer = {}
                # Run for loop over entries in Publish
                for Key, Value in Publish.items():
                    # Check if the dobby.timer module is loaded
                    self.Dobby.Timer_Init()
                    # Convert text time string aka 10s to ms int
                    Rate = self.Dobby.Sys_Modules['Timer'].Time_To_ms(Value)
                    # Add a timer
                    # 1 = Referance Name
                    # 2 = Timeout
                    # 3 = Callback
                    # 4 = Argument
                    self.Publish_Timer[Key] = self.Dobby.Sys_Modules['Timer'].Add(
                        self.Name + "-Publish-" + Key,
                        Rate,
                        self._Publish,
                        Key
                    )

                    # Start the timer
                    self.Publish_Timer[Key].Start()
                    
                    # Log event
                    self.Dobby.Log(0, "DHT/" + self.Name + "/Publish", Key + " interval set to: " + Value)

                # # State in Publish config
                # if Publish.get('State' , None) != None:

                # # json in Publish config
                # if Publish.get('State' , None) != None:
                


            # Publish
            # State
            # json

            # Mark DHT Sensor as ok
            ## if its not it will get disabled after 10 failed reads
            self.OK = True

            # Do first read os we have values avalible just after boot
            self.Read()
            



        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            
            # Publish state under bla bla bla /DHT/<Name>/Humidity and /DHT/<Name>/Temperature
            if Command == "?":
                # Publish state should handle it all
                self.Publish_State()
                    
            # Return current state as json
            elif Command == "json":
                # Publish_json should take care if it all
                self.Publish_json()

            else:
                self.Dobby.Log(2, 'DHT/' + self.Name, "Unknown command: " + str(Command))


        # -------------------------------------------------------------------------------------------------------
        def Read(self):
            # tries to read value from sensor
            ## False = Failed
            ## True = OK Value stored in 
            ### self.Sensor.humidity()
            ### self.Sensor.temperature()

            if self.OK == False:
                return

            # try to read value    
            try:
                self.Sensor.measure()
            # Unable to read from the sensor
            except OSError:
                # Add to error count
                self.Error_Count = self.Error_Count + 1

                # Check if we reached max error count
                if self.Error_Count > 10:
                    self.Dobby.Log(2, "DHT/" + str(self.Name), "Max error count reached disabling sensor - Error count: " + str(self.Error_Count))
                    # disable the sensor
                    self.OK = False

                # return when we get an error
                return False

            # Reset error counter, because we got a good reading
            self.Error_Count = 0

            # No reason for other actions since values is now avalible in 
            # self.Sensor.humidity()
            # self.Sensor.temperature()
            

        # -------------------------------------------------------------------------------------------------------
        def Get_json(self, Reset=False):

            # Read value sine not refreshed by loop
            if self.Read() is False:
                # Error logging already dont by read
                # Return false sence read failed
                return False
            # Check if we need to round
            ## Rounding
            elif self.Round_To is not None:
                # build json
                Return_dict = {
                    'Humidity': round(self.Sensor.humidity(), self.Round_To),
                    'Temperature': round(self.Sensor.temperature(), self.Round_To)
                }

            ## Not rounding
            else:
                # build json
                Return_dict = {
                    'Humidity': self.Sensor.humidity(),
                    'Temperature': self.Sensor.temperature()
                }
                
            return ujson.dumps(Return_dict)
            

        # -------------------------------------------------------------------------------------------------------
        def _Publish(self, Triggered_By):
            # Check who Triggered us
            if Triggered_By == "json":
                # Trigger callback
                self.Publish_json()
                
            elif Triggered_By == "State":
                # Trigger callback
                self.Publish_State()
                
            # Restat timer
            if self.OK == True:
                self.Publish_Timer[Triggered_By].Start()


        # -------------------------------------------------------------------------------------------------------
        def Publish_json(self):
            # Publish json to DHT/<Name>/json/State
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic("DHT", End=self.Name + '/json', State=True),
                    self.Get_json()
                ]
            )

        # -------------------------------------------------------------------------------------------------------
        def Publish_State(self):
            # Publishes Humidity Temperature to
            # DHT/<Name>/Humidity/State
            # DHT/<Name>/Temperature/State

            Publish_dict = {}

            # Error logging done by read
            if self.Read() == False:
                return
            # Humidity
            Publish_dict['Humidity'] = self.Sensor.humidity()
            # Temperature
            Publish_dict['Temperature'] = self.Sensor.temperature()

            # Loop over entries in Publish_dict
            for Key, Value in Publish_dict.items():
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Peripherals_Topic("DHT", End=self.Name + '/' + Key, State=True),
                        Value
                    ]
                )