from tidelight import TideTime
from datetime import datetime
from sympy import *

class TideTimeCollection:
    tide_times = []


    def __init__(self, led_count, tide_times=None):
        self.led_count = led_count

        #The leds that indicate tide level, not tide direction
        self.tide_level_led_count = led_count - 2

        #Tuple (last timestamp, led being lighted, tide direction)
        self.last_timestamp_collection = None

        if tide_times is not None:
            self.insert_tide_times(tide_times)


    def insert_tide_times(self, tide_times_list):
        times_to_be_removed = -1
        for i in range(0, len(tide_times_list)):
            if tide_times_list[i].timestamp < datetime.now().timestamp():
                times_to_be_removed += 1
            else:
                break
        for i in range(0, times_to_be_removed):
            tide_times_list.pop(0)

        for tide_time in tide_times_list:
            if not self.is_duplicate(tide_time):
                self.tide_times.append(tide_time)


    def is_empty(self):
        return not self.tide_times


    def is_duplicate(self, tide_time):
        for t in self.tide_times:
            if t.timestamp == tide_time.timestamp:
                return True
        return False


    def get_tide_direction(self):
        return self.tide_times[1].tide
