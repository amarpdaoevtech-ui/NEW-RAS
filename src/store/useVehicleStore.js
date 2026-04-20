import { create } from 'zustand';
import { detectVehicleId } from '../utils/vehicleDetection';
import { fetchTelemetry, fetchConfig } from '../api/apiClient';
import { wsManager } from '../api/websocket';

// Flatten nested telemetry objects to be easy to select.
const normalizeTelemetry = (raw) => {
  const temperatures = Array.isArray(raw.temperatures) ? raw.temperatures : [];

  return {
    speed_kmph: raw.speed_kmph ?? raw.speed ?? 0,
    voltage: raw.voltage ?? 0,
    current: raw.current ?? 0,
    power: raw.power ?? 0,
    soc: raw.soc ?? raw.battery_level ?? 0,
    soh: raw.soh ?? 100,
    temperature: raw.temperature ?? raw.temp ?? 0,
    throttle: raw.throttle ?? 0,
    battery_capacity: raw.battery_capacity ?? 100,
    charge_cycles: raw.charge_cycles ?? 0,
    charge_current: raw.charge_current ?? 0,
    remaining_time: raw.remaining_time ?? 0,
    total_distance: raw.total_distance ?? 0,
    current_ride_distance: raw.current_ride_distance ?? 0,
    dte: raw.dte ?? 0,
    dte_avg_consumption: raw.dte_avg_consumption ?? 0,
    dte_confidence: raw.dte_confidence ?? 'LOW',
    brake_state: raw.brake ? 'BRAKE ON' : 'BRAKE OFF',
    cruise_state: raw.cruise ? 'CRUISE ON' : 'CRUISE OFF',
    regen_state: raw.regen_active ? 'REGEN ON' : 'REGEN OFF',
    system_status: raw.status || 'NORMAL',
    connected_state: raw.connected ? 'BMS ONLINE' : 'BMS OFFLINE',
    esp32_state: raw.esp32_connected ? 'ESP32 OK' : 'ESP32 OFF',
    pi_battery_percent: raw.pi_battery?.percent ?? 0,
    mode: raw.speed_mode ?? raw.mode ?? 'ECO',
    speed_mode: raw.speed_mode ?? raw.mode ?? 'ECO',
    temperature2: temperatures[1] ?? raw.temperature2 ?? raw.temperature ?? raw.temp ?? 0,
    temperature3: temperatures[2] ?? raw.temperature3 ?? raw.temperature ?? raw.temp ?? 0,
    status: raw.status || 'NORMAL',
    _ts: Date.now(),
  };
};

const HISTORY_WINDOW_MS = 2 * 60 * 60 * 1000;
const HISTORY_SAMPLE_MS = 5 * 1000;

const appendHistoryPoint = (points, value, timestamp) => {
  const nextPoints = [...points, { timestamp, value: Number(value) || 0 }];
  const cutoff = timestamp - HISTORY_WINDOW_MS;
  return nextPoints.filter((point) => point.timestamp >= cutoff);
};

export const useVehicleStore = create((set, get) => ({
  vehicleId: 'default',
  connectionStatus: 'DISCONNECTED', // CONNECTED, CONNECTING, DISCONNECTED
  configError: null,
  isInitialized: false,
  rawTelemetry: {},
  history: {
    speed_kmph: [],
    throttle: [],
  },
  historySampleTs: {
    speed_kmph: 0,
    throttle: 0,
  },

  telemetry: {
    speed_kmph: 0,
    voltage: 0,
    current: 0,
    power: 0,
    soc: 0,
    soh: 100,
    temperature: 0,
    throttle: 0,
    battery_capacity: 100,
    charge_cycles: 0,
    charge_current: 0,
    remaining_time: 0,
    total_distance: 0,
    current_ride_distance: 0,
    dte: 0,
    dte_avg_consumption: 0,
    dte_confidence: 'LOW',
    brake_state: 'BRAKE OFF',
    cruise_state: 'CRUISE OFF',
    regen_state: 'REGEN OFF',
    system_status: 'NORMAL',
    connected_state: 'BMS OFFLINE',
    esp32_state: 'ESP32 OFF',
    pi_battery_percent: 0,
    mode: 'ECO',
    speed_mode: 'ECO',
    gps: { lat: 0, lng: 0 },
    temperature2: 0,
    temperature3: 0,
    _ts: 0,
  },

  setConnectionStatus: (status) => set({ connectionStatus: status }),

  updateTelemetry: (data) => {
    // Basic throttle logic (limit state updates to save renders).
    // Not using requestAnimationFrame here, but skipping high frequency frames
    const now = Date.now();
    const lastTs = get().telemetry._ts;
    if (now - lastTs < 50) return; // limit to 20 fps

    const normalized = normalizeTelemetry(data);
    set((state) => ({
      rawTelemetry: data && typeof data === 'object' ? data : {},
      telemetry: {
        ...state.telemetry,
        ...normalized,
      },
      history: {
        speed_kmph:
          now - state.historySampleTs.speed_kmph >= HISTORY_SAMPLE_MS
            ? appendHistoryPoint(state.history.speed_kmph, normalized.speed_kmph, now)
            : state.history.speed_kmph,
        throttle:
          now - state.historySampleTs.throttle >= HISTORY_SAMPLE_MS
            ? appendHistoryPoint(state.history.throttle, normalized.throttle, now)
            : state.history.throttle,
      },
      historySampleTs: {
        speed_kmph:
          now - state.historySampleTs.speed_kmph >= HISTORY_SAMPLE_MS
            ? now
            : state.historySampleTs.speed_kmph,
        throttle:
          now - state.historySampleTs.throttle >= HISTORY_SAMPLE_MS
            ? now
            : state.historySampleTs.throttle,
      },
    }));
  },

  initialize: async (vehicleId = 'default') => {
    const resolvedVehicleId = detectVehicleId(vehicleId);
    try {
      set({ vehicleId: resolvedVehicleId, isInitialized: false, configError: null });

      // In a real system, you might fetch specific vehicle config overrides
      // const config = await fetchConfig(vehicleId);

      // Attempt initial fetch to get base state faster
      try {
        const initialData = await fetchTelemetry();
        if (initialData) {
          get().updateTelemetry(initialData);
        }
      } catch (e) {
        console.warn("Initial REST fetch failed, relying on WS");
      }

      set({ isInitialized: true });

      // Hook up websocket
      wsManager.onStatusChange((status) => {
        get().setConnectionStatus(status);
      });

      wsManager.onMessage((message) => {
        get().updateTelemetry(message);
      });

      wsManager.connect();

    } catch (err) {
      set({ configError: err.message, isInitialized: true });
    }
  },

  cleanup: () => {
    wsManager.disconnect();
  }
}));
