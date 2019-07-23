from datetime import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET

from tidelight import TideTimeCollection, TideTime


def get_next_time_from():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def get_next_time_to():
    time = datetime.now() + timedelta(days=7)
    return time.strftime("%Y-%m-%dT%H:%M")


def get_next_api_run():
    return datetime.now() + timedelta(days=1)


def get_TideTimeCollection_from_xml_string(xml_string):
    tide_time_collection = TideTimeCollection()
    tide = ET.fromstring(xml_string)
    locationdata = tide[1]
    data = locationdata[2]
    for waterlevel in data:
        tide = waterlevel.attrib["flag"] == "low"
        timestring = waterlevel.attrib["time"]
        timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2 : ]
        timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
        tide_time_collection.insert_tide_time(TideTime(tide=tide, timestamp=timestamp))
    return tide_time_collection
