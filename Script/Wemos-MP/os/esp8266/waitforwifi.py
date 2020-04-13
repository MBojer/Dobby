#!/usr/bin/python

import utime

# -------------------------------------------------------------------------------------------------------
class Run:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Timeout=None, Print=False):

        # Referance to Dobby
        self.Dobby = Dobby

        self.Print = Print

        if self.Print == True:
            # clear serial
                print()
                print()

        # Connected to wifi already
        if self.Dobby.wlan0.isconnected():
            # Log event
            self.Dobby.Log(1, "System/WiFi", "Connected to SSID: " + str(self.Dobby.wlan0.config('essid')) + " IP: " + str(self.Dobby.wlan0.ifconfig()[0]))
            # return true since wifi is connected
            return

        # we if get to here we are not connected to wifi
        
        # Log that we are not connected
        self.Dobby.Log(0, "System/WiFi", "Not connected to WiFi, waiting for wifi to connecte. Timeout: " + str(Timeout))

        # int to hold 0.5 increments
        i = 0

        # try below code so we can cach ctrl + c
        try:
            # Not when we started
            Wait_Start = utime.ticks_ms()
            # Start while loop and wait for wifi to connect
            while self.Dobby.wlan0.isconnected() == False:
                if Print == True:
                    # print Waiting message message
                    print('Press CTRL + C to interrupt WiFi reconnect. Trying for: ' + str(i) + " sec", end="\r")
                # Sleep for 0.5s
                utime.sleep_ms(500)
                # Add 0.5 to i
                i = i + 0.5
                # Check for timeout
                if Timeout != None:
                    if utime.ticks_diff(utime.ticks_ms(), Wait_Start) > Timeout:
                        # Log timeout
                        self.Dobby.Log(0, "System/WiFi", "Timeout after " + str(Timeout) + "ms while waiting for wifi to connect")
                        # raise self.Dobby.Error
                        raise self.Dobby.Error("KeyboardInterrupt after " + str(i) + " sec")

        except KeyboardInterrupt:
            # Log error
            self.Dobby.Log(3, "System/WiFi", "Interrupted after " + str(i) + " sec")
            # raise self.Dobby.Error
            raise self.Dobby.Error("KeyboardInterrupt after " + str(i) + " sec")
        else:
            # Log event
            self.Dobby.Log(1, "System/WiFi", "WiFi connected to SSID: " + str(self.Dobby.wlan0.config('essid')) + " IP: " + str(self.Dobby.wlan0.ifconfig()[0]))
            # return true when wifi is connected
            return