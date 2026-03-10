from flask import jsonify, request
from api.server import app, api_server
from database.db_manager import db_manager
from config.settings import config

@app.route('/', methods=['GET'])
def index():
    return "DAO BMS Backend is running. Use /api/health for status."

@app.route('/api/bms', methods=['GET'])
def get_bms_data():
    with api_server.data_lock:
        return jsonify(api_server.bms_data)

@app.route('/api/config', methods=['GET'])
def get_config_route():
    return jsonify({
        "model": config.model_name,
        "name": config.model_config['name'],
        "parameters": config.get_parameters(),
        "display": config.get_display_config()
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    hours = request.args.get('hours', default=24, type=int)
    limit = request.args.get('limit', default=1000, type=int)
    logs = db_manager.get_recent_bms_logs(hours=hours, limit=limit)
    return jsonify(logs)

@app.route('/api/health', methods=['GET'])
def health_check():
    with api_server.data_lock:
        return jsonify({
            "status": "ok",
            "connected": api_server.bms_data["connected"],
            "last_update": api_server.bms_data["last_update"]
        })
