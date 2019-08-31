print("starting tidelight script")
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
from TideLightLedStrip import TideLightLedStrip


LED_COUNT = 60
LED_PIN        = 18
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 50    # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


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
                #TODO: Connection error excaption
                except requests.Timeout:
                    tide_time_collection_lock.notify_all()
                    tide_time_collection_lock.release()
                    print("Location release")
                    time.sleep(30)
                    continue


def lighting_thread():
    global LED_COUNT
    global strip
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
                    led_string = led_string.format("o", "x"*led, "o"*(LED_COUNT - 2 - led), "x")
                else:
                    led_string = led_string.format("x", "x"*(LED_COUNT - 2 - (led-1)), "o" * (led - 1), "o")
                print(led_string)
                strip.update_tide_leds(led, direction)
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                print("Light release")
                pause.until(timestamp)



# TODO: create config file if it doesn't exist
config = configparser.ConfigParser()
config.read('config.ini')
lon = config.get('apivalues', 'lon')
lat = config.get('apivalues', 'lat')

strip = TideLightLedStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

tide_time_collection = TideTimeCollection3.TideTimeCollection(LED_COUNT)
tide_time_collection_lock = threading.Condition()

api = TideApi(lon, lat)
location_data_thread = threading.Thread(target=get_location_data_thread, args=(api,))
lighting_thread = threading.Thread(target=lighting_thread)
location_data_thread.start()
lighting_thread.start()
