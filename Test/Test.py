#!/usr/bin/python

from subprocess import call, STDOUT
import os
if call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w')) != 0:
    print("Nope!")
else:
    print("Yup!")



#     git rev-parse HEAD
# 9f9d50837cec76849330fca56ab0abcd75d07045
# 98765b85f438403a3966e70dcc302caf4cdbba22
