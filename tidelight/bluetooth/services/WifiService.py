from pybleno import *
from ..characteristics.WifiScanCharacteristic import WifiScanCharacteristic
from ..characteristics.AddWifiCharacteristic import AddWifiCharacteristic

class WifiService(BlenoPrimaryService):
    uuid = 'ec01'
    def __init__(self):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec01',
          'characteristics': [
              WifiScanCharacteristic(),
              AddWifiCharacteristic()
          ]})
