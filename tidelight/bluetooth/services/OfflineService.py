from pybleno import *
from bluetooth.characteristics.offlinecharacteristics.HardwareClockSyncCharacteristic import HardwareClockSyncCharacteristic
from bluetooth.characteristics.offlinecharacteristics.OfflineDataCharacteristic import OfflineDataCharacteristic

class OfflineService(BlenoPrimaryService):
    uuid = 'ec02'
    def __init__(self, config):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec02',
          'characteristics': [
              HardwareClockSyncCharacteristic(),
              OfflineDataCharacteristic()
          ]})

