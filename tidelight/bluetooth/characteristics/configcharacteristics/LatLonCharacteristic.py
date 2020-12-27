from pybleno import *
import array
from Config import *
import traceback

class LatLonCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec1b',
            'properties': ['read', 'write', 'notify'],
            'value': None
          })
          
        self.config = config
        self._value = None
        self._updateValueCallback = None
          
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            lat, lon = self.config.getLatLon()
            dataString = lat + ':' + lon
            data = array.array('B', [0] * len(dataString))
            for i in range(len(dataString)):
                writeUInt8(data, ord(dataString[i]), i)
            callback(Characteristic.RESULT_SUCCESS, data)

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            dataString = ''
            for i in range(len(data)):
                dataString += chr(readUInt8(data, i))
            
            try:
                index = dataString.index(':')
                lat = ast.literal_eval(dataString[:index])
                lon = ast.literal_eval(dataString[index + 1:])
                self.config.setLatLon(lat, lon)
                callback(Characteristic.RESULT_SUCCESS)
            except ValueError as e:
                print(e)
                print('ValueError')
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            except:
                traceback.print_exc()
                callback(Characteristic.RESULT_UNLIKELY_ERROR)

    def onSubscribe(self, maxValueSize, updateValueCallback):
        print('EchoCharacteristic - onSubscribe')

        self._updateValueCallback = updateValueCallback

    def onUnsubscribe(self):
        print('EchoCharacteristic - onUnsubscribe')

        self._updateValueCallback = None

    def notify(self, data):
        print("Sending notification")
        self._updateValueCallback(data)



