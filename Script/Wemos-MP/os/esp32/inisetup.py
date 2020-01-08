import uos
from flashbdev import bdev

def check_bootsec():
    buf = bytearray(bdev.ioctl(5, 0)) # 5 is SEC_SIZE
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
FAT filesystem appears to be corrupted. If you had important data there, you
may want to make a flash snapshot to try to recover it. Otherwise, perform
factory reprogramming of MicroPython firmware (completely erase flash, followed
by firmware programming).
""")
        time.sleep(3)

def setup():
    check_bootsec()
    print("Performing initial setup")
    uos.VfsFat.mkfs(bdev)
    vfs = uos.VfsFat(bdev)
    uos.mount(vfs, '/')

    # Make dobby config dir
    uos.mkdir('/conf')
    # make lib dir
    uos.mkdir('/lib')

    with open("boot.py", "w") as f:
        f.write("""\
# Print to clear serial on boot
print("")
print("")
import esp
# Disable os debugging
esp.osdebug(None)
# Nothing to see here
""")

    with open("main.py", "w") as f:
        f.write("""\
# Import base system to get wifi up and download modules if needed
import base
# run base
base.Run()
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
