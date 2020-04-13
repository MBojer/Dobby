#!/usr/bin/python

## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300001

import machine
import utime
import ujson


class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Switch_Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Switch", "Initializing")
        
        # Loop over Peripherals in config
        for Name, Config in Switch_Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Switch to the Switch dict
            self.Peripherals[Name] = self.Switch(self.Dobby, Name, Config)
            # Check if the Switch is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Switch detected disabling it
                self.Dobby.Log(2, "Switch/" + Name, "Issue during setup, disabling the switch")
                
        self.Dobby.Log(0, "Switch", "Initialization complete")

    # -------------------------------------------------------------------------------------------------------
    # Place this function in dobbylib.loop
    # This is where we check and do stuff if Interrupt_Counter changed
    def Loop(self):
        for Name in self.Peripherals:
            self.Peripherals[Name].Loop()


    # -------------------------------------------------------------------------------------------------------
    class Switch:
        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Variable to indicate of the configuration of the switch went ok
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False
            
            # Name - Referance name
            self.Name = str(Name)

            # Name - Referance name
            if Config.get("Flip", None) != None:
                # Set flip so we can check if try or false
                self.Flip = Config['Flip']
                if self.Flip not in [True, False]:
                    # Default to false
                    self.Flip = False

            # Default to false if not set
            else:
                self.Flip = False

            # Check if we got a config dict if no dict we cant configure
            if type(Config) is not dict:
                return
            
            # Log Event
            self.Dobby.Log(0, "Switch/" + self.Name, "Initializing")

            # Check if we got the needed config
            for Entry in ['Pin']:
                if Config.get(Entry, None) == None:
                    self.Dobby.Log(2, "Switch/" + Name, "Missing config: " + Entry + " - Unable to initialize switch")
                    return

            # Check if PullUp is set to true 
            if Config.get("PullUp", None) != None:
                # Save value
                self.PullUp = bool(Config["PullUp"])
                # Log event
                self.Dobby.Log(0, "Switch/" + self.Name, "PullUp set to: " + str(self.PullUp))
            else:
                # Default to true
                self.PullUp = True

            # Save pin name to self.Pin
            self.Pin = Config['Pin']

            # Reset the pin
            try:
                self.Dobby.Pin_Monitor.Reserve(self.Pin, "Switch-" + self.Name, Pull=self.PullUp)
            except self.Dobby.Pin_Monitor.Error as e:
                # Pin in use unable to configure switch
                self.Dobby.Log(2, "Switch/" + Name, "Pin in use - Unable to initialize switch")
                # return so we dont set State to true aka mark the switch as configured
                return

            # Convert Wemos Pin to GPIO Pin Number
            self.Pin = self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['Pin'])

            # Check if the pin as i valid pin, Pin monitor returns false if pin is invalid
            if self.Pin is False:
                self.Dobby.Log(2, "Switch/" + id, "Invalid Pin Name: " + str(Config['Pin']) + " - Unable to initialize switch")
                return

            # Create Machine pin
            # We cannot make the pin before we check PullUp, above
            if self.PullUp ==  True:
                self.Pin = machine.Pin(self.Pin, machine.Pin.IN, machine.Pin.PULL_UP)
            else:
                self.Pin = machine.Pin(self.Pin, machine.Pin.IN)
            
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
                            self.Dobby.Log(2, "Switch/" + self.Name, "Trigger Message " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.MQTT_Message[Entry.lower()] = Config['Message'][Entry]
                        # log event
                        self.Dobby.Log(0, "Switch/" + self.Name, "Trigger Message " + Entry + " set to Topic: '" + self.MQTT_Message[Entry.lower()]['Topic'] + "' Payload: '" + self.MQTT_Message[Entry.lower()]['Payload'] + "'")
            
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
                            self.Dobby.Log(2, "Switch/" + self.Name, "Trigger Relay " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.Relay[Entry.lower()] = Config['Relay'][Entry]
                        # log event
                        self.Dobby.Log(
                            0,
                            "Switch/" + self.Name,
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
                            self.Dobby.Log(2, "Switch/" + self.Name, "Trigger Dimmer " + Entry + ": Missing " + Check + " - Disabling the '" + Entry + "' message")
                            # break since one is missing and we need both topic and payload
                            Failure = True

                    # Check if we failed to get the needed settings
                    if Failure == False:
                        # Save settings
                        self.Dimmer[Entry.lower()] = Config['Dimmer'][Entry]
                        # log event
                        self.Dobby.Log(
                            0,
                            "Switch/" + self.Name,
                            Entry + ": Trigger Dimmer: '" + self.Dimmer[Entry.lower()]['Name'] + "' State: '" + str(self.Dimmer[Entry.lower()]['State']) + "'"
                            )


            # Get optional config if any
            ## For
            self.For = {}
            # Check if we got 'for' set in config
            if Config.get("For", None) != None:
                for Entry in Config['For']:
                    # Check if the dobby.timer module is loaded
                    self.Dobby.Timer_Init()
                    # Add a timer
                    # 1 = Referance Name
                    # 2 = Timeout
                    # 3 = Callback
                    # 4 = Argument - Pass on or off
                    # Note For is active by creating <state> key with referance to timer in For dict
                    self.For[Entry.lower()] = self.Dobby.Sys_Modules['timer'].Add(
                        self.Name + "-For-" + Entry,
                        Config['For'][Entry],
                        self.For_Check,
                        Start=False,
                        Repeat=False,
                        Argument=Entry.lower()
                    )
                    # Log event
                    self.Dobby.Log(0, "Switch/" + self.Name, Entry + " For set to: " + str(Config['For'][Entry]))

            # Mark Switch as ok aka enable it
            self.OK = True

            # Subscribe to Switch topic if at least one Switch was ok
            self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Switch", End=Name))
            
            # State of switch - On/OFF aka True/False
            self.State = self.Get_State()

            # Log event
            self.Dobby.Log(0, "Switch/" + self.Name, "Initialization complete")


            # -------------------------------------------------------------------------------------------------------


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Payload, Sub_Topic=None):
            # Check if Switch is OK
            if self.OK == False:
                # FIX - Throw error custom error here and cache in Peripherals.On_Message, then remove Switch
                self.Dobby.Log(2, 'Switch-' + self.Name, "Disabeled")

            # Check what command aka payload was recived
            # ? - Returns - 0 = off 1 = on
            elif Payload == "?":
                # Publish state            
                self.Dobby.Log_Peripheral(
                    [
                        self.Dobby.Peripherals_Topic("Switch", End=self.Name, State=True),
                        self.Get_State()
                    ],
                    Retained=True
                )

            # Unknown command
            else: 
                self.Dobby.Log(2, 'Relay', "Unknown Relay command: " + str(Payload))


        # -------------------------------------------------------------------------------------------------------
        def Get_json(self):
            print("CODE ME")


        # -------------------------------------------------------------------------------------------------------
        def Get_State(self):
            # Returns the current state of the Switch in 'on' / 'off'
            # Flips the output of the pin since we are using pulldown and on will be 0 and off will be 1 on
            # Since fliped due to pull up then:
            # On = 0
            # off = 1
            # And if flip is active we reverse it all
            if self.Pin.value() == 0:
                if self.Flip == True:
                    return 'off'
                else:
                    return 'on'
            else:
                if self.Flip == True:
                    return 'on'
                else:
                    return 'off'


        # -------------------------------------------------------------------------------------------------------
        # State gets compared to current state and if equal Set_State is triggered
        def For_Check(self, State):

            # Compare pased state with current state
            if self.Get_State() == State:
                # Change state
                self.Set_State(State)

            # Stop the timer
            self.For[State.lower()].Stop()


        # -------------------------------------------------------------------------------------------------------
        def Set_State(self, State):

              # Build Topic
                Topic = self.Dobby.Peripherals_Topic("Switch", End=self.Name, State=True)

                # Log Switch was pressed
                self.Dobby.Log_Peripheral([Topic, self.Get_State()], True)

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
            # If Switch is disabled do nothing
            if self.OK == False:
                return

            # Store current state in variable
            Current_State = self.Get_State()
                        
            # check if current state == self.state
            # if so dont do anything
            if self.State != Current_State:
                # Loop over entrys in For if any
                for Name, Timer in self.For.items():
                    if Name == Current_State:
                        # Check if we already have a running timer
                        # if we do dont start aka reset the timer
                        if Timer.Running != True:
                            # Start the timer, it will then trigger For_Check with current state
                            Timer.Start()
                        # return so we dont trigger a normal state change
                        return

                # if we get to her for is not active for this state
                # Thus we change state asap is state != self.State
                self.Set_State(Current_State)