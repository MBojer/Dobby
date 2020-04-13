#!/usr/bin/python

## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300000

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
        self.Dobby.Log(1, "Uptime", "Initializing")

        # We will need the timer for something so lets init it now
        Dobby.Timer_Init()

        # if Interval is set configure a timer
        if "Interval" in Config:
            # Add a timer
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # 4 = Argument
            # We do not need to save a referance to the timer since we are not interacting with it
            self.Dobby.Sys_Modules['timer'].Add(
                "Uptime-Interval",
                Config['Interval'],
                self.Publish_Uptime,
                True,
                Start=True,
                Repeat=True
            )
            # Log event
            self.Dobby.Log(1, "Uptime/", "Interval set to: " + str(Config['Interval']))

            # remove Interval from Config
            # so we can run for loop on config to get the last configuration
            del Config['Interval']

        # Loop over remaining entrys in config
        for Entry in Config:
            # Add Entry aka Name to Config[Entry] so we can access it on Timer_Action
            Config[Entry]['Name'] = Entry
            # Create a timer for eatch entry
            # Callback set to Timer_Action
            # and Argument set to Config[Entry]
            # Timer_Action will then loop at the config we pass and take appropiate action
            # 1 = Referance Name
            # 2 = Timeout
            # 3 = Callback
            # 4 = Argument
            # We do not need to save this timer since will never interact with it
            self.Dobby.Sys_Modules['timer'].Add(
                "Uptime-Action-" + str(Entry),
                Entry,
                self.Timer_Action,
                Argument=Config[Entry],
                Start=True,
                Keep=False
            )
            # Log event
            self.Dobby.Log(1, "Uptime/", "Action registered at: " + str(Entry))


        # Subscribe to topic
        self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("Uptime"))

        # Log compleation
        self.Dobby.Log(0, "Uptime", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    def ms_To_Time(self, Time_ms, Add_Empthy=True):

        x = Time_ms / 1000
        seconds = round(x % 60)
        x /= 60
        minutes = round(x % 60)
        x /= 60
        hours = round(x % 24)
        x /= 24
        days = round(x)
        x /= 7
        weaks = round(x)

        Postfix_List = ['w', 'd', 'h', 'm', 's']

        Var_List = [weaks, days, hours, minutes, seconds]

        Return_String = ""

        for i in range(5):
            if Var_List[i] == 0 and Add_Empthy == False:
                continue
            else:
                Return_String = Return_String + str(Var_List[i]) + Postfix_List[i]

        return Return_String
        

    # -------------------------------------------------------------------------------------------------------
    def Timer_Action(self, Config):

        # Log avtion got triggered
        self.Dobby.Log(1, 'Uptime' + Config['Name'], "Triggering actions")

        if "Relay" in Config:
            self.Dobby.Modules['relay'].Peripherals[Config['Relay']['Name']].Set_State(Config['Relay']['State'])
            try:
                self.Dobby.Modules['relay'].Peripherals[Config['Relay']['Name']].Set_State(Config['Relay']['State'])
            except KeyError:
                pass

        if "Message" in Config:
            try:
                self.Dobby.Log_Peripheral([Config['Message']['Topic'], Config['Message']['Payload']])
            except KeyError:
                pass

    
    # -------------------------------------------------------------------------------------------------------
    def Publish_Uptime(self, Interval):
        # Publish uptime
        self.Dobby.Log_Peripheral(
            [
                self.Dobby.Peripherals_Topic("Uptime", State=True),
                self.ms_To_Time(utime.ticks_ms(), Add_Empthy=False)
            ],
            Retained=True
        )

    # -------------------------------------------------------------------------------------------------------
    def On_Message(self, Payload, Sub_Topic=None):
        # Check what command aka payload was recived
        # ? - Returns - 0 = off 1 = on
        if Payload == "?":
            # Publish state
            self.Publish_Uptime(False)

        # unknown command
        else: 
            self.Dobby.Log(2, 'Uptime', "Unknown command: " + str(Payload))