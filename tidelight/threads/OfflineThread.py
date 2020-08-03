from threading import Thread
from datetime import datetime, timedelta
import time
from kartverket_tide_api.exceptions import CannotFindElementException
from kartverket_tide_api.parsers import LocationDataParser
from xml.etree.ElementTree import ParseError
from util import get_time_in_1day, TideTime, get_time_in_30s
from TideTimeCollection import TideTimeCollection

class OfflineThread(Thread):
    def __init__(self, command_queue, xml_lock, tide_time_collection, tide_time_collection_lock, thread_manager, name=None):
        super().__init__(name=name)
        self.xml_lock = xml_lock
        self.tide_time_collection = tide_time_collection
        self.tide_time_collection_lock = tide_time_collection_lock
        self.command_queue = command_queue
        self.thread_manager = thread_manager
        self.is_stopping = False
        self.handlers = {
            OfflineCommand.STOP: self.stop,
            OfflineCommand.UPDATE_DATA: self.update_data,
            OfflineCommand.UPDATE_DATA_QUICK: self.update_data_quick
        }
        
    
    def run(self):
        next_run = 0
        while not self.is_stopping:
            if next_run < datetime.now().timestamp():
                with self.xml_lock:
                    print("Offline: xml lock aquired")
                    with self.tide_time_collection_lock:
                        print("Offline: collection lock aquired")
                        try:
                            with open('offline.xml', 'r') as xmlfile:
                                print("Starting to read file")
                                xml = xmlfile.read()
                                print("done reading file")
                            parser = LocationDataParser(xml)
                            print("parsing data")
                            waterlevels = parser.parse_response()['data']
                            print("done parsing")
                            coll = []
                            time_threshold = (datetime.now() + timedelta(days=7)).timestamp()
                            
                            print("adding data to coll")
                            for waterlevel in waterlevels:
                                tide = waterlevel.tide
                                timestring = waterlevel.time
                                timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                                timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                                if timestamp < time_threshold:
                                    coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))
                            print("done")

                            now = datetime.now().timestamp()
                            print("adding data to tide time collection")
                            self.tide_time_collection.insert_tide_times(coll, now)
                            #TODO
                            if self.tide_time_collection.is_empty():
                                pass
                                #self._xml_error(None)
                            self.tide_time_collection_lock.notify_all()
                            print("offline data ready")
                            next_run = get_time_in_1day()
                        except FileNotFoundError as e:
                            print(e)
                            #self._xml_error(None)
                            next_run = get_time_in_30s()
                            self.tide_time_collection_lock.notify_all()
                        except ParseError as e:
                            print(e)
                            #self._xml_error(None)
                            next_run = get_time_in_30s()
                            self.tide_time_collection_lock.notify_all()
                        except CannotFindElementException as e:
                            print(e)
                            #self._xml_error(None)
                            next_run = get_time_in_30s()
                            self.tide_time_collection_lock.notify_all()
                        except Exception as e:
                            print(e)
                            #self._xml_error(None)
                            next_run = get_time_in_30s()
                            self.tide_time_collection_lock.notify_all()
                    
                    
                    self.xml_lock.notify_all()
            
            
            
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(5)
        
    def stop(self, data):
        self.is_stopping = True
    
    def update_data_quick(self, data):
        with self.xml_lock:
            print("Offline: xml lock aquired")
            with self.tide_time_collection_lock:
                self.tide_time_collection.clear()
                print("Offline: collection lock aquired")
                try:
                    with open('offline.xml', 'r') as xmlfile:
                        print("Starting to read file")
                        xml = xmlfile.read()
                        print("done reading file")
                    parser = LocationDataParser(xml)
                    print("parsing data")
                    waterlevels = parser.parse_response()['data']
                    print("done parsing")
                    coll = []
                    time_threshold = (datetime.now() + timedelta(days=7)).timestamp()
                    
                    print("adding data to coll")
                    for waterlevel in waterlevels:
                        tide = waterlevel.tide
                        timestring = waterlevel.time
                        timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                        timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                        if timestamp < time_threshold:
                            coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))
                    print("done")

                    now = datetime.now().timestamp()
                    print("adding data to tide time collection")
                    self.tide_time_collection.insert_tide_times(coll, now)
                    #TODO
                    if self.tide_time_collection.is_empty():
                        pass
                        #self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                    print("offline data ready")
                except FileNotFoundError as e:
                    print(e)
                    #self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                except ParseError as e:
                    print(e)
                    #self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                except CannotFindElementException as e:
                    print(e)
                    #self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                except Exception as e:
                    print(e)
                    #self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
            
            
            self.xml_lock.notify_all()
        self.thread_manager.offline_data_update_quick()

    def update_data(self, data):
        with self.xml_lock:
            print("Offline: xml lock aquired")
            with self.tide_time_collection_lock:
                self.tide_time_collection.clear()
                print("Offline: collection lock aquired")
                try:
                    with open('offline.xml', 'r') as xmlfile:
                        print("Starting to read file")
                        xml = xmlfile.read()
                        print("done reading file")
                    parser = LocationDataParser(xml)
                    print("parsing data")
                    waterlevels = parser.parse_response()['data']
                    print("done parsing")
                    coll = []
                    time_threshold = (datetime.now() + timedelta(days=7)).timestamp()

                    print("adding data to coll")
                    for waterlevel in waterlevels:
                        tide = waterlevel.tide
                        timestring = waterlevel.time
                        timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                        timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                        if timestamp < time_threshold:
                            coll.append(TideTime(tide=tide, timestamp=timestamp, time=timestring))
                    print("done")

                    now = datetime.now().timestamp()
                    print("adding data to tide time collection")
                    self.tide_time_collection.insert_tide_times(coll, now)
                    # TODO
                    if self.tide_time_collection.is_empty():
                        pass
                        # self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                    print("offline data ready")
                except FileNotFoundError as e:
                    print(e)
                    # self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                except ParseError as e:
                    print(e)
                    # self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                except CannotFindElementException as e:
                    print(e)
                    # self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()
                except Exception as e:
                    print(e)
                    # self._xml_error(None)
                    self.tide_time_collection_lock.notify_all()

            self.xml_lock.notify_all()
        self.thread_manager.offline_data_update()
        

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)



class OfflineCommand:
    STOP, UPDATE_DATA, UPDATE_DATA_QUICK = range(3)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type
    