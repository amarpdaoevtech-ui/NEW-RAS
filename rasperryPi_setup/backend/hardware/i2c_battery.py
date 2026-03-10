import smbus2
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BatteryI2CReader:
    def __init__(self, bus_id=1, addr=0x2d):
        self.bus_id = bus_id
        self.addr = addr
        self.bus = None
        self.connected = False

    def connect(self):
        try:
            self.bus = smbus2.SMBus(self.bus_id)
            self.connected = True
            logger.info(f"Connected Battery I2C Bus {self.bus_id} at {hex(self.addr)}")
            return True
        except Exception as e:
            logger.error(f"Battery I2C error: {e}")
            self.connected = False
            return False

    def read_data(self):
        if not self.bus:
            if not self.connect(): return None
        try:
            # Read state
            state_data = self.bus.read_i2c_block_data(self.addr, 0x02, 1)
            s = state_data[0]
            state = "Fast Charging" if s & 0x40 else ("Charging" if s & 0x80 else ("Discharging" if s & 0x20 else "Idle"))
            
            # Read battery info
            bat_data = self.bus.read_i2c_block_data(self.addr, 0x20, 6)
            bat_v = bat_data[0] | (bat_data[1] << 8)
            bat_pct = bat_data[4] | (bat_data[5] << 8)
            
            return {
                "state": state,
                "voltage_mv": bat_v,
                "percent": int(bat_pct)
            }
        except Exception:
            self.connected = False
            return None
