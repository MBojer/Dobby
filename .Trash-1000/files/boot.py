# boot.py -- run on boot-up

# Libraries
## Dobby
## for reading fs
import os
## for delays
import utime
## for stuff
import machine
import sys
import ujson
import gc

# Version = 300000
# First didget = Software type 1-Production 2-Beta 3-Alpha
# Secound and third didget = Major version number
# Fourth to sixth = Minor version number

# Var to hold Dobby object
Dobby = None

# Boot Message
print()
print('   Booting Dobby - Free memory: ' + str(gc.mem_free()))

# Allow user to interrupt boot and enter cli
try:
    print()
    print('   Press ctrl + c to enter Command Line Interface')
    # Sleep for 3 sec and wait for input
    print('      Timeout in ' + str(3))
    utime.sleep(1)
    for i in range(1, 3):
        print('      Timeout in ' + str(3 - i))
        utime.sleep(1)
    print('      Timeout booting')
    print()
except KeyboardInterrupt:
    print('   Got ctrl + c entering Command Line Interface')
    print()
    # Load cli
    import dobby.cli
    dobby.cli.CLI()

# init Dobby Lib
# Try to load dobbylib
try:
    import dobby.main
# If fails halt
except MemoryError as e:
    print()
    print()
    print()
    print('   Unable to load Dobby Lib - Error: ' + str(e) + ' - Starting CLI')
    print()
    print()
    print()
    # Set Dobby to none so we know load failed
    Dobby = None
    # Start the CLI
    import dobby.cli
    dobby.cli.CLI()

# continue boot as normal since we loaded the lib
else:
    Dobby = dobby.main.Dobby()
    Dobby.Log(1, 'System', "Boot Done")