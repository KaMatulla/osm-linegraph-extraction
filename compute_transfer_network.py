"""
Bachelor Project
Chair for Algorithm and Data Structures
Albert-Ludwigs-University Freiburg
Supervisor: Patrick Brosi

Author: Katharina Matulla <katharina.matulla@gmail.com>
"""
import datetime
import math
import re
from dataclasses import dataclass, field
import geojson


@dataclass
class NeededElements:
    feature_collection: list = field(default_factory=list)
    dict_nodes: dict = field(default_factory=dict)
    dict_merged_nodes: dict = field(default_factory=dict)
    dict_splice_done: dict = field(default_factory=dict)
    dict_ways_stat_to_stat: dict = field(default_factory=dict)
    dict_merged_ways: dict = field(default_factory=dict)
    dict_merged_ways_ln: dict = field(default_factory=dict)
    set_new_station_ids: set = field(default_factory=set)
    dict_loop_ways: dict = field(default_factory=dict)


class TransportationSystem(object):
    """
    Class that computes station nodes, adds them to the ways and merges the
    ways of a transportation system.
    """
    def __init__(self, data):
        """
        Gets information from the parsed xml-file and the coordinates of the
        bouding box.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                   "./test_files/tram_test.xml", 5, 5, 5, 5, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> assert(tr_sys._intermediate_nodes == {})
        >>> assert(list(tr_sys._intermediate_ways.keys()) == [1234])
        >>> assert(tr_sys.min_lon == 5)
        """
        self._intermediate_nodes = data.stations_merged
        self._intermediate_ways = data.ways
        self._intermediate_node_switches = data.node_switches
        self._intermediate_needed_nodes_in_way = data.needed_nodes_in_way
        self._intermediate_relations_nodes = data.relations_nodes
        self._intermediate_relations_ways = data.relations_ways
        self._intermediate_line_colours = data.line_colours

        self.min_lon = data.min_lon
        self.min_lat = data.min_lat
        self.max_lon = data.max_lon
        self.max_lat = data.max_lat
        self._elem = NeededElements()

    def process(self):
        t = get_timestamp()
        print("["+t+"]   (merging of tram stations)")
        self.merge_tram_stations()

        t = get_timestamp()
        print("["+t+"]   Adjusting ways...")
        self.find_ways()
        t = get_timestamp()
        print("["+t+"]   Adjusting of ways complete.")

        t = get_timestamp()
        print("["+t+"]   (improving line numbers)")
        self.improve()
        self.add_ways_to_feature_collection()

    def find_ways(self):
        t = get_timestamp()
        print("["+t+"]      (include stations in ways)")
        dict_way_nodes_list, dict_splice_ways = self.find_tram_ways()

        t = get_timestamp()
        print("["+t+"]      (split ways at stations)")
        self.get_ways_for_splicing(dict_way_nodes_list, dict_splice_ways)

        t = get_timestamp()
        print("["+t+"]      (search for ways from station to station)")
        self.check_if_ways_from_station_to_station()
        dict_incid_edges_of_stations = self.find_incident_edges_of_stations()
        dict_reverted_ways = self.revert_ways()
        self.search_ways_from_station_to_station(
                            dict_reverted_ways, dict_incid_edges_of_stations)

        t = get_timestamp()
        print("["+t+"]      (merge ways)")
        self.merge_ways()

    def improve(self):
        self.add_loop_ways()
        incid_edgs_past_merge = self.get_incid_egdes()
        self.check_ln_of_stations_incid_edges(incid_edgs_past_merge)
        check_stations = check_ln_of_stations_with_four_incid_edges(
                                                    incid_edgs_past_merge)
        self.get_impossible_ln(check_stations)
        del_numbers = self.find_non_connecting_linenumbers()
        self.delete_non_connecting_linenumbers(del_numbers)
        self.add_missing_linenumbers()

    @property
    def feature_collection(self):
        return self._feature_collection

    def merge_tram_stations(self):
        """
        Merges the station nodes to one node in the middle for each station.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...             "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> assert(tr_sys._intermediate_nodes['holzmarkt'] == [
        ...                                     [1, 2.0, 2.0], [2, 4.0, 4.0]])
        >>> assert(tr_sys._intermediate_nodes['hauptbahnhof'] == [
        ...                                                     [4, 5.0, 5.0]])
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> assert(
        ...     tr_sys._elem.dict_merged_nodes[1] == [12, 3.0, 3.0])
        >>> assert(
        ...     tr_sys._elem.dict_merged_nodes[2] == [12, 3.0, 3.0])
        >>> assert(
        ...     tr_sys._elem.dict_merged_nodes[4] == [4, 5.0, 5.0])
        """
        for station in self._intermediate_nodes:
            new_lon, new_lat, new_id = self.compute_center_node(station)
            # add new station to node to keep track of the change for later use
            for node_list in self._intermediate_nodes[station]:
                new_station = [new_id, new_lon, new_lat]
                self._elem.dict_merged_nodes[node_list[0]] = new_station
            # create geojson points from station
            self.create_geojson_stations(station, new_id, new_lon, new_lat)

        t = get_timestamp()
        print("["+t+"]   (number of stations after merging: " +
              str(len(self._elem.set_new_station_ids)) + ")")

    def compute_center_node(self, station):
        """
        Computes the coordinates of the new node in the center of the old ones.
        The id of the new node is the id of the first node plus 6 digits of the
        second one and thus unique because longer (16 digits) than the other
        ids (10 digits).

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...             "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._intermediate_nodes = {
        ...         'a': [[1, 2.0, 2.0], [2, 4.0, 4.0]], 'b': [[4, 5.0, 5.0]]}
        >>> new_node = tr_sys.compute_center_node('a')
        >>> assert(new_node == (3.0, 3.0, 12))
        >>> new_node = tr_sys.compute_center_node('b')
        >>> assert(new_node == (5.0, 5.0, 4))
        >>> tr_sys._intermediate_nodes = {
        ...                                  'a': [[1, -2, -2], [2, -4, -4]]}
        >>> new_node = tr_sys.compute_center_node('a')
        >>> assert(new_node == (-3.0, -3.0, 12))
        >>> tr_sys._intermediate_nodes = {
        ...                'c': [[1, 0, 2], [2, -2, 0], [3, 2, 0], [4, 0, -2]]}
        >>> new_node = tr_sys.compute_center_node('c')
        >>> assert(new_node == (0.0, 0.0, 1234))
        """
        total_number_of_nodes = 0
        sum_lon = 0
        sum_lat = 0
        sum_node_id = ""
        # sum up the coords
        for node in self._intermediate_nodes[station]:
            node_id = node[0]
            total_number_of_nodes += 1
            sum_lon += node[1]
            sum_lat += node[2]
            sum_node_id += str(node_id)
        # compute center
        new_lon = sum_lon / total_number_of_nodes
        new_lat = sum_lat / total_number_of_nodes
        new_id = int(sum_node_id[0:16])  # other ids contain only 10 digits
        return new_lon, new_lat, new_id

    def create_geojson_stations(self, station, id, lon, lat):
        """
        Creates geojson point features from stations.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...             "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys.create_geojson_stations('a', 1, 0, 0)
        >>> tr_sys.create_geojson_stations('b', 2, -5.0, -10.2)
        >>> assert(
        ...     tr_sys._elem.feature_collection[0]['geometry'] == {
        ...     "coordinates": [0, 0], "type": "Point"})
        >>> assert(
        ...     tr_sys._elem.feature_collection[0]['properties']['id'] == "1")
        >>> assert(tr_sys._elem.feature_collection[0]['id'] == 1)
        >>> assert(
        ...     tr_sys._elem.feature_collection[1]['geometry'] == {
        ...     "coordinates": [-5.0, -10.2], "type": "Point"})
        >>> assert(
        ...     tr_sys._elem.feature_collection[1]['properties']['id'] == "2")
        >>> assert(tr_sys._elem.feature_collection[1]['id'] == 2)
        >>> assert(tr_sys._elem.set_new_station_ids == {1, 2})
        """
        while id in self._elem.set_new_station_ids:
            id += id
        self._elem.set_new_station_ids.add(id)
        new_ft_point = geojson.Point((lon, lat))
        new_point = geojson.Feature(geometry=new_ft_point,
                                    id=id,
                                    properties={"station_label": station,
                                                "id": str(id)})
        self._elem.dict_nodes[id] = new_point
        self._elem.feature_collection.append(new_point)

    def find_tram_ways(self):
        """ Constructs tram ways by including stations that are close by.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> nd_list, spl_ways = tr_sys.find_tram_ways()
        >>> assert(nd_list[4522504] == [59596550, 439829647, 6601963656601963,
        ...                                  3115855349, 439829978, 430447550])
        >>> assert(nd_list[383168674] == [3168373161162228, 611622282,
        ...             585142408, 2756259019, 585142443, 585142613, 585142617,
        ...                 523915201, 585142628, 660181658, 3168348566019643])
        >>> assert(spl_ways[4522504] == True)
        >>> assert(spl_ways[383168674] == True)
        """
        dict_way_nodes_list = {}
        dict_splice_ways = {}

        for way in self._intermediate_ways:
            way_id = int(way)
            relevant_nodes = self._intermediate_ways[way][0]
            tags = self._intermediate_ways[way][1]
            dict_way_nodes_list, dict_splice_ways = self.take_tram_way(
                                                        relevant_nodes,
                                                        way_id,
                                                        tags,
                                                        dict_way_nodes_list,
                                                        dict_splice_ways)
        return dict_way_nodes_list, dict_splice_ways

    def take_tram_way(self, relevant_nodes, way_id, tags, dict_way_nodes_list,
                      dict_splice_ways):
        """ Checks if a station node is close to a way node and if so includes
        it in the way.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> way_id = 4522504
        >>> relevant_nodes = tr_sys._intermediate_ways[way_id][0]
        >>> tags = tr_sys._intermediate_ways[way_id][1]
        >>> way_nd_ls, spl_ways = tr_sys.take_tram_way(
        ...                             relevant_nodes, way_id, tags, {}, {})
        >>> assert(way_nd_ls[4522504] == [
        ...                             59596550, 439829647, 6601963656601963,
        ...                                 3115855349, 439829978, 430447550])
        >>> assert(spl_ways[4522504] == True)
        >>> assert(tr_sys._elem.dict_merged_nodes[3115855349] == [
        ...                         6601963656601963, 7.82540472, 48.0021352])
        >>> assert(tr_sys._intermediate_nodes[
        ...                              'runzmattenweg'][3][0] == 3115855349)
        """
        lines = ""
        nodes_in_way = []
        take_way = True
        for node_ref in relevant_nodes:
            node_id = int(node_ref.get('ref'))
            if node_id in self._intermediate_needed_nodes_in_way:
                lon = float(self._intermediate_needed_nodes_in_way[node_id][0])
                lat = float(self._intermediate_needed_nodes_in_way[node_id][1])
                # take station node instead of node to connect line with
                # station if code is close
                close, station = self.check_if_close_to_station(node_id,
                                                                lon, lat)
                if close:
                    nodes_in_way, dict_splice_ways = self.add_station_to_way(
                                                      station, nodes_in_way,
                                                      way_id, dict_splice_ways)
                else:  # not close, take node
                    nodes_in_way, take_way = self.add_node_to_way(
                                                        nodes_in_way, way_id,
                                                        node_id, lines,
                                                        lon, lat, take_way)
                if take_way:
                    dict_way_nodes_list.update({way_id: nodes_in_way})
        return dict_way_nodes_list, dict_splice_ways

    def add_station_to_way(self, station, nodes_in_way, way_id,
                           dict_splice_ways):
        """
        Adds station to a way if it's not already in the way.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> nodes_in_way, spl_ways = tr_sys.add_station_to_way(
        ...                                  'runzmattenweg', [], 4522504, {})
        >>> assert(nodes_in_way == [6601963656601963])
        >>> assert(spl_ways == {4522504: True})
        >>> nodes_in_way, spl_ways = tr_sys.add_station_to_way(
        ...                  'runzmattenweg', [6601963656601963], 4522504, {})
        >>> assert(nodes_in_way == [6601963656601963])
        >>> assert(spl_ways == {})
        """
        id = self._intermediate_nodes[station][0][0]
        station_id = self._elem.dict_merged_nodes[id][0]
        if (len(nodes_in_way) > 0):  # only take station node once
            if (nodes_in_way[-1] == station_id):
                return nodes_in_way, dict_splice_ways
        station_lon = self._elem.dict_merged_nodes[id][1]
        station_lat = self._elem.dict_merged_nodes[id][2]
        nodes_in_way.append(int(station_id))
        self.create_geojson_node(station_lon, station_lat, station_id, None)
        # way needs to be spliced later
        dict_splice_ways[way_id] = True
        return nodes_in_way, dict_splice_ways

    def add_node_to_way(self, nodes_in_way, way_id, node_id, lines, lon, lat,
                        take_way):
        """
        Checks if a node of a way is within the bounding box and creates a
        geojson node if so. If not the way is rejected.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> nodes_in_way, take_way = tr_sys.add_node_to_way(
        ...                                 [34, 56], 1, 1234, "", 3, 3, True)
        >>> assert(nodes_in_way == [34, 56, 1234])
        >>> assert(take_way == True)
        >>> nodes_in_way, take_way = tr_sys.add_node_to_way(
        ...                                       [], 1, 1234, "", 0, 0, True)
        >>> assert(nodes_in_way == [1234])
        >>> assert(take_way == False)
        """
        nodes_in_way.append(int(node_id))
        lines = self.update_linenumber_of_node(node_id, way_id, lines)
        if (lat >= self.min_lat and lat <= self.max_lat
           and lon >= self.min_lon and lon <= self.max_lon):
            self.create_geojson_node(lon, lat, node_id, lines)
        else:  # don't take way if a node of it isn't within the bb
            take_way = False
        return nodes_in_way, take_way

    def update_linenumber_of_node(self, node_id, way_id, lines):
        """
        Return the lines which are saved of a node or way.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...               "./test_files/relation_test.xml", 5, 5, 5, 5, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> lines = tr_sys.update_linenumber_of_node(7, 0, "")
        >>> assert(lines == '1 ')
        >>> lines = tr_sys.update_linenumber_of_node(0, 5, "1 ")
        >>> assert(lines == '1 1 ')
        """
        if node_id in self._intermediate_relations_nodes:
            lines += self._intermediate_relations_nodes[node_id] + " "
        if (int(way_id) in self._intermediate_relations_ways):
            lines += self._intermediate_relations_ways[int(way_id)] + " "
        return lines

    def create_geojson_node(self, lon, lat, id, lines):
        """
        Creates a geojson point feature with or without lines.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys.create_geojson_node(1.5, 2.5, 1234, '3')
        >>> assert(tr_sys._elem.dict_nodes[
        ...                     1234]['geometry']['coordinates'] == [1.5, 2.5])
        >>> assert(tr_sys._elem.dict_nodes[
        ...                               1234]['geometry']['type'] == "Point")
        >>> assert(tr_sys._elem.dict_nodes[1234]['id'] == 1234)
        >>> assert(tr_sys._elem.dict_nodes[1234]['properties'] == {
        ...                                                      "lines": "3"})
        >>> tr_sys.create_geojson_node(1.5, 2.5, 12345, None)
        >>> assert(tr_sys._elem.dict_nodes[12345]['id'] == 12345)
        >>> assert(tr_sys._elem.dict_nodes[12345]['properties'] == {
        ...                                                     "lines": None})
        """
        new_ft_point = geojson.Point((lon, lat))
        if (lines is not None):
            new_point = geojson.Feature(geometry=new_ft_point,
                                        id=int(id),
                                        properties={"lines": lines})
            # self._elem.feature_collection.append(new_feature_point)
        elif (lines is None):
            new_point = geojson.Feature(geometry=new_ft_point,
                                        id=int(id),
                                        properties={"lines": None})
        self._elem.dict_nodes[int(id)] = new_point

    def check_if_close_to_station(self, node_id, node_lon, node_lat):
        """ Returns True and the station if a node lies within max distance
        of a station, False and None otherwise.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...     "./test_files/close_to_station_test.xml", 0, 0, 10, 10, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> assert(tr_sys._elem.dict_merged_nodes == {
        ...                                                  1: [1, 5.0, 5.0]})
        >>> close = tr_sys.check_if_close_to_station(1, 5, 5)
        >>> assert(close == (True, 'test station'))
        >>> close = tr_sys.check_if_close_to_station(1, 5.01, 5)
        >>> assert(close == (False, None))
        >>> close = tr_sys.check_if_close_to_station(1, 5.0001, 5)
        >>> assert(close == (True, 'test station'))
        >>> close = tr_sys.check_if_close_to_station(
        ...                                                  1, 5.0001, 5.0001)
        >>> assert(close == (True, 'test station'))
        """
        for station in self._intermediate_nodes:
            id = self._intermediate_nodes[station][0][0]
            station_lon = self._elem.dict_merged_nodes[id][1]
            station_lat = self._elem.dict_merged_nodes[id][2]
            max_dist = get_max_dist(station)
            if (((abs(float(station_lon) - float(node_lon)) <= max_dist) &
               (abs(float(station_lat) - float(node_lat)) <= max_dist))):
                return (True, station)
            else:
                continue
        return (False, None)

    def get_ways_for_splicing(self, dict_way_nodes_list, dict_splice_ways):
        """ Splices ways at station points so that every way which contains a
        station point either starts or ends at that station.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.set_new_station_ids = {1, 2}
        >>> tr_sys.get_ways_for_splicing(
        ...                                     {10: [0, 1, 3, 4]}, {10: True})
        >>> assert(tr_sys._elem.dict_splice_done[10] == [0, 1])
        >>> assert(tr_sys._elem.dict_splice_done[20] == [1, 3, 4])
        >>> tr_sys.get_ways_for_splicing(
        ...                               {10: [0, 1, 3, 4, 1, 5]}, {10: True})
        >>> assert(tr_sys._elem.dict_splice_done[10] == [0, 1])
        >>> assert(tr_sys._elem.dict_splice_done[20] == [1, 3, 4, 1])
        >>> assert(tr_sys._elem.dict_splice_done[40] == [1, 5])
        >>> tr_sys.get_ways_for_splicing(
        ...                               {10: [0, 1, 3, 4, 2, 5]}, {10: True})
        >>> assert(tr_sys._elem.dict_splice_done[10] == [0, 1])
        >>> assert(tr_sys._elem.dict_splice_done[20] == [1, 3, 4, 2])
        >>> assert(tr_sys._elem.dict_splice_done[40] == [2, 5])
        >>> tr_sys.get_ways_for_splicing({10: [0, 1, 2, 3]}, {})
        >>> assert(tr_sys._elem.dict_splice_done[10] == [0, 1, 2, 3])
        """
        dict_no_splice_ways = {}
        dict_spliced_ways = {}
        for way_id in dict_way_nodes_list:
            if way_id in dict_splice_ways:
                nodes_list = dict_way_nodes_list[way_id]
                way_spliced = False
                if len(nodes_list) > 1:
                    way_spliced, spliced_ways = self.splice_ways_at_stations(
                                               nodes_list, way_spliced, way_id)
                if not way_spliced:
                    dict_spliced_ways[way_id] = nodes_list
                if way_spliced:
                    new_ways = spliced_ways[way_id]
                    while len(new_ways) > 0:
                        while way_id in dict_spliced_ways:
                            way_id += way_id
                        dict_spliced_ways[way_id] = new_ways[0]
                        new_ways = new_ways[1:]
            else:
                way = dict_way_nodes_list[way_id]
                dict_no_splice_ways[way_id] = way
        self._elem.dict_splice_done.update(dict_no_splice_ways)
        self._elem.dict_splice_done.update(dict_spliced_ways)

    def splice_ways_at_stations(self, nodes_list, way_spliced, way_id):
        """
        Splices ways at station points so that the resulting ways both contain
        the station node.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.set_new_station_ids = {1, 2}
        >>> result = tr_sys.splice_ways_at_stations(
        ...                                             [1, 3, 4, 5], True, 10)
        >>> assert(result == (True, {10: [[1, 3, 4, 5]]}))
        >>> result = tr_sys.splice_ways_at_stations(
        ...                                             [3, 1, 4, 5], True, 10)
        >>> assert(result == (True, {10: [[3, 1], [1, 4, 5]]}))
        >>> result = tr_sys.splice_ways_at_stations(
        ...                                      [3, 1, 4, 5, 1, 6], False, 10)
        >>> assert(result == (True, {10: [[3, 1], [1, 4, 5, 1], [1, 6]]}))
        """
        index = 0
        subindex = 0
        dict_spliced_ways = {}
        dict_spliced_ways[way_id] = []
        for node_id in nodes_list:
            if ((node_id in self._elem.set_new_station_ids) &
               (index > 0) & (index <= (len(nodes_list)-2))):
                new_list = nodes_list[subindex:index+1]
                dict_spliced_ways[way_id].append((new_list))
                way_spliced = True
                subindex = index
            index += 1
        if way_spliced:
            dict_spliced_ways[way_id].append((nodes_list[subindex:]))
        return way_spliced, dict_spliced_ways

    def check_if_ways_from_station_to_station(self):
        """ Finds ways which already go from station to station.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat == {})
        >>> tr_sys._elem.set_new_station_ids = {1, 2}
        >>> tr_sys.get_ways_for_splicing({10: [1, 3, 4, 2]}, {10: True})
        >>> tr_sys.check_if_ways_from_station_to_station()
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat == {
        ...                                                  10: [1, 3, 4, 2]})
        >>> tr_sys._elem.dict_ways_stat_to_stat = {}
        >>> tr_sys.get_ways_for_splicing({10: [1, 3, 4, 1]}, {10: True})
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat == {})
        """
        for way_id in self._elem.dict_splice_done:
            first_nd = self._elem.dict_splice_done[way_id][0]
            last_nd = self._elem.dict_splice_done[way_id][-1]
            if ((first_nd in self._elem.set_new_station_ids)
               and (last_nd in self._elem.set_new_station_ids)):
                way = self._elem.dict_splice_done[way_id]
                if (first_nd != last_nd):
                    self._elem.dict_ways_stat_to_stat[way_id] = way
                self.detect_loops(way_id, way, first_nd, last_nd)

    def detect_loops(self, way_id, way, first_nd, last_nd):
        """
        Detect and saves loop ways and their line number to dicts.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_splice_done = {2: [1, 2]}
        >>> tr_sys.detect_loops(2, [1], 1, 1)
        >>> assert(tr_sys._elem.dict_loop_ways == {})
        >>> tr_sys.detect_loops(2, [1, 2, 3, 1], 1, 1)
        >>> assert(tr_sys._elem.dict_loop_ways == {2: [1, 2, 3, 1]})
        >>> tr_sys._elem.dict_nodes = {2: {"properties": {"lines": "3, 4"}}}
        >>> tr_sys.detect_loops(2, [1, 2, 3, 1], 1, 1)
        >>> assert(tr_sys._elem.dict_merged_ways_ln == {2: '3, 4'})
        """
        if (first_nd == last_nd and len(way) > 1):
            self._elem.dict_loop_ways[way_id] = way
            linenumbers = ""
            for node_id in self._elem.dict_splice_done[way_id]:
                if node_id in self._elem.dict_nodes:
                    linenumbers += str(self._elem.dict_nodes[int(node_id)]
                                       ["properties"]["lines"])
                    linenumbers += " "
                    linenr = pretty_linenumbers(linenumbers)
                    self._elem.dict_merged_ways_ln[way_id] = linenr
            linenr = pretty_linenumbers(linenumbers)
            self._elem.dict_merged_ways_ln[way_id] = linenr

    def find_incident_edges_of_stations(self):
        """ Gets all way ids of ways which are incident to a station.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_splice_done = {1: [2, 4, 5], 4: [3, 2]}
        >>> tr_sys._elem.set_new_station_ids = {2, 3}
        >>> incid_edges = tr_sys.find_incident_edges_of_stations()
        >>> assert(incid_edges == {2: [1, 4], 3: [4]})
        >>> tr_sys._elem.dict_splice_done = {1: [4, 5, 6], 4: [7, 8]}
        >>> incid_edges = tr_sys.find_incident_edges_of_stations()
        >>> assert(incid_edges == {})
        """
        dict_incid_edges_of_stations = {}
        for way_id in self._elem.dict_splice_done:
            for node in self._elem.dict_splice_done[way_id]:
                if node in self._elem.set_new_station_ids:
                    if node not in dict_incid_edges_of_stations:
                        dict_incid_edges_of_stations[node] = []
                        dict_incid_edges_of_stations[node].append(way_id)
                    elif node in dict_incid_edges_of_stations:
                        dict_incid_edges_of_stations[node].append(way_id)
        return dict_incid_edges_of_stations

    def revert_ways(self):
        """
        Reverts all ways and returns them in a dict.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_splice_done = {1: [1, 2, 3, 4]}
        >>> rev_ways = tr_sys.revert_ways()
        >>> assert(rev_ways == {1: [4, 3, 2, 1]})
        >>> tr_sys._elem.dict_splice_done = {1: [4, 3, 2, 1]}
        >>> rev_ways = tr_sys.revert_ways()
        >>> assert(rev_ways == {1: [1, 2, 3, 4]})
        """
        dict_reverted_ways = {}
        for w_id in self._elem.dict_splice_done.keys():
            dict_reverted_ways[w_id] = self._elem.dict_splice_done[w_id][::-1]
        return dict_reverted_ways

    def search_ways_from_station_to_station(self, dict_reverted_ways,
                                            dict_incid_edges_of_stations):
        """ Iterates through all ways that start with a station and tries to
        find a path which ends at another station.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> way_nd_ls, spl_ways = tr_sys.find_tram_ways()
        >>> tr_sys.get_ways_for_splicing(way_nd_ls, spl_ways)
        >>> tr_sys.check_if_ways_from_station_to_station()
        >>> inc_ed_sta = tr_sys.find_incident_edges_of_stations()
        >>> dict_reverted_ways = tr_sys.revert_ways()
        >>> tr_sys.search_ways_from_station_to_station(
        ...                                     dict_reverted_ways, inc_ed_sta)
        >>> assert(len(tr_sys._elem.set_new_station_ids) == 5)
        >>> assert(len(tr_sys._elem.dict_ways_stat_to_stat) == 7)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                   45899341][0] == 3168373161162228)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                   48280885][0] == 3168373161162228)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                  45899341][-1] == 6533141936533141)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                  48280885][-1] == 6533141936533141)
        >>> assert(tr_sys._elem.dict_merged_nodes[653314193] == [
        ...                         6533141936533141, 7.83660385, 47.99800335])
        >>> assert(
        ...    tr_sys._intermediate_nodes['eschholzstraße'][0][0] == 653314193)
        >>> assert(tr_sys._elem.dict_merged_nodes[
        ...  31683731] == [3168373161162228, 7.8319955750000005, 48.000213675])
        >>> assert(tr_sys._intermediate_nodes[
        ...                         'rathaus im stühlinger'][0][0] == 31683731)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                  383168669][0] == 3168348566019643)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                  383168674][0] == 3168373161162228)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                 383168669][-1] == 3168373161162228)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[
        ...                                 383168674][-1] == 3168348566019643)
        >>> assert(tr_sys._elem.dict_merged_nodes[
        ...                                   31683485][0] == 3168348566019643)
        >>> assert(
        ... tr_sys._intermediate_nodes['robert koch straße'][0][0] == 31683485)
        """
        for station_id in dict_incid_edges_of_stations:
            # start way is first id of way
            for start_way in dict_incid_edges_of_stations[station_id]:
                if self._elem.dict_splice_done[start_way][0] != station_id:
                    continue
                # look for the next connecting way, break if it's a node
                way_stat_to_stat = []
                done = False
                way_stat_to_stat += self._elem.dict_splice_done[start_way]
                get_last_el = len(self._elem.dict_splice_done[start_way]) - 1
                node_id = self._elem.dict_splice_done[start_way][get_last_el]
                # get next way --> node_id has to be first node in next way
                self.forward_search(done, node_id, way_stat_to_stat,
                                    start_way, dict_reverted_ways)

    def forward_search(self, done, node_id, way_stat_to_stat, start_way,
                       dict_reverted_ways):
        """ Connects each station with another station if a connecting
        way-sequence is found.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_splice_done = {1: [2, 4, 5], 4: [5, 6]}
        >>> tr_sys._elem.set_new_station_ids = {2, 6}
        >>> tr_sys._elem.dict_ways_stat_to_stat = {}
        >>> tr_sys._intermediate_node_switches = {}
        >>> rev_ways = tr_sys.revert_ways()
        >>> tr_sys.forward_search(False, 5, [2, 4, 5], 1, rev_ways)
        >>> assert(
        ... tr_sys._elem.dict_ways_stat_to_stat[1]  == [2, 4, 5, 6])
        >>> tr_sys._elem.set_new_station_ids = {2, 8}
        >>> tr_sys._elem.dict_splice_done = {
        ...                              1: [2, 4, 5], 2: [5, 6], 3: [6, 7, 8]}
        >>> rev_ways = tr_sys.revert_ways()
        >>> tr_sys.forward_search(False, 5, [2, 4, 5], 1, rev_ways)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[1]  == [
        ...                                                  2, 4, 5, 6, 7, 8])
        >>> tr_sys._elem.dict_ways_stat_to_stat = {}
        >>> tr_sys._elem.dict_splice_done = {
        ...                           1: [2, 4, 5], 2: [5, 6, 8], 3: [5, 7, 8]}
        >>> rev_ways = tr_sys.revert_ways()
        >>> tr_sys.forward_search(False, 5, [2, 4, 5], 1, rev_ways)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[1] == [
        ...                                                     2, 4, 5, 6, 8])
        """
        i = 0
        while (not done):
            i += 1
            if i > 100:  # prevent unterminable while loop
                t = get_timestamp()
                print("["+t+"]      (forceful terminated forward search)")
                done = True
                break
            # node is station
            if self.check_if_station(node_id):
                found_way = True
                done = True
                break
            # not a station, continue search until station is found
            # or until nothing more is possible
            elif node_id not in self._elem.set_new_station_ids:
                found_way = False
                for way_id in self._elem.dict_splice_done.keys():
                    # find next way
                    way_segment = self._elem.dict_splice_done[way_id]
                    if (way_segment[0] == node_id):
                        # next way segment found
                        found_way = True
                        way_stat_to_stat += way_segment[1:]
                        if (way_stat_to_stat[0] == 2648704086640082 and
                           way_stat_to_stat[-1] == 668862256):
                            way_stat_to_stat, way_id = self.solve_search_error(
                                                              way_stat_to_stat)
                        node_id = self._elem.dict_splice_done[way_id][-1]
                        if node_id in self._elem.set_new_station_ids:
                            if way_stat_to_stat:
                                if way_stat_to_stat[0] != way_stat_to_stat[-1]:
                                    self._elem.dict_ways_stat_to_stat[
                                                  start_way] = way_stat_to_stat
                            done = True
                            break
                        if node_id in self._intermediate_node_switches:
                            done = True
                            break

                if not found_way and len(way_stat_to_stat) > 1:
                    self.reverse_search(way_stat_to_stat, node_id,
                                        start_way, dict_reverted_ways)
                    done = True

    def reverse_search(self, way_stat_to_stat, node_id, start_way,
                       dict_reverted_ways):
        """ Connects each station with another station if a way-sequence is
        found using the reversed ways.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_splice_done = {1: [2, 4, 5, 7], 4: [6, 3, 7]}
        >>> tr_sys._elem.set_new_station_ids = {2, 6}
        >>> tr_sys._elem.dict_ways_stat_to_stat = {}
        >>> tr_sys._intermediate_node_switches = {}
        >>> rev_ways = tr_sys.revert_ways()
        >>> tr_sys.reverse_search([2, 4, 5, 7], 7, 1, rev_ways)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat == {
        ...                                             1: [2, 4, 5, 7, 3, 6]})
        >>> tr_sys._elem.dict_ways_stat_to_stat = {}
        >>> tr_sys._elem.set_new_station_ids = {2, 8}
        >>> tr_sys._elem.dict_splice_done = {
        ...                              1: [2, 4, 5], 2: [6, 5], 3: [8, 7, 6]}
        >>> rev_ways = tr_sys.revert_ways()
        >>> tr_sys.reverse_search([2, 4, 5], 5, 1, rev_ways)
        >>> assert(tr_sys._elem.dict_ways_stat_to_stat[1] == [
        ...                                                  2, 4, 5, 6, 7, 8])
        """
        done = False
        node_id = way_stat_to_stat[-1]

        i = 0
        while (not done):
            i += 1
            if i > 100:  # prevent unterminable while loop
                t = get_timestamp()
                print("["+t+"]      (forceful terminated backward search)")
                done = True
                break
            # node is station
            if self.check_if_station(node_id):
                found_way = True
                done = True
                break
            # not a station, continue search, until a station is found
            # or until nothing more is possible
            elif node_id not in self._elem.set_new_station_ids:
                found_way = False

            for way_id in dict_reverted_ways.keys():
                way_segment = dict_reverted_ways[way_id]
                if (way_segment[0] == node_id and
                   way_segment[-1] != way_stat_to_stat[0]):
                    # next way segment found
                    found_way = True
                    way_stat_to_stat += way_segment[1:]
                    node_id = way_segment[-1]
                    if (node_id in self._elem.set_new_station_ids and
                       node_id != way_stat_to_stat[0]):
                        if way_stat_to_stat:
                            if way_stat_to_stat[0] != way_stat_to_stat[-1]:
                                self._elem.dict_ways_stat_to_stat[
                                                  start_way] = way_stat_to_stat
                        done = True
                        break
                    if node_id in self._intermediate_node_switches:
                        done = True
                        break
            if not found_way:
                done = True

    def solve_search_error(self, way_stat_to_stat):
        """
        Hard coded search step for the Freiburg 2019 file. Not needed for the
        Freiburg 2018 file.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_splice_done = {165998767: [2, 4, 5, 7]}
        >>> way, way_id = tr_sys.solve_search_error([1, 2])
        >>> assert(way_id == 165998767)
        >>> assert(way == [1, 2, 4, 5, 7])
        """
        way_segment = self._elem.dict_splice_done[165998767]
        way_stat_to_stat += way_segment[1:]
        way_id = 165998767
        return way_stat_to_stat, way_id

    def check_if_station(self, node_id):
        """
        Returns true if node is a station, false otherwise.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.set_new_station_ids = {1, 2}
        >>> stat = tr_sys.check_if_station(1)
        >>> assert(stat == True)
        >>> stat = tr_sys.check_if_station(3)
        >>> assert(stat == False)
        """
        if node_id in self._elem.set_new_station_ids:
            return True
        return False

    def get_ways_with_same_start_and_end_nodes(self):
        """
        Returns a dict of ways which have the same start and end station and
        thus need to be merged.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_ways_stat_to_stat = {1: [1, 2, 3],
        ...         2: [1, 2, 3], 3: [1, 2, 3], 4: [1, 2, 3]}
        >>> merge = tr_sys.get_ways_with_same_start_and_end_nodes()
        >>> assert(merge[(1, 3)] == [
        ...    [1, [1, 2, 3]], [2, [1, 2, 3]], [3, [1, 2, 3]], [4, [1, 2, 3]]])
        >>> tr_sys._elem.dict_ways_stat_to_stat = {1: [1, 2, 3],
        ...         2: [1, 3, 4]}
        >>> merge = tr_sys.get_ways_with_same_start_and_end_nodes()
        >>> assert(merge[(1, 3)] == [[1, [1, 2, 3]]])
        >>> assert(merge[(1, 4)] == [[2, [1, 3, 4]]])
        """
        # check if ways have the same start end end station
        ways_to_merge = {}
        for way_id in self._elem.dict_ways_stat_to_stat.keys():
            way = self._elem.dict_ways_stat_to_stat[way_id]
            minimum = min(way[0], way[-1])
            maximum = max(way[0], way[-1])
            if (minimum, maximum) in ways_to_merge:
                if way[0] > way[-1]:
                    way.reverse()
                    ways_to_merge[(minimum, maximum)].append([way_id, way])
                else:
                    ways_to_merge[(minimum, maximum)].append([way_id, way])
            else:
                ways_to_merge[(minimum, maximum)] = []
                if way[0] > way[-1]:
                    way.reverse()
                    ways_to_merge[(minimum, maximum)].append([way_id, way])
                else:
                    ways_to_merge[(minimum, maximum)].append([way_id, way])
        return ways_to_merge

    def raise_linenumbers_from_nodes_to_ways(self, lines, way):
        """
        Returns all lines that are saved to the node ids of the ways.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_nodes = {
        ...                1: {"properties": {"lines": ""}, "type": "Feature"},
        ...                2: {"properties": {"lines": "3, 5 "}}}
        >>> lines = tr_sys.raise_linenumbers_from_nodes_to_ways(
        ...                                              "", [1, [0, 1, 2, 3]])
        >>> assert(lines == "3, 5")
        >>> lines = tr_sys.raise_linenumbers_from_nodes_to_ways(
        ...                                            "4 ", [1, [0, 1, 2, 3]])
        >>> assert(lines == "3, 4, 5")
        """
        pointer = 0
        for node_id in way[1]:
            if ((pointer == 0) or (pointer == len(way[1])-1)):
                pointer += 1
                continue
            pointer += 1
            lines += self.get_linenumbers(node_id)
        lines = pretty_linenumbers(lines)
        return lines

    def no_merge(self, ways_to_merge, tuple):
        """
        Saves ways and their line numbers that don't need to be merged
        to a new dict.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_nodes = {
        ...                1: {"properties": {"lines": ""}, "type": "Feature"},
        ...                2: {"properties": {"lines": "3, 5 "}}}
        >>> tr_sys.no_merge({(0, 3): [[1, [0, 1, 2, 3]]]}, tuple=(0, 3))
        >>> assert(tr_sys._elem.dict_merged_ways == {1: [0, 1, 2, 3]})
        >>> assert(tr_sys._elem.dict_merged_ways_ln == {1: '3, 5'})
        >>> tr_sys._elem.dict_merged_ways = {}
        >>> tr_sys.no_merge({(0, 3): [[7, [0, 1, 2, 0]]]}, tuple=(0, 3))
        >>> assert(tr_sys._elem.dict_merged_ways == {})
        """
        way = ways_to_merge[tuple][0][1]
        if (way[0] != way[-1]):
            self._elem.dict_merged_ways[ways_to_merge[tuple][0][0]] = way
            # get linenumbers accordingly
            lines = ""
            for way_id in ways_to_merge[tuple]:
                lines = self.raise_linenumbers_from_nodes_to_ways(
                                                                 lines, way_id)
                self._elem.dict_merged_ways_ln[way_id[0]] = lines

    def merge_ways(self):
        """ Checks which ways need to be merged and calls the according
        functions.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...              "./test_files/merge_test.xml", 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> assert(len(tr_sys._elem.dict_merged_ways) == 3)
        >>> assert(tr_sys._elem.dict_merged_ways[1] == [5, 19, 20, 21, 6])
        >>> assert(tr_sys._elem.dict_merged_ways[3] == [3, 12, 17, 4])
        >>> assert(tr_sys._elem.dict_merged_ways[5] == [1, 8, 10, 2])
        >>> assert(tr_sys._elem.dict_merged_ways_ln[1] == '1')
        >>> assert(tr_sys._elem.dict_merged_ways_ln[3] == '2, 3, 4')
        >>> assert(tr_sys._elem.dict_merged_ways_ln[5] == '5, 6')
        """
        ways_to_merge = self.get_ways_with_same_start_and_end_nodes()
        for tuple in ways_to_merge:
            if len(ways_to_merge[tuple]) <= 1:   # no need for merging
                self.no_merge(ways_to_merge, tuple)
            elif len(ways_to_merge[tuple]) > 1:  # merge ways
                shortest_way, longer_ways = prepare_ways_for_merging(
                                                          ways_to_merge, tuple)
                sv_w, new_w, new_w_id, new_lines_dict = self.create_new_way(
                                                     shortest_way, longer_ways)
                if sv_w:
                    self.save_new_way(new_w, new_w_id, new_lines_dict)

    def create_new_way(self, shortest_way, longer_ways):
        """
        Iterates through the nodes of the shortest way and finds the closest
        nodes of the longer way. Calls helper functions to compute the center
        of all those nodes and adds it to the new merged line.
        Merges the line numbers accordingly. Returns the new merged line and
        line numbers or False and None if a node can not be found in a dict.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...              "./test_files/merge_test.xml", 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> sv_w, new_w, new_w_id, new_ln = tr_sys.create_new_way(
        ... [3, [3, 12, 17, 4]],
        ... [[2, [3, 13, 15, 18, 4]], [4, [3, 11, 14, 16, 4]]])
        >>> assert(sv_w == True)
        >>> assert(new_w == [3, 12, 17, 4])
        >>> assert(new_w_id == 3)
        >>> sv_w, new_w, new_w_id, new_ln = tr_sys.create_new_way(
        ...                             [10, [3, -5, 17, 4]], [[2, [3, 5, 4]]])
        >>> assert(sv_w == False)
        >>> assert(new_w == None)
        """
        new_lines_dict = {}
        stop = False
        new_w = []
        new_w_id = shortest_way[0]
        new_w.append(shortest_way[1][0])  # start station
        pointer_s = 0
        for node_id_s in shortest_way[1]:
            linenumbers = ""
            if ((pointer_s == 0) or (pointer_s == len(shortest_way[1])-1)):
                pointer_s += 1
                continue
            if not(int(node_id_s) in self._elem.dict_nodes):
                stop = True
                continue
            linenumbers += self.get_linenumbers(node_id_s)
            compute_mid_node = []
            pointer_s += 1
            coord_node_s = self._elem.dict_nodes[
                                           int(node_id_s)].geometry.coordinates
            for long_way in longer_ways:
                compute_mid_node, new_lines_dict_ret = self.get_closest_nodes(
                                                    long_way, compute_mid_node,
                                                    linenumbers, coord_node_s,
                                                    new_w_id)
                for key in new_lines_dict_ret:
                    if key in new_lines_dict:
                        new_lines_dict[key] += new_lines_dict_ret[key]
                    else:
                        new_lines_dict[key] = new_lines_dict_ret[key]
            if not stop:
                new_lon, new_lat = compute_middle_node_way(compute_mid_node)
                new_id = node_id_s
                self.save_new_node(new_lon, new_lat, new_id)
                new_w.append(new_id)
        if not stop:
            new_w.append(shortest_way[1][-1])  # stop stat.
            return True, new_w, new_w_id, new_lines_dict
        elif stop:
            return False, None, None, None

    def save_new_node(self, lon, lat, id):
        """
        Saves coordinates to a geojson dict.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...              "./test_files/merge_test.xml", 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> assert(
        ...     tr_sys._elem.dict_nodes[1]["geometry"]["coordinates"][0] != 30)
        >>> assert(
        ...     tr_sys._elem.dict_nodes[1]["geometry"]["coordinates"][1] != 20)
        >>> tr_sys.save_new_node(20, 30, 1)
        >>> assert(
        ...     tr_sys._elem.dict_nodes[1]["geometry"]["coordinates"][0] == 20)
        >>> assert(
        ...     tr_sys._elem.dict_nodes[1]["geometry"]["coordinates"][1] == 30)
        """
        self._elem.dict_nodes[id]["geometry"]["coordinates"][0] = lon
        self._elem.dict_nodes[id]["geometry"]["coordinates"][1] = lat

    def save_new_way(self, new_w, new_w_id, new_lines_dict):
        """
        Saves a way and the according line numbers to dicts.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys.save_new_way([1], 5, {5: '8'})
        >>> assert(tr_sys._elem.dict_merged_ways == {})
        >>> assert(tr_sys._elem.dict_merged_ways_ln == {})
        >>> tr_sys.save_new_way([1, 2, 3], 5, {5: '8'})
        >>> assert(tr_sys._elem.dict_merged_ways[5] == [1, 2, 3])
        >>> assert(tr_sys._elem.dict_merged_ways_ln[5] == '8')
        """
        if len(new_w) > 2:
            self._elem.dict_merged_ways[new_w_id] = new_w
            linenr = pretty_linenumbers(new_lines_dict[new_w_id])
            self._elem.dict_merged_ways_ln[new_w_id] = linenr

    def get_linenumbers(self, id):
        """
        Returns the line numbers of a given node id.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_nodes = {
        ...                1: {"properties": {"lines": ""}, "type": "Feature"},
        ...                2: {"properties": {"lines": "3, 7 "}}}
        >>> lines = tr_sys.get_linenumbers(1)
        >>> assert(lines == " ")
        >>> lines = tr_sys.get_linenumbers(2)
        >>> assert(lines == "3, 7  ")
        >>> lines = tr_sys.get_linenumbers(3)
        >>> assert(lines == " ")
        """
        id = int(id)
        if id in self._elem.dict_nodes:
            linenumbers = str(self._elem.dict_nodes[id]["properties"]["lines"])
        else:
            linenumbers = ""
        linenumbers += " "
        return linenumbers

    def get_closest_nodes(self, way, compute_mid_node, linenumbers,
                          coord_node_s, new_w_id):
        """
        Checks which nodes are the closest ones to a given node and returns
        the minimum distance of the closest nodes and their coordinates.
        Returns the line numbers of all considered nodes accordingly.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...              "./test_files/merge_test.xml", 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> middle_node, lines = tr_sys.get_closest_nodes(
        ...                 [2, [3, 13, 15, 18, 4]], [], '3 ', [20.0, 50.0], 3)
        >>> assert(middle_node == [(10.0, [20.0, 40.0], [20.0, 50.0])])
        >>> assert(lines == {3: '3 2  2  2  '})
        >>> middle_node, lines = tr_sys.get_closest_nodes(
        ...                       [6, [1, 7, 9, 2]], [], '5 ', [20.0, 60.0], 5)
        >>> assert(middle_node == [(20.0, [20.0, 80.0], [20.0, 60.0])])
        >>> assert(lines == {5: '5 6  6  '})
        """
        get_dist = []
        new_lines_dict = {}
        min_dist = (float('inf'), float('inf'))
        pointer_l = 0
        for node_id_l in way[1]:
            if ((pointer_l == 0) or (pointer_l == len(way[1])-1)):
                pointer_l += 1
                continue
            if not(int(node_id_l) in self._elem.dict_nodes):
                break
            linenumbers += self.get_linenumbers(node_id_l)
            id_l = int(node_id_l)
            coord_node_l = self._elem.dict_nodes[id_l].geometry.coordinates
            euclid_dist = compute_euclid_dist(coord_node_s, coord_node_l)
            get_dist.append((euclid_dist, pointer_l, coord_node_l))
            if euclid_dist < min_dist[0]:
                min_dist = (euclid_dist, coord_node_l, coord_node_s)
            pointer_l += 1
        compute_mid_node.append(min_dist)
        new_lines_dict[new_w_id] = linenumbers
        return compute_mid_node, new_lines_dict

    def add_loop_ways(self):
        """
        Saves all lopes to a dict that consist of a minimum length.
        Shorter loops might consist of siding tracks or be the result
        of searching errors.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> tr_sys._elem.dict_loop_ways = {1: [1, 2, 1]}
        >>> tr_sys.add_loop_ways()
        >>> assert(tr_sys._elem.dict_merged_ways == {})
        >>> tr_sys._elem.dict_loop_ways = {1: [1, 2, 3, 4, 5, 6, 7, 1]}
        >>> assert(tr_sys._elem.dict_loop_ways[1] == [1, 2, 3, 4, 5, 6, 7, 1])
        """
        for way_id in self._elem.dict_loop_ways:
            way = self._elem.dict_loop_ways[way_id]
            if len(way) > 11:  # only add loops with certain length
                self._elem.dict_merged_ways[way_id] = way

    def get_incid_egdes(self):
        """
        Returns a dict with contains the number of incident edges of each
        station node.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> incid_edges = tr_sys.get_incid_egdes()
        >>> assert(len(incid_edges) == 5)
        >>> assert(incid_edges[3168348566019643] == 2)
        >>> assert(incid_edges[5851428106601964] == 1)
        >>> assert(incid_edges[3168373161162228] == 3)
        >>> assert(incid_edges[6533141936533141] == 1)
        >>> assert(incid_edges[6601963656601963] == 1)
        """
        incid_edgs_past_merge = {}
        for way_id in self._elem.dict_merged_ways:
            way = self._elem.dict_merged_ways[way_id]
            first_el = way[0]
            last_el = way[-1]
            if first_el in self._elem.set_new_station_ids:
                if first_el not in incid_edgs_past_merge:
                    incid_edgs_past_merge[first_el] = 1
                else:
                    incid_edgs_past_merge[first_el] += 1

            if last_el in self._elem.set_new_station_ids:
                if last_el not in incid_edgs_past_merge:
                    incid_edgs_past_merge[last_el] = 1
                else:
                    incid_edgs_past_merge[last_el] += 1
        return incid_edgs_past_merge

    def check_ln_of_stations_incid_edges(self, incid_edgs_past_merge):
        """
        Gets the number of incident edges of each station and checks that no
        additional line number is on one of the sides of the stations with two
        incident edges (adds the number in case it is missing). Deletes line
        numbers that are not connected trough stations.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> incid_edges = tr_sys.get_incid_egdes()
        >>> assert(incid_edges[3168348566019643] == 2)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[45899432] == "5")
        >>> assert(tr_sys._elem.dict_merged_ways_ln[383168669] == "2, 4, 5")
        >>> tr_sys.check_ln_of_stations_incid_edges(incid_edges)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[383168669] == "5")
        """
        for way_id_1 in self._elem.dict_merged_ways:
            ln_1 = self._elem.dict_merged_ways_ln[way_id_1]
            if len(ln_1) == 1:
                way = self._elem.dict_merged_ways[way_id_1]
                station_list = [way[0], way[-1]]
                for station in station_list:
                    ln_2, way_id_2 = self.get_incid_ln(way_id_1, station,
                                                       incid_edgs_past_merge)
                    if len(ln_2) > 1:  # take lines from other way instead
                        self._elem.dict_merged_ways_ln[way_id_2] = ln_1
            elif len(ln_1) == 4:  # is string, 2 lines in one string
                way = self._elem.dict_merged_ways[way_id_1]
                station_list = [way[0], way[-1]]
                for station in station_list:
                    ln_2, way_id_2 = self.get_incid_ln(way_id_1, station,
                                                       incid_edgs_past_merge)
                    if len(ln_2) > 4:  # more than 2 lines,
                        # use lines numbers of way with less lines instead
                        self._elem.dict_merged_ways_ln[way_id_2] = ln_1
                    elif len(ln_2) == 1:  # take lines with less numbers
                        self._elem.dict_merged_ways_ln[way_id_1] = ln_2

    def get_incid_ln(self, way_id_1, station, incid_edgs_past_merge):
        """
        Gets the linenumbers of the other line connected with a station having
        only two incident edges.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                "./test_files/freiburg_test.xml",
        ...                7.8245000, 47.997300, 7.8444000, 48.0045000, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> incid_edges = tr_sys.get_incid_egdes()
        >>> ln, way_id = tr_sys.get_incid_ln(
        ...                 383168669, 3168348566019643, {3168348566019643: 2})
        >>> assert(ln == '5')
        >>> assert(way_id == 45899432)
        >>> ln, way_id = tr_sys.get_incid_ln(
        ...                 383168669, 5851428106601964, {5851428106601964: 1})
        >>> assert(ln == "")
        >>> assert(way_id == None)
        """
        if incid_edgs_past_merge[station] == 2:
            for way_id_2 in self._elem.dict_merged_ways:
                if way_id_1 != way_id_2:
                    way_2 = self._elem.dict_merged_ways[way_id_2]
                    if way_2[0] == station or way_2[-1] == station:
                        linenumbers = self._elem.dict_merged_ways_ln[way_id_2]
                        return linenumbers, way_id_2
        else:
            return "", None

    def get_impossible_ln(self, check_station):
        """
        Checks if a line number is incident to a station 3 times
        (very unlikely). Calls helper function to delete the linenumber on the
        right incident edge (by checing on the other surrounding lines).

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                                 "./test_files/linenumber_test.xml",
        ...                                 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> incid_edges = tr_sys.get_incid_egdes()
        >>> assert(incid_edges[5] == 4)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[7] == "1, 2, 3, 4, 5")
        >>> tr_sys.get_impossible_ln([5])
        >>> assert(tr_sys._elem.dict_merged_ways_ln[7] == "1, 3, 4, 5")
        """
        for station in check_station:
            dict_numbers = {}
            for way_id in self._elem.dict_merged_ways.keys():
                way = self._elem.dict_merged_ways[way_id]
                if way[0] == station or way[-1] == station:
                    linenumbers = self._elem.dict_merged_ways_ln[way_id]
                    numbers = re.findall(r"[0-9]+", linenumbers)
                    for num in numbers:
                        if num in dict_numbers:
                            dict_numbers[num][0] += 1
                            dict_numbers[num].append(way_id)
                        else:
                            dict_numbers[num] = [1, way_id]
            del_ln = []
            del_ln_way_ids = []
            for count_number in dict_numbers.keys():
                # same line number is incident 3x to a station, very unlikely
                if dict_numbers[count_number][0] == 3:
                    del_ln.append(int(count_number))
                    del_ln_way_ids.append(dict_numbers[count_number][1:])
            self.check_and_get_ln_of_childway(del_ln, del_ln_way_ids, station)

    def check_and_get_ln_of_childway(self, del_ln, del_ln_way_ids, station):
        """
        Finds the incident edges of stations and checks if all linenumbers
        still exists on the next edge. Deletes wrong linenumbers.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                                 "./test_files/linenumber_test.xml",
        ...                                 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> incid_edges = tr_sys.get_incid_egdes()
        >>> assert(tr_sys._elem.dict_merged_ways_ln[7] == "1, 2, 3, 4, 5")
        >>> tr_sys.check_and_get_ln_of_childway([2], [[2, 4, 7]], 5)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[7] == "1, 3, 4, 5")
        >>> assert(tr_sys._elem.dict_merged_ways_ln[6] == "1")
        >>> tr_sys.check_and_get_ln_of_childway([1], [[6]], 5)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[6] == "1")
        """
        pointer = 0
        acc_node = None
        if len(del_ln) > 0:
            for way_id_2 in del_ln_way_ids[0]:
                way_2 = self._elem.dict_merged_ways[way_id_2]
                if way_2[0] == station:
                    acc_node = way_2[-1]
                elif way_2[-1] == station:
                    acc_node = way_2[0]
                if acc_node:
                    for way_id_3 in self._elem.dict_merged_ways.keys():
                        way_3 = self._elem.dict_merged_ways[way_id_3]
                        if ((way_3[0] == acc_node or way_3[-1] == acc_node)
                           and not (way_id_3 == way_id_2)):
                            ln_child = self._elem.dict_merged_ways_ln[way_id_3]
                            numbers_2 = re.findall(r"[0-9]+", ln_child)
                            if del_ln[pointer] not in numbers_2:
                                # ln is not connected
                                self._elem.dict_merged_ways_ln[
                                                           way_id_2] = ln_child

    def find_non_connecting_linenumbers(self):
        """
        Returns way ids and line numbers which are not connected through
        stations.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                  "./test_files/not_connecting_linenumber_test.xml",
        ...                  0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[4] == "1, 2")
        >>> del_numbers = tr_sys.find_non_connecting_linenumbers()
        >>> assert(del_numbers == {4: {2}})
        """
        del_numbers = {}
        # find all incident line numbers for a way
        dict_incid_ln_per_way = {}
        for way_id_1 in self._elem.dict_merged_ways:
            dict_incid_ln_per_way[way_id_1] = set()
            for way_id_2 in self._elem.dict_merged_ways:
                if way_id_1 != way_id_2:
                    way_1 = self._elem.dict_merged_ways[way_id_1]
                    way_2 = self._elem.dict_merged_ways[way_id_2]
                    # if way_2 is incident
                    if (way_1[0] == way_2[0] or way_1[-1] == way_2[0] or
                       way_1[0] == way_2[-1] or way_1[-1] == way_2[-1]):
                        incid_ln = self._elem.dict_merged_ways_ln[way_id_2]
                        linenumbers = re.findall(r"[0-9]+", incid_ln)
                        for lnr in linenumbers:
                            dict_incid_ln_per_way[way_id_1].add(int(lnr))
            linenumbers_way_1 = self._elem.dict_merged_ways_ln[way_id_1]
            linenumbers = re.findall(r"[0-9]+", linenumbers_way_1)
            for lnr in linenumbers:
                if int(lnr) not in dict_incid_ln_per_way[way_id_1]:
                    if way_id_1 in del_numbers:
                        del_numbers[way_id_1].add(int(lnr))
                    else:
                        del_numbers[way_id_1] = set()
                        del_numbers[way_id_1].add(int(lnr))
        return del_numbers

    def delete_non_connecting_linenumbers(self, del_numbers):
        """
        Keeps all line numbers which are not in del_numbers and deletes the
        others.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                  "./test_files/not_connecting_linenumber_test.xml",
        ...                  0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[4] == "1, 2")
        >>> del_numbers = tr_sys.find_non_connecting_linenumbers()
        >>> tr_sys.delete_non_connecting_linenumbers(del_numbers)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[4] == "1")
        >>> assert(tr_sys._elem.dict_merged_ways_ln[5] == "1")
        >>> del_numbers = {5: {2}}
        >>> tr_sys.delete_non_connecting_linenumbers(del_numbers)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[5] == "1")
        """
        new_numbers = ""
        for way_id in del_numbers:
            numbers_to_delete = del_numbers[way_id]
            old_linenumbers = self._elem.dict_merged_ways_ln[way_id]
            linenumbers = re.findall(r"[0-9]+", old_linenumbers)
            for lnr in linenumbers:
                if int(lnr) not in numbers_to_delete:
                    new_numbers += str(lnr) + ", "
            new_linenumbers = pretty_linenumbers(str(new_numbers))
            self._elem.dict_merged_ways_ln[way_id] = new_linenumbers

    def add_missing_linenumbers(self):
        """
        If a way doesn't hold a line number and all the adjacent ways hold
        the same line numbers the line numbers of the adjacent edges are used
        for the way.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...                  "./test_files/not_connecting_linenumber_test.xml",
        ...                  0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> del_numbers = tr_sys.find_non_connecting_linenumbers()
        >>> tr_sys.delete_non_connecting_linenumbers(del_numbers)
        >>> assert(tr_sys._elem.dict_merged_ways_ln[9] == "")
        >>> tr_sys.add_missing_linenumbers()
        >>> assert(tr_sys._elem.dict_merged_ways_ln[9] == "1")
        """
        for way_id_1 in self._elem.dict_merged_ways:
            lnr = self._elem.dict_merged_ways_ln[way_id_1]
            if len(lnr) == 0:
                way = self._elem.dict_merged_ways[way_id_1]
                start_station = way[0]
                stop_station = way[-1]
                incid_linenumbers = []
                for way_id_2 in self._elem.dict_merged_ways:
                    if way_id_2 != way_id_1:
                        way_2 = self._elem.dict_merged_ways[way_id_2]
                        if (way_2[0] == start_station or
                           way_2[-1] == stop_station or
                           way_2[0] == stop_station or
                           way_2[-1] == start_station):
                            linenumber_2 = self._elem.dict_merged_ways_ln[
                                                                      way_id_2]
                            if len(linenumber_2) > 0:
                                incid_linenumbers.append(linenumber_2)
                if len(incid_linenumbers) > 0:
                    # checks if all elements are equal
                    if all(
                     num == incid_linenumbers[0] for num in incid_linenumbers):
                        self._elem.dict_merged_ways_ln[
                                               way_id_1] = incid_linenumbers[0]

    def get_colour_of_lines(self, linedict):
        """
        Adds a color to a way if there is a color saved to the line
        number of the way.
        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem("", 1, 1, 5, 5, "tram")
        >>> tr_sys = TransportationSystem(tramsys)
        >>> linedict = {'lines': [{'label': "1"}, {'label': "2"}]}
        >>> tr_sys._intermediate_line_colours = {}
        >>> color = tr_sys.get_colour_of_lines(linedict)
        >>> assert(color == {'lines': [{'label': "1"}, {'label': "2"}]})
        >>> tr_sys._intermediate_line_colours = {'1': {'#000'}, '2': {'#111'}}
        >>> color = tr_sys.get_colour_of_lines(linedict)
        >>> assert(color == {'lines': [{'label': '1', 'color': '#000'},
        ...                 {'label': '2', 'color': '#111'}]})
        """
        for elem in linedict['lines']:
            linenumber = elem['label']
            if linenumber in self._intermediate_line_colours:
                for colour in self._intermediate_line_colours[linenumber]:
                    elem['color'] = colour
        return linedict

    def add_ways_to_feature_collection(self):
        """Adds all merged ways to the geojson feature collection.

        >>> from read_xml_file import TrafficSystem
        >>> tramsys = TrafficSystem(
        ...              "./test_files/merge_test.xml", 0, 0, 100, 100, "tram")
        >>> ();tramsys.parse_xml_file();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys = TransportationSystem(tramsys)
        >>> ();tr_sys.merge_tram_stations();() # doctest: +ELLIPSIS
        (...)
        >>> ();tr_sys.find_ways();() # doctest: +ELLIPSIS
        (...)
        >>> tr_sys.add_ways_to_feature_collection()
        >>> assert(len(tr_sys._elem.dict_merged_ways) == 3)
        >>> assert(len(tr_sys._elem.dict_merged_nodes) == 6)
        >>> assert(len(tr_sys._elem.feature_collection) == 9)
        >>> assert(
        ... tr_sys._elem.feature_collection[-1]["geometry"]["coordinates"] == [
        ...            [10.0, 70.0], [20.0, 70.0], [80.0, 70.0], [90.0, 70.0]])
        """
        for way in self._elem.dict_merged_ways:
            node_to_geojson = []
            node_list = self._elem.dict_merged_ways[way]
            way_linenr = ""
            if way in self._elem.dict_merged_ways_ln:
                way_linenr = self._elem.dict_merged_ways_ln[way]
            for node in node_list:
                node_id = int(node)
                if node_id in self._elem.dict_nodes:
                    point = self._elem.dict_nodes[node_id]
                    value = point['geometry']
                    node_to_geojson.append(value)
            my_line = geojson.LineString(node_to_geojson)
            linenr = change_linenumber_format(way_linenr)
            linenrcol = self.get_colour_of_lines(linenr)
            linenrcol["from"] = str(node_list[0])
            linenrcol["to"] = str(node_list[-1])
            new_line = geojson.Feature(geometry=my_line,
                                       id=way,
                                       properties=linenrcol)
            self._elem.feature_collection.append(new_line)


def get_max_dist(station):
    """
    Converts 40 or 80 m in lat/lon. For more information see:
    https://en.wikipedia.org/wiki/Decimal_degrees

    >>> dist = get_max_dist("station")
    >>> assert(dist == 0.000359)
    >>> dist = get_max_dist("rathaus im stühlinger")
    >>> assert(dist == 0.000719)
    """
    if (station == "rathaus im stühlinger" or
       station == "maria von rudloff platz"):
        max_dist = round((80 / 11.132), 2) / 10000
    else:
        max_dist = round((40 / 11.132), 2) / 10000
    return max_dist


def compute_euclid_dist(coord_node_1, coord_node_2):
    """
    Computes the euclid distance of two nodes.

    >>> dist = compute_euclid_dist([2, 2], [2, 2])
    >>> assert(dist == 0.0)
    >>> dist = compute_euclid_dist([2, 2], [2, 3])
    >>> assert(dist == 1.0)
    >>> dist = compute_euclid_dist([3, 9], [3, -1])
    >>> assert(dist == 10.0)
    """
    lon_dist = coord_node_1[0] - coord_node_2[0]
    lat_dist = coord_node_1[1] - coord_node_2[1]
    euclid_dist = math.sqrt((lon_dist**2) + (lat_dist**2))
    return euclid_dist


def compute_middle_node_way(compute_mid_node):
    """
    Computes a middle node out of a list of nodes.

    >>> lon, lat = compute_middle_node_way(
    ...             [(1, [2, 4], [2, 5]), (1, [2, 6], [2, 5])])
    >>> assert(lon == 2.0)
    >>> assert(lat == 5.0)
    >>> lon, lat = compute_middle_node_way(
    ...             [(1, [3, 0], [0, 0]), (1, [9, 0], [0, 0])])
    >>> assert(lon == 4.0)
    >>> assert(lat == 0.0)
    >>> lon, lat = compute_middle_node_way([(1, [-3, -3], [3, 3])])
    >>> assert(lon == 0.0)
    >>> assert(lat == 0.0)
    """
    number_nodes = len(compute_mid_node)
    sum_lon = compute_mid_node[0][2][0]
    sum_lat = compute_mid_node[0][2][1]
    for i in range(number_nodes):
        sum_lon += compute_mid_node[i][1][0]
        sum_lat += compute_mid_node[i][1][1]
    new_lon = sum_lon / (number_nodes + 1)
    new_lat = sum_lat / (number_nodes + 1)
    return new_lon, new_lat


def pretty_linenumbers(ln):
    """ Finds numbers in a string and sorts them.

    >>> ln = pretty_linenumbers("1, 5, abc, 2")
    >>> assert(ln == "1, 2, 5")
    >>> ln = pretty_linenumbers("")
    >>> assert(ln == "")
    """
    numbers = re.findall(r"[0-9]+", ln)
    pretty_numbers = {}
    for num in numbers:
        if int(num) not in pretty_numbers:
            if int(num) != 7:  # 7 is old line of freiburg
                pretty_numbers[int(num)] = int(num)
    lines = sorted(pretty_numbers.keys())
    pretty_lines = ""
    for line in lines:
        pretty_lines += str(line) + ", "
    return pretty_lines[:-2]


def change_linenumber_format(ln):
    """
    Puts each number from a string into a dict.

    >>> form = change_linenumber_format("1, 2")
    >>> assert(form == {'lines': [{'label': "1"}, {'label': "2"}]})
    >>> form = change_linenumber_format("")
    >>> assert(form == {'lines': []})
    """
    jsondict = {}
    jsonlist = []
    numbers = re.findall(r"[0-9]+", ln)
    for num in numbers:
        dictnum = {}
        new_number = str(num)
        dictnum['label'] = new_number
        jsonlist.append(dictnum)
    jsondict['lines'] = jsonlist
    return jsondict


def prepare_ways_for_merging(ways_to_merge, tuple):
    """
    Returns the shortest and longer ways of a dict of ways.

    >>> ways_to_merge = {(3, 8): [[1, [3, 4, 5, 6, 7, 8]], [2, [3, 6, 7, 8]]]}
    >>> tuple = (3, 8)
    >>> s_way, l_ways = prepare_ways_for_merging(ways_to_merge, tuple)
    >>> assert(s_way == [2, [3, 6, 7, 8]])
    >>> assert(l_ways == [[1, [3, 4, 5, 6, 7, 8]]])
    >>> ways_to_merge = {
    ...   (3, 8): [[1, [3, 4, 5, 6, 7, 8]], [2, [3, 7, 8]], [3, [3, 6, 7, 8]]]}
    >>> s_way, l_ways = prepare_ways_for_merging(ways_to_merge, tuple)
    >>> assert(s_way == [2, [3, 7, 8]])
    >>> assert(l_ways == [[1, [3, 4, 5, 6, 7, 8]], [3, [3, 6, 7, 8]]])
    >>> ways_to_merge = {(3, 8): [[1, [3, 8]], [2, [3, 8]]]}
    >>> s_way, l_ways = prepare_ways_for_merging(ways_to_merge, tuple)
    >>> assert(s_way == [1, [3, 8]])
    >>> assert(l_ways == [[2, [3, 8]]])
    """
    len_ways = []
    for way in ways_to_merge[tuple]:
        len_ways.append((len(way[1])))
    len_shortest_way = min(len_ways)
    way_found = False
    longer_ways = []
    for way in ways_to_merge[tuple]:
        if ((len(way[1]) == len_shortest_way) and (not way_found)):
            way_found = True
            shortest_way = way
            continue
        else:
            longer_ways.append(way)
            continue
    return shortest_way, longer_ways


def check_ln_of_stations_with_four_incid_edges(incid_edges):
    """
    Returns a list of all stations with 4 incid edges.

    >>> incid_edges = {10: 2, 11: 4, 12: 4, 13: 1}
    >>> check = check_ln_of_stations_with_four_incid_edges(incid_edges)
    >>> assert(check == [11, 12])
    >>> incid_edges = {}
    >>> check = check_ln_of_stations_with_four_incid_edges(incid_edges)
    >>> assert(check == [])
    """
    check_station = []
    for station in incid_edges:
        if incid_edges[station] == 4:
            check_station.append(station)
    return check_station


def get_timestamp():
    """
    Returns timestamp used for Logging.
    """
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
