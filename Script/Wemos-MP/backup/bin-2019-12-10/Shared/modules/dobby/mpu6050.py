# # #!/usr/bin/python
# # Source: https://github.com/adamjezek98/MPU6050-ESP8266-MicroPython

# import machine
# import ujson

# class Init:
#     # -------------------------------------------------------------------------------------------------------
#     def __init__(self, Dobby, Config):
#         # Referance to dobby
#         self.Dobby = Dobby
#         # Var to hold configured Peripherals
#         self.Peripherals = {}
#         # Log Event
#         self.Dobby.Log(1, "MPU6050", "Initializing")

#         # Loop over Peripherals in config
#         for Name, MPU6050_Config in Config.items():
#             # Make sure Name is a string
#             Name = str(Name)
#             # Add the MPU6050 to the MPU6050 dict
#             self.Peripherals[Name] = self.MPU6050(self.Dobby, Name, MPU6050_Config)
#             # Check if the MPU6050 is ok
#             if self.Peripherals[Name].OK is False:
#                 # Issue with MPU6050 detected disabling it
#                 self.Dobby.Log(2, "MPU6050/" + Name, "Issue during setup, disabling the MPU6050")
#                 # Delete the MPU6050 from Peripherals
#                 del self.Peripherals[Name]
#             # MPU6050 ok
#             else:
#                 # Subscribe to topic
#                 self.Dobby.MQTT_Subscribe(self.Dobby.Peripherals_Topic("MPU6050", End="+"))
        
#         # Log event
#         self.Dobby.Log(0, "MPU6050", "Initialization complete")


#     # -------------------------------------------------------------------------------------------------------
#     class MPU6050:

#         # -------------------------------------------------------------------------------------------------------
#         def __init__(self, Dobby, Name, Config):
#             # Referance to dobby
#             self.Dobby = Dobby

#             # OK
#             ## False = lError/Unconfigured
#             ## True = Running
#             self.OK = False

#             # Name - This will be added to the end of the topic
#             self.Name = str(Name)

#             # Check if we got the needed config
#             for Entry in ['SCL', 'SDA', 'INT']:
#                 if Config.get(Entry, None) is None:
#                     self.Dobby.Log(2, "MPU6050/" + self.Name, "Missing config: " + Entry + " - Unable to initialize")
#                     return

#             # Reserve the pins
#             # Check if pin is valid
#             # if fails pin is in use
#             try:
#                 self.Dobby.Pin_Monitor.Reserve(Config['SCL'], "MPU6050-" + self.Name + "-SCL")
#                 self.Dobby.Pin_Monitor.Reserve(Config['SDA'], "MPU6050-" + self.Name + "-SDA")
#                 self.Dobby.Pin_Monitor.Reserve(Config['INT'], "MPU6050-" + self.Name + "-INT")
#             except self.Dobby.Pin_Monitor.Error:
#                 # Pin in use unable to configure MPU6050
#                 self.Dobby.Log(2, "MPU6050/" + Name, "Pin in use - Unable to initialize")
#                 # return so we dont set State to true aka mark the MPU6050 as configured
#                 return

#             # Create the I2C object for this sensor
#             self.Sensor_I2C = machine.I2C(
#                 scl=machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['SCL'])),
#                 sda=machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['SDA']))
#             )
#             # Int Pin aka ready to ready
#             self.INT = machine.Pin(self.Dobby.Pin_Monitor.To_GPIO_Pin(Config['INT']), machine.Pin.IN)

#             self.Address=0x68

#             # We need to try here so we can cache os errors
#             try:
#                 self.Sensor_I2C.start()
#                 # Reset the sensor
#                 self.Sensor_I2C.writeto(self.Address, bytearray([107, 0]))
#                 self.Sensor_I2C.stop()
#             # os error = failed to read hence fail the sensor
#             except OSError:
#                 self.Dobby.Log(3, "MPU6050/" + Name, "I2C Init failed - Unable to initialize")
#                 # return so we dont mark the sensor as ok
#                 return

#             # Now we need to create a timer to read the sensor at certen intervals
#             # Check if the dobby.timer module is loaded
#             self.Dobby.Timer_Init()
#             Rate = self.Dobby.Sys_Modules['Timer'].Time_To_ms(Config.get('Rate', "0.5s"))
#             # Add a timer
#             # 1 = Referance Name
#             # 2 = Timeout
#             # 3 = Callback
#             self.Timer = self.Dobby.Sys_Modules['Timer'].Add(
#                 self.Name + "-Read",
#                 Rate,
#                 self.Read,
#                 Logging=False
#             )

#             # And start the timer so we start reading from the sensor
#             self.Timer.Start()

#             # A var to store the values last read from the sensor
#             self.Values = None

#             # mark the sensor as ok
#             self.OK = True



#         def Bit_16_To_Int(self, Hight, Low, Signed=False):
#             result = Hight
#             result = (result << 8) | Low
#             if (Signed == true):
#                 return result
#             else:
#                 return result


#         # float Big_Endian_32_To_Float(uint8_t Byte_0, uint8_t Byte_1, uint8_t Byte_2, uint8_t Byte_3, bool Signed)
#         # {
#         # int result = Byte_0;
#         # result = (result << 8) | Byte_1;
#         # result = (result << 16) | Byte_2;
#         # result = (result << 24) | Byte_3;
#         # if (Signed == true)
#         # {
#         #     return (int32_t)result;
#         # }
#         # else
#         # {
#         #     return (uint32_t)result;
#         # }
#         # }



#         # -------------------------------------------------------------------------------------------------------
#         def Read(self):

#             # If INT is true the sensor is not ready
#             if self.INT == True:
#                 return
            
#             raw_ints = self.get_raw_values()

#             vals = {}
#             vals["AcX"] = self.bytes_toint(raw_ints[0], raw_ints[1])
#             vals["AcY"] = self.bytes_toint(raw_ints[2], raw_ints[3])
#             vals["AcZ"] = self.bytes_toint(raw_ints[4], raw_ints[5])
#             vals["Tmp"] = self.bytes_toint(raw_ints[6], raw_ints[7]) / 340.00 + 36.53
#             vals["GyX"] = self.bytes_toint(raw_ints[8], raw_ints[9])
#             vals["GyY"] = self.bytes_toint(raw_ints[10], raw_ints[11])
#             vals["GyZ"] = self.bytes_toint(raw_ints[12], raw_ints[13])

#             # self.Values =  vals  # returned in range of Int16
#             # -32768 to 32767
            
#             # Restart the timer 
#             self.Timer.Start()

#             print("MARKER READ working below")
#             for Key, Value in vals.items():
#                 print(Key, Value)


#             # print(self.Values['GyX'])
#             # print(self.Values['GyY'])
#             # print(self.Values['GyZ'])
#             # OldMin = -32768
#             # OldMax = 32767
#             # NewMin = 0
#             # NewMax = 360
#             # NewValue = None
            
#             # OldRange = (OldMax - OldMin)
#             # if (OldRange == 0)
#             #     NewValue = NewMin
#             # else
#             # {
#             #     NewRange = (NewMax - NewMin)  
#             #     NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
#             # }
#             # print("MARKER READ", self.Values['GyY'], NewValue)

#         # -------------------------------------------------------------------------------------------------------
#         def get_raw_values(self):
#             self.Sensor_I2C.start()
#             a = self.Sensor_I2C.readfrom_mem(self.Address, 0x3B, 14)
#             self.Sensor_I2C.stop()
#             return a

#         # -------------------------------------------------------------------------------------------------------
#         def bytes_toint(self, firstbyte, secondbyte):
#             if not firstbyte & 0x80:
#                 return firstbyte << 8 | secondbyte
#             return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)




# #     def get_ints(self):
# #         b = self.get_raw_values()
# #         c = []
# #         for i in b:
# #             c.append(i)
# #         return c


# #     def val_test(self):  # ONLY FOR TESTING! Also, fast reading sometimes crashes Sensor_I2C
# #         from time import sleep
# #         while 1:
# #             print(self.get_values())
# #             sleep(0.05)
