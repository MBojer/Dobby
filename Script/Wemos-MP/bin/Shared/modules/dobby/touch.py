#!/usr/bin/python3

import machine
import utime
import ujson


class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Touch_Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Touch", "Initializing")
        
        # Loop over Peripherals in config
        for Name, Config in Touch_Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Touch to the Touch dict
            self.Peripherals[Name] = self.Touch(self.Dobby, Name, Config)
            # Check if the Touch is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Touch detected disabling it
                self.Dobby.Log(2, "Touch/" + Name, "Issue during setup, disabling the Touch")
            else:
                # Subscribe to Touch topic if at least one Touch was ok
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Touch", End="+"))
            
        self.Dobby.Log(0, "Touch", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    # Place this function in dobbylib.loop
    # This is where we check and do stuff if Interrupt_Counter changed
    def Loop(self):
        for Name in self.Peripherals:
            self.Peripherals[Name].Loop()


    # -------------------------------------------------------------------------------------------------------
    class Touch:

        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Variable to indicate of the configuration of the Touch went ok
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False
            
            # Name - Referance name
            self.Name = str(Name)

            # Log Event
            self.Dobby.Log(0, "Touch/" + self.Name, "Initializing")

            # Check if we got the needed config
            for Entry in ['Pin']:
                if Config.get(Entry, None) == None:
                    self.Dobby.Log(2, "Touch/" + Name, "Missing config: " + Entry + " - Unable to initialize Touch")
                    return

            # Save pin name to self.Pin
            self.Pin = Config['Pin']

            # Reset the pin
            try:
                self.Dobby.Pin_Monitor.Reserve(self.Pin, "Touch-" + self.Name)
            except self.Dobby.Pin_Monitor.Error as e:
                # Pin in use unable to configure Touch
                self.Dobby.Log(2, "Touch/" + Name, "Pin in use - Unable to initialize Touch")
                # return so we dont set State to true aka mark the Touch as configured
                return

            # Convert Wemos Pin to GPIO Pin Number
            # its a valid pin if we get to herer, check done during reserve
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            # if we get a value error its not a pin we can use for touch
            # Create TouchPad pin
            try:
                self.Pin = machine.TouchPad(machine.Pin(self.Pin))
            except ValueError:
                # Pin not a touch pin unable to configure Touch
                self.Dobby.Log(2, "Touch/" + Name, "Pin not usable for touch - Unable to initialize Touch")
                # return so we dont set State to true aka mark the Touch as configured
                return
            
            # Save trigger at if given
            # default to 50
            self.Trigger_At = Config.get('Trigger_At', 50)
            # Reset to default if we didnt get int
            if type(self.Trigger_At) != int:
                self.Trigger_At = 50

            # Log event
            self.Dobby.Log(0, "Touch/" + self.Name, "Trigger at set to " + str(self.Trigger_At))
            
            self.NoAction = 750
            self.Last_Action = utime.ticks_ms()

            # MQTT Message
            self.MQTT_Message = {}
            if Config.get("Message", None) != None:
                # For loop over entries in Messages if any
                for Entry in Config['Message']:
                    # Bool value to check if either topic or payload failed
                    Failure = False
                    # Check if we got both Topic and Payload
                    for Check in ['Topic', 'Payload']:
                        if Failure == True:
                            continue
                        # Missing topic or payload
                        if Config['Message'][Entry].get(Check, None) == None:
                            # Log event
                            self.Dobby.Log(2, "Touch/" + self.Name, "Trigger Message " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.MQTT_Message[Entry.lower()] = Config['Message'][Entry]
                        # log event
                        self.Dobby.Log(0, "Touch/" + self.Name, "Trigger Message " + Entry + " set to Topic: '" + self.MQTT_Message[Entry.lower()]['Topic'] + "' Payload: '" + self.MQTT_Message[Entry.lower()]['Payload'] + "'")
            

            # //////////////////////////////////////// Relay \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            self.Relay = {}
            if Config.get("Relay", None) != None:
                # For loop over On/Off to check for both messages
                for Entry in Config['Relay']:
                    # Bool value to check if either topic or payload failed
                    Failure = False
                    # Check if we got both Topic and Payload
                    for Check in ['Name', 'State']:
                        if Failure == True:
                            continue
                        # Missing topic or payload
                        if Config['Relay'][Entry].get(Check, None) == None:
                            # Log event
                            self.Dobby.Log(2, "Touch/" + self.Name, "Trigger Relay " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.Relay[Entry.lower()] = Config['Relay'][Entry]
                        # log event
                        self.Dobby.Log(
                            0,
                            "Touch/" + self.Name,
                            Entry + ": Trigger Relay: '" + self.Relay[Entry.lower()]['Name'] + "' State: '" + self.Relay[Entry.lower()]['State'] + "'"
                            )


            # //////////////////////////////////////// Dimmer \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            self.Dimmer = {}
            if Config.get("Dimmer", None) != None:
                # For loop over On/Off to check for both messages
                for Entry in Config['Dimmer']:
                    # Bool value to check if either topic or payload failed
                    Failure = False
                    # Check if we got both Topic and Payload
                    for Check in ['Name', 'State']:
                        if Failure == True:
                            continue
                        # Missing topic or payload
                        if Config['Dimmer'][Entry].get(Check, None) == None:
                            # Log event
                            self.Dobby.Log(2, "Touch/" + self.Name, "Trigger Dimmer " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.Dimmer[Entry.lower()] = Config['Dimmer'][Entry]
                        # log event
                        self.Dobby.Log(
                            0,
                            "Touch/" + self.Name,
                            Entry + ": Trigger Dimmer: '" + self.Dimmer[Entry.lower()]['Name'] + "' State: '" + str(self.Dimmer[Entry.lower()]['State']) + "'"
                            )

            # Mark Touch as ok aka enable it
            self.OK = True

            # What the reading should be when we are not getting touched
            self.High = 0
            # lets read 10 times over 100ms and get the Highest values
            for i in range(10):
                self.High = max(self.Pin.read(), self.High)
                # only sleep during the first 9 readings
                if i != 9:
                    # Sleep for 10 ms
                    utime.sleep_ms(10)

            # State of Touch - On/OFF aka True/False
            self.State = self.Get_State()

            # Log event
            self.Dobby.Log(0, "Touch/" + self.Name, "Initialization complete")



        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            
            # pusblises current state aka 1 or 0
            if Command == "?":
                # Build Topic
                Topic = self.Dobby.Peripherals_Topic("Touch", End=self.Name, State=True)
                # Log state
                self.Dobby.Log_Peripheral([Topic, self.State], True)
                    
            # Return current state as json
            elif Command == "json":
                # Publish_json should take care if it all
                self.Publish_json()

            else:
                self.Dobby.Log(2, 'Touch/' + self.Name, "Unknown command: " + str(Command))



        # -------------------------------------------------------------------------------------------------------
        def Publish_json(self):
            # Publish json to Touch/<Name>/json/State
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic("Touch", End=self.Name + '/json', State=True),
                    self.Get_json()
                ]
            )
        
        # -------------------------------------------------------------------------------------------------------
        def Get_json(self, Reset=False):

            Return_dict = {}
            Return_dict['Raw'] = self.Pin.read()
            Return_dict['State'] = self.State
            Return_dict['Trigger At'] = self.Trigger_At
                
            return ujson.dumps(Return_dict)
         

        # -------------------------------------------------------------------------------------------------------
        def Get_State(self):
            # Returns the current state of the Touch in 0 = off 1 = on            
            if self.High - self.Pin.read() > self.Trigger_At:
                return "on"
            else:
                return "off"


        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, State):

            # Log time for state change
            self.Last_Action = utime.ticks_ms()

            # Build Topic
            Topic = self.Dobby.Peripherals_Topic("Touch", End=self.Name, State=True)

            # Log Touch was pressed
            self.Dobby.Log_Peripheral([Topic, State], True)

            # Take action as per specified
            ## Message
            if self.MQTT_Message != {}:
                try:
                    self.Dobby.Log_Peripheral(self.MQTT_Message[State])
                except KeyError:
                    pass

            ## Relay
            if self.Relay != {}:
                # Trigger the local relay with the provided settings
                # We need a try here in case on or off is not set
                try:
                    self.Dobby.Modules['relay'].Peripherals[self.Relay[State]['Name']].Set_State(self.Relay[State]['State'])
                except KeyError:
                    pass

            ## Dimmer
            if self.Dimmer != {}:
                # Trigger the local Dimmer with the provided settings
                # We need a try here in case on or off is not set
                try:
                    self.Dobby.Modules['dimmer'].Peripherals[self.Dimmer[State]['Name']].Set_Percent(self.Dimmer[State]['State'])
                except KeyError:
                    pass

            # Save the current state to self.State
            self.State = State


        # -------------------------------------------------------------------------------------------------------
        def Loop(self):
            # If Touch is disabled do nothing
            if self.OK == False:
                return

            # Store current state in variable
            Current_State = self.Get_State()

            if utime.ticks_diff(utime.ticks_ms(), self.Last_Action) < self.NoAction:
                return

            # Check if state changed
            if Current_State != self.State:
                # state changed so will pass new state to set state
                self.Set_State(Current_State)