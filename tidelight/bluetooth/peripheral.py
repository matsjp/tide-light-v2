from pybleno import *
from .Config import Config
from .ConfigService import ConfigService
from .WifiService import WifiService
from .OfflineService import OfflineService
import threading
import time

bleno = Bleno()
config = Config()
configService = ConfigService(config)
wifiService = WifiService()
offlineService = OfflineService(config)

name = 'Tide light'
uuids = ['ec00', 'ec01', 'ec02']

#
# Wait until the BLE radio powers on before attempting to advertise.
# If you don't have a BLE radio, then it will never power on!
#
def onStateChange(state):
    if (state == 'poweredOn'):
        #
        # We will also advertise the service ID in the advertising packet,
        # so it's easier to find.
        #
        def on_startAdvertising(err):
            if err:
                print(err)

        bleno.startAdvertising(name, uuids, on_startAdvertising)
    else:
        bleno.stopAdvertising();
bleno.on('stateChange', onStateChange)
    
def onAdvertisingStart(error):
    if not error:
        print('advertising...')
        
        bleno.setServices([
            configService,
            wifiService,
            offlineService
        ])
bleno.on('advertisingStart', onAdvertisingStart)

def bluetooth():
    bleno.start()
    while True:
        time.sleep(100)

