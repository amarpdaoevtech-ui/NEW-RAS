import serial
import time
import os
from utils.logger import setup_logger
from config.settings import config
from logic.bms_protocol import crc16_modbus, decode_dao_bms_payload

logger = setup_logger(__name__)

class BMSSerialReader:
    def __init__(self):
        self.ser = None
        self.connected = False

    def find_working_port(self):
        ports = config.get_serial_ports()
        baud = config.get_baud_rate()
        for port in ports:
            if os.path.exists(port):
                try:
                    ser = serial.Serial(port=port, baudrate=baud, bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.1)
                    logger.info(f"Opened {port} at {baud} baud")
                    return ser
                except Exception as e:
                    logger.error(f"Failed to open {port}: {e}")
        return None

    def connect(self):
        self.ser = self.find_working_port()
        self.connected = self.ser is not None
        return self.connected

    def read_frame(self):
        if not self.ser:
            if not self.connect(): return None
        
        try:
            # Simple frame reader based on 0x5B start byte
            # This is a simplified version of the logic in bms_server_enhanced.py
            # To be robust, it should maintain a buffer
            pass # Implementation will be refined in main loop or here
        except Exception as e:
            logger.error(f"BMS Read Error: {e}")
            self.connected = False
            if self.ser: self.ser.close()
            self.ser = None
        return None

    def close(self):
        if self.ser: self.ser.close()
        self.connected = False
