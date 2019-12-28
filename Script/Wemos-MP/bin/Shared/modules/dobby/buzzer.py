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
        self.Dobby.Log(1, "Buzzer", "Initializing")

        # Loop over Peripherals in config
        for Name, Buzzer_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Buzzer to the Buzzer dict
            self.Peripherals[Name] = self.Buzzer(self.Dobby, self, Name, Buzzer_Config)
            # Check if the Buzzer is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Buzzer detected disabling it
                self.Dobby.Log(2, "Buzzer/" + Name, "Issue during setup, disabling the Buzzer")
            # Buzzer ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Buzzer", End="+"))
        
        # Log event
        self.Dobby.Log(0, "Buzzer", "Initialization complete")

    # -------------------------------------------------------------------------------------------------------
    def Check_Buzz_Info(self, Buzz_Info):
        # Check buzz info
        try:
            Number_Of = Buzz_Info[0]
            Buzz_For = Buzz_Info[1]
            Delay = Buzz_Info[2]
        except IndexError:
            # Log error
            self.Dobby.Log(2, 'Buzzer/' + self.Name, "Incorrect buzz info: " + str(Buzz_Info))
            # return so we dont restart the timer aka run below code
            return False
        else:
            return True


    # -------------------------------------------------------------------------------------------------------
    class Buzzer:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Main, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Referance Buzzer aka main script
            self.Main = Main

            # OK
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False

            # Name - This will be added to the end of the topic
            self.Name = str(Name)

            # Log Event
            self.Dobby.Log(0, "Buzzer/" + self.Name, "Initializing")

            # Check if we got the needed config
            try:
                self.Dobby.Config_Check("Buzzer", ['Pin'], Config)
            except self.Dobby.Module_Error:
                return

            # Get pin name from config
            self.Pin = Config['Pin']

            # Var to indicate if we currently have a buzz active or not
            self.Buzzing = False

            # How long to wait after one buzz before starting the next
            self.Pause = "3s"

            # List to hold buzzes we get when already buzzing
            self.Buzz_Queue = []

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(self.Pin, "Buzzer-" + self.Name)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure Buzzer
                self.Dobby.Log(3, "Buzzer/" + Name, "Unable to take ownership of Pin: " + self.Pin + " - Unable to initialize")
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
            # 4 = Argument
            # Note auto is active by creating <state> key with referance to timer in Auto dict
            self.Timer = self.Dobby.Sys_Modules['timer'].Add(
                "Buzzer-" + self.Name,
                "0.5s",
                self.Buzz,
                Logging=False
            )
            # Start the timer so we buzz 3 times when configured so we can see if we work
            # buzzer is on for 0.5s and pause between is 
            self.Start(1, "0.1s", "0.25s")
            # Mark as ok
            self.OK = True


        # -------------------------------------------------------------------------------------------------------
        def Start(self, Number_Of, Buzz_For, Delay):
                        
            if self.Buzzing == False:
                # Log error
                self.Dobby.Log(0, 'Buzzer/' + self.Name, "Buzzing - Number of: " + str(Number_Of) + " Buzz for: " + str(Buzz_For) + " Delay between: " + str(Delay))
                # Set self.Buzzing = True so we dont trigger this message again
                self.Buzzing = True
                # Start the timer imidiatly
                self.Timer.Start(Timeout_ms=0, Argument=[Number_Of, Buzz_For, Delay], Callback=self.Buzz)
            
            # We are currently buzzing so add to Buzz_Queue
            else:
                # Log error
                self.Dobby.Log(0, 'Buzzer/' + self.Name, "Added buzz to queue - Number of: " + str(Number_Of) + " Buzz for: " + str(Buzz_For) + " Delay between: " + str(Delay))
                # Add to queue
                self.Buzz_Queue.append([Number_Of, Buzz_For, Delay])


        # -------------------------------------------------------------------------------------------------------
        def Buzzer_Off(self):
            # Turns off the buzzer
            # meant to be triggered when buzzing is compleate
            self.Pin.off()
            # let reset self.Buzzing since we are done
            self.Buzzing = False
            
            # Check if we got a buzz in the queue
            if len(self.Buzz_Queue) != 0:
                # Start the timer and pass buzz info
                # remember to used self.Pause as Timeout
                self.Timer.Start(Timeout_ms=self.Pause, Argument=self.Buzz_Queue.pop(), Callback=self.Buzz)



        # -------------------------------------------------------------------------------------------------------
        def Buzz(self, Buzz_Info):
            # Check buzz info
            try:
                Buzz_Info[0]
                Buzz_Info[1]
                Buzz_Info[2]
            except IndexError:
                # Log error
                self.Dobby.Log(2, 'Buzzer/' + self.Name, "Incorrect buzz info: " + str(Buzz_Info))
                # Turn off the buzzer in case its on
                self.Pin.off()
                # return so we dont restart the timer aka run below code
                return


        # -------------------------------------------------------------------------------------------------------
        def Buzz(self, Buzz_Info):

            if self.Main.Check_Buzz_Info(Buzz_Info) == False:
                return

            Number_Of = int(Buzz_Info[0])
            Buzz_For = Buzz_Info[1]
            Delay = Buzz_Info[2]

            # Start with checking if pin is on, if so turn off and start timer
            # Buzzer is on
            if self.Pin.value() == 1:
                # turn pin off
                self.Pin.off()
                # start the timer with delay as timeout
                self.Timer.Start(Timeout_ms=Delay)


            # Buzzer is off
            else:
                # Turn the pin on the make noice
                self.Pin.on()

                # Subtract one from Number_Of
                Number_Of = Number_Of - 1

                # check if we got to 0
                if Number_Of == 0:
                    # start timer with Callback set to self.Buzzer_Off
                    # Remember to clear Argument and change Timeout_ms
                    self.Timer.Start(Argument="", Timeout_ms=Buzz_For, Callback=self.Buzzer_Off)

                # Not done buzzing yet
                else:
                    # start the timer with Buzz_For as timeout
                    # remember to pass Number_Of, Buzz_For, Delay as a list since Number_Of changed
                    self.Timer.Start(Timeout_ms=Buzz_For, Argument=[Number_Of, Buzz_For, Delay], Callback=self.Buzz)


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Payload, Sub_Topic=None):
            # Check if Buzzer is OK
            if self.OK == False:
                # FIX - Throw error custom error here and cache in Peripherals.On_Message, then remove Buzzer
                self.Dobby.Log(2, 'Buzzer/' + self.Name, "Disabeled")

            # Check what command aka payload was recived
            if Payload.lower().startswith('buzz ') == True:

                # Split payload to get 
                Payload = Payload.split(" ")
                try:
                    # 0 = "buzz"
                    Number_Of = Payload[1]
                    Buzz_For = Payload[2]
                    Delay = Payload[3]
                except IndexError:
                    self.Dobby.Log(2, 'Buzzer/' + self.Name, "Invalud buzz info provided")
                    return

                if self.Main.Check_Buzz_Info([Number_Of, Buzz_For, Delay]) == False:
                    self.Dobby.Log(2, 'Buzzer/' + self.Name, "Invalud buzz info provided")
                    return


                # Pass to self.Start
                self.Start(Number_Of, Buzz_For, Delay)

            # Unknown command
            else: 
                self.Dobby.Log(2, 'Buzzer', "Unknown Buzzer command: " + str(Payload))