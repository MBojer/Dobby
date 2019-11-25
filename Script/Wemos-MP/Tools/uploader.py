#!/usr/bin/python

import os
import sys

mpy_cross = '/home/virus/micropython/mpy-cross/mpy-cross'
Build_Dir = '../build/'

# 1 = File name
# 2 = Port if specified

try:
    File_Name = sys.argv[1]
except IndexError:
    print("Usage: uploader >filename> <port> - port is optional")
    quit()

try:
    Port = sys.argv[2]
except IndexError:
    Port = '/dev/ttyUSB0'
    
 
Base_Path = os.path.realpath(__file__)
Base_Path = Base_Path.replace('Tools/uploader.py', "")

Output_Name = File_Name[File_Name.index('/bin/') + 5:]
Output_Name = Base_Path + "build/" + Output_Name
Output_Name = Output_Name.replace("/modules", "/lib")

File_Name = File_Name.replace('../', Base_Path)

# make
os.system(mpy_cross + ' ' + File_Name + ' -o ' + Output_Name)

Output_Name = Output_Name[Output_Name.index('/build/') + 7:]

# if "/" in Output_Name:
#     Dir_List = Output_Name.split('/')
#     # make dir
#     Dir_String = ''

#     print  Dir_List

#     for Dir in Dir_List:

#         if "." in Dir:
#             break

#         Dir_String = Dir_String + "/" + Dir
    
#         print(Dir_String)

#         os.system('ampy --port ' + Port + ' mkdir ' + Dir_String)


# # upload
os.system('ampy --port ' + Port + ' put ' + File_Name + " " + Output_Name)