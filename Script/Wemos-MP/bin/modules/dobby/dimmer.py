
import machine
import utime
import ujson


class Init:

    # -------------------------------------------------------------------------------------------------------
    # Fix - This code can be in main as a for loop and can be removed from all sub modules
    def __init__(self, Dobby, Dimmer_Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Dimmers
        self.Dimmers = {}
        # Log Event
        self.Dobby.Log(1, "Dimmer", "Initializing")
        
        # Loop over Dimmers in config
        for Name, Config in Dimmer_Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Dimmer to the Dimmer dict
            self.Dimmers[Name] = self.Dimmer(self.Dobby, Name, Config)
            # Check if the Dimmer is ok
            if self.Dimmers[Name].OK is False:
                # Issue with Dimmer detected disabling it
                self.Dobby.Log(2, "Dimmer/" + Name, "Issue during setup, disabling the Dimmer")
            else:
                # Subscribe to Dimmer topic if at least one Dimmer was ok
                self.Dobby.MQTT_Subscribe(self.Dobby.Config['System_Header'] + "/Dimmer/" + self.Dobby.Config['Hostname'])
            
        self.Dobby.Log(0, "Dimmer", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    # Publish readings is requested to do so - Meant to be placed in dobbylib.On_Message()
    def On_Message(self, Topic, Payload):
        # Check if we need to take action based on topic
        if Topic == self.Dobby.Config['System_Header'] + "/Dimmer/" + self.Dobby.Config['Hostname']:
            # Run try on dimmer name
            # if failed unknown dimmer if not we pass payload to dimmer.on_message()
            try:
                # If we put name in try it we generate and error if we get name and no command
                Name = Payload[0:Payload.index(" ")]
                # Remember + 1 to not get space
                self.Dimmers[Name].On_Message(Payload[Payload.index(" ") + 1:])
            except IndexError as e:
                self.Dobby.Log(1, 'Dimmer', "Unknown Dimmer: " + Name)

            # return true so we end the for loop in dobby.main.MQTT_Handle_Incomming
            return True
    
        # return false so we DO NOT end the for loop in dobby.main.MQTT_Handle_Incomming
        return False


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
            if self.Dobby.Pin_Monitor.Reserve(self.Pin, "Dimmer-" + self.Name) == False:
                # Pin in use unable to configure Dimmer
                self.Dobby.Log(2, "Dimmer/" + Name, "Pin in use - Unable to initialize Dimmer")
                # return so we dont set State to true aka mark the Dimmer as configured
                return

            # Convert Wemos Pin to GPIO Pin Number
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            # Check if the pin as i valid pin, Pin monitor returns false if pin is invalid
            if self.Pin is False:
                self.Dobby.Log(2, "Dimmer/" + id, "Invalid Pin Name: " + str(Config['Pin']) + " - Unable to initialize Dimmer")
                return

            # Init pin save in self.Pin with frequancy set to max aka 1023
            self.Pin = machine.PWM(machine.Pin(self.Pin), freq=1023)

            # Stors current value in percent for later referance
            self.Percent = 0

            # Load Optional config if any
            ## Fade
            if Config.get("Fade", None) != None:
                # Save fade config to self.Fade
                self.Fade = Config['Fade']
                # Check if we got the needed config
                for Entry in ['Delay', 'Jump']:
                    # Check if we got the needed config
                    if self.Fade.get(Entry, None) == None:
                        # Log event
                        self.Dobby.Log(2, "Dimmer/" + self.Name + "/Fade", "Missing config: " + Entry + " - Cannot enable Fade")
                        # Set self.Fade = None to disable fade for this dimmer
                        self.Fade = None
                        # Break the for loop so we dont fail on self.Fade.get during next loop
                        break
                    else:
                        # Log event
                        self.Dobby.Log(0, "Dimmer/" + self.Name + "/Fade", Entry + " set to: " + str(self.Fade[Entry]))

                # Check if self.Fade is not acter config check, if so fade is disabled
                if self.Fade != None:
                    # Check if the dobby.timer module is loaded
                    self.Dobby.Timer_Init()
                    # Add a timer
                    # 1 = Referance Name
                    # 2 = Timeout
                    # 3 = Callback
                    # 4 = Argument
                    # 5 = Disable logging for this timer since it will be triggered a lot
                    # Note Fade is active by creating <state> key with referance to timer in Fade dict
                    self.Fade['Timer'] = self.Dobby.Sys_Modules['Timer'].Add(
                        self.Name + "-Fade",
                        self.Fade['Delay'],
                        self.Fade_Jump,
                        False,
                        False
                    )
            # Mark Dimmer as ok aka enable it
            self.OK = True

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
                self.Fade['Timer'].Start(Target)


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

            # Check if Fade is enabeled
            if self.Fade != None:
                # Start the timer and pass Target aka New_Percent
                self.Fade['Timer'].Start(New_Percent)
            
            # Fade not active change state
            else:
                self.Set_State(New_Percent)
            
            # return True so we dont trigger unknown command            
            return True
        

        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, New_Percent, Log_Event=True):
            # Change state
            self.Pin.duty(self.Percent_To_Frequency(New_Percent))
            # Not current percent value
            self.Percent = New_Percent
            # Check if we need to log the event
            if Log_Event == True:
                # Log peripheral
                # True, True = Generate topic and retained
                self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic("Dimmer", self.Name), New_Percent], True)
                # No reason to save state since we read it of the pin when needed
                # Return true since the value was changed
            return True


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command):
            # Handles messages to dimmer
            # At this sage we know self.name is valid

            # Set_Percent will return true if Command was a percent value between -100 and 100
            if self.Set_Percent(Command) != True:
                # the return is at the end since we only act on not true
                self.Dobby.Log(1, 'Dimmer', "Unknown Dimmer command: " + str(Command))
