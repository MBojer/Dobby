import utime
import machine


# -------------------------------------------------------------------------------------------------------
class Init:
    # Blinks the IndicatorLED
    # Usage:
    #     self is Dobby
    #     Init: IndicatorLED = Init(self)
    #     Start Blinking: IndicatorLED.Enable('WiFi')
    #     Stop Blinking: IndicatorLED.Disable('WiFi')
    
    # Version 300000


    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):
        # Times does not seem to be the best solution for this
        # Referance to dobby
        self.Dobby = Dobby
        # Log event
        self.Dobby.Log(0, "System", "IndicatorLED - Initializing")

        # Check if the pin owned by IndicatorLED
        if Dobby.Pin_Monitor.Get_Owner("D4") != "IndicatorLED":
            self.Dobby.Log(1, "System", "IndicatorLED - Disabeled pin: D4 - In owned by: " + str(Dobby.Pin_Monitor.Pins["D4"]['Owner']))
            return

        # Needed vars
        # Currently active blink only one can be active at the time
        self.Active = None
        # How many blinks is left in current cycle
        self.Active_Left = 0
        
        # How long to wait between cycles in sec
        self.Cycle_Delay = 3000
        
        # List of enabled blinks names
        self.Enabled = []
        # The information for each blink
        self.Blinks = {
            'Booting': {'Level': 0, 'Times': 5, 'Delay': 250, 'Once': True},
            'FindMe': {'Level': 0, 'Times': 20, 'Delay': 250, 'Once': True},
            'Log-Fatal': {'Level': 1, 'Times': 5, 'Delay': 1000, 'Once': True},
            'Log-Critical': {'Level': 2, 'Times': 4, 'Delay': 1000, 'Once': True},
            'Log-Error': {'Level': 3, 'Times': 3, 'Delay': 1000, 'Once': True},
            'Log-Warning': {'Level': 4, 'Times': 2, 'Delay': 1000, 'Once': True},
            'WiFi': {'Level': 5, 'Times': 2, 'Delay': 500, 'Once': False},
            'MQTT': {'Level': 6, 'Times': 4, 'Delay': 500, 'Once': False},
        }

        # I havent found a good way to get hardware info.
        # will use machine.EXT0_WAKE in a try statement
        # if we get AttibuteError then we know its a ESP8266
        try:
            if machine.EXT0_WAKE == None:
                pass
        # ESP8266
        except AttributeError:
            # The LED on a ESP8266 is ON when 0 and wise versa
            self.On_Value = False
        # ESP32
        else:
            # The LED on a ESP32 is ON when 1 and wise versa
            self.On_Value = True

        
        # Pin setup
        ## Convert Wemos Pin to GPIO Pin Number
        ## Create Machine pin
        self.Pin = machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin('D4'), machine.Pin.OUT)
        # Turn led off
        self.LED_Off()

        # Create the timer we need
        # Check if the dobby.timer module is loaded
        self.Dobby.Timer_Init()
        # Add a timer
        # 1 = Referance Name
        # 2 = Timeout
        # 3 = Callback
        # 4 = Disable logging for this timer since it will be triggered a lot
        # Note Fade is active by creating <state> key with referance to timer in Fade dict
        self.Timer = self.Dobby.Sys_Modules['Timer'].Add(
            "IndicatorLED",
            1,
            self.Reset,
            Logging = False
        )
        # Start the timer so we reset after 500 ms so we make the first blink seperate from the upload and boot blink
        # a timer will finish it current blink cycle and then look for a new blink if any 
        # and if multiple the one with the highets level
        self.Timer.Start(Argument=None, Timeout_ms=500, Callback=self.Reset)


    def Reset(self):    
        # Check if there is any timers in the queue
        if self.Enabled == []:
            return
        
        # Check if there is a active blink
        elif self.Active is None:
            # No active blinks need to enable one since we have some in self.Enabled
            # Activate the blink name from Enabled with the lowest level
            # Find the blink with the lowest level and activate that name
            self.Activate(self.Level_Check())
        
        else:
            print("TISSFSDF SJDFSDF")

        
    def Blink(self, Name):
        # Changes LED state
        # Subtracts one from Active_Left on off
        # if Active_Left == 0 then trigger Timer with reset and Cycle_Delay to reigger next blink if any

        # LED is off so turn it on and trigger relay again
        if self.State() == 'on':
            # Turn the led on
            self.LED_On()

        # Well if its not off then i guess its on
        else:
            # Turn the led off
            self.LED_Off()

            # -1 from Active_Left
            self.Active_Left = self.Active_Left - 1
            # Check if we did the last blink
            if self.Active_Left == 0:
                # Check if we only need to run this timer one
                if self.Blinks[Name]['Once'] == False:
                    # add it back at the end of the list
                    self.Enabled.append(Name)

                # then disable the blink
                self.Disable(Name)
                # return so we dont restart the timer
                return
                    
                    
        # Start the timer the active blinks delays
        self.Timer.Start(Argument=Name, Timeout_ms=self.Blinks[Name]['Delay'], Callback=self.Blink)


    def Activate(self, Name):
        # Activated a blink, this will overwrite any other blink currently active
        # Check if we need to start bliking asap or after Cycle_Delay
        if self.Active == None:
            self.Timer.Start(Argument=Name,Timeout_ms=0, Callback=self.Blink)
        else:
            self.Timer.Start(Argument=Name,Timeout_ms=self.Cycle_Delay, Callback=self.Blink)

        # Set Timers Timeout aka delay
        ## Set Timeout_ms to Cycle_Delay so we have a pause in between blink cycles

        # Mark the blink as active
        self.Active = str(Name)
        # Set how many blinks is left to do
        self.Active_Left = self.Blinks[Name]['Times']

        # log event
        self.Dobby.Log(0, 'System/IndicatorLED', 'Blink activated: ' + self.Active)


    def Level_Check(self):
        # Returns the name from Enabled with the lowest level from Blinks
        if self.Enabled is []:
            return None

        # if Only one entry in list retyrn that entry
        if len(self.Enabled) is 1:
            return self.Enabled[0]

        # Multiple entries find the lowest level
        Name = None
        Lowest_Level = 1337
        # Loop over keys and values in blinks dict
        for Key, Value in self.Blinks.items():
            # Check if key aka name is in Enabeled list
            if Key in self.Enabled:
                # If it is check if the level for that name is lover than Lowest_Level
                # if so set the level as lowest and not the name
                if Value['Level'] < Lowest_Level:
                    Lowest_Level = Value['Level']
                    Name = Key
        # Return the Name we found
        return Name

    def State(self):
        # I havent found a good way to get hardware info.
        # will use machine.EXT0_WAKE in a try statement
        # if we get AttibuteError then we know its a ESP8266
        try:
            if machine.EXT0_WAKE == None:
                pass
        # ESP8266
        except AttributeError:
            # The LED on a ESP8266 is ON when 0 and wise versa
            if not self.Pin.value() == False:
                return 'on'
            else:
                return 'off'
        # ESP32
        else:
            # The LED on a ESP32 is ON when 1 and wise versa
            if not self.Pin.value() == False:
                return 'off'
            else:
                return 'on'


    def LED_On(self):
        # The LED on a ESP8266 is ON when 0 and wise versa
        self.Pin.value(self.On_Value)
    
    def LED_Off(self):
        # The LED on a ESP8266 is ON when 0 and wise versa
        self.Pin.value(not self.On_Value)


    def Enable(self, Name):
        # Enables a blink with given name

        # Check if already Enabled
        if Name in self.Enabled:
            return True

        # Check if the name is a valid blink name
        elif self.Blinks.get(Name, None) is None:
            self.Dobby.Log(2, 'System/IndicatorLED', 'Cannot enable: ' + str(Name) + ' - Unknown name')
            return False
        
        # Log event
        self.Dobby.Log(0, 'System/IndicatorLED', 'Enabled: ' + str(Name))

        # Add the name to the Enabled list
        self.Enabled.append(Name)
        
        # Reset so we start blinking
        self.Reset()
        # Return true to indicated we enabeled ok
        return True


    def Disable(self, Name):
        # Enables a blink with given name

        # Check if not active
        if Name not in self.Enabled:
            return True

        # Check if we know the blink
        elif self.Blinks.get(Name, None) is None:
            self.Dobby.Log(2, 'System/IndicatorLED', 'Cannot disable: ' + str(Name) + ' - Unknown name')
            return False
        
        # If we get the name of the current blink then clear active values
        if self.Active == Name:
            # Clear Active
            # Loop will add then next blink if there is one in enabeled
            self.Active_Left = 0
            # Stop the timer
            self.Timer.Stop()
            # Make sure the led if off
            self.LED_Off()
            # Set active to none
            self.Active = None

        # Remove name from self.Enabeled
        self.Enabled.remove(Name)
        # Log event
        self.Dobby.Log(0, 'System/IndicatorLED', 'Disabled: ' + str(Name))

        return True