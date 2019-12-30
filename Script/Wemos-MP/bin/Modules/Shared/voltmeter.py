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
        self.Dobby.Log(1, "Voltmeter", "Initializing")

        # Loop over Peripherals in config
        for Name, Voltmeter_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Voltmeter to the Voltmeter dict
            self.Peripherals[Name] = self.Voltmeter(self.Dobby, Name, Voltmeter_Config)
            # Check if the Voltmeter is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Voltmeter detected disabling it
                self.Dobby.Log(2, "Voltmeter/" + Name, "Issue during setup, disabling the Voltmeter")
            # Voltmeter ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Voltmeter", End="+"))
        
        # Log event
        self.Dobby.Log(0, "Voltmeter", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    class Voltmeter:

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
            self.Dobby.Log(1, "Voltmeter/" + self.Name, "Initializing")

            # Check if we got the needed config
            for Entry in ['Pin']:
                if Config.get(Entry, None) == None:
                    self.Dobby.Log(3, "Voltmeter/" + Name, "Missing config: " + Entry + " - Unable to initialize Voltmeter")
                    return

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(Config['Pin'], "Voltmeter-" + self.Name, Analog=True)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure Voltmeter
                self.Dobby.Log(2, "Voltmeter/" + Name, "Pin in use - Unable to initialize")
                # return so we dont set State to true aka mark the Voltmeter as configured
                return

            # Make a pin object
            self.Pin = machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin']))
            try:
                # Create the ADC object
                self.Pin = machine.ADC(self.Pin)
            # We get a value error if the pin is not useable as a ADC pin
            except ValueError:
                # if we cant use the pin as a ADC pin we can't continue
                # Log event
                self.Dobby.Log(4, "Voltmeter/" + Name, "Not a ADC pin - Unable to initialize")
                # so return before marking as ok
                return

            # Holds the last voltage reading from the voltmeter
            self.Voltage = -1

            # ADC Max value is 1023 on esp8266 and 4095 on esp32
            if self.Dobby.ESP_Type == 32:
                self.ADC_Max = 4095
            else:
                self.ADC_Max = 1023

            # Get R3 if present, default to 0
            self.R3 = Config.get("R3", 0)

            # Read rate, default to "0.5s"
            self.Rate = Config.get("Rate", "0.5s")

            # Calc max voltage used to convert 1024 or 4095 to volt
            # The 320 is R1 aka 100k and R2 aka 220k
            self.Max_Bridge_Volt = (self.R3 + 320000) * 0.00001

            # Mark Voltmeter as ok aka enable it
            # Needs to be done before setting Init state
            self.OK = True

            # Check if the dobby.timer module is loaded
            self.Dobby.Timer_Init()
            # Add a timer
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # Disable logging since we read this often
            self.Read_Timer = self.Dobby.Sys_Modules['timer'].Add(
                "Voltmeter-" + self.Name + "-Read",
                self.Rate,
                self.Read,
                Logging=False
            )

            # Start the timer
            self.Read_Timer.Start()


        # -------------------------------------------------------------------------------------------------------
        def Read(self):

            # Read raw pin value
            Raw = self.Pin.read()

            # Convert to Voltage
            self.Voltage = Raw * (self.Max_Bridge_Volt / self.ADC_Max)

            # Start the timer
            self.Read_Timer.Start()


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Payload, Sub_Topic=None):
            # Check if Voltmeter is OK
            if self.OK == False:
                # FIX - Throw error custom error here and cache in Peripherals.On_Message, then remove Voltmeter
                self.Dobby.Log(2, 'Voltmeter-' + self.Name, "Disabeled")

            # Check what command aka payload was recived
            # ? - Returns - 0 = off 1 = on
            if Payload == "?":
                # Publish state            
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Peripherals_Topic("Voltmeter", End=self.Name, State=True),
                        self.Voltage
                    ],
                    Retained=True
                )
            # Toggle - Toggles the Voltmeter state aka on->off or off->on
            else: 
                self.Dobby.Log(2, 'Voltmeter', "Unknown Voltmeter command: " + str(Payload))