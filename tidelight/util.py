from datetime import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET

from tidelight import TideTimeCollection, TideTime


def get_next_time_from():
    d = datetime.now() + timedelta(days=-1)
    return d.strftime("%Y-%m-%dT%H:%M")


def get_next_time_to():
    time = datetime.now() + timedelta(days=7)
    return time.strftime("%Y-%m-%dT%H:%M")

def get_next_api_run():
    return datetime.now() + timedelta(days=1)

def get_time_in_30s():
    return datetime.now() + timedelta(seconds=30)


def get_TideTimeCollection_from_xml_string(xml_string):
    tide_times = []
    tide = ET.fromstring(xml_string)
    locationdata = tide[0]
    data = locationdata[2]
    for waterlevel in data:
        tide = (waterlevel.attrib["flag"] == "high")
        timestring = waterlevel.attrib["time"]
        timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2 : ]
        timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
        tide_times.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))

    return tide_times
