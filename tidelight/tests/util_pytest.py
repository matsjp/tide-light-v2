from tidelight import TideTime
from datetime import datetime
from tidelight.util import *


def test_xml_string():
    xml = """<tide>
<locationdata>
<location name="OSLO" code="OSL" latitude="59.908559" longitude="10.734510" delay="0" factor="1.00" obsname="OSLO" obscode="OSL" place="OSLO"/>
<reflevelcode>CD</reflevelcode>
<data type="prediction" unit="cm">
<waterlevel value="86.8" time="2019-07-30T17:42:00+02:00" flag="high"/>
<waterlevel value="52.9" time="2019-07-30T23:12:00+02:00" flag="low"/>
<waterlevel value="87.6" time="2019-07-31T06:03:00+02:00" flag="high"/>
<waterlevel value="51.1" time="2019-07-31T11:30:00+02:00" flag="low"/>
<waterlevel value="86.6" time="2019-07-31T18:27:00+02:00" flag="high"/>
</data>
</locationdata>
</tide>"""
    tide_times = []
    tide_times.append(
        TideTime(tide=True, timestamp=datetime.strptime("2019-07-30T17:42:00+0200", "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                 time="2019-07-30T17:42:00+0200"))
    tide_times.append(
        TideTime(tide=False, timestamp=datetime.strptime("2019-07-30T23:12:00+0200", "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                 time="2019-07-30T23:12:00+0200"))
    tide_times.append(
        TideTime(tide=True, timestamp=datetime.strptime("2019-07-31T06:03:00+0200", "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                 time="2019-07-31T06:03:00+0200"))
    tide_times.append(
        TideTime(tide=False, timestamp=datetime.strptime("2019-07-31T11:30:00+0200", "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                 time="2019-07-31T11:30:00+0200"))
    tide_times.append(
        TideTime(tide=True, timestamp=datetime.strptime("2019-07-31T18:27:00+0200", "%Y-%m-%dT%H:%M:%S%z").timestamp(),
                 time="2019-07-31T18:27:00+0200"))

    other_tide_time = get_TideTimeCollection_from_xml_string(xml)

    assert tide_times == other_tide_time

