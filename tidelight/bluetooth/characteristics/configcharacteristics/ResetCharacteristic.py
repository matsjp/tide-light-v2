from pybleno import *
import array
from Config import *
import traceback

class ResetCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec1c',
            'properties': ['write'],
            'value': None
          })
          
        self.config = config

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            data = readUInt8(data, 0)
            if data != 1:
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                try:
                    self.config.reset()
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except:
                    traceback.print_exc()
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)


