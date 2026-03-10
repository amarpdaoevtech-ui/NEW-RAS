import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def setup_logger(name):
    """Setup logger with file and stream handlers"""
    log_dir = Path(__file__).parent.parent.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / os.getenv('LOG_FILE', 'bms_server.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)
