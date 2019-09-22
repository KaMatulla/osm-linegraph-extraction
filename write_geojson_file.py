"""
Bachelor Project
Chair for Algorithm and Data Structures
Albert-Ludwigs-University Freiburg
Supervisor: Patrick Brosi

Author: Katharina Matulla <katharina.matulla@gmail.com>
"""
import datetime
import geojson


class GeojsonDump(object):
    """
    Class that saves the created nodes and ways to a .geojson file.

    >>> feature_collection = [{"geometry": {"coordinates": [10.0, 70.0],
    ...     "type": "Point"}, "id": 1, "properties": {"station": "a"},
    ...     "type": "Feature"}, {"geometry": {"coordinates": [[10.0, 70.0],
    ...     [20.0, 70.0], [80.0, 70.0], [90.0, 70.0]], "type": "LineString"},
    ...     "id": 5, "properties": {"lines": "5, 6"}, "type": "Feature"}]
    >>> dump = GeojsonDump("test.xml", feature_collection)
    >>> assert(dump._xml_file == "test.xml")
    >>> assert(len(dump._feature_collection) == 2)
    >>> assert(dump._feature_collection[0]["properties"]["station"] == "a")
    """
    def __init__(self, file_name, feature_collection):
        """
        Gets the file name and feature collection.
        """
        self._xml_file = file_name
        self._feature_collection = feature_collection
        self._now = datetime_to_str(datetime.datetime.now())

        dump_to_geojson_file(self._xml_file, self._feature_collection,
                             self._now)


@property
def get_datetime(self):
    return self._now


def dump_to_geojson_file(file_name, feature_collection, now):
    """
    Dumps feature collection as .geojson file.

    >>> feature_collection = [{"geometry": {"coordinates": [10.0, 70.0],
    ...     "type": "Point"}, "id": 1, "properties": {"station": "a"},
    ...     "type": "Feature"}, {"geometry": {"coordinates": [[10.0, 70.0],
    ...     [20.0, 70.0], [80.0, 70.0], [90.0, 70.0]], "type": "LineString"},
    ...     "id": 5, "properties": {"lines": "5, 6"}, "type": "Feature"}]
    >>> dump = GeojsonDump("test.xml", feature_collection)
    >>> counter = 0
    >>> station = 0
    >>> with open("test_files/test.geojson", "r") as file:
    ...     for line in file:
    ...         counter += 1
    ...         if 'station": "a'in line:
    ...             station += 1
    >>> assert(counter == 47)
    >>> assert(station == 1)
    """
    new_feature_collection = geojson.FeatureCollection(
                                    feature_collection)

    folder = "output/"
    if file_name[0:-4] == "test":
        now = ""
        folder = "test_files/"
    with open(folder + now + file_name[0:-4] + str(".geojson"), "w") as fp:
        geojson.dump(new_feature_collection, fp, indent=4, sort_keys=True)


def datetime_to_str(now):
    """
    Replaces datetime type with a string that can be used to save the file
    and thus assure no file gets overwritten

    >>> now = datetime_to_str("2019-02-12 19:03:50.163605")
    >>> assert(now == "2019-02-12_19-03-50_")
    >>> now = datetime_to_str("")
    >>> assert(now == "_")
    """
    now = str(now)[0:19].replace(" ", "_")
    now = now.replace(":", "-")
    now = now + "_"
    return now
