class TideTime:
    #tide = true means that there is tide. False means that there is no tide
    def __init__(self, timestamp, tide, time):
        self.timestamp = timestamp
        #True when going towards tide
        self.tide = tide
        self.time = time

    def __eq__(self, other):
        if not isinstance(other, TideTime):
            return NotImplemented

        return self.tide == other.tide and self.time == other.time and self.timestamp == other.timestamp
