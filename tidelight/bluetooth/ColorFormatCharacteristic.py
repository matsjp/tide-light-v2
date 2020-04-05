from pybleno import *
import array
import struct
import sys
import traceback
from builtins import str
from .Config import *
import traceback

class ColorFormatCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec11',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            colorFormat = self.config.getColorFormat()
            data = array.array('B', [0] * 1)
            formatCode = list(colorFormats.keys())[list(colorFormats.values()).index(colorFormat)]
            writeUInt8(data, formatCode, 0)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            formatCode = readUInt8(data, 0)
            if not self.validateColorFormat(formatCode):
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                colorFormat = colorFormats[formatCode]
                try:
                    self.config.setColorFormat(colorFormat)
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except:
                    traceback.print_exc()
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def validateColorFormat(self, formatCode):
        return formatCode in colorFormats.keys()

