from pybleno import *
from tidelight.bluetooth.characteristics.offlinecharacteristics.OfflineModeCharacteristic import OfflineModeCharacteristic
from tidelight.bluetooth.characteristics.offlinecharacteristics.OfflineDownloadCharacteristic import OfflineDownloadCharacteristic
from tidelight.bluetooth.characteristics.offlinecharacteristics.HardwareClockSyncCharacteristic import HardwareClockSyncCharacteristic

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

