TEST_CMD = python3 -m doctest
CHECKSTYLE_CMD = flake8


help:
	@echo ""
	@echo "This tool extracts public transport data (lines and stations) of a specified"
	@echo "public transport system (tram or subway) from OpenStreetMap-files within a defined region."
	@echo "It adjusts the extracted data, so that at the end only one line runs between a set of two stations"
	@echo "and saves this result in a geoJSON file."
	@echo "The adjustments include:"
	@echo    "- merging all nodes of one station into one middle station,"
	@echo    "- connecting those new merged stations with the ways,"
	@echo    "- merging the ways (and accordingly the line numbers of the transportation system) connecting the stations."
	@echo ""
	@echo "New results will be saved in the /output folder."
	@echo "Running the program will take ~5-20 minutes and needs ~20-30 MB."
	@echo ""
	@echo "<make all> will run tests, checkstyle and clean for all python files in this folder"
	@echo "<make usage> will print out the usage"
	@echo ""
	@echo "To reproduce the results for a city, type:"
	@echo    "<make freiburg-oct-2018>"
	@echo    "<make freiburg-jan-2019>"
	@echo    "<make chicago>"
	@echo    "<make munich>"
	@echo    "<make paris>"
	@echo    "<make stuttgart>"
	@echo    "<make london>"
	@echo ""
	@echo "Type <make freiburg-regbez>, to create a new result for freiburg using the freiburg-regbez-latest-file"
	@echo ""

usage:
	@echo ""
	@echo "All of the following options are required:"
	@echo ""
	@echo "python3 osm_to_geojson.py"
	@echo "--min_lon: <float>"
	@echo "--min_lat: <float>"
	@echo "--max_lon: <float>"
	@echo "--max_lat: <float>"
	@echo "--xml_file: <string> (the original xml(osm)-file)"
	@echo "--transport_vehicle: <string> (has to be 'tram' or 'subway')"
	@echo ""
	@echo "New results will be saved in the /output folder."

freiburg-oct-2018:
	python3 osm_to_geojson.py --min_lon 7.5 --min_lat 47.78 --max_lon 8.2400002 --max_lat 48.31 --transport_vehicle tram --xml_file /data/freiburg_oct_2018.xml

freiburg-jan-2019:
	python3 osm_to_geojson.py --min_lon 7.7069000 --min_lat 47.9467000 --max_lon 8.0262000 --max_lat 48.0620000 --transport_vehicle tram --xml_file /data/freiburg_jan_2019.xml

chicago:
	python3 osm_to_geojson.py --min_lon -87.9881000 --min_lat 41.6730000 --max_lon -86.7110000 --max_lat 42.1859000 --transport_vehicle subway --xml_file /data/chicago.xml

munich:
	python3 osm_to_geojson.py --min_lon 11.2624000 --min_lat 48.0147000 --max_lon 11.9009000 --max_lat 48.2447000 --transport_vehicle subway --xml_file /data/munich.xml

paris:
	python3 osm_to_geojson.py --min_lon 2.2083000 --min_lat 48.8035000 --max_lon 2.5275000 --max_lat 48.9169000 --transport_vehicle subway --xml_file /data/paris.xml

stuttgart:
	python3 osm_to_geojson.py --min_lon 8.9243000 --min_lat 48.6521000 --max_lon 9.5629000 --max_lat 48.8793000 --transport_vehicle tram --xml_file /data/stuttgart.xml

london:
	python3 osm_to_geojson.py --min_lon -0.2365000 --min_lat 51.4479000 --max_lon 0.0827000 --max_lat 51.5552000 --transport_vehicle subway --xml_file /data/london.xml

freiburg-regbez:
	python3 osm_to_geojson.py --min_lon 7.25319 --min_lat 47.29909 --max_lon 9.246965 --max_lat 48.75152 --transport_vehicle tram --xml_file freiburg-regbez-latest.osm

all: compile test checkstyle clean

compile:
	@echo "Nothing to compile for Python"

test:
	$(TEST_CMD) read_xml_file.py
	$(TEST_CMD) compute_transfer_network.py
	$(TEST_CMD) write_geojson_file.py

checkstyle:
	$(CHECKSTYLE_CMD) osm_to_geojson.py
	$(CHECKSTYLE_CMD) read_xml_file.py
	$(CHECKSTYLE_CMD) compute_transfer_network.py
	$(CHECKSTYLE_CMD) write_geojson_file.py

clean:
	rm -f *.pyc
	rm -rf __pycache__
