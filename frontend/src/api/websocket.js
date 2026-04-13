import { io } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_WS_URL || `http://${window.location.hostname}:5000`;
const TELEMETRY_EVENTS = ['bms_update', 'bms_data'];

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.onMessageCallback = null;
    this.onStatusChangeCallback = null;
    this.retryConfig = {
      attempt: 0,
      maxDelay: 30000,
      baseDelay: 1000,
    };
  }

  connect() {
    if (this.socket) {
      this.socket.disconnect();
    }
    
    this.socket = io(WS_URL, {
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: this.retryConfig.baseDelay,
      reconnectionDelayMax: this.retryConfig.maxDelay,
      randomizationFactor: 0.5,
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      this._updateStatus('CONNECTED');
      this.retryConfig.attempt = 0;
    });

    this.socket.on('disconnect', (reason) => {
      this._updateStatus('DISCONNECTED');
    });

    this.socket.on('connect_error', (err) => {
      this._updateStatus('CONNECTING');
      this.retryConfig.attempt++;
    });

    TELEMETRY_EVENTS.forEach((eventName) => {
      this.socket.on(eventName, (data) => {
        if (this.onMessageCallback) {
          this.onMessageCallback(data);
        }
      });
    });
  }

  _updateStatus(status) {
    if (this.onStatusChangeCallback) {
      this.onStatusChangeCallback(status);
    }
  }

  onMessage(cb) {
    this.onMessageCallback = cb;
  }

  onStatusChange(cb) {
    this.onStatusChangeCallback = cb;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const wsManager = new WebSocketManager();
