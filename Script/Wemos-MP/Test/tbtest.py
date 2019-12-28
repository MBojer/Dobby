import sys, traceback

test = [1, 2]
try:
    test[4]
except IndexError as e:
    import traceback
    test = traceback.format_exc()
    print("MARKER", test)