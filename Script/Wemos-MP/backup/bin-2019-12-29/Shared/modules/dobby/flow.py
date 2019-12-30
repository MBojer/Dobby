import machine
import ujson

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Flow", "Initializing")

        # Loop over Peripherals in config
        for Name, Flow_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Flow to the Flow dict
            self.Peripherals[Name] = self.Flow(self.Dobby, Name, Flow_Config)
            # Check if the Flow is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Flow detected disabling it
                self.Dobby.Log(2, "Flow/" + Name, "Issue during setup, disabling the Flow")
                # Delete the Flow from Peripherals
                del self.Peripherals[Name]
            # Flow ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Flow", End="+"))
        
        # Log event
        self.Dobby.Log(0, "Flow", "Initialization complete")



    # -------------------------------------------------------------------------------------------------------
    def Loop(self):
        # Pass to each sensors loop
        for Name in self.Peripherals:
            # Run loop for each sensor
            self.Peripherals[Name].Loop()

    # -------------------------------------------------------------------------------------------------------
    class Flow:

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

            # Check if we got the needed config
            for Entry in ['Pin', 'Ticks_Liter']:
                if Config.get(Entry, None) is None:
                    self.Dobby.Log(3, "Flow/" + self.Name, "Missing config: " + Entry + " - Unable to initialize")
                    return

            # Reserve the pin
            # Check if pin is valid
            # if fails pin is in use
            try:
                self.Dobby.Pin_Monitor.Reserve(Config['Pin'], "Flow-" + self.Name)
            except self.Dobby.Pin_Monitor.Error:
                # Pin in use unable to configure Flow
                self.Dobby.Log(2, "Flow/" + Name, "Pin in use - Unable to initialize")
                # return so we dont set State to true aka mark the Flow as configured
                return

            # Convert pin Name to GPIO pin
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            # Var to hold the Pin object for this sensor
            self.Pin = machine.Pin(
                self.Pin,
                machine.Pin.IN,
                machine.Pin.PULL_UP
            )

            # Create the interrupt for the pin
            self.Pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.Interrupt_Callback)
            
            # Var to hold ticks from sensor
            self.Ticks = 0

            # How many ticks goes to 1 liter
            self.Ticks_Liter = Config['Ticks_Liter']

            # Store Publish_L if in config
            self.Publish_L = Config.get('Publish_L', False)

            # How many liters we counted since last reboot
            self.Liters = 0
            

            # //////////////////////////////////////// MQTT Message \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
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
                            self.Dobby.Log(2, "DS18B20/" + str(self.Name), "Trigger Message " + str(Entry) + ": Missing " + str(Check) + " - Disabling the '" + str(Entry) + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings in a dict under key message
                        self.MQTT_Message[Entry.lower()] = {'Message': Config['Message'][Entry]}
                        # log event
                        self.Dobby.Log(0, "DS18B20/" + str(self.Name), "Trigger Message " + str(Entry) + " set to Topic: '" + str(self.MQTT_Message[Entry.lower()]['Message']['Topic']) + "' Payload: '" + str(self.MQTT_Message[Entry.lower()]['Message']['Payload']) + "'")

            # Mark the sensor as ok
            self.OK = True


        # -------------------------------------------------------------------------------------------------------
        def Interrupt_Callback(self, Pin):
            # Add one to ticks
            self.Ticks = self.Ticks + 1

        
        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):
            
            # Publish state under bla bla bla/Flow/<Name>/State
            if Command == "?":
                # Publish state should handle it all
                self.Publish_State()

            # Publish state under bla bla bla/Flow/<Name>/State
            elif Command.lower() == "reset":
                # Set ticks and liters to 0
                self.Ticks = 0
                self.Liters = 0
                # Log event
                self.Dobby.Log(2, 'Flow/' + self.Name, "Liter reset")
                

            # # Return current state as json
            # elif Command == "json":
            #     # Publish_json should take care if it all
            #     self.Publish_json()

            else:
                self.Dobby.Log(2, 'Flow/' + self.Name, "Unknown command: " + str(Command))


        # -------------------------------------------------------------------------------------------------------
        def Publish_State(self):
            # Logs current liters to name / state
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic("Flow", End=self.Name, State=True),
                    self.Liters
                ]
            )


        # -------------------------------------------------------------------------------------------------------
        def Loop(self):
            # Checks the interrupt counter

            # check if we got enough ticks for a liter
            if self.Ticks > self.Ticks_Liter:
                # Disable interrupts and save state
                state = machine.disable_irq()
                # Deduct from Ticks
                self.Ticks = self.Ticks - self.Ticks_Liter
                # Enable the interrupts again
                machine.enable_irq(state)
            
                # Add 1 liter to self.Liters
                self.Liters = self.Liters + 1

                # Now lets check whats actions we need to take if any
                # Publish message if self.Publish_L is true
                if self.Publish_L == True:
                    # Publich current liters to state topic
                    self.Publish_State()

                # Check if we need to send a message
                # MQTT_Message
                for Key in self.MQTT_Message:
                    # Skip active
                    if Key == 'Active':
                        continue
                    # Check if Liters is within message range
                    # Key should contain "<n1>-<n2>"
                    # n1 = Low Value 
                    # n2 = High Value
                    # Action_Check will then check if self.Liters is between n1 and n2
                    # Split the key at - to get n1 and n2
                    Key_Split = Key.split("-")

                    if float(Key_Split[0]) <= self.Liters <= float(Key_Split[1]):
                        # Check if we already send the message fir this range
                        if self.MQTT_Message.get('Active', None) != Key:
                            # Send the message
                            self.Dobby.Log_Peripheral(self.MQTT_Message[Key]['Message'])
                            # Note that we send the message
                            self.MQTT_Message['Active'] = Key