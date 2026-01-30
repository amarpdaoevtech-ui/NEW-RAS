#!/usr/bin/env python3
import smbus2
import time
import json
import re
import logging

logger = logging.getLogger(__name__)

class SpeedI2CReader:
    def __init__(self, bus_id=1, addr=0x08):
        self.bus_id = bus_id
        self.addr = addr
        self.bus = None
        self.last_seq = None
        self.last_mode = None
        self.mode_names = {0: "POWER", 1: "ECONOMY", 2: "SPORTS"} # Updated based on user request: 0,1,2 = power, economy, sports
        self.last_data = {
            "speed_kmph": 0.0,
            "mode": "ECONOMY",
            "mode_index": 1,
            "voltage": 0.0,
            "soc": 0,
            "current": 0,
            "brake": 0,
            "seq": 0
        }
        self.connected = False

    def connect(self):
        try:
            self.bus = smbus2.SMBus(self.bus_id)
            self.connected = True
            logger.info(f"Connected to Speed I2C Bus {self.bus_id} at address {hex(self.addr)}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Speed I2C: {e}")
            self.connected = False
            return False

    def read_data(self):
        if not self.bus:
            if not self.connect():
                return None
        
        try:
            # Read 128 bytes from I2C slave
            msg = smbus2.i2c_msg.read(self.addr, 128)
            self.bus.i2c_rdwr(msg)
            
            # Convert to text, strip trailing spaces
            text = "".join(chr(b) for b in msg if 32 <= b < 127).strip()
            
            # Find complete JSON between < and >
            match = re.search(r'<(\{[^>]+\})>', text)
            
            if not match:
                return None
                
            frame = match.group(1)
            d = json.loads(frame)
            
            # Skip duplicates (same sequence number)
            if self.last_seq is not None and d['seq'] == self.last_seq:
                return None
            
            self.last_seq = d['seq']
            
            # Sanity check speed
            speed = float(d.get('spd', 0.0))
            if speed > 100 or speed < 0:
                speed = 0.0
            
            mode_idx = d.get('mode', 1)
            mode_str = self.mode_names.get(mode_idx, f"UNK({mode_idx})")
            
            self.last_data = {
                "speed_kmph": round(speed, 1),
                "mode": mode_str,
                "mode_index": mode_idx,
                "voltage": d.get('v', 0.0),
                "soc": d.get('soc', 0),
                "current": d.get('cur', 0),
                "brake": d.get('brk', 0),
                "seq": d.get('seq', 0)
            }
            
            return self.last_data
            
        except Exception as e:
            logger.debug(f"I2C Read Error: {e}")
            return None

    def close(self):
        if self.bus:
            self.bus.close()
