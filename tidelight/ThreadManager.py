import threading
import time
from datetime import datetime
from queue import Queue
from xml.etree.ElementTree import ParseError
import ast

import RPi.GPIO as GPIO
#from ConfigReader import *
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
        self.config = ThreadManagerConfigBinding(self)
        self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL = self.config.getLEDConstants()
        self.lat, self.lon = self.config.getLatLon()
        self.ldr_pin = int(self.config.getLDRPin())
        self.ldr_active = ast.literal_eval(self.config.getLdrActive())
        self.offline_mode = ast.literal_eval(self.config.getOfflineMode())
        self.color_format = self.config.getColorFormat()
        
        self.high_tide_direction_color = self.color_converter(self.config.getHighTideDirectionColor())
        self.low_tide_direction_color = self.color_converter(self.config.getLowTideDirectionColor())
        self.tide_level_indicator_color = self.color_converter(self.config.getTideLevelIndicatorColor())
        self.no_tide_level_indicator_color = self.color_converter(self.config.getNoTideLevelIndicatorColor())
        self.tide_level_indicator_moving_colors = self.colors_converter(self.config.getTideLevelIndicatorMovingColor())
        self.no_tide_level_indicator_moving_colors = self.colors_converter(self.config.getNoTideLevelIndicatorMovingColor())
        
        self.moving_speed = float(self.config.getMovingSpeed())
        self.moving_pattern = self.config.getMovingPattern()
        
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
        self.strip = TideLightLedStrip(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS,
                                       self.LED_CHANNEL)
        self.strip_lock = threading.Condition()
        self.led_queue = Queue()
        self.tide_time_collection = TideTimeCollection(self.LED_COUNT)
        self.tide_time_collection_lock = threading.Condition()

        self.lighting_name = 'lighting'
        self.bluetooth_name = 'bluetooth'
        self.ldr_name = 'ldr'
        self.location_name = 'location'
        self.controller_name = 'controller'
        
        

    def run(self):
        #GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        self.strip.begin()
        location_data_thread = LocationDataThread(self.lat, self.lon, self.tide_time_collection, self.tide_time_collection_lock,
                                                  self.location_command_queue, self.location_reply_queue,
                                                  name=self.location_name)
        if self.offline_mode:
            print('starting offline mode thread')
            self.offline_tide_data()
        else:
            print('starting location data thread')
            location_data_thread.start()
        lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock, self.LED_COUNT,
                                         self.led_queue,
                                         self.offline_mode, self.lighting_command_queue, self.lighting_reply_queue,
                                         name=self.lighting_name)
        ldr_thread = LdrThread(self.ldr_pin, self.LED_BRIGHTNESS, self.LED_BRIGHTNESS, self.strip, self.strip_lock,
                               self.ldr_command_queue, self.ldr_reply_queue, name=self.ldr_name)
        bluetooth_thread = BluetoothThread(self.bluetooth_command_queue, self.bluetooth_reply_queue, self.config,
                                           name=self.bluetooth_name)
        
        controller_thread = StripControllerThread(self.strip, self.strip_lock, self.high_tide_direction_color,
                                                  self.low_tide_direction_color,
                                                  self.tide_level_indicator_color, self.no_tide_level_indicator_color,
                                                  self.tide_level_indicator_moving_colors,
                                                  self.no_tide_level_indicator_moving_colors, self.led_queue, self.moving_pattern,
                                                  self.LED_COUNT, self.moving_speed, self.controller_command_queue,
                                                  self.controller_reply_queue, name=self.controller_name)

        print('starting lighting thread')
        lighting_thread.start()
        print('starting controller thread')
        controller_thread.start()
        if self.ldr_active:
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
        if new_lat != self.lat or new_lon != self.lon:
            self.lat = new_lat
            self.lon = new_lon
            if not self.offline_mode:
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
                    location_data_thread = LocationDataThread(self.lat, self.lon, self.tide_time_collection,
                                                              self.tide_time_collection_lock,
                                                              self.location_command_queue, self.location_reply_queue,
                                                              name=self.location_name)
                    location_data_thread.start()
                    lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock,
                                                     self.LED_COUNT,
                                                     self.led_queue,
                                                     self.offline_mode, self.lighting_command_queue,
                                                     self.lighting_reply_queue,
                                                     name=self.lighting_name)
                    lighting_thread.start()
                    controller_thread = StripControllerThread(self.strip, self.strip_lock, self.high_tide_direction_color,
                                                              self.low_tide_direction_color,
                                                              self.tide_level_indicator_color,
                                                              self.no_tide_level_indicator_color,
                                                              self.tide_level_indicator_moving_colors,
                                                              self.no_tide_level_indicator_moving_colors, self.led_queue,
                                                              self.moving_pattern,
                                                              self.LED_COUNT, self.moving_speed, self.controller_command_queue,
                                                              self.controller_reply_queue, name=self.controller_name)
                    controller_thread.start()



    def change_brightness(self, new_brightness):
        if new_brightness != self.LED_BRIGHTNESS:
            self.LED_BRIGHTNESS = new_brightness
            with self.strip_lock:
                self.strip.setBrightness(new_brightness)
                self.strip_lock.notify_all()
            if self.thread_running(self.ldr_name):
                self.ldr_command_queue.put(LdrCommand(LdrCommand.SETBRIGHTNESS, self.LED_BRIGHTNESS))

    def change_ldr_active(self, new_active):
        thread_running = self.thread_running(self.ldr_name)

        if new_active and not thread_running:
            self.ldr_active = new_active
            ldr_thread = LdrThread(self.ldr_pin, self.LED_BRIGHTNESS, self.LED_BRIGHTNESS, self.strip, self.strip_lock,
                                   self.ldr_command_queue, self.ldr_reply_queue, name='ldr')
            ldr_thread.start()
        elif not new_active and thread_running:
            self.ldr_active = new_active
            self.ldr_command_queue.put(LdrCommand(LdrCommand.STOP, None))

    def change_high_tide_direction_color(self, new_color):
        color = self.color_converter(new_color)
        if color != self.high_tide_direction_color:
            self.high_tide_direction_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWHIGHTIDEDIRECTIONCOLOR,
                                                                    color))

    def change_low_tide_direction_color(self, new_color):
        color = self.color_converter(new_color)
        if color != self.low_tide_direction_color:
            self.low_tide_direction_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWLOWTIDEDIRECTIONCOLOR,
                                                                    color))

    def change_tide_level_indicator_color(self, new_color):
        color = self.color_converter(new_color)
        if color != self.tide_level_indicator_color:
            self.tide_level_indicator_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORCOLOR,
                                                                    color))

    def change_no_tide_level_indicator_color(self, new_color):
        color = self.color_converter(new_color)
        if color != self.no_tide_level_indicator_color:
            self.no_tide_level_indicator_color = color
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWNOTIDELEVELINDICATORCOLOR,
                                                                    color))

    def change_tide_level_indicator_moving_color(self, new_colors):
        colors = self.colors_converter(new_colors)
        if colors != self.tide_level_indicator_moving_colors:
            self.tide_level_indicator_moving_colors = colors
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORMOVINGCOLOR,
                                                                    color))

    def change_no_tide_level_indicator_moving_color(self, new_colors):
        colors = self.colors_converter(new_colors)
        if colors != self.no_tide_level_indicator_moving_colors:
            self.no_tide_level_indicator_moving_colors = colors
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(
                    ControllerCommand(ControllerCommand.NEWNOTIDELEVELINDICATORMOVINGCOLOR,
                                      color))

    def change_moving_speed(self, new_moving_speed):
        if new_moving_speed != self.moving_speed:
            self.moving_speed = new_moving_speed
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
                self.moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
            except ParseError:
                self. moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
            except CannotFindElementException:
                self.moving_pattern = 'red_blink'
                self.tide_time_collection_lock.notify_all()
    
    def reset(self):
        if self.thread_running(self.location_name):
                    location_thread = self.get_thread(self.location_name)
                    if location_thread is not None:
                        self.location_command_queue.put(LocationCommand(LocationCommand.STOP, None))
                        location_thread.join()
        
        if self.thread_running(self.controller_name):
            controller_thread = self.get_thread(self.controller_name)
            if controller_thread is not None:
                self.controller_command_queue.put(ControllerCommand.STOP, None)
                controller_thread.join()
        
        if self.thread_running(self.lighting_name):
            lighting_thread = self.get_thread(self.lighting_name)
            if lighting_thread is not None:
                self.lighting_command_queue.put(LightingCommand.STOP, None)
                lighting_thread.join()
        
        if self.thread_running(self.ldr_name):
            ldr_thread = self.get_thread(self.ldr_name)
            if ldr_thread is not None:
                self.ldr_command_queue.put(LdrCommand.STOP, None)
                ldr_thread.join()
        
        self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL = self.config.getLEDConstants()
        self.lat, self.lon = self.config.getLatLon()
        self.ldr_pin = int(self.config.getLDRPin())
        self.ldr_active = ast.literal_eval(self.config.getLdrActive())
        self.offline_mode = ast.literal_eval(self.config.getOfflineMode())
        self.color_format = self.config.getColorFormat()
        
        self.high_tide_direction_color = self.color_converter(self.config.getHighTideDirectionColor())
        self.low_tide_direction_color = self.color_converter(self.config.getLowTideDirectionColor())
        self.tide_level_indicator_color = self.color_converter(self.config.getTideLevelIndicatorColor())
        self.no_tide_level_indicator_color = self.color_converter(self.config.getNoTideLevelIndicatorColor())
        self.tide_level_indicator_moving_colors = self.colors_converter(self.config.getTideLevelIndicatorMovingColor())
        self.no_tide_level_indicator_moving_colors = self.colors_converter(self.config.getNoTideLevelIndicatorMovingColor())
        
        self.moving_speed = float(self.config.getMovingSpeed())
        self.moving_pattern = self.config.getMovingPattern()
        
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
        
        self.strip = TideLightLedStrip(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS,
                                       self.LED_CHANNEL)
        self.strip_lock = threading.Condition()
        self.led_queue = Queue()
        self.tide_time_collection = TideTimeCollection(self.LED_COUNT)
        self.tide_time_collection_lock = threading.Condition()
        
        self.strip.begin()
        location_data_thread = LocationDataThread(self.lat, self.lon, self.tide_time_collection, self.tide_time_collection_lock,
                                                  self.location_command_queue, self.location_reply_queue,
                                                  name=self.location_name)
        if self.offline_mode:
            print('starting offline mode thread')
            self.offline_tide_data()
        else:
            print('starting location data thread')
            location_data_thread.start()
        lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock, self.LED_COUNT,
                                         self.led_queue,
                                         self.offline_mode, self.lighting_command_queue, self.lighting_reply_queue,
                                         name=self.lighting_name)
        ldr_thread = LdrThread(self.ldr_pin, self.LED_BRIGHTNESS, self.LED_BRIGHTNESS, self.strip, self.strip_lock,
                               self.ldr_command_queue, self.ldr_reply_queue, name=self.ldr_name)
        
        controller_thread = StripControllerThread(self.strip, self.strip_lock, self.high_tide_direction_color,
                                                  self.low_tide_direction_color,
                                                  self.tide_level_indicator_color, self.no_tide_level_indicator_color,
                                                  self.tide_level_indicator_moving_colors,
                                                  self.no_tide_level_indicator_moving_colors, self.led_queue, self.moving_pattern,
                                                  self.LED_COUNT, self.moving_speed, self.controller_command_queue,
                                                  self.controller_reply_queue, name=self.controller_name)

        print('starting lighting thread')
        lighting_thread.start()
        print('starting controller thread')
        controller_thread.start()
        if self.ldr_active:
            print('starting ldr thread')
            ldr_thread.start()