from api.server import socketio, api_server
from utils.logger import setup_logger

logger = setup_logger(__name__)

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected via WebSocket')
    with api_server.data_lock:
        socketio.emit('bms_update', api_server.bms_data)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('request_data')
def handle_request_data():
    with api_server.data_lock:
        socketio.emit('bms_update', api_server.bms_data)
