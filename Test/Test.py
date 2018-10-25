#!/usr/bin/python

from subprocess import call, STDOUT
import os
if call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w')) != 0:
    print("Nope!")
else:
    print("Yup!")
