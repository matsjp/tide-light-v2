from pybleno import *
import array
import struct
import sys
import traceback
from builtins import str
from ..Config import *
import traceback

class OfflineModeCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec0f',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            state = self.config.getOfflineMode()
            data = array.array('B', [0] * 1)
            stateCode = list(offlineModeStates.keys())[list(offlineModeStates.values()).index(state)]
            writeUInt8(data, stateCode, 0)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            modeCode = readUInt8(data, 0)
            if not self.validateOfflineMode(modeCode):
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                mode = offlineModeStates[modeCode]
                try:
                    self.config.setOfflineMode(mode)
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except:
                    traceback.print_exc()
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def validateOfflineMode(self, mode):
        return mode in offlineModeStates.keys()

