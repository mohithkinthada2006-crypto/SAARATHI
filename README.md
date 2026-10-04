# Saarathi — Vehicle-Aware Smart Mobility Assistant
iQOO Hackathon 2026 · Grand Finale · Mobility Track

Saarathi is a vehicle-aware smart mobility assistant that evaluates candidate routes against vehicle type (bike / car / EV), terrain elevation, road surface quality, and hazard density to produce a transparent **Journey Suitability Score (0–100)** and an explainable recommendation.

---

## Architecture
- **Backend**: FastAPI + OSRM (Open Source Routing Machine) + Open-Meteo Elevation API
- **Android App**: Kotlin + Jetpack Compose + On-Device Accelerometer Hazard Detection
- **AI Engine**: Rule-based explainability with planned on-device QNN integration (Gemma 2B / Llama 3.2 1B via Qualcomm AI Hub)
- **Bridge**: iQOO Office Kit for cross-device connectivity

---

## Quick Start

### 1. Setup & Preprocess OSRM Data
```bash
./setup.sh
```
This sets up the Python virtual environment, downloads the OpenStreetMap Karnataka extract, and runs the OSRM extraction, partition, and customization pipelines.

### 2. Deploy Services
```bash
./deploy.sh
```
This spins up the OSRM container on port `5000` and the Saarathi FastAPI backend on port `8000`.

### 3. Configure Android App
Update `BASE_URL` in `android/app/src/main/java/com/saarathi/app/data/ApiService.kt` to your laptop's LAN IP (e.g. `http://192.168.1.100:8000/`) or `http://10.0.2.2:8000/` if using the Android Emulator.

### 4. Build and Install on Phone
```bash
./scripts/deploy_phone.sh
```

---

## Demo Coordinates (Bengaluru)
- **Start (MG Road)**: `12.9756, 77.6068`
- **End (Koramangala)**: `12.9352, 77.6244`

---

## Vehicle Scoring Factors

| Factor | Bike Weight | Car Weight | EV Weight |
|---|---|---|---|
| **Efficiency (Duration)** | 20% | 27% | 18% |
| **Road Quality & Smoothness** | 28% | 20% | 12% |
| **Vehicle Match & Dimensions** | 17% | 20% | 12% |
| **Hazard & Safety Risk** | 22% | 15% | 10% |
| **Elevation & Gradients** | 8% | 8% | 18% |
| **Energy & Battery Security** | 5% | 10% | 30% |
| **Total** | **100%** | **100%** | **100%** |
