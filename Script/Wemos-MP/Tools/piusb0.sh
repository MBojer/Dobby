#!/bin/bash
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

picocom -b 115200 $Port
