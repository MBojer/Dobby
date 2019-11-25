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

        # Loop over Relays in config
        for Name, Relay_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Relay to the Relay dict
            self.Relays[Name] = self.Relay(self.Dobby, Name, Relay_Config)
            # Check if the Relay is ok
            if self.Relays[Name].OK is False:
                # Issue with Relay detected disabling it
                self.Dobby.Log(2, "Relay/" + Name, "Issue during setup, disabling the Relay")
            # Relay ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config['Hostname'])
        
        # Log event
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
        
        # Pass to Relay
        # Split payload to get command
        self.Relays[Name].On_Message(str(Payload.split(" ")[1]))
        
        
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

            # OK
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False

            # Name - This will be added to the end of the topic
            self.Name = str(Name)

            # Log Event
            self.Dobby.Log(0, "Relay/" + self.Name, "Initializing")

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
            if self.Dobby.Pin_Monitor.Reserve(self.Pin, "Relay-" + self.Name) == False:
                self.Dobby.Log(3, "Relay/" + Name, "Unable to take ownership of Pin: " + self.Pin + " - Unable to initialize Relay")
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

 
            # Auto
            self.Auto = {}
            # Check if auto is set in config
            if Config.get('Auto', None) != None:
                # For loop over On,Off
                for Entry in ['On', 'Off']:
                    # Check if config is present
                    if Config['Auto'].get(Entry, None) != None:
                        # Spawn a create a Relay_Auto instanace
                        # 1 = On/Off in boot, remember to take flip into account. Use self.Get_State to do this
                        # 2 = Auto how long to wait in ms
                        # 3 = Reference to Relay self.On of self.Off()
                        # Use the bool value of on/off as key
                        # Remember to no need to filp falue since we are referring to name aka on off
                        self.Auto[Entry.lower()] = self.Relay_Auto(
                            self.Get_State(Entry),
                            Config['Auto'][Entry],
                            self.On() if Entry.lower() == 'on' else self.Off()
                        )
                        # Log event
                        self.Dobby.Log(0, "Relay/" + self.Name, Entry + " Auto set to: " + str(Config['Auto'][Entry]) + " ms")


            # Delay
            self.Delay = {}
            # Check if we for is set in config
            if Config.get('Delay', None) != None:
                # For loop over On,Off
                for Entry in ['On', 'Off']:
                    # Check if config is present
                    if Config['Delay'].get(Entry, None) != None:
                        # Spawn a create a Relay_Delay instanace
                        # 1 = On/Off in boot, remember to take flip into account. Use self.Get_State to do this
                        # 2 = Delay how long to wait in ms
                        # 3 = Reference to Relay self.On of self.Off()
                        # Use the bool value of on/off as key
                        # Remember to no need to filp falue since we are referring to name akak on off
                        self.Delay[Entry.lower()] = self.Relay_Delay(
                            self.Get_State(Entry),
                            Config['Delay'][Entry],
                            self.On() if Entry.lower() == 'on' else self.Off()
                        )
                        # Log event
                        self.Dobby.Log(0, "Relay/" + self.Name, Entry + " Delay set to: " + str(Config['Delay'][Entry]) + " ms")


            # Create Machine pin
            self.Pin = machine.Pin(self.Pin, machine.Pin.OUT)

            # Mark Relay as ok aka enable it

            # Needs to be done before setting Init state
            self.OK = True
            
            # Set the relay to Init state
            if Config.get('Init', None) == None:
                # Default to "Off"
                self.Off()
            else:
                if Config['Init'].lower() == 'on':
                    self.On()
                elif Config['Init'].lower() == 'off':
                    self.Off()
                else:
                    # Unknown Init state Default to off
                    self.Dobby.Log(2, "Relay/" + Name, "Invalid Init State: " + str(Config['Init']) + " - Setting relay Init state to: Off")
                    self.Off()


        def On_Message(self, Command):
            # Check if relay is OK
            if self.OK == False:
                # FIX - Throw error custom error here and cache in Relays.On_Message, then remove relay
                self.Dobby.Log(2, 'Relay-' + self.Name, "Disabeled")

            # Check what command was recived
            # ? - Returns - 0 = off 1 = on
            if Command == "?":
                # Publish state            
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config["Hostname"] + "/" + str(self.Name),
                        self.Get_State(None, True)
                    ]
                )
            # on - Turns relay on
            elif str(Command).lower() in ["on", "1"]:
                self.On()

            # off - Turns relay off
            elif str(Command).lower() in ["off", "0"]:
                self.Off()

            # Toggle - Toggles the relay state aka on->off or off->on
            elif str(Command).lower() in ["toggle", "2"]:
                self.Toggle()

            # Toggle - Toggles the relay state aka on->off or off->on
            else: 
                self.Dobby.Log(2, 'Relay', "Unknown Relay command: " + str(Command))



        # -------------------------------------------------------------------------------------------------------
        def Get_State(self, Input=None, Return_String=False):
            #  Input=None: Returns the relays current state taking into account Flip
            #  Input=On: Bool value of On taking flip into account
            #  Input=Off: Bool value of Off taking flip into account

            # If Input is not none we need to return the bool value of the string given
            # taking flip into account
            if Input != None:
                # Get bool value of Input
                Input = self.Dobby.OnOff_To_Bool(Input)
                # if we got none the Input provided was not valid, pass none back to what ever triggered state
                if Input == None:
                    return None
                # Check if flip is active
                if self.Flip == True:
                    return not Input
                # Flip not active
                else:
                    return Input
                    
            # Input is == so user wants the current relay state
            # Check if output is flipped
            if self.Flip == True:
                Current_State = bool(not self.Pin.value())
            else:
                Current_State = bool(self.Pin.value())
            
            # Check if we need to return bool or string
            if Return_String == True:
                if Current_State == True:
                    Current_State = "On"
                else:
                    Current_State = "Off"

            # Return either bool or str
            return Current_State
        

        # -------------------------------------------------------------------------------------------------------
        def State_Change_Check(self, Log_Change):
            # Checks if relay state change, if so save the new calue and published state change message to /Relay/<Hostname>/<self.Name>
            # Get state to chack agains
            New_Relay_State = self.Get_State()

            # Publish state change if state changed
            if self.Pin_State != New_Relay_State:
                # Save pin state
                self.Pin_State = New_Relay_State
                # Check if we need to log the event
                if Log_Change == True:
                    # Publish State changed
                    self.Dobby.Log_Peripheral(
                        [
                            self.Dobby.Config['System_Header'] + "/Relay/" + self.Dobby.Config["Hostname"] + "/" + str(self.Name),
                            self.Get_State(False)
                        ]
                    )


        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, New_State, Log_Change=True):
            # Changes state of relay.
            # Options is On/1 Off/0 Toggle/2

            # if we got a string convert to int
            if isinstance(New_State, str) == True:
                if New_State.lower() == 'off':
                    New_State = 0 
                elif New_State.lower() == 'on':
                    New_State = 1 
                elif New_State.lower() == 'toggle':
                    New_State = 2 
                else:
                    self.Dobby.Log(2, "Relay/" + self.Name, "Unknown state provided: " + str(New_State))
                    # Return false because we failed
                    return False

            # Since New_State is not a string check if its 0,1 or 2, if not its a incorrect state we got
            elif int(New_State) not in [0, 1, 2]:
                self.Dobby.Log(2, "Relay/" + self.Name, "Unknown state provided: " + str(New_State))
                # Return false because we failed
                return False


            # Check if current state == requested state
            if self.Pin_State == New_State:
                return

            # Flip value if 2 is selected aka toggle
            ## We need to check whats state the relay is in so we can trigger the oposite function
            ## to get delay taken into account
            if New_State == 2:
                # If on trigger off and vise versa
                if self.Get_State(Return_String=True) == "On":
                    self._Off()
                else:
                    self._On()

            # Turn on
            elif New_State == 1:
                self._On()

            # Turn off
            elif New_State == 0:
                self._Off()

            return True


        # -------------------------------------------------------------------------------------------------------
        def On(self):
            # Just trigger self.Set_State it will handle the rest
            self.Set_State('On')


        # -------------------------------------------------------------------------------------------------------
        def _On(self, Log_Change=True, Ignore_Delay=False):
            # Changed the relay state to on and accounts for flip

            # If Relay is disabled do nothing
            if self.OK == False:
                self.Dobby.Log(2, "Relay/" + self.Name, "Relay disabeled unable to change state to: On")
                return

            # If delay is not configured or we were told to ignore it
            # aka when the timeout wants to change state
            if Ignore_Delay == True or self.Delay == {}:
                # stop delay if present
                if self.Delay.get('on', None) != None:
                    self.Delay['on'].Stop()
                # stop Auto if present
                if self.Auto.get('on', None) != None:
                    self.Auto['on'].Stop()

            # Not ignoreing delay so start delay or auto
            else:
                if self.Auto.get('on', None) != None:
                    self.Auto['on'].Start()
                if self.Delay.get('on', None) != None:
                    self.Delay['on'].Start()

                

            # Check if state changed if so publish
            self.State_Change_Check(Log_Change)




        # -------------------------------------------------------------------------------------------------------
        def Off(self, Log_Change=True, Ignore_Delay=False):
            # Just trigger self.Set_State it will handle the rest
            self.Set_State('Off')


        # -------------------------------------------------------------------------------------------------------
        def _Off(self, Log_Change=True, Ignore_Delay=False):
            # Changed the relay state to off and accounts for flip

            # If Relay is disabled do nothing
            if self.OK == False:
                self.Dobby.Log(2, "Relay/" + self.Name, "Relay disabeled unable to change state to: Off")
                return

                
            if Ignore_Delay == True or self.Delay == {}:
                # Change state before logging
                self.Set_State(0, True)
                # Log state after changing
                self.State_Change_Check(Log_Change)
                # stop Auto if present
                if self.Auto.get('off', None) != None:
                    self.Auto['off'].Stop()
                # stop delay if present
                if self.Delay.get('off', None) != None:
                    self.Delay['off'].Stop()
            else:
                if self.Auto.get('off', None) != None:
                    self.Auto['off'].Start()
                if self.Delay.get('off', None) != None:
                    self.Delay['off'].Start()

        # -------------------------------------------------------------------------------------------------------
        def Toggle(self, Log_Change=True):
            # If Relay is disabled do nothing
            if self.OK == False:
                self.Dobby.Log(2, "Relay/" + self.Name, "Relay disabeled unable to toggle state")
                return
            # Toggle the state of the relay aka if on it turns off and vise versa
            self.Set_State(not self.Get_State())
            # Log state after changing
            self.State_Change_Check(Log_Change)
 
        # -------------------------------------------------------------------------------------------------------
        def Loop(self):
            # If Relay is disabled do nothing
            if self.OK == False:
                return
        
            # Store current state in variable
            Current_State = self.Get_State()

            # Run loop for each instance in self.Auto if any
            for Entry in self.Auto:
                # Run the loop in a if statement and return if we get true
                # true indicate Auto.loop changed state
                if self.Auto[Entry].Loop(Current_State) is True:
                    return
            
            # Run loop for each instance in self.Delay if any
            for Entry in self.Delay:
                # Run the loop in a if statement and return if we get true
                # true indicate Delay.loop changed state
                if self.Delay[Entry].Loop(Current_State) is True:
                    return


        # -------------------------------------------------------------------------------------------------------
        class Relay_Delay:
        
            # -------------------------------------------------------------------------------------------------------
            def __init__(self, Target_State, For_ms, Change_State_Referance):
                # Referance to Change_State so we can change state from here
                self.Change_State = Change_State_Referance
                ## Target_State aka pin on or off - triggers events if == to current state
                # Remember to not the Target state to get it to match with the Relay state
                self.Target_State = Target_State
                ## How long the Relay needs to be in a given state before state change will be triggered
                self.For_ms = For_ms
                ## When last state change took place
                ### Will we set to None when Relay changes to oposite state of Pin_State
                self.Delay_Last = None
                ## Starts as false so we dont trigger before a state changed happens
                self.Active = False


            def Stop(self):
                # Set self.Active to False to indicate we have a running timeout
                self.Active = False
                self.Delay_Last = None
            

            def Start(self):
                # Set self.Delay_Last to ticks_ms so we can do diff on it later
                self.Delay_Last = utime.ticks_ms()
                # Set self.Active to true to indicate we have a running timeout
                self.Active = True
            

            def Loop(self, Current_State):
                # Place in Relay.loop() and pass current pin state
                # Checks if its time to trigger events if not notes ticks to compate against

                # if self.Active is true then we are waiting for a timeout
                if self.Active == True:
                    # Check if we timed out
                    if utime.ticks_diff(utime.ticks_ms(), self.Delay_Last) > self.For_ms:
                        # Check if current state == Target_State
                        if Current_State == self.Target_State:
                            # Change state since Relay is still in target state after timeout
                            self.Change_State(Current_State)
                            # Stop so we dont trigger this again
                            self.Stop()
                        # Value not equal to desired state so dont trigger any actions
                        else:
                            # Stop so we dont trigger this again
                            self.Stop()
                    # Return true while a timeout is running regardless of state change
                    return True
                # return false if no timeout is running
                else:
                    return False

        # -------------------------------------------------------------------------------------------------------
        class Relay_Auto:

            # -------------------------------------------------------------------------------------------------------
            def __init__(self, Target_State, Auto_ms, Change_State_Referance):
                # Referance to Change_State so we can change state from here
                self.Change_State = Change_State_Referance
                ## Target_State aka pin on or off
                self.Target_State = Target_State
                ## How long the Relay needs to be in a given state before state change will be triggered
                self.Auto_ms = Auto_ms
                ## When last state change took place
                ### Will we set to None when Relay changes to oposite state of Pin_State
                self.Auto_Last = None
                ## Starts as false so we dont trigger before a state changed happens
                self.Active = False


            def Stop(self):
                # Set self.Active to False to indicate we have a running timeout
                self.Active = False
                self.Auto_Last = None
            

            def Start(self):
                # Set self.Auto_Last to ticks_ms so we can do diff on it later
                self.Auto_Last = utime.ticks_ms()
                # Set self.Active to true to indicate we have a running timeout
                self.Active = True
            

            def Loop(self, Current_State):
                # Place in Relay.loop() and pass current pin state
                # Checks if its time to trigger events if not notes ticks to compate against

                # if self.Active is true then we are waiting for a timeout
                if self.Active == True:
                    # Check if we timed out
                    if utime.ticks_diff(utime.ticks_ms(), self.Auto_Last) > self.Auto_ms:
                        # Check if current state == Target_State
                        if Current_State == self.Target_State:
                            # Change state since Relay is still in target state after timeout
                            self.Change_State(Current_State)
                            # Stop so we dont trigger this again
                            self.Stop()
                        # Value not equal to desired state so dont trigger any actions
                        else:
                            # Stop so we dont trigger this again
                            self.Stop()
                    # Return true while a timeout is running regardless of state change
                    return True
                # return false if no timeout is running
                else:
                    return False