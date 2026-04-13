# EV Dashboard — Frontend Specification Document

**Project:** Real-Time Electric Vehicle Dashboard
**Platform:** Raspberry Pi 4 · 7-inch Display (1024 × 600 px)
**Date:** 2026-03-24
**Status:** In Progress — Tile UI complete, live data wiring pending

---

## 1. Project Overview

A real-time EV telemetry dashboard running locally on a Raspberry Pi.
The display shows live vehicle data (speed, battery, temperature, drive mode, etc.) received from an ESP32 microcontroller via a Python backend.

**Key goals:**
- Optimised exactly for a 7-inch 1024×600px screen — no responsive layout
- Config-driven: changing one JSON file changes the entire UI layout
- No internet dependency — runs fully offline on the Pi
- Instant data refresh — WebSocket push, no polling

---

## 2. Hardware Setup

| Component       | Details                              |
|-----------------|--------------------------------------|
| Display         | 7-inch HDMI, 1024 × 600 px           |
| Compute         | Raspberry Pi 4                       |
| Microcontroller | ESP32 (reads sensors, sends CAN/BMS) |
| Connection      | ESP32 → Pi via USB Serial / Wi-Fi    |

---

## 3. Technology Stack

| Layer       | Technology          | Purpose                              |
|-------------|---------------------|--------------------------------------|
| Frontend    | React + Vite        | UI rendering                         |
| State       | Zustand             | Global live telemetry store          |
| Transport   | Socket.IO (client)  | WebSocket connection to backend      |
| HTTP        | Axios               | Initial REST fetch on startup        |
| Styling     | Inline CSS          | No Tailwind — self-contained tiles   |
| Config      | JSON                | Drives layout without code changes   |

---

## 4. System Architecture

```
┌─────────────┐       Serial / Wi-Fi      ┌──────────────────┐
│    ESP32    │ ─────────────────────────► │  Python Backend  │
│ (sensors,   │                            │  (FastAPI /      │
│  BMS, CAN)  │                            │   Flask)         │
└─────────────┘                            └────────┬─────────┘
                                                    │
                                          Socket.IO WebSocket
                                          events: bms_update
                                                    │
                                                    ▼
                                     ┌──────────────────────────┐
                                     │   React Frontend (Pi)    │
                                     │                          │
                                     │  websocket.js            │
                                     │    ↓ onMessage           │
                                     │  useVehicleStore         │
                                     │    ↓ updateTelemetry     │
                                     │  TilesEngine             │
                                     │    ↓ reads config        │
                                     │  TileType1–6             │
                                     │    ↓ renders on screen   │
                                     └──────────────────────────┘
```

---

## 5. API & Data Layer

### 5.1 REST API (startup only)

**Endpoint:** `GET http://localhost:5000/api/bms`
**Purpose:** Fetch initial vehicle state on page load so tiles are not empty before first WebSocket message.
**Used by:** `apiClient.js` → `fetchTelemetry()`

```json
{
  "speed_kmph": 45.2,
  "voltage": 72.4,
  "current": 18.1,
  "soc": 83,
  "temperature": 38,
  "mode": "ECO",
  "brake": false,
  "cruise": false,
  "connected": true
}
```

### 5.2 WebSocket (live data)

**URL:** `http://localhost:5000` (Socket.IO)
**Events listened:** `bms_update`, `bms_data`
**Push frequency:** Every ~500ms from backend
**Reconnect:** Automatic, infinite retries, exponential backoff (1s → 30s max)

The WebSocket manager (`websocket.js`) is a singleton class. It:
1. Connects on app initialise
2. Fires `onMessage(data)` callback on every telemetry event
3. Fires `onStatusChange(status)` for CONNECTED / DISCONNECTED / CONNECTING

### 5.3 Full Telemetry Field Reference

| Field                  | Type    | Description                          |
|------------------------|---------|--------------------------------------|
| `speed_kmph`           | number  | Current vehicle speed (km/h)         |
| `voltage`              | number  | Battery pack voltage (V)             |
| `current`              | number  | Battery current draw (A)             |
| `power`                | number  | Instantaneous power (W)              |
| `soc`                  | number  | State of Charge (%)                  |
| `soh`                  | number  | State of Health (%)                  |
| `temperature`          | number  | Primary temperature sensor (°C)      |
| `throttle`             | number  | Throttle position (%)                |
| `dte`                  | number  | Distance to Empty (km)               |
| `total_distance`       | number  | Odometer total (km)                  |
| `current_ride_distance`| number  | Current trip distance (km)           |
| `mode` / `speed_mode`  | string  | Drive mode: NOR / ECO / HIGH         |
| `brake`                | boolean | Brake engaged                        |
| `cruise`               | boolean | Cruise control active                |
| `regen_active`         | boolean | Regenerative braking active          |
| `connected`            | boolean | BMS connection state                 |
| `esp32_connected`      | boolean | ESP32 connection state               |

---

## 6. State Management (Zustand Store)

**File:** `src/store/useVehicleStore.js`

The store is the single source of truth for all live data.

### Lifecycle
```
App mounts
  → store.initialize() called
    → REST GET /api/bms  (initial snapshot)
    → wsManager.connect()
      → on each WS message → store.updateTelemetry(data)
        → normalise raw fields
        → throttle to max 20 fps (50ms gate)
        → update telemetry object
        → append to history arrays (every 5s)
```

### History Tracking
- Fields tracked: `speed_kmph`, `throttle`
- Sample interval: every **5 seconds**
- Retention window: **2 hours** (auto-pruned)
- Format: `[{ timestamp: ms, value: number }, ...]`
- Used by TileType1 (line graph) for scrolling history

---

## 7. Config-Driven Layout Engine

**File:** `src/engine/TilesEngine.jsx`
**Config:** `src/config/tilesConfig.json`

### How it works

1. `TilesEngine` reads `tilesConfig.json` at startup
2. Maps each tile's `type` number to a React component via `REGISTRY`
3. Places each tile on a CSS grid using `col`, `row`, `w`, `h`
4. Passes `props` from config directly into the component

```js
const REGISTRY = {
  1: TileType1,   // Line graph
  2: TileType2,   // Circular ring
  3: TileType3,   // Progress bar
  4: TileType4,   // Status + number
  5: TileType5,   // Hero number
  6: TileType6,   // Drive mode
};
```

### To add a tile — no code change needed:
```json
{
  "id": "tile_12",
  "type": 2,
  "col": 1, "row": 5,
  "w": 1,   "h": 2,
  "props": { "label": "SOH", "value": 94, "unit": "%", "min": 0, "max": 100 }
}
```

### Grid Specification

| Property     | Value     |
|--------------|-----------|
| Screen       | 1024 × 600 px |
| Columns      | 4         |
| Rows         | 6         |
| Column width | 246 px    |
| Row height   | 91 px     |
| Gap          | 8 px      |
| Padding X    | 8 px      |
| Padding Y    | 7 px      |

### Current Layout (11 tiles)

```
Col:  1           2           3           4
     ┌───────────────────────┬───────────┬───────────┐  Row 1
     │                       │           │           │
     │      tile_1           │  tile_2   │  tile_3   │  Row 2
     │   TileType1 (2×3)     │ TileType2 │ TileType3 │
     │                       ├───────────┼───────────┤  Row 3
     ├───────────┬───────────┤  tile_4   │  tile_5   │
     │  tile_7   │  tile_8   │ TileType4 │ TileType5 │  Row 4
     │ TileType3 │ TileType2 ├───────────┼───────────┤
     │           │           │  tile_6   │  tile_9   │  Row 5
     ├───────────┼───────────┤ TileType6 │ TileType5 │
     │  tile_10  │  tile_11  │           │           │  Row 6
     │ TileType4 │ TileType4 │           │           │
     └───────────┴───────────┴───────────┴───────────┘
```

---

## 8. TileType Component Reference

### TileType1 — Live Graph Tile
- **Grid size:** w=2, h=3 → **500 × 289 px**
- **Use for:** Speed, voltage, current, temperature
- **Sections:** Header | Line Graph (Y axis + SVG + X time axis) | Range bar (MIN──●──MAX)
- **Graph:** Dashed grid, gradient fill area, live scrolling line, glowing live dot, floating value pill
- **Alert:** Range bar dot turns red at ≤15% or ≥85%
- **Props:** `label`, `value`, `unit`, `min`, `max`, `history`

### TileType2 — Circular Ring Tile
- **Grid size:** w=1, h=2 → **246 × 190 px**
- **Use for:** Battery SOC, State of Health, charge level
- **Sections:** Header | 270° arc ring with value inside | MIN / MAX footer
- **Ring:** 20px thick stroke, gap at bottom (7:30→4:30), color: green→amber→red
- **Alert:** Ring pulses + outer glow at ≤15% or ≥85%
- **Props:** `label`, `value`, `unit`, `min`, `max`

### TileType3 — Progress Bar Tile
- **Grid size:** w=1, h=2 → **246 × 190 px**
- **Use for:** Throttle, power output, SOC
- **Sections:** Header | Big value + unit | Thick horizontal bar (18px) + MIN/MAX
- **Bar colors:** Green (normal) → Amber (60%+) → Red (85%+)
- **Alert:** Bar pulses + glows at ≤15% or ≥85%
- **Props:** `label`, `value`, `unit`, `min`, `max`

### TileType4 — Status + Number Tile
- **Grid size:** w=1, h=2 → **246 × 190 px**
- **Use for:** BMS status, ESP32 connection, brake/cruise/regen state
- **Sections:** Header | Status dot + ON/OFF text + Big number + unit
- **ON:** Green dot with pulsing ring animation
- **OFF:** Red static dot
- **Accepted status:** `true/false`, `"ON"/"OFF"/"CONNECTED"/"ACTIVE"/"ENABLED"/"OK"`
- **Props:** `label`, `value`, `unit`, `status`

### TileType5 — Hero Number Tile
- **Grid size:** w=1, h=2 → **246 × 190 px**
- **Use for:** Odometer, Distance to Empty, trip distance
- **Sections:** Header | Very large number (64px) | Unit + accent gradient underline
- **No alerts** — purely informational
- **Props:** `label`, `value`, `unit`

### TileType6 — Drive Mode Tile
- **Grid size:** w=1, h=2 → **246 × 190 px**
- **Use for:** Drive mode display
- **Sections:** Header | Active mode badge (pulsing dot + big mode text) | Mode pills (NOR / ECO / HIGH)
- **Modes:** NOR = blue | ECO = green | HIGH = orange
- **Props:** `label`, `mode`

---

## 9. Alert System

All tiles use the same thresholds. No external config required.

| Condition       | Threshold        | Visual Effect                              |
|-----------------|------------------|--------------------------------------------|
| Near minimum    | value ≤ 15% range| Red color + pulse animation + glow         |
| Near maximum    | value ≥ 85% range| Red color + pulse animation + glow         |
| Normal range    | 16% – 84%        | Green / amber, no animation                |

Animations are injected via `<style>` tags inside each component using CSS `@keyframes`. No external CSS file dependency.

---

## 10. File Structure

```
src/
├── main.jsx                      # React entry point
├── App.jsx                       # Root — renders TilesEngine centered
├── index.css                     # Global reset only
│
├── engine/
│   └── TilesEngine.jsx           # Config reader + CSS grid renderer
│
├── config/
│   └── tilesConfig.json          # Layout config — edit to change UI
│
├── components/tiles/
│   ├── TileType1.jsx             # Line graph tile
│   ├── TileType2.jsx             # Circular ring tile
│   ├── TileType3.jsx             # Progress bar tile
│   ├── TileType4.jsx             # Status + number tile
│   ├── TileType5.jsx             # Hero number tile
│   └── TileType6.jsx             # Drive mode tile
│
├── store/
│   └── useVehicleStore.js        # Zustand — live telemetry + history
│
├── api/
│   ├── apiClient.js              # Axios REST client (GET /api/bms)
│   └── websocket.js              # Socket.IO WebSocket manager
│
├── hooks/
│   └── useCountUp.js             # Animated number count-up hook
│
└── utils/
    └── vehicleDetection.js       # Vehicle ID resolution utility
```

---

## 11. What is Done vs Pending

### Done
- [x] All 6 TileType components designed and built
- [x] Config-driven TilesEngine with CSS grid layout
- [x] tilesConfig.json with 11 tiles placed on grid
- [x] Zustand store with all telemetry fields
- [x] WebSocket manager (Socket.IO, auto-reconnect)
- [x] REST API client for initial snapshot
- [x] History tracking for speed and throttle (2hr rolling window)
- [x] Alert system (pulse + glow at limits)
- [x] App renders correctly on 7-inch display

### Pending
- [ ] Wire live store data to tile props in tilesConfig (parameter binding)
- [ ] Multiple layout presets (e.g. Charging view, Riding view, Parked view)
- [ ] Layout switching UI
- [ ] History tracking for additional fields (voltage, current, temperature)
- [ ] Test with real ESP32 hardware data

---

## 12. Environment Variables

| Variable        | Default                    | Description               |
|-----------------|----------------------------|---------------------------|
| `VITE_API_URL`  | `http://localhost:5000/api` | REST API base URL         |
| `VITE_WS_URL`   | `http://localhost:5000`     | WebSocket server URL      |

Set in `.env` file at project root.

---

## 13. Running the Dashboard

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production (Pi deployment)
npm run build
npm run preview
```

Dev server runs at `http://localhost:5173`
