from pybleno import *
import subprocess

class HardwareClockSyncCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80
    RESET_COMMAND = 0x1

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': 'ec11',
            'properties': ['write'],
            'value': None
          })

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        elif len(data) != 1:
            callback(Characteristic.RESULT_INVALID_ATTRIBUTE_LENGTH)
        else:
            code = readUInt8(data, 0)
            if code != 0x1:
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            else:
                try:
                    subprocess.run(['hwclock', '-w'])
                    callback(Characteristic.RESULT_SUCCESS)
                except Exception as e:
                    raise e
                    