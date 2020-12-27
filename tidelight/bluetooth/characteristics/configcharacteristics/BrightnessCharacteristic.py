from pybleno import *
import array
import traceback
import logging

class BrightnessCharacteristic(Characteristic):
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
            brightness = int(self.config.getBrightness())
            data = array.array('B', [0] * 1)
            writeUInt8(data, brightness, 0)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            brightness = readUInt8(data, 0)
            try:
                self.config.setBrightness(brightness)
                callback(Characteristic.RESULT_SUCCESS)
            except ValueError:
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            except Exception as e:
                logging.exception(e)
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
        