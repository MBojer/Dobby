#!/usr/bin/python

## Version
### First didget = Software type 1-Production 2-Beta 3-Alpha
### Secound and third didget = Major version number
### Fourth to sixth = Minor version number
Version = 300002

import machine
import utime
import ujson

class Init:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Group_Config):
        # Referance to dobby
        self.Dobby = Dobby
        # Var to hold configured Peripherals
        self.Peripherals = {}
        # Log Event
        self.Dobby.Log(1, "Group", "Initializing")
        
        # Loop over Peripherals in config
        for Name, Config in Group_Config.items():
            # Make sure Name is a string
            Name = str(Name)
            # Add the Group to the Group dict
            self.Peripherals[Name] = self.Group(self.Dobby, Name, Config)
            # Check if the Group is ok
            if self.Peripherals[Name].OK is False:
                # Issue with Group detected disabling it
                self.Dobby.Log(2, "Group/" + Name, "Issue during setup, disabling the Group")
                # Remove from self.Peripherals
                del self.Peripherals[Name]
            else:
                # Subscribe to Group topic if at least one Group was ok
                # Remeber the + at the end
                self.Dobby.MQTT_Subscribe(self.Dobby.System_Header + "/Group/"+ Name)
                # On/Off Topics
                self.Dobby.MQTT_Subscribe(self.Dobby.System_Header + "/Group/"+ Name + "/OnOff")
            
        self.Dobby.Log(0, "Group", "Initialization complete")


    # -------------------------------------------------------------------------------------------------------
    class Group:

        def __init__(self, Dobby, Name, Config):
            # Referance to dobby
            self.Dobby = Dobby

            # Variable to indicate of the configuration of the Group went ok
            ## False = Error/Unconfigured
            ## True = Running
            self.OK = False
            
            # Name - Referance name
            self.Name = str(Name)

            # Log Event
            self.Dobby.Log(0, "Group/" + self.Name, "Initializing")

            # Check if we got the needed config
            for Entry in ['Dimmer', 'Relay']:

                # We only need one so break for loop on hit
                if Config.get(Entry, None) != None:
                    break
            else:
                self.Dobby.Log(2, "Group/" + Name, "Missing config: 'Dimmer' or 'Relay' - Unable to initialize Group")
                # Return so we dont set ok = True
                return

            # Dict holding target aka names og Peripherals
            self.Targets = {}


            # //////////////////////////////////////// Dimmer \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            # Store config if any
            if Config.get('Dimmer', None) != None:
                self.Targets['dimmer'] = Config["Dimmer"]

            # //////////////////////////////////////// Relay \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
            # Store config if any
            if Config.get('Relay', None) != None:
                self.Targets['relay'] = Config["Relay"]

            # Mark Group as ok aka enable it
            self.OK = True
        
            # Publish what members we got in the Group
            self.Dobby.Log(0, "Group/" + self.Name, ujson.dumps({"Members": self.Targets}))
            
            # Log event
            self.Dobby.Log(0, "Group/" + self.Name, "Initialization complete")


        # -------------------------------------------------------------------------------------------------------
        def On_Message(self, Command, Sub_Topic=None):

            # Hand message off to dimmers and relays if configured
            for Peripheral in ['dimmer', 'relay']:
                try:
                    # Loop over entries on list
                    for Target_Name in self.Targets[Peripheral]:
                            self.Dobby.Modules[Peripheral].Peripherals[Target_Name].On_Message(Command, Sub_Topic=Sub_Topic)
                            # Pass to each entry on self.Targets list
                except KeyError:
                    pass
                
            # Log state message
            self.Dobby.Log_Peripheral([self.Dobby.System_Header + "/Group" + self.Name + "/State", Command])
