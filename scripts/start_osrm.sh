#!/usr/bin/env bash
set -e

# Run OSRM backend container in standalone MLD mode
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../backend/osrm_data"

echo "Starting OSRM server on port 5000 from ${DATA_DIR}..."
docker run -t -i -p 5000:5000 -v "${DATA_DIR}:/data" osrm/osrm-backend \
    osrm-routed --algorithm mld /data/karnataka-latest.osrm
