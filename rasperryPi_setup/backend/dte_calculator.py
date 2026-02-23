#!/usr/bin/env python3
"""
DTE (Distance-to-Empty) Calculator for EV Scooter
Calculates real-time range based on battery capacity, consumption history, and sensor data
"""
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import logging
import time

# Setup logging
logger = logging.getLogger(__name__)


class DTECalculator:
    """Calculate Distance-to-Empty for EV scooter"""
    
    def __init__(self, db_path='data/bms_data.db', battery_capacity_wh=2370, nominal_voltage=79.0):
        """
        Initialize DTE Calculator
        
        Args:
            db_path: Path to SQLite database
            battery_capacity_wh: Battery capacity in Wh (79V × 30Ah = 2370 Wh for 703-O)
            nominal_voltage: Nominal battery voltage (79V for 703-O)
        """
        self.db_path = db_path
        self.battery_capacity_wh = battery_capacity_wh
        self.nominal_voltage = nominal_voltage
        
        # Session tracking
        self.session_id = None
        self.session_start_time = None
        self.last_distance = 0
        self.last_soc = 100
        self.total_energy_used = 0
        self.total_energy_regenerated = 0
        self.total_distance = 0
        self.is_moving = False
        self.last_speed = 0
        self.last_timestamp = None
        
        # ✅ NEW: Track last power reading time for proper energy integration
        self.last_power_timestamp = None
        
        # calibration factor for current sensor (1.0 = no change)
        self.current_calibration = 1.0
        # session initial soc for calibration
        self.session_initial_soc = None
        
        # Cache for performance
        self.cached_dte = 0
        self.cached_avg_consumption = 0
        self.last_dte_update_time = None
        self.last_dte_value = 0
        self.dte_smoothing_factor = 0.3  # EMA smoothing
        
        # ✅ NEW: Track last consumption log time to avoid duplicate entries
        self.last_consumption_log_time = None
        self.last_consumption_log_distance = 0
        
        # ✅ Automatically initialize database on startup
        self.init_database()

    
    def init_database(self):
        """Initialize database tables for DTE tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create ride_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ride_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    initial_soc INTEGER,
                    final_soc INTEGER,
                    initial_temperature REAL,
                    final_temperature REAL,
                    total_distance REAL DEFAULT 0,
                    total_energy_used REAL DEFAULT 0,
                    total_energy_regenerated REAL DEFAULT 0,
                    avg_consumption REAL DEFAULT 0,
                    bike_model TEXT,
                    riding_mode TEXT
                )
            ''')
            
            # Create consumption_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consumption_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    distance_traveled REAL,
                    energy_used REAL,
                    energy_regenerated REAL,
                    avg_consumption REAL,
                    current_speed REAL,
                    current_soc INTEGER,
                    riding_mode TEXT,
                    FOREIGN KEY (session_id) REFERENCES ride_sessions(session_id)
                )
            ''')
            
            # Create dte_cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dte_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    soc INTEGER,
                    dte REAL,
                    avg_consumption REAL,
                    regen_active INTEGER,
                    speed_kmph REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ DTE database tables initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing DTE database: {e}")
    
    def start_session(self, initial_soc, bike_model="703-O", riding_mode="medium"):
        """Start a new ride session"""
        from uuid import uuid4
        
        try:
            self.session_id = f"ride_{uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
            self.session_start_time = datetime.now()
            self.last_soc = initial_soc
            self.session_initial_soc = initial_soc
            self.total_energy_used = 0
            self.total_energy_regenerated = 0
            self.total_distance = 0
            self.last_distance = 0
            self.last_power_timestamp = None
            self.last_consumption_log_time = None
            self.last_consumption_log_distance = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ride_sessions 
                (session_id, initial_soc, bike_model, riding_mode)
                VALUES (?, ?, ?, ?)
            ''', (self.session_id, initial_soc, bike_model, riding_mode))
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Started session {self.session_id} with SOC={initial_soc}%")
            return self.session_id
        except Exception as e:
            logger.error(f"❌ Error starting session: {e}")
            return None
    
    def detect_regen_braking(self, current_a):
        """Detect if regenerative braking is active (negative current)"""
        return current_a < -2.0  # Threshold: -2A or less
    
    def detect_ride_status(self, speed_kmph, throttle_pos):
        """Detect if bike is in motion"""
        self.is_moving = speed_kmph > 2.0 or throttle_pos > 10
        return self.is_moving
    
    def get_temperature_factor(self, temperature_c):
        """Get efficiency factor based on temperature"""
        if temperature_c < -10:
            return 0.75
        elif temperature_c < 0:
            return 0.85
        elif temperature_c <= 25:
            return 1.0
        elif temperature_c <= 35:
            return 0.95
        else:
            return 0.85  # Heat reduces efficiency
    
    def get_mode_multiplier(self, mode):
        """Get consumption multiplier based on riding mode (speed-dependent)"""
        mode_map = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.4
        }
        return mode_map.get(mode.lower(), 1.0)

    def get_adjusted_capacity(self, soh_percent, temperature_c):
        """Calculate adjusted battery capacity based on SOH and temperature"""
        base_capacity = self.battery_capacity_wh * (soh_percent / 100.0)
        temp_factor = self.get_temperature_factor(temperature_c)
        return base_capacity * temp_factor
    
    def calculate_available_energy(self, soc_percent, soh_percent, temperature_c):
        """
        Calculate available energy using blended SOC and coulomb-count approach.
        
        Returns:
            float: Available energy in Wh
        """
        adjusted_capacity = self.get_adjusted_capacity(soh_percent, temperature_c)
        
        # SOC-based energy
        energy_soc = (soc_percent / 100.0) * adjusted_capacity
        
        # For coulomb-count approximation, use historical data if available
        energy_cc = energy_soc  # Default to SOC-based
        
        try:
            if self.session_id:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT SUM(energy_used) - SUM(energy_regenerated)
                    FROM consumption_history
                    WHERE session_id = ?
                ''', (self.session_id,))
                result = cursor.fetchone()
                conn.close()
                
                if result[0]:
                    energy_used_net = result[0]
                    # Estimate remaining based on initial capacity and consumption
                    energy_cc = adjusted_capacity - energy_used_net
                    energy_cc = max(0, min(energy_cc, adjusted_capacity))
        except Exception as e:
            logger.warning(f"⚠️ Could not get coulomb-count energy: {e}")
        
        # Blend: 60% coulomb-count + 40% SOC-based
        blend_weight_cc = 0.6
        available_energy = (blend_weight_cc * energy_cc) + ((1 - blend_weight_cc) * energy_soc)
        
        return max(available_energy, 0)
    
    def get_moving_average_consumption(self, window_km=25):
        """
        Calculate moving average consumption from recent history
        
        Args:
            window_km: Distance window for moving average (default 25 km)
        
        Returns:
            float: Average consumption in Wh/km, or smart default if insufficient data
        """
        if self.session_id is None:
            # Use a smarter default based on mode
            mode_defaults = {
                'low': 32.0,
                'medium': 36.0,
                'high': 43.0
            }
            return mode_defaults.get('medium', 36.0)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent consumption history, ordered by distance
            cursor.execute('''
                SELECT distance_traveled, energy_used, energy_regenerated 
                FROM consumption_history 
                WHERE session_id = ? 
                ORDER BY distance_traveled DESC 
                LIMIT 100
            ''', (self.session_id,))
            
            data = cursor.fetchall()
            conn.close()
            
            if len(data) < 5:
                # ✅ FIX: Return estimated consumption based on actual energy used
                if len(data) >= 2:
                    rows = [(row[0], row[1], row[2]) for row in data]
                    rows_sorted = sorted(rows, key=lambda x: x[0])
                    first = rows_sorted[0]
                    last = rows_sorted[-1]
                    distance_delta = last[0] - first[0]
                    energy_used_delta = last[1] - first[1]
                    net_energy = energy_used_delta
                    
                    if distance_delta > 0.1:
                        calc_consumption = max(net_energy / distance_delta, 5.0)
                        logger.info(f"📊 Calculated consumption from {len(data)} samples: {calc_consumption:.2f} Wh/km")
                        return calc_consumption
                
                # Fallback: Use battery capacity × calibration factor ÷ typical range
                # For 703-O: use a 65 km typical range → consumption ≈ battery_capacity_wh / 65
                default_consumption = (self.battery_capacity_wh / 65.0) * self.current_calibration
                logger.info(f"⚠️ Low data samples ({len(data)}), using calibrated default: {default_consumption:.2f} Wh/km")
                return default_consumption
            
            # Build sorted list by distance (ascending)
            rows = [(row[0], row[1], row[2]) for row in data]
            rows_sorted = sorted(rows, key=lambda x: x[0])

            if not rows_sorted or len(rows_sorted) < 2:
                return 18.0

            max_dist = rows_sorted[-1][0]
            min_allowed = max(max_dist - window_km, 0)

            # keep entries within window (distance >= min_allowed)
            window_rows = [r for r in rows_sorted if r[0] >= min_allowed]
            if len(window_rows) < 2:
                return 18.0

            first = window_rows[0]
            last = window_rows[-1]

            distance_delta = last[0] - first[0]
            energy_used_delta = last[1] - first[1]
            energy_regen_delta = last[2] - first[2]
            net_energy = energy_used_delta - energy_regen_delta

            if distance_delta > 0.1:
                avg_consumption = net_energy / distance_delta
                logger.debug(f"Moving avg consumption ({window_km} km window): {avg_consumption:.2f} Wh/km")
                return max(avg_consumption, 5.0)

            return 18.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating moving average consumption: {e}")
            return 18.0

    
    def log_sensor_reading(self, voltage_v, current_a, soc_percent, soh_percent, temperature_c, 
                           speed_kmph, throttle_pos, distance_km=None, mode="medium", timestamp=None):
        """
        Log individual sensor reading and update session stats
        
        ✅ FIXED: Properly integrate energy over time intervals
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Auto-start session if needed
            if self.session_id is None and soc_percent > 10:
                self.start_session(soc_percent, riding_mode=mode)
            
            if self.session_id is None:
                return
            
            # ✅ Track distance
            if distance_km is not None:
                distance_delta = distance_km - self.last_distance
                if distance_delta >= 0:
                    self.total_distance += distance_delta
                    self.last_distance = distance_km
            
            # ✅ FIXED: Properly calculate energy used over TIME interval
            # Energy (Wh) = Power (W) × Time (hours)
            current_timestamp = time.time()
            
            if self.last_power_timestamp is not None:
                time_delta_seconds = current_timestamp - self.last_power_timestamp
                time_delta_hours = time_delta_seconds / 3600.0
                
                # Calculate power
                power_w = voltage_v * current_a
                
                # Check for regen
                is_regen = self.detect_regen_braking(current_a)
                
                # Energy = Power × Time (in hours)
                energy_delta_wh = abs(power_w) * time_delta_hours
                
                if is_regen and power_w < 0:
                    self.total_energy_regenerated += energy_delta_wh
                    logger.debug(f"🔋 Regen: +{energy_delta_wh:.4f} Wh")
                elif power_w > 0:
                    self.total_energy_used += energy_delta_wh
                    logger.debug(f"⚡ Discharge: -{energy_delta_wh:.4f} Wh (P={power_w:.1f}W, Δt={time_delta_seconds:.1f}s)")
            
            self.last_power_timestamp = current_timestamp
            
            # ✅ Log consumption entry if distance threshold reached (every 0.5 km)
            if distance_km is not None:
                distance_since_last_log = distance_km - self.last_consumption_log_distance
                
                if distance_since_last_log >= 0.5:  # Log every 500m
                    avg_consumption = self.get_moving_average_consumption()
                    self._log_consumption_entry(
                        self.total_distance,
                        self.total_energy_used,
                        self.total_energy_regenerated,
                        avg_consumption,
                        speed_kmph,
                        soc_percent,
                        mode
                    )
                    self.last_consumption_log_distance = distance_km
                    logger.info(f"📍 Logged consumption: Distance={self.total_distance:.2f}km, Energy={self.total_energy_used:.2f}Wh, Avg={avg_consumption:.2f}Wh/km")
            
            self.last_soc = soc_percent
            self.last_timestamp = timestamp
            
        except Exception as e:
            logger.error(f"❌ Error logging sensor reading: {e}")
    
    def _log_consumption_entry(self, distance_traveled, energy_used, energy_regenerated, 
                               avg_consumption, current_speed, current_soc, riding_mode):
        """Log consumption data point to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO consumption_history 
                (session_id, distance_traveled, energy_used, energy_regenerated, 
                 avg_consumption, current_speed, current_soc, riding_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.session_id, distance_traveled, energy_used, energy_regenerated,
                  avg_consumption, current_speed, current_soc, riding_mode))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error logging consumption entry: {e}")
    
    def calculate_dte(self, soc_percent, soh_percent, temperature_c, speed_kmph, mode="medium"):
        """
        Calculate Distance-to-Empty with smoothing and rate limiting
        
        Returns:
            tuple: (dte_km, avg_consumption_wh_per_km, regen_active)
        """
        # ✅ Freeze DTE when speed < 2 km/h (stationary)
        freeze_speed_threshold = 2.0
        if speed_kmph < freeze_speed_threshold:
            logger.debug(f"DTE frozen: speed={speed_kmph} < {freeze_speed_threshold} km/h")
            return (self.last_dte_value, self.cached_avg_consumption, False)
        
        try:
            # Get average consumption (auto-handles low-data scenarios)
            avg_consumption = self.get_moving_average_consumption()
            
            # Get available energy
            available_energy = self.calculate_available_energy(soc_percent, soh_percent, temperature_c)
            
            # Calculate raw DTE
            if avg_consumption > 0:
                dte_raw = available_energy / avg_consumption
            else:
                dte_raw = 0
            
            # ✅ Rate limiter: max change of 0.5 km per update
            max_change_km_per_update = 0.5
            if self.last_dte_value > 0:
                dte_change = dte_raw - self.last_dte_value
                if abs(dte_change) > max_change_km_per_update:
                    dte_raw = self.last_dte_value + (max_change_km_per_update if dte_change > 0 else -max_change_km_per_update)
                    logger.debug(f"DTE rate limited: change {dte_change:.2f} → {max_change_km_per_update:.2f}")
            
            # ✅ EMA smoothing for UX
            if self.last_dte_value > 0:
                dte_smoothed = (self.dte_smoothing_factor * dte_raw) + ((1 - self.dte_smoothing_factor) * self.last_dte_value)
            else:
                dte_smoothed = dte_raw
            
            # Cap DTE at reasonable maximum (e.g., 150 km for 703-O)
            dte_final = min(dte_smoothed, 150)
            
            # Detect regen
            regen_active = False
            
            # Cache values
            self._cache_dte(dte_final, soc_percent, avg_consumption, regen_active)
            self.last_dte_value = dte_final
            self.cached_dte = dte_final
            self.cached_avg_consumption = avg_consumption
            self.last_dte_update_time = datetime.now()
            
            logger.info(f"Available energy: {available_energy:.2f} Wh")
            logger.info(f"Average consumption: {avg_consumption:.2f} Wh/km")
            logger.info(f"Calculated DTE: {dte_final:.2f} km")
            
            return (dte_final, avg_consumption, regen_active)
            
        except Exception as e:
            logger.error(f"❌ Error calculating DTE: {e}")
            return (self.last_dte_value, self.cached_avg_consumption, False)
    
    def _cache_dte(self, dte, soc, avg_consumption, regen_active):
        """Cache DTE value in database for dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dte_cache (soc, dte, avg_consumption, regen_active)
                VALUES (?, ?, ?, ?)
            ''', (soc, dte, avg_consumption, 1 if regen_active else 0))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error caching DTE: {e}")
    
    def end_session(self, final_soc, final_temperature=None):
        """End current ride session and save stats"""
        try:
            if self.session_id is None:
                return
            
            avg_consumption = self.get_moving_average_consumption() if self.total_distance > 0 else 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE ride_sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    final_soc = ?,
                    final_temperature = ?,
                    total_distance = ?,
                    total_energy_used = ?,
                    total_energy_regenerated = ?,
                    avg_consumption = ?
                WHERE session_id = ?
            ''', (final_soc, final_temperature, self.total_distance, 
                  self.total_energy_used, self.total_energy_regenerated,
                  avg_consumption, self.session_id))
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Ended session {self.session_id}: distance={self.total_distance:.2f} km, " +
                       f"energy_used={self.total_energy_used:.2f}Wh, consumption={avg_consumption:.2f} Wh/km")
            
            # Reset session
            self.session_id = None
            self.total_distance = 0
            self.total_energy_used = 0
            self.total_energy_regenerated = 0
            
        except Exception as e:
            logger.error(f"❌ Error ending session: {e}")
    
    def get_current_dte(self):
        """Get cached DTE value"""
        return self.cached_dte
    
    def get_current_avg_consumption(self):
        """Get cached average consumption"""
        return self.cached_avg_consumption
    
    def get_session_stats(self):
        """Get current session statistics"""
        return {
            'session_id': self.session_id,
            'total_distance': round(self.total_distance, 2),
            'total_energy_used': round(self.total_energy_used, 2),
            'total_energy_regenerated': round(self.total_energy_regenerated, 2),
            'avg_consumption': round(self.get_moving_average_consumption() if self.total_distance > 0 else 0, 2),
            'current_dte': round(self.cached_dte, 2),
            'is_moving': self.is_moving
        }