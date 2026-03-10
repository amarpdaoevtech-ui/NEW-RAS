# System Specification Document: Firmware Version v2

This document serves as the master technical specification for the **EV Data Logger System (Firmware v2)**. It outlines the hardware inventory, software architecture, and communication protocols currently implemented in the Raspberry Pi setup.

---

## 1. System Architecture Overview

The system uses a **Raspberry Pi 4 Model B** as the central processing unit (Master), with an **ESP32** acting as a real-time sensor hub and secondary controller (Slave). The system monitors battery health (BMS), motor performance, and environmental sensors.

---

## 2. Hardware Inventory

### 2.1 Computing & Control
| Component | Specification | Role |
| :--- | :--- | :--- |
| **Main Controller** | Raspberry Pi 4 Model B | System Master, API Server, Data Logging |
| **Sensor Hub** | ESP32 Dev Board (CP2102) | Real-time sensor processing (Speed/Throttle) |
| **Operating System** | Raspbian 64-bit | Core OS for Raspberry Pi |

### 2.2 Energy & Power Management
| Component | Specification | Notes |
| :--- | :--- | :--- |
| **BMS** | JBD (Jiabaida) SP24s004-K V1.3 | 24s LiFePO4 (3.2V), 50A |
| **Power Protection** | Waveshare UPS HAT (E) | Provides battery backup and power monitoring |

### 2.3 Drive Train
| Component | Specification | Details |
| :--- | :--- | :--- |
| **Motor** | BLDC Hub Motor | High-efficiency propulsion |
| **Motor Controller** | Lingbo LBMC072182HJ3AEU-M23 | SN: 72V 202201210133 |

### 2.4 Sensor Suite
| Sensor | type | Role |
| :--- | :--- | :--- |
| **Vibration** | ADXL345 (3-Axis Accelerometer) | Impact and motion detection |
| **Environmental** | BME280 | Temperature, Pressure, and Humidity |
| **Speed/Hall** | Integrated in Hub Motor | Fed via ESP32 for high-precision tracking |

---

## 3. Communication Protocols

| Interface | Protocol | Participants | Configuration |
| :--- | :--- | :--- | :--- |
| **BMS Link** | RS485 | Pi <-> JBD BMS | 9600 Baud, Modbus/DAO Frame |
| **Internal Bus** | I2C | Pi <-> ESP32 | Address: `0x08` |
| **Power Monitor**| I2C | Pi <-> UPS HAT | Address: `0x2d` |
| **Sensor Link** | I2C | ESP32 <-> Sensors | Local bus on ESP32 |
| **User Interface**| WebSockets | Backend <-> Frontend | Socket.IO (Real-time stream) |

---

## 4. Software Technical Stack

### 4.1 Backend (Service Layer)
- **Runtime**: Python 3.10+
- **Framework**: Flask (Core API), Flask-SocketIO (Real-time events)
- **Library Dependencies**:
    - `pyserial`: Serial communication with BMS.
    - `smbus2`: I2C communication with ESP32 and UPS HAT.
    - `eventlet`: Concurrent networking for high-frequency data streams.
- **Persistence**: 
    - `data/odometer.json`: Persistent distance tracking.
    - `config/bike_models.json`: Configuration-driven design parameters.

### 4.2 Frontend (Presentation Layer)
- **Runtime**: Node.js (Vite Build System)
- **Framework**: React 19 (Functional Components)
- **Styling**: Tailwind CSS
- **Features**: Dynamic tile mapping, theme switching (Dark/Light), real-time gauges.

---

## 5. System Configuration (Firmware v2)

The system is designed to be **Zero-Hardcoding Ready**. Key parameters for the "v2" vehicle model are defined in the backend configuration:

- **BMS Protocol**: RS485 (JBD Specific frame decoding)
- **Voltage Range**: Optimized for 72V Nominal (LiFePO4 24s)
- **Update Frequency**:
    - Telemetry (Speed/Throttle): 10Hz (Every 100ms)
    - Battery/BMS: 1Hz - 2Hz
    - Environment/UPS: Polled every 5 seconds

---
*Created for: DAO EV TECH - System Administration*
