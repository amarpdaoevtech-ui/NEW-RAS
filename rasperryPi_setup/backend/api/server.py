from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
import time
from config.settings import config

class APIServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Shared data structure
        self.bms_data = {
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
            "speed_kmph": 0.0,
            "speed_raw": 0,
            "speed_mode": "Low",
            "throttle": 0.0,
            "brake": 0,
            "cruise": 0,
            "esp32_connected": False,
            "pi_battery": {"percent": 0, "state": "Unknown", "voltage_mv": 0},
            "dte": 0.0,
            "dte_avg_consumption": 0.0,
            "dte_confidence": "LOW",
            "regen_active": False,
            "total_distance": 0.0,
            "current_ride_distance": 0.0
        }
        self.data_lock = threading.Lock()

    def update_data(self, key, value=None):
        with self.data_lock:
            if isinstance(key, dict):
                self.bms_data.update(key)
            else:
                self.bms_data[key] = value
            self.bms_data["last_update"] = time.time()

    def emit_update(self):
        with self.data_lock:
            self.socketio.emit('bms_update', self.bms_data)

api_server = APIServer()
app = api_server.app
socketio = api_server.socketio
