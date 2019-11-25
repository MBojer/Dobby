
# -------------------------------------------------------------------------------------------------------
class Init:
    # Handles pushnotification via Wirepusher app
    # Checks responce to see if message was delivered offline it will store the message in a queue 
    # Queue will be cleared next time we ar online

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby):
        self.Dobby = Dobby
        print("CODE ME")

        # Need id and message

    # https://wirepusher.com/send?id=KSjcmpg8j&title=MPYtest&message=fromESP&type=Alert

    # response = urequests.get('https://wirepusher.com/send?id=KSjcmpg8j&title=MPYtest&message=fromESP&type=Alert')
    # response = urequests.post('https://wirepusher.com/send?id=KSjcmpg8j&title=MPYtest&message=fromESP&type=Alert')
    # print(type(response))

    def Loop(self):
        test = 1


