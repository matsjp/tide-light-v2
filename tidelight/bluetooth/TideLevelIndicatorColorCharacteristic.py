from pybleno import *
import array
import struct
import sys
import traceback
from builtins import str
from .Config import *
import traceback
import re

class TideLevelIndicatorColorCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec14',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            color = self.config.getTideLevelIndicatorColor()
            colorList = re.findall('\d+', color)
            data = array.array('B', [0] * 3)
            for i in range(3):
                writeUInt8(data, int(colorList[i]), i)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 3:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            colorList = []
            for i in range(3):
                colorList.append(readUInt8(data, i))
            color = '[{},{},{}]'.format(*colorList)
            if not self.config.validateColor(color):
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                try:
                    self.config.setTideLevelIndicatorColor(color)
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except:
                    traceback.print_exc()
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
    




