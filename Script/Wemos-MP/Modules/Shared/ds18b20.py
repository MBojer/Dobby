#!/usr/bin/python

## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300001

import ds18x20
import onewire
import machine
import ujson


class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Shared, DS18B20_Config):
        # Referance to Shared
        self.Shared = Shared
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Shared.Log(1, "DS18B20", "Initializing")

        # Before we can init the sensor we need to create the pins
        # we also need to create a timer that can trigger a read and then pass the values to the configured sensors

        # Check if we got a pin config
        if DS18B20_Config.get('Pins', None) == None:
            # Raise a Error so we disable this module since we dont have any configured pins
            raise self.Shared.Error("'Pins' not in config, unable to initialize")
        
        # Holds read timers used to trigger reading and store of values
        self.Read_Timers = {}
        # Holds the ds18b20 sensor object
        self.Sensor_Pins = {}

        self.Unconfigured = []

        # Now we need to creat a ds18b20 instance for each pin
        for Pin_Name in DS18B20_Config['Pins']:
            # Lets reserve the pin
            try:
                self.Shared.Pin_Monitor.Reserve(Pin_Name, "DS18B20-" + Pin_Name)
            except self.Shared.Pin_Monitor.Error as e:
                if str(e).endswith("DS18B20-" + Pin_Name) == True:
                    self.Shared.Log(0, "DS18B20", "Pin already owned by a DS18B20")
                else:
                    # Pin in use unable to configure DS18B20
                    self.Shared.Log(2, "DS18B20/" + Pin_Name, "Pin in use - Unable to initialize")
                    # Continue since we were unable to resetve the pin
                    continue
            
            
            # Create the dict that will hopd the ds18b20 object and error count
            self.Sensor_Pins[Pin_Name] = {}
            
            # Now we need to create a ds18b20 object so we can do a scan and read from the sensors
            # Will store it in Sensor_Pins under pin name and then Sensor
            self.Sensor_Pins[Pin_Name]['Sensor'] = ds18x20.DS18X20(
                onewire.OneWire(
                    machine.Pin(
                        self.Shared.Pin_Monitor.To_GPIO_Pin(
                            Pin_Name
                        )
                    )
                )
            )
            # Now will create an error counter for that pin
            self.Sensor_Pins[Pin_Name]['Error'] = 0
            
            
            # Creat the Read Timer, to refresh values from all the sensors on a spisific pin
            # so we dont have to wait when we request a value or have to publish
            # Check if the timer module is loaded
            self.Shared.Timer_Init()
            # Get rate to default to 1.5s if present
            # if rate is less then 1.5 then we need to set the rate to 1.5s 
            # anything else will generate None value from the sensor
            Rate = self.Shared.Sys_Modules['timer'].Time_To_ms(
                DS18B20_Config['Pins'].get(
                    'Rate',
                    '1.5s'
                ),
                Min_Value='1.5s'
            )
            
            # Log event
            self.Shared.Log(0, "DS18B20/" + Pin_Name + "/ReadTimer", "Interval set to: " + str(Rate) + " ms")

            # Add a timer
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # Disable logging since we trigger this timer a lot
            try:
                self.Read_Timers[Pin_Name] = self.Shared.Sys_Modules['timer'].Add(
                    "DS18B20-" + Pin_Name + "-Read",
                    Rate,
                    self.Read_Sensor,
                    Argument=Pin_Name,
                    Logging=False
                )
            # Unable to create the timer, remove the entire pin and all sensors attached to it from the config
            except self.Shared.Sys_Modules['timer'].Timer_Error as e:
                # delete both ds18b20 sensor object, the read timer was not stored so no reason to relete it
                del self.Sensor_Pins[Pin_Name]
                # continue since this pin failed
                continue

            # Start the timer
            self.Read_Timers[Pin_Name].Start()
            
        
        # After configuring the sensors we now need to do a scan and list all connected ids
        # Check if we got at least one pin
        if self.Sensor_Pins != {}:
            # Var to hold a string containing pin number and connected devices
            Return_String = ""
            for Pin_Name in self.Sensor_Pins:
                # Do a scan
                Scan = self.Sensor_Pins[Pin_Name]['Sensor'].scan()
                
                # Holds the id's we found during the init scan
                # during sensor setup will add the matching callback as the value
                # The key will be the sensors id as a string
                # that way we can loop over ids when reading and use:
                # [id_byte] = id in byte array to read spicific sensor
                # [Callback] = self.Store_Temperature from the matching sensor
                self.ids = {}

                # Add id to Return_String
                Return_String = Return_String + "'" + Pin_Name + "': "
    
                # Add each id to matching pin
                for Entry in Scan:
                    # Convert the id to string
                    id_str = str(hex(int.from_bytes(Entry, 'little')))
                    # Creat a key in self.ids
                    self.ids[id_str] = {}
                    # Save the id as bytearray so we can use it in self.Pass_Temperature 
                    self.ids[id_str]['id_byte'] = Entry
                    # Add id to Return_String
                    Return_String = Return_String + " '" + id_str + "'"

                # list what ids we found so we can spot of we got a new id we have not configured
                # Log as Info se we can see if we lost one during boot
                self.Shared.Log(1, "DS18B20", "Connected devices: " + Return_String)

        # Unable to configre any pins
        # so fail module load
        else:
            # Raise error - Error logging done by Main
            raise self.Shared.Error("Unable to configure any of the pins in 'Pins'")

        # Delete Pins from DS18B20_Config so we dont load it as a sensor
        del DS18B20_Config['Pins']
        
        # Loop over Peripherals in config
        for Name, Config in DS18B20_Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the DS18B20 to the DS18B20 dict
            self.Peripherals[Name] = self.DS18B20(self.Shared, self, Name, Config)
            # Check if the DS18B20 is ok
            if self.Peripherals[Name].OK is False:
                # Issue with DS18B20 detected disabling it
                self.Shared.Log(2, "DS18B20/" + Name, "Issue during setup, disabling the DS18B20")
            else:
                # Subscribe to DS18B20 topic if at least one DS18B20 was ok
                self.Shared.MQTT_Subscribe(self.Shared.Peripherals_Topic("DS18B20", End="+"))

        # Log event
        self.Shared.Log(0, "DS18B20", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    def Read_Sensor(self, Pin_Name):

        Delete_Sensor = False

        # Tells the sensors to read values, now wait 1.5s before getting them from the sensor
        try:
            self.Sensor_Pins[Pin_Name]['Sensor'].convert_temp()
        except onewire.OneWireError as e:
            Delete_Sensor = str(e)
        except KeyError as e:
            return
        else:
            # Reset error count on sucessfull read
            self.Sensor_Pins[Pin_Name]['Error'] = 0
        
        finally:
            if Delete_Sensor != False:
                # Add to error count
                self.Sensor_Pins[Pin_Name]['Error'] = self.Sensor_Pins[Pin_Name]['Error'] + 1
                # Log event
                self.Shared.Log(0, "DS18B20/" + Pin_Name, "Unable to read pin. Error count: " + str(self.Sensor_Pins[Pin_Name]['Error']))

                # check if we reached max error counter aka 10
                if self.Sensor_Pins[Pin_Name]['Error'] >= 10:
                    # Log event
                    self.Shared.Log(0, "DS18B20/" + Pin_Name, "Disabling pin. Max error count reached")
                    # remove the sensor from self.Sensor_Pins so we stop scanning it
                    del self.Sensor_Pins[Pin_Name]
                    # return here so we dont trigger an KeyError below
                    # return also prevents the timer for starting
                    return


        # restart the timer and change callback to Pass_Temperature
        self.Read_Timers[Pin_Name].Callback = self.Pass_Temperature
        self.Read_Timers[Pin_Name].Start()


    # -------------------------------------------------------------------------------------------------------
    def Pass_Temperature(self, Pin_Name):
        # Passes the value from the sensor to matching ds18b20 sensor

        # self.ids contains:
        #   key = str value of id
        #   Value:
        #       [id_byte] = is as bytearray
        #       [Callback] = use this [Callback](Reading) to pass temp to sensor

        for Key in self.ids:
            # Try to read value from sensor with id self.ids[Key]['id_byte']
            try:
                Reading = self.Sensor_Pins[Pin_Name]['Sensor'].read_temp(self.ids[Key]['id_byte'])
            except Exception as e:
                # Pass none to Store_Temperature to indicate error
                # Store_Temperature will disabele the sensor if error count max is reached
                Reading = None
            # Pass the reading to the sensor
            try:
                self.ids[Key]['Callback'](Reading)
            
            # We if get an keyerror the sensor wasent configures so reports unknown sensor 
            except KeyError:
                # Do nothing if we already marked as unconfigured
                if Key not in self.Unconfigured:
                    pass
                else:    
                    # Log unconfigured sensor
                    self.Shared.Log(2, "DS18B20", "Unconfigured sensor on Pin: " + Pin_Name + " id: " + Key)
                    # Add to self.Unconfigured so we dont send this message again
                    self.Unconfigured.append(Key)

        # restart the timer and change callback to Read_Sensor
        self.Read_Timers[Pin_Name].Callback = self.Read_Sensor
        self.Read_Timers[Pin_Name].Start()



    # -------------------------------------------------------------------------------------------------------
    class DS18B20:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, DS18B20_Main, Name, Config):

            # Referance to dobby
            self.Shared = Dobby

            # OK
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False

            # Name - This will be added to the end of the topic
            self.Name = str(Name)
            
            # Check if we got the needed config
            for Entry in ['id']:
                if Config.get(Entry, None) == None:
                    self.Shared.Log(3, "DS18B20/" + self.Name, "Missing config: " + Entry + " - Unable to initialize")
                    return

            # Holds the last value read from the sensor
            # -128 == Havent be read the first time
            self.Temperature = -128

            # Set callback in self.ids
            try:
                DS18B20_Main.ids[Config['id']]['Callback'] = self.Store_Temperature
            # If we get a key error then the sensor was not found aka not connected
            except KeyError:
                # Log event
                self.Shared.Log(3, "DS18B20/" + self.Name, "Sensor not found during scan - Unable to initialize")
                # return so we dont mark the sensor as ok
                return

            # Error counter
            ## every time a read fails the error counter will get ++
            ## when = 10 the sensor will be disabeled
            ## it will be reset after a sucessfull read 
            self.Error_Count = 0

            # Round
            # Only use when publishing, readings is stored without rounding
            self.Round = Config.get("Round", None)
            # If round is not a int then will default to None
            if type(self.Round) != int:
                # Log event
                self.Shared.Log(1, "DS18B20/" + self.Name, "Rounding disabeled invalid config: " + str(self.Round))
                # Reset round
                self.Round = None
            else:
                # Log event
                self.Shared.Log(0, "DS18B20/" + self.Name, "Rounding to: " + str(self.Round) + " didgets")
            
            
            # //////////////////////////////////////// Indicator \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            self.Indicator = {}
            if Config.get("Indicator", None) != None:
                # List of config entries to check for
                Check_List = ['Name', 'Times', 'On_For', 'Delay', 'Repeat']
                
                # For loop over entries in Indicator if any
                for Entry in Config['Indicator']:
                    # Check config entries
                    try:
                        self.Shared.Config_Check("DS18B20/" + self.Name + "/Indicator/" + str(Entry), Check_List, Config['Indicator'][Entry])
                    # Pass on errors
                    # Error logging done by Config_Check
                    except self.Shared.Error:
                        pass
                    # If all ok save config to variables
                    else:
                        # Save settings
                        self.Indicator[Entry] = Config['Indicator'][Entry]
                        # Create log string
                        Info = 'Trigger Indicator ' + Entry + ' set to'
                        Info = Info + ' Name:' + str(self.Indicator[Entry]['Name'])
                        Info = Info + ' Times:' + str(self.Indicator[Entry]['Times'])
                        Info = Info + ' On_For:' + str(self.Indicator[Entry]['On_For'])
                        Info = Info + ' Delay:' + str(self.Indicator[Entry]['Delay'])
                        Info = Info + ' Repeat:' + str(self.Indicator[Entry]['Repeat'])
                        # log event
                        self.Shared.Log(0, "DS18B20/" + self.Name, Info)

            
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
                            self.Shared.Log(2, "DS18B20/" + self.Name, "Trigger Message " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.MQTT_Message[Entry.lower()] = Config['Message'][Entry]
                        # log event
                        self.Shared.Log(0, "DS18B20/" + self.Name, "Trigger Message " + Entry + " set to Topic: '" + self.MQTT_Message[Entry.lower()]['Topic'] + "' Payload: '" + self.MQTT_Message[Entry.lower()]['Payload'] + "'")


            # //////////////////////////////////////// Relay \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            self.Relay = {}
            if Config.get("Relay", None) != None:
                # For loop over On/Off to check for both messages
                for Entry in Config['Relay']:
                    # Bool value to check if we are missing config
                    Failure = False
                    # Check if we got both Topic and Payload
                    for Check in ['Name', 'State']:
                        if Failure == True:
                            continue
                        # Missing topic or payload
                        if Config['Relay'][Entry].get(Check, None) == None:
                            # Log event
                            self.Shared.Log(2, "DS18B20/" + self.Name, "Trigger Relay " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.Relay[Entry.lower()] = Config['Relay'][Entry]
                        # log event
                        self.Shared.Log(
                            0,
                            "DS18B20/" + self.Name,
                            Entry + ": Trigger Relay: '" + self.Relay[Entry.lower()]['Name'] + "' State: '" + self.Relay[Entry.lower()]['State'] + "'"
                            )


            # //////////////////////////////////////// Publish \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            Publish = Config.get('Publish' , None)
            # Check if we need to create a Publish timer
            if Publish is not None:
                # Create a dict to hold the timers
                self.Publish_Timer = {}
                # Run for loop over entries in Publish
                for Key, Value in Publish.items():
                    # Add a timer
                    # 1 = Referance Name
                    # 2 = Timeout
                    # 3 = Callback
                    # 4 = Argument
                    self.Publish_Timer[Key] = self.Shared.Sys_Modules['timer'].Add(
                        self.Name + "-Publish-" + Key,
                        Value,
                        self._Publish,
                        Argument=Key
                    )

                    # Start the timer
                    self.Publish_Timer[Key].Start()
                    
                    # Log event
                    self.Shared.Log(0, "DS18B20/" + self.Name + "/Publish", Key + " interval set to: " + Value)

            # Mark sensor as ok
            self.OK = True


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            
            # Publish state under bla bla bla /DS18B20/<Name>/Temperature
            if Command == "?":
                # Publish state should handle it all
                self.Publish_State()

            else:
                self.Shared.Log(2, 'DS18B20/' + self.Name, "Unknown command: " + str(Command))



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
            # Check if we need to round
            if self.Round != None:
                Publish_Temp = round(self.Temperature, self.Round)
            else:
                Publish_Temp = self.Temperature
                
            # Publishes Temperature to DS18B20/<Name>/Temperature/State
            self.Shared.Log_Peripheral(
                [
                    self.Shared.Peripherals_Topic("DS18B20", End=self.Name + '/Temperature', State=True),
                    Publish_Temp
                ]
            )

        
        # -------------------------------------------------------------------------------------------------------
        def Store_Temperature(self, Temperature):
            
            # Check if Temperature is None, if so we had a read error
            if Temperature == None:
                # Add 1 to error count
                self.Error_Count = self.Error_Count + 1
                # check if we reached max error count
                if self.Error_Count > 10:
                    # Log event
                    self.Shared.Log(2, "DS18B20/" + str(self.Name), "Max error count reached disabling sensor - Error count: " + str(self.Error_Count))
                    # disable the sensor
                    self.OK = False
                else:
                    # Log event
                    self.Shared.Log(2, "DS18B20/" + str(self.Name), "Unable to read - Error count: " + str(self.Error_Count))
                # return so we dont pass none to the code below
                return

            # Reset error counter, because we got a good reading
            self.Error_Count = 0

            # Save the Temperature we recived
            self.Temperature = Temperature

            # After saving the Temperature lets see if we need to take any achtion
            # Indicator
            for Key in self.Indicator:
                # We need to skip the 'Active' key
                if Key == 'Active':
                    continue
                # Run action check to see if we need to continue
                # remember to pass key since will check it against self.Temperature
                if self.Action_Check(Key, self.Indicator) == True:
                    try:
                        # Need to indicate
                        # Remove old indicator if present
                        self.Shared.Modules['indicator'].Peripherals[self.Indicator[Key]['Name']].Remove("DS18B20/" + self.Name)
                        # Add new indicator
                        self.Shared.Modules['indicator'].Peripherals[self.Indicator[Key]['Name']].Add(
                            "DS18B20/" + self.Name,
                            self.Indicator[Key]['Times'],
                            self.Indicator[Key]['On_For'],
                            self.Indicator[Key]['Delay'],
                            self.Indicator[Key]['Repeat']
                        )
                    except KeyError:
                        pass

            # MQTT_Message
            for Key in self.MQTT_Message:
                # We need to skip the 'Active' key
                if Key == 'Active':
                    continue
                # Run action check to see if we need to continue
                # remember to pass key since will check it against self.Temperature
                if self.Action_Check(Key, self.MQTT_Message) == True:
                    try:
                        self.Shared.Log_Peripheral(self.MQTT_Message[Key])
                    except KeyError:
                        pass

            ## Relay
            for Key in self.Relay:
                # We need to skip the 'Active' key
                if Key == 'Active':
                    continue

                if self.Action_Check(Key, self.Relay) == True:
                    # Trigger the local relay with the provided settings
                    # We need a try here in case on or off is not set
                    try:
                        self.Shared.Modules['relay'].Peripherals[self.Relay[Key]['Name']].Set_State(self.Relay[Key]['State'])
                    except KeyError as e:
                        self.Shared.Log(0, "DS18B20/" + self.Name, "Unable to trigger relay")
                    else:
                        self.Shared.Log(0, "DS18B20/" + self.Name, "Current temperature: " + str(self.Temperature) + " matches action: " + Key + " Triggering Relay: " + self.Relay[Key]['Name'])


        # -------------------------------------------------------------------------------------------------------
        def Action_Check(self, Key, Dict):
            # Key should contain "<n1>-<n2>"
            # n1 = Low Value 
            # n2 = High Value
            # Action_Check will then check if self.Temperature is between n1 and n2
            # Split the key at - to get n1 and n2
            Key_Split = Key.split("-")

            if float(Key_Split[0]) <= self.Temperature <= float(Key_Split[1]):
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