from pybleno import *
import subprocess

class HardwareClockSyncCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': 'ec11',
            'properties': ['write', 'read'],
            'value': None
          })

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            dateString = ''
            for i in range(len(data)):
                dateString += chr(readUInt8(data, i))
            try:
                shellResult = subprocess.run(['date', '-s', '{}'.format(dateString)], stdout=subprocess.PIPE).stdout.decode('utf-8')
                print('New date: ' + shellResult)
                shellResult = subprocess.run(['hwclock', '-w'], stdout=subprocess.PIPE).stdout.decode('utf-8')
                print('New hwclock: ' + subprocess.run(['hwclock', '-r'], stdout=subprocess.PIPE).stdout.decode('utf-8'))
                callback(Characteristic.RESULT_SUCCESS)
            except:
                traceback.print_exc()
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
        
    def onReadRequest(self, offset, callback):
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            date = subprocess.run(['date'], stdout=subprocess.PIPE).stdout.decode("utf-8")
            
            data = array.array('B', [0] * len(date))
            for i in range(len(date)):
                writeUInt8(data, ord(date[i]), i)
            callback(Characteristic.RESULT_SUCCESS, data);
                    
