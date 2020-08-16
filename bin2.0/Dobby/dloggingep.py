#!/usr/bin/python3

import json
import time
import os
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import threading

class Init:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Config):

        self.Version = 300000

        self.Agents = {}

        # Log init
        Dobby.Log.Info("Logging EP", "Loading version: " + str(self.Version))

        # Loop over each main entry aka name of device
        for Entry_Name in Config:
            # Spawn an agent for each main entry
            # remember to pass config
            self.Agents[Entry_Name] = self.Agent(Dobby, Entry_Name, Config[Entry_Name])

        
    # -------------------------------------------------------------------------------------------------------
    class Agent:

        # -------------------------------------------------------------------------------------------------------
        # Custom Exception
        class Error(Exception):
            pass

        # -------------------------------------------------------------------------------------------------------
        def __init__(self, Dobby, Name, Config):

            # Make sure name is a string
            self.Name = str(Name) 

            # Referance to dobby
            self.Dobby = Dobby
            # Referance to ddb
            self.ddb = Dobby.ddb
            # Referance to Dobby.Log
            self.Log = Dobby.Log
            
            # db name to log to
            self.Log_db = 'Dobby_Logging_EP'

            # Log init
            self.Log.Info("Logging EP", "Starting agent: " + str(Name))

            # Check if config is enabeled
            if Config['Enabled'] == False:
                # Log init
                self.Log.Warning("Logging EP - " + Name, "Enabled is false disabling agent")
                return

            # save log rate and serial port to vars
            self.Serial_Port = Config['Serial Port']
            self.Log_Rate = Config['Log Rate']

            # Dir with key = Firendly name and var = hex value to check
            self.Check_Dir = {}

            # Check if serial port exists
            try:
                os.stat(self.Serial_Port)
            except OSError:
                self.Log.Error("EP Logger", self.Name + ' - Serial port: ' + str(self.Serial_Port) + " does not exist. Quitting. Check the driver")
            else:
                # Save entries we need to check
                for Entry, Value in Config.items():
                    # check if entry contains " - 0x"
                    # then will assume its a hex value in it and add it to the Check_Dir
                    if " - 0x" not in Entry:
                        continue
                    
                    # Done store if value = false
                    elif Value == False:
                        continue

                    # split entry to get name and hex value
                    Entry = Entry.split(" - ")
                    
                    # Var containing name for ease of coding
                    Name = Entry[0]

                    # store value
                    self.Check_Dir[Name] = {'id': str(Entry[1])}

                    if 'log' in Value:
                        self.Check_Dir[Name]['log'] = True
                        self.Logging = True
                    
                    if 'publish' in Value:
                        self.Check_Dir[Name]['publish'] = True

                    # Add multiplier
                    self.Check_Dir[Name]['Multiplier'] = 1

                    # If one of the strings in the list below is in name then
                    # multuplyer needs to be 0.01 and not 1
                    Test_List = ['Amp', 'Volt', "Watt", "Temperature"]

                    for Test_Name in Test_List:
                        if Test_Name in Name:
                            self.Check_Dir[Name]['Multiplier'] = 0.01
                            break

                # Create the Modbus client
                self.EP_Logger_Client = ModbusClient(method = 'rtu', port = self.Serial_Port, baudrate = 115200)

                # Start checker thread
                EP_Logger_Thread = threading.Thread(name='DobbyEPLoggerChecker', target=self.Checker, kwargs={})
                EP_Logger_Thread.daemon = True
                EP_Logger_Thread.start()


        def Checker(self):
            # Start eternal loop
            while True:


                # Create the connection if we need to log
                if self.Logging == True:
                    db_Connection = self.ddb.Connect(self.Log_db, Create_If_Missing=True)
                    # Enable auto commit
                    self.ddb.Run("SET autocommit = 1;", Connection=db_Connection)

                # Request values
                for Name, Dict in self.Check_Dir.items():

                    # Read input value
                    ## 0x3200 and 0x3201 needs to read two units
                    if Name in {'Battery Status', 'Charger Status'}:
                        Modbus_Value = self.Read_Input(Dict['id'], 2)
                    else:
                        Modbus_Value = self.Read_Input(Dict['id'])

                    # Check for errors
                    # Not pritty but it works
                    if str(type(Modbus_Value)) == "<class 'pymodbus.exceptions.ModbusIOException'>":
                        # Log event
                        self.Log("Debug", "EP Logger", "Modbus", "Unable to read: " + Name + " - " + str(Modbus_Value))
                        continue

                    # Battery Status
                    if Name == 'Battery Status':

                        # D3-D0: 
                        # 00H Normal 
                        # 01H Overvolt 
                        # 02H Under Volt
                        # 03H Low Volt Disconnect
                        # 04H Fault 

                        # D7-D4: 
                        # 00H Normal
                        # 01H Over Temp.(Higher than the warning settings)
                        # 02H Low Temp.( Lower than the warning settings), 

                        # D8: 
                        # normal 0 
                        # Battery inerternal resistance abnormal 1, 

                        # D15: 
                        # 1-Wrong identification for rated voltage
                        
                        # https://www.oipapio.com/question-5355673
                        # No clue how this works but it seems to do so will take it 

                        # Define each mask as a tuple with all the bit at 1 and distance from the right:
                        D3_D0_mask = (0b1111, 0)
                        D7_D4_mask = (0b1111, 4)
                        D8_mask = (0b1, 8)
                        D15_mask = (0b1, 15)

                        # Creating the json dict with all values as false
                        json_State = {}
                        json_State["Fault"] = False
                        json_State["Low Volt Disconnect"] = False
                        json_State["Under Volt"] = False
                        json_State["Overvolt"] = False
                        json_State["Normal Voltage"] = False
                        json_State["Low Temp"] = False
                        json_State["Over Temp"] = False
                        json_State["Normal Temp"] = False
                        json_State["Battery internal resistance abnormal"] = False
                        json_State["Wrong identification for rated voltage"] = False

                        # compare each mask to the value, after shifting to the right position:
                        # Update values to true if so
                        if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 4:
                            json_State["Fault"] = True
                        if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 3:
                            json_State["Low Volt Disconnect"] = True
                        if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 2:
                            json_State["Under Volt"] = True
                        if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 1:
                            json_State["Overvolt"] = True
                        if D3_D0_mask[0]&(Modbus_Value.registers[0]>>D3_D0_mask[1]) == 0:
                            json_State["Normal Voltage"] = True
                        if D7_D4_mask[0]&(Modbus_Value.registers[0]>>D7_D4_mask[1]) == 2:
                            json_State["Low Temp"] = True
                        if D7_D4_mask[0]&(Modbus_Value.registers[0]>>D7_D4_mask[1]) == 1:
                            json_State["Over Temp"] = True
                        if D7_D4_mask[0]&(Modbus_Value.registers[0]>>D7_D4_mask[1]) == 0:
                            json_State["Normal Temp"] = True
                        if D8_mask[0]&(Modbus_Value.registers[0]>>D8_mask[1]) == 1:
                            json_State["Battery internal resistance abnormal"] = True
                        if D15_mask[0]&(Modbus_Value.registers[0]>>D15_mask[1]) == 1:
                            json_State["Wrong identification for rated voltage"] = True

                        Modbus_Value = json.dumps(json_State)


                    elif Name == 'Charger Status':

                        # D15-D14: Input volt status. 
                        #     00H normal
                        #     01H no power connected
                        #     02H Higher volt input
                        #     03H Input volt error.
                        # D13: Charging MOSFET is shorted.
                        # D12: Charging or Anti-reverse MOSFET is shorted.
                        # D11: Anti-reverse MOSFET is shorted.
                        # D10: Input is over current.
                        # D9: The load is Over current.
                        # D8: The load is shorted.
                        # D7: Load MOSFET is shorted.
                        # D4: PV Input is shorted.
                        # D3-2: Charging status.
                        #     00 No charging
                        #     01 Float
                        #     02 Boost
                        #     03 Equlization.
                        # D1: 0 Normal, 1 Fault.
                        # D0: 1 Running, 0 Standby


                        # Define each mask as a tuple with all the bit at 1 and distance from the right:
                        D0_mask = (0b1, 0)
                        D1_mask = (0b1, 1)
                        D3_D2_mask = (0b11, 2)
                        D4_mask = (0b1, 4)
                        D7_mask = (0b1, 7)
                        D8_mask = (0b1, 8)
                        D9_mask = (0b1, 9)
                        D10_mask = (0b1, 10)
                        D11_mask = (0b1, 11)
                        D12_mask = (0b1, 12)
                        D13_mask = (0b1, 13)
                        D15_D14_mask = (0b11, 14)

                        # Creating the json dict with all values as false
                        json_State = {}
                        json_State['Running'] = False
                        json_State['Standby'] = False
                        json_State['Normal'] = False
                        json_State['Fault'] = False
                        json_State['No charging'] = False
                        json_State['Float'] = False
                        json_State['Boost'] = False
                        json_State['Equlization'] = False
                        json_State['PV Input is shorted'] = False
                        json_State['Charging or Anti-reverse MOSFET is shorted'] = False
                        json_State['Anti-reverse MOSFET is shorted'] = False
                        json_State['Input is over current'] = False
                        json_State['The load is Over current'] = False
                        json_State['The load is shorted'] = False
                        json_State['Load MOSFET is shorted'] = False
                        json_State['Load MOSFET is shorted'] = False
                        json_State['Input voltage normal'] = False
                        json_State['No power connected'] = False
                        json_State['Higher volt input'] = False
                        json_State['Input volt error'] = False

                        # D0
                        if D0_mask[0]&(Modbus_Value.registers[0]>>D0_mask[1]) == 1:
                            json_State['Running'] = True
                        else:
                            json_State['Standby'] = True
                        # D1
                        if D1_mask[0]&(Modbus_Value.registers[0]>>D1_mask[1]) == 1:
                            json_State['Normal'] = True
                        else:
                            json_State['Fault'] = True
                        # D3-D2
                        if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 0:
                            json_State['No charging'] = True
                        if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 1:
                            json_State['Float'] = True
                        if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 2:
                            json_State['Boost'] = True
                        if D3_D2_mask[0]&(Modbus_Value.registers[0]>>D3_D2_mask[1]) == 3:
                            json_State['Equlization'] = True
                        # D4
                        if D4_mask[0]&(Modbus_Value.registers[0]>>D4_mask[1]) == 1:
                            json_State['PV Input is shorted'] = True
                        # D7
                        if D7_mask[0]&(Modbus_Value.registers[0]>>D7_mask[1]) == 1:
                            json_State['Charging or Anti-reverse MOSFET is shorted'] = True
                        # D8
                        if D8_mask[0]&(Modbus_Value.registers[0]>>D8_mask[1]) == 1:
                            json_State['Anti-reverse MOSFET is shorted'] = True
                        # D9
                        if D9_mask[0]&(Modbus_Value.registers[0]>>D9_mask[1]) == 1:
                            json_State['Input is over current'] = True
                        # D10
                        if D10_mask[0]&(Modbus_Value.registers[0]>>D10_mask[1]) == 1:
                            json_State['The load is Over current'] = True
                        # D11
                        if D11_mask[0]&(Modbus_Value.registers[0]>>D11_mask[1]) == 1:
                            json_State['The load is shorted'] = True
                        # D12
                        if D12_mask[0]&(Modbus_Value.registers[0]>>D12_mask[1]) == 1:
                            json_State['Load MOSFET is shorted'] = True
                        # D13
                        if D13_mask[0]&(Modbus_Value.registers[0]>>D13_mask[1]) == 1:
                            json_State['Load MOSFET is shorted'] = True
                        # D3-D2
                        if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 0:
                            json_State['Input voltage normal'] = True
                        if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 1:
                            json_State['No power connected'] = True
                        if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 2:
                            json_State['Higher volt input'] = True
                        if D15_D14_mask[0]&(Modbus_Value.registers[0]>>D15_D14_mask[1]) == 3:
                            json_State['Input volt error'] = True

                        Modbus_Value = json.dumps(json_State)


                    else:
                        Modbus_Value = str(float(Modbus_Value.registers[0] * Dict['Multiplier']))

                    # Check if we need to log
                    if Dict.get('log', False) != False:

                        self.Log_Value(Name, Modbus_Value, db_Connection)

                    # Check if we need to publish
                    if Dict.get('publish', False) != False:
                        # Build topic
                        Topic = self.Dobby.Config['System Header'] + '/EP/' + str(self.Name) + '/' + str(Name)
                        # If Modbus_Value is float we round to two didgets
                        try:
                            Modbus_Value = float(Modbus_Value)
                        except:
                            pass
                        else:
                            # if we got a number ending with .0 we return only the whole number
                            if str(Modbus_Value).endswith(".0"):
                                Modbus_Value = int(Modbus_Value)
                            # else we round to two didgets
                            else:
                                Modbus_Value = round(Modbus_Value, 2)

                        # Publish
                        self.Dobby.MQTT.Publish(Topic, str(Modbus_Value), Retained=True, Build_Topic=False)
                        # Log event
                        self.Log.Debug("EP Logger", "MQTT Publish - Topic: " + Topic + " - Payload: " + str(Modbus_Value))

                # Create the connection if we need to log
                if self.Logging == True:
                    self.ddb.Disconnect(db_Connection)

                # Sleep till next read
                time.sleep(self.Time_To_ms(self.Log_Rate))



        # -------------------------------------------------------------------------------------------------------
        def Log_Value(self, Name, Value, db_Connection, Retry=False):

            # try to write message to db before any checks
            try:
                self.ddb.Run("INSERT INTO `" + self.Name + "` (`Name`, `Value`) VALUES ('" + Name + "', '" + str(Value) + "');", Connection=db_Connection)
            except self.ddb.Error as e:
                # Create table if missing
                if str(e) == "Missing table":
                    self.ddb.Run("CREATE TABLE `" + self.Name + "` (`id` int(11) NOT NULL AUTO_INCREMENT, `Name` varchar(45) NOT NULL, `Value` varchar(45) NOT NULL, `DateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`), UNIQUE KEY `id_UNIQUE` (`id`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;", Connection=db_Connection)
                    Retry = True
                else:
                    print("FIX THIS: " + str(e))
            finally:
                # Retry if we needed to create the table
                if Retry == True:
                    self.Log_Value(Name, Value, db_Connection, Retry=True)

        # -------------------------------------------------------------------------------------------------------
        def Read_Input(self, Address, Count=1):

            Address = int(str(Address), 16)

            Modbus_Value = ""

            try:
                Modbus_Value = self.EP_Logger_Client.read_input_registers(Address, Count, unit=1)
            except (pyModbus.ConnectionException):
                self.Log("Debug", "EP Logger", self.Name, "Error reading: " + str(Address) + " Count: " + str(Count))

            return Modbus_Value



        # -------------------------------------------------------------------------------------------------------
        def _To_ms(self, Time):

            if type(Time) != str:
                return Time

            try:
                if Time.lower().endswith("s") == True:
                    # Convert Time to ms
                    return int(float(Time[:-1]) * 1000)
                    
                elif Time.lower().endswith("m") == True:
                    # Convert Time to ms
                    return int(float(Time[:-1]) * 60000)
                    
                elif Time.lower().endswith("h") == True:
                    # Convert Time to ms
                    return int(float(Time[:-1]) * 3600000)

            except ValueError:
                # Raise error
                raise self.Error("Invalid time provided: " + str(Time))

        # -------------------------------------------------------------------------------------------------------
        def Time_To_ms(self, Time, Min_Value=None):
            # if Time is int will return it assuming it already in ms format
            # Converts a string contrining <number of><format> to ms
            # Format options: 
            #     s = seconds
            #     m = minutes
            #     h = hours
            # Check if int with try and return it assuming its ms already
            try: 
                return int(Time)
            except ValueError:
                pass

            # we need at least one number and one char
            if len(Time) < 2:
                # pass so we trigger error
                pass

            # Convert Time and Min value to ms
            Time_ms = self._To_ms(Time)

            if Min_Value != None:
                Min_ms = self._To_ms(Min_Value)
                # Compare the two values and default to Min_ms if Time_ms is lower then Min_ms
                if Time_ms < Min_ms:
                    # Default to Min_ms aka Min_Value
                    Time_ms = Min_ms
                    # Log event
                    self.Dobby.Log(2, "Timer", "Time: " + str(Time) + " is less then Min Value: " + str(Min_Value) + " defaulting to Min Value")

            # Return the time in ms we made
            return Time_ms * 0.001


