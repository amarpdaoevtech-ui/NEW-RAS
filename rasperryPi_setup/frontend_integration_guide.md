# Frontend Integration Guide: EV Data Logger System

This document provides all the necessary technical information for the frontend intern to implement the proposed **Modular EV Data Logger Dashboard Framework (MEDDF)**. It details the current system architecture, tech stack, API communication, and data structures.

---

## 1. System Overview & Architecture

The system follows a classic **Client-Server Architecture** designed for real-time telemetry.

- **Backend**: Python-based service handling serial/I2C sensor data and serving it via REST and WebSockets.
- **Frontend**: React-based SPA (Single Page Application) that visualizes data in real-time.
- **Communication Protocol**:
    - **REST API**: Used for initial configuration, historical data, and health checks.
    - **WebSockets (Socket.IO)**: Used for high-frequency, real-time telemetry updates.

---

## 2. Technical Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: Flask
- **Real-time Engine**: Flask-SocketIO (using Gevent or Eventlet)
- **Primary Port**: `5000`
- **Host**: `0.0.0.0` (accessible from any device on the network)

### Frontend (Current Setup)
- **Framework**: React 19 (Functional Components, Hooks)
- **Build Tool**: Vite (extremely fast development and bundling)
- **Styling**: Tailwind CSS 3.4
- **State Management**: Context API (Proposed: Zustand)
- **Icons**: Lucide React
- **WebSocket Client**: socket.io-client
- **Dev Port**: `5173`

---

## 3. Communication Details

### 3.1 REST API Endpoints

The backend provides several key endpoints for data retrieval:

| Endpoint | Method | Description | Sample Response |
| :--- | :--- | :--- | :--- |
| `/api/bms` | `GET` | Current real-time state snapshot | `{ "voltage": 72.4, "soc": 85, ... }` |
| `/api/config` | `GET` | Active bike model & display settings | `{ "model": "703-O", "parameters": { ... } }` |
| `/api/history` | `GET` | Recent logs for charts (params: `hours`, `limit`) | `[ { "timestamp": ..., "speed_kmph": 45 }, ... ]` |
| `/api/health` | `GET` | Backend system status and last update time | `{ "status": "ok", "connected": true }` |

### 3.2 WebSocket Interface (Socket.IO)

Real-time data is streamed via the `bms_update` event.

- **Event Name**: `bms_update`
- **Data Type**: Full JSON Object (State Sync)
- **Example Usage**:
```javascript
import { io } from 'socket.io-client';

const socket = io('http://<PI_IP_ADDRESS>:5000');
socket.on('bms_update', (data) => {
    console.log("New Telemetry Data:", data);
});
```

---

## 4. Data Model & Parameters

The following parameters are broadcast from the backend and should be mapped to the UI tiles.

### 4.1 Primary Telemetry (BMS)
| Parameter | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `voltage` | `float` | Volts (V) | Total pack voltage |
| `current` | `float` | Amperes (A) | Real-time current (negative for discharge) |
| `power` | `float` | Watts (W) | Calculated power (V * A) |
| `soc` | `int` | Percentage (%) | State of Charge |
| `soh` | `int` | Percentage (%) | State of Health |
| `temperature` | `float` | °C | Average battery temperature |
| `temperatures` | `Array` | °C | List of 5 individual temperature sensors |
| `charge_cycles`| `int` | Count | Total battery charge cycles |

### 4.2 Ride Metrics (Speed/Distance)
| Parameter | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `speed_kmph` | `float` | km/h | Current vehicle speed |
| `speed_mode` | `string` | - | Operating mode (e.g., "Low", "Mid", "High") |
| `throttle` | `float` | % | Throttle input position |
| `total_distance` | `float` | km | Cumulative Odometer (saved in `odometer.json`) |
| `current_ride_distance` | `float` | km | Distance traveled in the current trip |

### 4.3 Intelligent Calculations (DTE)
| Parameter | Type | Unit | Description |
| :--- | :--- | :--- | :--- |
| `dte` | `float` | km | Distance to Empty (Remaining Range) |
| `dte_avg_consumption` | `float` | Wh/km | Average energy consumption rate |
| `dte_confidence` | `string` | - | Calculation reliability ("LOW", "MED", "HIGH") |

### 4.4 System & Status
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `connected` | `boolean` | BMS Serial connection status |
| `esp32_connected` | `boolean` | I2C data source (speed sensors) status |
| `last_update` | `float` | Unix timestamp of the last successful data read |
| `pi_battery` | `Object` | Status of the Raspberry Pi's own battery (percent, state, voltage_mv) |

---

## 5. Data Frequencies

To optimize rendering, be aware of the internal backend update rates:

- **Speed/Throttle/Mode**: Updated every **100ms (10Hz)**. UI should be smooth.
- **BMS (Voltage/SOC/Current)**: Updated as soon as serial data arrives (typically **~500ms - 1s**).
- **Pi Battery Status**: Updated every **5 seconds**.
- **Odometer Persistence**: Written to disk every **30 seconds**.

---

## 6. Guidance for Implementation (MEDDF)

1. **Configuration-Driven**: Use the `/api/config` response to decide which tiles to show. Do not hardcode "Scooter A" or "Bike B" designs.
2. **Selective Subscription**: Use a state manager (like **Zustand**) to ensure that updating `speed_kmph` does not re-render the `temperature` tile.
3. **Mocking**: For development, you can create a local JSON file that mimics the `bms_update` object to test UI logic without the hardware.
4. **Theme**: Respect the `theme` field in the display config (default is `dark`).

---
*Created for: DAO EV TECH Frontend Internship*
