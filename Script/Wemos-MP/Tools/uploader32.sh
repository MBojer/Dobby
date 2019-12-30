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

if [ "$1" = "--upload" ];
    then
        echo 
        echo "ONLY upload firmware"

        # change dir to micropyhton
        cd ~/micropython/ports/esp32/

        esptool.py --chip esp32 --port $Port --baud 460800 write_flash -z 0x1000 build-GENERIC/firmware.bin 
        
        echo "start serial"
        ~/piusb0.sh
        exit
fi


if [ "$1" = "-e" ];
    then
        echo 
        echo "Erassing flash before uploading firmware"
        esptool.py -p $Port erase_flash
        echo "   Done"
fi




# if [ "$1" = "--power" ];
#     then
#         echo "Removing old Dobby modules"
#         rm -v -Rf ~/micropython/ports/esp32/modules/dobby

#         echo "Copying Power modules"
#         cp -v -R "$(dirname "$(realpath "$0")")"/../bin/Special/Power/modules ~/micropython/ports/esp32/

if [ "$1" = "--nocopy" ];
    then
        echo "NOT copying modules"
    else
        echo "Removing old Dobby modules"
        rm -v -Rf ~/micropython/ports/esp32/modules/
        
        # copy modules
        echo "Copying modules"
        cp -v -r "$(dirname "$(realpath "$0")")"/../bin/System/modules ~/micropython/ports/esp32/
        # copy modules
        echo "Copying esp32 modules"
        cp -v -r "$(dirname "$(realpath "$0")")"/../bin/esp32/modules ~/micropython/ports/esp32/
fi


# change dir to micropyhton
cd ~/micropython/ports/esp32/

# clean after last make
echo 
echo make clean
make clean | grep error

# make 
echo 
echo Making
make | grep 'error'


# Check if make went ok aka we have the file below
FILE="build-GENERIC/firmware.bin"
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

esptool.py --chip esp32 --port $Port --baud 460800 write_flash -z 0x1000 build-GENERIC/firmware.bin 


# back to the dir we came from
cd $Back_To_Dir

end=`date +%s`
runtime=$((end-start))

echo "Upload time: "$runtime"s"

# Open serial connection
echo start serial
picocom -b 115200 $Port