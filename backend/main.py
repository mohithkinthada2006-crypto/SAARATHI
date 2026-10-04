"""
Saarathi FastAPI Backend — Vehicle-Aware Mobility Assistant
Serves interactive Web UI, route scoring, elevation estimation, EV feasibility analysis, and explainable recommendations.
"""

from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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


@app.get("/", response_class=HTMLResponse)
async def home_ui(request: Request):
    # If client explicitly asks for JSON, return service metadata
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse({
            "service": "Saarathi API",
            "status": "online",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        })

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Saarathi — Vehicle-Aware Smart Mobility Assistant</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <style>
        :root {
            --bg-base: #0a0d13;
            --bg-card: #131822;
            --bg-card-hover: #18202d;
            --bg-card-inner: #0d1118;
            --border: #222c3d;
            --border-highlight: rgba(25, 211, 181, 0.4);
            --teal: #19D3B5;
            --teal-glow: rgba(25, 211, 181, 0.25);
            --green: #2ECC71;
            --warn: #F5A524;
            --risk: #FF4D4F;
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --radius-lg: 20px;
            --radius-md: 14px;
            --radius-sm: 8px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Subtle animated background grid */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(circle at 15% 15%, rgba(25, 211, 181, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(46, 204, 113, 0.05) 0%, transparent 40%),
                linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
            z-index: -1;
            pointer-events: none;
        }

        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 24px 20px 40px;
        }

        /* Header */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-icon {
            width: 46px;
            height: 46px;
            border-radius: 12px;
            background: linear-gradient(135deg, #19D3B5 0%, #008f75 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 0 20px var(--teal-glow);
        }

        .brand-title {
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #FFFFFF 40%, var(--teal) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-subtitle {
            font-size: 13px;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .header-badges {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .badge {
            padding: 6px 14px;
            border-radius: 100px;
            font-size: 12px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }

        .badge-live {
            background: rgba(46, 204, 113, 0.12);
            border-color: rgba(46, 204, 113, 0.3);
            color: var(--green);
        }

        .badge-live::before {
            content: '';
            width: 7px;
            height: 7px;
            background: var(--green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--green);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        .badge-iqoo {
            background: rgba(25, 211, 181, 0.1);
            border-color: rgba(25, 211, 181, 0.3);
            color: var(--teal);
        }

        /* Layout Grid */
        .grid {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 24px;
        }

        @media (max-width: 960px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }

        /* Card Styles */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .card-title {
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }

        /* Form Controls */
        .form-group {
            margin-bottom: 18px;
        }

        .label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Vehicle Selector */
        .vehicle-selector {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            background: var(--bg-card-inner);
            padding: 6px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
        }

        .vehicle-btn {
            border: none;
            background: transparent;
            color: var(--text-secondary);
            padding: 12px 6px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
            font-family: inherit;
        }

        .vehicle-btn span:first-child {
            font-size: 20px;
        }

        .vehicle-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.04);
        }

        .vehicle-btn.active {
            background: var(--teal);
            color: #0E1116;
            box-shadow: 0 4px 14px var(--teal-glow);
            font-weight: 700;
        }

        /* EV Battery Slider */
        .battery-container {
            display: none;
            background: var(--bg-card-inner);
            padding: 16px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            margin-bottom: 18px;
            animation: fadeIn 0.3s ease;
        }

        .battery-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .battery-val {
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: var(--teal);
        }

        input[type="range"] {
            width: 100%;
            height: 6px;
            border-radius: 4px;
            background: #252e3d;
            outline: none;
            accent-color: var(--teal);
            cursor: pointer;
        }

        /* Inputs */
        .input-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .input-field {
            width: 100%;
            background: var(--bg-card-inner);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 13px;
            font-family: inherit;
            transition: border-color 0.2s;
        }

        .input-field:focus {
            outline: none;
            border-color: var(--teal);
            box-shadow: 0 0 0 2px var(--teal-glow);
        }

        /* Preset Chips */
        .presets {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 6px;
        }

        .preset-chip {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 100px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .preset-chip:hover {
            border-color: var(--teal);
            color: var(--teal);
        }

        /* CTA Button */
        .btn-cta {
            width: 100%;
            background: linear-gradient(135deg, #19D3B5 0%, #00B496 100%);
            border: none;
            color: #0a0d13;
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 700;
            padding: 16px;
            border-radius: var(--radius-md);
            cursor: pointer;
            box-shadow: 0 6px 20px var(--teal-glow);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 10px;
        }

        .btn-cta:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 28px rgba(25, 211, 181, 0.4);
        }

        .btn-cta:active {
            transform: translateY(0);
        }

        .btn-cta:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Right Panel: Map + Results */
        .results-wrapper {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        #map {
            height: 380px;
            width: 100%;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            z-index: 1;
            background: #0d1118;
        }

        /* 100% Free OpenStreetMap with high-contrast sleek Dark Mode filter - No API Key Needed */
        .leaflet-tile {
            filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.2) brightness(0.7);
        }

        /* Hero Recommendation Box */
        .recommendation-hero {
            background: linear-gradient(145deg, rgba(25, 211, 181, 0.08) 0%, rgba(19, 24, 34, 0.95) 100%);
            border: 1px solid var(--border-highlight);
            border-radius: var(--radius-lg);
            padding: 24px;
            position: relative;
            overflow: hidden;
        }

        .recommendation-hero::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
            background: var(--teal);
            box-shadow: 0 0 12px var(--teal);
        }

        .rec-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .rec-route-name {
            font-family: 'Outfit', sans-serif;
            font-size: 26px;
            font-weight: 800;
            color: var(--teal);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .score-pill {
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            background: rgba(25, 211, 181, 0.15);
            border: 1px solid var(--teal);
            color: var(--teal);
            padding: 4px 16px;
            border-radius: 100px;
        }

        .rec-explanation {
            font-size: 15px;
            color: #E2E8F0;
            line-height: 1.6;
        }

        /* Routes Comparison Cards */
        .routes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
        }

        .route-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 18px;
            transition: all 0.25s ease;
            position: relative;
        }

        .route-card:hover {
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        .route-card.is-best {
            border-color: var(--teal);
            background: linear-gradient(180deg, rgba(25, 211, 181, 0.05) 0%, var(--bg-card) 100%);
            box-shadow: 0 4px 20px rgba(25, 211, 181, 0.12);
        }

        .rc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .rc-title {
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .rc-title.best {
            color: var(--teal);
        }

        .rc-score {
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .rc-metrics {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: var(--text-secondary);
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }

        .metric-dot {
            color: var(--text-muted);
        }

        /* Sub-scores bars */
        .subscores-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .subscore-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-secondary);
        }

        .subscore-bar-bg {
            width: 90px;
            height: 5px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            overflow: hidden;
            margin-left: 8px;
        }

        .subscore-bar-fill {
            height: 100%;
            background: var(--teal);
            border-radius: 4px;
        }

        /* EV Badge */
        .ev-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            margin-bottom: 10px;
        }

        .ev-badge.feasible {
            background: rgba(46, 204, 113, 0.15);
            color: var(--green);
        }

        .ev-badge.low-margin {
            background: rgba(245, 165, 36, 0.15);
            color: var(--warn);
        }

        .ev-badge.high-risk {
            background: rgba(255, 77, 79, 0.15);
            color: var(--risk);
        }

        /* Footer */
        footer {
            margin-top: 40px;
            text-align: center;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-muted);
        }

        footer a {
            color: var(--teal);
            text-decoration: none;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Navigation Header -->
        <header>
            <div class="brand">
                <div class="brand-icon">🧭</div>
                <div>
                    <h1 class="brand-title">Saarathi</h1>
                    <p class="brand-subtitle">Vehicle-Aware Smart Mobility Assistant</p>
                </div>
            </div>
            <div class="header-badges">
                <span class="badge badge-iqoo">⚡ iQOO Hackathon 2026</span>
                <span class="badge badge-live">Backend Online</span>
                <a href="/docs" target="_blank" class="badge" style="text-decoration:none; color:var(--teal);">📖 Swagger Docs</a>
            </div>
        </header>

        <!-- Main Workspace -->
        <div class="grid">
            <!-- Left Controls Sidebar -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Route Parameters</h2>
                </div>

                <div class="form-group">
                    <label class="label">Vehicle Type</label>
                    <div class="vehicle-selector">
                        <button type="button" class="vehicle-btn active" data-vehicle="bike" onclick="selectVehicle('bike')">
                            <span>🏍️</span>
                            <span>Bike</span>
                        </button>
                        <button type="button" class="vehicle-btn" data-vehicle="car" onclick="selectVehicle('car')">
                            <span>🚗</span>
                            <span>Car</span>
                        </button>
                        <button type="button" class="vehicle-btn" data-vehicle="ev" onclick="selectVehicle('ev')">
                            <span>⚡</span>
                            <span>EV</span>
                        </button>
                    </div>
                </div>

                <!-- Dynamic EV Battery Input -->
                <div class="battery-container" id="battery-box">
                    <div class="battery-header">
                        <label class="label" style="margin:0;">Current Battery</label>
                        <span class="battery-val" id="battery-label">100%</span>
                    </div>
                    <input type="range" id="battery-slider" min="5" max="100" value="100" oninput="updateBattery(this.value)">
                </div>

                <!-- Coordinates Inputs -->
                <div class="form-group">
                    <label class="label">Origin (Start Lat, Lon)</label>
                    <div class="input-row">
                        <input type="number" step="any" id="start-lat" class="input-field" value="12.9756" placeholder="Lat">
                        <input type="number" step="any" id="start-lon" class="input-field" value="77.6068" placeholder="Lon">
                    </div>
                </div>

                <div class="form-group">
                    <label class="label">Destination (End Lat, Lon)</label>
                    <div class="input-row">
                        <input type="number" step="any" id="end-lat" class="input-field" value="12.9352" placeholder="Lat">
                        <input type="number" step="any" id="end-lon" class="input-field" value="77.6244" placeholder="Lon">
                    </div>
                    <div class="presets">
                        <span class="preset-chip" onclick="setCoords(12.9756, 77.6068, 12.9352, 77.6244)">MG Road ➔ Koramangala</span>
                        <span class="preset-chip" onclick="setCoords(12.9784, 77.6408, 12.9698, 77.7500)">Indiranagar ➔ Whitefield</span>
                    </div>
                </div>

                <button class="btn-cta" id="compare-btn" onclick="evaluateRoutes()">
                    <span>⚡</span>
                    <span>Compare & Score Routes</span>
                </button>
            </div>

            <!-- Right Results & Interactive Map Panel -->
            <div class="results-wrapper">
                <!-- Leaflet Interactive Map -->
                <div id="map"></div>

                <!-- Live Recommendation Banner -->
                <div id="recommendation-container" style="display:none;"></div>

                <!-- Candidate Routes Grid -->
                <div id="routes-container" class="routes-grid"></div>
            </div>
        </div>

        <footer>
            Saarathi · Vehicle-Aware Mobility Engine · Powered by FastAPI & OpenStreetMap
        </footer>
    </div>

    <script>
        let currentVehicle = 'bike';
        let currentBattery = 100;
        let map, routeLayers = [];

        // Initialize Dark Tile Map (No API Key Required)
        function initMap() {
            map = L.map('map', { zoomControl: true }).setView([12.9554, 77.6156], 13);
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(map);
        }

        function selectVehicle(v) {
            currentVehicle = v;
            document.querySelectorAll('.vehicle-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.vehicle === v);
            });
            document.getElementById('battery-box').style.display = (v === 'ev') ? 'block' : 'none';
        }

        function updateBattery(val) {
            currentBattery = parseFloat(val);
            document.getElementById('battery-label').innerText = val + '%';
        }

        function setCoords(sLat, sLon, eLat, eLon) {
            document.getElementById('start-lat').value = sLat;
            document.getElementById('start-lon').value = sLon;
            document.getElementById('end-lat').value = eLat;
            document.getElementById('end-lon').value = eLon;
            evaluateRoutes();
        }

        async function evaluateRoutes() {
            const btn = document.getElementById('compare-btn');
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span><span>Analyzing Terrain & Suitability...</span>';

            const payload = {
                start_lat: parseFloat(document.getElementById('start-lat').value),
                start_lon: parseFloat(document.getElementById('start-lon').value),
                end_lat: parseFloat(document.getElementById('end-lat').value),
                end_lon: parseFloat(document.getElementById('end-lon').value),
                vehicle: currentVehicle,
                battery_pct: currentBattery
            };

            try {
                const res = await fetch('/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) throw new Error('API returned status ' + res.status);
                const data = await res.json();
                renderResults(data);
            } catch (err) {
                alert('Error querying Saarathi route engine: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>⚡</span><span>Compare & Score Routes</span>';
            }
        }

        function renderResults(data) {
            // 1. Clear previous layers
            routeLayers.forEach(l => map.removeLayer(l));
            routeLayers = [];

            const bounds = [];
            const colors = ['#19D3B5', '#60A5FA', '#F59E0B', '#A78BFA'];

            // 2. Render Hero Recommendation
            const recBox = document.getElementById('recommendation-container');
            const bestRoute = data.routes[data.best_index];
            recBox.style.display = 'block';
            recBox.innerHTML = `
                <div class="recommendation-hero">
                    <div class="rec-top">
                        <div class="rec-route-name">
                            <span>★</span>
                            <span>Take Route ${data.best_index + 1}</span>
                        </div>
                        <span class="score-pill">${bestRoute.score} / 100</span>
                    </div>
                    <p class="rec-explanation">${data.explanation}</p>
                </div>
            `;

            // 3. Render Route Cards
            const cardsBox = document.getElementById('routes-container');
            cardsBox.innerHTML = '';

            data.routes.forEach((r, idx) => {
                const isBest = (idx === data.best_index);
                const strokeColor = isBest ? '#19D3B5' : colors[(idx + 1) % colors.length];

                // Add GeoJSON polyline to Leaflet Map
                if (r.geometry && r.geometry.coordinates) {
                    const latLngs = r.geometry.coordinates.map(pt => [pt[1], pt[0]]);
                    latLngs.forEach(pt => bounds.push(pt));

                    const poly = L.polyline(latLngs, {
                        color: strokeColor,
                        weight: isBest ? 6 : 4,
                        opacity: isBest ? 1.0 : 0.6,
                        dashArray: isBest ? null : '6, 6'
                    }).addTo(map);

                    poly.bindPopup(`<b>Route ${r.index + 1}</b><br>Score: ${r.score}/100<br>ETA: ${r.eta_min}m | Dist: ${r.distanceKm}km`);
                    routeLayers.push(poly);
                }

                // EV pill
                let evPillHtml = '';
                if (r.ev) {
                    const statusClass = r.ev.status === 'HIGH_RISK' ? 'high-risk' : (r.ev.status === 'LOW_MARGIN' ? 'low-margin' : 'feasible');
                    evPillHtml = `
                        <div class="ev-badge ${statusClass}">
                            ⚡ ${r.ev.status.replace('_', ' ')} · Arrival ${r.ev.arrival_pct}%
                        </div>
                    `;
                }

                // Sub-scores breakdown
                const subScoreItems = Object.entries(r.sub_scores || {}).map(([key, val]) => `
                    <div class="subscore-item">
                        <span style="text-transform:capitalize;">${key}</span>
                        <div style="display:flex; align-items:center;">
                            <span style="font-weight:600; color:var(--text-primary);">${val}</span>
                            <div class="subscore-bar-bg">
                                <div class="subscore-bar-fill" style="width:${val}%;"></div>
                            </div>
                        </div>
                    </div>
                `).join('');

                const cardHtml = `
                    <div class="route-card ${isBest ? 'is-best' : ''}">
                        <div class="rc-header">
                            <span class="rc-title ${isBest ? 'best' : ''}">
                                ${isBest ? '★ ' : ''}Route ${r.index + 1}
                            </span>
                            <span class="rc-score">${r.score}<span style="font-size:13px; color:var(--text-muted);">/100</span></span>
                        </div>
                        <div class="rc-metrics">
                            <span>⏱️ ${r.eta_min} min</span>
                            <span class="metric-dot">·</span>
                            <span>📍 ${r.distance_km} km</span>
                            <span class="metric-dot">·</span>
                            <span>⛰️ ${r.elevation_gain_m}m</span>
                        </div>
                        ${evPillHtml}
                        <div class="subscores-list">
                            ${subScoreItems}
                        </div>
                    </div>
                `;
                cardsBox.innerHTML += cardHtml;
            });

            // Fit map bounds
            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [30, 30] });
            }
        }

        window.onload = () => {
            initMap();
            evaluateRoutes();
        };
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


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
