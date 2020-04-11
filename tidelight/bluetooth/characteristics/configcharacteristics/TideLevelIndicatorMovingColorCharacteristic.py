from pybleno import *
import array
import traceback
import re

class TideLevelIndicatorMovingColorCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec16',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            color = self.config.getTideLevelIndicatorMovingColor()
            colorList = re.findall('\d+', color)
            data = array.array('B', [0] * len(colorList))
            for i in range(len(colorList)):
                writeUInt8(data, int(colorList[i]), i)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data)%3 != 0:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            split = self.splitList(data)
            colorsList = []
            for color in split:
                colorsList.append('[{},{},{}]'.format(*color))
            colorsString = '['
            for i in range(len(colorsList)):
                colorsString += colorsList[i]
                if i != len(colorsList) - 1:
                    colorsString += ','
            colorsString += ']'
            if not self.config.validateColors(colorsString):
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                try:
                    self.config.setTideLevelIndicatorMovingColor(colorsString)
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except:
                    traceback.print_exc()
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def splitList(self, lst):
        split = []
        for i in range(int(len(lst) / 3)):
            sub = list()
            for j in range(3):
                sub.append(readUInt8(lst, 3*i + j))
            split.append(sub)
        return split
    






