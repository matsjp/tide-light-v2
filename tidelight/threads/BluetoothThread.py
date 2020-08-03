import time
from threading import Thread
from bluetooth.peripheral import Peripheral


class BluetoothThread(Thread):
    def __init__(self, command_queue, threadManagerConfigBinding, name=None):
        super().__init__(name=name)
        self.threadManagerConfigBinding = threadManagerConfigBinding
        self.command_queue = command_queue
        self.is_stopping = False
        self.handlers = {
            BluetoothCommand.STOP: self.stop
        }
        self.peripheral = Peripheral(threadManagerConfigBinding)

    def run(self):
        self.peripheral.start()
        while not self.is_stopping:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(5)

    def stop(self, data):
        self.is_stopping = True
        self.peripheral.stop()

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)


class BluetoothCommand:
    STOP = range(1)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type
