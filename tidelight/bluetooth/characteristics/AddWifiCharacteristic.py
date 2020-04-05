from pybleno import *
import array
import struct
import sys
import traceback
from builtins import str
from ..Config import *
import traceback
from wifi import Cell, Scheme
import subprocess

class AddWifiCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80
    wpa_supplicant = '/etc/wpa_supplicant/wpa_supplicant.conf'

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': 'ec10',
            'properties': ['write'],
            'value': None
          })
          
        self._value = None
        self._updateValueCallback = None

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        #Receive ssid and wifi password
        #Attemot to connect
        #read should return self._value
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            dataString = ''
            for i in range(len(data)):
                dataString += chr(readUInt8(data, i))
            index = dataString.find(':')
            if index == -1:
                password = None
                ssid = dataString
            else:
                ssid = dataString[:index]
                password = dataString[index + 1:]
            try:
                lineNumber = self.wifiAdded(ssid)
                added = True
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    added = False
                else:
                    callback(Characteristic.RESULT_UNLIKELY_ERROR)
                    return
            try:
                if added:
                    #TODO: check if network has password
                    self.modifyExistingPassword(password, lineNumber)
                else:
                    self.addWifi(ssid, password)
                #TODO: determine if wifi needs to restart
                command = ['wpa_cli' ,'-i', 'wlan0' ,'reconfigure']
                subprocess.check_output(command)
                callback(Characteristic.RESULT_SUCCESS)
            except:
                traceback.print_exc()
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
    
    def addWifi(self, ssid, password):
        if password:
            network = """
network={{
    ssid=\"{}\"
    psk=\"{}\"
}}
""".format(ssid, password)
        else:
            network = """network={{
    ssid=\"{}\"
    key_mgmt=NONE
}}
""".format(ssid)
        with open(self.wpa_supplicant, 'a') as file:
            file.write(network)
        print(network)
    
    def wifiAdded(self, ssid):
        command = ['sudo', 'grep', '-nr', 'ssid="{}"'.format(ssid), self.wpa_supplicant]
        grep = subprocess.check_output(command).decode('utf-8')
        return int(grep[:grep.index(':')])
    
    def modifyExistingPassword(self, password, lineNumber):
        with open(self.wpa_supplicant, 'r') as file:
            lines = file.readlines()
        lines[lineNumber] = '    psk={}\n'.format(password)
        with open(self.wpa_supplicant, 'w') as file:
            for i in range(len(lines)):
                file.write(lines[i])
        
    
    
        



