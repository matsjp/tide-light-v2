from pybleno import *
from tidelight.bluetooth.characteristics.wificharacteristics.WifiScanCharacteristic import WifiScanCharacteristic
from tidelight.bluetooth.characteristics.wificharacteristics.AddWifiCharacteristic import AddWifiCharacteristic

class WifiService(BlenoPrimaryService):
    uuid = 'ec01'
    def __init__(self):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec01',
          'characteristics': [
              WifiScanCharacteristic(),
              AddWifiCharacteristic()
          ]})
