#!/usr/bin/python

import machine

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Pressure", "Initializing")

        # Loop over Peripherals in config
        for Name, Pressure_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Pressure to the Pressure dict
            self.Peripherals[Name] = self.Pressure(self.Dobby, Name, Pressure_Config)
            # Check if the Pressure is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Pressure detected disabling it
                self.Dobby.Log(2, "Pressure/" + Name, "Issue during setup, disabling the Pressure")
                # Delete the Pressure from Peripherals
                del self.Peripherals[Name]
            # Pressure ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Pressure", End="+"))
        
        # Log event
        self.Dobby.Log(0, "Pressure", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    class Pressure:

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

            # Check if we got the needed config
            for Entry in ['Pin', 'Max_Pressure']:
                if Config.get(Entry, None) is None:
                    self.Dobby.Log(2, "Pressure/" + self.Name, "Missing config: " + Entry + " - Unable to initialize")
                    return

            # ADC Max value is 1023 on esp8266 and 4095 on esp32
            if self.Dobby.ESP_Type == 32:
                self.ADC_Max = 4095
            else:
                self.ADC_Max = 1023

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(Config['Pin'], "Pressure-" + self.Name, Analog=True)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure Pressure
                self.Dobby.Log(2, "Pressure/" + Name, "Pin in use - Unable to initialize")
                # return so we dont set State to true aka mark the Pressure as configured
                return

            # Make a pin object
            self.Pin = machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin']))
            # Create the ADC object
            self.Pin = machine.ADC(self.Pin)

            # Save Max_Pressure
            self.Max_Pressure = Config['Max_Pressure']

            # Get R3 if present, default to 0
            self.R3 = Config.get("R3", 0)

            # Calc max voltage used to convert 1024 to volt
            # The 320 is R1 aka 100k and R2 aka 220k
            self.Max_Bridge_Volt = (self.R3 + 320000) * 0.00001

            # Min_Volt will move min aka 0 to Min_Volt fx 0.5
            # default to 0
            self.Min_Volt = Config.get('Min_Volt', 0)
            
            # Same for max volt default to self.Max_Bridge_Volt
            self.Max_Volt = Config.get('Max_Volt', self.Max_Bridge_Volt)
            # If min volt is set will adjust max volt 
            # by subtracting min volt since we subtract it from voltage on reading 
            # to get pressure scale to start at 0 and go to max volt
            if self.Min_Volt != 0:
                self.Max_Volt = self.Max_Volt - self.Min_Volt

            self.Round_To = Config.get('Round', None)
            # Check if we need to round return value
            if self.Round_To != None:
                self.Dobby.Log(0, "Pressure/" + self.Name, "Rounding to didgets: " + str(self.Round_To))
                # Convert self.Round_To to int
                self.Round_To = int(self.Round_To)
                       
            Publish = Config.get('Publish' , None)
            # Check if we need to create a Publish timer
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
                    self.Dobby.Log(0, "Pressure/" + self.Name + "/Publish", Key + " interval set to: " + Value)


            # //////////////////////////////////////// MQTT Message \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            self.MQTT_Message = {}
            if Config.get("Message", None) != None:
                # For loop over entries in Messages if any
                for Entry in Config['Message']:
                    # Bool value to check if either topic or payload failed
                    Failure = False
                    # Check if we got both Topic and Payload
                    for Check in ['Topic', 'Payload']:
                        if Failure == True:
                            continue
                        # Missing topic or payload
                        if Config['Message'][Entry].get(Check, None) == None:
                            # Log event
                            self.Dobby.Log(2, "Pressure/" + self.Name, "Trigger Message " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.MQTT_Message[Entry.lower()] = Config['Message'][Entry]
                        # log event
                        self.Dobby.Log(0, "Pressure/" + self.Name, "Trigger Message " + Entry + " set to Topic: '" + self.MQTT_Message[Entry.lower()]['Topic'] + "' Payload: '" + self.MQTT_Message[Entry.lower()]['Payload'] + "'")


            # //////////////////////////////////////// Push \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            self.Push = {}
            if Config.get("Push", None) != None:
                # For loop over entries in Pushs if any
                for Entry in Config['Push']:
                    # Bool value to check if either topic or Message failed
                    Failure = False
                    # Check if we got both Topic and Message
                    for Check in ['id', 'Message']:
                        if Failure == True:
                            continue
                        # Missing id or Message
                        if Config['Push'][Entry].get(Check, None) == None:
                            # Log event
                            self.Dobby.Log(2, "Pressure/" + self.Name, "Trigger Push " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' Push")
                            # break since one is missing and we need both id and Message
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.Push[Entry.lower()] = Config['Push'][Entry]
                        # log event
                        self.Dobby.Log(0, "Pressure/" + self.Name, "Trigger Push " + Entry + " set to id: '" + self.Push[Entry.lower()]['id'] + "' Message: '" + self.Push[Entry.lower()]['Message'] + "'")


            # Creat the Read Timer, to refresh values from all the sensors on a spisific pin
            # so we dont have to wait when we request a value or have to publish
            # Check if the dobby.timer module is loaded
            self.Dobby.Timer_Init()
            # Get rate to default to 1.5s if present
            # Max rate for the A0 on esp8266 is 0.002 
            # but lets set max to 0.2 so other things can get cpu time as well
            Rate = self.Dobby.Sys_Modules['Timer'].Time_To_ms(
                Config.get(
                    'Rate',
                    '0.2s'
                ),
                Min_Value='0.2s'
            )
            
            # Log event
            self.Dobby.Log(0, "Pressure/" + Config['Pin'] + "/ReadTimer", "Interval set to: " + str(Rate) + " ms")

            # Add a timer
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # Disable logging since we trigger this timer a lot
            try:
                self.Timer = self.Dobby.Sys_Modules['Timer'].Add(
                    "Pressure-" + self.Name + "-Read",
                    Rate,
                    self.Read,
                    Logging=False
                )
            # Unable to create the timer, remove the entire pin and all sensors attached to it from the config
            except self.Dobby.Sys_Modules['Timer'].Timer_Error as e:
                # log error
                self.Dobby.Log(3, "Pressure/" + Config['Pin'] + "/ReadTimer", "Error initializing MQTT Messages and Publish disabeled. Error: " + str(e))
                # Now we need to clear self.MQTT_Message disable it
                self.MQTT_Message = {}
            else:
                # Start the timer since we loaded it ok
                self.Timer.Start()

            # Vars to hold values read from pin
            self.Volt = -100
            self._Pressure = -100

            # Mark Pressure Sensor as ok
            self.OK = True


            # Do first read os we have values avalible just after boot
            self.Read()


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            
            # Publish state under bla bla bla /Pressure/<Name>/State
            if Command == "?":
                # Publish state should handle it all
                self.Publish_State()
                    
            else:
                self.Dobby.Log(2, 'Pressure/' + self.Name, "Unknown command: " + str(Command))


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
            self.Publish_Timer[Triggered_By].Start()        
        

        # -------------------------------------------------------------------------------------------------------
        def Publish_State(self):
            # Publishes _Pressure to Pressure/<Name>/State
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic("Pressure", End=self.Name, State=True),
                    self._Pressure
                ]
            )



        # -------------------------------------------------------------------------------------------------------
        def Read(self):

            # Read raw pin value
            Raw = self.Pin.read()

            # Convert to volts
            self.Volt = Raw * (self.Max_Bridge_Volt / self.ADC_Max)

            # if self.Min_Volt != 0 then we need to subtract it from self.Max_Volt and self.Volt
            # to get the convertion to match
            # After this min volt is 0 in the followin math
            if self.Min_Volt != 0:
                self.Volt = self.Volt - self.Min_Volt
                # Now we need to check if self.Volt went below 0 if so set to 0
                if self.Volt < 0:
                    self.Volt = 0

            # set v to max volt if above max volt            
            elif self.Volt > self.Max_Volt:
                self.Volt = self.Max_Volt


            # convert volt to pressure
            # self._Pressure = 3.4 * (6.89476 / 4.5)
            self._Pressure = self.Volt * (self.Max_Pressure / self.Max_Volt)

            # MQTT_Message
            for Key in self.MQTT_Message:
                # We need to skip the 'Active' key
                if Key == 'Active':
                    continue
                # Run action check to see if we need to continue
                # remember to pass key since will check it against self._Pressure
                if self.Action_Check(Key, self.MQTT_Message) == True:
                    try:
                        self.Dobby.Log_Peripheral(self.MQTT_Message[Key])
                    except KeyError:
                        pass

            # Push
            for Key in self.Push:
                # We need to skip the 'Active' key
                if Key == 'Active':
                    continue
                # Run action check to see if we need to continue
                # remember to pass key since will check it against self._Pressure
                if self.Action_Check(Key, self.Push) == True:
                    try:
                        self.Dobby.Push_Send(
                            self.Push[Key]['id'],
                            "Pressure",
                            self.Push[Key]['Message']
                        )
                    except KeyError:
                        pass
            
            # At the very end round the number if set we want all the didgets when running the for loops above
            if self.Round_To != None:
                self._Pressure = round(self._Pressure, self.Round_To)

            # Start the timer
            self.Timer.Start()


        # -------------------------------------------------------------------------------------------------------
        def Action_Check(self, Key, Dict):
            # Key should contain "<n1>-<n2>"
            # n1 = Low Value 
            # n2 = High Value
            # Action_Check will then check if self._Pressure is between n1 and n2
            # Split the key at - to get n1 and n2
            Key_Split = Key.split("-")

            if float(Key_Split[0]) <= self._Pressure <= float(Key_Split[1]):
                # Not we need to check if we already triggered this action
                # this is done by checking if Dict['Active'] == Key
                
                if Dict[Key].get('Active', "") != Key:
                    # Set current Key as active
                    Dict[Key]['Active'] = Key
                    # Return true to indicate we need to take action
                    return True

            else:
                # Since no key is active will clear active
                Dict[Key]['Active'] = ""

            # If we didnt rethrn True above return false so indicate no action needed 
            return False