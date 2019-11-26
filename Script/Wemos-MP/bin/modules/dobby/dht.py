import dht
import machine
import ujson

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured DHTs
        self.DHTs = {}
        # Log Event
        self.Dobby.Log(1, "DHT", "Initializing")

        # Loop over DHTs in config
        for Name, DHT_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the DHT to the DHT dict
            self.DHTs[Name] = self.DHT(self.Dobby, Name, DHT_Config)
            # Check if the DHT is ok
            if self.DHTs[Name].OK is False:
                # Issue with DHT detected disabling it
                self.Dobby.Log(2, "DHT/" + Name, "Issue during setup, disabling the DHT")
            # DHT ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Config['System_Header'] + "/DHT/" + self.Dobby.Config['Hostname'])
        
        # Log event
        self.Dobby.Log(0, "DHT", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    # Publish readings is requested to do so - Meant to be placed in dobbylib.On_Message()
    def On_Message(self, Topic, Payload):
        # Check if we need to take action based on topic
        if Topic != self.Dobby.Config['System_Header'] + "/DHT/" + self.Dobby.Config['Hostname']:
            return

        # Check if we got both a name and a command
        if len(Payload.split()) < 2:
            self.Dobby.Log(1, 'DHT', "Unknown DHT command: " + str(Payload))
            return

        # Get DHT name from payload
        Name = str(Payload.split(" ")[0])
        
        # Check if DHT is configured
        ## DHT configured
        if Name not in self.DHTs:
            # Log event
            self.Dobby.Log(1, 'DHT', "Unknown DHT: " + Name)
            return
        
        # Pass to DHT
        # Split payload to get command
        self.DHTs[Name].On_Message(str(Payload.split(" ")[1]))


    # -------------------------------------------------------------------------------------------------------
    class DHT:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # OK
            ## False = Error/Unconfigured
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
                       
            # Average
            ## Can be set via config
            # None = Returns last reading when asked for value
            # <int > 10> = Returns an rolling average over the last <int> reading
            ## Also provides Min and Max readings
            ## Min and Max is reset when values is requested via DHT_Sensor.read()
            self.Average = Config.get('Average' , None)
            # Check if we need to create a running average
            # self.Sensors[self.Name]['Average'] contains the RunningVarage object if enabled
            if self.Average is not None:
                # Convert self.Average to int
                self.Average = int(self.Average)
                # Create rate var to hold sensor read interval if average is enabeled
                ## Defaults to 10 sec
                self.Rate = Config.get('Rate', 10)
                # Log event
                ## Refresh rate is only relevant if average is enabeled
                self.Dobby.Log(0, "DHT/" + self.Name, "Refresh rate: " + str(self.Rate))
                self.Dobby.Log(0, "DHT/" + self.Name, "Enabling Running Average of readings: " + str(self.Average))
                # import dobby.runningaverage to enable runnin gaverage
                import dobby.runningaverage
                # Init dobby running average lib for humidity reading
                self.Average_Humidity = dobby.runningaverage.Running_Average(self.Average, self.Round_To)
                # Init dobby running average lib for temperature reading
                self.Average_Temperature = dobby.runningaverage.Running_Average(self.Average, self.Round_To)

            # Do first read os we have values avalible just after boot
            self.Read()
            
            # Mark DHT Sensor as ok
            ## if its not it will get disabled after 10 failed reads
            self.OK = True



        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Payload):
            
            # Return current state
            if Payload == "?":
                # Return current state
                # Build topic with Peripherals_Topic and add name to the end
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Peripherals_Topic("DHT", self.Name),
                        self.Get_json(Reset=True)
                    ],
                )
            
            if Payload.lower() == "read":
                # Read from the sensor and report ok or failed
                if self.Read() is False:
                    self.Dobby.Log(1, 'DHT/' + self.Name, "Read: Failed")
                else:
                    self.Dobby.Log(1, 'DHT/' + self.Name, "Read: OK")


            else:
                self.Dobby.Log(2, 'DHT/' + self.Name, "Unknown command: " + str(Payload))

            print("MARKER")
            print(Payload)



        # -------------------------------------------------------------------------------------------------------
        def Read(self):
            # tries to read value from sensor
            ## False = Failed
            ## True = OK Value stored in 
            ### self.Sensor.humidity()
            ### self.Sensor.temperature()

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
                else:
                    # If average is false log as Warning so it can be seen early
                    if self.Average is None:
                        # Log event
                        Log_Level = 2
                    else:
                        Log_Level = 0
                    # Log event
                    self.Dobby.Log(Log_Level, "DHT/" + str(self.Name), "Unable to read sensor values - Error count: " + str(self.Error_Count))

                # return when we get an error
                return False

            # Reset error counter, because we got a good reading
            self.Error_Count = 0

            if self.Average is not None:
                # Add values to average
                self.Average_Humidity.Add(self.Sensor.humidity())
                self.Average_Temperature.Add(self.Sensor.temperature())
                # return true because we got a good reading
                return True

            # Add values to average
            self.Average_Humidity.Add(self.Sensor.humidity())
            self.Average_Temperature.Add(self.Sensor.temperature())



        # -------------------------------------------------------------------------------------------------------
        def Get_json(self, Reset=False):
            # If average is False we need to read the current valuer before building the json
            if self.Average is None:

                # Read value sine not refreshed by loop
                if self.Read() is False:
                    # build json
                    Return_dict = {'Error': 'Unable to read values from sensor'}
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
            
            # Average is enabeled so we need to build the json with values from dobby.runningaverage lib
            ## Average_Humidity
            ## Average_Temperature
            else:
                # Rounding already donne by dobby.runningaverage
                # build return dict
                json_dict = {
                    'Humidity': self.Average_Humidity.Get_dict(),
                    'Temperature': self.Average_Temperature.Get_dict()
                }
                # reset average min max if requested
                if Reset is True:
                    self.Average_Humidity.Reset()
                    self.Average_Temperature.Reset()
            
            # return json
            return ujson.dumps(json_dict) 