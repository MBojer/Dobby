#!/bin/bash

start=`date +%s`

Module_Path=~/Wemos-MP/Modules/

# get current dir so we can go back there when done
Back_To_Dir=$PWD
Port="None"

if [ -e "/dev/ttyUSB0" ];
    then
        Port=/dev/ttyUSB0

elif [ -e "/dev/ttyUSB1" ];
    then
        Port=/dev/ttyUSB1

elif [ "$Port" = "None" ];
    then
        echo "Unable to find port"
        exit
fi

echo ""
echo "Port set to: $Port"

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

# copy modules - shared
echo "Creating Shared mpy files"
# change dir to device folder
cd $Module_Path/Shared
# Dir list
Module_List=(*)
for Module_Name in "${Module_List[@]}"; do
    # Remove .py from name
    Module_Name=${Module_Name/.py/""}
    # Log event
    echo "   ${Module_Name}"
    # Create mpy file
    ~/micropython/mpy-cross/mpy-cross "$Module_Name.py"
    # Move to www
    mv "${Module_Name}.mpy" ../../www/Modules/$Device/
done


# copy modules - device
echo "Creating $Device mpy files"
# change dir to device folder
cd $Module_Path/$Device
# Dir list
Module_List=(*)
for Module_Name in "${Module_List[@]}"; do
    # Remove .py from name
    Module_Name=${Module_Name/.py/""}
    # Log event
    echo "   ${Module_Name}"
    # Create mpy file
    ~/micropython/mpy-cross/mpy-cross "$Module_Name.py"
    # Move to www
    mv "${Module_Name}.mpy" ../../www/Modules/$Device/
done

# back to the dir we came from
cd $Back_To_Dir

end=`date +%s`
runtime=$((end-start))

echo "Run time: "$runtime"s"

echo "Done"