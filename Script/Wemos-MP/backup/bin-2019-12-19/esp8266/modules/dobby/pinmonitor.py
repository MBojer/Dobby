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
        ## Dict holding reserved pins
        ### Format <Wemos Pin Name>: {'Owner': "DHT"} 
        self.Pins = {"D4": {'Owner': "IndicatorLED"}}

    # -------------------------------------------------------------------------------------------------------
    def Raise_Error(self, Error_Text):
        # Log event
        self.Dobby.Log(3, "PinMonitor", Error_Text)
        # Raise error
        raise self.Error(Error_Text)

    # -------------------------------------------------------------------------------------------------------
    def Is_Free(self, Pin):
        # Check if pin is valid
        # self.Valid_Pin will raise an error if not
        self.Valid_Pin(Pin)
        # Check if pin is free
        if Pin in self.Pins:
            # Check if its indicator led owning the pin if so we can overwrite it
            if Pin == "D4":
                self.Dobby.Log(1, "PinMonitor", "Pin: D4 is owned by IndicatorLED but can be reassigned")
                # return here since pin can be reassigned
                return True
            # Any other owner then IndicatorLED is failed
            else:
                # Raise error
                self.Raise_Error("Pin: " + Pin + " owned by: " + self.Pins[Pin]['Owner'])
        # Pin Free
        else:    
            self.Dobby.Log(0, "PinMonitor", "Pin: " + Pin + " is free")
            return True


    # -------------------------------------------------------------------------------------------------------
    def Reserve(self, Pin, Owner, Pull=False, Analog=False):
        # Check if pin is free
        # GPIO 16 aka D0 cannot have pull activated so fail if pull is requested active on D0

        # If Analog=True then will only reserve the pin if we get A0
        if Analog == True and Pin != "A0":
            # Raise error
            self.Raise_Error("Only analog pin on ESP8266 is 'A0'")            
            
        # If pull is false do nothing
        if Pull == True:
            # Check if we are dealing with pin D0
            if Pin.lower() == 'd0':
                # Raise error
                self.Raise_Error("Pin: " + Pin + " cannot have pull active, unable to reserve pin")

        # Is free will raise an error if the pin is not free
        # IndicatorLED will be overwriten if set
        if self.Is_Free(Pin) == True:
            # Reserve pin
            self.Pins[str(Pin)] = {'Owner': str(Owner)}
            # log event
            self.Dobby.Log(0, "PinMonitor", "Pin: " + Pin + " reserved for: " + str(Owner))
            # return true after sucesfully reserving the pin
            return True
        

    # -------------------------------------------------------------------------------------------------------
    def To_Wemos_Pin(self, Pin):
        # Convert to upper case to make checking easier
        Pin = Pin.upper()
        # Dict where key is pin name and value is gpio number
        Pin_Dict = {
            'D0': 16,
            'D1': 5,
            'D2': 4,
            'D3': 0,
            'D4': 2,
            'D5': 14,
            'D6': 12,
            'D7': 13,
            'D8': 15,
            'A0': 0
        }
        
        # Get gpio number from fict if key is not in dict return False aka failed
        return machine.Pin(Pin_Dict.get(Pin, False))


    # -------------------------------------------------------------------------------------------------------
    def To_GPIO_Pin(self, Pin):
        # Check if already valid pin
        if Pin in [0, 2, 4, 5, 12, 13, 14, 15, 16]:
            return Pin
        # Convert wemos pin name string to goip pin int
        # Convert pin name string to lover case
        Pin = Pin.upper()
        # Check of pin is valid
        if Pin == "D0":
            GPIO_Pin = 16
        elif Pin == "D1":
            GPIO_Pin = 5
        elif Pin == "D2":
            GPIO_Pin = 4
        elif Pin == "D3":
            GPIO_Pin = 0
        elif Pin == "D4":
            GPIO_Pin = 2
        elif Pin == "D5":
            GPIO_Pin = 14
        elif Pin == "D6":
            GPIO_Pin = 12
        elif Pin == "D7":
            GPIO_Pin = 13
        elif Pin == "D8":
            GPIO_Pin = 15
        # Note A0 is pin 0 as well as D3
        elif "A0" in Pin:
            GPIO_Pin = 0
        # if invalid string return false
        else:
            # Log event
            self.Dobby.Log(2, "PinMonitor", "Invalid wemos Pin name: " + str(Pin))
            # Raise error
            self.Raise_Error("Invalid wemos Pin name: " + str(Pin))
        # Return value
        return GPIO_Pin


    def Valid_Pin(self, Pin):
        # Wemos Pin Name
        if type(Pin) is str:
            if Pin.lower() in ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "a0"]:
                self.Dobby.Log(0, "PinMonitor", "Valid Wemos Pin Name: " + Pin)
                return True
        # GPIO Pin
        else:
            if Pin in [0, 2, 4, 5, 12, 13, 14, 15, 16]:
                self.Dobby.Log(0, "PinMonitor", "Valid GPIO number: " + str(Pin))
                return True
        # Unknown pin
        # Log event
        self.Dobby.Log(2, "PinMonitor", "Invalid pin: " + str(Pin))
        # Raise error
        self.Raise_Error("Invalid pin: " + str(Pin))

    # -------------------------------------------------------------------------------------------------------
    def Get_Owner(self, Pin):
        # Return owner name of pin
        # returns none if free

        # Check if owner exists
        if self.Pins[Pin].get('Owner', None) != None:
            # if pin is owned return the owners name
            return self.Pins[Pin]['Owner']
        # Return None if pin is now owned by anyone
        else:
            # if not owned return None to indicate its free
            return None
