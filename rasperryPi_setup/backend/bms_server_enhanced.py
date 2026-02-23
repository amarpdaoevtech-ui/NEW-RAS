#!/usr/bin/env python3
"""
DAO BMS Data Server for E-Bike Dashboard
Enhanced version with database logging and configuration support
Optimized for Raspberry Pi 4
"""

import serial
import time
import os
import json
import threading
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from speed_i2c_reader import SpeedI2CReader
from battery_i2c_reader import BatteryI2CReader
from dte_calculator_enhanced import EnhancedDTECalculator
from odometer import PersistentOdometer

# Load environment variables
load_dotenv()

# ================= CONFIGURATION =================
class Config:
    """Configuration manager for bike models"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / 'config' / 'bike_models.json'
        self.load_config()
    
    def load_config(self):
        """Load bike model configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            bike_model = os.getenv('BIKE_MODEL', config_data.get('active_model', '703-O'))
            
            if bike_model not in config_data['models']:
                raise ValueError(f"Bike model '{bike_model}' not found in configuration")
            
            self.model_config = config_data['models'][bike_model]
            self.model_name = bike_model
            
            print(f"✅ Loaded configuration for: {self.model_config['name']}")
            
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            print("Using default configuration for 703-O")
            self._load_default_config()
    
    def _load_default_config(self):
        """Fallback default configuration"""
        self.model_name = "703-O"
        self.model_config = {
            "name": "Scooty Model 703-O (Default)",
            "protocol": "RS485",
            "baud_rate": 9600,
            "serial_ports": ["/dev/ttyAMA0", "/dev/serial0", "/dev/ttyS0"],
            "parameters": {
                "max_voltage": 60.0,
                "max_current": 50.0,
                "max_power": 3000.0,
                "max_speed": 60,
                "max_temperature": 80,
                "battery_capacity": 30,
                "num_temp_sensors": 5
            },
            "bms_config": {
                "frame_start": "0x5B",
                "command_response": "0x82",
                "data_length": 24,
                "crc_type": "modbus",
                "voltage_multiplier": 0.1,
                "current_multiplier": 0.1,
                "temp_offset": -40
            },
            "display": {
                "show_temperature": True,
                "show_voltage": True,
                "show_current": True,
                "show_power": True,
                "show_soc": True,
                "show_soh": True,
                "show_speed": False,
                "theme": "dark"
            }
        }
    
    def get_serial_ports(self):
        """Get serial port configuration"""
        override_port = os.getenv('SERIAL_PORT')
        if override_port:
            return [override_port]
        return self.model_config['serial_ports']
    
    def get_baud_rate(self):
        """Get baud rate"""
        override_baud = os.getenv('BAUD_RATE')
        if override_baud:
            return int(override_baud)
        return self.model_config['baud_rate']
    
    def get_parameters(self):
        """Get bike parameters"""
        return self.model_config['parameters']
    
    def get_bms_config(self):
        """Get BMS configuration"""
        return self.model_config['bms_config']
    
    def get_display_config(self):
        """Get display configuration"""
        return self.model_config['display']

# Initialize configuration
config = Config()

# ================= DATABASE SETUP =================
class Database:
    """Database manager for BMS data logging"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / os.getenv('DB_PATH', 'data/bms_data.db')
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        self.log_interval = int(os.getenv('DB_LOG_INTERVAL', 5))
        self.last_log_time = 0
    
    def init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create BMS data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bms_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    bike_model TEXT,
                    temperature REAL,
                    voltage REAL,
                    current REAL,
                    power REAL,
                    soc INTEGER,
                    soh INTEGER,
                    battery_capacity INTEGER,
                    charge_cycles INTEGER,
                    charge_current REAL,
                    remaining_time REAL,
                    status TEXT,
                    temp_sensor_1 REAL,
                    temp_sensor_2 REAL,
                    temp_sensor_3 REAL,
                    temp_sensor_4 REAL,
                    temp_sensor_5 REAL
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON bms_logs(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
            print(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def log_data(self, data):
        """Log BMS data to database"""
        try:
            current_time = time.time()
            
            # Only log at specified interval
            if current_time - self.last_log_time < self.log_interval:
                return
            
            self.last_log_time = current_time
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            temps = data.get('temperatures', [0, 0, 0, 0, 0])
            while len(temps) < 5:
                temps.append(0)
            
            cursor.execute('''
                INSERT INTO bms_logs (
                    bike_model, temperature, voltage, current, power,
                    soc, soh, battery_capacity, charge_cycles,
                    charge_current, remaining_time, status,
                    temp_sensor_1, temp_sensor_2, temp_sensor_3,
                    temp_sensor_4, temp_sensor_5
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.model_name,
                data.get('temperature', 0),
                data.get('voltage', 0),
                data.get('current', 0),
                data.get('power', 0),
                data.get('soc', 0),
                data.get('soh', 0),
                data.get('battery_capacity', 0),
                data.get('charge_cycles', 0),
                data.get('charge_current', 0),
                data.get('remaining_time', 0),
                data.get('status', 'Unknown'),
                temps[0], temps[1], temps[2], temps[3], temps[4]
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Database logging error: {e}")
    
    def get_recent_logs(self, hours=24, limit=1000):
        """Get recent logs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT * FROM bms_logs 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (cutoff_time, limit))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
            return []
    
    def cleanup_old_data(self):
        """Remove old data based on retention policy"""
        try:
            retention_days = int(os.getenv('DATA_RETENTION_DAYS', 30))
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            cursor.execute('DELETE FROM bms_logs WHERE timestamp < ?', (cutoff_date,))
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted > 0:
                print(f"🗑️ Cleaned up {deleted} old records")
            
        except Exception as e:
            print(f"❌ Database cleanup error: {e}")

# Initialize database
db = Database()

# Initialize Enhanced DTE Calculator (Industry-competitive algorithms)
# Battery capacity for 703-O: 79V × 30Ah = 2370 Wh
dte_calc = EnhancedDTECalculator(
    db_path=str(Path(__file__).parent.parent / os.getenv('DB_PATH', 'data/bms_data.db')),
    battery_capacity_wh=2370,  # 79V × 30Ah
    nominal_voltage=79.0
)

# Initialize Persistent Odometer
odometer = PersistentOdometer(
    storage_path=str(Path(__file__).parent / 'data' / 'odometer.json')
)

# ================= LOGGING SETUP =================
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / os.getenv('LOG_FILE', 'bms_server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ================= SHARED DATA =================
bms_data = {
    "temperature": 0.0,
    "temperatures": [0, 0, 0, 0, 0],
    "voltage": 0.0,
    "current": 0.0,
    "power": 0.0,
    "soc": 0,
    "soh": 0,
    "battery_capacity": 0,
    "charge_cycles": 0,
    "charge_current": 0.0,
    "remaining_time": 0.0,
    "status": "Initializing...",
    "status_flags": [],
    "last_update": 0,
    "connected": False,
    "bike_model": config.model_name,
    "config": config.get_parameters(),
    # Speed & ESP32 Data
    "speed_kmph": 0.0,
    "speed_raw": 0,
    "speed_mode": "Low",
    "throttle": 0.0,
    "brake": 0,
    "cruise": 0,
    "undervoltage": 0,
    "overtemp": 0,
    "speed_limit": 0,
    "esp32_connected": False,
    "pi_battery": {
        "percent": 0,
        "state": "Unknown",
        "voltage_mv": 0
    },
    # DTE Data (Enhanced)
    "dte": 0.0,
    "dte_avg_consumption": 0.0,
    "dte_confidence": "LOW",  # NEW: Confidence level (LOW, MEDIUM, HIGH)
    "regen_active": False,
    "session_id": None,
    "total_distance": 0.0
}
data_lock = threading.Lock()

# ================= FLASK APP =================
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ================= BMS PROTOCOL =================
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
        logger.warning("Invalid DAO payload length")
        return

    bms_config = config.get_bms_config()
    
    bat_cap = u16(payload[0], payload[1])
    charge_cnt = u16(payload[2], payload[3])
    voltage = u16(payload[4], payload[5]) * bms_config['voltage_multiplier']
    chg_cur = u16(payload[6], payload[7]) * bms_config['current_multiplier']
    dchg_cur = u16(payload[8], payload[9]) * bms_config['current_multiplier']
    soc = payload[10]
    health = payload[11]
    status = u16(payload[12], payload[13])
    rem_time = payload[14] * 0.1

    num_sensors = config.get_parameters()['num_temp_sensors']
    temps = [(s8(payload[i]) - 40) for i in range(15, 15 + num_sensors)]
    avg_temp = sum(temps) / len(temps) if temps else 0
    status_desc = decode_bms_status(status)
    
    power = voltage * dchg_cur

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

    logger.info(f"BMS UPDATE: V={voltage:.1f}V I={dchg_cur:.1f}A P={power:.1f}W SoC={soc}% SoH={health}% Temp={avg_temp:.1f}°C Speed={bms_data.get('speed_kmph', 0.0):.1f}km/h")
    
    # Log to database
    db.log_data(bms_data)
    
    # ========== DTE: record sensor inputs (calculation moved to timed task) ==========
    # Detect regen braking (negative current)
    regen_active = dte_calc.detect_regen_braking(dchg_cur)

    # Log sensor reading for later DTE calculation (do not calculate DTE here)
    speed_kmph = bms_data.get("speed_kmph", 0.0)
    throttle_pos = bms_data.get("throttle", 0.0)

    dte_calc.detect_ride_status(speed_kmph, throttle_pos)

    dte_calc.log_sensor_reading(
        voltage_v=voltage,
        current_a=dchg_cur,
        soc_percent=soc,
        soh_percent=health,
        temperature_c=avg_temp,
        speed_kmph=speed_kmph,
        throttle_pos=throttle_pos,
        distance_km=bms_data.get("total_distance", 0.0),
        mode=bms_data.get("speed_mode", "medium").lower()
    )

    # Update regen flag and emit a lightweight update (DTE will be computed on timer)
    with data_lock:
        bms_data["regen_active"] = regen_active

    socketio.emit('bms_update', bms_data)

def find_working_port():
    """Find a working serial port"""
    ports = config.get_serial_ports()
    baud = config.get_baud_rate()
    
    for port in ports:
        if os.path.exists(port):
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1
                )
                logger.info(f"Successfully opened {port} at {baud} baud")
                return ser
            except Exception as e:
                logger.error(f"Failed to open {port}: {e}")
    return None

def bms_reader_thread():
    """Background thread to read BMS data"""
    logger.info("Starting BMS Reader Thread...")
    
    ser = find_working_port()
    
    if not ser:
        logger.error("COULD NOT OPEN ANY SERIAL PORT!")
        with data_lock:
            bms_data["status"] = "Serial port error"
            bms_data["connected"] = False
        return

    logger.info(f"Listening on {ser.port}...")
    
    buffer = bytearray()
    last_data_time = time.time()
    
    try:
        while True:
            b = ser.read(1)
            
            if not b:
                if time.time() - last_data_time > 10:
                    with data_lock:
                        bms_data["status"] = "No data from BMS"
                        bms_data["connected"] = False
                continue
            
            last_data_time = time.time()
            buffer += b

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

            if cmd == 0x82 and length == 0x18:
                if len(data) < 24:
                    continue

                if data[0] != 0x2A or data[1] != 0x16:
                    continue

                payload = data[2:]
                decode_dao_bms_payload(payload)

    except Exception as e:
        logger.error(f"BMS Reader Error: {e}")
        with data_lock:
            bms_data["status"] = f"Error: {str(e)}"
            bms_data["connected"] = False
    finally:
        if ser:
            ser.close()

def i2c_reader_thread():
    """Background thread to read speed and battery data via I2C"""
    logger.info("Starting I2C Reader Thread...")
    
    speed_reader = SpeedI2CReader()
    battery_reader = BatteryI2CReader()
    
    last_loop_time = time.time()
    last_valid_i2c = time.time()
    last_emit_time = 0  # Track last socketio emit time for continuous updates
    
    while True:
        try:
            current_time = time.time()
            time_delta = current_time - last_loop_time
            last_loop_time = current_time
            
            # Read Speed Data
            spd_data = speed_reader.read_data()
            should_emit = False  # Flag to control when to emit
            
            if spd_data:
                # NEW DATA RECEIVED
                last_valid_i2c = current_time
                speed_kmph = spd_data["speed_kmph"]
                
                # Update persistent odometer
                total_distance = odometer.update(speed_kmph, time_delta)
                
                with data_lock:
                    bms_data["speed_kmph"] = speed_kmph
                    bms_data["throttle"] = spd_data.get("throttle", 0.0)
                    bms_data["speed_mode"] = spd_data["mode"]
                    bms_data["brake"] = spd_data["brake"]
                    bms_data["esp32_connected"] = True
                    bms_data["last_update"] = time.time()
                    bms_data["total_distance"] = round(total_distance, 2)  # Persist distance
                
                # ✅ Log speed activity for debugging
                if speed_kmph > 0:
                    logger.debug(f"SPD_SYNC: {speed_kmph} kmh | ODO: {total_distance} km")
                
                should_emit = True  # Always emit when we get new data
                
            else:
                # NO NEW DATA (duplicate sequence number or no I2C data)
                # ✅ PATIENT TIMEOUT: Only reset to 0 if no data for 10 seconds
                if current_time - last_valid_i2c > 10.0:
                    with data_lock:
                        if bms_data["speed_kmph"] > 0:
                            logger.warning("Speed signal lost! Resetting to 0.")
                        bms_data["speed_kmph"] = 0.0
                        bms_data["throttle"] = 0.0
                        bms_data["esp32_connected"] = False
                    
                    should_emit = True  # Emit the reset state
                
                # ✅ CRITICAL FIX: Even if we got duplicate sequence numbers,
                # emit the current speed/throttle values every 100ms to keep display updated
                elif current_time - last_emit_time >= 0.1:
                    should_emit = True  # Emit current state for continuous display
            
            # Emit socketio update if needed
            if should_emit:
                socketio.emit('bms_update', bms_data)
                last_emit_time = current_time
            
            # Read Battery Data (less frequent)
            if int(time.time()) % 2 == 0:
                bat_data = battery_reader.read_data()
                if bat_data:
                    with data_lock:
                        bms_data["pi_battery"] = {
                            "percent": bat_data["pi_battery_percent"],
                            "state": bat_data["state"],
                            "voltage_mv": bat_data["battery_voltage_mv"]
                        }
                    
                    # Emit update for battery
                    socketio.emit('bms_update', bms_data)
            
        except Exception as e:
            logger.error(f"I2C Reader Error: {e}")
            
        time.sleep(0.1) # Loop every 100ms (reduced from 50ms to match ESP32 update rate)

# ================= REST API ENDPOINTS =================

@app.route('/api/bms', methods=['GET'])
def get_bms_data():
    """Get current BMS data"""
    with data_lock:
        return jsonify(bms_data)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get bike configuration"""
    return jsonify({
        "model": config.model_name,
        "name": config.model_config['name'],
        "parameters": config.get_parameters(),
        "display": config.get_display_config()
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical data"""
    hours = request.args.get('hours', default=24, type=int)
    limit = request.args.get('limit', default=1000, type=int)
    
    logs = db.get_recent_logs(hours=hours, limit=limit)
    return jsonify(logs)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    with data_lock:
        return jsonify({
            "status": "ok",
            "connected": bms_data["connected"],
            "last_update": bms_data["last_update"],
            "bike_model": config.model_name
        })

@app.route('/api/dte', methods=['GET'])
def get_dte():
    """Get Distance-to-Empty estimation and consumption data (Enhanced)"""
    with data_lock:
        return jsonify({
            "dte": bms_data.get("dte", 0),
            "dte_avg_consumption": bms_data.get("dte_avg_consumption", 0),
            "dte_confidence": bms_data.get("dte_confidence", "LOW"),  # NEW
            "regen_active": bms_data.get("regen_active", False),
            "total_distance": bms_data.get("total_distance", 0),  # NEW
            "soc": bms_data.get("soc", 0),
            "soh": bms_data.get("soh", 0),
            "temperature": bms_data.get("temperature", 0),
            "voltage": bms_data.get("voltage", 0),
            "current": bms_data.get("current", 0),
            "speed_kmph": bms_data.get("speed_kmph", 0)
        })

@app.route('/api/dte/session', methods=['GET'])
def get_dte_session():
    """Get current DTE session statistics"""
    stats = dte_calc.get_session_stats()
    return jsonify(stats)

@app.route('/api/dte/session/start', methods=['POST'])
def start_dte_session():
    """Start a new DTE calculation session"""
    try:
        initial_soc = request.json.get('initial_soc', bms_data.get('soc', 100))
        bike_model = request.json.get('bike_model', config.model_name)
        riding_mode = request.json.get('mode', 'medium')
        
        session_id = dte_calc.start_session(initial_soc, bike_model, riding_mode)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "initial_soc": initial_soc
        })
    except Exception as e:
        logger.error(f"Error starting DTE session: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/dte/session/end', methods=['POST'])
def end_dte_session():
    """End current DTE session and get summary"""
    try:
        final_soc = request.json.get('final_soc', bms_data.get('soc', 0))
        final_temperature = request.json.get('temperature', bms_data.get('temperature', None))
        
        summary = dte_calc.end_session(final_soc, final_temperature)
        
        return jsonify({
            "success": True,
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Error ending DTE session: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

# ================= WEBSOCKET EVENTS =================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected')
    with data_lock:
        emit('bms_update', bms_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

@socketio.on('request_data')
def handle_request():
    """Handle manual data request"""
    with data_lock:
        emit('bms_update', bms_data)

# ================= BACKGROUND TASKS =================

def cleanup_task():
    """Periodic cleanup task"""
    while True:
        time.sleep(86400)  # Run daily
        db.cleanup_old_data()


def dte_update_task():
    """Timed DTE calculation task with enhanced algorithm support."""
    interval = int(os.getenv('DTE_CALC_INTERVAL', 3))
    logger.info(f"Starting Enhanced DTE update task, interval={interval}s")
    while True:
        try:
            with data_lock:
                soc = bms_data.get('soc', 0)
                soh = bms_data.get('soh', 100)
                temp = bms_data.get('temperature', 0)
                speed = bms_data.get('speed_kmph', 0.0)
                throttle = bms_data.get('throttle', 0.0)  # NEW: Pass throttle for instant power
                mode = bms_data.get('speed_mode', 'medium').lower()

            # Calculate DTE using the enhanced calculator
            # Returns: (dte_km, consumption, regen_active, confidence)
            result = dte_calc.calculate_dte(
                soc_percent=soc,
                soh_percent=soh,
                temperature_c=temp,
                speed_kmph=speed,
                throttle_pct=throttle,  # NEW: Instant power factor
                mode=mode
            )
            
            # Handle both old 3-tuple and new 4-tuple returns for compatibility
            if len(result) == 4:
                dte_km, avg_consumption, regen, confidence = result
            else:
                dte_km, avg_consumption, regen = result
                confidence = 'MEDIUM'

            with data_lock:
                bms_data['dte'] = round(dte_km, 2)
                bms_data['dte_avg_consumption'] = round(avg_consumption, 2)
                bms_data['regen_active'] = regen
                bms_data['dte_confidence'] = confidence  # NEW: Confidence level
                bms_data['session_id'] = dte_calc.session_id
                bms_data['total_distance'] = round(dte_calc.total_distance, 2)

            # Emit DTE update to clients
            socketio.emit('bms_update', bms_data)

        except Exception as e:
            logger.error(f"DTE update task error: {e}")

        time.sleep(interval)


# ================= MAIN =================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DAO BMS DATA SERVER - ENHANCED VERSION")
    print("=" * 60)
    print(f"📋 Bike Model: {config.model_config['name']}")
    print(f"🔧 Protocol: {config.model_config['protocol']}")
    print(f"💾 Database: {db.db_path}")
    print("=" * 60)
    
    # Start BMS reader thread
    reader_thread = threading.Thread(target=bms_reader_thread, daemon=True)
    reader_thread.start()
    
    # Start cleanup task
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    
    # Start I2C reader thread (Speed & Pi Battery)
    i2c_thread = threading.Thread(target=i2c_reader_thread, daemon=True)
    i2c_thread.start()

    # Start timed DTE update task (computes DTE every few seconds)
    dte_thread = threading.Thread(target=dte_update_task, daemon=True)
    dte_thread.start()
    
    # Start Flask server
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', 5000))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    print(f"\n🌐 Starting Web Server on {host}:{port}...")
    print(f"   REST API: http://localhost:{port}/api/bms")
    print(f"   WebSocket: ws://localhost:{port}")
    print("=" * 60)
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)