from pybleno import *
from ..characteristics.OfflineModeCharacteristic import OfflineModeCharacteristic
from ..characteristics.OfflineDownloadCharacteristic import OfflineDownloadCharacteristic

class OfflineService(BlenoPrimaryService):
    uuid = 'ec02'
    def __init__(self, config):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec02',
          'characteristics': [
              OfflineModeCharacteristic(config),
              OfflineDownloadCharacteristic(config)
              
          ]})

