
import machine
import utime
import ujson

# -------------------------------------------------------------------------------------------------------
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

# -------------------------------------------------------------------------------------------------------
class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

# -------------------------------------------------------------------------------------------------------
class TransitionError(Error):
    """Raised when an operation attempts a state transition that's not
    allowed.

    Attributes:
        previous -- state at beginning of transition
        next -- attempted new state
        message -- explanation of why the specific transition is not allowed
    """

    def __init__(self, previous, next, message):
        self.previous = previous
        self.next = next
        self.message = message


# -------------------------------------------------------------------------------------------------------
def MQTT_Message(Message):
    # Message Should be dict or list
    # List = [<Topic>, <Payload>]
    # Dict = {'Topic': <Topic>, 'Payload': <Payload>}
    # We need a try here in case Topic or Payload is not set

    # Check if list
    if type(Message) == list:
        try:
            Dobby.Log_Peripheral(
                str(Message['Topic']),
                str(Message['Payload'])
            )
        except KeyError:
            if 
            raise KeyError("Message has to be dict or list")
            
            
        # Do nothing
        pass
    # Check if dict
    elif type(Message) == dict:
        # Convert to dict:

    else:
        raise TypeError("Message has to be dict or list")