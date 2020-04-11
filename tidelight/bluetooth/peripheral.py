from pybleno import *
from .services.ConfigService import ConfigService
from .services.WifiService import WifiService
from .services.OfflineService import OfflineService


class Peripheral:
    def __init__(self, config):
        self.bleno = Bleno()
        self.config = config
        self.configService = ConfigService(config)
        self.wifiService = WifiService()
        self.offlineService = OfflineService(config)
        self.name = 'Tide light'
        self.uuids = ['ec00', 'ec01', 'ec02']
        self.bleno.on('stateChange', self.onStateChange)
        self.bleno.on('advertisingStart', self.onAdvertisingStart)

    #
    # Wait until the BLE radio powers on before attempting to advertise.
    # If you don't have a BLE radio, then it will never power on!
    #
    def onStateChange(self, state):
        if state == 'poweredOn':
            #
            # We will also advertise the service ID in the advertising packet,
            # so it's easier to find.
            #
            def on_startAdvertising(err):
                if err:
                    print(err)

            self.bleno.startAdvertising(self.name, self.uuids, on_startAdvertising)
        else:
            self.bleno.stopAdvertising()

    def onAdvertisingStart(self, error):
        if not error:
            print('advertising...')

            self.bleno.setServices([
                self.configService,
                self.wifiService,
                self.offlineService
            ])

    def start(self):
        self.bleno.start()

    def stop(self):
        self.bleno.stopAdvertising()
        self.bleno.disconnect()