import configparser
from kartverkettideapi.apiwrapper.TideApi import TideApi
from tidelight import TideTimeCollection
from tidelight.util import *
import requests
import time
import threading
import pause


def get_location_data_thread(api: TideApi):
    sleep_until = 0
    with tide_time_collection_lock:
        tide_time_collection_lock.notify_all()
    if type(api) is not TideApi:
        raise ValueError("Paramater api must be of type {}, not of type {}".format(TideApi, type(api)))
    while True:
        if datetime.now().timestamp() < sleep_until:
            tide_time_collection_lock.release()
            pause.until(sleep_until)

        with tide_time_collection_lock:
            try:
                response = api.get_location_data(get_next_time_from(), get_next_time_to())
                coll = get_TideTimeCollection_from_xml_string(response)
                for tidetide in coll.tide_times:
                    tide_time_collection.insert_tide_time(tidetide)

                tide_time_collection_lock.notify_all()
                pause.until(get_next_api_run())
            except requests.Timeout:
                tide_time_collection_lock.notify_all()
                time.sleep(30)
                continue



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

