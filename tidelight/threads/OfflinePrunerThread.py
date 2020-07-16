from threading import Thread
from datetime import datetime, timedelta
from util import get_time_in_1day
from queue import Queue
from xml.etree.ElementTree import ParseError
import time
from kartverket_tide_api.parsers import LocationDataParser
from kartverket_tide_api.exceptions import CannotFindElementException, NoTideDataErrorException
from kartverket_tide_api.tideobjects import WaterLevel
import xml.etree.ElementTree as ElementTree
import os

class OfflinePrunerThread(Thread):
    def __init__(self, command_queue, reply_queue, xml_lock, name=None):
        super().__init__(name=name)
        self.xml_lock = xml_lock
        self.command_queue = command_queue
        self.reply_queue = reply_queue
        self.is_stopping = False
        self.handlers = {
            OfflinePrunerCommand.STOP: self.stop
        }
        
    
    def run(self):
        next_run = 0
        while not self.is_stopping:
            if next_run < datetime.now().timestamp():
                prunedXmlString = ""
                #prune
                prune = False
                with self.xml_lock:
                    try:
                        with open('offline.xml', 'r') as xmlfile:
                            xml = xmlfile.read()
                            root = ElementTree.XML(xml)
                            
                            
                            location_data = root.find('locationdata')
                            if location_data is None:
                                raise CannotFindElementException('Cannot find location_data element')
                            nodata = location_data.find('nodata')

                            if nodata is not None:
                                raise NoTideDataErrorException('This location has no tide data')
                            data = location_data.find('data')

                            if data is None:
                                raise CannotFindElementException('Cannot find data element')

                            data_type = data.attrib['type']
                            water_levels = []
                            for water_level in data.iter('waterlevel'):
                                attribs = water_level.attrib
                                if attribs['flag'] == 'high' or attribs['flag'] == 'low':
                                    water_levels.append((WaterLevel(attribs['value'],
                                                                   attribs['time'],
                                                                   data_type,
                                                                   attribs['flag'] == 'high'), water_level))
                                else:
                                    water_levels.append((WaterLevel(attribs['value'],
                                                                   attribs['time'],
                                                                   data_type), water_level))

                            
                            
                            for waterlevel in water_levels:
                                tide = waterlevel[0].tide
                                timestring = waterlevel[0].time
                                timestring = timestring[:len(timestring) - 3] + timestring[len(timestring) - 2:]
                                timestamp = datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z").timestamp()
                                time_threshold = (datetime.now() - timedelta(days=2)).timestamp()
                                if timestamp < time_threshold:
                                    prune = True
                                    data.remove(waterlevel[1])
                                else:
                                    break
                            if prune:
                                prunedXmlString = ElementTree.tostring(root, encoding='unicode')
                    except FileNotFoundError as e:
                        print(e)
                    except ParseError as e:
                        print(e)
                    except CannotFindElementException as e:
                        print(e)
                    except Exception as e:
                        print(e)
                    if prune:
                        try:
                            with open("prune.xml", "w+") as xmlfile:
                                xmlfile.write(prunedXmlString)
                            os.rename("prune.xml", "offline.xml")
                        except Exception as e:
                                print(e)
                            
                    next_run = get_time_in_1day()
                    self.xml_lock.notify_all()
                
            if not self.command_queue.empty():
                command = self.command_queue.get()
                self.handle_command(command)
            time.sleep(5)
        
    def stop(self, data):
        self.is_stopping = True
    

    def handle_command(self, command):
        self.handlers[command.command_type](command.data)
    


def getData(xmlstring):
    root = ElementTree.XML(xmlstring)
    location_data = root.find('locationdata')
    if location_data is None:
        raise CannotFindElementException('Cannot find location_data element')
    nodata = location_data.find('nodata')
    if nodata is not None:
        raise NoTideDataErrorException('This location has no tide data')
    data = location_data.find('data')
    if data is None:
        raise CannotFindElementException('Cannot find data element')
    return data


class OfflinePrunerCommand:
    STOP = range(1)

    def __init__(self, command_type, data):
        self.data = data
        self.command_type = command_type


class OfflinePrunerReply:
    def __init__(self, reply_type, data):
        self.data = data
        self.reply_type = reply_type


    
