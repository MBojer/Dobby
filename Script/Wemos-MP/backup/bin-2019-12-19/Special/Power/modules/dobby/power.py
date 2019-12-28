#!/usr/bin/python

import utime
import machine
import ujson


# Subscribed to
# /<System_Header>/<Hoatname>/Power/<Name>

# Publishes following message automaticly
# /<System_Header>/<Hoatname>/Power/<Name>/Contactor
# /<System_Header>/<Hoatname>/Power/<Name>/State
# /<System_Header>/<Hoatname>/Power/<Name>/Uptime

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Power", "Initializing")

        # Check if we got the needed config
        try:
            self.Dobby.Config_Check("Power", ['Output_0', 'Input_0', 'Input_1'], Config)
        except self.Dobby.Module_Error:
            return

        # Needed shared variables
        # What output is currently active
        self.Output_Active = "Output_0"
        self.Output_List = []

        # What Input is currently active
        self.Input_Active = None
        self.Input_List = []
        
        # If true we are currently changing inputs, aka waiting for No_Power timeout
        self.Changing_Input = True
        
        # Store push id
        self.Push_id = Config.get('Push_id', None)

        # Loop over Peripherals in config
        for Name, Power_Config in Config.items():
            # Make sure Name is a string
            Name = str(Name)
            if Name.startswith("Output_") == True:
                # Add the Output to the Power dict
                self.Peripherals[Name] = self.Output(self.Dobby, self, Name, Power_Config)
                # Add to Output list
                self.Output_List.append(Name)
            elif Name.startswith("Input_") == True:
                # Add the Suppy to the Power dict
                self.Peripherals[Name] = self.Input(self.Dobby, self, Name, Power_Config)
                # Add to Input list
                self.Input_List.append(Name)
            # only run below loop for output and Input 
            else:
                continue

            # Check if the Power is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Power detected disabling it
                self.Dobby.Log(2, "Power/" + Name, "Issue during setup, disabling")
                # Delete the Power from Peripherals
                del self.Peripherals[Name]
                # remove from input or output list
                if Name.startswith("Output_") == True:
                    del self.Output_List[Name]
                else:
                    del self.Input_List[Name]

            # Power ok
            else:
                # Subscribe to topic
                self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Power"))
        
        # Sort the input and output lists
        self.Input_List = sorted(self.Input_List)
        self.Output_List = sorted(self.Output_List)

        # Log event
        self.Dobby.Log(0, "Power", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    def Loop(self):

        # Run loop for each peripheral
        for Name in self.Peripherals:
            self.Peripherals[Name].Loop()
    

    # -------------------------------------------------------------------------------------------------------
    def Wait_For_No_Power(self):
        pass


    # -------------------------------------------------------------------------------------------------------
    def On_Message(self, Command):


        # Publish state under bla bla bla /Power/<Name>/State
        if Command == "?":
            # Publish the following info:
                # Active Output Output_Active
                # Active Input Input_Active
                # Output x:
                #     Name
                #     On
                #     Supply Voltage
                #     Contactor
                # Input x:
                #     Name
                #     On
                #     Avalible
                #     Priority
                #     Delay
                #     Uptime
                #     Supply Voltage
                #     Contactor
            # Generate state dict
            State_Dict = {}
            State_Dict['Active Output'] = self.Output_Active
            State_Dict['Active Input'] = self.Input_Active
            
            # Create the name dict entry for Input and output aka type
            State_Dict["Outputs"] = {}
            State_Dict["Inputs"] = {}

            # Loop over Peripherals
            for Name in self.Peripherals:
                
                # To get type we need to split at "_" then add "s" to [0]
                Type = Name.split("_")[0] + "s"
                # Creat the dict for this name
                State_Dict[Type][Name] = {}
                
                # Info thats the same regardless of output or Input 
                State_Dict[Type][Name]['Name'] = self.Peripherals[Name].Name
                State_Dict[Type][Name]['On'] = self.Peripherals[Name].On
                State_Dict[Type][Name]['Supply Voltage'] = self.Peripherals[Name].Voltmeter.Voltage
                State_Dict[Type][Name]['Contactor'] = self.Peripherals[Name].Contactor_Relay.Get_State(Return_String=False)
                
                # Only input has unique entries
                if Name.startswith("Input_") == True:
                    # Save info
                    State_Dict[Type][Name]['Avalible'] = self.Peripherals[Name].Avalible
                    State_Dict[Type][Name]['Priority'] = self.Peripherals[Name].Priority
                    State_Dict[Type][Name]['Delay'] = self.Peripherals[Name].Delay
                    # Update uptime for peripheral
                    self.Peripherals[Name].Get_Uptime()
                    # Save uptime
                    State_Dict[Type][Name]['Uptime'] = self.Peripherals[Name].Uptime

            # Publish State dict to .../Power/State
            # FIX Add date time aka timestamp

            # /<System_Header>/<Hoatname>/Power/State
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic('Power', State=True),
                    ujson.dumps(State_Dict)
                ]
            )

        else:
            self.Dobby.Log(2, 'Power/' + self.Name, "Unknown command: " + str(Command))


    # -------------------------------------------------------------------------------------------------------
    def Find_Input(self):

        # Var to hold Peripherals name with highest priority where active is true
        Highest_Priority = -1
        Input_Name = None

        for Name in self.Input_List:
            # Check if Input is Avalible
            if self.Peripherals[Name].Avalible == True:
                # if avalible we need to check if names self.Priority is larger then Highest_Priority
                if self.Peripherals[Name].Priority > Highest_Priority:
                    # Save new highest input
                    Highest_Priority = self.Peripherals[Name].Priority
                    Input_Name = Name

        if Input_Name != self.Input_Active:
            # Highest priority input changed
            # we need to trigger an input change
            self.Change_Input(Input_Name)


    # -------------------------------------------------------------------------------------------------------
    def Contactors_All_Off(self):
        # Turns all Contactors off
        # usually triggered before a input change

        # Loop over entries in Input list
        for Name in self.Input_List:
            # Turn contactor off for each input
            self.Peripherals[Name].Contactor_Off()

        # Loop over entries in Output list
        for Name in self.Output_List:
            # Turn contactor off for each Output
            self.Peripherals[Name].Contactor_Off()


    # -------------------------------------------------------------------------------------------------------
    def Change_Input(self, New_Input):
        # Changes to input name provided in New_Input

        # Log event
        self.Dobby.Log(1, "Power", "Changing input to: " + self.Peripherals[New_Input].Name)

        # Set self.Input_Active to Highest_Priority so we know what input to change to
        self.Input_Active = New_Input

        # Set ALL Contactors both input and output
        self.Contactors_All_Off()        
        

            

    # -------------------------------------------------------------------------------------------------------
    class Output:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Power, Output_Name, Config):
            # Referance to dobby
            self.Dobby = Dobby
            # Referance to power aka mother object
            self.Power = Power

            # OK
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False

            # Check if we got the needed config
            try:
                self.Dobby.Config_Check("Power/" + Output_Name, ['Contactor_Relay', 'Supply_Voltmeter', 'Supply_Trigger', 'No_Power'], Config)
            except self.Dobby.Module_Error:
                return

            # Store name default to output name if not set
            self.Name = Config.get('Name', Output_Name)

            # Store the config values
            self.No_Power = Config['No_Power']
            self.Supply_Trigger = Config['Supply_Trigger']
            # Create referance to Peripherals
            try:
                self.Contactor_Relay = self.Dobby.Modules['relay'].Peripherals[Config['Contactor_Relay']]
                self.Voltmeter = self.Dobby.Modules['voltmeter'].Peripherals[Config['Supply_Voltmeter']]
            # If we get a KeyError we are missing a peripheral
            except KeyError as e:
                self.Dobby.Log(4, "Power/" + self.Name, "Missing peripheral: " + str(e))
                # return so we dont mark the output as ok
                return
            
            # is true if Input is on
            self.On = None

            # Wether or not we need to wait before turning the Input on again
            self.No_Power_Done = False
            
            # We also need a timer to handle on power periode
            self.No_Power_Timer = self.Dobby.Sys_Modules['Timer'].Add(
                "Power-NoPower",
                self.No_Power,
                self.No_Power_Compleate
            )
            # Log event
            self.Dobby.Log(0, "Power/" + self.Name, "No Power interval set to: " + Config['No_Power'])

            # Mark output as ok
            self.OK = True
            
            # Log event
            self.Dobby.Log(0, "Power" + self.Name, "Initialization complete")




        # -------------------------------------------------------------------------------------------------------
        def No_Power_Compleate(self):
            # Just to make sure check that we got no power on output
            if self.Voltmeter.Voltage > self.Supply_Trigger:
                # Restart power timer
                self.No_Power_Timer.Start()
                # return so we dont trigger below code
                return

            # At this stage the Inputs contactor can we turned on as well as the output contactor
            # Input first
            self.Power.Peripherals[self.Power.Input_Active].Contactor_Relay.Set_On()
            # Then output
            self.Power.Peripherals[self.Power.Output_Active].Contactor_Relay.Set_On()


        # -------------------------------------------------------------------------------------------------------
        def Contactor_Off(self):
            
            # only change if on
            if self.Contactor_Relay.Get_State() == 1:
                try:
                    self.Contactor_Relay.Set_Off()
                except KeyError as e:
                    self.Dobby.Log(6, "Power/" + self.Name, "Unable to trigger contactor relay")
                    # FIX ERROR HANDLIG HERE SINCE WE DONT KNOW IF WE ARE OFF OR ON
                else:
                    # Log Peripherals state
                    # /<System_Header>/<Hoatname>/Power/<Name>/Contactor
                    self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic('Power', End=self.Name + '/Contactor', State=False), "0"])


        # -------------------------------------------------------------------------------------------------------
        def Loop(self):
            # Checks Output voltmeter agains Output tigger if >= then mark output as on < mark output as off 
            # Then start the NoPower timer, it will then set No_Power_Done to true

            # If something is not right then dont run the loop
            if self.OK != True:
                return

            # Check if volts is above self.Voltmeter_Trigger
            if self.Voltmeter.Voltage >= self.Supply_Trigger:
                # Check if we already marked the Output as on
                if self.On != True:
                    # Log event
                    self.Dobby.Log(0, "Power/" + self.Name, "Output: On")
                    # Mark Output as on
                    self.On = True
                    # Stop self.No_Power_Timer if running
                    self.No_Power_Timer.Stop()

            else:
                # Check if we already marked the Output as off
                if self.On != False:
                    # Log event
                    self.Dobby.Log(0, "Power/" + self.Name, "Output: Off")
                    # Mark Output as off
                    self.On = False
                    # Turn off contactor since we lost power
                    self.Contactor_Off()
                    # Start the No Power timer
                    self.No_Power_Timer.Start()


    # -------------------------------------------------------------------------------------------------------
    class Input:

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Power, Input_Name, Config):
            # Referance to dobby
            self.Dobby = Dobby
            # Referance to power aka mother object
            self.Power = Power

            # OK
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False

            # Check if we got the needed config
            try:
                self.Dobby.Config_Check("Power/" + Input_Name, ['Name', 'Contactor_Relay', 'Supply_Voltmeter', 'Supply_Trigger', 'Signal_Relay'], Config)
            except self.Dobby.Module_Error:
                return

            # Store the config values
            self.Supply_Trigger = Config['Supply_Trigger']
            # Create referance to Peripherals
            try:
                self.Contactor_Relay = self.Dobby.Modules['relay'].Peripherals[Config['Contactor_Relay']]
                self.Signal_Relay = self.Dobby.Modules['relay'].Peripherals[Config['Signal_Relay']]
                self.Voltmeter = self.Dobby.Modules['voltmeter'].Peripherals[Config['Supply_Voltmeter']]
            # If we get a KeyError we are missing a peripheral
            except KeyError as e:
                self.Dobby.Log(4, "Power/" + self.Name, "Missing peripheral: " + str(e))
                # return so we dont mark the output as ok
                return

            # If True then we have power avalible from this source
            self.Avalible = False

            # Get priority from Input name
            self.Priority = int(Input_Name.replace("Input_", ""))
            
            # Name - This will be added to the end of the topic
            self.Name = str(Config['Name'])
            
            # true if Input is on
            self.On = None
            
            # Check if uptime is configured
            self.Uptime = Config.get('Uptime', None)
            if self.Uptime != None:
                # Convert Uptime to a string
                self.Uptime = "0h0m0s"
                # what ms the Input came on at
                self.Uptime_Start = 0

                # Check if the dobby.timer module is loaded
                self.Dobby.Timer_Init()
                # Add a timer
                # 1 = Referance Name
                # 2 = Timeout
                # 3 = Callback
                # 4 = Argument
                # Note auto is active by creating <state> key with referance to timer in Auto dict
                self.Uptime_Timer = self.Dobby.Sys_Modules['Timer'].Add(
                    "Power-Uptime-" + self.Name,
                    Config['Uptime'],
                    self.Publish_Uptime
                )
                # Log event
                self.Dobby.Log(0, "Power/" + self.Name, "Uptime publish interval set to: " + Config['Uptime'])

            # Store delay for referance later
            # default to 2 sec
            self.Delay = Config.get('Delay', "2s")
            # We also need a timer to handle on and off delay
            self.Delay_Timer = self.Dobby.Sys_Modules['Timer'].Add(
                "Power-Delay-" + self.Name,
                self.Delay,
                self.Signal_Off
            )
            # Log event
            self.Dobby.Log(0, "Power/" + self.Name, "On / Off delay set to: " + self.Delay)
            
            # Mark as OK
            self.OK = True

            # Log event
            self.Dobby.Log(0, "Power/" + self.Name, "Initialization complete")


        # -------------------------------------------------------------------------------------------------------
        def Get_Uptime(self):
            # if Input is off uptime is 0...
            if self.On == False:
                self.Uptime = "0h0m0s"
            else:
                # get uptime is ms
                self.Uptime = utime.ticks_diff(utime.ticks_ms(), self.Uptime_Start)
                # convert ms to string with hours minutes and secunds
                self.Uptime = self.Dobby.ms_To_Time(self.Uptime)


        # -------------------------------------------------------------------------------------------------------
        def Publish_Uptime(self):
            # Update self.Uptime
            self.Get_Uptime()
            # Publish uptime
            # /<System_Header>/<Hoatname>/Power/<Name>/Uptime
            self.Dobby.Log_Peripheral(
                [
                    self.Dobby.Peripherals_Topic('Power', End=self.Name + '/Uptime'),
                    self.Uptime
                ]
            )
            # restart the publish uptime timer
            self.Uptime_Timer.Start()


        # -------------------------------------------------------------------------------------------------------
        def Signal_Off(self):
            # Used by delay timer to turn signal off after turning contactor off
            if self.Signal_Relay.Get_State() == 1:
                self.Signal_Relay.Set_Off()


        # -------------------------------------------------------------------------------------------------------
        def Contactor_Off(self, Ignore_Active=True):
            # Trigger the local relay with the provided settings
            # If Ignore_Active = True when contactor will not change state if self.Input_Active = self.Priority
            if Ignore_Active == True and "Input_" + str(self.Priority) == self.Power.Input_Active:
                return

            # only change if on
            if self.Contactor_Relay.Get_State() == 1:
                try:
                    self.Contactor_Relay.Set_Off()
                except KeyError as e:
                    self.Dobby.Log(6, "Power/" + self.Name, "Unable to trigger contactor relay")
                    # FIX ERROR HANDLIG HERE SINCE WE DONT KNOW IF WE ARE OFF OR ON
                else:
                    # Will send off signal to everything but Input 0
                    if self.Priority != 0:
                        self.Delay_Timer.Start()
                    # Log Peripherals state
                    # /<System_Header>/<Hoatname>/Power/<Name>/Contactor
                    self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic('Power', End=self.Name + '/Contactor', State=False), "0"])
                    # Send push if configured
                    if self.Power.Push_id != None:
                        self.Dobby.Push_Send(self.Power.Push_id, "Power", self.Name + " - Contactor: Off", Type='Info')
            

        # -------------------------------------------------------------------------------------------------------
        def Mark_As_Avalible(self):
            # Only mark as avalible if still on
            if self.On == True:
                # Mark as avalible
                self.Avalible = True
                # Since a input became avalible will check if we got a new Highest_Priority input
                self.Power.Find_Input()


        # -------------------------------------------------------------------------------------------------------
        def Loop(self):
            # Checks voltmeter agains supply tigger if >= then mark as avalible if < mark as not avalible

            # If something is not right then dont run the loop
            if self.OK != True:
                return

            # Check if volts is above self.Voltmeter_Trigger
            if self.Voltmeter.Voltage >= self.Supply_Trigger:
                # Check if we already marked the Input as on
                if self.On != True:
                    # Log event
                    self.Dobby.Log(0, "Power/" + self.Name, "On")
                    
                    # Start the active timer so we set self.Avalible to true 
                    self.Delay_Timer.Start(Callback=self.Mark_As_Avalible)

                    # Check if we need to publish uptime
                    if self.Uptime != None:
                        # Save current ms so we can use it to Calc uptime
                        self.Uptime_Start = utime.ticks_ms()
                        # Start publishing uptime 
                        self.Uptime_Timer.Start()

                    # MQTT - Mark as on
                    # /<System_Header>/<Hoatname>/Power/<Name>/State
                    self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic('Power', End=self.Name, State=True), "1"])

                    # Send push if configured
                    if self.Power.Push_id != None:
                        self.Dobby.Push_Send(self.Power.Push_id, "Power", self.Name + " On", Type='Info')
                    
                    # Mark Input as on
                    self.On = True
            else:
                # Check if we already marked the Input as off
                if self.On != False:
                    # Log event
                    self.Dobby.Log(0, "Power/" + self.Name, "Off")
                    # Since we are off we cant be avalible
                    self.Avalible = False
                    # since we lost an input will check what the new Highest_Priority input is
                    self.Power.Find_Input()
                    
                    # Mark Input as running off mqtt
                    # /<System_Header>/<Hoatname>/Power/<Name>/State
                    self.Dobby.Log_Peripheral([self.Dobby.Peripherals_Topic('Power', End=self.Name, State=True), "0"])
    
                    # None at init so we can check agains it to make sure we dont send a new message at boot
                    if self.On != None:
                        # Send push if configured
                        if self.Power.Push_id != None:
                            # Update self.Uptime
                            self.Get_Uptime()
                            # push
                            self.Dobby.Push_Send(self.Power.Push_id, "Power", self.Name + " Off - Was on for: " + self.Uptime, Type='Info')
        
                        # Publish the final uptime
                        self.Publish_Uptime()

                    # Stop uptime timer so we dont publish again
                    self.Uptime_Timer.Stop()

                    if self.Power.Input_Active == "Input_" + str(self.Priority):
                        # Remove from active since supply voltage disapered aka we lost power
                        self.Power.Input_Active = None

                    # Turn contactor relay off
                    self.Contactor_Off()

                    # Mark Input as off
                    self.On = False