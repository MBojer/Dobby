
def ms_To_Time():
    millis=input("Enter time in milliseconds ")
    millis = int(millis)
    seconds=(millis/1000)%60
    seconds = int(seconds)
    minutes=(millis/(1000*60))%60
    minutes = int(minutes)
    hours=(millis/(1000*60*60))%24

    print ("%d:%d:%d" % (hours, minutes, seconds))
