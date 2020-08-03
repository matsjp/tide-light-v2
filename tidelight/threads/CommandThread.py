from threading import Thread


class CommandThread(Thread):
    def __init__(self, reply_quene, thread_manager, name=None):
        super().__init__(name=name)
        self.reply_quene = reply_quene
        self.thread_manager = thread_manager
        self.handlers = {
            CommandCommand.TEST: self.test,
            CommandCommand.LATLON: self.latLon
        }

    def run(self):
        while True:
            print("Waiting for command")
            command = input()
            try:
                self.handle_command(CommandCommand(command, None))
            except KeyError:
                print(command + " is not a valid command")
    def handle_command(self, command):
        self.handlers[command.command_type](command.data)

    def test(self, data):
        print("This is a test command")

    def latLon(self, data):
        lat = 69.97
        lon = 23.29
        self.thread_manager.change_lat_lon(lat, lon)





class CommandCommand:
    TEST="test"
    LATLON="latlon"
    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type

class CommandReply:
    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type
