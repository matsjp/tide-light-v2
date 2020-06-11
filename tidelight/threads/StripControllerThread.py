import time
from threading import Thread
from queue import Queue

from rpi_ws281x import Color


class StripControllerThread(Thread):
    def __init__(self, strip, strip_lock, high_tide_direction_color, low_tide_direction_color,
                 tide_level_indicator_color,
                 no_tide_level_indicator_color, tide_level_indicator_moving_colors,
                 no_tide_level_indicator_moving_colors, led_queue, moving_pattern,
                 led_count, moving_speed, command_queue, reply_quene, name=None):
        super().__init__(name=name)
        self.reply_quene = reply_quene
        self.command_queue = command_queue
        self.moving_speed = moving_speed
        self.tide_level_indicator_moving_colors = tide_level_indicator_moving_colors
        self.no_tide_level_indicator_moving_colors = no_tide_level_indicator_moving_colors
        self.led_count = led_count
        self.strip = strip
        self.strip_lock = strip_lock
        self.high_tide_direction_color = high_tide_direction_color
        self.low_tide_direction_color = low_tide_direction_color
        self.no_tide_level_indicator_color = no_tide_level_indicator_color
        self.led_queue = led_queue
        self.moving_pattern = moving_pattern
        self.tide_level_indicator_color = tide_level_indicator_color
        self.is_stopping = False
        self.handlers = {
            ControllerCommand.STOP: self.stop,
            ControllerCommand.NEWMOVINGPATTERN: self.set_moving_pattern,
            ControllerCommand.NEWMOVINGSPEED: self.set_moving_speed,
            ControllerCommand.NEWHIGHTIDEDIRECTIONCOLOR: self.set_high_tide_direction_color,
            ControllerCommand.NEWLOWTIDEDIRECTIONCOLOR: self.set_low_tide_direction_color,
            ControllerCommand.NEWTIDELEVELINDICATORCOLOR: self.set_tide_level_indicator_color,
            ControllerCommand.NEWNOTIDELEVELINDICATORCOLOR: self.set_no_tide_level_indicator_color,
            ControllerCommand.NEWTIDELEVELINDICATORMOVINGCOLOR: self.set_tide_level_indicator_moving_colors,
            ControllerCommand.NEWNOTIDELEVELINDICATORMOVINGCOLOR: self.no_tide_level_indicator_moving_colors
        }
        self.led = None
        self.direction = None

    def run(self):
        on = True
        if self.moving_pattern != 'red_blink':
            first_time_data = self.led_queue.get()
            self.led = first_time_data.led
            self.direction = first_time_data.direction
            with self.strip_lock:
                self.strip.update_tide_leds(self.led, self.direction, self.high_tide_direction_color,
                                            self.low_tide_direction_color, self.tide_level_indicator_color,
                                            self.no_tide_level_indicator_color)
                self.strip_lock.notify_all()
        while not self.is_stopping:
            if not self.led_queue.empty():
                new_data = self.led_queue.get()
                self.led = new_data.led
                self.direction = new_data.direction
                with self.strip_lock:
                    self.strip.update_tide_leds(self.led, self.direction, self.high_tide_direction_color,
                                                self.low_tide_direction_color, self.tide_level_indicator_color,
                                                self.no_tide_level_indicator_color)
                    self.strip_lock.notify_all()
            if self.moving_pattern == 'wave':
                if self.led is not None and self.direction is not None:
                    self.led_wave(self.led, self.direction, self.command_queue)
            elif self.moving_pattern == 'regular':
                pass
            elif self.moving_pattern == 'red_blink':
                self.red_blink(on)
                on = not on

            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
                time.sleep(1)

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)

    def led_wave(self, led, direction, command_queue):
        color_queue = Queue()
        for i in range(len(self.no_tide_level_indicator_moving_colors)):
            color_queue.put((self.no_tide_level_indicator_moving_colors[i], self.tide_level_indicator_moving_colors[i]))
        # If going to tide
        if direction:
            for i in range(1, self.led_count - 1):
                with self.strip_lock:
                    color_set = color_queue.get()
                    color_queue.put(color_set)
                    if i <= led:
                        self.strip.setPixelColor(i, color_set[1])
                    else:
                        self.strip.setPixelColor(i, color_set[0])

                    previous_led = (i - color_queue.qsize()) % (self.led_count - 2)
                    if previous_led == 0:
                        previous_led = self.led_count - 2
                    if previous_led <= led:
                        self.strip.setPixelColor(previous_led, self.tide_level_indicator_color)
                    else:
                        self.strip.setPixelColor(previous_led, self.no_tide_level_indicator_color)
                    self.strip.show()
                    self.strip_lock.notify_all()
                if not command_queue.empty():
                    with self.strip_lock:
                        self.strip.update_tide_leds(led, direction, self.high_tide_direction_color,
                                                    self.low_tide_direction_color, self.tide_level_indicator_color,
                                                    self.no_tide_level_indicator_color)
                        self.strip_lock.notify_all()
                    return
                time.sleep(self.moving_speed)
        else:
            for i in range(self.led_count - 2, 0, -1):
                with self.strip_lock:
                    color_set = color_queue.get()
                    color_queue.put(color_set)
                    if i <= self.led_count - 1 - led:
                        self.strip.setPixelColor(i, color_set[1])
                    else:
                        self.strip.setPixelColor(i, color_set[0])

                    previous_led = (i + color_queue.qsize()) % (self.led_count - 2)
                    if previous_led == 0:
                        previous_led = self.led_count - 2
                    if previous_led <= self.led_count - 1 - led:
                        self.strip.setPixelColor(previous_led, self.tide_level_indicator_color)
                    else:
                        self.strip.setPixelColor(previous_led, self.no_tide_level_indicator_color)
                    self.strip.show()
                    self.strip_lock.notify_all()
                if not command_queue.empty():
                    with self.strip_lock:
                        self.strip.update_tide_leds(led, direction, self.high_tide_direction_color,
                                                    self.low_tide_direction_color, self.tide_level_indicator_color,
                                                    self.no_tide_level_indicator_color)
                        self.strip_lock.notify_all()
                    return
                time.sleep(self.moving_speed)

    # Show error with data saved in offline.xml
    def red_blink(self, on):
        with self.strip_lock:
            for i in range(self.led_count):
                if on:
                    self.strip.setPixelColor(i, Color(255, 0, 0))
                else:
                    self.strip.setPixelColor(i, Color(0, 0, 0))
            self.strip.show()
            self.strip_lock.notify_all()
            print(on)
        time.sleep(5)

    def led_regular(self, strip, led, direction, led_count, moving_color_top, moving_color_bottom, still_color_top,
                    still_color_bottom, speed):
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

    def set_moving_pattern(self, data):
        self.moving_pattern = data

    def stop(self, data):
        self.is_stopping = True

    def set_moving_speed(self, data):
        self.moving_speed = data

    def set_high_tide_direction_color(self, data):
        self.high_tide_direction_color = data
        if self.led is not None and self.direction is not None:
            with self.strip_lock:
                self.strip.update_tide_leds(self.led, self.direction, self.high_tide_direction_color,
                                        self.low_tide_direction_color, self.tide_level_indicator_color,
                                        self.no_tide_level_indicator_color)
                self.strip_lock.notify_all()

    def set_low_tide_direction_color(self, data):
        self.low_tide_direction_color = data
        if self.led is not None and self.direction is not None:
            with self.strip_lock:
                self.strip.update_tide_leds(self.led, self.direction, self.high_tide_direction_color,
                                        self.low_tide_direction_color, self.tide_level_indicator_color,
                                        self.no_tide_level_indicator_color)
                self.strip_lock.notify_all()

    def set_tide_level_indicator_color(self, data):
        self.tide_level_indicator_color = data
        if self.led is not None and self.direction is not None:
            with self.strip_lock:
                self.strip.update_tide_leds(self.led, self.direction, self.high_tide_direction_color,
                                        self.low_tide_direction_color, self.tide_level_indicator_color,
                                        self.no_tide_level_indicator_color)
                self.strip_lock.notify_all()

    def set_no_tide_level_indicator_color(self, data):
        self.no_tide_level_indicator_color = data
        if self.led is not None and self.direction is not None:
            with self.strip_lock:
                self.strip.update_tide_leds(self.led, self.direction, self.high_tide_direction_color,
                                        self.low_tide_direction_color, self.tide_level_indicator_color,
                                        self.no_tide_level_indicator_color)
                self.strip_lock.notify_all()

    def set_tide_level_indicator_moving_colors(self, data):
        self.tide_level_indicator_moving_colors = data

    def set_no_tide_level_indicator_moving_colors(self, data):
        self.no_tide_level_indicator_moving_colors = data


class ControllerCommand:
    STOP, NEWMOVINGPATTERN, NEWMOVINGSPEED, NEWHIGHTIDEDIRECTIONCOLOR, NEWLOWTIDEDIRECTIONCOLOR,\
        NEWTIDELEVELINDICATORCOLOR, NEWNOTIDELEVELINDICATORCOLOR, NEWTIDELEVELINDICATORMOVINGCOLOR,\
    NEWNOTIDELEVELINDICATORMOVINGCOLOR= range(9)
    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type


class ControllerReply:
    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type
