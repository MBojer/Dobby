# boot.py -- runs on boot-up

# Variables
Version = 1

WiFi_SSID = "NoInternetHere"
WiFi_Password = "NoPassword1!"

def WiFi_Connect():
	import network
	sta_if = network.WLAN(network.STA_IF)
	if not sta_if.isconnected():
		print('Starting connecting to SSID: ' + WiFi_SSID)
		sta_if.active(True)
		sta_if.connect(WiFi_SSID, WiFi_Password)
		while not sta_if.isconnected():
			pass

	print('network config:', sta_if.ifconfig())

	
from umqtt.robust import MQTTClient

	# Test reception e.g. with:
	# mosquitto_sub -t foo_topic

WiFi_Connect()

# def main(server="localhost"):
#     c = MQTTClient("umqtt_client", server)
#     c.connect()
#     c.publish(b"foo_topic", b"hello")
#     c.disconnect()

# if __name__ == "__main__":
#     main()

from umqtt.simple import MQTTClient
client = MQTTClient('Test', '192.168.0.2', 1883,'DasBoot', 'NoSinking')
client.connect()

print("Done")
