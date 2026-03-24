import sqlite3
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from config.settings import config

class DBManager:
    """Database manager for BMS data and DTE logging"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent / os.getenv('DB_PATH', 'data/bms_data.db')
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_interval = int(os.getenv('DB_LOG_INTERVAL', 5))
        self.last_log_time = 0
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            cursor = conn.cursor()
            
            # BMS logs
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
            
            # Ride sessions
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
            
            # Consumption history — lifetime odometer logbook
            # One row every 0.25km of total lifetime distance, regardless of ride
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consumption_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_odometer_km REAL,
                    session_distance_km REAL,
                    voltage REAL,
                    current REAL,
                    current_soc INTEGER,
                    current_speed REAL,
                    riding_mode TEXT,
                    FOREIGN KEY (session_id) REFERENCES ride_sessions(session_id)
                )
            ''')
            
            # DTE cache
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
            
            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON bms_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumption_odometer ON consumption_history(total_odometer_km)')

            # --- Auto-migration: detect and upgrade old consumption_history schema ---
            cursor.execute("PRAGMA table_info(consumption_history)")
            col_names = [row[1] for row in cursor.fetchall()]
            if 'distance_traveled' in col_names or 'total_odometer_km' not in col_names:
                print("⚠️  Old consumption_history schema detected. Migrating to new schema...")
                cursor.execute("DROP TABLE IF EXISTS consumption_history")
                cursor.execute('''
                    CREATE TABLE consumption_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        total_odometer_km REAL,
                        session_distance_km REAL,
                        voltage REAL,
                        current REAL,
                        current_soc INTEGER,
                        current_speed REAL,
                        riding_mode TEXT,
                        FOREIGN KEY (session_id) REFERENCES ride_sessions(session_id)
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumption_odometer ON consumption_history(total_odometer_km)')
                print("✅ consumption_history migrated to new schema.")
            # -------------------------------------------------------------------------

            conn.commit()
            conn.close()
            print(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def log_bms_data(self, data):
        """Log BMS data to database"""
        try:
            current_time = time.time()
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

    def get_recent_bms_logs(self, hours=24, limit=1000):
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

# Global DB manager instance
db_manager = DBManager()
