#!/usr/bin/env bash
set -e
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p osrm_data
if [ ! -f osrm_data/karnataka-latest.osm.pbf ]; then
  wget -O osrm_data/karnataka-latest.osm.pbf \
    https://download.geofabrik.de/asia/india/karnataka-latest.osm.pbf
fi
docker run -t -v $(pwd)/osrm_data:/data osrm/osrm-backend \
  osrm-extract -p /opt/car.lua /data/karnataka-latest.osm.pbf
docker run -t -v $(pwd)/osrm_data:/data osrm/osrm-backend \
  osrm-partition /data/karnataka-latest.osrm
docker run -t -v $(pwd)/osrm_data:/data osrm/osrm-backend \
  osrm-customize /data/karnataka-latest.osrm
cd ..
echo "Setup complete."
