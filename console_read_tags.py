#!/usr/bin/python3

import sys
import os
import ctypes
import time

from Constants import *
from ErrCodes import *
from TagReader import TagReader


rfid = TagReader();

print("Reader s/n: {}".format(rfid.reader_serial()))
print("Reader type: {}".format(rfid.reader_type()))
# print("poll_tag(): " + str(rfid.poll_tag()))

while(1):
    print("poll_tag(): {}".format( rfid.poll_tag() ))
    time.sleep(0.25)
