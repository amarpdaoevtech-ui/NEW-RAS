from utils.logger import setup_logger
from config.settings import config

logger = setup_logger(__name__)

BMS_STATUS_FLAGS = {
    0x0001: "Normal discharge",
    0x0002: "Normal charging",
    0x0004: "Charging saturation protection",
    0x0008: "Battery low voltage protection",
    0x0010: "Overcurrent protection during charging",
    0x0020: "Discharge overcurrent protection",
    0x0040: "Battery overheat protection",
    0x0080: "Battery discharge low temperature protection",
    0x0100: "Battery pack open circuit",
    0x0200: "Discharge short circuit protection",
    0x0400: "Battery overheat protection (secondary)",
    0x0800: "Battery charging low temperature protection",
    0x1000: "Circuit board MOS overheat protection",
    0x2000: "Temperature sensor malfunction",
    0x4000: "Reserved",
    0x8000: "Reserved",
}

def crc16_modbus(data: bytes):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF

def u16(lo, hi):
    return (hi << 8) | lo

def s8(v):
    return v - 256 if v > 127 else v

def decode_bms_status(status):
    if status == 0x0000:
        return ["Normal / No fault"]
    active = []
    for bit, desc in BMS_STATUS_FLAGS.items():
        if status & bit:
            active.append(desc)
    return active

def decode_dao_bms_payload(payload: bytes):
    """Decode BMS payload and return a data dictionary"""
    if len(payload) != 22:
        logger.warning("Invalid DAO payload length")
        return None

    bms_config = config.get_bms_config()
    parameters = config.get_parameters()
    
    bat_cap = u16(payload[0], payload[1])
    charge_cnt = u16(payload[2], payload[3])
    voltage = u16(payload[4], payload[5]) * bms_config['voltage_multiplier']
    chg_cur = u16(payload[6], payload[7]) * bms_config['current_multiplier']
    dchg_cur = u16(payload[8], payload[9]) * bms_config['current_multiplier']
    soc = payload[10]
    health = payload[11]
    status_raw = u16(payload[12], payload[13])
    rem_time = payload[14] * 0.1

    num_sensors = parameters['num_temp_sensors']
    temps = [(s8(payload[i]) - 40) for i in range(15, 15 + num_sensors)]
    avg_temp = sum(temps) / len(temps) if temps else 0
    status_desc = decode_bms_status(status_raw)
    
    power = voltage * dchg_cur

    return {
        "battery_capacity": bat_cap,
        "charge_cycles": charge_cnt,
        "voltage": round(voltage, 1),
        "charge_current": round(chg_cur, 1),
        "current": round(dchg_cur, 1),
        "soc": soc,
        "soh": health,
        "remaining_time": round(rem_time, 1),
        "temperatures": [round(t, 1) for t in temps],
        "temperature": round(avg_temp, 1),
        "power": round(power, 2),
        "status_flags": status_desc,
        "status": status_desc[0] if status_desc else "Unknown",
        "connected": True
    }
