Last Updated: 09 April 2019

Purpose of this Tool
--------------------
This tool extracts public transport data (lines and stations) of a specified
public transport system (tram or subway) from OpenStreetMap-files within a defined region.

It adjusts the extracted data, so that at the end only one line runs between a set of two stations
and saves this result in a geoJSON file.

The adjustments include:
	- merging all nodes of one station into one middle station,
	- connecting those new merged stations with the ways and
	- merging the ways (and accordingly the line numbers of the transportation system) connecting the stations.


Folder Structure
----------------

The following contents should be available in the svn-folder (and in the docker container):

1.) The python-files (python version 3.6) to produce the results (Extraction of Public Transport Linegraphs from OpenStreetMap):
	- osm_to_geojson.py (contains the main function, from which the functions of the other files are called)
	- read_xml_file.py
	- compute_transfer_network.py
	- write_geojson_file.py

2.) A Makefile to get further information (e. g. the statements also mentioned below).

3.) A bash startup script to print a welcome message in the docker shell.

4.) A file requirements.txt which lists all needed python requirements to run the program.

5.) A folder "test_files", which contains the constructed test files for the unittests.

6.) A folder "geojson_results", which contains the .geojson-file results of the project.

7.) An (empty) folder "output", in which new results will get saved if the program will be executed successfully in the docker container.

8.) A folder "www", which contains all files for the web page.

Only in the docker container (not the svn-folder) should further be the follwing xml(osm)-files in the folder data:
(included from the folder katharina-matulla on the nfs)
	- freiburg_oct_2018.xml (only for this file the output will be without any errors like false line numbers)
	- freiburg_jan_2019.xml
	- stuttgart.xml
	- munich.xml
	- chicago.xml
	- paris.xml
	- london.xml
	- freiburg-regbez-latest.osm

If you want to reproduce the results, you can call the python-program with the following statements:

Freiburg October 2018
python3 osm_to_geojson.py --min_lon 7.5 --min_lat 47.78 --max_lon 8.2400002 --max_lat 48.31 --transport_vehicle tram --xml_file /data/freiburg_oct_2018.xml

Freiburg January 2019
python3 osm_to_geojson.py --min_lon 7.7069000 --min_lat 47.9467000 --max_lon 8.0262000 --max_lat 48.0620000 --transport_vehicle tram --xml_file /data/freiburg_jan_2019.xml

Chicago
python3 osm_to_geojson.py --min_lon -87.9881000 --min_lat 41.6730000 --max_lon -86.7110000 --max_lat 42.1859000 --transport_vehicle subway --xml_file /data/chicago.xml

Munich
python3 osm_to_geojson.py --min_lon 11.2624000 --min_lat 48.0147000 --max_lon 11.9009000 --max_lat 48.2447000 --transport_vehicle subway --xml_file /data/munich.xml

Paris
python3 osm_to_geojson.py --min_lon 2.2083000 --min_lat 48.8035000 --max_lon 2.5275000 --max_lat 48.9169000 --transport_vehicle subway --xml_file /data/paris.xml

Stuttgart
python3 osm_to_geojson.py --min_lon 8.9243000 --min_lat 48.6521000 --max_lon 9.5629000 --max_lat 48.8793000 --transport_vehicle tram --xml_file /data/stuttgart.xml

London
python3 osm_to_geojson.py --min_lon -0.2365000 --min_lat 51.4479000 --max_lon 0.0827000 --max_lat 51.5552000 --transport_vehicle subway --xml_file /data/london.xml

Freiburg "freiburg-regbez-latest"
python3 osm_to_geojson.py --min_lon 7.25319 --min_lat 47.29909 --max_lon 9.246965 --max_lat 48.75152 --transport_vehicle tram --xml_file freiburg-regbez-latest.osm
