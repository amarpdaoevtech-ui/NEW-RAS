// src/utils/vehicleDetection.js

/**
 * Detect the active vehicle identifier.
 * Order of precedence:
 *   1. URL query param `vehicle`
 *   2. localStorage key `vehicleId`
 *   3. fallback to the default passed to initialize()
 */
export const detectVehicleId = (fallback = 'default') => {
  // 1. URL param
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const urlVehicle = params.get('vehicle');
    if (urlVehicle) return urlVehicle;
  }

  // 2. localStorage
  try {
    const stored = typeof window !== 'undefined' && window.localStorage.getItem('vehicleId');
    if (stored) return stored;
  } catch (e) {
    // ignore storage errors
  }

  // 3. fallback
  return fallback;
};
