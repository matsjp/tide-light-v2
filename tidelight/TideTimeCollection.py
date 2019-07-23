from tidelight.tidetime import TideTime

class TideTimeCollection:
    tide_times = set()

    def insert_tide_time(self, tide_time: TideTime):
        if type(tide_time) is not TideTime:
            raise ValueError("tide_time must be of type {} not {}".format(TideTime, type(tide_time)))
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
