from tidelight import TideTime
from datetime import datetime
from sympy import *


class TideTimeCollection:

    def __init__(self, led_count):
        self.led_count = led_count

        # The leds that indicate tide level, not tide direction
        self.tide_level_led_count = led_count - 2

        # Tuple (last timestamp, led being lighted, tide direction)
        self.last_timestamp_collection = None

        self.tide_times = []

    def insert_tide_times(self, tide_times_list, now):
        times_to_be_removed = -1
        for i in range(0, len(tide_times_list)):
            if tide_times_list[i].timestamp < now:
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
        return tide_time in self.tide_times

    def get_tide_direction(self):
        return self.tide_times[1].tide

    def get_timestamp_collection(self, now):
        try:
            if self.is_empty():
                #Raise indexerror?
                #Raise some error indicating that the list is empty?
                self.last_timestamp_collection = None
            if self.last_timestamp_collection is None:
                last_tide = self.tide_times[0]
                next_tide = self.tide_times[1]
                fraction = (now - last_tide.timestamp) / (next_tide.timestamp - last_tide.timestamp)
                for i in range(1, self.tide_level_led_count):
                    if fraction >=
            else:
                pass
        except IndexError:
            self.last_timestamp_collection = None
            return None
