from pybleno import *
import array
from Config import *
import traceback

class MovingSpeedCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec1a',
            'properties': ['read', 'write'],
            'value': None
          })
          
        self.config = config
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            movingSpeed = self.config.getMovingSpeed()
            
            data = array.array('B', [0] * len(movingSpeed))
            for i in range(len(movingSpeed)):
                writeUInt8(data, ord(movingSpeed[i]), i)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            numberString = ''
            for i in range(len(data)):
                numberString += chr(readUInt8(data, i))
            try:
                movingSpeed = ast.literal_eval(numberString)
                self.config.setMovingSpeed(movingSpeed)
                callback(Characteristic.RESULT_SUCCESS)
            except ValueError:
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            except:
                traceback.print_exc()
                callback(Characteristic.RESULT_UNLIKELY_ERROR)


