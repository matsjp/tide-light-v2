print("starting tidelight script")
import sys
import RPi.GPIO as GPIO

sys.path.append('../')
import configparser
from kartverket_tide_api import TideApi
from kartverket_tide_api.parsers import LocationDataParser
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
import ast
import re
import json

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
    next_run = 0

    if type(api) is not TideApi:
        raise ValueError("Paramater api must be of type {}, not of type {}".format(TideApi, type(api)))
    while True:
        print('Before aqcuiring')
        with tide_time_collection_lock:
            print("Location aqcuire")
            if datetime.now().timestamp() < next_run:
                tide_time_collection_lock.notify_all()
                print("Location release")
                next_run = get_time_in_30s()
            else:
                try:
                    print("sending request")
                    response = api.get_location_data(lon, lat, get_next_time_from(), get_next_time_to(), 'TAB')
                    
                    print(response)
                    #TODO handle parsing exceptions
                    parser = LocationDataParser(response)
                    waterlevels = parser.parse_response()['data']
                    coll = []
                    for waterlevel in waterlevels:
                        #TODO what to do if tide is None
                        tide = waterlevel.tide
                        timestring = waterlevel.time
                        timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2 : ]
                        timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                        #TODO figure out difference between time and timestamp. Why didn't past myself properly document that
                        coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))
                        
                    now = datetime.now().timestamp()

                    tide_time_collection.insert_tide_times(coll, now)

                    tide_time_collection_lock.notify_all()
                    print("Location release")
                    next_run = get_next_api_run()
                except requests.Timeout as e:
                    tide_time_collection_lock.notify_all()
                    print(e + "     |Connection timeout")
                    print("Location release")
                    next_run = get_time_in_30s()
                    continue
                except requests.ConnectionError as e:
                    print(e + "     |Connection error")
                    next_run = get_time_in_30s()
                    continue
                except requests.TooManyRedirects as e:
                    print(e + "     |TooManyRedirects")
                    next_run = get_time_in_30s()
                    continue
                except:
                    print("Error occured: ", sys.exc_info()[0])
                    next_run = get_time_in_30s()
                    continue
        pause.until(next_run)


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

def strip_controller_thread(strip, strip_lock, led_queue, led_count, moving_speed, moving_pattern):
    #get the first data about led and direction from the lighting_thread
    first_time_data = led_queue.get()
    led = first_time_data.led
    direction = first_time_data.direction
    with strip_lock:
        strip.update_tide_leds(led, direction, high_tide_direction_color,
                               low_tide_direction_color, tide_level_indicator_color,
                                no_tide_level_indicator_color)
        strip_lock.notify_all()
    while True:
        if not led_queue.empty():
            new_data = led_queue.get()
            led = new_data.led
            direction = new_data.direction
            with strip_lock:
                strip.update_tide_leds(led, direction, high_tide_direction_color,
                                       low_tide_direction_color, tide_level_indicator_color,
                                        no_tide_level_indicator_color)
                strip_lock.notify_all()
        if moving_pattern == 'wave':
            led_wave(strip, led, direction, led_count, no_tide_level_indicator_moving_colors,
                     tide_level_indicator_moving_colors, no_tide_level_indicator_color, tide_level_indicator_color, moving_speed, strip_lock)
        elif moving_pattern == 'regular':
            pass
        else:
            time.sleep(1)


def ldr_controller_thread(strip, strip_lock):
    brightness = LED_BRIGHTNESS
    while True:
        count = rc_time(ldr_pin)
        new_brightness = scale_and_invert(1, 500000, 10, 100, count)
        if new_brightness != brightness:
            with strip_lock:
                strip.setBrightness(new_brightness)
                brightness = new_brightness
                strip_lock.notify_all()

#Regex that is used to validate the list of colors
#Format is [[45,23,56],[1,12,255]] etc
#List of lists containing rgb color
regex_color_list = '^\[(\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]'\
'{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9'\
']{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-'\
'9]{2}|2[0-4][0-9]|25[0-5])\],)*\[([0-9]|[1-8][0-9]|9[0-'\
'9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0'\
'-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9['\
'0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\]\]$|^\[\]$'

#Regex that is used to validate a single color
#Format is [123,255,12]
#Is a single rgb color
regex_single_color = '^\[([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{'\
'2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9]'\
'{2}|2[0-4][0-9]|25[0-5]),([0-9]|[1-8][0-9]|9[0-9]|1[0-9'\
']{2}|2[0-4][0-9]|25[0-5])\]$'

# TODO: create config file if it doesn't exist
GPIO.setmode(GPIO.BOARD)
config = configparser.ConfigParser()
config.read('config.ini')
lon = config.get('apivalues', 'lon')
lat = config.get('apivalues', 'lat')

LED_COUNT = ast.literal_eval(config.get('ledstrip', 'LED_COUNT'))
LED_PIN = ast.literal_eval(config.get('ledstrip', 'LED_PIN'))
LED_FREQ_HZ = ast.literal_eval(config.get('ledstrip', 'LED_FREQ_HZ'))
LED_DMA = ast.literal_eval(config.get('ledstrip', 'LED_DMA'))
LED_BRIGHTNESS = ast.literal_eval(config.get('ledstrip', 'LED_BRIGHTNESS'))
LED_INVERT = ast.literal_eval(config.get('ledstrip', 'LED_INVERT'))
LED_CHANNEL = ast.literal_eval(config.get('ledstrip', 'LED_CHANNEL'))

ldr_pin = ast.literal_eval(config.get('ldr', 'ldr_pin'))
ldr_active = ast.literal_eval(config.get('ldr', 'ldr_active'))

#TODO: make excaptions for all these possible errors
color_format = config.get('color', 'color_format')
if color_format not in ['rgb', 'bgr']:
    print('Color_format must be "rgb" or "bgr"')
    exit()
high_tide_direction_color_string = config.get('color', 'high_tide_direction_color')
if not re.match(regex_single_color, high_tide_direction_color_string):
    print('high_tide_direction_color must have the following format: [23,43,34] where'\
          'the digit is between 0 and 255')
    exit()
htdc_list = json.loads(high_tide_direction_color_string)

low_tide_direction_color_string = config.get('color', 'low_tide_direction_color')
if not re.match(regex_single_color, low_tide_direction_color_string):
    print('low_tide_direction_color must have the following format: [23,43,34] where'\
          'the digit is between 0 and 255')
    exit()
ltdc_list = json.loads(low_tide_direction_color_string)

tide_level_indicator_color_string = config.get('color', 'tide_level_indicator_color')
if not re.match(regex_single_color, tide_level_indicator_color_string):
    print('tide_level_indicator_color must have the following format: [23,43,34] where'\
          'the digit is between 0 and 255')
    exit()
tlic_list = json.loads(tide_level_indicator_color_string)

no_tide_level_indicator_color_string = config.get('color', 'no_tide_level_indicator_color')
if not re.match(regex_single_color, no_tide_level_indicator_color_string):
    print('no_tide_level_indicator_color must have the following format: [23,43,34] where'\
          'the digit is between 0 and 255')
    exit()
ntlic_list = json.loads(no_tide_level_indicator_color_string)

tide_level_indicator_moving_color_string = config.get('color', 'tide_level_indicator_moving_color')
if not re.match(regex_color_list, tide_level_indicator_moving_color_string):
    print('tide_level_indicator_moving_color must have the following format: [[23,43,34],[13,255,1]] etc where'\
          'the digit is between 0 and 255')
    exit()
tlimc_list = json.loads(tide_level_indicator_moving_color_string)

no_tide_level_indicator_moving_color_string = config.get('color', 'no_tide_level_indicator_moving_color')
if not re.match(regex_color_list, no_tide_level_indicator_moving_color_string):
    print('no_tide_level_indicator_moving_color must have the following format: [[23,43,34],[13,255,1]] etc where'\
          'the digit is between 0 and 255')
    exit()
ntlimc_list = json.loads(no_tide_level_indicator_moving_color_string)

if len(ntlimc_list) != len(tlimc_list):
    print('The number of rgbs in each moving tide indicator must be equal')
    exit()

if color_format == 'rgb':
    high_tide_direction_color = Color(htdc_list[0], htdc_list[1], htdc_list[2])
    low_tide_direction_color = Color(ltdc_list[0], ltdc_list[1], ltdc_list[2])
    tide_level_indicator_color = Color(tlic_list[0], tlic_list[1], tlic_list[2])
    no_tide_level_indicator_color = Color(ntlic_list[0], ntlic_list[1], ntlic_list[2])
    
    tide_level_indicator_moving_colors = []
    for color in tlimc_list:
        tide_level_indicator_moving_colors.append(Color(color[0], color[1], color[2]))
    no_tide_level_indicator_moving_colors = []
    for color in ntlimc_list:
        no_tide_level_indicator_moving_colors.append(Color(color[0], color[1], color[2]))
else:
    high_tide_direction_color = Color(htdc_list[2], htdc_list[1], htdc_list[0])
    low_tide_direction_color = Color(ltdc_list[2], ltdc_list[1], ltdc_list[0])
    tide_level_indicator_color = Color(tlic_list[2], tlic_list[1], tlic_list[0])
    no_tide_level_indicator_color = Color(ntlic_list[2], ntlic_list[1], ntlic_list[0])
    
    tide_level_indicator_moving_colors = []
    for color in tlimc_list:
        tide_level_indicator_moving_colors.append(Color(color[2], color[1], color[0]))
    no_tide_level_indicator_moving_colors = []
    for color in ntlimc_list:
        no_tide_level_indicator_moving_colors.append(Color(color[2], color[1], color[0]))
    

moving_speed = ast.literal_eval(config.get('color', 'moving_speed'))
moving_pattern = config.get('color', 'moving_pattern')
if moving_pattern not in ['no', 'wave', 'regular']:
    print('moving_pattern must be no, wave or regular')
    exit()

if (moving_pattern in ['wave', 'regular'] and
    (len(tide_level_indicator_moving_colors) == 0
     or len(no_tide_level_indicator_moving_colors) == 0)):
    print('For moving patterns you need colors. They cannot be []')
    exit()


strip = TideLightLedStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip_lock = threading.Condition()
strip.begin()

led_queue = Queue()


tide_time_collection = TideTimeCollection3.TideTimeCollection(LED_COUNT)
tide_time_collection_lock = threading.Condition()

api = TideApi()
location_data_thread = threading.Thread(target=get_location_data_thread, args=(api,))
lighting_thread = threading.Thread(target=lighting_thread, args=(led_queue,))
controller_thread = threading.Thread(target=strip_controller_thread, args=(strip, strip_lock, led_queue, LED_COUNT, moving_speed, moving_pattern))
ldr_thread = threading.Thread(target=ldr_controller_thread, args=(strip, strip_lock))
print('starting location data thread')
location_data_thread.start()
print('starting lighting thread')
lighting_thread.start()
print('starting controller thread')
controller_thread.start()
if ldr_active:
    print('starting ldr thread')
    ldr_thread.start()




def led_wave(strip, led, direction, led_count, moving_colors_top, moving_colors_bottom, still_color_top, still_color_bottom, speed, strip_lock):
    # If going to tide
    color_queue = Queue()
    for i in range(len(moving_colors_top)):
        color_queue.put((moving_colors_top[i], moving_colors_bottom[i]))
    if direction:
        for i in range(1, led_count - 1):
            with strip_lock:
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
                strip_lock.notify_all()
            time.sleep(speed)
    else:
        for i in range(led_count - 2, 0, -1):
            with strip_lock:
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
                strip_lock.notify_all()
            time.sleep(speed)


def led_regular(strip, led, direction, led_count, moving_color_top, moving_color_bottom, still_color_top, still_color_bottom, speed):
    # If going to tide
    if direction:
        for i in range(1, led_count - 1):
            previous_led = (i - 2) % (led_count - 2)
            if previous_led == 0:
                previous_led = led_count - 2
            if previous_led <= led:
                strip.setPixelColor(previous_led, still_color_bottom)
            else:
                strip.setPixelColor(previous_led, still_color_top)
            if i <= led:
                strip.setPixelColor(i, moving_color_bottom)
            else:
                strip.setPixelColor(i, moving_color_top)
            strip.show()
            time.sleep(speed)
    else:
        for i in range(led_count - 2, 0, -1):
            previous_led = (i + 2) % (led_count - 2)
            if previous_led == 0:
                previous_led = led_count - 2
            if previous_led <= led_count - 1 - led:
                strip.setPixelColor(previous_led, still_color_bottom)
            else:
                strip.setPixelColor(previous_led, still_color_top)
            if i <= led_count - 1 - led:
                strip.setPixelColor(i, moving_color_bottom)
            else:
                strip.setPixelColor(i, moving_color_top)
            strip.show()
            time.sleep(speed)
