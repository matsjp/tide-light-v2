from pybleno import *
import array
import traceback
from wifi import Cell

class WifiScanCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': 'ec0f',
            'properties': ['write', 'notify'],
            'value': None
          })
          
        self._value = None
        self._updateValueCallback = None

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        elif readUInt8(data, 0) != 0x1:
            callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
        else:
            try:
                #TODO scan in a new thread
                #When a new scanning request arrives check if it is already scanning
                cells = Cell.all('wlan0')
                for cell in cells:
                    cellString = ''
                    cellString += cell.ssid
                    if cell.encrypted:
                        cellString += ':' + cell.encryption_type
                    notificationData = array.array('B', [0] * len(cellString))
                    for i in range(len(cellString)):
                        writeUInt8(notificationData, ord(cellString[i]), i)
                    self._updateValueCallback(notificationData)
                callback(Characteristic.RESULT_SUCCESS)
                    
                
            except:
                traceback.print_exc()
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def onSubscribe(self, maxValueSize, updateValueCallback):
        print('EchoCharacteristic - onSubscribe')
        
        self._updateValueCallback = updateValueCallback

    def onUnsubscribe(self):
        print('EchoCharacteristic - onUnsubscribe');
        
        self._updateValueCallback = None



