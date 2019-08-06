import sys

sys.path.append('../')
import configparser
from kartverkettideapi.apiwrapper.TideApi import TideApi
from tidelight import TideTimeCollection3
from tidelight.util import *
import requests
import time
import threading
import pause
from datetime import datetime


def get_location_data_thread(api: TideApi):
    sleep_until = 0

    if type(api) is not TideApi:
        raise ValueError("Paramater api must be of type {}, not of type {}".format(TideApi, type(api)))
    while True:
        with tide_time_collection_lock:
            print("Location aqcuire")
            if datetime.now().timestamp() < sleep_until:
                tide_time_collection_lock.release()
                tide_time_collection_lock.notify_all()
                print("Location release")
                pause.until(sleep_until)
            else:
                try:
                    response = api.get_location_data(get_next_time_from(), get_next_time_to())
                    print(response)
                    coll = get_TideTimeCollection_from_xml_string(response)
                    now = datetime.now().timestamp()

                    tide_time_collection.insert_tide_times(coll, now)

                    tide_time_collection_lock.notify_all()
                    tide_time_collection_lock.release()
                    print("Location release")
                    pause.until(get_next_api_run())
                except requests.Timeout:
                    tide_time_collection_lock.notify_all()
                    tide_time_collection_lock.release()
                    print("Location release")
                    time.sleep(30)
                    continue


def lighting_thread():
    global led_count
    while True:
        tide_time_collection_lock.acquire()
        print("Light acquire")
        if tide_time_collection.is_empty():
            tide_time_collection_lock.notify_all()
            tide_time_collection_lock.release()
            print("Light release")
            time.sleep(30)
        else:
            now = datetime.now().timestamp()
            #TODO: better variable name
            time_stamp_collection = tide_time_collection.get_timestamp_collection(now)
            if time_stamp_collection is None:
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                print("Light release")
                time.sleep(30)
            else:
                print(time_stamp_collection)
                timestamp = time_stamp_collection[0]
                led = time_stamp_collection[1]
                direction = time_stamp_collection[2]
                led_string = "{} {}{} {}"
                if direction:
                    led_string = led_string.format("o", "x"*led, "o"*(led_count - led), "x")
                else:
                    led_string = led_string.format("x", "x"*(led_count - (led-1)), "o" * (led - 1), "o")
                print(led_string)
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                print("Light release")
                pause.until(timestamp)



# TODO: create config file if it doesn't exist
config = configparser.ConfigParser()
config.read('config.ini')
lon = config.get('apivalues', 'lon')
lat = config.get('apivalues', 'lat')

led_count = 60

tide_time_collection = TideTimeCollection3.TideTimeCollection(led_count)
tide_time_collection_lock = threading.Condition()

api = TideApi(lon, lat)
location_data_thread = threading.Thread(target=get_location_data_thread, args=(api,))
lighting_thread = threading.Thread(target=lighting_thread)
location_data_thread.start()
lighting_thread.start()
