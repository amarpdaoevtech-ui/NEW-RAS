import axios from 'axios';

// Default to same host if we omit origin, assuming proxy or standard setup
const API_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000/api`;

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchTelemetry = async () => {
  try {
    const res = await apiClient.get('/bms');
    return res.data;
  } catch (error) {
    console.error("REST GET Error:", error);
    throw error;
  }
};

export const fetchConfig = async () => {
  try {
    const res = await apiClient.get('/config');
    return res.data;
  } catch (error) {
    console.error("Config GET Error:", error);
    throw error;
  }
};
