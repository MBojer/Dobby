#!/bin/bash

start=`date +%s`

# get current dir so we can go back there when done
Back_To_Dir=$PWD
Port="None"

if [ -e "/dev/ttyUSB0" ];
    then
        Port=/dev/ttyUSB0
fi

if [ -e "/dev/ttyUSB1" ];
    then
        Port=/dev/ttyUSB1
fi

if [ "$Port" = "None" ];
    then
        echo "Unable to find port"
        exit
fi

echo "Port set to: $Port"
echo ""

if [ "$1" = "-ou" ];
    then
        echo 
        echo "upload firmware"
        
        if [ "$1" = "-pro" ];
            then
            echo "   D1 mini PRO v1.0"
            esptool.py --port $Port --baud 460800 write_flash -fm dio -fs 4MB -ff 40m 0x0000000 micropython/ports/esp8266/build-GENERIC/firmware-combined.bin
        else
            echo "   D1 mini"
            esptool.py --port $Port --baud 460800 write_flash --flash_size=detect 0 ~/micropython/ports/esp8266/build-GENERIC/firmware-combined.bin
        fi
        ~/piusb0.sh
        exit
fi


if [ "$1" = "-erase" ];
    then
        echo 
        echo "Erassing firmware"
        esptool.py -p $Port erase_flash
        echo "   Done"
        exit
fi

if [ "$1" = "--nocopy" ];
    then
        echo "NOT copying modules"
    else
        echo "Copying Shared modules"
        # copy modules
        cp -v -R "$(dirname "$(realpath "$0")")"/../bin/shared/modules ~/micropython/ports/esp8266/
        echo "Copying modules"
        # copy modules
        cp -v -R "$(dirname "$(realpath "$0")")"/../bin/esp8266/modules ~/micropython/ports/esp8266/
fi


# change dir to micropyhton
cd ~/micropython/ports/esp8266/

# clean after last make
echo 
echo make clean
make clean | grep error

# make 
echo 
echo Making
make | grep error


# Check if make went ok aka we have the file below
FILE="build-GENERIC/firmware-combined.bin"
if test -f "$FILE";
    then
        echo "OK"
    else
        echo
        echo "Make failed"
        exit
fi



# Upload firmware
echo 
echo "Uploading firmware:"

if [ "$1" = "-pro" ];
    then
        echo "D1 ini PRO v1.0"
        esptool.py --port $Port --baud 460800 write_flash -fm dio -fs 4MB -ff 40m 0x0000000 ~/micropython/ports/esp8266/build-GENERIC/firmware-combined.bin
    else
        echo "D1 Mini"
        esptool.py --port $Port --baud 460800 write_flash --flash_size=detect 0 ~/micropython/ports/esp8266/build-GENERIC/firmware-combined.bin
fi


# back to the dir we came from
cd $Back_To_Dir


end=`date +%s`
runtime=$((end-start))

echo "Upload time: "$runtime

# Open serial connection
echo start serial
picocom -b 115200 $Port