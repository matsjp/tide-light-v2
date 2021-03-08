from datetime import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET
import configparser
import os
import json
from rpi_ws281x import Color

from tidetime import TideTime
try:
    import httplib
except:
    import http.client as httplib


def get_next_time_from():
    d = datetime.now() + timedelta(days=-1)
    return d.strftime("%Y-%m-%dT%H:%M")


def get_next_time_to():
    time = datetime.now() + timedelta(days=1000)
    return time.strftime("%Y-%m-%dT%H:%M")


def get_next_api_run():
    return (datetime.now() + timedelta(days=1)).timestamp()


def get_time_in_30s():
    return (datetime.now() + timedelta(seconds=30)).timestamp()


def get_time_in_1day():
    return (datetime.now() + timedelta(days=1)).timestamp()


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


def color_string_to_color(color_string):
    color = json.loads(color_string)
    return Color(color[0], color[1], color[2])


def colors_string_to_list(colors_string):
    colors_list = json.loads(colors_string)
    colors = []
    for c in colors_list:
        colors.append(c[0], c[1], c[2])
    return colors


def internetConnection():
    conn = httplib.HTTPConnection("www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except:
        conn.close()
        return False


def color_converter(color, color_format):
    color_list = json.loads(color)
    if color_format == "bgr":
        return Color(color_list[2], color_list[1], color_list[0])
    else:
        return Color(color_list[0], color_list[1], color_list[2])


def colors_converter(colors, color_format):
    temp_colors_list = json.loads(colors)
    colors_list = []
    if color_format == "bgr":
        for color in temp_colors_list:
            colors_list.append(Color(color[2], color[1], color[0]))
        return colors_list
    else:
        for color in temp_colors_list:
            colors_list.append(Color(color[0], color[1], color[2]))
        return colors_list
