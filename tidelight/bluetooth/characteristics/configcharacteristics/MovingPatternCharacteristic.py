from pybleno import *
import array
from Config import *
import traceback
import logging

class MovingPatternCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec19',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            pattern = self.config.getMovingPattern()
            data = array.array('B', [0] * 1)
            patternCode = list(movingPatterns.keys())[list(movingPatterns.values()).index(pattern)]
            writeUInt8(data, patternCode, 0)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            patternCode = readUInt8(data, 0)
            if not self.validatePatternCode(patternCode):
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                movingPattern = movingPatterns[patternCode]
                try:
                    self.config.setMovingPattern(movingPattern)
                    callback(Characteristic.RESULT_SUCCESS)
                except ValueError:
                    callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
                except Exception as e:
                    logging.exception(e)
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def validatePatternCode(self, patternCode):
        return patternCode in movingPatterns.keys()

