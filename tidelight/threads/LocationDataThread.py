import sys
import time
from threading import Thread
from datetime import datetime
import requests
from kartverket_tide_api import TideApi
from kartverket_tide_api.parsers import LocationDataParser

from util import TideTime, get_next_api_run, get_time_in_30s, get_next_time_to, get_next_time_from


class LocationDataThread(Thread):
    def __init__(self, lat, lon, tide_time_collection, tide_time_collection_lock, command_queue, reply_quene, name=None):
        super().__init__(name=name)
        self.reply_quene = reply_quene
        self.command_queue = command_queue
        self.tide_time_collection_lock = tide_time_collection_lock
        self.tide_time_collection = tide_time_collection
        self.lon = lon
        self.lat = lat
        self.api = TideApi()
        self.is_stopping = False
        self.handlers = {
            LocationCommand.STOP: self.stop
        }

    def run(self):
        next_run = 0
        while not self.is_stopping:
            if next_run < datetime.now().timestamp():
                print('Before acquiring')
                with self.tide_time_collection_lock:
                    print("Location acquire")
                    if datetime.now().timestamp() < next_run:
                        print('too early')
                        self.tide_time_collection_lock.notify_all()
                        print("Location release: too early")
                    else:
                        print('Going to try sending request')
                        try:
                            print("sending request")
                            response = self.api.get_location_data(self.lon, self.lat, get_next_time_from(),
                                                                  get_next_time_to(), 'TAB')

                            print(response)
                            # TODO handle parsing exceptions
                            parser = LocationDataParser(response)
                            waterlevels = parser.parse_response()['data']
                            coll = []
                            for waterlevel in waterlevels:
                                # TODO what to do if tide is None
                                tide = waterlevel.tide
                                timestring = waterlevel.time
                                timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                                timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                                # TODO figure out difference between time and timestamp. Why didn't past myself properly document that
                                coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))

                            now = datetime.now().timestamp()

                            self.tide_time_collection.insert_tide_times(coll, now)

                            self.tide_time_collection_lock.notify_all()
                            print("Location release: waiting for next data download time")
                            next_run = get_next_api_run()
                        except requests.exceptions.Timeout as e:
                            self.tide_time_collection_lock.notify_all()
                            print(e)
                            print('Connection timeout')
                            print("Location release: 30s timeout")
                            next_run = get_time_in_30s()
                        except requests.exceptions.ConnectionError as e:
                            print(e)
                            print('Connection error')
                            print('Location release: 30s connection error')
                            next_run = get_time_in_30s()
                        except requests.exceptions.TooManyRedirects as e:
                            print(e)
                            print('TooManyRedirects')
                            print('Location release: 30s TooManyRedirects')
                            next_run = get_time_in_30s()
                        except requests.exceptions.RequestException as e:
                            print(e)
                            print('TooManyRedirects')
                            print('Location release: 30s RequestException')
                            next_run = get_time_in_30s()
                        except:
                            print("Error occured: ", sys.exc_info()[0])
                            print('Location release: 30s unknown error')
                            next_run = get_time_in_30s()

            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(5)

    def stop(self):
        self.is_stopping = True

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)


class LocationCommand:
    STOP = range(2)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type


class LocationhReply:
    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type
