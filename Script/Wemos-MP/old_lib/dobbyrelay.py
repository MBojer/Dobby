# import dobbylib as Dobby

import machine
import utime
import ujson


class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Relays
        self.Relays = {}
        # Log Event
        self.Dobby.Log(1, "Relay", "Initializing")
        
        One_Relay_Configured = False

        # Loop over Relays in config
        for Name, Relay_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Relay to the Relay dict
            self.Relays[Name] = self.Relay(self.Dobby, Name, Relay_Config)
            # Check if the Relay is ok
            if self.Relays[Name].Running is False:
                # Issue with Relay detected disabling it
                self.Dobby.Log(2, "Relay/" + Name, "Issue during setup, disabling the Relay")
            else:
                One_Relay_Configured = True
        # Subscribe to Relay topic if at least one Relay was ok
        if One_Relay_Configured is True:
            self.Dobby.MQTT_Subscribe(self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config['Hostname'])

        self.Dobby.Log(0, "Relay", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    # Publish readings is requested to do so - Meant to be placed in dobbylib.On_Message()
    def On_Message(self, Topic, Payload):
        # Check if we need to take action based on topic
        if Topic != self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config['Hostname']:
            return

        # Check if we got both a name and a command
        if len(Payload.split()) < 2:
            self.Dobby.Log(1, 'Relay', "Unknown Relay command: " + str(Payload))
            return

        # Get relay name from payload
        Name = str(Payload.split(" ")[0])
        
        # Check if relay is configured
        ## Relay configured
        if Name not in self.Relays:
            # Log event
            self.Dobby.Log(1, 'Relay', "Unknown Relay: " + Name)
            return
        
        # Split payload to get Relay and command
        Command = str(Payload.split(" ")[1].lower())
        # Get current state
        Current_Relay_State = self.Relays[Name].Pin.value()

        # Check what command was recived
        # ? - Returns - 0 = off 1 = on
        if Command == "?":
            # Publish state            
            self.Dobby.Log_Peripheral(self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config["Hostname"] + "/" + str(Name), Current_Relay_State, True)
        # on - Turns relay on
        elif Command == "on":
            self.Relays[Name].On()

        # off - Turns relay off
        elif Command == "off":
            self.Relays[Name].Off()

        # Toggle - Toggles the relay state aka on->off or off->on
        elif Command == "toggle":
            self.Relays[Name].Toggle()


    # -------------------------------------------------------------------------------------------------------
    # Place this function in dobbylib.loop
    # This is where we check and do stuff if Interrupt_Counter changed
    def Loop(self):
        for Name in self.Relays:
            self.Relays[Name].Loop()



    # -------------------------------------------------------------------------------------------------------
    class Relay:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Running
            ## False = Error/Unconfigured
            ## True = Running
            self.Running = False

            # Name - This will be added to the end of the topic
            self.Name = str(Name)

            # Log Event
            self.Dobby.Log(0, "Relay/" + self.Name, "Initializing")

            # Check if we got the needed config
            for Entry in ['Pin']:
                if Config.get(Entry, None) is None:
                    self.Dobby.Log(2, "Relay/" + Name, "Missing config: " + Entry + " - Unable to initialize Relay")
                    return

            # Convert Wemos Pin to GPIO Pin Number
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            if self.Pin is False:
                self.Dobby.Log(2, "Relay/" + Name, "Invalid Pin Name: " + str(Config['Pin']) + " - Unable to initialize Relay")
                return

            # Flip - If True On (1) is Off (0)
            self.Flip = Config.get('Flip', False)
            if self.Flip is True:
                self.Dobby.Log(0, "Relay/" + Name, "Flip active")

            # Auto - "Time" in sec the relay before state is set to "State"
            self.Auto = Config.get('Auto', None)
            if self.Auto is not None:
                # Generate needed variables
                self.Auto_ms = None
                self.Auto_State = Config['Auto'].get('State', None)
                self.Auto_Time = Config['Auto'].get('Time', None)
                # Missing config check
                if self.Auto_State is None or self.Auto_Time is None:
                    self.Dobby.Log(2, "Relay/" + Name, "Settings missing for Auto - Auto disabeled")
                    # Set auto to none to disable it
                    self.Auto = None
                    # Remove unneded vars
                    del self.Auto_ms
                    del self.Auto_State
                    del self.Auto_Time
                # All ok
                else:
                    # Log event
                    self.Dobby.Log(0, "Relay/" + Name, "Auto: " + str(self.Auto_State) + " After: " + str(self.Auto_Time))
                    

            # Create Machine pin
            self.Pin = machine.Pin(self.Pin, machine.Pin.OUT)

            # Curent State of the relay
            ## Set to current state
            self.State = self.Pin.value()

            # Mark Relay as ok aka enable it
            self.Running = True


        # -------------------------------------------------------------------------------------------------------
        def State_Change_Check(self):
            # Checks if relay state change, if so save the new calue and published state change message to /Relay/<Hostname>/<self.Name>
            # Get state to chack agains
            New_Relay_State = self.Pin.value()

            # Publish state change if state changed
            if self.State != New_Relay_State:
                # Save new state
                self.State = New_Relay_State
                # Publish State changed
                self.Dobby.Log_Peripheral(self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config["Hostname"] + "/" + str(self.Name), self.State, True)


        # -------------------------------------------------------------------------------------------------------
        def On(self):
            # Changed the relay state to on and accounts for flip

            # If Relay is disabled do nothing
            if self.Running is False:
                self.Dobby.Log(2, "Relay/" + self.Name, "Relay disabeled unable to change state to: On")
                return

            # Set relay to on if not on
            ## Check if Flip is configurd
            ### Flip configured
            if self.Flip is True:
                # Check if state already is on
                if self.State != 0:
                    self.Pin.off()

            ### Flip NOT configured
            else:
                # Check if state already is on
                if self.State != 1:
                    self.Pin.on()

            # Check if state changed if so publish
            self.State_Change_Check()


        # -------------------------------------------------------------------------------------------------------
        def Off(self):
            # Changed the relay state to off and accounts for flip

            # If Relay is disabled do nothing
            if self.Running is False:
                self.Dobby.Log(2, "Relay/" + self.Name, "Relay disabeled unable to change state to: Off")
                return

            # Set relay to on if not on
            ## Check if Flip is configurd
            ### Flip configured
            if self.Flip is True:
                # Check if state already is on
                if self.State != 1:
                    self.Pin.on()

            ### Flip NOT configured
            else:
                # Check if state already is on
                if self.State != 0:
                    self.Pin.off()

            # Check if state changed if so publish
            self.State_Change_Check()



        # -------------------------------------------------------------------------------------------------------
        def Toggle(self):
            # Toggle the state of the relay aka if on it turns off and vise versa
            # check if relay is on
            if self.State == 1:
                self.Pin.off()
            else:
                self.Pin.on()

            # Check if state changed if so publish
            self.State_Change_Check()




 
        # -------------------------------------------------------------------------------------------------------
        def Loop(self):
            # If Relay is disabled do nothing
            if self.Running is False:
                return
            # Check if self.Auto is not because past that variables will not exist
            if self.Auto is not None:
                # check if its time to turn off
                if utime.ticks_diff(utime.ticks_ms(), self.Auto_ms) > self.Auto_Time * 1000:
                    # Change relay state
                    ## If State = 0 then turn relay off
                    if self.Auto_State is 0:
                        self.Off()
                    ## If State = 1 then turn relay on
                    else:
                        self.On()
                    # Disable auto
                    self.Auto_ms = None