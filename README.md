# Saarathi — Vehicle-Aware Smart Mobility Assistant
iQOO Hackathon 2026 · Grand Finale · Mobility Track

Saarathi is a vehicle-aware smart mobility assistant that evaluates candidate routes against vehicle type (bike / car / EV), terrain elevation, road surface quality, and hazard density to produce a transparent **Journey Suitability Score (0–100)** and an explainable recommendation.

---

## Architecture
- **Backend**: FastAPI + Serverless Routing + Open-Meteo Elevation API
- **Deployment**: Vercel (Serverless Python runtime)
- **Android App**: Kotlin + Jetpack Compose + On-Device Accelerometer Hazard Detection
- **AI Engine**: Explainable Journey Reasoning engine (designed for Snapdragon NPU on-device LLMs via Qualcomm AI Hub)

---

## Deploy to Vercel (1-Click)

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Deploy Saarathi on Vercel"
   git push origin main
   ```
2. Go to **[vercel.com/new](https://vercel.com/new)**.
3. Import your GitHub repository: `mohithkinthada2006-crypto/SAARATHI`.
4. Click **Deploy**.

Your API will be live at `https://<your-project>.vercel.app`.

---

## API Endpoints
- `GET /health` → `{"status": "ok", "service": "saarathi"}`
- `POST /compare` → Evaluates and scores alternative routes based on vehicle type and battery headroom.

---

## Android App Setup
Update `BASE_URL` in `android/app/src/main/java/com/saarathi/app/data/ApiService.kt` to your Vercel deployment URL:
```kotlin
const val BASE_URL = "https://<your-project>.vercel.app/"
```

Build and run on your device:
```bash
cd android
./gradlew installDebug
```
