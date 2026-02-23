#!/usr/bin/env python3
"""
Enhanced DTE (Distance-to-Empty) Calculator for EV Scooter
Industry-competitive algorithms based on: Ola, Ather, TVS, Bajaj research

Features:
  ✓ Segmented consumption windows (Ather-inspired)
  ✓ Real-time power prediction (TVS-inspired)
  ✓ Mode-specific base consumption (Industry standard)
  ✓ Idle drain compensation (Ather innovation)
  ✓ SOC non-linearity (All manufacturers)
  ✓ Confidence calculation
  ✓ No ML - embedded-friendly

Version: 1.0 | Date: February 2026
"""
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import logging
import time

# Setup logging
logger = logging.getLogger(__name__)


class EnhancedDTECalculator:
    """
    Industry-competitive DTE calculator for 2-wheeler EVs
    Based on: Ola Electric, Ather Energy, TVS iQube, Bajaj Chetak
    """
    
    # Mode-specific base consumption (Wh/km) - Industry averages
    MODE_BASE = {
        'low': 27.5,      # ECO mode (Ather ECO: ~25-30, Ola ECO: ~26-28)
        'medium': 37.5,   # RIDE mode (Ather Ride: ~35-40, Ola Normal: ~36-42)
        'high': 55.0      # SPORT mode (Ather Sport: ~50-60, Ola Sport: ~52-65)
    }
    
    # Power maps for instant prediction (Watts) - Calibrated for 3-4 kW motor
    POWER_MAPS = {
        'low': {0: 50, 25: 150, 50: 300, 75: 450, 100: 600},
        'medium': {0: 80, 25: 250, 50: 500, 75: 750, 100: 1000},
        'high': {0: 120, 25: 400, 50: 800, 75: 1200, 100: 1600}
    }
    
    def __init__(self, db_path='data/bms_data.db', battery_capacity_wh=2370, nominal_voltage=79.0):
        """
        Initialize Enhanced DTE Calculator
        
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
        
        # Track last power reading time for proper energy integration
        self.last_power_timestamp = None
        
        # Calibration factor for current sensor (1.0 = no change)
        self.current_calibration = 1.0
        # Session initial soc for calibration
        self.session_initial_soc = None
        
        # Cache for performance
        self.cached_dte = 0
        self.cached_avg_consumption = 0
        self.last_dte_update_time = None
        self.last_dte_value = 0
        
        # ✅ NEW: Enhanced smoothing parameters (More stable)
        self.dte_smoothing_alpha = 0.05  # Very slow smoothing to prevent jumps
        self.max_rate_change_km = 0.1    # Max 100m change per update cycle
        
        # Track last consumption log time to avoid duplicate entries
        self.last_consumption_log_time = None
        self.last_consumption_log_distance = 0
        
        # ✅ NEW: Idle drain configuration (Ather innovation)
        self.idle_drain_rate_per_hour = 0.0003  # 0.03% per hour
        self.expected_idle_hours = 12  # Average parking time
        
        # ✅ Automatically initialize database on startup
        self.init_database()

    
    def init_database(self):
        """Initialize database tables for DTE tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            # ✅ OPTIMIZATION: Enable WAL mode for high concurrency
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            
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
            
            # Create consumption_history table with instant_consumption column
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consumption_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    distance_traveled REAL,
                    energy_used REAL,
                    energy_regenerated REAL,
                    avg_consumption REAL,
                    instant_consumption REAL,
                    current_speed REAL,
                    current_soc INTEGER,
                    riding_mode TEXT,
                    FOREIGN KEY (session_id) REFERENCES ride_sessions(session_id)
                )
            ''')
            
            # ✅ OPTIMIZATION: Index for fast segmentation queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumption_distance ON consumption_history(distance_traveled)')
            
            # Create dte_cache table with confidence column
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dte_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    soc INTEGER,
                    dte REAL,
                    avg_consumption REAL,
                    regen_active INTEGER,
                    speed_kmph REAL,
                    confidence TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Enhanced DTE database tables initialized successfully (WAL Mode)")
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
    
    # =========================================================================
    # ✅ ENHANCED: Temperature Factor (More granular)
    # =========================================================================
    def get_temperature_factor(self, temperature_c):
        """
        Get efficiency factor based on temperature
        More granular than before based on Li-ion characteristics
        """
        if temperature_c < -10:
            return 1.25  # 25% more consumption in extreme cold
        elif temperature_c < 0:
            return 1.18  # 18% more in freezing
        elif temperature_c < 10:
            return 1.12  # 12% more in cold
        elif temperature_c <= 30:
            return 1.0   # Optimal range
        elif temperature_c <= 40:
            return 1.05  # 5% more in heat
        else:
            return 1.12  # 12% more in extreme heat
    
    def get_mode_multiplier(self, mode):
        """Get consumption multiplier based on riding mode"""
        mode_map = {
            'low': 0.75,    # ECO mode reduces consumption
            'medium': 1.0,  # Normal mode baseline
            'high': 1.45    # Sport mode increases consumption
        }
        return mode_map.get(mode.lower(), 1.0)

    # =========================================================================
    # ✅ NEW: SOC Non-Linearity Factor (Prevents last-km anxiety)
    # =========================================================================
    def get_soc_usable_factor(self, soc_percent):
        """
        Lithium-ion voltage sag compensation
        All major manufacturers use this
        
        Why: At low SOC, battery voltage drops non-linearly,
        reducing effective power delivery and range.
        """
        if soc_percent > 20:
            # Normal operation - full capacity
            return 1.0
        elif soc_percent > 10:
            # Voltage sag region - linear reduction
            # At 20%: factor = 1.0
            # At 10%: factor = 0.85
            return 0.85 + (soc_percent - 10) * 0.015
        else:
            # Critical low SOC - further reduction
            # At 10%: factor = 0.85
            # At 0%: factor = 0.70 (minimum)
            return 0.70 + soc_percent * 0.015

    # =========================================================================
    # ✅ NEW: Idle Drain Compensation (Ather innovation)
    # =========================================================================
    def apply_idle_drain_compensation(self, energy_wh):
        """
        Account for vampire drain while parked
        Ather 450X includes this - improves user trust
        
        Typical drain sources:
          - BMS monitoring: 0.5-1 W continuous
          - Telematics: 0.2-0.5 W
          - Total: ~1-2 Wh per hour
        """
        # Calculate idle drain rate (as Wh per hour)
        idle_drain_wh_per_hour = self.battery_capacity_wh * self.idle_drain_rate_per_hour
        
        # Total expected idle drain
        total_idle_drain = idle_drain_wh_per_hour * self.expected_idle_hours
        
        # Subtract from available energy
        compensated_energy = energy_wh - total_idle_drain
        
        return max(0, compensated_energy)

    # =========================================================================
    # ✅ NEW: Real-Time Power Factor (TVS iQube method)
    # =========================================================================
    def get_instant_power_consumption(self, throttle_pct, mode, speed_kmph):
        """
        Predict instantaneous consumption from current state
        TVS iQube uses this for "next minute" prediction
        
        Returns: Consumption in Wh/km
        """
        if speed_kmph <= 0:
            return 0
        
        mode_lower = mode.lower() if isinstance(mode, str) else 'medium'
        if mode_lower not in self.POWER_MAPS:
            mode_lower = 'medium'
        
        # Clamp throttle to 0-100 range
        throttle_pct = max(0, min(100, throttle_pct))
        
        # Interpolate power based on throttle position
        power_w = self._interpolate(throttle_pct, self.POWER_MAPS[mode_lower])
        
        # Convert to consumption rate (Wh/km)
        consumption_wh_per_km = power_w / speed_kmph
        
        return consumption_wh_per_km
    
    def _interpolate(self, value, value_map):
        """Linear interpolation between points"""
        keys = sorted(value_map.keys())
        
        # Handle edge cases
        if value <= keys[0]:
            return value_map[keys[0]]
        if value >= keys[-1]:
            return value_map[keys[-1]]
        
        # Find the two points to interpolate between
        for i in range(len(keys) - 1):
            if keys[i] <= value <= keys[i+1]:
                x0, x1 = keys[i], keys[i+1]
                y0, y1 = value_map[x0], value_map[x1]
                fraction = (value - x0) / (x1 - x0)
                return y0 + fraction * (y1 - y0)
        
        return value_map[keys[-1]]

    # =========================================================================
    # ✅ NEW: Segmented Consumption Windows (Ather method)
    # =========================================================================
    def get_segmented_consumption(self, total_distance_km, window_weights=None):
        """
        Multi-window weighted average (Ather 450X method)
        Recent behavior predicts next km best, but we need longer-term trends
        
        Default weights: 1km: 50%, 5km: 30%, 15km: 20%
        """
        if window_weights is None:
            window_weights = {1: 0.50, 5: 0.30, 15: 0.20}
        
        if self.session_id is None:
            return self.MODE_BASE.get('medium', 37.5)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            weighted_consumption = 0
            total_weight_used = 0
            
            for window_km, weight in window_weights.items():
                start_dist = max(0, total_distance_km - window_km)
                
                cursor.execute('''
                    SELECT distance_traveled, energy_used, energy_regenerated 
                    FROM consumption_history 
                    WHERE session_id = ? 
                      AND distance_traveled >= ? 
                      AND distance_traveled <= ?
                    ORDER BY distance_traveled
                ''', (self.session_id, start_dist, total_distance_km))
                
                data = cursor.fetchall()
                
                if len(data) >= 2:
                    first = data[0]
                    last = data[-1]
                    distance_delta = last[0] - first[0]
                    energy_used_delta = last[1] - first[1]
                    energy_regen_delta = last[2] - first[2]
                    net_energy = energy_used_delta - energy_regen_delta
                    
                    if distance_delta > 0.1:
                        window_consumption = max(net_energy / distance_delta, 5.0)
                        weighted_consumption += weight * window_consumption
                        total_weight_used += weight
                        logger.debug(f"Window {window_km}km: {window_consumption:.2f} Wh/km (weight={weight})")
            
            conn.close()
            
            if total_weight_used > 0:
                # Normalize by total weight used
                return weighted_consumption / total_weight_used
            else:
                # No data available, return mode base
                return self.MODE_BASE.get('medium', 37.5)
                
        except Exception as e:
            logger.error(f"❌ Error in segmented consumption: {e}")
            return self.MODE_BASE.get('medium', 37.5)

    # =========================================================================
    # ✅ NEW: Blended Consumption (70% historical + 30% instant)
    # =========================================================================
    def get_blended_consumption(self, total_distance_km, throttle_pct, mode, speed_kmph):
        """
        Blend historical and instant consumption
        70% historical (segmented) + 30% instant (real-time power)
        """
        mode_lower = mode.lower() if isinstance(mode, str) else 'medium'
        
        # Get historical consumption (segmented windows)
        historical = self.get_segmented_consumption(total_distance_km)
        
        # Get instant power consumption
        instant = self.get_instant_power_consumption(throttle_pct, mode, speed_kmph)
        
        if historical > 0 and instant > 0:
            # Blend: 70% historical + 30% instant
            return 0.70 * historical + 0.30 * instant
        elif historical > 0:
            return historical
        elif instant > 0:
            # No historical data, blend instant with mode base
            return 0.50 * instant + 0.50 * self.MODE_BASE.get(mode_lower, 37.5)
        else:
            # Fallback to mode base
            return self.MODE_BASE.get(mode_lower, 37.5)

    # =========================================================================
    # ✅ NEW: Confidence Calculation
    # =========================================================================
    def calculate_confidence(self, total_distance_km, soc_percent):
        """
        Calculate confidence level based on available data and SOC
        
        Returns: 'LOW', 'MEDIUM', or 'HIGH'
        """
        if total_distance_km < 5:
            return 'LOW'
        elif total_distance_km < 15 or soc_percent < 20:
            return 'MEDIUM'
        else:
            return 'HIGH'

    def get_adjusted_capacity(self, soh_percent, temperature_c):
        """Calculate adjusted battery capacity based on SOH and temperature"""
        base_capacity = self.battery_capacity_wh * (soh_percent / 100.0)
        # Note: temp_factor here increases consumption, not reduces capacity directly
        # So we don't apply it to capacity, but to consumption instead
        return base_capacity
    
    def calculate_available_energy(self, soc_percent, soh_percent, temperature_c):
        """
        Calculate available energy with SOC non-linearity
        
        Returns:
            float: Available energy in Wh
        """
        # Base capacity adjusted for SOH
        adjusted_capacity = self.get_adjusted_capacity(soh_percent, temperature_c)
        
        # SOC-based energy
        energy = (soc_percent / 100.0) * adjusted_capacity
        
        # ✅ NEW: Apply SOC non-linearity factor
        soc_factor = self.get_soc_usable_factor(soc_percent)
        energy *= soc_factor
        
        # ✅ NEW: Apply idle drain compensation
        energy = self.apply_idle_drain_compensation(energy)
        
        return max(energy, 0)
    
    # =========================================================================
    # ✅ ENHANCED: Rate Limiter
    # =========================================================================
    def _rate_limit(self, new_dte, max_change=None):
        """
        Prevent sudden jumps in DTE
        """
        if max_change is None:
            max_change = self.max_rate_change_km
        
        if self.last_dte_value == 0:
            return new_dte
        
        change = new_dte - self.last_dte_value
        if abs(change) > max_change:
            return self.last_dte_value + (max_change if change > 0 else -max_change)
        return new_dte
    
    # =========================================================================
    # ✅ ENHANCED: EMA Smoothing
    # =========================================================================
    def _ema_smooth(self, raw_val):
        """Exponential moving average for smooth DTE display"""
        if self.last_dte_value == 0:
            return raw_val
        return (self.dte_smoothing_alpha * raw_val + 
                (1 - self.dte_smoothing_alpha) * self.last_dte_value)
    
    def log_sensor_reading(self, voltage_v, current_a, soc_percent, soh_percent, temperature_c, 
                           speed_kmph, throttle_pos, distance_km=None, mode="medium", timestamp=None):
        """
        Log individual sensor reading and update session stats
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Auto-start session if needed
            if self.session_id is None and soc_percent > 10:
                self.start_session(soc_percent, riding_mode=mode)
            
            if self.session_id is None:
                return
            
            # Track distance
            if distance_km is not None:
                distance_delta = distance_km - self.last_distance
                if distance_delta >= 0:
                    self.total_distance += distance_delta
                    self.last_distance = distance_km
            
            # Calculate energy used over TIME interval
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
            
            # Log consumption entry if distance threshold reached (every 0.5 km)
            if distance_km is not None:
                distance_since_last_log = distance_km - self.last_consumption_log_distance
                
                if distance_since_last_log >= 0.5:  # Log every 500m
                    avg_consumption = self.get_segmented_consumption(self.total_distance)
                    instant_consumption = self.get_instant_power_consumption(throttle_pos, mode, speed_kmph)
                    
                    self._log_consumption_entry(
                        self.total_distance,
                        self.total_energy_used,
                        self.total_energy_regenerated,
                        avg_consumption,
                        instant_consumption,
                        speed_kmph,
                        soc_percent,
                        mode
                    )
                    self.last_consumption_log_distance = distance_km
                    logger.info(f"📍 Logged consumption: Distance={self.total_distance:.2f}km, Energy={self.total_energy_used:.2f}Wh, Avg={avg_consumption:.2f}Wh/km, Instant={instant_consumption:.2f}Wh/km")
            
            self.last_soc = soc_percent
            self.last_timestamp = timestamp
            
        except Exception as e:
            logger.error(f"❌ Error logging sensor reading: {e}")
    
    def _log_consumption_entry(self, distance_traveled, energy_used, energy_regenerated, 
                               avg_consumption, instant_consumption, current_speed, current_soc, riding_mode):
        """Log consumption data point to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO consumption_history 
                (session_id, distance_traveled, energy_used, energy_regenerated, 
                 avg_consumption, instant_consumption, current_speed, current_soc, riding_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.session_id, distance_traveled, energy_used, energy_regenerated,
                  avg_consumption, instant_consumption, current_speed, current_soc, riding_mode))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error logging consumption entry: {e}")
    
    # =========================================================================
    # ✅ ENHANCED: Main DTE Calculation
    # =========================================================================
    def calculate_dte(self, soc_percent, soh_percent, temperature_c, speed_kmph, 
                      throttle_pct=0, mode="medium"):
        """
        Calculate Distance-to-Empty with industry-competitive algorithms
        
        Returns:
            tuple: (dte_km, avg_consumption_wh_per_km, regen_active, confidence)
        """
        # ✅ FIX: Don't freeze immediately - continue processing data
        # Only freeze the FINAL DTE value if stationary
        freeze_speed_threshold = 2.0
        is_stationary = speed_kmph < freeze_speed_threshold
        
        try:
            mode_lower = mode.lower() if isinstance(mode, str) else 'medium'
            
            # Step 2: Get blended consumption (70% historical + 30% instant)
            consumption = self.get_blended_consumption(
                self.total_distance, throttle_pct, mode_lower, speed_kmph
            )
            
            # Step 3: Apply temperature compensation
            temp_factor = self.get_temperature_factor(temperature_c)
            consumption *= temp_factor
            
            # Ensure minimum consumption
            consumption = max(consumption, 5.0)
            
            # Step 4: Calculate available energy (with SOC non-linearity + idle drain)
            available_energy = self.calculate_available_energy(soc_percent, soh_percent, temperature_c)
            
            # Step 5: Calculate raw DTE
            if consumption > 0:
                dte_raw = available_energy / consumption
            else:
                dte_raw = 0
            
            # Step 6: Rate limiter (±0.3 km per update)
            dte_raw = self._rate_limit(dte_raw)
            
            # Step 7: EMA smoothing (α=0.25)
            dte_smoothed = self._ema_smooth(dte_raw)
            
            # Step 8: Cap DTE at reasonable maximum
            max_dte = self.battery_capacity_wh / 20  # ~118 km for 2370 Wh
            dte_final = min(dte_smoothed, max_dte)
            
            # Step 9: Calculate confidence
            confidence = self.calculate_confidence(self.total_distance, soc_percent)
            
            # Detect regen (for display purposes)
            regen_active = False
            
            # ✅ FIX: Freeze DTE display when stationary, but AFTER processing data
            if is_stationary:
                logger.debug(f"DTE frozen (stationary): speed={speed_kmph} < {freeze_speed_threshold} km/h, using last value={self.last_dte_value:.2f}km")
                # Still cache the consumption data for future calculations
                self._cache_dte(self.last_dte_value, soc_percent, consumption, regen_active, speed_kmph, confidence)
                self.cached_avg_consumption = consumption  # Update consumption even when frozen
                return (self.last_dte_value, consumption, regen_active, confidence)
            
            # Cache values
            self._cache_dte(dte_final, soc_percent, consumption, regen_active, speed_kmph, confidence)
            self.last_dte_value = dte_final
            self.cached_dte = dte_final
            self.cached_avg_consumption = consumption
            self.last_dte_update_time = datetime.now()
            
            logger.info(f"📊 DTE Calculation: Energy={available_energy:.2f}Wh, Consumption={consumption:.2f}Wh/km, DTE={dte_final:.2f}km, Confidence={confidence}")
            
            return (dte_final, consumption, regen_active, confidence)
            
        except Exception as e:
            logger.error(f"❌ Error calculating DTE: {e}")
            confidence = self.calculate_confidence(self.total_distance, soc_percent)
            return (self.last_dte_value, self.cached_avg_consumption, False, confidence)
    
    def _cache_dte(self, dte, soc, avg_consumption, regen_active, speed_kmph=0, confidence='LOW'):
        """Cache DTE value in database for dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dte_cache (soc, dte, avg_consumption, regen_active, speed_kmph, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (soc, dte, avg_consumption, 1 if regen_active else 0, speed_kmph, confidence))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Error caching DTE: {e}")
    
    def end_session(self, final_soc, final_temperature=None):
        """End current ride session and save stats"""
        try:
            if self.session_id is None:
                return
            
            avg_consumption = self.get_segmented_consumption(self.total_distance) if self.total_distance > 0 else 0
            
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
            'avg_consumption': round(self.get_segmented_consumption(self.total_distance) if self.total_distance > 0 else 0, 2),
            'current_dte': round(self.cached_dte, 2),
            'is_moving': self.is_moving,
            'confidence': self.calculate_confidence(self.total_distance, self.last_soc)
        }


# =========================================================================
# Backward compatibility wrapper
# =========================================================================
def get_moving_average_consumption(self, window_km=25):
    """
    Backward compatibility: Use segmented consumption instead
    """
    return self.get_segmented_consumption(self.total_distance)

# Add method to class
EnhancedDTECalculator.get_moving_average_consumption = get_moving_average_consumption
