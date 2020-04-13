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
base.Run(Log_Queue)
# delete the log queue
del Log_Queue
# Run base loop
base.Loop(Log_Queue)

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