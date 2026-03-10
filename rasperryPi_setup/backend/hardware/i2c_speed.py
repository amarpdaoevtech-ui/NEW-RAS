import smbus2
import time
import json
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SpeedI2CReader:
    def __init__(self, bus_id=1, addr=0x08):
        self.bus_id = bus_id
        self.addr = addr
        self.bus = None
        self.last_seq = None
        self.mode_names = {0: "LOW", 1: "MED", 2: "HIGH"}
        self.last_data = {
            "speed_kmph": 0.0, "throttle": 0.0, "mode": "MED", "mode_index": 1,
            "voltage": 0.0, "soc": 0, "current": 0, "brake": 0, "seq": 0
        }
        self.connected = False

    def connect(self):
        try:
            self.bus = smbus2.SMBus(self.bus_id)
            self.connected = True
            logger.info(f"Connected Speed I2C Bus {self.bus_id} at {hex(self.addr)}")
            return True
        except Exception as e:
            logger.error(f"Speed I2C error: {e}")
            self.connected = False
            return False

    def _parse_frame(self, raw_bytes):
        text = "".join(chr(b) for b in raw_bytes if 32 <= b < 127).strip()
        matches = list(re.finditer(r'<(\{[^>]+\})>', text))
        if not matches: return None
        for match in reversed(matches):
            try: return json.loads(match.group(1))
            except: continue
        return None

    def read_data(self):
        if not self.bus:
            if not self.connect(): return None
        try:
            msg = smbus2.i2c_msg.read(self.addr, 128)
            self.bus.i2c_rdwr(msg)
            raw = list(msg)
            d = self._parse_frame(raw)
            if not d: return None
            
            seq = d.get('seq', -1)
            th = float(d.get('th', 0.0))
            if self.last_seq == seq and abs(th - self.last_data['throttle']) <= 1.0:
                return None
            
            self.last_seq = seq
            spd = float(d.get('spd', 0.0))
            if spd > 150 or spd < 0: spd = 0.0
            
            self.last_data = {
                "speed_kmph": round(spd, 1),
                "throttle": round(th, 1),
                "mode": self.mode_names.get(d.get('mode', 1), "UNK"),
                "mode_index": d.get('mode', 1),
                "voltage": d.get('v', 0.0),
                "soc": d.get('soc', 0),
                "current": d.get('cur', 0),
                "brake": d.get('brk', 0),
                "seq": seq
            }
            return self.last_data
        except Exception:
            self.connected = False
            return None
