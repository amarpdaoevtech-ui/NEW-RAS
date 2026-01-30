#!/usr/bin/env python3
"""
DAO BMS Data Server for E-Bike Dashboard
Reads BMS data via RS-485 and serves it via WebSocket and REST API
Optimized for Raspberry Pi 4
"""

import serial
import time
import os
import json
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# ================= CONFIGURATION =================
POSSIBLE_PORTS = [
    "/dev/ttyAMA0",    # Hardware UART (primary - best choice)
    "/dev/serial0",    # Symlink to primary UART
    "/dev/ttyS0",      # Mini UART (unreliable, avoid)
]
BAUD = 9600

# Shared data structure (thread-safe with lock)
bms_data = {
    "temperature": 0.0,      # Average of 5 sensors
    "temperatures": [0, 0, 0, 0, 0],  # Individual temps
    "voltage": 0.0,
    "current": 0.0,          # Discharge current
    "power": 0.0,            # Calculated: V * I
    "soc": 0,                # State of Charge %
    "soh": 0,                # State of Health %
    "battery_capacity": 0,
    "charge_cycles": 0,
    "charge_current": 0.0,
    "remaining_time": 0.0,
    "status": "Initializing...",
    "status_flags": [],
    "last_update": 0,
    "connected": False
}
data_lock = threading.Lock()

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access
socketio = SocketIO(app, cors_allowed_origins="*")

# =================================================

def crc16_modbus(data: bytes):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF

def u16(lo, hi):
    return (hi << 8) | lo

def s8(v):
    return v - 256 if v > 127 else v

BMS_STATUS_FLAGS = {
    0x0001: "Normal discharge",
    0x0002: "Normal charging",
    0x0004: "Charging saturation protection",
    0x0008: "Battery low voltage protection",
    0x0010: "Overcurrent protection during charging",
    0x0020: "Discharge overcurrent protection",
    0x0040: "Battery overheat protection",
    0x0080: "Battery discharge low temperature protection",
    0x0100: "Battery pack open circuit",
    0x0200: "Discharge short circuit protection",
    0x0400: "Battery overheat protection (secondary)",
    0x0800: "Battery charging low temperature protection",
    0x1000: "Circuit board MOS overheat protection",
    0x2000: "Temperature sensor malfunction",
    0x4000: "Reserved",
    0x8000: "Reserved",
}

def decode_bms_status(status):
    if status == 0x0000:
        return ["Normal / No fault"]
    active = []
    for bit, desc in BMS_STATUS_FLAGS.items():
        if status & bit:
            active.append(desc)
    return active

def decode_dao_bms_payload(payload: bytes):
    """Decode BMS payload and update shared data structure"""
    if len(payload) != 22:
        print("⚠ Invalid DAO payload length")
        return

    bat_cap = u16(payload[0], payload[1])
    charge_cnt = u16(payload[2], payload[3])
    voltage = u16(payload[4], payload[5]) * 0.1
    chg_cur = u16(payload[6], payload[7]) * 0.1
    dchg_cur = u16(payload[8], payload[9]) * 0.1
    soc = payload[10]
    health = payload[11]
    status = u16(payload[12], payload[13])
    rem_time = payload[14] * 0.1

    temps = [(s8(payload[i]) - 40) for i in range(15, 20)]
    avg_temp = sum(temps) / len(temps)
    status_desc = decode_bms_status(status)
    
    # Calculate power (W = V * I)
    power = voltage * dchg_cur

    # Update shared data with lock
    with data_lock:
        bms_data["battery_capacity"] = bat_cap
        bms_data["charge_cycles"] = charge_cnt
        bms_data["voltage"] = round(voltage, 1)
        bms_data["charge_current"] = round(chg_cur, 1)
        bms_data["current"] = round(dchg_cur, 1)
        bms_data["soc"] = soc
        bms_data["soh"] = health
        bms_data["remaining_time"] = round(rem_time, 1)
        bms_data["temperatures"] = [round(t, 1) for t in temps]
        bms_data["temperature"] = round(avg_temp, 1)
        bms_data["power"] = round(power, 2)
        bms_data["status_flags"] = status_desc
        bms_data["status"] = status_desc[0] if status_desc else "Unknown"
        bms_data["last_update"] = time.time()
        bms_data["connected"] = True

    print(f"\n🔋 BMS UPDATE: V={voltage:.1f}V I={dchg_cur:.1f}A P={power:.1f}W SoC={soc}% SoH={health}% Temp={avg_temp:.1f}°C")
    
    # Emit to all connected WebSocket clients
    socketio.emit('bms_update', bms_data)

def find_working_port():
    """Find a working serial port"""
    for port in POSSIBLE_PORTS:
        if os.path.exists(port):
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=BAUD,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1
                )
                print(f"✅ Successfully opened {port}")
                return ser
            except Exception as e:
                print(f"❌ Failed to open {port}: {e}")
    return None

def bms_reader_thread():
    """Background thread to read BMS data"""
    print("📡 Starting BMS Reader Thread...")
    
    ser = find_working_port()
    
    if not ser:
        print("❌ COULD NOT OPEN ANY SERIAL PORT!")
        with data_lock:
            bms_data["status"] = "Serial port error"
            bms_data["connected"] = False
        return

    print(f"📊 Listening on {ser.port} at {BAUD} baud...")
    
    buffer = bytearray()
    last_data_time = time.time()
    
    try:
        while True:
            b = ser.read(1)
            
            if not b:
                # Check for timeout
                if time.time() - last_data_time > 10:
                    with data_lock:
                        bms_data["status"] = "No data from BMS"
                        bms_data["connected"] = False
                continue
            
            last_data_time = time.time()
            buffer += b

            # Sync to frame start
            while buffer and buffer[0] != 0x5B:
                buffer.pop(0)

            if len(buffer) < 9:
                continue

            data_len = buffer[5]
            frame_len = 6 + data_len + 2

            if len(buffer) < frame_len:
                continue

            frame = buffer[:frame_len]
            buffer = buffer[frame_len:]

            body = frame[:-2]
            crc_rx = frame[-2] | (frame[-1] << 8)
            crc_calc = crc16_modbus(body)

            if crc_rx != crc_calc:
                continue

            addr = frame[1]
            inv_addr = frame[2]
            cmd = frame[4]
            length = frame[5]
            data = frame[6:-2]

            if inv_addr != (~addr & 0xFF):
                continue

            # DAO upload response
            if cmd == 0x82 and length == 0x18:
                if len(data) < 24:
                    continue

                if data[0] != 0x2A or data[1] != 0x16:
                    continue

                payload = data[2:]
                decode_dao_bms_payload(payload)

    except Exception as e:
        print(f"❌ BMS Reader Error: {e}")
        with data_lock:
            bms_data["status"] = f"Error: {str(e)}"
            bms_data["connected"] = False
    finally:
        if ser:
            ser.close()

# ============== REST API ENDPOINTS ==============

@app.route('/api/bms', methods=['GET'])
def get_bms_data():
    """Get current BMS data via REST API"""
    with data_lock:
        return jsonify(bms_data)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    with data_lock:
        return jsonify({
            "status": "ok",
            "connected": bms_data["connected"],
            "last_update": bms_data["last_update"]
        })

# ============== WEBSOCKET EVENTS ==============

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('🔌 Client connected')
    with data_lock:
        emit('bms_update', bms_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('🔌 Client disconnected')

@socketio.on('request_data')
def handle_request():
    """Handle manual data request"""
    with data_lock:
        emit('bms_update', bms_data)

# ============== MAIN ==============

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DAO BMS DATA SERVER")
    print("=" * 60)
    
    # Start BMS reader in background thread
    reader_thread = threading.Thread(target=bms_reader_thread, daemon=True)
    reader_thread.start()
    
    # Start Flask server
    print("\n🌐 Starting Web Server...")
    print("   REST API: http://localhost:5000/api/bms")
    print("   WebSocket: ws://localhost:5000")
    print("=" * 60)
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
