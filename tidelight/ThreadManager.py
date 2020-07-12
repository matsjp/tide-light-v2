import threading
import time
from datetime import datetime
from queue import Queue
from xml.etree.ElementTree import ParseError
import ast

import RPi.GPIO as GPIO
from TideLightLedStrip import TideLightLedStrip
from kartverket_tide_api.exceptions import CannotFindElementException
from kartverket_tide_api.parsers import LocationDataParser
from threads.BluetoothThread import BluetoothThread, BluetoothCommand
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
        self._read_config_variables()
        
        self._create_thread_queues()

        self.handlers = {
            ThreadManager.LIGHTINGHANDLERS: {
                LightingReply.XMLERROR: self._xml_error
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
        self.xml_error = False
        self.shutdown = False
        
        

    def run(self):
        GPIO.setmode(GPIO.BOARD)
        self.strip.begin()
        for i in range(self.LED_COUNT):
            self.strip.setPixelColor(i, Color(0,255,0))
            self.strip.show()
        print('starting bluetooth thread')
        self.start_bluetooth_thread()
        if self.offline_mode:
            print('starting offline mode thread')
            self.offline_tide_data()
        else:
            print('starting location data thread')
            self.start_location_thread()
        print('starting lighting thread')
        self.start_lighting_thread()
        print('starting controller thread')
        self.start_controller_thread()
        if self.ldr_active:
            print('starting ldr thread')
            self.start_ldr_thread()
        while not self.shutdown:
            if not self.lighting_reply_queue.empty():
                reply = self.lighting_reply_queue.get()
                self.handle_reply(reply, ThreadManager.LIGHTINGHANDLERS)

            time.sleep(5)

    def handle_reply(self, reply, handler):
        self.handlers[handler][reply.reply_type](reply.data)

    def _xml_error(self, data):
        self.stop_lighting_thread()
        self.change_moving_pattern('red_blink')

    def change_lat_lon(self, new_lat, new_lon):
        if new_lat != self.lat or new_lon != self.lon:
            self.lat = new_lat
            self.lon = new_lon
            if not self.offline_mode:
                self.stop_location_thread()
                self.stop_controller_thread()
                self.stop_lighting_thread()
                self.tide_time_collection.clear()
                self.start_location_thread()
                self.start_controller_thread()
                self.start_lighting_thread()
    
    def change_moving_pattern(self, new_moving_pattern):
        if self.moving_pattern != new_moving_pattern:
            self.moving_pattern = new_moving_pattern
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWMOVINGPATTERN, new_moving_pattern))



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
            self.start_ldr_thread()
        elif not new_active and thread_running:
            self.ldr_active = new_active
            self.stop_ldr_thread()

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

    def change_tide_level_indicator_moving_colors(self, new_colors):
        colors = self.colors_converter(new_colors)
        if colors != self.tide_level_indicator_moving_colors:
            self.tide_level_indicator_moving_colors = colors
            if self.thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORMOVINGCOLOR,
                                                                    color))

    def change_no_tide_level_indicator_moving_colors(self, new_colors):
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
    
    def change_offline_mode(self, new_offline_mode):
        if self.offline_mode != new_offline_mode:
            self.offline_mode = new_offline_mode
            self.reset()

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
        with self.tide_time_collection_lock:
            try:
                with open('offline.xml', 'r') as xmlfile:
                    print("Starting to read file")
                    xml = xmlfile.read()
                    print("done reading file")
                parser = LocationDataParser(xml)
                print("parsing data")
                waterlevels = parser.parse_response()['data']
                print(waterlevels)
                print("done parsing")
                coll = []
                
                print("adding data to coll")
                for waterlevel in waterlevels:
                    tide = waterlevel.tide
                    timestring = waterlevel.time
                    timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                    timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                    coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))
                print("done")

                now = datetime.now().timestamp()
                print("adding data to tide time collection")
                self.tide_time_collection.insert_tide_times(coll, now)
                if self.tide_time_collection.is_empty():
                    self._xml_error(None)
                self.tide_time_collection_lock.notify_all()
                print("offline data ready")
            except FileNotFoundError:
                self._xml_error(None)
                self.tide_time_collection_lock.notify_all()
            except ParseError:
                self._xml_error(None)
                self.tide_time_collection_lock.notify_all()
            except CannotFindElementException:
                self._xml_error(None)
                self.tide_time_collection_lock.notify_all()
            except Exception:
                self._xml_error(None)
                self.tide_time_collection_lock.notify_all()
    
    def _read_config_variables(self):
        self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_BRIGHTNESS, self.LED_INVERT, self.LED_CHANNEL = self.config.getLEDConstants()
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
    
    def _create_thread_queues(self):
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
    
    
    def stop_location_thread(self):
        if self.thread_running(self.location_name):
                    location_thread = self.get_thread(self.location_name)
                    if location_thread is not None:
                        self.location_command_queue.put(LocationCommand(LocationCommand.STOP, None))
                        location_thread.join()
    
    def stop_controller_thread(self):
        if self.thread_running(self.controller_name):
            controller_thread = self.get_thread(self.controller_name)
            if controller_thread is not None:
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.STOP, None))
                controller_thread.join()
    
    def stop_lighting_thread(self):
        if self.thread_running(self.lighting_name):
            lighting_thread = self.get_thread(self.lighting_name)
            if lighting_thread is not None:
                self.lighting_command_queue.put(LightingCommand(LightingCommand.STOP, None))
                lighting_thread.join()
    
    def stop_ldr_thread(self):
        if self.thread_running(self.ldr_name):
            ldr_thread = self.get_thread(self.ldr_name)
            if ldr_thread is not None:
                self.ldr_command_queue.put(LdrCommand(LdrCommand.STOP, None))
                ldr_thread.join()
    
    def stop_bluetooth_thread(self):
        if self.thread_running(self.bluetooth_name):
            bluetooth_thread = self.get_thread(self.bluetooth_name)
            if bluetooth_thread is not None:
                self.bluetooth_command_queue.put(BluetoothCommand(BluetoothCommand.STOP, None))
                bluetooth_thread.join()
    
    def start_location_thread(self):
        location_data_thread = LocationDataThread(self.lat, self.lon, self.tide_time_collection, self.tide_time_collection_lock,
                                                  self.location_command_queue, self.location_reply_queue,
                                                  name=self.location_name)
        location_data_thread.start()
    
    def start_lighting_thread(self):
        lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock, self.LED_COUNT,
                                         self.led_queue,
                                         self.offline_mode, self.lighting_command_queue, self.lighting_reply_queue,
                                         name=self.lighting_name)
        lighting_thread.start()
    
    def start_ldr_thread(self):
        ldr_thread = LdrThread(self.ldr_pin, self.LED_BRIGHTNESS, self.LED_BRIGHTNESS, self.strip, self.strip_lock,
                               self.ldr_command_queue, self.ldr_reply_queue, name=self.ldr_name)
        ldr_thread.start()
    
    def start_controller_thread(self):
        controller_thread = StripControllerThread(self.strip, self.strip_lock, self.high_tide_direction_color,
                                                  self.low_tide_direction_color,
                                                  self.tide_level_indicator_color, self.no_tide_level_indicator_color,
                                                  self.tide_level_indicator_moving_colors,
                                                  self.no_tide_level_indicator_moving_colors, self.led_queue, self.moving_pattern,
                                                  self.LED_COUNT, self.moving_speed, self.controller_command_queue,
                                                  self.controller_reply_queue, name=self.controller_name)
        controller_thread.start()
    
    def start_bluetooth_thread(self):
        bluetooth_thread = BluetoothThread(self.bluetooth_command_queue, self.bluetooth_reply_queue, self.config,
                                           name=self.bluetooth_name)
        bluetooth_thread.start()
    
    def reset(self):
        self.stop_location_thread()
        self.stop_controller_thread()
        self.stop_lighting_thread()
        self.stop_ldr_thread()
        self._read_config_variables()
        self._create_thread_queues()
        
        self.strip = TideLightLedStrip(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS,
                                       self.LED_CHANNEL)
        self.strip_lock = threading.Condition()
        self.led_queue = Queue()
        self.tide_time_collection = TideTimeCollection(self.LED_COUNT)
        self.tide_time_collection_lock = threading.Condition()
        
        self.strip.begin()
        if self.offline_mode:
            print('starting offline mode thread')
            self.offline_tide_data()
        else:
            print('starting location data thread')
            self.start_location_thread()

        print('starting lighting thread')
        self.start_lighting_thread()
        print('starting controller thread')
        self.start_controller_thread()
        if self.ldr_active:
            print('starting ldr thread')
            self.start_ldr_thread()
    
    def update_offline_data(self):
        if self.offline_mode:
            self.reset()
    
    def stop(self):
        print("Stopping location thread")
        self.stop_location_thread()
        print("Stopping location thread")
        self.stop_controller_thread()
        print("Stopping lighting thread")
        self.stop_lighting_thread()
        print("Stopping ldr thread")
        self.stop_ldr_thread()
        print("Stopping bluetooth thread")
        self.stop_bluetooth_thread()
        print("Cleaning up GPIO")
        GPIO.cleanup()
        print("Shutting down the tide light program")
        self.shutdown = True
        