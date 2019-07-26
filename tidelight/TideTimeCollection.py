from tidelight.tidetime import TideTime

class TideTimeCollection:
    tide_times = set()

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
            self.tide_times.add(tide_time)

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

    def is_empty():
        return not tide_times

    def get_last_tide():
        return tide_times[0]

    def get_next_tide():
        return tide_times[1]

    def get_next_time_stamp
