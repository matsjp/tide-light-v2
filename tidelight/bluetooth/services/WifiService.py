from pybleno import *
from bluetooth.characteristics.wificharacteristics.WifiScanCharacteristic import WifiScanCharacteristic
from bluetooth.characteristics.wificharacteristics.AddWifiCharacteristic import AddWifiCharacteristic
from bluetooth.characteristics.wificharacteristics.InternetConnectionCharacteristic import InternetConnectionCharacteristic

class WifiService(BlenoPrimaryService):
    uuid = 'ec01'
    def __init__(self):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec01',
          'characteristics': [
              WifiScanCharacteristic(),
              AddWifiCharacteristic(),
              InternetConnectionCharacteristic()
          ]})
