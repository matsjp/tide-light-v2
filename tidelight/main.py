from xml.etree.ElementTree import ParseError

import RPi.GPIO as GPIO
from kartverket_tide_api.exceptions import CannotFindElementException

from kartverket_tide_api.parsers import LocationDataParser
from tidelight import TideTimeCollection
from tidelight.util import *
import threading
from datetime import datetime
from TideLightLedStrip import TideLightLedStrip
from queue import Queue
from threads.BluetoothThread import BluetoothThread
from threads.LdrThread import LdrThread
from threads.StripControllerThread import StripControllerThread
from threads.LightingThread import LightingThread
from threads.LocationDataThread import LocationDataThread
from ThreadManager import ThreadManager

manager = ThreadManager()
manager.run()


"""GPIO.setmode(GPIO.BOARD)

strip = TideLightLedStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip_lock = threading.Condition()
strip.begin()

led_queue = Queue()

tide_time_collection = TideTimeCollection.TideTimeCollection(LED_COUNT)
tide_time_collection_lock = threading.Condition()

location_data_thread = LocationDataThread(lat, lon, tide_time_collection, tide_time_collection_lock)
if offline_mode:
    print('starting offline mode thread')
    offline_tide_data()
else:
    print('starting location data thread')
    location_data_thread.start()
lighting_thread = LightingThread(tide_time_collection, tide_time_collection_lock, LED_COUNT, led_queue, offline_mode)
ldr_thread = LdrThread(ldr_pin, LED_BRIGHTNESS, LED_BRIGHTNESS, strip, strip_lock)
bluetooth_thread = BluetoothThread()

controller_thread = StripControllerThread(strip, strip_lock, high_tide_direction_color, low_tide_direction_color,
                                          no_tide_level_indicator_color, no_tide_level_indicator_moving_colors,
                                          no_tide_level_indicator_moving_colors,
                                          tide_level_indicator_moving_colors, led_queue, moving_pattern,
                                          LED_COUNT, moving_speed)

print('starting lighting thread')
lighting_thread.start()
print('starting controller thread')
controller_thread.start()
if ldr_active:
    print('starting ldr thread')
    ldr_thread.start()
print('starting bluetooth thread')
bluetooth_thread.start()"""
