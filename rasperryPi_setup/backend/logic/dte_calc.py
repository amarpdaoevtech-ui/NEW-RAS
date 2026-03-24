import sqlite3
import time
import logging
from datetime import datetime
from uuid import uuid4
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EnhancedDTECalculator:
    """
    Industry-competitive DTE calculator for 2-wheeler EVs
    """
    
    MODE_BASE = {
        'low': 27.5,
        'medium': 37.5,
        'high': 55.0
    }
    
    POWER_MAPS = {
        'low': {0: 50, 25: 150, 50: 300, 75: 450, 100: 600},
        'medium': {0: 80, 25: 250, 50: 500, 75: 750, 100: 1000},
        'high': {0: 120, 25: 400, 50: 800, 75: 1200, 100: 1600}
    }
    
    VMAX = 84.0
    VMIN = 69.0

    def __init__(self, db_manager, battery_capacity_wh=2250, nominal_voltage=75.0):
        self.db_manager = db_manager
        self.db_path = db_manager.db_path
        self.battery_capacity_wh = battery_capacity_wh
        self.nominal_voltage = nominal_voltage
        
        self.session_id = None
        self.session_start_time = None
        self.last_distance = 0
        self.last_soc = 100
        self.total_energy_used = 0
        self.total_energy_regenerated = 0
        self.total_distance = 0
        self.is_moving = False
        self.last_power_timestamp = None
        
        self.cached_dte = 0
        self.cached_avg_consumption = 0
        self.last_dte_value = 0
        self.dte_smoothing_alpha = 0.20
        
        self.last_consumption_log_distance = 0
        self.idle_drain_rate_per_hour = 0.0003
        self.expected_idle_hours = 12

    def start_session(self, initial_soc, bike_model="703-O", riding_mode="medium"):
        try:
            self.session_id = f"ride_{uuid4().hex[:8]}_{int(time.time())}"
            self.session_start_time = datetime.now()
            self.last_soc = initial_soc
            self.total_energy_used = 0
            self.total_energy_regenerated = 0
            self.total_distance = 0
            self.last_distance = 0
            self.last_power_timestamp = None
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
        return current_a < -2.0

    def detect_ride_status(self, speed_kmph, throttle_pos):
        self.is_moving = speed_kmph > 2.0 or throttle_pos > 10
        return self.is_moving

    def get_temperature_factor(self, temperature_c):
        if temperature_c < -10: return 1.25
        elif temperature_c < 0: return 1.18
        elif temperature_c < 10: return 1.12
        elif temperature_c <= 30: return 1.0
        elif temperature_c <= 40: return 1.05
        else: return 1.12

    def get_voltage_soc(self, voltage_v):
        v = max(self.VMIN, min(self.VMAX, voltage_v))
        return round(((v - self.VMIN) / (self.VMAX - self.VMIN)) * 100.0, 1)

    def get_effective_soc(self, bms_soc, voltage_v):
        if voltage_v < 1.0: return bms_soc
        v_soc = self.get_voltage_soc(voltage_v)
        return 0.70 * bms_soc + 0.30 * v_soc

    def get_soc_usable_factor(self, soc_percent):
        if soc_percent > 20: return 1.0
        elif soc_percent > 10: return 0.85 + (soc_percent - 10) * 0.015
        else: return 0.70 + soc_percent * 0.015

    def apply_idle_drain_compensation(self, energy_wh):
        idle_drain_wh_per_hour = self.battery_capacity_wh * self.idle_drain_rate_per_hour
        total_idle_drain = idle_drain_wh_per_hour * self.expected_idle_hours
        return max(0, energy_wh - total_idle_drain)

    def get_instant_power_consumption(self, throttle_pct, mode, speed_kmph):
        if speed_kmph <= 0: return 0
        mode_lower = mode.lower() if isinstance(mode, str) else 'medium'
        if mode_lower not in self.POWER_MAPS: mode_lower = 'medium'
        throttle_pct = max(0, min(100, throttle_pct))
        power_w = self._interpolate(throttle_pct, self.POWER_MAPS[mode_lower])
        return power_w / speed_kmph
    
    def _interpolate(self, value, value_map):
        keys = sorted(value_map.keys())
        if value <= keys[0]: return value_map[keys[0]]
        if value >= keys[-1]: return value_map[keys[-1]]
        for i in range(len(keys) - 1):
            if keys[i] <= value <= keys[i+1]:
                x0, x1 = keys[i], keys[i+1]
                y0, y1 = value_map[x0], value_map[x1]
                return y0 + (value - x0) / (x1 - x0) * (y1 - y0)
        return value_map[keys[-1]]

    def get_segmented_consumption(self, total_distance_km):
        window_weights = {1: 0.50, 5: 0.30, 15: 0.20}
        if self.session_id is None: return self.MODE_BASE.get('medium', 37.5)
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
                    WHERE session_id = ? AND distance_traveled >= ? AND distance_traveled <= ?
                    ORDER BY distance_traveled
                ''', (self.session_id, start_dist, total_distance_km))
                data = cursor.fetchall()
                if len(data) >= 2:
                    dist_delta = data[-1][0] - data[0][0]
                    net_energy = (data[-1][1] - data[0][1]) - (data[-1][2] - data[0][2])
                    if dist_delta > 0.1:
                        weighted_consumption += weight * max(net_energy / dist_delta, 5.0)
                        total_weight_used += weight
            conn.close()
            if total_weight_used > 0: return weighted_consumption / total_weight_used
            if self.total_distance > 0.2 and self.total_energy_used > 0:
                return max((self.total_energy_used - self.total_energy_regenerated) / self.total_distance, 5.0)
            return self.MODE_BASE.get('medium', 37.5)
        except Exception: return self.MODE_BASE.get('medium', 37.5)

    def calculate_dte(self, soc_percent, soh_percent, temperature_c, speed_kmph, throttle_pct=0, mode="medium", voltage_v=0.0):
        is_stationary = speed_kmph < 2.0
        try:
            mode_lower = mode.lower() if isinstance(mode, str) else 'medium'
            historical = self.get_segmented_consumption(self.total_distance)
            instant = self.get_instant_power_consumption(throttle_pct, mode_lower, speed_kmph)
            
            if historical > 0 and instant > 0: consumption = 0.70 * historical + 0.30 * instant
            elif historical > 0: consumption = historical
            elif instant > 0: consumption = 0.50 * instant + 0.50 * self.MODE_BASE.get(mode_lower, 37.5)
            else: consumption = self.MODE_BASE.get(mode_lower, 37.5)
            
            consumption *= self.get_temperature_factor(temperature_c)
            consumption = max(consumption, 30.0)
            
            eff_soc = self.get_effective_soc(soc_percent, voltage_v)
            energy = (eff_soc / 100.0) * (self.battery_capacity_wh * (soh_percent / 100.0))
            energy *= self.get_soc_usable_factor(eff_soc)
            energy = self.apply_idle_drain_compensation(energy)

            dte_raw = energy / consumption if consumption > 0 else 0
            
            if self.last_dte_value != 0:
                change = dte_raw - self.last_dte_value
                if change > 0: dte_raw = self.last_dte_value + min(change, 0.1 if speed_kmph > 2.0 else 0.3)
                else: dte_raw = self.last_dte_value + max(change, -1.0)
            
            if self.last_dte_value != 0:
                dte_final = self.dte_smoothing_alpha * dte_raw + (1 - self.dte_smoothing_alpha) * self.last_dte_value
            else: dte_final = dte_raw
            
            dte_final = min(dte_final, self.battery_capacity_wh / 35.0)
            confidence = 'LOW' if self.total_distance < 5 else ('MEDIUM' if self.total_distance < 15 or soc_percent < 20 else 'HIGH')
            
            if is_stationary: return (self.last_dte_value, consumption, False, confidence)
            
            self._cache_dte(dte_final, soc_percent, consumption, False, speed_kmph, confidence)
            self.last_dte_value = dte_final
            return (dte_final, consumption, False, confidence)
        except Exception as e:
            logger.error(f"Error DTE: {e}")
            return (self.last_dte_value, 37.5, False, 'LOW')

    def _cache_dte(self, dte, soc, avg_consumption, regen, speed, conf):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO dte_cache (soc, dte, avg_consumption, regen_active, speed_kmph, confidence) VALUES (?, ?, ?, ?, ?, ?)',
                         (soc, dte, avg_consumption, 1 if regen else 0, speed, conf))
            conn.commit()
            conn.close()
        except: pass

    def log_sensor_reading(self, voltage_v, current_a, soc_percent, soh_percent, temperature_c,
                           speed_kmph, throttle_pos,
                           total_odometer_km=None, session_distance_km=None, mode="medium"):
        try:
            if self.session_id is None and soc_percent > 10:
                self.start_session(soc_percent, riding_mode=mode)
            if self.session_id is None: return

            # Track current mode immediately
            self.riding_mode = mode

            # Track session distance using the odometer's session_distance_km directly
            if session_distance_km is not None:
                self.total_distance = session_distance_km

            # Accumulate energy consumed this session
            cur_ts = time.time()
            if self.last_power_timestamp:
                dt_h = (cur_ts - self.last_power_timestamp) / 3600.0
                p_w = voltage_v * current_a
                energy = abs(p_w) * dt_h
                if current_a < -2.0: self.total_energy_regenerated += energy
                elif p_w > 0: self.total_energy_used += energy
            self.last_power_timestamp = cur_ts

            # Log a snapshot for efficiency history every 0.25km of TOTAL LIFETIME odometer
            if total_odometer_km is not None and (total_odometer_km - self.last_consumption_log_distance) >= 0.25:
                self._log_consumption(
                    total_odometer_km=total_odometer_km,
                    session_distance_km=session_distance_km or 0.0,
                    voltage_v=voltage_v,
                    current_a=current_a,
                    soc=soc_percent,
                    speed=speed_kmph,
                    mode=mode
                )
                self.last_consumption_log_distance = total_odometer_km
            
            # Always update the ride_sessions summary row to ensure persistence
            self._update_session_totals()

        except Exception as e: logger.error(f"Error log sensors: {e}")

    def _log_consumption(self, total_odometer_km, session_distance_km, voltage_v, current_a, soc, speed, mode):
        """Insert one lifetime odometer snapshot row into consumption_history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO consumption_history '
                '(session_id, total_odometer_km, session_distance_km, voltage, current, current_soc, current_speed, riding_mode) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (self.session_id, round(total_odometer_km, 4), round(session_distance_km, 4),
                 round(voltage_v, 2), round(current_a, 2), soc, round(speed, 2), mode)
            )
            conn.commit()
            conn.close()
        except Exception as e: logger.error(f"Error _log_consumption: {e}")

    def _update_session_totals(self):
        """Persist the running session totals and latest mode back to the ride_sessions table."""
        if self.session_id is None:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE ride_sessions SET total_distance = ?, total_energy_used = ?, total_energy_regenerated = ?, riding_mode = ? WHERE session_id = ?',
                (round(self.total_distance, 4), round(self.total_energy_used, 4), 
                 round(self.total_energy_regenerated, 4), self.riding_mode, self.session_id)
            )
            if cursor.rowcount == 0:
                logger.warning(f"No ride_sessions row found to update for session {self.session_id}")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating session totals: {e}")

    def get_session_stats(self):
        return {
            "session_id": self.session_id,
            "total_distance": round(self.total_distance, 2),
            "total_energy_used": round(self.total_energy_used, 2),
            "total_energy_regen": round(self.total_energy_regenerated, 2)
        }
