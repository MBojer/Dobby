
class Running_Average:

    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Queue_Length=5, Round_To=None):
        # Needed Vars
        ## How many antries before we start doing fun stuff
        self.Max_Entries = int(Queue_Length)
        ## List of entries
        self.Entry_List = []
        # Last calculated average
        self.Average = None
        # Current reading aka last reading
        self.Current = None
        # Round_To
        if Round_To is None:
            self.Round_To = None
        else:
            self.Round_To = Round_To
            
        ## If not none the returned values will be limited to x didgets after 0
        ## Holds Current Min and Max reading values since last reset
        self.Min = None
        self.Max = None
        # Well 3 is min because i say so
        if self.Max_Entries < 3:
            self.Max_Entries = 3


    # -------------------------------------------------------------------------------------------------------
    def Add(self, Value):
        # Adds a new value to the entry list and removes entries if needed
        # Save value to Current variuable
        self.Current = Value

        # Add value to Entry_List
        self.Entry_List.append(self.Current)

        # Check if list has reached max
        ## Max Reached
        while len(self.Entry_List) > self.Max_Entries:
            # Remove oldes value
            self.Entry_List.pop(0)

        # Calc Current - Min - Max values
        try:
            self.Min = min(self.Min, Value)
        except TypeError:
            self.Min = self.Current
        try:
            self.Max = max(self.Max, Value)
        except TypeError:
            self.Max = self.Current
        self.Average = sum(self.Entry_List) / len(self.Entry_List)
        

    # -------------------------------------------------------------------------------------------------------
    def Reset(self):
        # Sets min and max to current aka resets them
        # normally run after reading values from vars
        # but could be called only once a day to get min max for the day
        self.Min = self.Current
        self.Max = self.Current


    # -------------------------------------------------------------------------------------------------------
    # returns dict containing values Average, Current, Min, Max
    def Get_Average(self):
        # Check if we need to round values
        ## Rounding
        if self.Round_To is not None:
            return round(self.Average, self.Round_To)
        ## Not rounding
        else:
            self.Current


    # -------------------------------------------------------------------------------------------------------
    # returns dict containing values Average, Current, Min, Max
    def Get_dict(self):
        # Check if we need to round values
        ## Rounding
        if self.Round_To is not None:
            return {
                    'Average': round(self.Average, self.Round_To),
                    'Current': round(self.Current, self.Round_To),
                    'Min': round(self.Min, self.Round_To),
                    'Max': round(self.Max, self.Round_To)
                }
        ## Not rounding
        else:
            return {
                    'Average': self.Average,
                    'Current': self.Current,
                    'Min': self.Min,
                    'Max': self.Max
                }