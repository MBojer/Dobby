#!/usr/bin/python

# import sys
import socket

import time
# def main(args):
#
#
# main(sys.argv)

ip = "10.0.0.167"
port = 8888
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# file = 'sample.csv'
#
# fp = open(file, 'r')
# for line in fp:
# fp.close()
sock.sendto('{"MQTT_Username": "DasBoot", "Config_ID": "1", "WiFi_Password": "", "Auto_Update": "0", "MQTT_Port": "1883", "Hostname": "MegaTest", "MQTT_Broker": "10.0.0.2", "System_Sub_Header": "", "MQTT_KeepAlive_Interval": "60", "MQTT_Password": "NoSinking", "MQTT_Allow_Flash_Password": "", "WiFi_SSID": "", "System_Header": "/1B"}'.encode('utf-8'), (ip, port))
# for i in range(50):
#     print i
#     sock.sendto('{"MQTT_Username": "DasBoot", "Config_ID": "1", "WiFi_Password": "", "Auto_Update": "0", "MQTT_Port": "1883", "Hostname": "MegaTest", "MQTT_Broker": "10.0.0.2", "System_Sub_Header": "", "MQTT_KeepAlive_Interval": "60", "MQTT_Password": "NoSinking", "MQTT_Allow_Flash_Password": "", "WiFi_SSID": "", "System_Header": "/1B"}'.encode('utf-8'), (ip, port))
#     time.sleep(0.500)

print "done"
