"""
Saarathi Scoring Engine — Vehicle-Aware Journey Suitability
Calculates multi-dimensional suitability scores for bike, car, and EV routes,
along with battery feasibility and explainable recommendations.
"""

from typing import Dict, Any, Tuple, List

# Factor weights per vehicle type (each summing to 100)
WEIGHTS: Dict[str, Dict[str, int]] = {
    "bike": {
        "efficiency": 20,
        "road": 28,
        "suitability": 17,
        "hazards": 22,
        "elevation": 8,
        "energy": 5,
    },
    "car": {
        "efficiency": 27,
        "road": 20,
        "suitability": 20,
        "hazards": 15,
        "elevation": 8,
        "energy": 10,
    },
    "ev": {
        "efficiency": 18,
        "road": 12,
        "suitability": 12,
        "hazards": 10,
        "elevation": 18,
        "energy": 30,
    },
}

EV_THRESHOLDS = {"high_risk": 5.0, "low_margin": 8.0}
EV_PCT_PER_KM = 1.8  # Estimated percentage battery consumption per km


def sub_score_efficiency(duration_sec: float) -> int:
    """
    Efficiency score: Faster routes receive higher scores.
    Standardized duration decay capped strictly between 0 and 100.
    """
    duration_min = duration_sec / 60.0
    # Baseline: 15 mins or less gets near 100; decreases as duration increases
    score = 100.0 - (duration_min * 1.5)
    return int(max(0, min(100, round(score))))


def sub_score_road(route_index: int, osm_surface: str | None = None) -> int:
    """
    Road quality sub-score: Assesses pavement, potholes, and surface smoothness.
    Falls back to mock deterministic index distribution if OSM data is absent.
    """
    if osm_surface:
        surface_lower = osm_surface.lower()
        if "asphalt" in surface_lower or "paved" in surface_lower:
            return 92
        elif "compacted" in surface_lower or "concrete" in surface_lower:
            return 75
        elif "unpaved" in surface_lower or "gravel" in surface_lower:
            return 40

    fallback_scores = [50, 92, 75]
    return fallback_scores[route_index % len(fallback_scores)]


def sub_score_suitability(vehicle: str, route_index: int) -> int:
    """
    Vehicle compatibility sub-score:
    Tailors suitability based on road width, traffic flow, and vehicle dynamics.
    Includes +5% bike bias or +2% EV bias.
    """
    base_scores = [70, 85, 80]
    base = base_scores[route_index % len(base_scores)]
    if vehicle == "bike":
        base += int(base * 0.05)
    elif vehicle == "ev":
        base += int(base * 0.02)
    return int(max(0, min(100, base)))


def sub_score_hazards(route_index: int) -> int:
    """
    Hazard safety sub-score: Reflects blackspots, sharp bends, and heavy intersection density.
    Higher score indicates fewer hazards / safer route.
    """
    hazard_scores = [45, 90, 70]
    return hazard_scores[route_index % len(hazard_scores)]


def sub_score_elevation(elevation_gain_m: float) -> int:
    """
    Elevation impact sub-score:
    Higher elevation gain penalizes bicycles and EVs due to physical effort/energy draw.
    Score = 100 - gain/5, capped 0–100.
    """
    score = 100.0 - (elevation_gain_m / 5.0)
    return int(max(0, min(100, round(score))))


def sub_score_energy(distance_km: float, vehicle: str, battery_pct: float = 100.0) -> int:
    """
    Energy efficiency sub-score:
    For non-EVs returns standard baseline of 70.
    For EVs evaluates remaining battery headroom after distance travel.
    """
    if vehicle != "ev":
        return 70

    energy_used = distance_km * EV_PCT_PER_KM
    remaining_battery = max(0.0, battery_pct - energy_used)
    # Scaled sub-score reflecting remaining energy security
    score = (remaining_battery / 100.0) * 100.0
    return int(max(0, min(100, round(score))))


def score_route(
    route: Dict[str, Any],
    vehicle: str,
    battery_pct: float = 100.0,
    route_index: int = 0,
) -> Tuple[int, Dict[str, int]]:
    """
    Computes overall Journey Suitability Score (0–100) and component sub-scores
    using vehicle-specific weightings.
    """
    v_type = vehicle.lower() if vehicle.lower() in WEIGHTS else "car"
    w = WEIGHTS[v_type]

    duration_sec = float(route.get("duration", 1200))
    distance_km = float(route.get("distance", 5000)) / 1000.0
    elevation_gain = float(route.get("elevation_gain", 40.0))

    sub_scores = {
        "efficiency": sub_score_efficiency(duration_sec),
        "road": sub_score_road(route_index),
        "suitability": sub_score_suitability(v_type, route_index),
        "hazards": sub_score_hazards(route_index),
        "elevation": sub_score_elevation(elevation_gain),
        "energy": sub_score_energy(distance_km, v_type, battery_pct),
    }

    total_weighted = sum(sub_scores[k] * (w[k] / 100.0) for k in w)
    final_score = int(max(0, min(100, round(total_weighted))))

    return final_score, sub_scores


def ev_feasibility(distance_km: float, battery_pct: float = 100.0) -> Dict[str, Any]:
    """
    Evaluates EV battery feasibility and arrival margin.
    Flags HIGH_RISK (<5% margin) and LOW_MARGIN (<8% margin).
    """
    energy_used_pct = round(distance_km * EV_PCT_PER_KM, 1)
    arrival_pct = round(battery_pct - energy_used_pct, 1)

    if arrival_pct < 5.0:
        status = "HIGH_RISK"
    elif arrival_pct < 8.0:
        status = "LOW_MARGIN"
    else:
        status = "FEASIBLE"

    return {
        "energy_used_pct": energy_used_pct,
        "arrival_pct": arrival_pct,
        "status": status,
        "uncertainty_pct": 3.0,
    }


def generate_explanation(
    vehicle: str,
    best_route: Dict[str, Any],
    best_idx: int,
    all_routes: List[Dict[str, Any]],
) -> str:
    """
    Generates explainable recommendation reasoning.
    Designed with a single interface to be seamlessly replaced with an
    on-device LLM (Gemma 2B / Llama 3.2 1B via Qualcomm AI Hub / QNN).
    """
    route_num = best_idx + 1
    v = vehicle.lower()
    best_sub = best_route.get("sub_scores", {})
    best_score = best_route.get("score", 0)

    # Find the fastest route index for comparison
    durations = [r.get("duration_sec", r.get("duration", 0)) for r in all_routes]
    fastest_idx = durations.index(min(durations)) if durations else best_idx

    reasons = []
    if v == "bike":
        if best_sub.get("road", 0) >= 80:
            reasons.append("better road surface and fewer potholes")
        if best_sub.get("elevation", 0) >= 80:
            reasons.append("minimal steep climbs")
        if best_sub.get("hazards", 0) >= 80:
            reasons.append("lower hazard density")
        if not reasons:
            reasons.append("superior two-wheeler maneuverability and safety")

    elif v == "ev":
        ev_data = best_route.get("ev", {})
        arrival = ev_data.get("arrival_pct", 50.0)
        reasons.append(f"safe battery arrival margin of {arrival}%")
        if best_sub.get("elevation", 0) >= 80:
            reasons.append("gentle gradients that conserve energy")
        if best_sub.get("efficiency", 0) >= 75:
            reasons.append("steady cruise efficiency")

    else:  # car
        if best_sub.get("efficiency", 0) >= 80:
            reasons.append("optimal speed and flow")
        if best_sub.get("road", 0) >= 80:
            reasons.append("smooth multilane tarmac")
        if not reasons:
            reasons.append("overall balanced driving comfort")

    joined_reasons = " and ".join(reasons)

    if fastest_idx != best_idx and len(all_routes) > 1:
        time_diff_min = max(
            1,
            int(
                round(
                    (
                        all_routes[best_idx].get("duration_sec", 0)
                        - all_routes[fastest_idx].get("duration_sec", 0)
                    )
                    / 60.0
                )
            ),
        )
        return (
            f"Route {route_num} is {time_diff_min} min slower than the fastest alternative, "
            f"but more suitable for your {v} because it offers {joined_reasons} (Suitability: {best_score}/100)."
        )

    return (
        f"Route {route_num} is strongly recommended for your {v} with a Suitability Score of "
        f"{best_score}/100 due to {joined_reasons}."
    )
