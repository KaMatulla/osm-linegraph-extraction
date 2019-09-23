Last Updated: 23 September 2019

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

The following does not work on GitHub yet.
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

