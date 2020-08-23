import machine
import utime
import ujson

## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300007

class Init:

    # -------------------------------------------------------------------------------------------------------
    # Fix - This code can be in main as a for loop and can be removed from all sub modules
    def __init__(self, Dobby, Dimmer_Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Dimmer", "Initializing")
        
        # Loop over Peripherals in config
        for Name, Config in Dimmer_Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Dimmer to the Dimmer dict
            self.Peripherals[Name] = self.Dimmer(self.Dobby, Name, Config)
            # Check if the Dimmer is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Dimmer detected disabling it
                self.Dobby.Log(2, "Dimmer/" + Name, "Issue during setup, disabling the Dimmer")
                # Delete the DHT from Peripherals
                del self.Peripherals[Name]
            # Only subscribe of Peripheral was ok
            else:
                # Subscribe to Dimmer topic if at least one Dimmer was ok
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Dimmer", End=Name))
                # On/Off Topics
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Dimmer", End=Name + "/json"))

            
        self.Dobby.Log(0, "Dimmer", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    class Dimmer:

        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Variable to indicate of the configuration of the Dimmer went ok
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False
            
            # Name - Referance name
            self.Name = str(Name)

            # Check if we got a config dict if no dict we cant configure
            if type(Config) is not dict:
                return
            
            # Log Event
            self.Dobby.Log(0, "Dimmer/" + self.Name, "Initializing")

            # Check if we got the needed config
            for Entry in ['Pin']:
                if Config.get(Entry, None) == None:
                    self.Dobby.Log(2, "Dimmer/" + Name, "Missing config: " + Entry + " - Unable to initialize Dimmer")
                    return

            # Save pin name to self.Pin
            self.Pin = Config['Pin']

            # Reset the pin
            try:
                self.Dobby.Pin_Monitor.Reserve(self.Pin, "Dimmer-" + self.Name)
            except self.Dobby.Pin_Monitor.Error:
                # Error logging already done by pin monitor so just return here
                return

            # Convert Wemos Pin to GPIO Pin Number
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            # Check if the pin as i valid pin, Pin monitor returns false if pin is invalid
            if self.Pin is False:
                self.Dobby.Log(2, "Dimmer/" + id, "Invalid Pin Name: " + str(Config['Pin']) + " - Unable to initialize Dimmer")
                return

            # Init pin save in self.Pin with frequancy set to max aka 1000 if not defined in device config - PWM_Frequancy
            
            # self.Pin = machine.PWM(machine.Pin(self.Pin), freq=self.Dobby.Config.get('PWM_Frequancy', 1000))
            self.Pin = machine.PWM(machine.Pin(self.Pin), freq=20000)

            # Whether the dimmer is on or off
            self.On = False

            # Stors current value in percent for later referance
            # Start it at 1 so we can set it to 0 when done setting up since dimmer start at 100%
            self.Percent = 1
            # Stores last percent value, used to turn the light on
            # Dimmer/<Name>/On is triggered and we are off then will set the current percent value this this value
            # the last percent value is saved every time the percent is set to 0
            self.Last_Percent = 75

            # Save fade config to self.Fade
            # or defauly to below values
            self.Fade = Config.get("Fade", {'Delay': 15, 'Jump': 1})
            
            # Check if we got the needed config
            for Entry in ['Delay', 'Jump']:
                # Check if we got the needed config
                if self.Fade.get(Entry, None) == None:
                    # Log event
                    self.Dobby.Log(2, "Dimmer/" + self.Name + "/Fade", "Missing config: " + Entry + " - Cannot enable Fade")
                    # Set self.Fade = None to disable fade for this dimmer
                    self.Fade = None
                    # Break the for loop so we dont fail on self.Fade.get during next loop
                    return
                else:
                    # Log event
                    self.Dobby.Log(0, "Dimmer/" + self.Name + "/Fade", Entry + " set to: " + str(self.Fade[Entry]))

            # Check if the dobby.timer module is loaded
            self.Dobby.Timer_Init()
            # Add a timer
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # 4 = Argument
            # 5 = Disable logging for this timer since it will be triggered a lot
            # Note Fade is active by creating <state> key with referance to timer in Fade dict
            self.Fade['timer'] = self.Dobby.Sys_Modules['timer'].Add(
                "Dimmer-" + self.Name + "-Fade",
                self.Fade['Delay'],
                self.Fade_Jump,
                Argument=False,
                Logging=False
            )


            ## //////////////////// MaxOn \\\\\\\\\\\\\\\\\\\\
            self.MaxOn = Config.get("MaxOn", None)
            if self.MaxOn != None:

                # Convert max on to ms
                Max_ms = self.Dobby.Sys_Modules['timer'].Time_To_ms(Config['MaxOn'])
                # Check if we got a error in convertion
                if Max_ms == None:
                    # Log event - error
                    self.Dobby.Log(0, "Dimmer/" + self.Name + "/MaxOn", "MaxOn not valid: " + str(Config['MaxOn']) + " - Disabling")
                    
                else:
                    # Log event
                    self.Dobby.Log(0, "Dimmer/" + self.Name + "/MaxOn", "MaxOn set to: " + str(Config['MaxOn']))

                    # Check if the dobby.timer module is loaded
                    self.Dobby.Timer_Init()

                    # We will store the timer int MaxOn var if configured
                    # Add a timer
                    # 1 = Referance Name
                    # 2 = Timeout
                    # 3 = Callback
                    # 4 = Argument
                    # Note MaxOn is active by creating <state> key with referance to timer in MaxOn dict
                    self.MaxOn = self.Dobby.Sys_Modules['timer'].Add(
                        self.Name + "-MaxOn",
                        Max_ms,
                        self.Set_Percent,
                        Argument=0
                    )
            
            # Mark Dimmer as ok aka enable it
            self.OK = True

            # Since the dimmer comes on at 100% will set it to 0
            self.Set_Percent(0)
           

            # Log event
            self.Dobby.Log(0, "Dimmer/" + self.Name, "Initialization complete")


        # -------------------------------------------------------------------------------------------------------
        def Percent_To_Frequency(self, Value):
            # Returns a int containing the frequency value based on procent of 1023
            return round(int(Value) * 1023 / 100)

        # -------------------------------------------------------------------------------------------------------
        def Frequency_To_Percent(self, Value):
            # Returns a int containing the procent value of 1023
            return round(1023 / 100 * int(Value))


        # -------------------------------------------------------------------------------------------------------
        def Get_State(self, Percent=True):
            if Percent == True:
                return self.Percent
            else:
                return self.Pin.duty()

        # -------------------------------------------------------------------------------------------------------
        def Fade_Jump(self, Target):
            # Fades to <Target> % value

            # Check if Target is equal to current percent value
            if self.Percent == Target:
                # Since we are done return
                return

            # Check if we have to + or -
            ## Smaller aka we need to + current value to get to Target
            if self.Percent < Target:
                Action = "+"
            else:
                Action = "-"

            # Create New_Percent by + or - self.Fade['Jump']
            New_Percent = eval(str(self.Percent) + Action + str(self.Fade['Jump']))
            
            # Got to target
            if New_Percent == Target:
                # We got to target so log state
                self.Set_State(New_Percent, True)
                # Since we are done return
                return

            # Change action to match < or >
            # If we do + self.Percent then we need to check for New_Percent being larger than aka >
            if Action == "+":
                Action = ">"
            else:
                Action = "<"

            # Passed target
            if eval(str(New_Percent) + Action + str(Target)) == True:
                # If we passed target with New_Percent then simply set to Target
                # We got to target so log state
                self.Set_State(Target, True)

            # Not at target yet
            else:
                # not at target do not log state
                self.Set_State(New_Percent, False, False)
                # Start the timer again and pass original target
                self.Fade['timer'].Argument = Target
                self.Fade['timer'].Start()


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
                raise self.Error("Is_Numer: Invalid value provided: " + str(Value))
            
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
                        raise self.Error("Is_Numer: Number: " + str(Value) + " not between -100% and 100%")
                # if we are not checking for percent return the value
                return Value



        # -------------------------------------------------------------------------------------------------------
        def Set_Percent(self, New_Percent, MatchValue = True):
            # Sets value to a value givent
            # will trigger fade if activated

            Set_Value = True

            Do_Math = False

            # Check if we got a step aka New_Percent starts with + pr -
            if str(New_Percent).startswith('+') == True or str(New_Percent).startswith('-') == True:
                Do_Math = True

            # Check if state is a percent value
            # Dobby.Is_Number will raise a Value error if not valued procent
            try:
                New_Percent = int(self.Is_Number(New_Percent, Round=True, Percent=True))
            except self.Dobby.Error:
                # Log error
                self.Dobby.Log(2, "Dimmer/" + self.Name, "Invalid value provided: " + str(New_Percent))
                # return True so we dont trigger unknown command            
                return True

            if Do_Math == True:
                # Eval will run the math in the string form New_Percent
                New_Percent = eval(str(self.Percent) + str(New_Percent))

            # Set New_Percent is smaller than 0 set to 0 if larger than 100 set to 100
            if New_Percent < 0:
                New_Percent = 0
                Set_Value = False
            elif New_Percent > 100:
                New_Percent = 100
                Set_Value = False

            if MatchValue == True:
                # Check if % we got == self.Percent
                # if so trun the dimmer off
                # Only do this if we are setting a value and not stepping with + or -
                if Set_Value == True:
                    if self.Percent == New_Percent:
                        # Set New_Percent to 0 so we turn off or fade to 0
                        New_Percent = 0

                    # If we are setting to = 0 then note last state
                    if New_Percent == 0:
                        self.Last_Percent = self.Percent

            # Check if Fade is enabeled
            if self.Fade != None:
                # Start the timer and pass Target aka New_Percent
                self.Fade['timer'].Argument = New_Percent
                self.Fade['timer'].Start()
            
            # Fade not active change state
            else:
                self.Set_State(New_Percent)
            
            # return True so we dont trigger unknown command            
            return True
        

        # -------------------------------------------------------------------------------------------------------
        def Log_json(self):

            # Create the json dict
            json_Dict = {}
            # Add online
            json_Dict['online'] = True
            # Add on
            if self.Percent == 0:
                json_Dict['on'] = False
            else:
                json_Dict['on'] = True
            # Add brightness
            if self.Percent == 0:
                json_Dict['brightness'] = self.Last_Percent
            else:
                json_Dict['brightness'] = self.Percent

            # Log peripheral
            # True = Generate topic and retained
            self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic("Dimmer", End=self.Name + "/json", State=True), ujson.dumps(json_Dict)])


        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, New_Percent, Log_Event=True, Log_json=True):
            # Change state
            self.Pin.duty(self.Percent_To_Frequency(New_Percent))
            
            # Note current percent value
            self.Percent = New_Percent

            # Check if MaxOn is configured
            if self.MaxOn != None:
                # if MaxOn is not None then its a timer we need to start if value is not 0 and stop of 0
                # Stop timer
                if self.Percent == 0:
                    self.MaxOn.Stop()
                # Start timer
                else:
                    self.MaxOn.Callback = self.Set_Percent
                    self.MaxOn.Argument = 0
                    self.MaxOn.Start()
            
            # Check if we need to log the event
            if Log_Event == True:
                # Log peripheral
                # True = Generate topic and retained
                self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic("Dimmer", End=self.Name, State=True), New_Percent])
                # No reason to save state since we read it of the pin when needed
                # Return true since the value was changed
                
            
            # Check if we need to log a json
            if Log_json == True:

                self.Log_json()
                # No reason to save state since we read it of the pin when needed
                # Return true since the value was changed
                
            return True


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            # Handles messages to dimmer
            # At this sage we know self.name is valid
            
            # check if we got json sub topic
            # Remember Sub_Topic gets set to lower in base
            if Sub_Topic == 'json':

                # Try to convert the command to a json
                try:
                    Command = ujson.loads(Command)
                # if fails return
                except:
                    self.Dobby.Log(2, "Dimmer/" + self.Name, "Invalid json recived")
                    return
                
                # Check if on is true
                if Command['on'] == True:
                    # If on is true we set the percent aka brightness regardless
                    self.Set_Percent(Command['brightness'], MatchValue=False)
                
                # Command['on'] == False
                else:
                    # Save self.Percent to self.Last_Percent so we can reffer to if while on is false
                    self.Last_Percent = Command['brightness']
                    # Set percent to 0 since on is false
                    self.Set_Percent(0, MatchValue=False)
                    # Log the state change regardless if it changes or not
                    # its done so google sees the change in brightness
                    self.Log_json()


            # After altering command then check commands as normal
            elif Command == "?":
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Peripherals_Topic("Dimmer", End=self.Name, State=True),
                        self.Percent
                    ]
                )

            # Set_Percent will return true if Command was a percent value between -100 and 100
            elif self.Set_Percent(Command) != True:
                # the return is at the end since we only act on not true
                self.Dobby.Log(1, 'Dimmer', "Unknown Dimmer command: " + str(Command))
