from pybleno import *
import array
import traceback
from kartverket_tide_api import TideApi
from kartverket_tide_api.parsers import LocationDataParser

class OfflineDownloadCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    def __init__(self, config):
        Characteristic.__init__(self, {
            'uuid': 'ec10',
            'properties': ['read', 'write'],
            'value': None
          })
        self.api = TideApi()
        self.config = config
        self.lat, self.lon = config.getLatLon()
        self.xmlPath = 'offline.xml'
          
    def onReadRequest(self, offset, callback):
        #TODO
        
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            #TODO: what if theres no such file
            with open(self.xmlPath, 'r') as xmlfile:
                xml = xmlfile.read()
            parser = LocationDataParser(xml)
            waterlevels = parser.parse_response()['data']
            fromTime = waterlevels[0].time[:10]
            toTime = waterlevels[len(waterlevels) - 1].time[:10]
            dataString = fromTime + ':' + toTime
            data = array.array('B', [0] * len(dataString))
            for i in range(len(dataString)):
                writeUInt8(data, ord(dataString[i]), i)
            callback(Characteristic.RESULT_SUCCESS, data);

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG)
        else:
            dataString = ''
            for i in range(len(data)):
                dataString += chr(readUInt8(data, i))
            
            try:
                #TODO validate strings
                index = dataString.index(':')
                fromTime = dataString[:index]
                toTime = dataString[index + 1:]
                #TODO validate downloaded data
                api = TideApi()
                response = api.get_location_data(self.lon, self.lat, fromTime, toTime, 'TAB')
                with open(self.xmlPath, 'w+') as xmlfile:
                    xmlfile.write(response)
                callback(Characteristic.RESULT_SUCCESS)
            except ValueError as e:
                print(e)
                print('ValueError')
                callback(self.CYBLE_GATT_ERR_HTS_OUT_OF_RANGE)
            except:
                traceback.print_exc()
                callback(Characteristic.RESULT_UNLIKELY_ERROR)
        




