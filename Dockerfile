FROM ubuntu:18.10 as build
MAINTAINER Katharina Matulla <katharina.matulla@gmail.com>
WORKDIR "/tmp"
RUN apt-get update && apt-get install -y python3 python3-pip make git vim wget zip bzip2 unzip --no-install-recommends apt-utils
RUN python3 -m pip install --upgrade pip pytest
WORKDIR "/root"

# get all files
COPY . .

# install python3 dependencies
RUN python3 -m pip install -r requirements.txt

# freiburg-regbez-latest
RUN wget https://download.geofabrik.de/europe/germany/baden-wuerttemberg/freiburg-regbez-latest.osm.bz2
RUN bzip2 -d freiburg-regbez-latest.osm.bz2

WORKDIR "/root/"
CMD ["/bin/bash", "--rcfile", "bashrc"]

# Porgram start
# python3 osm_to_geojson.py --min_lon 7.5 --min_lat 47.78 --max_lon 8.2400002 --max_lat 48.31 --transport_vehicle tram --xml_file /data/freiburg_oct_2018.xml
# use the Makefile for other cities/versions

# build docker image: docker build -t osm-geojson .
# start docker container: docker run -it -v /nfs/students/katharina-matulla:/data osm-geojson
