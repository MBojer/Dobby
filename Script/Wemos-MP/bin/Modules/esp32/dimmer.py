import machine
import utime
import ujson


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
            else:
                # Subscribe to Dimmer topic if at least one Dimmer was ok
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Dimmer", End="+"))
                # On/Off Topics
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Dimmer", End="+/OnOff"))

            
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

            # Stors current value in percent for later referance
            self.Percent = 0
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
                self.Name + "-Fade",
                self.Fade['Delay'],
                self.Fade_Jump,
                False,
                False
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

            # Since the dimmer is ok we can now creat the ALL topic
            

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
                self.Set_State(New_Percent, False)
                # Start the timer again and pass original target
                self.Fade['timer'].Start(Target)


        # -------------------------------------------------------------------------------------------------------
        def Set_Percent(self, New_Percent):
            # Sets value to a value givent
            # will trigger fade if activated

            # Check if state is a percent value
            # Dobby.Is_Number will raise a Value error if not valued procent
            try:
                New_Percent = self.Dobby.Is_Number(New_Percent, Round=True, Percent=True)
            except ValueError:
                return False

            # Check if % we got == self.Percent
            # if so trun the dimmer off
            if self.Percent == New_Percent:
                # Set New_Percent to 0 so we turn off or fade to 0
                New_Percent = 0

            # If we are setting to = 0 then note last state
            if New_Percent == 0:
                self.Last_Percent = self.Percent

            # Check if Fade is enabeled
            if self.Fade != None:
                # Start the timer and pass Target aka New_Percent
                self.Fade['timer'].Start(New_Percent)
            
            # Fade not active change state
            else:
                self.Set_State(New_Percent)
            
            # return True so we dont trigger unknown command            
            return True
        

        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, New_Percent, Log_Event=True):
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
                    self.MaxOn.Start(Callback=self.Set_Percent, Argument=0)
            
            # Check if we need to log the event
            if Log_Event == True:
                # Log peripheral
                # True = Generate topic and retained
                self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic("Dimmer", End=self.Name, State=True), New_Percent])
                # No reason to save state since we read it of the pin when needed
                # Return true since the value was changed
            return True


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            # Handles messages to dimmer
            # At this sage we know self.name is valid
            
            # check if we got OnOff sub topic
            if Sub_Topic == 'onoff':
                # Now check we the command is 0 aka OFF or 1 ON
                # Compare in string so we cache both string and int
                if str(Command) == '1':
                    # Set command to self.Last_Percent
                    # only if self.Percent == 0 aka already off
                    if self.Percent == 0:
                        Command = self.Last_Percent
                    else:
                        # if we are already on then do nothing aka return
                        return
                
                elif str(Command) == '0':
                    # Set command to self.Last_Percent
                    # only if self.Percent != 0 aka already on
                    if self.Percent != 0:
                        Command = 0
                    else:
                        # if we are already off then do nothing aka return
                        return

            # After altering command then check commands as normal
            if Command == "?":
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
