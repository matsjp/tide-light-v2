from pybleno import *
from bluetooth.characteristics.offlinecharacteristics.OfflineModeCharacteristic import OfflineModeCharacteristic
from bluetooth.characteristics.offlinecharacteristics.OfflineDownloadCharacteristic import OfflineDownloadCharacteristic
from bluetooth.characteristics.offlinecharacteristics.HardwareClockSyncCharacteristic import HardwareClockSyncCharacteristic

class OfflineService(BlenoPrimaryService):
    uuid = 'ec02'
    def __init__(self, config):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec02',
          'characteristics': [
              OfflineModeCharacteristic(config),
              OfflineDownloadCharacteristic(config),
              HardwareClockSyncCharacteristic()
              
          ]})

