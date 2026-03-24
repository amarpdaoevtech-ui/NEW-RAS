#!/usr/bin/env python3
import threading
import time
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config.settings import config
from utils.logger import setup_logger
from database.db_manager import db_manager
from logic.odometer import PersistentOdometer
from logic.dte_calc import EnhancedDTECalculator
from logic.bms_protocol import crc16_modbus, decode_dao_bms_payload
from hardware.bms_serial import BMSSerialReader
from hardware.i2c_speed import SpeedI2CReader
from hardware.i2c_battery import BatteryI2CReader
from api.server import api_server, socketio, app
import api.routes # Register routes
import api.sockets # Register socket events

logger = setup_logger("Main")

# Initialize shared components
odometer = PersistentOdometer(storage_path='data/odometer.json')
dte_calc = EnhancedDTECalculator(db_manager=db_manager)

def bms_reader_thread():
    logger.info("Starting BMS Reader Thread...")
    reader = BMSSerialReader()
    
    if not reader.connect():
        logger.error("Could not open BMS Serial Port!")
        api_server.update_data("status", "Serial port error")
        return

    ser = reader.ser
    buffer = bytearray()
    
    while True:
        try:
            b = ser.read(1)
            if not b: continue
            
            buffer += b
            while buffer and buffer[0] != 0x5B:
                buffer.pop(0)

            if len(buffer) < 9: continue
            data_len = buffer[5]
            frame_len = 6 + data_len + 2
            if len(buffer) < frame_len: continue

            frame = buffer[:frame_len]
            buffer = buffer[frame_len:]

            body = frame[:-2]
            crc_rx = frame[-2] | (frame[-1] << 8)
            if crc_rx != crc16_modbus(body): continue

            if frame[4] == 0x82 and frame[5] == 0x18:
                raw_payload = frame[6:-2]
                if len(raw_payload) < 24: continue
                if raw_payload[0] != 0x2A or raw_payload[1] != 0x16: continue
                
                payload = raw_payload[2:]
                data = decode_dao_bms_payload(payload)
                if data:
                    api_server.update_data(data)
                    db_manager.log_bms_data(api_server.bms_data)
                    
                    # Update DTE tracking with current odometer totals
                    dte_calc.log_sensor_reading(
                        voltage_v=data['voltage'],
                        current_a=data['current'],
                        soc_percent=data['soc'],
                        soh_percent=data['soh'],
                        temperature_c=data['temperature'],
                        speed_kmph=api_server.bms_data['speed_kmph'],
                        throttle_pos=api_server.bms_data['throttle'],
                        total_odometer_km=odometer.get_distance(),
                        session_distance_km=odometer.get_session_distance(),
                        mode=api_server.bms_data['speed_mode']
                    )
                    
                    dte, cons, regen, conf = dte_calc.calculate_dte(
                        data['soc'], data['soh'], data['temperature'],
                        api_server.bms_data['speed_kmph'],
                        api_server.bms_data['throttle'],
                        api_server.bms_data['speed_mode'],
                        data['voltage']
                    )
                    
                    api_server.update_data({
                        "dte": round(dte, 1),
                        "dte_avg_consumption": round(cons, 1),
                        "dte_confidence": conf
                    })
                    api_server.emit_update()

        except Exception as e:
            logger.error(f"BMS Thread Error: {e}")
            time.sleep(1)

def i2c_reader_thread():
    logger.info("Starting I2C Reader Thread...")
    speed_reader = SpeedI2CReader()
    battery_reader = BatteryI2CReader()
    
    last_loop_time = time.time()
    
    while True:
        try:
            current_time = time.time()
            time_delta = current_time - last_loop_time
            last_loop_time = current_time
            
            # Speed Data
            spd_data = speed_reader.read_data()
            if spd_data:
                api_server.update_data({
                    "speed_kmph": spd_data['speed_kmph'],
                    "throttle": spd_data['throttle'],
                    "speed_mode": spd_data['mode'],
                    "brake": spd_data['brake'],
                    "esp32_connected": True
                })
            
            # Continuous Odometer Update (even if no new I2C frame due to steady speed/throttle)
            with api_server.data_lock:
                current_speed = api_server.bms_data['speed_kmph']
            
            total_dist, session_dist = odometer.update(current_speed, time_delta)
            
            api_server.update_data({
                "total_distance": round(total_dist, 2),
                "current_ride_distance": round(session_dist, 2)
            })
            
            if spd_data or (int(current_time * 10) % 10 == 0): # Emit on new data or 1Hz
                api_server.emit_update()
            
            # Battery Data
            if int(current_time) % 5 == 0:
                bat_data = battery_reader.read_data()
                if bat_data:
                    api_server.update_data("pi_battery", bat_data)
                    api_server.emit_update()

            # Save Odometer
            if int(current_time) % 30 == 0:
                odometer.save()

        except Exception as e:
            logger.error(f"I2C Thread Error: {e}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    logger.info("DAO BMS Backend Starting...")
    
    # Start threads
    threads = [
        threading.Thread(target=bms_reader_thread, daemon=True),
        threading.Thread(target=i2c_reader_thread, daemon=True)
    ]
    
    for t in threads:
        t.start()
        
    # Start Flask/SocketIO
    logger.info("Starting API Server on port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
