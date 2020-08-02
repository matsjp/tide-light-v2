import os
import sys
import time
from threading import Thread
from datetime import datetime
import requests
from kartverket_tide_api import TideApi
from kartverket_tide_api.parsers import LocationDataParser

from util import TideTime, get_next_api_run, get_time_in_30s, get_next_time_to, get_next_time_from


class LocationDataThread(Thread):
    def __init__(self, lat, lon, tide_time_collection, tide_time_collection_lock, command_queue, reply_queue, xml_lock, name=None):
        super().__init__(name=name)
        self.reply_queue = reply_queue
        self.command_queue = command_queue
        self.xml_lock = xml_lock
        self.tide_time_collection_lock = tide_time_collection_lock
        self.tide_time_collection = tide_time_collection
        self.lon = lon
        self.lat = lat
        self.api = TideApi()
        self.is_stopping = False
        self.next_run = 0
        self.handlers = {
            LocationCommand.STOP: self.stop,
            LocationCommand.LOCATION_UPDATE: self.location_update
        }

    def run(self):
        while not self.is_stopping:
            if self.next_run < datetime.now().timestamp():
                print('Before acquiring')
                with self.xml_lock:
                    print("Location acquire")
                    if datetime.now().timestamp() < self.next_run:
                        print('too early')
                        print("Location release: too early")
                    else:
                        print('Going to try sending request')
                        try:
                            print("sending request")
                            response = self.api.get_location_data(self.lon, self.lat, get_next_time_from(),
                                                                  get_next_time_to(), 'TAB')

                            # TODO handle parsing exceptions
                            parser = LocationDataParser(response)
                            waterlevels = parser.parse_response()['data']
                            if waterlevels is not None:
                                if len(waterlevels) != 0:
                                    try:
                                        with open("download.xml", "w+") as xmlfile:
                                            xmlfile.write(response)
                                        if os.path.exists("offline.xml"):
                                            os.remove("offline.xml")
                                        os.rename("download.xml", "offline.xml")
                                    except Exception as e:
                                        print(e)


                            print("Location release: waiting for next data download time")
                            self.next_run = get_next_api_run()
                        except requests.exceptions.Timeout as e:
                            print(e)
                            print('Connection timeout')
                            print("Location release: 30s timeout")
                            self.next_run = get_time_in_30s()
                        except requests.exceptions.ConnectionError as e:
                            print(e)
                            print('Connection error')
                            print('Location release: 30s connection error')
                            self.next_run = get_time_in_30s()
                        except requests.exceptions.TooManyRedirects as e:
                            print(e)
                            print('TooManyRedirects')
                            print('Location release: 30s TooManyRedirects')
                            self.next_run = get_time_in_30s()
                        except requests.exceptions.RequestException as e:
                            print(e)
                            print('TooManyRedirects')
                            print('Location release: 30s RequestException')
                            self.next_run = get_time_in_30s()
                        except:
                            print("Error occured: ", sys.exc_info()[0])
                            print('Location release: 30s unknown error')
                            self.next_run = get_time_in_30s()
                    self.xml_lock.notify_all()

            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(5)

    def stop(self, data):
        self.is_stopping = True
    
    def location_update(self, data):
        self.lat = data['lat']
        self.lon = data['lon']
        with self.xml_lock:
            try:
                print("sending request")
                response = self.api.get_location_data(self.lon, self.lat, get_next_time_from(),
                                                      get_next_time_to(), 'TAB')

                # TODO handle parsing exceptions
                parser = LocationDataParser(response)
                waterlevels = parser.parse_response()['data']
                if waterlevels is not None:
                    if len(waterlevels) != 0:
                        with open("download.xml", "w+") as xmlfile:
                            xmlfile.write(response)
                        if os.path.exists("offline.xml"):
                            os.remove("offline.xml")
                        os.rename("download.xml", "offline.xml")
                    else:
                        raise Exception
                else:
                    raise Exception


                print("Location release: waiting for next data download time")
                self.next_run = get_next_api_run()
            except requests.exceptions.Timeout as e:
                print(e)
                print('Connection timeout')
                print("Location release: 30s timeout")
                self.writeBlankFile()
                self.next_run = get_time_in_30s()
            except requests.exceptions.ConnectionError as e:
                print(e)
                print('Connection error')
                print('Location release: 30s connection error')
                self.writeBlankFile()
                self.next_run = get_time_in_30s()
            except requests.exceptions.TooManyRedirects as e:
                print(e)
                print('TooManyRedirects')
                print('Location release: 30s TooManyRedirects')
                self.writeBlankFile()
                self.next_run = get_time_in_30s()
            except requests.exceptions.RequestException as e:
                print(e)
                print('TooManyRedirects')
                print('Location release: 30s RequestException')
                self.writeBlankFile()
                self.next_run = get_time_in_30s()
            except:
                print("Error occured: ", sys.exc_info()[0])
                print('Location release: 30s unknown error')
                self.writeBlankFile()
                self.next_run = get_time_in_30s()
            self.xml_lock.notify_all()
        self.reply_queue.put(LocationReply(LocationReply.LOCATION_UPDATE, None))
    
    def writeBlankFile(self):
        try:
            with open("download.xml", "w+") as xmlfile:
                xmlfile.write("")
                if os.path.exists("offline.xml"):
                    os.remove("offline.xml")
                os.rename("download.xml", "offline.xml")
        except Exception:
            pass
        

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)


class LocationCommand:
    STOP, LOCATION_UPDATE = range(2)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type


class LocationReply:
    LOCATION_UPDATE = range(1)
    
    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type
