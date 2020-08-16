#!/usr/bin/python3

class Init:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Dobby, Verbose=False):

        # Version number
        self.Version = 300000
        # Referance to dobby
        self.Dobby = Dobby
        # Referance to ddb
        self.ddb = Dobby.ddb
        # if Verbose is active will log to terminal, ignores log level
        self.Verbose = Verbose
        # all messages below this level will NOT be logged, except for if verbose is active
        self.Level = 1
        # Name of db we are logging to
        self.Log_db = "Dobby_Logging"
        # Log event
        self.Info("Logging", "Loaded version: " + str(self.Version))

    # -------------------------------------------------------------------------------------------------------
    def Print(self, Owner, Message):
        if self.Verbose == True:
            print(Owner, Message)

    # -------------------------------------------------------------------------------------------------------
    def Debug(self, Owner, Message):
        self.Log(str(Owner), str(Message), 'Debug')

    # -------------------------------------------------------------------------------------------------------
    def Info(self, Owner, Message):
        self.Log(str(Owner), str(Message), 'Info')

    # -------------------------------------------------------------------------------------------------------
    def Warning(self, Owner, Message):
        self.Log(str(Owner), str(Message), 'Warning')

    # -------------------------------------------------------------------------------------------------------
    def Error(self, Owner, Message):
        self.Log(str(Owner), str(Message), 'Error')

    # -------------------------------------------------------------------------------------------------------
    def Critical(self, Owner, Message):
        self.Log(str(Owner), str(Message), 'Critical')

    # -------------------------------------------------------------------------------------------------------
    def Fatal(self, Owner, Message):
        self.Log(str(Owner), str(Message), 'Fatal')

    # -------------------------------------------------------------------------------------------------------
    def Log(self, Owner, Message, Level):
        
        # terminal
        if self.Verbose == True:
            print(Level + " - " + Owner + " - " + Message)
