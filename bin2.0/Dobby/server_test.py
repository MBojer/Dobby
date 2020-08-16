#!/usr/bin/python3

import socket
import paho.mqtt.client as MQTT
import os

host = ''       # your IP address
port = 8500    # pick a port you want to listen on. 
backlog = 5     # number of clients you could handle at once
size = 1024     # max size of data packet

# create socket:
Server_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

Server_Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


# connect to host / port:
Server_Socket.bind((host,port))

# start listening:
Server_Socket.listen(backlog)


# MQTT
MQTT_Client = MQTT.Client(client_id="GPS-" + str(os.urandom(1)[0] %1000), clean_session=True)        

MQTT_Client.connect_async("10.0.0.2", port=1883, keepalive=60, bind_address="")

MQTT_Client.loop_start()


GPS_Data = dict()
GPS_Data['Last'] = dict()
GPS_Data['Current'] = dict()

print("Starting server NMEA to MQTT listening on: " + str(port))


def Publish_Change(Key):

    # Publish message
    MQTT_Client.publish('/Boat/GPS/' + Key, payload=GPS_Data['Current'][Key], retain=False)

    # Save value to last
    GPS_Data['Last'][Key] = GPS_Data['Current'][Key]


def Value_Chech(Key):

    # Check if Key is in last reading
    if Key not in GPS_Data['Last']:
        Publish_Change(Key)

    # Key in 'Last'
    else:
        if GPS_Data['Last'][Key] != GPS_Data['Current'][Key]:
            Publish_Change(Key)


# stay in this loop until ctrl-c is typed at console:
try:
    while True:
        client, address = Server_Socket.accept()
        data = client.recv(size)

        if data:

            # Convert to string
            data = data.decode("utf-8")
            # Strip \r
            data = data.replace('\r', '')
            # Strip \n
            data = data.replace('\n', '')

            # Split data at ","
            data = data.split(',')

            # Save the wanted data

            if data[0] == '$GPGGA':
                GPS_Data['Current']['Quality'] = data[6]
                if GPS_Data['Current']['Quality'] == '0':
                    GPS_Data['Current']['Quality'] = 'Invalid'
                elif GPS_Data['Current']['Quality'] == '1':
                    GPS_Data['Current']['Quality'] = 'Fix'
                elif GPS_Data['Current']['Quality'] == '2':
                    GPS_Data['Current']['Quality'] = 'Diff'
                Value_Chech('Quality')
                
                GPS_Data['Current']['Satellites'] = data[7]
                Value_Chech('Satellites')
                GPS_Data['Current']['Altitude'] = data[9]
                Value_Chech('Altitude')


            elif data[0] == '$GPVTG':
                GPS_Data['Current']['True'] = data[1]
                Value_Chech('True')
                GPS_Data['Current']['Magnetic'] = data[3]
                Value_Chech('Magnetic')
                GPS_Data['Current']['knots'] = data[5]
                Value_Chech('knots')
                GPS_Data['Current']['kmh'] = data[7]
                Value_Chech('kmh')

            
        client.close()

        # # echo data to console
        # print("###################################################")
        # print("###################################################")
        # print("###################################################")
        # for Key in GPS_Data['Current']:
        #     print(Key, GPS_Data['Current'][Key])


except KeyboardInterrupt:
    client.close()
    Server_Socket.close()
    print("Quitting")
    quit()











        # # GPGGA - GPS fix data.
        # if 'GPGGA' in Last_Reading:

        #     # GPGGA['UTC'] = data[1]
        #     # # Strip the last '.00'
        #     # GPGGA['UTC'] = GPGGA['UTC'][:-3]

        #     # GPGGA['Latitude'] = data[2]
        #     # GPGGA['Latitude_Compas'] = data[3]
        #     # GPGGA['Longitude'] = data[4]
        #     # GPGGA['Longitude_Compas'] = data[5]

        #     # # String for google maps
        #     # # Latitude
        #     # if GPGGA['Latitude_Compas'] == "S":
        #     #     GPGGA['Google'] = '-'
        #     # else:
        #     #     GPGGA['Google'] = ''

        #     # Temp_Var = GPGGA['Latitude'].replace('.', '')
        #     # Temp_Var = Temp_Var[:2] + '.' + Temp_Var[2:]
            
        #     # GPGGA['Google'] = GPGGA['Google'] + Temp_Var + ', '

        #     # # Longitude
        #     # if GPGGA['Longitude_Compas'] == "W":
        #     #     GPGGA['Google'] = GPGGA['Google'] + '-'

        #     # Temp_Var = GPGGA['Longitude'].replace('.', '')
        #     # Temp_Var = Temp_Var[1:]
        #     # Temp_Var = Temp_Var[:2] + '.' + Temp_Var[2:]
            
        #     # GPGGA['Google'] = GPGGA['Google'] + Temp_Var


        #     # 'Latitude': '5318.427296', 'Latitude_Compas': 'N', 'Longitude': '00632.516024', 'Longitude_Compas': 'W',


        #     GPS_Data['Quality'] = Last_Reading['GPGGA'][6]
        #     if GPS_Data['Quality'] == '0':
        #         GPS_Data['Quality'] = 'Invalid'
        #     elif GPS_Data['Quality'] == '1':
        #         GPS_Data['Quality'] = 'Fix'
        #     elif GPS_Data['Quality'] == '2':
        #         GPS_Data['Quality'] = 'Diff'
            
        #     GPS_Data['Satellites'] = Last_Reading['GPGGA'][7]
        #     GPS_Data['Altitude'] = Last_Reading['GPGGA'][9]


        #     # GPGGA['Horizontal dilution of position'] = data[8]
        #     # GPGGA['Meters  (Antenna height unit)'] = data[10]
        #     # GPGGA['Geoidal separation (Diff. between WGS-84 earth ellipsoid and mean sea level. geoid is below WGS-84 ellipsoid)'] = data[11]
        #     # GPGGA['Meters  (Units of geoidal separation)'] = data[12]
        #     # GPGGA['Age in seconds since last update from diff. reference station'] = data[13]
        #     # GPGGA['Diff. reference station ID#'] = data[14]
        #     # GPGGA['Checksum'] = data[15]



        # # # GPVTG - GPS fix data.
        # elif data.startswith("$GPVTG"):

        #     # Var to hold formated data
        #     GPVTG = dict()

        #     # Split data at ","
        #     data = data.split(',')

        #     # GPVTG ['$GPVTG', '358.1', 'T', '4.7', 'M', '0.0', 'N', '0.0', 'K', 'A*2F']
        #     # Field	Meaning
        #     # 0	Message ID $GPVTG
        #     # 1	Track made good (degrees true)
        #     # 2	T: track made good is relative to true north
        #     # 3	Track made good (degrees magnetic)
        #     # 4	M: track made good is relative to magnetic north
        #     # 5	Speed, in knots
        #     # 6	N: speed is measured in knots
        #     # 7	Speed over ground in kilometers/hour (kph)
        #     # 8	K: speed over ground is measured in kph
        #     # 9	The checksum data, always begins with *

        #     GPVTG['True'] = data[1]
        #     GPVTG['Magnetic'] = data[3]
        #     GPVTG['knots'] = data[5]
        #     GPVTG['kph'] = data[7]

        #     # Add to last reading
        #     Last_Reading['GPVTG'] = GPVTG




        # # GNGNS - GPS fix data.
        # elif data.startswith("$GNGNS"):

        #     # Var to hold formated data
        #     GNGNS = dict()

        #     # Split data at ","
        #     data = data.split(',')

        #     # GNGNS ['$GNGNS', '235402.00', '5318.428913', 'N', '00632.517136', 'W', 'AAN', '12', '1.3', '84.5', '48.0', '', '*38']

        #     GNGNS = data

        #     # Add to last reading
        #     Last_Reading['GNGNS'] = GNGNS



        # # PQGSV - GPS fix data.
        # elif data.startswith("$PQGSV"):

        #     # Var to hold formated data
        #     PQGSV = dict()

        #     # Split data at ","
        #     data = data.split(',')


        #     PQGSV = data

        #     # Add to last reading
        #     Last_Reading['PQGSV'] = PQGSV
