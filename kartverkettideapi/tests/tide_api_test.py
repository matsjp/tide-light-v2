from kartverkettideapi.apiwrapper.TideApi import TideApi
import xmltodict
import vcr


@vcr.use_cassette('vcr_cassettes/location_data.yml')
def test_get_location_data_valid():
    expected_response = """<tide>
<locationdata>
<location name="OSLO" code="OSL" latitude="59.908559" longitude="10.734510" delay="0" factor="1.00" obsname="OSLO" obscode="OSL" place="OSLO"/>
<reflevelcode>CD</reflevelcode>
<data type="prediction" unit="cm">
<waterlevel value="43.7" time="2019-06-07T02:58:00+02:00" flag="low"/>
<waterlevel value="73.6" time="2019-06-07T09:56:00+02:00" flag="high"/>
<waterlevel value="47.9" time="2019-06-07T15:13:00+02:00" flag="low"/>
<waterlevel value="76.1" time="2019-06-07T22:07:00+02:00" flag="high"/>
<waterlevel value="41.5" time="2019-06-08T03:49:00+02:00" flag="low"/>
<waterlevel value="75.4" time="2019-06-08T10:50:00+02:00" flag="high"/>
<waterlevel value="47.3" time="2019-06-08T16:06:00+02:00" flag="low"/>
<waterlevel value="78.1" time="2019-06-08T23:00:00+02:00" flag="high"/>
<waterlevel value="39.7" time="2019-06-09T04:46:00+02:00" flag="low"/>
<waterlevel value="77.8" time="2019-06-09T11:50:00+02:00" flag="high"/>
<waterlevel value="46.4" time="2019-06-09T17:05:00+02:00" flag="low"/>
<waterlevel value="80.2" time="2019-06-10T00:01:00+02:00" flag="high"/>
<waterlevel value="38.3" time="2019-06-10T05:50:00+02:00" flag="low"/>
<waterlevel value="80.5" time="2019-06-10T12:53:00+02:00" flag="high"/>
<waterlevel value="45.5" time="2019-06-10T18:09:00+02:00" flag="low"/>
</data>
</locationdata>
</tide>"""
    expected_response = xmltodict.parse(expected_response)
    lon = "10.73451"
    lat = "59.908559"
    fromtime = "2019-06-07T00:00"
    totime = "2019-06-10T23:59"
    api = TideApi(lon=lon, lat=lat)
    response = api.get_location_data(fromtime, totime)
    response = xmltodict.parse(response)
    assert response == expected_response, "Response {} is not equal to expected response {}".format(response, expected_response)


#TODO: find some way to cause a timeout exception
def test_get_location_data_timeout():
    lon = "10.73451"
    lat = "59.908559"
    fromtime = "2019-06-07T00:00"
    totime = "2019-06-10T23:59"
    api = TideApi(lon=lon, lat=lat)
