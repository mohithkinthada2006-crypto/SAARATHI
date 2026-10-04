"""
Saarathi FastAPI Backend — Vehicle-Aware Mobility Assistant
Serves route scoring, elevation estimation, EV feasibility analysis, and explainable recommendations.
"""

from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scoring import score_route, ev_feasibility, generate_explanation
import routing
import elevation

app = FastAPI(title="Saarathi API", version="1.0.0")

# Enable wide CORS for mobile app, web dashboard, and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RouteRequest(BaseModel):
    start_lat: float = Field(..., description="Starting latitude")
    start_lon: float = Field(..., description="Starting longitude")
    end_lat: float = Field(..., description="Destination latitude")
    end_lon: float = Field(..., description="Destination longitude")
    vehicle: str = Field(..., description="Vehicle type: 'bike', 'car', or 'ev'")
    battery_pct: float = Field(
        100.0, ge=0.0, le=100.0, description="Current battery percentage for EV"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "saarathi"}


@app.post("/compare")
async def compare_routes(request: RouteRequest):
    vehicle = request.vehicle.strip().lower()
    if vehicle not in {"bike", "car", "ev"}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid vehicle '{request.vehicle}'. Must be 'bike', 'car', or 'ev'.",
        )

    # 1. Fetch Candidate Routes from OSRM
    osrm_data = await routing.fetch_candidate_routes(
        start_lon=request.start_lon,
        start_lat=request.start_lat,
        end_lon=request.end_lon,
        end_lat=request.end_lat,
    )

    if not osrm_data or osrm_data.get("code") != "Ok" or not osrm_data.get("routes"):
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch candidate routes from routing engine.",
        )

    raw_routes = osrm_data["routes"]
    processed_routes: List[Dict[str, Any]] = []

    fallback_elevations = [120.0, 40.0, 80.0]

    for idx, r in enumerate(raw_routes):
        distance_meters = float(r.get("distance", 5000))
        duration_seconds = float(r.get("duration", 1200))
        distance_km = round(distance_meters / 1000.0, 2)
        eta_min = round(duration_seconds / 60.0, 1)

        # Extract & sample geometry coordinates for elevation profiling
        geometry = r.get("geometry", {})
        coords = geometry.get("coordinates", [])

        # Sample up to 5 points along the route: [lon, lat] -> (lat, lon)
        sampled_points = []
        if coords:
            step = max(1, len(coords) // 5)
            selected_coords = [coords[i] for i in range(0, len(coords), step)][:5]
            if coords[-1] not in selected_coords:
                selected_coords.append(coords[-1])
            sampled_points = [(pt[1], pt[0]) for pt in selected_coords]

        # 2. Fetch Elevation Gain with resilient fallback
        elev_gain = fallback_elevations[idx % len(fallback_elevations)]
        if sampled_points:
            try:
                elev_gain = await elevation.get_elevation_gain(sampled_points)
            except Exception:
                elev_gain = fallback_elevations[idx % len(fallback_elevations)]

        r["elevation_gain"] = elev_gain
        r["duration_sec"] = duration_seconds

        # 3. Score Route
        score, sub_scores = score_route(
            route=r,
            vehicle=vehicle,
            battery_pct=request.battery_pct,
            route_index=idx,
        )

        route_entry: Dict[str, Any] = {
            "index": idx,
            "score": score,
            "sub_scores": sub_scores,
            "distance_km": distance_km,
            "eta_min": eta_min,
            "elevation_gain_m": elev_gain,
            "duration_sec": duration_seconds,
            "geometry": geometry,
        }

        # 4. EV Feasibility Analysis
        if vehicle == "ev":
            route_entry["ev"] = ev_feasibility(
                distance_km=distance_km,
                battery_pct=request.battery_pct,
            )

        processed_routes.append(route_entry)

    # 5. Determine Best Route (argmax score)
    best_idx = max(range(len(processed_routes)), key=lambda i: processed_routes[i]["score"])
    best_route = processed_routes[best_idx]

    # 6. Generate Rule-Based Explanation (Plug-and-play for Qualcomm AI Hub / QNN LLM)
    explanation = generate_explanation(
        vehicle=vehicle,
        best_route=best_route,
        best_idx=best_idx,
        all_routes=processed_routes,
    )

    return {
        "vehicle": vehicle,
        "best_index": best_idx,
        "explanation": explanation,
        "routes": processed_routes,
    }
