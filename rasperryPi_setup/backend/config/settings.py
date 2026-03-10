import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration manager for bike models"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / 'config' / 'bike_models.json'
        self.load_config()
    
    def load_config(self):
        """Load bike model configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            bike_model = os.getenv('BIKE_MODEL', config_data.get('active_model', '703-O'))
            
            if bike_model not in config_data['models']:
                raise ValueError(f"Bike model '{bike_model}' not found in configuration")
            
            self.model_config = config_data['models'][bike_model]
            self.model_name = bike_model
            
            print(f"✅ Loaded configuration for: {self.model_config['name']}")
            
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            print("Using default configuration for 703-O")
            self._load_default_config()
    
    def _load_default_config(self):
        """Fallback default configuration"""
        self.model_name = "703-O"
        self.model_config = {
            "name": "Scooty Model 703-O (Default)",
            "protocol": "RS485",
            "baud_rate": 9600,
            "serial_ports": ["/dev/ttyAMA0", "/dev/serial0", "/dev/ttyS0"],
            "parameters": {
                "max_voltage": 60.0,
                "max_current": 50.0,
                "max_power": 3000.0,
                "max_speed": 60,
                "max_temperature": 80,
                "battery_capacity": 30,
                "num_temp_sensors": 5
            },
            "bms_config": {
                "frame_start": "0x5B",
                "command_response": "0x82",
                "data_length": 24,
                "crc_type": "modbus",
                "voltage_multiplier": 0.1,
                "current_multiplier": 0.1,
                "temp_offset": -40
            },
            "display": {
                "show_temperature": True,
                "show_voltage": True,
                "show_current": True,
                "show_power": True,
                "show_soc": True,
                "show_soh": True,
                "show_speed": False,
                "theme": "dark"
            }
        }
    
    def get_serial_ports(self):
        """Get serial port configuration"""
        override_port = os.getenv('SERIAL_PORT')
        if override_port:
            return [override_port]
        return self.model_config['serial_ports']
    
    def get_baud_rate(self):
        """Get baud rate"""
        override_baud = os.getenv('BAUD_RATE')
        if override_baud:
            return int(override_baud)
        return self.model_config['baud_rate']
    
    def get_parameters(self):
        """Get bike parameters"""
        return self.model_config['parameters']
    
    def get_bms_config(self):
        """Get BMS configuration"""
        return self.model_config['bms_config']
    
    def get_display_config(self):
        """Get display configuration"""
        return self.model_config['display']

# Global config instance
config = Config()
