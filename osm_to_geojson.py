"""
Bachelor Project
Chair for Algorithm and Data Structures
Albert-Ludwigs-University Freiburg
Supervisor: Patrick Brosi

Author: Katharina Matulla <katharina.matulla@gmail.com>
"""
import datetime
from compute_transfer_network import TransportationSystem
from read_xml_file import TrafficSystem
from write_geojson_file import GeojsonDump


def get_timestamp():
    """
    Returns timestamp used for Logging.
    """
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


if __name__ == "__main__":
    """
    Main function to parse the arguments, extract public transport data from
    an osm(xml)-file, adjust the data and save the data in a geojson-file.
    """
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--min_lon', type=float, help='Minimum longitude',
                        required=True)
    parser.add_argument('--min_lat', type=float, help='Minimum latitude',
                        required=True)
    parser.add_argument('--max_lon', type=float, help='Maximum longitude',
                        required=True)
    parser.add_argument('--max_lat', type=float, help='Maximum latitude',
                        required=True)
    parser.add_argument('--xml_file', help='XML file to parse',
                        required=True)
    parser.add_argument('--transport_vehicle',
                        help='The transport vehicle: tram or subway',
                        required=True)

    args = parser.parse_args()

    traffic_system = TrafficSystem(
                      args.xml_file,
                      args.min_lon,
                      args.min_lat,
                      args.max_lon,
                      args.max_lat,
                      transport_vehicle=args.transport_vehicle
                 )
    t = get_timestamp()
    print("["+t+"] Parsing xml file...")

    traffic_system.parse_xml_file()

    t = get_timestamp()
    print("["+t+"] Parsing complete.")

    t = get_timestamp()
    print("["+t+"] Computing transfer network...")

    transportation_system = TransportationSystem(traffic_system)
    transportation_system.process()

    t = get_timestamp()
    print("["+t+"] Computing complete.")

    t = get_timestamp()
    print("["+t+"] Saving geoJSON file...")
    geojson_dump = GeojsonDump(args.xml_file,
                               transportation_system._elem.feature_collection)
    created_filename = geojson_dump._now

    t = get_timestamp()
    print("["+t+"] Saved file " + created_filename + str(args.xml_file[0:-4]) +
          ".geojson in the output folder.")
