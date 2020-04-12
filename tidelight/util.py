from datetime import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET
import configparser
import os

from tidetime import TideTime


def get_next_time_from():
    d = datetime.now() + timedelta(days=-1)
    return d.strftime("%Y-%m-%dT%H:%M")


def get_next_time_to():
    time = datetime.now() + timedelta(days=7)
    return time.strftime("%Y-%m-%dT%H:%M")


def get_next_api_run():
    return (datetime.now() + timedelta(days=1)).timestamp()


def get_time_in_30s():
    return (datetime.now() + timedelta(seconds=30)).timestamp()


def get_TideTimeCollection_from_xml_string(xml_string):
    tide_times = []
    tide = ET.fromstring(xml_string)
    locationdata = tide[0]
    data = locationdata[2]
    for waterlevel in data:
        tide = (waterlevel.attrib["flag"] == "high")
        timestring = waterlevel.attrib["time"]
        timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
        timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
        tide_times.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))

    return tide_times


def configExists():
    return os.path.exists('config.ini')


def defaultConfig():
    path = 'config.ini'
    apivalues = {
        'lat': '59.908',
        'lon': '10.734'
    }
    ledstrip = {
        'led_count': '60',
        'led_pin': '18',
        'led_freq_hz': '800000',
        'led_dma': '10',
        'led_brightness': '100',
        'led_invert': 'False',
        'led_channel': '0'
    }
    ldr = {
        'ldr_pin': '11',
        'ldr_active': 'True'
    }
    color = {
        'color_format': 'rgb',
        'high_tide_direction_color': '[24,255,4]',
        'low_tide_direction_color': '[255,0,0]',
        'tide_level_indicator_color': '[0,0,255]',
        'no_tide_level_indicator_color': '[128,0,128]',
        'tide_level_indicator_moving_color': '[[255,105,115],[255,159,176],[100,100,255]]',
        'no_tide_level_indicator_moving_color': '[[91,73,255],[73,164,255],[73,255,255]]',
        'moving_pattern': 'wave',
        'moving_speed': '0.5',
    }
    offline = {
        'offline_mode': 'False'
    }
    config = configparser.ConfigParser()
    config['apivalues'] = apivalues
    config['ledstrip'] = ledstrip
    config['ldr'] = ldr
    config['color'] = color
    config['offline'] = offline

    config.write(open(path, 'w+'))
