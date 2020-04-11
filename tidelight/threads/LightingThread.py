import time
from threading import Thread
from datetime import datetime
from tidelight.LedDirection import LedDirection


class LightingThread(Thread):
    def __init__(self, tide_time_collection, tide_time_collection_lock, LED_COUNT, led_queue, offline_mode,
                 command_queue, reply_quene, name=None):
        super().__init__(name=name)
        self.reply_quene = reply_quene
        self.command_queue = command_queue
        self.offline_mode = offline_mode
        self.led_queue = led_queue
        self.LED_COUNT = LED_COUNT
        self.tide_time_collection_lock = tide_time_collection_lock
        self.tide_time_collection = tide_time_collection
        self.handlers = {
            LightingCommand.STOP: self.stop
        }
        self.is_stopping = False

    def run(self):
        next_run = 0
        while not self.is_stopping:
            if datetime.now().timestamp() > next_run:
                with self.tide_time_collection_lock:
                    print("Light acquire")
                    if self.tide_time_collection.is_empty():
                        self.tide_time_collection_lock.notify_all()
                        if self.offline_mode:
                            # TODO red blink
                            self.reply_quene.put(LightingReply(LightingReply.XMLERROR, None))
                            print('XML error')
                        print("Light release")
                    else:
                        now = datetime.now().timestamp()
                        # TODO: better variable name
                        time_stamp_collection = self.tide_time_collection.get_timestamp_collection(now)
                        if time_stamp_collection is None:
                            self.tide_time_collection_lock.notify_all()
                            if self.offline_mode:
                                # TODO red blink
                                print('XML error')
                                self.reply_quene.put(LightingReply(LightingReply.XMLERROR, None))
                            print("Light release")
                        else:
                            timestamp = time_stamp_collection[0]
                            led = time_stamp_collection[1]
                            direction = time_stamp_collection[2]
                            led_string = "{} {}{} {}"
                            if direction:
                                led_string = led_string.format("o", "x" * led, "o" * (self.LED_COUNT - 2 - led), "x")
                            else:
                                led_string = led_string.format("x", "x" * (self.LED_COUNT - 2 - (led - 1)),
                                                               "o" * (led - 1), "o")
                            print(led_string)
                            self.led_queue.put(LedDirection(led, direction))
                            self.tide_time_collection_lock.notify_all()
                            print("Light release")
                            next_run = timestamp
                            print(next_run)
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(1)
        print('Lighting thread shutting down')

    def stop(self, data):
        self.is_stopping = True

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)


class LightingCommand:
    STOP = range(1)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type


class LightingReply:
    XMLERROR = range(1)

    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type
