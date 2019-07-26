import sys
sys.path.append('../')
import configparser
from kartverkettideapi.apiwrapper.TideApi import TideApi
from tidelight import TideTimeCollection
from tidelight.util import *
import requests
import time
import threading
import pause
from datetime import datetime


def get_location_data_thread(api: TideApi):
    sleep_until = 0
    #Why is this here?
    with tide_time_collection_lock:
        tide_time_collection_lock.notify_all()
    if type(api) is not TideApi:
        raise ValueError("Paramater api must be of type {}, not of type {}".format(TideApi, type(api)))
    while True:
        if datetime.now().timestamp() < sleep_until:
            tide_time_collection_lock.release()
            tide_time_collection_lock.notify_all()
            pause.until(sleep_until)

        with tide_time_collection_lock:
            try:
                response = api.get_location_data(get_next_time_from(), get_next_time_to())
                print(response)
                coll = get_TideTimeCollection_from_xml_string(response)

                times_to_be_removed = -1
                for i in range(0, len(coll)):
                    if coll[i].timestamp < datetime.now().timestamp():
                        times_to_be_removed += 1
                    else:
                        break
                for i in range(0, times_to_be_removed):
                    coll.pop(0)
                
                for tidetime in coll.tide_times:
                    tide_time_collection.insert_tide_time(tidetide)

                
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                pause.until(get_next_api_run())
            except requests.Timeout:
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                time.sleep(30)
                continue

def lighting_thread():
    tide = None
    last_tide_time = None
    while True:
        with tide_time_collection_lock:
            if not tide_time_collection:
                tide_time_collection_lock.notify_all()
                tide_time_collection_lock.release()
                time.sleep(30)
            else:
                if tide is None:
                    tide = tide_time.tide
                if last_tide_time is None:
                    last_tide_time = tide_time_collection.pop(0)
                tide_time = tide_time_collection[0]
                if tide_time.timestamp < datetime.now().timestamp():
                    last_tide_time = tide_time_collection.pop(0)
                    tide_time = tide_time_collection[0]
                    tide = tide_time.tide
                now = datetime.now().timestamp()
                fraction = (now - last_tide_time-timestamp)/(tide_time_collection[0].timestamp - last_tide_time)
                print(tide)
                print(fraction)

#TODO: create config file if it doesn't exist
config = configparser.ConfigParser()
config.read('config.ini')
lon = config.get('apivalues', 'lon')
lat = config.get('apivalues', 'lat')

tide_time_collection = TideTimeCollection()
tide_time_collection_lock = threading.Condition()

api = TideApi(lon, lat)
location_data_thread = threading.Thread(target=get_location_data_thread, args=(api,))
location_data_thread.start()

