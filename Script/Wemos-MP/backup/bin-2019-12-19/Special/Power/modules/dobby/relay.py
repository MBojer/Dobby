import machine
import utime
import ujson

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Relay", "Initializing")

        # Loop over Peripherals in config
        for Name, Relay_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Relay to the Relay dict
            self.Peripherals[Name] = self.Relay(self.Dobby, Name, Relay_Config)
            # Check if the Relay is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Relay detected disabling it
                self.Dobby.Log(2, "Relay/" + Name, "Issue during setup, disabling the Relay")
            # Relay ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Relay", End="+"))
        
        # Log event
        self.Dobby.Log(0, "Relay", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    class Relay:

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

            # Log Event
            self.Dobby.Log(0, "Relay/" + self.Name, "Initializing")

            # Auto
            self.Auto = {}
            # Delay
            self.Delay = {}

            # Check if we got the needed config
            for Entry in ['Pin']:
                if Config.get(Entry, None) == None:
                    self.Dobby.Log(3, "Relay/" + Name, "Missing config: " + Entry + " - Unable to initialize Relay")
                    return

            # Convert Wemos Pin to GPIO Pin Number
            self.Pin = Config['Pin']
            # Hold the current relay state so we can check again it
            self.Pin_State = None

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(self.Pin, "Relay-" + self.Name)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure Relay
                self.Dobby.Log(3, "Relay/" + Name, "Unable to take ownership of Pin: " + self.Pin + " - Unable to initialize Relay")
                # return so we dont set State to true aka mark the Voltmeter as configured
                return

            # Convert Wemos Pin to GPIO Pin Number
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            if self.Pin == False:
                self.Dobby.Log(3, "Relay/" + Name, "Invalid Pin Name: " + str(Config['Pin']) + " - Unable to initialize Relay")
                return

            # Flip - If True On (1) is Off (0)
            self.Flip = Config.get('Flip', False)
            if self.Flip == True:
                self.Dobby.Log(0, "Relay/" + Name, "Flip active")


            # Create Machine pin
            # And mark the Relay as ok before we get auto or delay since they might trigger a state change
            self.Pin = machine.Pin(self.Pin, machine.Pin.OUT)

            # Mark Relay as ok aka enable it
            # Needs to be done before setting Init state
            self.OK = True
            
            # Set the relay to Init state
            if Config.get('Init', None) == None:
                # Default to 'off'
                self.Set_Off()
            elif Config['Init'].lower() == 'on':
                self.Set_On()
            elif Config['Init'].lower() == 'off':
                self.Set_Off()
            else:
                # Unknown Init state Default to off
                self.Dobby.Log(2, "Relay/" + Name, "Invalid Init State: " + str(Config['Init']) + " - Setting relay Init state to: Off")
                self.Set_Off()


            # Check if auto is set in config
            if Config.get('Auto', None) != None:
                # Check if the dobby.timer module is loaded
                self.Dobby.Timer_Init()
                # Add a timer
                # 1 = Referance Name
                # 2 = Timeout
                # 3 = Callback
                # 4 = Argument
                # Note auto is active by creating <state> key with referance to timer in Auto dict
                self.Auto[Config['Auto']['State'].lower()] = self.Dobby.Sys_Modules['Timer'].Add(
                    self.Name + "-Auto-" + Config['Auto']['State'],
                    Config['Auto']['Time'],
                    self.Set_State,
                    Config['Auto']['State'].lower()
                )
                # Log event
                self.Dobby.Log(0, "Relay/" + self.Name, Config['Auto']['State'] + " Auto set to: " + str(Config['Auto']['Time']) + " ms")


        def On_Message(self, Payload, Sub_Topic=None):
            # Check if relay is OK
            if self.OK == False:
                # FIX - Throw error custom error here and cache in Peripherals.On_Message, then remove relay
                self.Dobby.Log(2, 'Relay-' + self.Name, "Disabeled")

            # Check what command aka payload was recived
            # ? - Returns - 0 = off 1 = on
            if Payload == "?":
                # Publish state            
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Peripherals_Topic("Relay", End=self.Name, State=True),
                        self.Get_State(True)
                    ],
                    Retained=True
                )
            # on - Turns relay on
            elif str(Payload).lower() in ['on', "1"]:
                self.On()

            # off - Turns relay off
            elif str(Payload).lower() in ['off', "0"]:
                self.Off()

            # Toggle - Toggles the relay state aka on->off or off->on
            elif str(Payload).lower() in ["toggle", "2"]:
                self.Toggle()

            # Toggle - Toggles the relay state aka on->off or off->on
            else: 
                self.Dobby.Log(2, 'Relay', "Unknown Relay command: " + str(Payload))



        # -------------------------------------------------------------------------------------------------------
        def Get_State(self, Return_String=False):
            #  Returns the Peripherals current state taking into account Flip
            #  If Return_String == True then will return 'on' or 'off'
                    
            # Input is == so user wants the current relay state
            # Check if output is flipped
            if self.Flip == True:
                Current_State = bool(not self.Pin.value())
            else:
                Current_State = bool(self.Pin.value())
            
            # Check if we need to return bool or string
            if Return_String == True:
                if Current_State == True:
                    Current_State = 'on'
                else:
                    Current_State = 'off'

            # Return either bool or str
            return Current_State
        

        # -------------------------------------------------------------------------------------------------------
        def Log_State_Change(self):
            # Logs the state of the relay to mqtt
            
            # Get state to chack agains
            # True = Return string so we get on or off
            New_Relay_State = self.Get_State(True)

            # # Publish state change if state changed
            # if self.Pin_State != New_Relay_State:
            # Save pin state
            self.Pin_State = New_Relay_State
            # Publish State changed
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic('Relay', End=self.Name, State=True),
                    New_Relay_State
                ],
                Retained=True
            )

        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, New_State):
            # Changes state of relay.
            # Options is On Off Toggle

            # Check if Relay is OK
            if self.OK == False:
                # Fix - Remove relay on failure, reais custom error and delete if so
                self.Dobby.Log(2, "Relay/" + self.Name, "Relay disabeled unable to change state")
                return False

            # Convert New_State to lower to match system wide lower case
            New_State = New_State.lower()
            # Check if we got a valid state
            if New_State not in ['on', 'off', 'toggle']:
                    self.Dobby.Log(2, "Relay/" + self.Name, "Unknown state provided: " + New_State)
                    # Return false because we failed
                    return False

            # Check if current state == requested state
            # Gets set by self.Log_State_Change
            if self.Pin_State == New_State:
                return False
            
            # Flip value if 2 is selected aka toggle
            # By using self.Get_State we get on or off with flip taking into account
            if New_State == 'toggle':
                # If on trigger off and vise versa
                if self.Get_State(True) == 'on':
                    self.Set_Off()
                else:
                    self.Set_On()

            # Turn on
            elif New_State == 'on':
                self.Set_On()

            # Turn off
            elif New_State == 'off':
                self.Set_Off()

            return True



        # -------------------------------------------------------------------------------------------------------
        def Set_On(self):
            # Changed the relay state to on and accounts for flip
            
            # Change Relay state
            # Remember to pass Flip regardless if true of false
            self.Pin.value(self.Dobby.OnOff_To_Bool('on', self.Flip))

            # Check if auto is enabled remember to use off for on
            if self.Auto.get('off', None) != None:
                # Start Timer
                self.Auto['off'].Start()

            # Log state changed
            self.Log_State_Change()


        # -------------------------------------------------------------------------------------------------------
        def Set_Off(self):
            # Changed the relay state to off and accounts for flip

            # Change Relay state
            # Remember to pass Flip regardless if true of false
            self.Pin.value(self.Dobby.OnOff_To_Bool('off', self.Flip))

            # Check if auto is enabled remember to use off for on
            if self.Auto.get('on', None) != None:
                # Start Timer
                self.Auto['on'].Start()

            # Log state changed
            self.Log_State_Change()


        # -------------------------------------------------------------------------------------------------------
        def On(self):
            # Just trigger self.Set_State it will handle the rest
            self.Set_State('on')

        # -------------------------------------------------------------------------------------------------------
        def Off(self):
            # Just trigger self.Set_State it will handle the rest
            self.Set_State('off')

        # -------------------------------------------------------------------------------------------------------
        def Toggle(self):
            # Flips the relay to oposite state

            # Change relay state
            self.Set_State('Toggle')