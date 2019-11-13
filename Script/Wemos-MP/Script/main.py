# Check if we dobby lib got loaded
if Dobby is not None:

    # Start eternal loop
    while True:
        # Check for mqtt messages
        Dobby.Loop()
        # Sleep a bit not to use 100% CPU
        utime.sleep(0.1)



print('Main Loop End')
print('Main Loop End')
print('Main Loop End')
print('Main Loop End')
print('Main Loop End')
print('Main Loop End')