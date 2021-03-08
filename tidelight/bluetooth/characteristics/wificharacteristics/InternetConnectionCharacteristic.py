from pybleno import *
import array
import traceback
import logging
from util import internetConnection

class InternetConnectionCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    CONNECTED = 0x1
    DISCONNECTED = 0x2

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': 'ec10',
            'properties': ['read'],
            'value': None
          })
          
        self._value = None
    

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            if internetConnection():
                connected = self.CONNECTED
            else:
                connected = self.DISCONNECTED
            data = array.array('B', [0] * 1)
            writeUInt8(data, connected, 0)
            callback(Characteristic.RESULT_SUCCESS, data)



