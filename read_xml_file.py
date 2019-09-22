"""
Bachelor Project
Chair for Algorithm and Data Structures
Albert-Ludwigs-University Freiburg
Supervisor: Patrick Brosi

Author: Katharina Matulla <katharina.matulla@gmail.com>
"""
import datetime
import re
from dataclasses import dataclass, field
from lxml import etree as etree


@dataclass
class NeededElements:
    dict_stations_merged: dict = field(default_factory=dict)
    dict_needed_nodes_in_way: dict = field(default_factory=dict)
    dict_relations_nodes: dict = field(default_factory=dict)
    dict_relations_ways: dict = field(default_factory=dict)
    dict_contruction_nodes: dict = field(default_factory=dict)
    dict_needed_nodes: dict = field(default_factory=dict)
    dict_needed_ways: dict = field(default_factory=dict)
    dict_node_switches: dict = field(default_factory=dict)
    dict_colour_line: dict = field(default_factory=dict)


class TrafficSystem(object):
    """
    Class to get relevant information system of a given transportation system
    from a given xml-file of osm.
    """
    def __init__(
        self,
        xml_file,
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        transport_vehicle,
    ):
        """
        >>> tramsys = TrafficSystem(
        ...                   "./test_files/tram_test.xml", 1, 1, 1, 1, "tram")
        >>> assert(tramsys.transport_vehicle == 'tram')
        >>> assert(tramsys._xml_file == "./test_files/tram_test.xml")
        >>> assert(tramsys.min_lon == 1)
        """
        self._xml_file = xml_file
        self.min_lon = min_lon
        self.min_lat = min_lat
        self.max_lon = max_lon
        self.max_lat = max_lat
        self.transport_vehicle = transport_vehicle

        self._elem = NeededElements()

    def parse_xml_file(self):
        self._validate_input()

        t = get_timestamp()
        print("["+t+"]   (start parsing ways in xml file)")
        self._find_ways()

        t = get_timestamp()
        print("["+t+"]   (start parsing relations in xml file)")
        self._find_relations()

        t = get_timestamp()
        print("["+t+"]   (start parsing stations in xml file)")
        self._find_stations()

    def _validate_input(self):
        bounds = self.get_bounding_box_of_file()
        self.check_bounding_box_of_file(bounds[0], bounds[1], bounds[2],
                                        bounds[3])

    def _find_ways(self):
        self.find_relevant_ways_in_file()
        self.find_nodes_of_ways_in_file()

    def _find_relations(self):
        self.save_relations_of_tram()

    def _find_stations(self):
        self.find_stations_in_file()

    @property
    def stations_merged(self):
        return self._elem.dict_stations_merged

    @property
    def node_switches(self):
        return self._elem.dict_node_switches

    @property
    def needed_nodes_in_way(self):
        return self._elem.dict_needed_nodes_in_way

    @property
    def ways(self):
        return self._elem.dict_needed_ways

    @property
    def relations_nodes(self):
        return self._elem.dict_relations_nodes

    @property
    def relations_ways(self):
        return self._elem.dict_relations_ways

    @property
    def line_colours(self):
        return self._elem.dict_colour_line

    def get_bounding_box_of_file(self):
        """
        Checks if the desired bounding box is contained in the xml-file
        and returns the bounds.
        Quits if not the case.

        >>> tramsys = TrafficSystem(
        ...         "./test_files/bounding_box_1_test.xml", 1, 1, 1, 1, "tram")
        >>> ();box = tramsys.get_bounding_box_of_file();() # doctest: +ELLIPSIS
        (...)
        >>> assert(box == ('5', '5', '25', '25'))
        >>> tramsys = TrafficSystem(
        ...         "./test_files/bounding_box_2_test.xml", 1, 1, 1, 1, "tram")
        >>> ();box = tramsys.get_bounding_box_of_file();() # doctest: +ELLIPSIS
        (...)
        >>> assert(box == ('-25', '-25', '-5', '-5'))
        """
        for event, elem in etree.iterparse(self._xml_file, events=('start',
                                                                   'end')):
            if (event == 'start'):
                if (elem.tag == 'bounds'):
                    bound_min_lon = elem.attrib['minlon']
                    bound_min_lat = elem.attrib['minlat']
                    bound_max_lon = elem.attrib['maxlon']
                    bound_max_lat = elem.attrib['maxlat']
                    t = get_timestamp()
                    print("["+t+"]   (bounding box of file: "
                          + str(bound_min_lon) + " " + str(bound_min_lat) + " "
                          + str(bound_max_lon) + " "
                          + str(bound_max_lat) + ")")
                    break
            clear_element(elem)
        clear_element(elem)
        return bound_min_lon, bound_min_lat, bound_max_lon, bound_max_lat

    def check_bounding_box_of_file(self, bound_min_lon, bound_min_lat,
                                   bound_max_lon, bound_max_lat):
        """
        Checks if osm entity is within the given bounding box.

        >>> tramsys = TrafficSystem(
        ...       "./test_files/bounding_box_1_test.xml", 5, 5, 25, 25, "tram")
        >>> ();tramsys.check_bounding_box_of_file(5,
        ...                                  5, 25, 25);() # doctest: +ELLIPSIS
        (...)
        >>> tramsys = TrafficSystem(
        ...   "./test_files/bounding_box_2_test.xml", -25, -25, -5, -5, "tram")
        >>> ();tramsys.check_bounding_box_of_file(-25,
        ...                                -25, -5, -5);() # doctest: +ELLIPSIS
        (...)
        >>> tramsys = TrafficSystem(
        ... "./test_files/bounding_box_2_test.xml", -20.0, -25, -5, -5, "tram")
        >>> ();tramsys.check_bounding_box_of_file(-25.000,
        ...                                -25, -5, -5);() # doctest: +ELLIPSIS
        (...)
        >>> tramsys = TrafficSystem(
        ...         "./test_files/bounding_box_2_test.xml", 1, 1, 1, 1, "tram")
        >>> tramsys.check_bounding_box_of_file(0, 0, 0, 0)
        Traceback (most recent call last):
        SystemExit: None
        """
        if (((float(bound_min_lon)) <= (self.min_lon)) &
           ((float(bound_min_lon)) <= (self.max_lon)) &
           ((float(bound_min_lat)) <= (self.min_lat)) &
           ((float(bound_min_lat)) <= (self.max_lat)) &
           ((float(bound_max_lon)) >= (self.max_lon)) &
           ((float(bound_max_lon)) >= (self.min_lon)) &
           ((float(bound_max_lat)) >= (self.max_lat)) &
           ((float(bound_max_lat)) >= (self.min_lat))):
            t = get_timestamp()
            print("["+t+"]   (data within bounding box)")
        else:   # not in bb
            t = get_timestamp()
            print("["+t+"]   (data not within bounding box)")
            t = get_timestamp()
            print("["+t+"]   (exiting)")
            exit()

    def find_relevant_ways_in_file(self):
        """
        Iterates trough the xml file and finds ways. If a way is found it
        calls helper functions to process the information.

        >>> tramsys = TrafficSystem(
        ...                   "./test_files/tram_test.xml", 5, 5, 5, 5, "tram")
        >>> tramsys.find_relevant_ways_in_file()
        >>> assert (list(tramsys._elem.dict_needed_ways.keys())[0] == 1234)
        >>> assert (len(list(tramsys._elem.dict_needed_ways.keys())) == 1)
        """
        for event, elem in etree.iterparse(self._xml_file, events=('start',
                                                                   'end')):
            if (elem.tag == 'node'):
                clear_element(elem)
                continue
            elif (elem.tag == 'relation'):
                clear_element(elem)
                break
            elif (event == 'start' and elem.tag == 'way'):
                take_way = self.check_take_way(elem)
                if take_way:
                    children = elem.findall('tag')
                    is_used_way = check_if_used_way(children)
                    if is_used_way:

                        way_id = int(elem.attrib['id'])
                        self.get_nodes_of_way(elem, way_id)
                clear_element(elem)
                continue
            elif (event == 'end' and elem.tag == 'way'):
                clear_element(elem)
        clear_element(elem)

    def check_take_way(self, elem):
        """
        Returns true if a way is a tram (or subway) way. False otherwise.

        >>> tramsys = TrafficSystem(
        ...                   "./test_files/tram_test.xml", 1, 1, 1, 1, "tram")
        >>> for event, elem in etree.iterparse(tramsys._xml_file, events=(
        ...                                                   'start', 'end')):
        ...     if (event == 'start' and elem.tag == 'way'):
        ...         take_way = tramsys.check_take_way(elem)
        ...         break
        >>> assert (take_way == True)
        >>> for event, elem in etree.iterparse(tramsys._xml_file, events=(
        ...                                                   'start', 'end')):
        ...     if (event == 'start' and elem.tag == 'way'):
        ...         if (int(elem.attrib['id']) == 2):
        ...             take_way = tramsys.check_take_way(elem)
        ...             break
        >>> assert (take_way == False)
        """
        children = elem.findall('tag')
        is_tram_way = False
        is_subway_way = False
        if (self.transport_vehicle == "tram"):
            is_tram_way = check_if_tram_way(children)
        elif (self.transport_vehicle == "subway"):
            is_subway_way = check_if_subway_way(children)
        if (is_tram_way or is_subway_way):
            return True
        else:
            return False

    def get_nodes_of_way(self, elem, way_id):
        """
        Gets all nodes and tags of an element and saves the node ids and tags
        in a dict.

        >>> tramsys = TrafficSystem(
        ...                   "./test_files/tram_test.xml", 5, 5, 5, 5, "tram")
        >>> tramsys.find_relevant_ways_in_file()
        >>> assert(list(tramsys._elem.dict_needed_nodes.keys())[0] == 1)
        >>> assert(list(tramsys._elem.dict_needed_nodes.keys())[1] == 2)
        >>> assert(list(tramsys._elem.dict_needed_nodes.keys())[2] == 3)
        >>> assert(len(list(tramsys._elem.dict_needed_nodes.keys())) == 3)
        """
        relevant_nodes = elem.findall('nd')
        tags = elem.findall('tag')
        self._elem.dict_needed_ways[way_id] = [relevant_nodes, tags]
        for node in relevant_nodes:
            node_id = int(node.attrib['ref'])
            self._elem.dict_needed_nodes[node_id] = True
            clear_element(elem)
        clear_element(elem)

    def find_nodes_of_ways_in_file(self):
        """
        Iterates through the xml-file and saves the needed nodes to a dict.

        >>> tramsys = TrafficSystem(
        ...                   "./test_files/tram_test.xml", 5, 5, 5, 5, "tram")
        >>> tramsys.find_relevant_ways_in_file()
        >>> tramsys.find_nodes_of_ways_in_file()
        >>> assert(list(tramsys._elem.dict_needed_nodes_in_way.keys())[0] == 1)
        >>> assert(list(tramsys._elem.dict_needed_nodes_in_way.keys())[1] == 2)
        >>> assert(list(tramsys._elem.dict_needed_nodes_in_way.keys())[2] == 3)
        >>> assert(tramsys._elem.dict_needed_nodes_in_way[1] == ['6', '5'])
        >>> assert(tramsys._elem.dict_node_switches[2] == True)
        """
        for event, elem in etree.iterparse(self._xml_file, events=('start',
                                                                   'end')):
            if (event == 'start'):
                if not(elem.tag == 'node'):
                    clear_element(elem)
                    continue
                elif (elem.tag == 'node'):
                    nd_id = int(elem.attrib['id'])
                    if nd_id in self._elem.dict_needed_nodes:
                        lon = elem.attrib['lon']
                        lat = elem.attrib['lat']
                        node_switch = check_if_switch(elem)
                        if node_switch:
                            self._elem.dict_node_switches[nd_id] = True
                        self._elem.dict_needed_nodes_in_way[nd_id] = [lon, lat]
                        clear_element(elem)
                        continue
                elif (elem.tag == 'way'):
                    clear_element(elem)
                    break
            if (event == 'end'):
                clear_element(elem)

    def save_relations_of_tram(self):
        """
        Iterates through the xml-file and calls helper functions if a relation
        is found.

        >>> tramsys = TrafficSystem(
        ...               "./test_files/relation_test.xml", 5, 5, 5, 5, "tram")
        >>> tramsys.save_relations_of_tram()
        >>> assert(list(tramsys._elem.dict_relations_ways.keys())[0] == 5)
        >>> assert(list(tramsys._elem.dict_relations_ways.keys())[1] == 6)
        >>> assert(tramsys._elem.dict_relations_ways[5] == '1')
        >>> assert(list(tramsys._elem.dict_relations_nodes.keys())[0] == 7)
        >>> assert(list(tramsys._elem.dict_relations_nodes.keys())[1] == 8)
        >>> assert(tramsys._elem.dict_relations_nodes[8] == '1')
        """
        for event, elem in etree.iterparse(self._xml_file, events=('start',
                                                                   'end')):
            if (event == 'start'):
                if not (elem.tag == 'relation'):
                    clear_element(elem)
                    continue
                elif (elem.tag == 'relation'):
                    self.check_relation(elem)
                    clear_element(elem)
                    continue
            if (event == 'end'):
                clear_element(elem)

    def check_relation(self, elem):
        """
        Saves the line-references of nodes and ways contained in relations
        (which are referring to the transport vehicle) in dicts.

        >>> tramsys = TrafficSystem(
        ...               "./test_files/relation_test.xml", 5, 5, 5, 5, "tram")
        >>> tramsys.save_relations_of_tram()
        >>> assert (tramsys.transport_vehicle == 'tram')
        >>> assert(list(tramsys._elem.dict_relations_ways.keys())[0] == 5)
        >>> assert(list(tramsys._elem.dict_relations_ways.keys())[1] == 6)
        >>> assert(tramsys._elem.dict_relations_ways[5] == '1')
        >>> assert(list(tramsys._elem.dict_relations_nodes.keys())[0] == 7)
        >>> assert(list(tramsys._elem.dict_relations_nodes.keys())[1] == 8)
        >>> assert(tramsys._elem.dict_relations_nodes[8] == '1')
        """
        tags = elem.findall('tag')
        for tag in tags:
            if ('v' in tag.attrib):
                if self.transport_vehicle == "tram":
                    if (tag.attrib['v'] == 'tram' and
                       tag.attrib['k'] != 'historic' and
                       tag.attrib['k'] != 'historic:railway'):
                        self.take_relation(elem)
                        break
                elif self.transport_vehicle == "subway":
                    if (tag.attrib['k'] == 'route' and
                       tag.attrib['v'] == 'subway'):
                        self.take_relation(elem)
                        break

    def take_relation(self, elem):
        """
        Checks if the relation holds a line number and if so, saves the number
        to the nodes and ways of the relation in a dict.

        >>> tramsys = TrafficSystem(
        ...               "./test_files/relation_test.xml", 5, 5, 5, 5, "tram")
        >>> tramsys.save_relations_of_tram()
        >>> assert(list(tramsys._elem.dict_relations_ways.keys())[0] == 5)
        >>> assert(list(tramsys._elem.dict_relations_ways.keys())[1] == 6)
        >>> assert(tramsys._elem.dict_relations_ways[5] == '1')
        >>> assert(list(tramsys._elem.dict_relations_nodes.keys())[0] == 7)
        >>> assert(list(tramsys._elem.dict_relations_nodes.keys())[1] == 8)
        >>> assert(tramsys._elem.dict_relations_nodes[8] == '1')
        """
        linenumber_found = False
        colour_found = False
        tags = elem.findall('tag')
        for tag in tags:
            if ('k' in tag.attrib):
                if (tag.attrib['k'] == 'ref'):
                    linenr = tag.attrib['v']
                    linenumber_found = True
                if (tag.attrib['k'] == 'colour'):
                    colour = tag.attrib['v']
                    colour_found = True
        if linenumber_found:
            members = elem.findall('member')
            for member in members:
                mem_id = int(member.attrib['ref'])
                if (member.attrib['type'] == 'way'):
                    if (mem_id in self._elem.dict_relations_ways):
                        self._elem.dict_relations_ways[mem_id] += ", "
                        self._elem.dict_relations_ways[mem_id] += linenr
                    else:
                        self._elem.dict_relations_ways[mem_id] = linenr
                    # save colour to way if there is a colour, if more than one
                    # colour is found for a line only the last one is saved
                    if colour_found:
                        self._elem.dict_colour_line[linenr] = set()
                        self._elem.dict_colour_line[linenr].add(colour)
                elif (member.attrib['type'] == 'node'):
                    if (mem_id in self._elem.dict_relations_nodes):
                        self._elem.dict_relations_nodes[mem_id] += ", "
                        self._elem.dict_relations_nodes[mem_id] += linenr
                    else:
                        self._elem.dict_relations_nodes[mem_id] = linenr

    def find_stations_in_file(self):
        """
        Parses trough the xml file and looks for nodes. Calls helper
        function to process the node.

        >>> tramsys = TrafficSystem(
        ...             "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
        >>> tramsys.find_stations_in_file()
        >>> assert(list(
        ...       tramsys._elem.dict_stations_merged.keys())[0] == 'holzmarkt')
        >>> assert(list(
        ...    tramsys._elem.dict_stations_merged.keys())[1] == 'hauptbahnhof')
        >>> assert(tramsys._elem.dict_stations_merged['holzmarkt'] ==
        ...                                     [[1, 2.0, 2.0], [2, 4.0, 4.0]])
        >>> assert(tramsys._elem.dict_stations_merged['hauptbahnhof'] ==
        ...                                                    [[4, 5.0, 5.0]])
        """
        for event, elem in etree.iterparse(self._xml_file, events=('start',
                                                                   'end')):
            if (event == 'end' and elem.tag == 'node'):
                self.process_node(elem)
                clear_element(elem)
            elif (elem.tag == 'way'):
                clear_element(elem)
                break
        clear_element(elem)

    def process_node(self, elem):
        """
        Checks if a node belongs to the transport vehicle and is a station
        node. Checks whether station is still active, not under construction
        and within the given bounding box. If so, calls helper function to save
        the station node to a dict.

        >>> tramsys = TrafficSystem(
        ...             "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
        >>> tramsys.find_stations_in_file()
        >>> assert(list(
        ...  tramsys._elem.dict_contruction_nodes.keys())[0] == 'hauptbahnhof')
        >>> assert(
        ...       tramsys._elem.dict_contruction_nodes['hauptbahnhof'] == True)
        """
        children = elem.getchildren()
        take_node = check_for_station(children, self.transport_vehicle)
        constr_tag = False
        if take_node:
            constr_tag = check_if_construction_tag(children)
        if constr_tag:  # not all stations have construction tag
            take_node = False
            for child in children:
                if child.attrib['k'] == 'name':
                    station = child.attrib['v']
                    station = simplify_station_name(station)
                    self._elem.dict_contruction_nodes[station] = True
                    break
        if take_node and not constr_tag:
            lon = float(elem.attrib['lon'])
            lat = float(elem.attrib['lat'])
            if (lat >= self.min_lat and lat <= self.max_lat and
               lon >= self.min_lon and lon <= self.max_lon):
                self.take_station(elem, children, lon, lat)
                clear_element(elem)

    def take_station(self, elem, children, lon, lat):
        """
        Adds a station node to a dict (station name is key)
        or appends node for later merging if station is already in dict.

        >>> tramsys = TrafficSystem(
        ...             "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
        >>> tramsys.find_stations_in_file()
        >>> assert(list(
        ...       tramsys._elem.dict_stations_merged.keys())[0] == 'holzmarkt')
        >>> assert(list(
        ...    tramsys._elem.dict_stations_merged.keys())[1] == 'hauptbahnhof')
        >>> assert(tramsys._elem.dict_stations_merged['holzmarkt'] ==
        ...                                     [[1, 2.0, 2.0], [2, 4.0, 4.0]])
        >>> assert(tramsys._elem.dict_stations_merged['hauptbahnhof'] ==
        ...                                                    [[4, 5.0, 5.0]])
        """
        node_id = int(elem.attrib['id'])
        for child in children:
            if child.attrib['k'] == 'name':
                station = child.attrib['v']  # name of station

                station = simplify_station_name(station)
                if station not in self._elem.dict_contruction_nodes:
                    new_st = [node_id, lon, lat]
                    if station not in self._elem.dict_stations_merged:
                        self._elem.dict_stations_merged[station] = [new_st]
                    else:
                        self._elem.dict_stations_merged[station].append(new_st)


def check_if_tram_way(children):
    """
    Returns true if a way is a tram way and not a side way. False otherwise.

    >>> tramsys = TrafficSystem(
    ...                       "./test_files/tram_test.xml", 1, 1, 1, 1, "tram")
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...     if (event == 'start' and elem.tag == 'way'):
    ...         children = elem.findall('tag')
    ...         break
    >>> tram_way = check_if_tram_way(children)
    >>> assert (tram_way == True)
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...     if (event == 'start' and elem.tag == 'way'):
    ...         if (int(elem.attrib['id']) == 2):
    ...             children = elem.findall('tag')
    ...             break
    >>> tram_way = check_if_tram_way(children)
    >>> assert (tram_way == False)
    """
    tram_way = False
    for child in children:  # take way, works for freiburg
        if (child.attrib['v'] == 'tram' or
           child.attrib['k'] == 'tram' or
           child.attrib['v'] == 'light_rail'):
            tram_way = True
            break
    if tram_way:  # don't use side tracks
        for child in children:
            if (child.attrib['k'] == 'service' and
               child.attrib['v'] == "siding"):
                tram_way = False
                break
    return tram_way


def check_if_subway_way(children):
    """
    Returns true if a way is a subway way. False otherwise.

    >>> tramsys = TrafficSystem(
    ...                   "./test_files/subway_test.xml", 1, 1, 1, 1, "subway")
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...     if (event == 'start' and elem.tag == 'way'):
    ...         children = elem.findall('tag')
    ...         break
    >>> subway_way = check_if_subway_way(children)
    >>> assert (subway_way == True)
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...     if (event == 'start' and elem.tag == 'way'):
    ...         if (int(elem.attrib['id']) == 2):
    ...             children = elem.findall('tag')
    ...             break
    >>> subway_way = check_if_subway_way(children)
    >>> assert (subway_way == False)
    """
    subway_way = False
    for child in children:  # take way, works for freiburg
        if (child.attrib['k'] == 'railway' and
           child.attrib['v'] == 'subway'):
            subway_way = True
            break
    return subway_way


def check_if_used_way(children):
    """
    Returns true if a way is not historic or under construction. False
    otherwise.

    >>> tramsys = TrafficSystem(
    ...                       "./test_files/tram_test.xml", 1, 1, 1, 1, "tram")
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...     if (event == 'start' and elem.tag == 'way'):
    ...         children = elem.findall('tag')
    ...         break
    >>> used_way = check_if_used_way(children)
    >>> assert (used_way == True)
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...     if (event == 'start' and elem.tag == 'way'):
    ...         if (int(elem.attrib['id']) == 3):
    ...             children = elem.findall('tag')
    ...             break
    >>> used_way = check_if_used_way(children)
    >>> assert (used_way == False)
    """
    used_way = True
    for child in children:
        if (child.attrib['k'] == 'historic' or
           child.attrib['k'] == 'historic:railway' or
           child.attrib['k'] == 'construction' or
           child.attrib['v'] == 'construction'):
            used_way = False
            break
    return used_way


def check_if_switch(elem):
    """
    Returns true if a way contains a switch-tag. False otherwise.

    >>> tramsys = TrafficSystem(
    ...                       "./test_files/tram_test.xml", 1, 1, 1, 1, "tram")
    >>> tramsys.find_relevant_ways_in_file()
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...    if (elem.tag == 'node'):
    ...        node_id = int(elem.attrib['id'])
    ...        if (node_id == 1):
    ...            if (node_id in tramsys._elem.dict_needed_nodes):
    ...                switch = check_if_switch(elem)
    ...                break
    >>> assert (switch == False)
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...    if (elem.tag == 'node'):
    ...        node_id = int(elem.attrib['id'])
    ...        if (node_id == 2):
    ...            if (node_id in tramsys._elem.dict_needed_nodes):
    ...                switch = check_if_switch(elem)
    ...                break
    >>> assert (switch == True)
    """
    node_switch = False
    node_tags = elem.getchildren()
    for tag in node_tags:
        if (tag.attrib['k'] == 'railway:switch' and tag.attrib['v'] == 'no'):
            node_switch = True
            break
    return node_switch


def check_for_station(children, transport_vehicle):
    """
    Returns true if a node is station of the given transport vehicle. False
    otherwise.

    >>> tramsys = TrafficSystem(
    ...                 "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...    if (event == 'end' and elem.tag == 'node'):
    ...        children = elem.getchildren()
    ...        take_nd = check_for_station(children, tramsys.transport_vehicle)
    ...        break
    >>> assert (take_nd == True)
    >>> subwaysys = TrafficSystem(
    ...                 "./test_files/stations_test.xml", 5, 5, 5, 5, "subway")
    >>> for event, elem in etree.iterparse(subwaysys._xml_file, events=(
    ...                                                       'start', 'end')):
    ...    if (event == 'end' and elem.tag == 'node'):
    ...        childs = elem.getchildren()
    ...        take_nd = check_for_station(childs, subwaysys.transport_vehicle)
    ...        break
    >>> assert (take_nd == False)
    """
    take_node = False
    for child in children:
        if ('k' in child.attrib) or ('v' in child.attrib):
            if (transport_vehicle == "tram"):
                if ((child.attrib['k'] == 'tram') or
                   (child.attrib['v'] == 'tram_stop')):
                    take_node = True
                    break
            elif (transport_vehicle == "subway"):
                if ((child.attrib['k'] == 'station' and
                   child.attrib['v'] == 'subway') or
                   (child.attrib['k'] == 'subway') and
                   (child.attrib['v'] == 'yes')):
                    take_node = True
                    break
    return take_node


def check_if_construction_tag(children):
    """
    Returns true if a node holds a construction tag. False otherwise.

    >>> tramsys = TrafficSystem(
    ...                 "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...    if (event == 'end' and elem.tag == 'node'):
    ...        childs = elem.getchildren()
    ...        take_node = check_for_station(childs, tramsys.transport_vehicle)
    ...        constr_tag = False
    ...        if take_node:
    ...            constr_tag = check_if_construction_tag(childs)
    ...            break
    >>> assert (constr_tag == False)
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...    if (event == 'end' and elem.tag == 'node'):
    ...        childs = elem.getchildren()
    ...        take_node = check_for_station(childs, tramsys.transport_vehicle)
    ...        constr_tag = False
    ...        if take_node:
    ...            constr_tag  = check_if_construction_tag(childs)
    >>> assert (constr_tag == True)
    """
    construction_tag = False
    for child in children:
        if ('k' in child.attrib):
            if (child.attrib['k'] == 'construction' or
               child.attrib['k'] == 'historic' or
               child.attrib['k'] == 'historic:railway'):
                construction_tag = True
                break
    return construction_tag


def clear_element(elem):
    """
    Clears all element and their parents (to release memory).

    >>> tramsys = TrafficSystem(
    ...                 "./test_files/stations_test.xml", 1, 1, 10, 10, "tram")
    >>> for event, elem in etree.iterparse(tramsys._xml_file, events=('start',
    ...                                                               'end')):
    ...    if (elem.tag == 'node'):
    ...        break
    >>> assert (elem.getprevious() != None)
    >>> clear_element(elem)
    >>> assert (elem.getprevious() == None)
    """
    elem.clear()
    while elem.getprevious() is not None:
        del elem.getparent()[0]


def simplify_station_name(station_name):
    """
    Returns a simplified station name (lowercases, splits commas).

    >>> simplify_station_name("")
    ''
    >>> simplify_station_name("spam")
    'spam'
    >>> simplify_station_name("ÜÄÖß0123-_ üäös")
    'üäöß üäös'
    >>> simplify_station_name("siegesdenkmal, demnächst")
    'siegesdenkmal'
    """
    station, sep, tail = station_name.partition(',')
    simple_name = re.sub('[^a-z,ä,ö,ü,Ä,Ö,Ü,ß]+', ' ', station.lower())
    return simple_name


def get_timestamp():
    """
    Returns timestamp used for Logging.
    """
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
