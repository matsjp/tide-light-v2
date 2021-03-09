from pybleno import *
import array
import traceback
import logging

class LEDCountCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80
    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec1d',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            count = int(self.config.getLEDCount())
            data = array.array('B', [0] * 1)
            writeUInt8(data, count, 0)
            callback(Characteristic.RESULT_SUCCESS, data)

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            count = readUInt8(data, 0)
            try:
                self.config.setLEDCount(count)
                callback(Characteristic.RESULT_SUCCESS)
            except ValueError:
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            except Exception as e:
                logging.exception(e)
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
        