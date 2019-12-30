#!/usr/bin/python3

import utime
import machine

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Indicator", "Initializing")

        # Loop over Peripherals in config
        for Name, Indicator_Config in Config.items():
            # Make sure Name is a string
            self.Add(Name, Indicator_Config)
        # Log event
        self.Dobby.Log(0, "Indicator", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    def Add(self, Name, Config):

        # Make sure Name is a string
        Name = str(Name)
        # Add the Indicator to the Indicator dict
        self.Peripherals[Name] = self.Indicator(self.Dobby, self, Name, Config)

        # Check if the Indicator is ok
        if self.Peripherals[Name].OK is False:
            # Issue with Indicator detected disabling it
            self.Dobby.Log(2, "Indicator/" + Name, "Issue during setup, removing the Indicator")
            # remove the name from Peripherals
            del self.Peripherals[Name]
        # Indicator ok
        else:
            # Subscribe to topic
            self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Indicator", End="+"))


    # -------------------------------------------------------------------------------------------------------
    class Indicator:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Main, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Referance Indicator aka main script
            self.Main = Main

            # OK
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False

            # Name - This will be added to the end of the topic
            self.Name = str(Name)

            # Log Event
            self.Dobby.Log(0, "Indicator/" + self.Name, "Initializing")

            # Check if we got the needed config
            try:
                self.Dobby.Config_Check("Indicator", ['Pin'], Config)
            except self.Dobby.Module_Error:
                return

            # Get pin name from config
            self.Pin = Config['Pin']

            # How long to wait after one Indicator before starting the next
            self.Pause = "1.5s"

            # List to hold Indicators we get when already Active
            self.Indicator_Queue = []

            # Dict holding active indications
            self.Active = {}
            # List holding what order to do indications from self.Active
            self.Active_Order = []

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(self.Pin, "Indicator-" + self.Name)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure Indicator
                self.Dobby.Log(3, "Indicator/" + Name, "Unable to take ownership of Pin: " + self.Pin + " - Unable to initialize")
                # return so we dont set State to true aka mark the Voltmeter as configured
                return

            # No need to try since we know is a valid pin since try above passed
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            # create the output pin object
            self.Pin = machine.Pin(self.Pin, machine.Pin.OUT)

            # Check if the dobby.timer module is loaded
            self.Dobby.Timer_Init()
            # Add a timer
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # Note auto is active by creating <state> key with referance to timer in Auto dict
            self.Timer = self.Dobby.Sys_Modules['timer'].Add(
                "Indicator-" + self.Name,
                "0.5s",
                self.Ping,
                Logging=False
            )

            # Mark as ok
            self.OK = True
            
            # Start the timer so we Indicator 3 times when configured so we can see if we work
            # Indicator is on for 0.5s and pause between 1s 
            self.Add('Init', 3, "0.1s", "0.25s")


        # -------------------------------------------------------------------------------------------------------
        def Add(self, Name, Left, On_For, Delay, Repeat=False):
            # dont add duplicates just make sure the timer is running if duplicate
            if Name not in self.Active.keys():
                # Creat dict to hold info in self.Active
                self.Active[Name] = {}
                # Append to self.Active_Order so we know when to run the indication
                self.Active_Order.append(Name)

                # add info
                self.Active[Name]['Left'] = Left
                self.Active[Name]['On_For'] = On_For
                self.Active[Name]['Delay'] = Delay
                self.Active[Name]['Repeat'] = Repeat

                # Add Reset_To if repeat is true so we know how many blinks to do when resetting
                if Repeat == True:
                    self.Active[Name]['Reset_To'] = Left

                # Log event
                self.Dobby.Log(0, 'Indicator/' + self.Name, "Added Indicator " + str(Name) + " - Number of: " + str(Left) + " On for: " + str(On_For) + " Delay between: " + str(Delay) + " Repeat: " + str(Repeat))

            # Check if the timer if running if not start it
            if self.Timer.Running == False:
                # Start the timer with timeout 0 so we trigger asap
                self.Timer.Start(Timeout_ms=0, Callback=self.Ping)


        # -------------------------------------------------------------------------------------------------------
        def Remove(self, Name):

            Removed = False

            if self.Active_Order != []:
                # if name currently active then set repeat to false to we dont reset when done
                if self.Active_Order[0] == Name:
                    self.Active[Name]['Repeat'] = False
                    # return should then take care of the rest
                    Removed = True
                    
                # if not active del info dict from self.Active 
                try:
                    del self.Active[Name]
                except KeyError:
                    pass
                else:
                    Removed = True
                    
                # remove instances name from active order
                try:
                    self.Active_Order.remove(Name)
                except ValueError:
                    pass
                else:
                    Removed = True
            
            # Log event
            if Removed == True:
                self.Dobby.Log(0, 'Indicator/' + self.Name, "Removed: " + str(Name))
            else:
                self.Dobby.Log(0, 'Indicator/' + self.Name, str(Name) + " not added")


        # -------------------------------------------------------------------------------------------------------
        def End(self):
            # Turns off the Indicator
            # meant to be triggered when Indicator is compleate
            self.Pin.off()

            if self.Active == {}:
                return

            # Check if repeat is not false if so its the number we need to reset Left to
            elif self.Active[self.Active_Order[0]]['Repeat'] != False:
                # add to back to self.Active_Order
                self.Active_Order.append(self.Active_Order[0])
                # Reset Left, number is in ['Repeat']
                self.Active[self.Active_Order[0]]['Left'] = self.Active[self.Active_Order[0]]['Reset_To']

            # Repeat is false so remove from active and active order
            else:
                # Remove entry from active dict
                del self.Active[self.Active_Order[0]]

            # remove first entry from Active_Order
            # required for both if and else above
            self.Active_Order.pop(0)

            if self.Active != {}:
                # Start timer again with self.Pause as timeout
                self.Timer.Start(Timeout_ms=self.Pause, Callback=self.Ping)


        # -------------------------------------------------------------------------------------------------------
        def Ping(self):

            if self.Active == {}:
                return

            # Start with checking if pin is on, if so turn off and start timer
            # Indicator is on
            if self.Pin.value() == 1:
                # turn pin off
                self.Pin.off()
                # start the timer with delay as timeout
                self.Timer.Start(Timeout_ms=self.Active[self.Active_Order[0]]['Delay'])


            # Indicator is off
            else:
                # Turn the pin on the make noice
                self.Pin.on()

                # Subtract one from Left
                self.Active[self.Active_Order[0]]['Left'] = self.Active[self.Active_Order[0]]['Left'] - 1

                # check if we got to 0 or less
                if self.Active[self.Active_Order[0]]['Left'] <= 0:
                    # Start timer setting Callback to end since we got to last indication
                    # end will start next if needed
                    self.Timer.Start(Callback=self.End, Timeout_ms=self.Active[self.Active_Order[0]]['On_For'])

                # Not done yet
                else:
                    # start the timer with On_For as timeout
                    # remember to pass Left, On_For, Delay as a list since Left changed
                    self.Timer.Start(Callback=self.Ping, Timeout_ms=self.Active[self.Active_Order[0]]['On_For'])


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Payload, Sub_Topic=None):
            # Check if Indicator is OK
            if self.OK == False:
                # FIX - Throw error custom error here and cache in Peripherals.On_Message, then remove Indicator
                self.Dobby.Log(2, 'Indicator/' + self.Name, "Disabeled")

            # Check what command aka payload was recived
            if Payload.lower().startswith('add ') == True:

                # Split payload to get 
                Payload = Payload.split(" ")
                try:
                    # 0 = "add "
                    Left = Payload[1]
                    On_For = Payload[2]
                    Delay = Payload[3]
                except IndexError:  
                    self.Dobby.Log(2, 'Indicator/' + self.Name, "Invalud Indicator info provided")
                    return

                # Pass to self.Start
                self.Start(Left, On_For, Delay)

            # Unknown command
            else: 
                self.Dobby.Log(2, 'Indicator', "Unknown Indicator command: " + str(Payload))