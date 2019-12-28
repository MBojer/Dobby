# #!/usr/bin/python

# import ds18x20
# import onewire
# import machine
# import ujson

# class Init:

#     # -------------------------------------------------------------------------------------------------------
#     def __init__(self, Dobby, DS18B20_Config):
#         # Referance to dobby
#         self.Dobby = Dobby
#         # Var to hold configured Peripherals
#         self.Peripherals = {}
#         # Log Event
#         self.Dobby.Log(1, "DS18B20", "Initializing")

#         # Before we can init the sensor we need to create the pins
#         # we also need to create a timer that can trigger a read and then pass the values to the configured sensors

#         # Check if we got a pin config
#         if DS18B20_Config.get('Pins', None) == None:
#             # Raise a Module_Error so we disable this module since we dont have any configured pins
#             raise self.Dobby.Module_Error("'Pins' not in config, unable to initialize")
        
#         # Holds read timers used to trigger reading and store of values
#         self.Read_Timers = {}
#         # Holds the ds18b20 sensor object
#         self.Sensor_Pins = {}


#         # Now we need to creat a ds18b20 instance for each pin
#         for Pin_Name in DS18B20_Config['Pins']:
#             # Lets reserve the pin
#             try:
#                 self.Dobby.Pin_Monitor.Reserve(Pin_Name, "DS18B20-" + Pin_Name)
#             except self.Dobby.Pin_Monitor.Error as e:
#                 if str(e).endswith("DS18B20-" + Pin_Name) == True:
#                     self.Dobby.Log(0, "DS18B20", "Pin already owned by a DS18B20")
#                 else:
#                     # Pin in use unable to configure DS18B20
#                     self.Dobby.Log(2, "DS18B20/" + Pin_Name, "Pin in use - Unable to initialize")
#                     # Continue since we were unable to resetve the pin
#                     continue
            
#             # Now we need to create a ds18b20 object so we can do a scan and read from the sensors
#             # Will store it in Sensor_Pins
#             self.Sensor_Pins[Pin_Name] = ds18x20.DS18X20(
#                 onewire.OneWire(
#                     machine.Pin(
#                         self.Dobby.Pin_Monitor.To_GPIO_Pin(
#                             Pin_Name
#                         )
#                     )
#                 )
#             )

#             # Creat the Read Timer, to refresh values from all the sensors on a spisific pin
#             # so we dont have to wait when we request a value or have to publish
#             # Check if the dobby.timer module is loaded
#             self.Dobby.Timer_Init()
#             # Get rate to default to 1.5s if present
#             # if rate is less then 1.5 then we need to set the rate to 1.5s 
#             # anything else will generate None value from the sensor
#             Rate = self.Dobby.Sys_Modules['Timer'].Time_To_ms(
#                 DS18B20_Config['Pins'].get(
#                     'Rate',
#                     '1.5s'
#                 ),
#                 Min_Value='1.5s'
#             )
            
#             # Log event
#             self.Dobby.Log(0, "DS18B20/" + Pin_Name + "/ReadTimer", "Interval set to: " + str(Rate) + " ms")

#             # Add a timer
#             # 1 = Referance Name
#             # 2 = Timeout
#             # 3 = Callback
#             # Disable logging since we trigger this timer a lot
#             try:
#                 self.Read_Timers[Pin_Name] = self.Dobby.Sys_Modules['Timer'].Add(
#                     "DS18B20-" + Pin_Name + "-Read",
#                     Rate,
#                     self.Read_Sensor,
#                     Argument=Pin_Name,
#                     Logging=False
#                 )
#             # Unable to create the timer, remove the entire pin and all sensors attached to it from the config
#             except self.Dobby.Sys_Modules['Timer'].Timer_Error as e:
#                 # delete both ds18b20 sensor object, the read timer was not stored so no reason to relete it
#                 del self.Sensor_Pins[Pin_Name]
#                 # continue since this pin failed
#                 continue

#             # Start the timer
#             self.Read_Timers[Pin_Name].Start()
            
        
#         # After configuring the sensors we now need to do a scan and list all connected ids
#         # Check if we got at least one pin
#         if self.Sensor_Pins != {}:
#             # Var to hold a string containing pin number and connected devices
#             Return_String = ""
#             for Pin_Name in self.Sensor_Pins:
#                 # Do a scan
#                 Scan = self.Sensor_Pins[Pin_Name].scan()
                
#                 # Holds the id's we found during the init scan
#                 # during sensor setup will add the matching callback as the value
#                 # The key will be the sensors id as a string
#                 # that way we can loop over ids when reading and use:
#                 # [id_byte] = id in byte array to read spicific sensor
#                 # [Callback] = self.Store_Temperature from the matching sensor
#                 self.ids = {}

#                 # Add id to Return_String
#                 Return_String = Return_String + "'" + Pin_Name + "': "
    
#                 # Add each id to matching pin
#                 for Entry in Scan:
#                     # Convert the id to string
#                     id_str = str(hex(int.from_bytes(Entry, 'little')))
#                     # Creat a key in self.ids
#                     self.ids[id_str] = {}
#                     # Save the id as bytearray so we can use it in self.Pass_Temperature 
#                     self.ids[id_str]['id_byte'] = Entry
#                     # Add id to Return_String
#                     Return_String = Return_String + " '" + id_str + "'"

#                 # list what ids we found so we can spot of we got a new id we have not configured
#                 self.Dobby.Log(0, "DS18B20", "Connected devices:" + Return_String)

#         # Unable to configre any pins
#         # so fail module load
#         else:
#             # Raise error - Error logging done by Main
#             raise self.Dobby.Module_Error("Unable to configure any of the pins in 'Pins'")

#         # Delete Pins from DS18B20_Config so we dont load it as a sensor
#         del DS18B20_Config['Pins']
        
#         # Loop over Peripherals in config
#         for Name, Config in DS18B20_Config.items():
#             # Make sure Name is a string
#             Name = str(Name)
#             # Add the DS18B20 to the DS18B20 dict
#             self.Peripherals[Name] = self.DS18B20(self.Dobby, self, Name, Config)
#             # Check if the DS18B20 is ok
#             if self.Peripherals[Name].OK is False:
#                 # Issue with DS18B20 detected disabling it
#                 self.Dobby.Log(2, "DS18B20/" + Name, "Issue during setup, disabling the DS18B20")
#             else:
#                 # Subscribe to DS18B20 topic if at least one DS18B20 was ok
#                 self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("DS18B20", End="+"))

#         # Log event
#         self.Dobby.Log(0, "DS18B20", "Initialization complete")


#     # -------------------------------------------------------------------------------------------------------
#     def Read_Sensor(self, Pin_Name):

#         # Tells the sensors to read values, now wait 1.5s before getting them from the sensor
#         self.Sensor_Pins[Pin_Name].convert_temp()

#         # restart the timer and change callback to Pass_Temperature
#         self.Read_Timers[Pin_Name].Start(Callback=self.Pass_Temperature)


#     # -------------------------------------------------------------------------------------------------------
#     def Pass_Temperature(self, Pin_Name):
#         # Passes the value from the sensor to matching ds18b20 sensor

#         # self.ids contains:
#         #   key = str value of id
#         #   Value:
#         #       [id_byte] = is as bytearray
#         #       [Callback] = use this [Callback](Reading) to pass temp to sensor

#         for Key in self.ids:
#             # Try to read value from sensor with id self.ids[Key]['id_byte']
#             try:
#                 Reading = self.Sensor_Pins[Pin_Name].read_temp(self.ids[Key]['id_byte'])
#             except Exception as e:
#                 # Pass none to Store_Temperature to indicate error
#                 # Store_Temperature will disabele the sensor if error count max is reached
#                 Reading = None
#             # Pass the reading to the sensor
#             self.ids[Key]['Callback'](Reading)


#         # restart the timer and change callback to Read_Sensor
#         self.Read_Timers[Pin_Name].Start(Callback=self.Read_Sensor)


    
#     # -------------------------------------------------------------------------------------------------------
#     class DS18B20:

#         # -------------------------------------------------------------------------------------------------------
#         def __init__(self, Dobby, DS18B20_Main, Name, Config):

#             # Referance to dobby
#             self.Dobby = Dobby

#             # OK
#             ## False = Error/Unconfigured
#             ## True = Running
#             self.OK = False

#             # Name - This will be added to the end of the topic
#             self.Name = str(Name)
            
#             # Check if we got the needed config
#             for Entry in ['id']:
#                 if Config.get(Entry, None) == None:
#                     self.Dobby.Log(3, "DS18B20/" + self.Name, "Missing config: " + Entry + " - Unable to initialize")
#                     return

#             # Holds the last value read from the sensor
#             # -128 == Havent be read the first time
#             self.Temperature = -128

#             # Set callback in self.ids
#             try:
#                 DS18B20_Main.ids[Config['id']]['Callback'] = self.Store_Temperature
#             # If we get a key error then the sensor was not found aka not connected
#             except KeyError:
#                 # Log event
#                 self.Dobby.Log(3, "DS18B20/" + self.Name, "Sensor not found during scan - Unable to initialize")
#                 # return so we dont mark the sensor as ok
#                 return

#             # Error counter
#             ## every time a read fails the error counter will get ++
#             ## when = 10 the sensor will be disabeled
#             ## it will be reset after a sucessfull read 
#             self.Error_Count = 0


#             # //////////////////////////////////////// MQTT Message \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#             self.MQTT_Message = {}
#             if Config.get("Message", None) != None:
#                 # For loop over entries in Messages if any
#                 for Entry in Config['Message']:
#                     # Bool value to check if either topic or payload failed
#                     Failure = False
#                     # Check if we got both Topic and Payload
#                     for Check in ['Topic', 'Payload']:
#                         if Failure == True:
#                             continue
#                         # Missing topic or payload
#                         if Config['Message'][Entry].get(Check, None) == None:
#                             # Log event
#                             self.Dobby.Log(2, "DS18B20/" + self.Name, "Trigger Message " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
#                             # break since one is missing and we need both topic and payload
#                             Failure = True

#                     # Check if we failed to get the needed settings
#                     if Failure == False:
#                         # Save settings
#                         self.MQTT_Message[Entry.lower()] = Config['Message'][Entry]
#                         # log event
#                         self.Dobby.Log(0, "DS18B20/" + self.Name, "Trigger Message " + Entry + " set to Topic: '" + self.MQTT_Message[Entry.lower()]['Topic'] + "' Payload: '" + self.MQTT_Message[Entry.lower()]['Payload'] + "'")


#             # //////////////////////////////////////// Relay \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#             self.Relay = {}
#             if Config.get("Relay", None) != None:
#                 # For loop over On/Off to check for both messages
#                 for Entry in Config['Relay']:
#                     # Bool value to check if we are missing config
#                     Failure = False
#                     # Check if we got both Topic and Payload
#                     for Check in ['Name', 'State']:
#                         if Failure == True:
#                             continue
#                         # Missing topic or payload
#                         if Config['Relay'][Entry].get(Check, None) == None:
#                             # Log event
#                             self.Dobby.Log(2, "DS18B20/" + self.Name, "Trigger Relay " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
#                             # break since one is missing and we need both topic and payload
#                             Failure = True

#                     # Check if we failed to get the needed settings
#                     if Failure == False:
#                         # Save settings
#                         self.Relay[Entry.lower()] = Config['Relay'][Entry]
#                         # log event
#                         self.Dobby.Log(
#                             0,
#                             "DS18B20/" + self.Name,
#                             Entry + ": Trigger Relay: '" + self.Relay[Entry.lower()]['Name'] + "' State: '" + self.Relay[Entry.lower()]['State'] + "'"
#                             )


#             # //////////////////////////////////////// Publish \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#             Publish = Config.get('Publish' , None)
#             # Check if we need to create a Publish timer
#             # self.Sensors[self.Name]['Publish'] contains the RunningVarage object if enabled
#             if Publish is not None:
#                 # Create a dict to hold the timers
#                 self.Publish_Timer = {}
#                 # Run for loop over entries in Publish
#                 for Key, Value in Publish.items():
#                     # Add a timer
#                     # 1 = Referance Name
#                     # 2 = Timeout
#                     # 3 = Callback
#                     # 4 = Argument
#                     self.Publish_Timer[Key] = self.Dobby.Sys_Modules['Timer'].Add(
#                         self.Name + "-Publish-" + Key,
#                         Value,
#                         self._Publish,
#                         Argument=Key
#                     )

#                     # Start the timer
#                     self.Publish_Timer[Key].Start()
                    
#                     # Log event
#                     self.Dobby.Log(0, "DS18B20/" + self.Name + "/Publish", Key + " interval set to: " + Value)

#             # Mark sensor as ok
#             self.OK = True


#         # -------------------------------------------------------------------------------------------------------
#         def _Publish(self, Triggered_By):
#             # Check who Triggered us
#             if Triggered_By == "json":
#                 # Trigger callback
#                 self.Publish_json()
                
#             elif Triggered_By == "State":
#                 # Trigger callback
#                 self.Publish_State()
                
#             # Restat timer
#             self.Publish_Timer[Triggered_By].Start()        
        
        
#         # -------------------------------------------------------------------------------------------------------
#         def Publish_State(self):
#             # Publishes Temperature to DS18B20/<Name>/Temperature/State
#             self.Dobby.Log_Peripheral(
#                 [
#                     self.Dobby.Peripherals_Topic("DS18B20", End=self.Name + '/Temperature', State=True),
#                     self.Temperature
#                 ]
#             )

        
#         # -------------------------------------------------------------------------------------------------------
#         def Store_Temperature(self, Temperature):
            
#             # Check if Temperature is None, if so we had a read error
#             if Temperature == None:
#                 # Add 1 to error count
#                 self.Error_Count = self.Error_Count + 1
#                 # check if we reached max error count
#                 if self.Error_Count > 10:
#                     # Log event
#                     self.Dobby.Log(2, "DS18B20/" + str(self.Name), "Max error count reached disabling sensor - Error count: " + str(self.Error_Count))
#                     # disable the sensor
#                     self.OK = False
#                 else:
#                     # Log event
#                     self.Dobby.Log(2, "DS18B20/" + str(self.Name), "Unable to read - Error count: " + str(self.Error_Count))
#                 # return so we dont pass none to the code below
#                 return

#             # Reset error counter, because we got a good reading
#             self.Error_Count = 0

#             # Save the Temperature we recived
#             self.Temperature = Temperature

#             # After saving the Temperature lets see if we need to take any achtion
#             # MQTT_Message
#             for Key in self.MQTT_Message:
#                 # Run action check to see if we need to continue
#                 # remember to pass key since will check it against self.Temperature
#                 if self.Action_Check(Key, self.MQTT_Message) == True:
#                     try:
#                         self.Dobby.Log_Peripheral(self.MQTT_Message[Key])
#                     except KeyError:
#                         pass

#             ## Relay
#             for Key in self.Relay:
#                 # We need to skip the 'Active' key
#                 if Key == 'Active':
#                     continue

#                 if self.Action_Check(Key, self.Relay) == True:
#                     # Trigger the local relay with the provided settings
#                     # We need a try here in case on or off is not set
#                     try:
#                         self.Dobby.Modules['relay'].Peripherals[self.Relay[Key]['Name']].Set_State(self.Relay[Key]['State'])
#                     except KeyError as e:
#                         self.Dobby.Log(0, "DS18B20/" + self.Name, "Unable to trigger relay")
#                         continue
                    
#                     self.Dobby.Log(0, "DS18B20/" + self.Name, "Current temperature: " + str(self.Temperature) + " matches action: " + Key + " Triggering Relay: " + self.Relay[Key]['Name'])



#         # -------------------------------------------------------------------------------------------------------
#         def Action_Check(self, Key, Dict):
#             # Key should contain "<n1>-<n2>"
#             # n1 = Low Value 
#             # n2 = High Value
#             # Action_Check will then check if self.Temperature is between n1 and n2
#             # Split the key at - to get n1 and n2
#             Key_Split = Key.split("-")

#             if float(Key_Split[0]) <= self.Temperature <= float(Key_Split[1]):
#                 # Not we need to check if we already triggered this action
#                 # this is done by checking if Dict['Active'] == Key
#                 if Dict[Key].get('Active', "") != Key:
#                     # Set current Key as active
#                     Dict[Key]['Active'] = Key
#                     # Return true to indicate we need to take action
#                     return True

#             # If we didnt rethrn True above return false so indicate no action needed 
#             return False