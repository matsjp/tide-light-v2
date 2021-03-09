from pybleno import *
import array
import traceback
import logging
from kartverket_tide_api.parsers import LocationDataParser
from kartverket_tide_api.exceptions import CannotFindElementException
from xml.etree.ElementTree import ParseError

class OfflineDataCharacteristic(Characteristic):
    CYBLE_GATT_ERR_HTS_OUT_OF_RANGE = 0x80

    NO_PROBLEM = 0x1
    TOO_LITTLE_DATA_ERROR = 0x2
    FILE_NOT_FOUND_ERROR = 0x3
    PARSE_ERROR = 0x4
    UNKNOWN_ERROR = 0x5

    def __init__(self):
        Characteristic.__init__(self, {
            'uuid': 'ec10',
            'properties': ['read'],
            'value': None
          })
          
        self._value = None
    

    def onReadRequest(self, offset, callback):
        if offset:
            callback(Characteristic.RESULT_ATTR_NOT_LONG, None)
        else:
            try:
                with open('offline.xml', 'r') as xmlfile:
                    xml = xmlfile.read()
                parser = LocationDataParser(xml)
                waterlevels = parser.parse_response()['data']
                if len(waterlevels) < 50:
                    result = self.TOO_LITTLE_DATA_ERROR
                else:
                    result = self.NO_PROBLEM


            except FileNotFoundError as e:
                result = self.FILE_NOT_FOUND_ERROR
            except ParseError as e:
                print(e)
                result = self.PARSE_ERROR
            except CannotFindElementException as e:
                print(e)
                result = self.PARSE_ERROR
            except Exception as e:
                print(e)
                result = self.UNKNOWN_ERROR
            finally:
                data = array.array('B', [0] * 1)
                writeUInt8(data, result, 0)
                callback(Characteristic.RESULT_SUCCESS, data)



