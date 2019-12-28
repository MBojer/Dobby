 # -------------------------------------------------------------------------------------------------------
#Pin monitor
class Init:
    # -------------------------------------------------- Config exception --------------------------------------------------
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):
        # Create needed vars
        ## Referance to dobby
        self.Dobby = Dobby
        # A dict with Key = Pin Name and Value dict with GPIO number, Owner, Type
        self.Pins = {
            'IO0': {'GPIO': 0, 'Type': ['PWM', 'Touch']},
            'TXD': {'GPIO': 1, 'Type': ['TX']},
            'RXD': {'GPIO': 3, 'Type': ['RX']},
            'CLK': {'GPIO': 6, 'Type': ['Flash']},
            'SD0': {'GPIO': 7, 'Type': ['Flash']},
            'SD1': {'GPIO': 8, 'Type': ['Flash']},
            'SD2': {'GPIO': 9, 'Type': ['PWM']},
            'SD3': {'GPIO': 10, 'Type': ['PWM']},
            'CMD': {'GPIO': 11, 'Type': ['Flash']},
            'TDI': {'GPIO': 12, 'Type': ['PWM', 'Touch']},
            'TCK': {'GPIO': 13, 'Type': ['PWM', 'Touch']},
            'TMS': {'GPIO': 14, 'Type': ['PWM', 'Touch']},
            'TD0': {'GPIO': 15, 'Type': ['PWM', 'Touch']},
            'IO2': {'GPIO': 2, 'Type': ['PWM', 'Touch'], 'Owner': 'IndicatorLED'},
            'IO4': {'GPIO': 4, 'Type': ['PWM', 'Touch']},
            'IO5': {'GPIO': 5, 'Type': ['PWM']},
            'IO16': {'GPIO': 16, 'Type': ['Flash']},
            'IO17': {'GPIO': 17, 'Type': ['Flash']},
            'IO18': {'GPIO': 18, 'Type': ['PWM']},
            'IO19': {'GPIO': 19, 'Type': ['PWM']},
            'IO21': {'GPIO': 21, 'Type': ['PWM']},
            'IO22': {'GPIO': 22, 'Type': ['PWM']},
            'IO23': {'GPIO': 23, 'Type': ['PWM']},
            'IO25': {'GPIO': 25, 'Type': ['PWM']},
            'IO26': {'GPIO': 26, 'Type': ['PWM']},
            'IO27': {'GPIO': 27, 'Type': ['PWM', 'Touch']},
            'IO32': {'GPIO': 32, 'Type': ['PWM', 'Touch']},
            'IO33': {'GPIO': 33, 'Type': ['PWM', 'Touch']},
            'IO34': {'GPIO': 34, 'Type': ['Input',]},
            'IO35': {'GPIO': 35, 'Type': ['Input', 'PWM']},
            'SVP': {'GPIO': 36, 'Type': ['Input', 'PWM']},
            'SVN': {'GPIO': 39, 'Type': ['Input', 'PWM']}
        }
        # Var holding all wemos pin names
        self.Wemos_Pins = {
            'D0': 'IO26',
            'D1': 'IO22',
            'D2': 'IO21',
            'D3': 'IO17',
            'D4': 'IO2',
            'D5': 'IO18',
            'D6': 'IO19',
            'D7': 'IO23',
            'D8': 'IO5',
            'A0': 'SVP',
            'RX': 'RXD',
            'TX': 'TXD'
        }


    # -------------------------------------------------------------------------------------------------------
    def Is_Free(self, Pin):
        # Check if pin is valid
        # self.Valid_Pin will raise an error if not
        self.Valid_Pin(Pin)
        
        # Check if someone owns the pin
        # Pin does not have an owner
        if self.Pins[Pin].get("Owner", None) == None:
            # Pin Free
            self.Dobby.Log(0, "PinMonitor", "Pin: " + Pin + " is free")
            return True
    
        # Pin does HAS an owner
        else:
            # Check if its indicator led owning the pin
            # if so we can overwrite it
            if self.Pins[Pin]["Owner"] == 'IndicatorLED':
                self.Dobby.Log(1, "PinMonitor", "Pin: " + Pin + " is owned by IndicatorLED but can be reassigned")
                # return here since pin can be reassigned
                return True
            # If not owned by indicator led raise an error
            else:
                # Raise error
                self.Raise_Error("Pin: " + Pin + " owned by: " + self.Pins[Pin]['Owner'])

    # -------------------------------------------------------------------------------------------------------
    def Raise_Error(self, Error_Text):
        # Log event
        self.Dobby.Log(3, "PinMonitor", Error_Text)
        # Raise error
        raise self.Error(Error_Text)


    # -------------------------------------------------------------------------------------------------------
    def Wemos_To_Mini32_Pin(self, Pin):
        # Check if we got a Wemos D1 mini pin name
        if Pin.upper() in self.Wemos_Pins:
            # If so then get value from self.Wemos_Pins mathing keys
            # Log event
            self.Dobby.Log(0, "PinMonitor", "Pin name converted from: " + Pin + " to " + self.Wemos_Pins[Pin])
            # Change pin name
            return self.Wemos_Pins[Pin]
        # Not a wemos pin so return what we got unaltered
        else:
            return Pin

    # -------------------------------------------------------------------------------------------------------
    def Reserve(self, Pin, Owner, Pull=False):
        # Check if pin is free

        # Convert to Wemos Pin if we got one
        Pin = self.Wemos_To_Mini32_Pin(Pin)
        

        # If not then check if we got a Mini32 pin name
        # If we got a Wemos D1 name we just changed it to matching Mini32 name above
        if Pin.upper() in self.Pins:
            # if Owner startswith Dimmer when we need to check if pin is a PWM pin
            if Owner.startswith("Dimmer") == True:
                # Check that pin is not marked as input aka input only
                if 'Input' in self.Pins[Pin]['Type']:
                    self.Raise_Error("Pin: " + Pin + " is input only, unable to reserve pin")
                    
                # Check if we have 'PWM' in the 'Type' key
                if 'PWM' not in self.Pins[Pin]['Type']:
                    self.Raise_Error("Pin: " + Pin + " is not a PWM pin, unable to reserve pin")
        
            # Is free will raise an error if the pin is not free
            # IndicatorLED will be overwriten if set
            if self.Is_Free(Pin) == True:
                # Reserve pin
                self.Pins[Pin]['Owner'] = str(Owner)
                # log event
                self.Dobby.Log(0, "PinMonitor", "Pin: " + Pin + " reserved for: " + str(Owner))
                # return true after sucesfully reserving the pin
                return True
            

            # # GPIO 16 aka D0 cannot have pull activated so fail if pull is requested active on D0
            # # If pull is false do nothing
            # if Pull == True:
            #     # Check if we are dealing with pin D0
            #     if Pin.lower() == 'd0':
            #         # Log event
            #         self.Dobby.Log(2, "PinMonitor", "Pin: " + Pin + " cannot have pull active, unable to reserve pin")
            #         # Raise error
            #         raise self.Error("Pin: " + Pin + " cannot have pull active, unable to reserve pin")




        # Invalid pin name
        else:
            # Raise error
            self.Raise_Error("Invalid Pin name: " + str(Pin))

        
    # -------------------------------------------------------------------------------------------------------
    def To_GPIO_Pin(self, Pin):
        # Convert pin name string to goip pin int
        
        # Convert to Wemos Pin if we got one
        Pin = self.Wemos_To_Mini32_Pin(Pin)

        if self.Pins[Pin].get('GPIO', None) != None:
            return self.Pins[Pin]['GPIO']
        else:
            # Raise error
            self.Raise_Error("Invalid wemos Pin name: " + str(Pin))


    # -------------------------------------------------------------------------------------------------------
    def Valid_Pin(self, Pin):
        # Check if the str passed as Pin is a valid pin name
        # check for mini32 pin name
        if Pin.upper() in self.Pins:
            self.Dobby.Log(0, "PinMonitor", "Valid Pin Name: " + Pin)
            return True
        # check for wemos pin name
        elif Pin.upper() in self.Wemos_Pins:
            self.Dobby.Log(0, "PinMonitor", "Valid Pin Name: " + Pin)
            return True
            # Unknown pin
        else:
            # Raise error
            self.Raise_Error("Invalid pin: " + str(Pin))




    # -------------------------------------------------------------------------------------------------------
    def Get_Owner(self, Pin):
        # Return owner name of pin
        # returns none if free

        # Convert to Wemos Pin if we got one
        Pin = self.Wemos_To_Mini32_Pin(Pin)

        # Check if owner exists
        if self.Pins[Pin].get('Owner', None) != None:
            # if pin is owned return the owners name
            return self.Pins[Pin]['Owner']
        # Return None if pin is now owned by anyone
        else:
            # if not owned return None to indicate its free
            return None
