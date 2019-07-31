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


    def get_timestamp_collection(self):
        try:
            if datetime.now().timestamp() > self.tide_times[1].timestamp:
                self.tide_times.pop(0)
            if self.is_empty():
                #Raise indexerror?
                #Raise some error indicating that the list is empty?
                self.last_timestamp_collection = None
                return None
            if self.last_timestamp_collection is None:
                last_tide = self.tide_times[0]
                next_tide = self.tide_times[1]
                now = datetime.now().timestamp()
                fraction = (now - last_tide.timestamp)/(next_tide.timestamp - last_tide.timestamp)
                for i in range(1, 58):
                    if fraction >= (i - 1)/58 and fraction <= i/58:
                        nexttimestamp = Symbol("nexttimestamp")
                        equation = Eq((nexttimestamp - last_tide.timestamp)/(next_tide.timestamp - last_tide.timestamp), i/58)
                        timestamp = int(solve(equation)[0])

                        direction = self.get_tide_direction()


                        if direction:
                            timestamp_collection = ((timestamp, i, direction), (None, i - 1, direction))
                            if i == self.tide_level_led_count:
                                self.tide_times.pop(0)
                        else:
                            timestamp_collection = ((timestamp, i, direction), (None, i - 1, direction))
                            if i == 1:
                                self.tide_times.pop(0)
            
                        self.last_timestamp_collection = (timestamp, i, direction)
                        return timestamp_collection


            last_tide = self.tide_times[0]
            next_tide = self.tide_times[1]

            direction = self.get_tide_direction

            if direction:
                print("Direction: high")
                led = self.last_timestamp_collection[1] + 1
                if led == self.tide_level_led_count:
                    self.tide_times.pop(0)
                
            else:
                print("Direction: low")
                led = self.last_timestamp_collection[1] - 1
                if led == 1:
                    self.tide_times.pop(0)

            nexttimestamp = Symbol("nexttimestamp")
            equation = Eq((nexttimestamp - last_tide.timestamp)/(next_tide.timestamp - last_tide.timestamp), led/58)
            timestamp = int(solve(equation)[0])

            direction = self.get_tide_direction()

            timestamp_collection = ((timestamp, led, direction), self.last_timestamp_collection)
            
            self.last_timestamp_collection = (timestamp, led, direction)
            return timestamp_collection
            
        except IndexError:
            self.last_timestamp_collection = None
            raise IndexError
        


    
