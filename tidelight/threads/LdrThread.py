import math
import time
from threading import Thread

from RPi import GPIO


class LdrThread(Thread):
    def __init__(self, ldr_pin, brightness, max_brightness, strip, strip_lock, command_queue, name=None):
        super().__init__(name=name)
        self.command_queue = command_queue
        self.ldr_pin = ldr_pin
        self.brightness = brightness
        self.max_brightness = max_brightness
        self.strip = strip
        self.strip_lock = strip_lock
        self.minLdrCount = 1
        self.maxLdrCount = 250000
        self.oldmin = 1
        self.oldmax = 500000
        self.min_brightness = 1
        self.is_stopping = False
        self.active = True
        self.handlers = {
            LdrCommand.STOP: self.stop,
            LdrCommand.SETBRIGHTNESS: self.set_brightness
        }

    def run(self):
        while not self.is_stopping:
            if self.active:
                ldrCount = self.rc_time(self.ldr_pin)
                newBrightness = self.scale_and_invert(ldrCount)
                if newBrightness != self.brightness:
                    time.sleep(1)
                    ldrCount = self.rc_time(self.ldr_pin)
                    newBrightness2 = self.scale_and_invert(ldrCount)
                    if newBrightness == newBrightness2:
                        with self.strip_lock:
                            self.strip.setBrightness(newBrightness)
                            self.brightness = newBrightness
                            self.strip_lock.notify_all()
                    elif newBrightness < self.brightness and newBrightness2 < self.brightness:
                        with self.strip_lock:
                            b = self.brightness - int((self.brightness - newBrightness)/2)
                            self.strip.setBrightness(b)
                            self.brightness = b
                            self.strip_lock.notify_all()
                    elif newBrightness > self.brightness and newBrightness2 > self.brightness:
                        with self.strip_lock:
                            b = self.brightness + int((newBrightness - self.brightness)/2)
                            self.strip.setBrightness(b)
                            self.brightness = b
                            self.strip_lock.notify_all()

            """count = self.rc_time(self.ldr_pin)
            new_brightness = self.brightness_round(self.scale_and_invert(count))
            if new_brightness != self.brightness:
                time.sleep(1)
                count = self.rc_time(self.ldr_pin)
                temp_brightness = self.brightness_round(self.scale_and_invert(count))
                if temp_brightness == new_brightness:
                    with self.strip_lock:
                        self.strip.setBrightness(new_brightness)
                        self.brightness = new_brightness
                        self.strip_lock.notify_all()"""
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)

    def brightness_round(self, brightness):
        brightness = brightness / 10
        brightness = math.ceil(brightness)
        brightness = brightness * 10
        if brightness > 255:
            return 255
        return brightness

    def rc_time(self, pin_to_circuit):
        count = 0

        # Output on the pin for
        GPIO.setup(pin_to_circuit, GPIO.OUT)
        GPIO.output(pin_to_circuit, GPIO.LOW)
        time.sleep(0.1)

        # Change the pin back to input
        GPIO.setup(pin_to_circuit, GPIO.IN)

        # Count until the pin goes high
        while GPIO.input(pin_to_circuit) == GPIO.LOW and count < self.maxLdrCount:
            count += 1

        return count

    def scale_and_invert(self, value):
        if value > self.maxLdrCount:
            value = self.maxLdrCount
        scaled = int(((value - self.minLdrCount) * (self.max_brightness - self.min_brightness)/
        (self.maxLdrCount - self.minLdrCount)) + self.min_brightness)
        if scaled < self.min_brightness:
            scaled = self.min_brightness
        if scaled > self.max_brightness:
            scaled = self.max_brightness
        invert = self.max_brightness + self.min_brightness - scaled
        return invert
        """if oldvalue > self.oldmax:
            oldvalue = self.oldmax
        if oldvalue < self.oldmin:
            oldvalue = self.oldmin
        non_inverted = int((((oldvalue - self.oldmin) * (self.max_brightness - self.newmin)) / (
                    self.oldmax - self.oldmin)) + self.newmin)
        middle = int((self.newmin + self.max_brightness) / 2)
        temp = middle - non_inverted
        if temp + middle < 1:
            return 1
        return middle + temp"""

    def stop(self, data):
        self.is_stopping = True
        with self.strip_lock:
            self.strip.setBrightness(self.max_brightness)
            self.strip_lock.notify_all()

    def set_brightness(self, data):
        self.brightness = data
        self.max_brightness = data
    
    def set_active(self, data):
        self.active = data
        if data == False:
            with self.strip_lock:
                self.strip.setBrightness(self.max_brightness)
                self.strip_lock.notify_all()

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)



class LdrCommand:
    STOP, SETBRIGHTNESS, SETACTIVE = range(3)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type
