"""from tidelight.tidetime import TideTime
from datetime import datetime
from sympy import *

class TideTimeCollection:
    tide_times = []

    def __init__(self, led_count):
        self.led_count = led_count

        #The leds that indicate tide level, not tide direction
        self.tide_level_led_count = led_count - 2

        #Tuple (last timestamp, led being lighted, tide direction)
        self.last_timestamp_collection = None

    #Delete?
    def insert_tide_time(self, tide_time: TideTime):
        if type(tide_time) is not TideTime:
            raise ValueError("tide_time must be of type {} not {}".format(TideTime, type(tide_time)))
        self.tide_times.add(tide_time)


    def insert_tide_times(self, tide_times_list):
        times_to_be_removed = -1
        for i in range(0, len(coll)):
            if tide_times_list[i].timestamp < datetime.now().timestamp():
                times_to_be_removed += 1
            else:
                break
        for i in range(0, times_to_be_removed):
            tide_times_list.pop(0)

        for tide_time in tide_time_list:
            if not self.is_duplicate(tide_time):
                self.tide_times.add(tide_time)

    #Delete?
    def get_next_tide_time(self):
        lowest = None
        for i in self.tide_times:
            if lowest is None:
                lowest = i
            elif lowest.timestamp > i.timestamp:
                lowest = i
        if lowest is not None:
            self.tide_times.remove(lowest)
        return lowest

    def get_next_timestamp():
        try:
            if datetime.now().timestamp() > tide_times[1].timestamp:
                tide_times.pop(0)
            if self.last_timestamp_collection is None:
                #TODO
                pass
            last_tide = tide_times[0]
            next_tide = tide_times[1]
            nexttimestamp = Symbol("nexttimestamp")
            equation = Eq((now - last_tide.timestamp)/(next_tide.timestamp - last_tide.timestamp))
            timestamp = int(solve(equation)[0])

            direction = self.get_tide_direction
            if direction:
                
            
            
            
        except IndexError:
            return None

    def is_empty():
        return not tide_times

    def get_last_tide():
        return tide_times[0]

    def get_next_tide():
        return tide_times[1]

    def get_next_time_stamp

    def is_duplicate(tide_time):
        for t in tide_times:
            if t.timestamp == tide_time.timestamp:
                return True
        return False
    
    def get_tide_direction():
        return tide_times[1].tide"""
