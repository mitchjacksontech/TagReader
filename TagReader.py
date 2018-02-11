#!/usr/bin/env python3
"""
    Class to interface with the uFR Classic RFID Tag Reader

    Library implements only a small subsetr of the API calls available
    - Connect / Disconnect
    - Poll hardware type and serial number
    - Poll the Unique Identifier (UID) of presented RFID tags
    - Poll the type of RFID tag presented

    Borrows heavily from manufacturer sample code found at foo
    https://www.d-logic.net/code/nfc-rfid-reader-sdk/ufr-mf-examples-python

"""

# Python libs
from ctypes import *
from ctypes.util import find_library
import time

# d-logic libs - not a fan of their format.  But they do update them,
# so keeping their provided format to avoid work later
from Constants import *
from ErrCodes import *


class TagReader():
    def __init__(self):
        self.debug = True
        self.__load_library()
#        self.ufr = CDLL('libuFCoder-armhf.so')

        self.status = 'DISCONNECTED'

        # These variables will be used as pointers for the C DLL library
        # Don't access these variables directly.  They aren't what you expect.
        self.__ufr_is_connected = c_uint32()
        self.__ufr_reader_type = c_uint32()
        self.__ufr_reader_serial = c_uint32()


    def poll_tag(self):
        """
            Polls the RFID reader buffer, returns ASCII string of HEX
            Tag Unique Identifier (UID) or None
        """
        self.__check_connection()

        tag_uid          = (c_ubyte * 9)()
        tag_uid_size     = c_uint8()
        tag_type         = c_uint32()
        dlogic_card_type = c_uint8()

        # Choosing between GetCardIdEx and GetLastCardIdEx...
        #   Using the current buffer, so we can detect when no tag is
        #   presented.  If we have latency on the raspberry pi, might
        #   need to switch to GetLastCardIdEx
        response_code = self.ufr.GetCardIdEx(
            byref(tag_type),
            tag_uid,
            byref(tag_uid_size)
        )

        if response_code == DL_OK:
            decoded_uid = str()
            for i in range(tag_uid_size.value):
                # Convert bytes into hex
                decoded_uid += '%0.2x' % tag_uid[i]
            return decoded_uid.upper()

        return None


    def reader_serial(self):
        """
            Returns the serial number of the RFID reader
        """
        if not self.__ufr_reader_serial.value:
            self.__check_connection()
            response_code = self.ufr.GetReaderSerialNumber(byref(self.__ufr_reader_serial))

            if response_code != DL_OK:
                self.__ufr_reader_serial = c_uint32()

        return (self.__ufr_reader_serial.value)


    def reader_type(self):
        """
            Returns the driver-identified RFID reader type
        """
        if not self.__ufr_reader_type.value:
            self.__check_connection()
            response_code = self.ufr.GetReaderType(byref(self.__ufr_reader_type))

            if response_code != DL_OK:
                self.__ufr_reader_type = c_uint32()

        return hex(self.__ufr_reader_type.value)


    def __check_connection(self):
        """
            In case the usb cable to the reader is disconnected and
            reconnected.  This method asks the reader if it is connected,
            and initiates a disconnect/reconnect if needed
        """
        if self.ufr:
            self.ufr.ReaderStillConnected(byref(self.__ufr_is_connected))

        if not self.__ufr_is_connected:
            self.__connect()


    def __connect(self):
        """
            Open the RFID reader through the driver API.  This
            connection must be closed before another connection
            can be established with the reader.

            If a connection cannot be established, retry every 1 second
            and display the connection error code
        """

        self.ufr.ReaderStillConnected(byref(self.__ufr_is_connected))

        retry = 1
        while self.__ufr_is_connected.value != 1:
            self.__disconnect()
            time.sleep(1)
            response_code = self.ufr.ReaderOpen()
            if response_code != DL_OK:
                print("Reader Connection Error {:d}. Retry #{:d}".format(response_code, retry))
                retry += 1
            else:
                print("Got response code: {:d}".format(response_code))
            self.ufr.ReaderStillConnected(byref(self.__ufr_is_connected))
            print ("ReaderStillConnected: " + str(self.__ufr_is_connected.value))


    def __disconnect(self):
        """
            Disconnect the com session with the RFID reader.  Existing
            sessions must be disconnected before another session may be
            established.
        """
        if self.ufr:
            self.ufr.ReaderClose()
        self.__ufr_reader_serial = c_uint32()
        self.__ufr_reader_type = c_uint32()


    def __load_library(self):
        """
            Load the uFCoder dll
        """
        lib_loc = find_library('uFCoder') or find_library('uFCoder-armhf')

        if lib_loc:
            self.ufr = CDLL(lib_loc)

        if not self.ufr:
            self.ufr = CDLL('libuFCoder-armhf.so')

        if not self.ufr:
            raise SystemExit("uFCoder library could not be loaded")
