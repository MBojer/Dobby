#!/bin/bash

Upload_Firmware() {
    echo 
    echo "Uploading firmware"

    # change dir to micropyhton
    cd ~/micropython/ports/$Device/

    if [ "$Device" = "esp32" ];
        then
            echo "   esp32"
            esptool.py --chip esp32 --port $Port --baud 460800 write_flash -z 0x1000 build-GENERIC/firmware.bin
        else
            # check if we are uploading to esp8266 pro
            if [ "$3" = "-pro" ];
                then
                echo "   D1 mini PRO v1.0"
                esptool.py --port $Port --baud 460800 write_flash -fm dio -fs 4MB -ff 40m 0x0000000 build-GENERIC/firmware-combined.bin
            else
                echo "   D1 mini"
                esptool.py --port $Port --baud 460800 write_flash --flash_size=detect 0 build-GENERIC/firmware-combined.bin
            fi
        
        echo
        echo "Upload done"
        echo
    fi
}



start=`date +%s`

# get current dir so we can go back there when done
Back_To_Dir=$PWD

Device="None"
if [ "$1" = "esp32" ];
    then
        Device="esp32"

elif [ "$1" = "esp8266" ];
    then
        Device="esp8266"

elif [ "$Device" = "None" ];
    then
        echo "Please enter device: 'esp32', 'esp8266'"
        exit
fi

# Find port
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

echo ""
echo "Port set to: $Port"

if [ "$2" = "-u" ];
    then
        Upload_Firmware
 
        echo "start serial"
        ~/piusb0.sh
        exit
fi


if [ "$2" = "-s" ];
    then
        echo "start serial"
        ~/piusb0.sh
        exit
fi

if [ "$2" = "-e" ];
    then
        echo 
        echo "Erassing flash before uploading firmware"
        esptool.py -p $Port erase_flash
        echo "   Done"
fi


if [ "$2" = "-f" ];
    then
        FILE=$3
        if ! test -f "$FILE";
            then
                echo
                echo "   no sutch file: "$FILE
                exit
        fi

        # String .py from file name
        File_Name=${FILE/.py/""}
        
        echo 
        echo "Uploading $File_Name to /lib"
        echo "   Creating $File_Name.mpy"
        # ~/micropython/mpy-cross/mpy-cross $File_Name.py

        OUTPUT="$(~/micropython/mpy-cross/mpy-cross $File_Name.py)"
        echo "${OUTPUT}"        

        # Check if make went ok aka we have the file below
        FILE=$File_Name".mpy"
        if test -f "$FILE";
            then
                # Log event
                echo "   generated new mpy for: $File_Name"
            else
                echo
                echo "   unable to create mpy file for: $File_Name"
                exit
        fi

        echo "   Uploading $File_Name.mpy"
        ampy -p $Port put $File_Name.mpy '/lib/'$File_Name'.mpy'
        echo "   Removing $File_Name.mpy"
        rm $File_Name.mpy
        echo "   Starting Serial"
        ~/piusb0.sh
        exit
fi


if [ "$2" = "--nocopy" ];
    then
        echo "NOT copying modules"
    else
        # copy modules
        echo "Copying modules"
        cp -v -r "$(dirname "$(realpath "$0")")"/../os/Shared/*.py ~/micropython/ports/$Device/modules
        # copy modules
        echo "Copying $Device modules"
        cp -v -r "$(dirname "$(realpath "$0")")"/../os/$Device/*.py ~/micropython/ports/$Device/modules
        
        if [ "$Device" = "esp8266" ];
            then
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/base.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/cli.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/config.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/loader.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/timer.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/indicator.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/pinmonitor.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/umqttsimple.py ~/micropython/ports/$Device/modules
                cp -v "$(dirname "$(realpath "$0")")"/../os/$Device/waitforwifi.py ~/micropython/ports/$Device/modules

        fi
                
fi



# change dir to micropyhton
cd ~/micropython/ports/$Device/

# clean after last make
echo 
echo make clean
make clean | grep error

# make 
echo 
echo Making
make | grep 'error'


# Check if make went ok aka we have the file below
if [ "$Device" = "esp32" ];
    then
        FILE="build-GENERIC/firmware.bin"
    else
        FILE="build-GENERIC/firmware-combined.bin"
fi
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

Upload_Firmware

# back to the dir we came from
cd $Back_To_Dir

end=`date +%s`
runtime=$((end-start))

echo "Upload time: "$runtime"s"

# Open serial connection
echo start serial
picocom -b 115200 $Port