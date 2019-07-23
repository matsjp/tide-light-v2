import requests


class TideApi:
    api_url = "http://api.sehavniva.no/tideapi.php"

    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat

    def get_location_data(self, fromtime, totime):
        tide_request="locationdata"
        datatype = "TAB"
        dst="1"
        refcode="CD"
        lang="en"

        payload = {"tide_request": tide_request,
                   "fromtime": fromtime,
                   "totime": totime,
                   "datatype": datatype,
                   "dst": dst,
                   "refcode": refcode,
                   "lang": lang,
                   "lon": self.lon,
                   "lat": self.lat}
        try:
            response = requests.get(self.api_url, params=payload)
            # Check for failure in response code and raise exception if error is found
            response.raise_for_status()
            return response.content.decode()
        except requests.exceptions.Timeout as e:
            raise e
        except requests.exceptions.TooManyRedirects:
            #TODO: Handle this exception
            pass
        except requests.exceptions.RequestException as e:
            print(e)
            raise e
