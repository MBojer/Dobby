#!/bin/bash


Check_File () {
    Module_Name=$1
    # Remove .py from name
    Module_Name=${Module_Name/.py/""}

    # Make hash file
    File_Hash=`cat "$Module_Name.py" | /usr/bin/md5sum | cut -f1 -d" "`
    # Read current hash
    Stored_Hash=$(<"../../www/Modules/$Device/${Module_Name}.md5")
    
    if [ "$Stored_Hash" = "$File_Hash" ];
        then
            echo "   no changes to: $Module_Name"
        else
            # Not change
            Change=1
            # Create mpy file
            ~/micropython/mpy-cross/mpy-cross "$Module_Name.py"

            # Check if make went ok aka we have the file below
            FILE="${Module_Name}.mpy"
            if test -f "$FILE";
                then
                    # Log event
                    echo "   generated new mpy and hash for: ${Module_Name}"
                else
                    echo
                    echo "   unable to create mpy file for: ${Module_Name}"
                    exit
            fi

            # Move to www
            mv "${Module_Name}.mpy" ../../www/Modules/$Device/
            # chmod
            chmod 775 ../../www/Modules/$Device/
            # delete old has file
            rm "../../www/Modules/$Device/${Module_Name}.md5"
            # write to file
            echo $File_Hash >> "../../www/Modules/$Device/${Module_Name}.md5"
            # chmod
            chmod 775 "../../www/Modules/$Device/${Module_Name}.md5"
    fi

}

Change=0

start=`date +%s`

# get current dir so we can go back there when done
Back_To_Dir=$PWD

# Change dir to modules
Module_Path=~/Wemos-MP/Modules/

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
    Check_File $Module_Name
done


# copy modules - device
echo "Creating $Device mpy files"
# change dir to device folder
cd $Module_Path/$Device
# Dir list
Module_List=(*)
for Module_Name in "${Module_List[@]}"; do
    Check_File $Module_Name
done

# Create index.json
cd ../../www/Modules/$Device/
Module_List=(*)
json_String="["
for Module_Name in "${Module_List[@]}"; do
    if [[ $Module_Name == *".mpy"* ]]; 
        then
            # Remove .py from name
            Module_Name=${Module_Name/.mpy/""}
            json_String=$json_String',"'$Module_Name'"'
    fi
done


if [ "$Change" = 1 ];
    then
        # write index.json
        echo "writing index.json"
        # remove old index.json
        rm index.json
        # Fix string
        json_String=${json_String/[,/"["}
        json_String=$json_String"]"
        # write to file
        echo $json_String >> "index.json"
        # chmod
        chmod 775 "index.json"
fi

# back to the dir we came from
cd $Back_To_Dir

end=`date +%s`
runtime=$((end-start))

echo 
echo "Run time: "$runtime"s"

echo "Done"
exit