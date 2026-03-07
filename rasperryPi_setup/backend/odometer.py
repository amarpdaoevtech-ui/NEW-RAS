
import os
import json
import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class PersistentOdometer:
    """
    Persistent odometer that survives power cycles.
    Tracks:
      - total_distance_km : cumulative lifetime odometer (saved to disk)
      - session_distance_km: this boot/ride session only (resets on restart)
    """
    def __init__(self, storage_path='data/odometer.json'):
        self.storage_path = storage_path
        self.total_distance_km = 0.0       # Lifetime odometer (persisted)
        self.session_distance_km = 0.0     # This ride since boot (volatile)
        self.last_update_time = time.time()
        self.lock = Lock()
        self.load()

    def load(self):
        """Load total odometer value from storage. Session always starts at 0."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.total_distance_km = data.get('total_distance_km', 0.0)
                    logger.info(f"✅ Loaded odometer: {self.total_distance_km:.2f} km (session starts at 0.0 km)")
            else:
                logger.info("No odometer file found, starting from 0.0 km")
                self.save()
        except Exception as e:
            logger.error(f"Error loading odometer: {e}")
        # Session ALWAYS resets to zero on boot
        self.session_distance_km = 0.0

    def save(self):
        """Save total odometer value to disk (session distance is NOT saved - intentional)"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({'total_distance_km': self.total_distance_km}, f)
        except Exception as e:
            logger.error(f"Error saving odometer: {e}")

    def update(self, speed_kmph, time_delta_seconds):
        """
        Update both total and session odometer based on speed and elapsed time.
        Returns: (total_distance_km, session_distance_km)
        """
        with self.lock:
            if speed_kmph > 0 and time_delta_seconds > 0:
                # distance = speed (km/h) × time (h)
                distance_increment = speed_kmph * (time_delta_seconds / 3600.0)

                # Sanity check: reject impossible jumps (> 200 km/h equivalent)
                max_possible = 200 * (time_delta_seconds / 3600.0)
                if distance_increment < max_possible:
                    self.total_distance_km += distance_increment
                    self.session_distance_km += distance_increment
                else:
                    logger.warning(
                        f"Ignored large distance jump: {distance_increment:.4f} km "
                        f"(speed={speed_kmph}, delta={time_delta_seconds:.2f}s)"
                    )

            return self.total_distance_km, self.session_distance_km

    def get_distance(self):
        """Returns lifetime total distance (km)"""
        with self.lock:
            return self.total_distance_km

    def get_session_distance(self):
        """Returns this-ride distance since last boot (km)"""
        with self.lock:
            return self.session_distance_km

    def get_both(self):
        """Returns (total_km, session_km) atomically"""
        with self.lock:
            return self.total_distance_km, self.session_distance_km
