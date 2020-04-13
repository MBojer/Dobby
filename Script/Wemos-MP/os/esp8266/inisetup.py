import uos
import network
from flashbdev import bdev

def check_bootsec():
    buf = bytearray(bdev.SEC_SIZE)
    bdev.readblocks(0, buf)
    empty = True
    for b in buf:
        if b != 0xff:
            empty = False
            break
    if empty:
        return True
    fs_corrupted()

def fs_corrupted():
    import time
    while 1:
        print("""\
The FAT filesystem starting at sector %d with size %d sectors appears to
be corrupted. If you had important data there, you may want to make a flash
snapshot to try to recover it. Otherwise, perform factory reprogramming
of MicroPython firmware (completely erase flash, followed by firmware
programming).
""" % (bdev.START_SEC, bdev.blocks))
        time.sleep(3)

def setup():
    check_bootsec()
    print("Performing initial setup")
    uos.VfsFat.mkfs(bdev)
    vfs = uos.VfsFat(bdev)
    uos.mount(vfs, '/')

    # Make dobby config dir
    uos.mkdir('conf')
    # make lib dir
    uos.mkdir('lib')

    with open("boot.py", "w") as f:
        f.write("""\
# Print to clear serial on boot
print("")
print("")
# Disable os debugging
import esp
esp.osdebug(None)
""")

    with open("main.py", "w") as f:
        f.write("""\
# Import and run loader to check modules
import loader
# Run loader
Loader = loader.Run()
# get log queue from loader
Log_Queue = Loader.Log_Queue
# Delete the Loader and loader to free memory
del Loader
del loader

# Import base system to get wifi up and download modules if needed
import base
# run base with loader.Run() as arguments, it will return a loader log to be published when connected
Base = base.Run(Log_Queue)
# delete the log queue
del Log_Queue
# Run base loop
Base.Loop()

# If we get to here something went wrong so lets reboot
print()
print()
print()
print()
print()
print("End of loop rebooting - we should not get to here")
print()
print()
print()
print()
print()
""")

    return vfs
