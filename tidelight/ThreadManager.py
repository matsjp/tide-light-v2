import ast
import time
from queue import Queue
from pybleno import *

import RPi.GPIO as GPIO

from ThreadManagerConfigBinding import ThreadManagerConfigBinding
from TideLightLedStrip import TideLightLedStrip
from TideTimeCollection import TideTimeCollection
from bluetooth.peripheral import Peripheral
from threads.BluetoothThread import BluetoothThread, BluetoothCommand
from threads.CommandThread import CommandThread
from threads.LdrThread import LdrThread, LdrCommand
from threads.LightingThread import LightingThread, LightingCommand
from threads.LocationDataThread import LocationDataThread, LocationCommand
from threads.OfflinePrunerThread import OfflinePrunerThread, OfflinePrunerCommand
from threads.OfflineThread import OfflineThread, OfflineCommand
from threads.StripControllerThread import StripControllerThread, ControllerCommand
from util import *
from utils.threadUtils import *
import array


class ThreadManager:
    LIGHTINGHANDLERS, LOCATIONHANDLERS, BLUETOOTHHANDLERS, LDRHANDLERS, CONTROLLERHANDLERS, PRUNERHANDLERS, OFFLINEHANDLERS = range(
        7)

    def __init__(self):
        self.config = ThreadManagerConfigBinding(self)
        self.peripheral = Peripheral(self.config)
        self._read_config_variables()

        self._create_thread_queues()

        self.handlers = {
            ThreadManager.LIGHTINGHANDLERS: {
                #LightingReply.XMLERROR: self._xml_error
            },
            ThreadManager.LOCATIONHANDLERS: {
                #LocationReply.LOCATION_UPDATE: self.location_update
            },
            ThreadManager.LDRHANDLERS: {

            },
            ThreadManager.CONTROLLERHANDLERS: {

            },
            ThreadManager.BLUETOOTHHANDLERS:
                {

                },
            ThreadManager.PRUNERHANDLERS: {
            },
            ThreadManager.OFFLINEHANDLERS: {
                #OfflineReply.UPDATE_DATA: self.offline_data_update
            }
        }
        self.strip = TideLightLedStrip(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT,
                                       self.LED_BRIGHTNESS,
                                       self.LED_CHANNEL)
        self.xml_lock = threading.Condition()
        self.strip_lock = threading.Condition()
        self.led_queue = Queue()
        self.tide_time_collection = TideTimeCollection(self.LED_COUNT)
        self.tide_time_collection_lock = threading.Condition()
        self.quick = False

        self.lighting_name = 'lighting'
        self.bluetooth_name = 'bluetooth'
        self.ldr_name = 'ldr'
        self.location_name = 'location'
        self.controller_name = 'controller'
        self.pruner_name = 'pruner'
        self.offline_name = 'offline'
        # TODO look into xml errors
        self.xml_error = False
        self.shutdown = False

    def run(self):
        GPIO.setmode(GPIO.BOARD)
        self.strip.begin()
        for i in range(self.LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 255, 0))
            self.strip.show()
        print('starting bluetooth thread')
        self.start_bluetooth_thread()
        print('starting offline mode thread')
        self.start_offline_thread()
        time.sleep(0.5)
        print('starting location data thread')
        self.start_location_thread()
        time.sleep(0.5)
        print('starting lighting thread')
        self.start_lighting_thread()
        time.sleep(0.5)
        print('starting controller thread')
        self.start_controller_thread()
        if self.ldr_active:
            print('starting ldr thread')
            self.start_ldr_thread()
        print("starting pruner thread")
        self.start_pruner_thread()
        self.command_reply_queue = Queue()
        command_thread = CommandThread(self.command_reply_queue, self)
        command_thread.start()
        while not self.shutdown:
            if not self.lighting_reply_queue.empty():
                reply = self.lighting_reply_queue.get()
                self.handle_reply(reply, ThreadManager.LIGHTINGHANDLERS)
            if not self.location_reply_queue.empty():
                reply = self.location_reply_queue.get()
                self.handle_reply(reply, ThreadManager.LOCATIONHANDLERS)
            if not self.offline_reply_queue.empty():
                reply = self.offline_reply_queue.get()
                self.handle_reply(reply, ThreadManager.OFFLINEHANDLERS)

            time.sleep(5)

    def handle_reply(self, reply, handler):
        self.handlers[handler][reply.reply_type](reply.data)


    def change_lat_lon(self, new_lat, new_lon):
        if new_lat != self.lat or new_lon != self.lon:
            self.lat = new_lat
            self.lon = new_lon
            #TODO check internet connection earlier. In the bluetooth characteristic. Error if no internet
            if internetConnection():
                print("updating location")
                self.quick = True
                self.location_command_queue.put(LocationCommand(LocationCommand.LOCATION_UPDATE_QUICK, {'lat': self.lat, 'lon': self.lon}))

    def change_moving_pattern(self, new_moving_pattern):
        if self.moving_pattern != new_moving_pattern:
            self.moving_pattern = new_moving_pattern
            if thread_running(self.controller_name):
                self.controller_command_queue.put(
                    ControllerCommand(ControllerCommand.NEWMOVINGPATTERN, new_moving_pattern))

    def change_brightness(self, new_brightness):
        if new_brightness != self.LED_BRIGHTNESS:
            self.LED_BRIGHTNESS = new_brightness
            with self.strip_lock:
                self.strip.setBrightness(new_brightness)
                self.strip_lock.notify_all()
            if thread_running(self.ldr_name):
                self.ldr_command_queue.put(LdrCommand(LdrCommand.SETBRIGHTNESS, self.LED_BRIGHTNESS))

    def change_ldr_active(self, new_active):
        running = thread_running(self.ldr_name)

        if new_active and not thread_running:
            self.ldr_active = new_active
            self.start_ldr_thread()
        elif not new_active and running:
            self.ldr_active = new_active
            self.stop_ldr_thread()

    def change_high_tide_direction_color(self, new_color):
        color = color_converter(new_color)
        if color != self.high_tide_direction_color:
            self.high_tide_direction_color = color
            if thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWHIGHTIDEDIRECTIONCOLOR,
                                                                    color))

    def change_low_tide_direction_color(self, new_color):
        color = color_converter(new_color)
        if color != self.low_tide_direction_color:
            self.low_tide_direction_color = color
            if thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWLOWTIDEDIRECTIONCOLOR,
                                                                    color))

    def change_tide_level_indicator_color(self, new_color):
        color = color_converter(new_color)
        if color != self.tide_level_indicator_color:
            self.tide_level_indicator_color = color
            if thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORCOLOR,
                                                                    color))

    def change_no_tide_level_indicator_color(self, new_color):
        color = color_converter(new_color)
        if color != self.no_tide_level_indicator_color:
            self.no_tide_level_indicator_color = color
            if thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWNOTIDELEVELINDICATORCOLOR,
                                                                    color))

    def change_tide_level_indicator_moving_colors(self, new_colors):
        colors = colors_converter(new_colors)
        if colors != self.tide_level_indicator_moving_colors:
            self.tide_level_indicator_moving_colors = colors
            if thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWTIDELEVELINDICATORMOVINGCOLOR,
                                                                    colors))

    def change_no_tide_level_indicator_moving_colors(self, new_colors):
        colors = colors_converter(new_colors)
        if colors != self.no_tide_level_indicator_moving_colors:
            self.no_tide_level_indicator_moving_colors = colors
            if thread_running(self.controller_name):
                self.controller_command_queue.put(
                    ControllerCommand(ControllerCommand.NEWNOTIDELEVELINDICATORMOVINGCOLOR,
                                      colors))

    def change_moving_speed(self, new_moving_speed):
        if new_moving_speed != self.moving_speed:
            self.moving_speed = new_moving_speed
            if thread_running(self.controller_name):
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.NEWMOVINGSPEED, new_moving_speed))

    def _read_config_variables(self):
        self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_BRIGHTNESS, self.LED_INVERT, self.LED_CHANNEL = self.config.getLEDConstants()
        self.lat, self.lon = self.config.getLatLon()
        self.ldr_pin = int(self.config.getLDRPin())
        self.ldr_active = ast.literal_eval(self.config.getLdrActive())
        self.color_format = self.config.getColorFormat()

        self.high_tide_direction_color = color_converter(self.config.getHighTideDirectionColor())
        self.low_tide_direction_color = color_converter(self.config.getLowTideDirectionColor())
        self.tide_level_indicator_color = color_converter(self.config.getTideLevelIndicatorColor())
        self.no_tide_level_indicator_color = color_converter(self.config.getNoTideLevelIndicatorColor())
        self.tide_level_indicator_moving_colors = colors_converter(self.config.getTideLevelIndicatorMovingColor())
        self.no_tide_level_indicator_moving_colors = colors_converter(self.config.getNoTideLevelIndicatorMovingColor())

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
        self.pruner_command_queue = Queue()
        self.pruner_reply_queue = Queue()
        self.offline_command_queue = Queue()
        self.offline_reply_queue = Queue()

    def stop_location_thread(self):
        if thread_running(self.location_name):
            location_thread = get_thread(self.location_name)
            if location_thread is not None:
                self.location_command_queue.put(LocationCommand(LocationCommand.STOP, None))
                location_thread.join()

    def stop_controller_thread(self):
        if thread_running(self.controller_name):
            controller_thread = get_thread(self.controller_name)
            if controller_thread is not None:
                self.controller_command_queue.put(ControllerCommand(ControllerCommand.STOP, None))
                controller_thread.join()

    def stop_lighting_thread(self):
        if thread_running(self.lighting_name):
            lighting_thread = get_thread(self.lighting_name)
            if lighting_thread is not None:
                self.lighting_command_queue.put(LightingCommand(LightingCommand.STOP, None))
                lighting_thread.join()

    def stop_ldr_thread(self):
        if thread_running(self.ldr_name):
            ldr_thread = get_thread(self.ldr_name)
            if ldr_thread is not None:
                self.ldr_command_queue.put(LdrCommand(LdrCommand.STOP, None))
                ldr_thread.join()

    def stop_bluetooth_thread(self):
        if thread_running(self.bluetooth_name):
            bluetooth_thread = get_thread(self.bluetooth_name)
            if bluetooth_thread is not None:
                self.bluetooth_command_queue.put(BluetoothCommand(BluetoothCommand.STOP, None))
                bluetooth_thread.join()

    def stop_pruner_thread(self):
        if thread_running(self.pruner_name):
            pruner_thread = get_thread(self.pruner_name)
            if pruner_thread is not None:
                self.pruner_command_queue.put(OfflinePrunerCommand(OfflinePrunerCommand.STOP, None))
                pruner_thread.join()

    def stop_offline_thread(self):
        if thread_running(self.offline_name):
            offline_thread = get_thread(self.offline_name)
            if offline_thread is not None:
                self.offline_command_queue.put(OfflineCommand(OfflineCommand.STOP, None))
                offline_thread.join()

    def start_location_thread(self):
        location_data_thread = LocationDataThread(self.lat, self.lon, self.tide_time_collection,
                                                  self.tide_time_collection_lock,
                                                  self.location_command_queue, self.xml_lock, self,
                                                  name=self.location_name)
        location_data_thread.start()

    def start_lighting_thread(self):
        lighting_thread = LightingThread(self.tide_time_collection, self.tide_time_collection_lock, self.LED_COUNT,
                                         self.led_queue,
                                         self.lighting_command_queue,
                                         name=self.lighting_name)
        lighting_thread.start()

    def start_ldr_thread(self):
        ldr_thread = LdrThread(self.ldr_pin, self.LED_BRIGHTNESS, self.LED_BRIGHTNESS, self.strip, self.strip_lock,
                               self.ldr_command_queue, name=self.ldr_name)
        ldr_thread.start()

    def start_controller_thread(self):
        controller_thread = StripControllerThread(self.strip, self.strip_lock, self.high_tide_direction_color,
                                                  self.low_tide_direction_color,
                                                  self.tide_level_indicator_color, self.no_tide_level_indicator_color,
                                                  self.tide_level_indicator_moving_colors,
                                                  self.no_tide_level_indicator_moving_colors, self.led_queue,
                                                  self.moving_pattern,
                                                  self.LED_COUNT, self.moving_speed, self.controller_command_queue,
                                                  name=self.controller_name)
        controller_thread.start()

    def start_bluetooth_thread(self):
        bluetooth_thread = BluetoothThread(self.bluetooth_command_queue, self.peripheral,
                                           name=self.bluetooth_name)
        bluetooth_thread.start()

    def start_pruner_thread(self):
        pruner_thread = OfflinePrunerThread(self.pruner_command_queue, self.xml_lock,
                                            name=self.pruner_name)
        pruner_thread.start()

    def start_offline_thread(self):
        offline_thread = OfflineThread(self.offline_command_queue,
                                       self.xml_lock,
                                       self.tide_time_collection,
                                       self.tide_time_collection_lock,
                                       self,
                                       name=self.offline_name)
        offline_thread.start()

    def reset(self):
        self.stop_location_thread()
        self.stop_controller_thread()
        self.stop_lighting_thread()
        self.stop_ldr_thread()
        self.stop_pruner_thread()
        self.stop_offline_thread()
        self._read_config_variables()
        self._create_thread_queues()

        self.strip = TideLightLedStrip(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT,
                                       self.LED_BRIGHTNESS,
                                       self.LED_CHANNEL)
        self.strip_lock = threading.Condition()
        self.led_queue = Queue()
        self.tide_time_collection = TideTimeCollection(self.LED_COUNT)
        self.tide_time_collection_lock = threading.Condition()

        self.strip.begin()
        print("starting location thread")
        self.start_location_thread()
        print("starting offline thread")
        self.start_offline_thread()
        print('starting lighting thread')
        self.start_lighting_thread()
        print('starting controller thread')
        self.start_controller_thread()
        if self.ldr_active:
            print('starting ldr thread')
            self.start_ldr_thread()
        self.start_pruner_thread()

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
        print("Stopping pruner thread")
        self.stop_pruner_thread()
        print("Stopping offline thread")
        self.stop_offline_thread()
        print("Cleaning up GPIO")
        GPIO.cleanup()
        print("Shutting down the tide light program")
        self.shutdown = True

    def xml_error(self):
        self.stop_lighting_thread()
        self.change_moving_pattern('red_blink')

    def location_update_quick(self):
        print("updating offline data")
        self.offline_command_queue.put(OfflineCommand(OfflineCommand.UPDATE_DATA_QUICK, None))

    def location_update(self):
        print("updating offline data")
        self.offline_command_queue.put(OfflineCommand(OfflineCommand.UPDATE_DATA, None))

    def offline_data_update_quick(self):
        print("stopping controller")
        self.stop_controller_thread()
        print("stopping lighting")
        self.stop_lighting_thread()
        print("starting lighting")
        self.start_lighting_thread()
        print("starting controller")
        self.start_controller_thread()
        self.location_command_queue.put(
            LocationCommand(LocationCommand.LOCATION_UPDATE, {'lat': self.lat, 'lon': self.lon}))

    def offline_data_update(self):
        print("stopping controller")
        self.stop_controller_thread()
        print("stopping lighting")
        self.stop_lighting_thread()
        print("starting lighting")
        self.start_lighting_thread()
        print("starting controller")
        self.start_controller_thread()

        lat, lon = self.config.getLatLon()
        dataString = lat + ':' + lon
        data = array.array('B', [0] * len(dataString))
        for i in range(len(dataString)):
            writeUInt8(data, ord(dataString[i]), i)
        self.peripheral.configService.latLonCharacteristic.notify(data)
