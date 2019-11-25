#!/bin/bash

# get current dir so we can go back there when done
Back_To_Dir=$PWD
Port=/dev/ttyUSB0

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
        echo "upload /main.py"
        ampy -p $Port put /media/Dobby/Script/Wemos-MP/bin/main.py
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


if [ "$1" = "-om" ];
    then
        echo 
        echo "Only uploading /main.py"
        ampy -p $Port put /media/Dobby/Script/Wemos-MP/bin/main.py
        echo "Starting Serial"
        ~/piusb0.sh
        exit
fi



echo Copying modules
# copy modules
cp -v -R "$(dirname "$(realpath "$0")")"/../bin/modules ~/micropython/ports/esp8266/


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

# check is user told us to upload main.py
if [ "$1" = "-m" ];
    then
        ampy -p $Port put /media/Dobby/Script/Wemos-MP/bin/main.py
fi

# Open serial connection
echo start serial
~/piusb0.sh