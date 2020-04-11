from pybleno import *
import array
from tidelight.Config import *
import traceback

class LdrActiveCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec10',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            state = self.config.getLdrActive()
            data = array.array('B', [0] * 1)
            stateCode = list(ldrStates.keys())[list(ldrStates.values()).index(state)]
            writeUInt8(data, stateCode, 0)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            stateCode = readUInt8(data, 0)
            if not self.validateLdrActive(stateCode):
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                ldrActive = ldrStates[stateCode]
                try:
                    self.config.setLdrActive(ldrActive)
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except:
                    traceback.print_exc()
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def validateLdrActive(self, ldrActive):
        return ldrActive in ldrStates.keys()
