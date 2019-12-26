print("starting tidelight script")
import sys
import RPi.GPIO as GPIO

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
from math import sqrt,cos,sin,radians

LED_COUNT = 60
LED_PIN = 18
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 50  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

def scale_and_invert(oldmin, oldmax, newmin, newmax, oldvalue):
    if oldvalue > oldmax:
        oldvalue = oldmax
    if oldvalue < oldmin:
        oldvalue = oldmin
    non_inverted = int((((oldvalue - oldmin)*(newmax - newmin))/(oldmax - oldmin)) + newmin)
    middle = int((newmin + newmax)/2)
    temp = middle - non_inverted
    return middle + temp


def rc_time(pin_to_circuit):
    count = 0

    # Output on the pin for
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)

    # Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)

    # Count until the pin goes high
    while (GPIO.input(pin_to_circuit) == GPIO.LOW):
        count += 1

    return count



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

def strip_controller_thread(strip, strip_lock, led_queue, led_count):
    #get the first data about led and direction from the lighting_thread
    first_time_data = led_queue.get()
    led = first_time_data.led
    direction = first_time_data.direction
    with strip_lock:
        strip.update_tide_leds(led, direction)
        strip_lock.notify_all()
    while True:
        with strip_lock:
            if not led_queue.empty():
                new_data = led_queue.get()
                led = new_data.led
                direction = new_data.direction
                strip.update_tide_leds(led, direction)
            moving_colors_top = [Color(0, 0, 255), Color(0, 75, 255), Color(0, 150, 255)]
            moving_colors_bottom = [Color(128, 0, 128), Color(128, 0, 64), Color(128, 0, 0)]
            led_wave(strip, led, direction, led_count, moving_colors_top, moving_colors_bottom, Color(128,0,128), Color(0, 0, 255), 0.5)
            strip_lock.notify_all()


def ldr_controller_thread(strip, strip_lock):
    brightness = LED_BRIGHTNESS
    while True:
        count = rc_time(ldr_pin)
        new_brightness = scale_and_invert(1, 500000, 1, 100, count)
        if new_brightness != brightness:
            with strip_lock:
                strip.setBrightness(new_brightness)
                brightness = new_brightness
                strip_lock.notify_all()



# TODO: create config file if it doesn't exist
GPIO.setmode(GPIO.BOARD)
ldr_pin = 11
config = configparser.ConfigParser()
config.read('config.ini')
lon = config.get('apivalues', 'lon')
lat = config.get('apivalues', 'lat')

strip = TideLightLedStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip_lock = threading.Condition()
strip.begin()

led_queue = Queue()


tide_time_collection = TideTimeCollection3.TideTimeCollection(LED_COUNT)
tide_time_collection_lock = threading.Condition()

api = TideApi(lon, lat)
location_data_thread = threading.Thread(target=get_location_data_thread, args=(api,))
lighting_thread = threading.Thread(target=lighting_thread, args=(led_queue,))
controller_thread = threading.Thread(target=strip_controller_thread, args=(strip, strip_lock, led_queue, LED_COUNT))
ldr_thread = threading.Thread(target=ldr_controller_thread, args=(strip, strip_lock))
location_data_thread.start()
lighting_thread.start()
controller_thread.start()
ldr_thread.start()




def led_wave(strip, led, direction, led_count, moving_colors_top, moving_colors_bottom, still_color_top, still_color_bottom, speed):
    # If going to tide
    color_queue = Queue()
    for i in range(len(moving_colors_top)):
        color_queue.put((moving_colors_top[i], moving_colors_bottom[i]))
    if direction:
        for i in range(1, led_count - 1):
            color_set = color_queue.get()
            color_queue.put(color_set)
            if i <= led:
                strip.setPixelColor(i, color_set[1])
            else:
                strip.setPixelColor(i, color_set[0])

            previous_led = (i - color_queue.qsize()) % (led_count - 2)
            if previous_led == 0:
                previous_led = led_count - 2
            if previous_led <= led:
                strip.setPixelColor(previous_led, still_color_bottom)
            else:
                strip.setPixelColor(previous_led, still_color_top)
            strip.show()
            time.sleep(speed)
    else:
        for i in range(led_count - 2, 0, -1):
            color_set = color_queue.get()
            color_queue.put(color_set)
            if i <= led_count - 1 - led:
                strip.setPixelColor(i, color_set[1])
            else:
                strip.setPixelColor(i, color_set[0])

            previous_led = (i + color_queue.qsize()) % (led_count - 2)
            if previous_led == 0:
                previous_led = led_count - 2
            if previous_led <= led_count - 1 - led:
                strip.setPixelColor(previous_led, still_color_bottom)
            else:
                strip.setPixelColor(previous_led, still_color_top)
            strip.show()
            time.sleep(speed)

