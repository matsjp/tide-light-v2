import time
from threading import Thread
from tidelight.bluetooth.peripheral import *


class BluetoothThread(Thread):
    def __init__(self, command_queue, reply_quene, name=None):
        super().__init__(name=name)
        self.reply_quene = reply_quene
        self.command_queue = command_queue
        self.is_stopping = False
        self.handlers = {
            BluetoothCommand.STOP: self.stop
        }

    def run(self):
        bleno.start()
        while not self.is_stopping:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(5)

    def stop(self):
        self.is_stopping = True
        bleno.stopAdvertising()
        bleno.disconnect()

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)


class BluetoothCommand:
    STOP = range(1)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type


class BluetoothReply:
    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type
