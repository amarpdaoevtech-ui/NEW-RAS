
import os
import json
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class PersistentOdometer:
    def __init__(self, storage_path='data/odometer.json'):
        self.storage_path = storage_path
        self.total_distance_km = 0.0
        self.last_update_time = time.time()
        self.lock = Lock()
        self.load()

    def load(self):
        """Load odometer value from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.total_distance_km = data.get('total_distance_km', 0.0)
                    logger.info(f"Loaded odometer: {self.total_distance_km:.2f} km")
            else:
                logger.info("No odometer file found, starting from 0.0 km")
                self.save()
        except Exception as e:
            logger.error(f"Error loading odometer: {e}")

    def save(self):
        """Save odometer value to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({'total_distance_km': self.total_distance_km}, f)
        except Exception as e:
            logger.error(f"Error saving odometer: {e}")

    def update(self, speed_kmph, time_delta_seconds):
        """Update odometer based on speed and time"""
        with self.lock:
            if speed_kmph > 0 and time_delta_seconds > 0:
                # distance = speed (km/h) * time (h)
                distance_increment = speed_kmph * (time_delta_seconds / 3600.0)
                
                # Sanity check: limit impossible jumps (e.g. > 200 km/h avg)
                if distance_increment < (200 * (time_delta_seconds / 3600.0)):
                    self.total_distance_km += distance_increment
                    
                    # Save periodically (e.g. every 0.1 km or every minute)
                    # For now, we rely on the caller to call save() periodically to avoid excessive disk writes
                else:
                    logger.warning(f"Ignored large distance jump: {distance_increment:.4f} km (speed={speed_kmph})")
            
            return self.total_distance_km

    def get_distance(self):
        with self.lock:
            return self.total_distance_km
