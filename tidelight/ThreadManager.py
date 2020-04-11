import threading
import time
from datetime import datetime
from queue import Queue
from xml.etree.ElementTree import ParseError

import RPi.GPIO as GPIO
from ConfigReader import *
from TideLightLedStrip import TideLightLedStrip
from kartverket_tide_api.exceptions import CannotFindElementException
from kartverket_tide_api.parsers import LocationDataParser
from threads.BluetoothThread import BluetoothThread
from threads.LdrThread import LdrThread, LdrCommand
from threads.LocationDataThread import LocationDataThread, LocationCommand
from threads.StripControllerThread import StripControllerThread, ControllerCommand, ControllerReply
from threads.LightingThread import LightingThread, LightingReply, LightingCommand

from TideTimeCollection import TideTimeCollection
from util import *

from ThreadManagerConfigBinding import ThreadManagerConfigBinding


class ThreadManager:
    LIGHTINGHANDLERS, LOCATIONHANDLERS, BLUETOOTHHANDLERS, LDRHANDLERS, CONTROLLERHANDLERS = range(5)

    def __init__(self):
        self.location_command_queue = Queue()
        self.location_reply_queue = Queue()
        self.ldr_command_queue = Queue()
        self.ldr_reply_queue = Queue()
        self.lighting_command_queue = Queue()
        self.lighting_reply_queue = Queue()
        self.controller_command_queue = Queue()
        self.controller_reply_queue = Queue()
        self.bluetooth_command_queue = Queue()
        self.bluetooth_reply_queue = Queue()

        self.handlers = {
            ThreadManager.LIGHTINGHANDLERS: {
                LightingReply.XMLERROR: self.xml_error
            },
            ThreadManager.LOCATIONHANDLERS: {

            },
            ThreadManager.LDRHANDLERS: {

            },
            ThreadManager.CONTROLLERHANDLERS: {

            },
            ThreadManager.BLUETOOTHHANDLERS:
                {

                }
        }
        self.strip = TideLightLedStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS,
                                       LED_CHANNEL)
        self.strip_lock = threading.Condition()
        self.led_queue = Queue()
        self.tide_time_collection = TideTimeCollection(LED_COUNT)
        self.tide_time_collection_lock = threading.Condition()

        self.lighting_name = 'lighting'
        self.bluetooth_name = 'bluetooth'
        self.ldr_name = 'ldr'
        self.location_name = 'location'
        self.controller_name = 'controller'
        self.threadManagerConfigBinding = ThreadManagerConfigBinding(self)

    def run(self):
        GPIO.setmode(GPIO.BOARD)
        self.strip.begin()
        location_data_thread = LocationDataThread(lat, lon, self.tide_time_collection, self.tide_time_collection_lock,
                                                  self.location_command_queue, self.location_reply_queue,
                                                  name=self.location_name)
        if offline_mode:
            print('starting offline mode thread')
            self.offline_tide_data()
        else:
            print('starting location data thread')
            location_data_thread.start()
        lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock, LED_COUNT,
                                         self.led_queue,
                                         offline_mode, self.lighting_command_queue, self.lighting_reply_queue,
                                         name=self.lighting_name)
        ldr_thread = LdrThread(ldr_pin, LED_BRIGHTNESS, LED_BRIGHTNESS, self.strip, self.strip_lock,
                               self.ldr_command_queue, self.ldr_reply_queue, name=self.ldr_name)
        bluetooth_thread = BluetoothThread(self.bluetooth_command_queue, self.bluetooth_reply_queue, self.threadManagerConfigBinding,
                                           name=self.bluetooth_name)

        controller_thread = StripControllerThread(self.strip, self.strip_lock, high_tide_direction_color,
                                                  low_tide_direction_color,
                                                  no_tide_level_indicator_color, no_tide_level_indicator_moving_colors,
                                                  no_tide_level_indicator_moving_colors,
                                                  tide_level_indicator_moving_colors, self.led_queue, moving_pattern,
                                                  LED_COUNT, moving_speed, self.controller_command_queue,
                                                  self.controller_reply_queue, name=self.controller_name)

        print('starting lighting thread')
        lighting_thread.start()
        print('starting controller thread')
        controller_thread.start()
        if ldr_active:
            print('starting ldr thread')
            ldr_thread.start()
        print('starting bluetooth thread')
        bluetooth_thread.start()
        while True:
            if not self.lighting_reply_queue.empty():
                reply = self.lighting_reply_queue.get()
                self.handle_reply(reply, ThreadManager.LIGHTINGHANDLERS)

            time.sleep(5)

    def handle_reply(self, reply, handler):
        self.handlers[handler][reply.reply_type](reply.data)

    def xml_error(self, data):
        if self.thread_running(self.lighting_name):
            self.lighting_command_queue.put(LightingCommand(LightingCommand.STOP, None))
        if self.thread_running(self.controller_name):
            self.controller_command_queue.put(ControllerCommand(ControllerCommand.XMLERROR, None))

    def change_lat_lon(self, new_lat, new_lon):
        global lat
        global lon
        global offline_mode
        if new_lat != lat or new_lon != lon:
            lat = new_lat
            lon = new_lon
            if not offline_mode:
                if self.thread_running(self.location_name):
                    location_thread = self.get_thread(self.location_name)
                    if location_thread is not None:
                        self.location_command_queue.put(LocationCommand(LocationCommand.STOP, None))
                        location_thread.join()
                    if self.thread_running(self.controller_name):
                        controller_thread = self.get_thread(self.controller_name)
                        if controller_thread is not None:
                            self.controller_command_queue.put(ControllerCommand(ControllerCommand.STOP, None))
                            controller_thread.join()
                    if self.thread_running(self.lighting_name):
                        lighhting_thread = self.get_thread(self.lighting_name)
                        if lighhting_thread is not None:
                            self.lighting_command_queue.put(LightingCommand(LightingCommand.STOP, None))
                            lighhting_thread.join()
                    self.tide_time_collection.clear()
                    location_data_thread = LocationDataThread(lat, lon, self.tide_time_collection,
                                                              self.tide_time_collection_lock,
                                                              self.location_command_queue, self.location_reply_queue,
                                                              name=self.location_name)
                    location_data_thread.start()
                    lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock,
                                                     LED_COUNT,
                                                     self.led_queue,
                                                     offline_mode, self.lighting_command_queue,
                                                     self.lighting_reply_queue,
                                                     name=self.lighting_name)
                    lighting_thread.start()
                    controller_thread = StripControllerThread(self.strip, self.strip_lock, high_tide_direction_color,
                                                              low_tide_direction_color,
                                                              no_tide_level_indicator_color,
                                                              no_tide_level_indicator_moving_colors,
                                                              no_tide_level_indicator_moving_colors,
                                                              tide_level_indicator_moving_colors, self.led_queue,
                                                              moving_pattern,
                                                              LED_COUNT, moving_speed, self.controller_command_queue,
                                                              self.controller_reply_queue, name=self.controller_name)
                    controller_thread.start()



    def change_brightness(self, new_brightness):
        global LED_BRIGHTNESS
        if new_brightness != LED_BRIGHTNESS:
            LED_BRIGHTNESS = new_brightness
            with self.strip_lock:
                self.strip.setBrightness(new_brightness)
                self.strip_lock.notify_all()
            if self.thread_running(self.ldr_name):
                self.ldr_command_queue.put(LdrCommand(LdrCommand.SETBRIGHTNESS, LED_BRIGHTNESS))

    def change_ldr_active(self, new_active):
        global ldr_active
        thread_running = self.thread_running(self.ldr_name)

        if new_active and not thread_running:
            ldr_active = new_active
            ldr_thread = LdrThread(ldr_pin, LED_BRIGHTNESS, LED_BRIGHTNESS, self.strip, self.strip_lock,
                                   self.ldr_command_queue, self.ldr_reply_queue, name='ldr')
            ldr_thread.start()
        elif not new_active and thread_running:
            ldr_active = new_active
            self.ldr_command_queue.put(LdrCommand(LdrCommand.STOP, None))

    def change_high_tide_direction_color(self, new_color):
        global high_tide_direction_color
        color = self.color_converter(new_color)
        if color != high_tide_direction_color:
            high_tide_direction_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWHIGHTIDEDIRECTIONCOLOR,
                                                                    color))

    def change_low_tide_direction_color(self, new_color):
        global low_tide_direction_color
        color = self.color_converter(new_color)
        if color != low_tide_direction_color:
            low_tide_direction_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWLOWTIDEDIRECTIONCOLOR,
                                                                    color))

    def change_tide_level_indicator_color(self, new_color):
        global tide_level_indicator_color
        color = self.color_converter(new_color)
        if color != tide_level_indicator_color:
            tide_level_indicator_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORCOLOR,
                                                                    color))

    def change_no_tide_level_indicator_color(self, new_color):
        global no_tide_level_indicator_color
        color = self.color_converter(new_color)
        if color != no_tide_level_indicator_color:
            no_tide_level_indicator_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWNOTIDELEVELINDICATORCOLOR,
                                                                    color))

    def change_tide_level_indicator_moving_color(self, new_colors):
        global tide_level_indicator_moving_colors
        colors = self.colors_converter(new_colors)
        if colors != tide_level_indicator_moving_colors:
            tide_level_indicator_moving_colors = colors
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORMOVINGCOLOR,
                                                                    color))

    def change_no_tide_level_indicator_moving_color(self, new_colors):
        global no_tide_level_indicator_moving_colors
        colors = self.colors_converter(new_colors)
        if colors != no_tide_level_indicator_moving_colors:
            no_tide_level_indicator_moving_colors = colors
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(
                    ControllerCommand(ControllerCommand.NEWNOTIDELEVELINDICATORMOVINGCOLOR,
                                      color))

    def change_moving_speed(self, new_moving_speed):
        global moving_speed
        if new_moving_speed != moving_speed:
            moving_speed = new_moving_speed
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWMOVINGSPEED, new_moving_speed))

    def thread_running(self, name):
        for thread in threading.enumerate():
            if thread.name == name:
                return True
        return False

    def color_converter(self, color):
        color_list = json.loads(color)
        return Color(color_list[0], color_list[1], color_list[2])

    def colors_converter(self, colors):
        temp_colors_list = json.loads(colors)
        colors_list = []
        for color in temp_colors_list:
            colors_list.append(Color(color[0], color[1], color[2]))
        return colors_list

    def get_thread(self, name):
        for thread in threading.enumerate():
            if thread.name == name:
                return thread
        return None

    def offline_tide_data(self):
        # TODO: do something if none of the offline data is current date
        with self.tide_time_collection_lock:
            # TODO: what if theres no such file
            global moving_pattern
            try:
                with open('offline.xml', 'r') as xmlfile:
                    xml = xmlfile.read()
                parser = LocationDataParser(xml)
                waterlevels = parser.parse_response()['data']
                coll = []
                for waterlevel in waterlevels:
                    # TODO what to do if tide is None
                    tide = waterlevel.tide
                    timestring = waterlevel.time
                    timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                    timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                    # TODO figure out difference between time and timestamp. Why didn't past myself properly document that
                    coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))

                now = datetime.now().timestamp()
                self.tide_time_collection.insert_tide_times(coll, now)
                if self.tide_time_collection.is_empty():
                    moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
            except FileNotFoundError:
                moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
            except ParseError:
                moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
            except CannotFindElementException:
                moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
