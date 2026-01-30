#!/usr/bin/env python3
import smbus2
import time
import logging

logger = logging.getLogger(__name__)

class BatteryI2CReader:
    def __init__(self, bus_id=1, addr=0x2d):
        self.bus_id = bus_id
        self.addr = addr
        self.bus = None
        self.connected = False
        self.low_vol = 3150 # mV

    def connect(self):
        try:
            self.bus = smbus2.SMBus(self.bus_id)
            self.connected = True
            logger.info(f"Connected to Battery I2C Bus {self.bus_id} at address {hex(self.addr)}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Battery I2C: {e}")
            self.connected = False
            return False

    def read_data(self):
        if not self.bus:
            if not self.connect():
                return None
        
        try:
            # Read charging state
            state_data = self.bus.read_i2c_block_data(self.addr, 0x02, 1)
            state = "Idle"
            if state_data[0] & 0x40:
                state = "Fast Charging"
            elif state_data[0] & 0x80:
                state = "Charging"
            elif state_data[0] & 0x20:
                state = "Discharging"
            
            # Read VBUS info
            vbus_data = self.bus.read_i2c_block_data(self.addr, 0x10, 6)
            vbus_v = vbus_data[0] | (vbus_data[1] << 8)
            vbus_i = vbus_data[2] | (vbus_data[3] << 8)
            vbus_p = vbus_data[4] | (vbus_data[5] << 8)
            
            # Read Battery info
            bat_data = self.bus.read_i2c_block_data(self.addr, 0x20, 12)
            bat_v = bat_data[0] | (bat_data[1] << 8)
            bat_i = bat_data[2] | (bat_data[3] << 8)
            if bat_i > 0x7FFF:
                bat_i -= 0xFFFF
            bat_pct = bat_data[4] | (bat_data[5] << 8)
            rem_cap = bat_data[6] | (bat_data[7] << 8)
            
            # Read Cell voltages
            cell_data = self.bus.read_i2c_block_data(self.addr, 0x30, 8)
            cells = [
                cell_data[0] | (cell_data[1] << 8),
                cell_data[2] | (cell_data[3] << 8),
                cell_data[4] | (cell_data[5] << 8),
                cell_data[6] | (cell_data[7] << 8)
            ]
            
            return {
                "state": state,
                "vbus_voltage_mv": vbus_v,
                "vbus_current_ma": vbus_i,
                "vbus_power_mw": vbus_p,
                "battery_voltage_mv": bat_v,
                "battery_current_ma": bat_i,
                "pi_battery_percent": int(bat_pct),
                "remaining_capacity_mah": rem_cap,
                "cell_voltages_mv": cells
            }
        except Exception as e:
            logger.debug(f"Battery I2C Read Error: {e}")
            return None

    def close(self):
        if self.bus:
            self.bus.close()
