"""
Saarathi Elevation Module — Open-Meteo elevation API integration.
Calculates cumulative positive elevation gain across route coordinates.
"""

from typing import List, Tuple
import httpx

OPEN_METEO = "https://api.open-meteo.com/v1/elevation"


async def get_elevation_gain(coords: List[Tuple[float, float]]) -> float:
    """
    Fetches elevation profile from Open-Meteo for a list of (lat, lon) coordinates
    and calculates cumulative positive gain (only upward diffs).
    """
    if not coords or len(coords) < 2:
        return 0.0

    lats = ",".join(f"{lat:.6f}" for lat, _ in coords)
    lons = ",".join(f"{lon:.6f}" for _, lon in coords)

    params = {"latitude": lats, "longitude": lons}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO, params=params)
            response.raise_for_status()
            data = response.json()
            elevations = data.get("elevation", [])

            if not elevations or len(elevations) < 2:
                return 0.0

            positive_gain = 0.0
            for i in range(1, len(elevations)):
                diff = elevations[i] - elevations[i - 1]
                if diff > 0:
                    positive_gain += diff

            return round(positive_gain, 1)
    except Exception as e:
        raise e
