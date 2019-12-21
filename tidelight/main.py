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
from queue import Queue
from rpi_ws281x import *

LED_COUNT = 60
LED_PIN = 18
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 50  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

class LedDirection:
    def __init__(self, led, direction):
        self.led = led
        self.direction = direction


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
                    print("sending request")
                    response = api.get_location_data(get_next_time_from(), get_next_time_to())
                    print(response)
                    coll = get_TideTimeCollection_from_xml_string(response)
                    now = datetime.now().timestamp()

                    tide_time_collection.insert_tide_times(coll, now)

                    tide_time_collection_lock.notify_all()
                    tide_time_collection_lock.release()
                    print("Location release")
                    pause.until(get_next_api_run())
                # TODO: Connection error excaption
                except requests.Timeout:
                    tide_time_collection_lock.notify_all()
                    tide_time_collection_lock.release()
                    print("Connection timeout")
                    print("Location release")
                    time.sleep(30)
                    continue
                except:
                    print("Error occured: ", sys.exc_info()[0])


def lighting_thread(led_queue):
    global LED_COUNT
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
            # TODO: better variable name
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
                    led_string = led_string.format("o", "x" * led, "o" * (LED_COUNT - 2 - led), "x")
                else:
                    led_string = led_string.format("x", "x" * (LED_COUNT - 2 - (led - 1)), "o" * (led - 1), "o")
                print(led_string)
                led_queue.put(LedDirection(led, direction))
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                print("Light release")
                pause.until(timestamp)

def strip_controller_thread(strip, led_queue, led_count):
    #get the first data about led and direction from the lighting_thread
    first_time_data = led_queue.get()
    led = first_time_data.led
    direction = first_time_data.direction
    strip.update_tide_leds(led, direction)
    while True:
        if not led_queue.empty():
            new_data = led_queue.get()
            led = new_data.led
            direction = new_data.direction
        led_wave(strip, led, direction, led_count, Color(255, 0, 255), Color(128,0,128), Color(0, 0, 255))


# TODO: create config file if it doesn't exist
config = configparser.ConfigParser()
config.read('config.ini')
lon = config.get('apivalues', 'lon')
lat = config.get('apivalues', 'lat')

strip = TideLightLedStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

led_queue = Queue()


tide_time_collection = TideTimeCollection3.TideTimeCollection(LED_COUNT)
tide_time_collection_lock = threading.Condition()

api = TideApi(lon, lat)
location_data_thread = threading.Thread(target=get_location_data_thread, args=(api,))
lighting_thread = threading.Thread(target=lighting_thread, args=(led_queue,))
controller_thread = threading.Thread(target=strip_controller_thread, args=(strip, led_queue, LED_COUNT))
location_data_thread.start()
lighting_thread.start()
controller_thread.start()




def led_wave(strip, led, direction, led_count, moving_color, still_color_top, still_color_bottom):
    # If going to tide

    #remove top and bottom led
    led_count = led_count - 2
    if direction:
        for i in range(1, led_count):
            if i == 1:
                if led < led_count:
                    strip.setPixelColor(led_count, still_color_top)
                else:
                    strip.setPixelColor(led_count, still_color_bottom)
            else:
                if i - 1 < led_count:
                    strip.setPixelColor(i - 1, still_color_top)
                else:
                    strip.setPixelColor(i - 1, still_color_bottom)
            strip.setPixelColor(i, moving_color)
            strip.show()
            time.sleep(0.25)
    else:
        for i in range(led_count, 0, -1):
            if i == led_count:
                if 1 > led:
                    strip.setPixelColor(1, still_color_bottom)
                else:
                    strip.setPixelColor(1, still_color_top)
            else:
                if i + 1 > led:
                    strip.setPixelColor(i + 1, still_color_bottom)
                else:
                    strip.setPixelColor(i + 1, still_color_top)
            strip.setPixelColor(i, moving_color)
            strip.show()
            time.sleep(0.25)

