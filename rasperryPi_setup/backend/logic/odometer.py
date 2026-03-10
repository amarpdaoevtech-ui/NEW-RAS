import os
import json
import time
from threading import Lock
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PersistentOdometer:
    """
    Persistent odometer that survives power cycles.
    """
    def __init__(self, storage_path='data/odometer.json'):
        self.storage_path = storage_path
        self.total_distance_km = 0.0       # Lifetime odometer (persisted)
        self.session_distance_km = 0.0     # This ride since boot (volatile)
        self.last_update_time = time.time()
        self.lock = Lock()
        self.load()

    def load(self):
        """Load total odometer value from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.total_distance_km = data.get('total_distance_km', 0.0)
                    logger.info(f"✅ Loaded odometer: {self.total_distance_km:.2f} km")
            else:
                logger.info("No odometer file found, starting from 0.0 km")
                self.save()
        except Exception as e:
            logger.error(f"Error loading odometer: {e}")
        self.session_distance_km = 0.0

    def save(self):
        """Save total odometer value to disk."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({'total_distance_km': self.total_distance_km}, f)
        except Exception as e:
            logger.error(f"Error saving odometer: {e}")

    def update(self, speed_kmph, time_delta_seconds):
        """Update both total and session odometer."""
        with self.lock:
            if speed_kmph > 0 and time_delta_seconds > 0:
                distance_increment = speed_kmph * (time_delta_seconds / 3600.0)
                max_possible = 200 * (time_delta_seconds / 3600.0)
                if distance_increment < max_possible:
                    self.total_distance_km += distance_increment
                    self.session_distance_km += distance_increment
                else:
                    logger.warning(f"Ignored large distance jump: {distance_increment:.4f} km")
            return self.total_distance_km, self.session_distance_km

    def get_distance(self):
        return self.total_distance_km

    def get_session_distance(self):
        return self.session_distance_km

    def get_both(self):
        with self.lock:
            return self.total_distance_km, self.session_distance_km
