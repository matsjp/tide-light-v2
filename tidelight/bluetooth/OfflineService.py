from pybleno import *
from .OfflineModeCharacteristic import OfflineModeCharacteristic
from .OfflineDownloadCharacteristic import OfflineDownloadCharacteristic

class OfflineService(BlenoPrimaryService):
    uuid = 'ec02'
    def __init__(self, config):
        BlenoPrimaryService.__init__(self, {
          'uuid': 'ec02',
          'characteristics': [
              OfflineModeCharacteristic(config),
              OfflineDownloadCharacteristic(config)
              
          ]})

