from tidelight import TideTime
from tidelight.TideTimeCollection3 import TideTimeCollection


def test_insert_test_all_inserted():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    assert tide_times == tide_time_collection.tide_times


def test_insert_test_all_but_first_inserted():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 25)
    assert [TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")] == tide_time_collection.tide_times


def test_insert_duplicate():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    tide_time_collection.insert_tide_times(tide_times, 15)
    assert tide_times == tide_time_collection.tide_times


def test_is_empty_true():
    tide_time_collection = TideTimeCollection(10)
    assert tide_time_collection.is_empty()


def test_is_empty_false():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)

    assert not tide_time_collection.is_empty()


def test_is_duplicate_true():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    assert tide_time_collection.is_duplicate(TideTime(tide=True, timestamp=10, time=""))


def test_is_duplicate_false():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    assert not tide_time_collection.is_duplicate(TideTime(tide=True, timestamp=500, time=""))


def test_get_tide_direction_true():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=True, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    assert tide_time_collection.get_tide_direction()


def test_get_tide_direction_false():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time=""),
                  TideTime(tide=True, timestamp=30, time=""), TideTime(tide=False, timestamp=40, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    assert not tide_time_collection.get_tide_direction()


def test_get_timestamp_collection_empty():
    tide_time_collection = TideTimeCollection(10)
    assert tide_time_collection.get_timestamp_collection() is None


def test_get_timestamp_collection_index_error():
    tide_times = [TideTime(tide=True, timestamp=10, time=""), TideTime(tide=False, timestamp=20, time="")]
    tide_time_collection = TideTimeCollection(10)

    tide_time_collection.insert_tide_times(tide_times, 15)
    assert tide_time_collection.last_timestamp_collection is None







