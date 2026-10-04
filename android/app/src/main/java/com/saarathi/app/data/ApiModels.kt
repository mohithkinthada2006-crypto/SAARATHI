package com.saarathi.app.data

import com.google.gson.annotations.SerializedName

data class RouteRequest(
    @SerializedName("start_lat") val startLat: Double,
    @SerializedName("start_lon") val startLon: Double,
    @SerializedName("end_lat") val endLat: Double,
    @SerializedName("end_lon") val endLon: Double,
    @SerializedName("vehicle") val vehicle: String,
    @SerializedName("battery_pct") val batteryPct: Double = 100.0
)

data class EvInfo(
    @SerializedName("energy_used_pct") val energyUsedPct: Double,
    @SerializedName("arrival_pct") val arrivalPct: Double,
    @SerializedName("status") val status: String,
    @SerializedName("uncertainty_pct") val uncertaintyPct: Double
)

data class RouteEntry(
    @SerializedName("index") val index: Int,
    @SerializedName("score") val score: Int,
    @SerializedName("sub_scores") val subScores: Map<String, Int>,
    @SerializedName("distance_km") val distanceKm: Double,
    @SerializedName("eta_min") val etaMin: Double,
    @SerializedName("elevation_gain_m") val elevationGainM: Double,
    @SerializedName("ev") val ev: EvInfo? = null
)

data class CompareResponse(
    @SerializedName("vehicle") val vehicle: String,
    @SerializedName("best_index") val bestIndex: Int,
    @SerializedName("explanation") val explanation: String,
    @SerializedName("routes") val routes: List<RouteEntry>
)
