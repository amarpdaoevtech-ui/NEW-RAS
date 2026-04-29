import React, { useMemo, useState } from 'react';
import { useVehicleStore } from '../store/useVehicleStore';

const BACKEND_URL = `${window.location.protocol}//${window.location.hostname}:5000`;

export default function HeaderRideToggle() {
  const connectionStatus = useVehicleStore((s) => s.connectionStatus);
  const rawTelemetry = useVehicleStore((s) => s.rawTelemetry) || {};
  
  const connected = connectionStatus === 'CONNECTED';
  const rideActiveRaw = rawTelemetry.ride_active;
  const sessionId = rawTelemetry.session_id;

  const rideActive = useMemo(() => {
    if (typeof rideActiveRaw === 'boolean') return rideActiveRaw;
    if (typeof rideActiveRaw === 'string') return rideActiveRaw.toUpperCase() === 'ON';
    return false;
  }, [rideActiveRaw]);

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function toggleRide() {
    if (busy || !connected) return;
    setBusy(true);
    setErr('');
    try {
      const endpoint = rideActive ? '/api/ride/stop' : '/api/ride/start';
      const res = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || json.success === false) {
        throw new Error(json.error || `Request failed (${res.status})`);
      }
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  // Visuals computation
  let pillBg, pillBorder, pillText, icon, textGlow;
  
  if (!connected) {
    pillBg = 'linear-gradient(135deg, #1A2535 0%, #0F1722 100%)';
    pillBorder = '#334155';
    pillText = '#64748B';
    icon = '●';
    textGlow = 'none';
  } else if (rideActive) {
    pillBg = 'linear-gradient(135deg, rgba(255,58,92,0.1) 0%, rgba(255,58,92,0.2) 100%)';
    pillBorder = '#FF3A5C';
    pillText = '#FF3A5C';
    icon = '■';
    textGlow = '0 0 12px rgba(255,58,92,0.8)';
  } else {
    // Ready
    pillBg = 'linear-gradient(135deg, rgba(0,184,255,0.1) 0%, rgba(0,184,255,0.2) 100%)';
    pillBorder = '#00B8FF';
    pillText = '#00B8FF';
    icon = '▶';
    textGlow = '0 0 12px rgba(0,184,255,0.8)';
  }

  const mainText = busy ? 'SYNC...' : (rideActive ? 'STOP RIDE' : (connected ? 'START RIDE' : 'OFFLINE'));
  const subText = rideActive ? (sessionId ? `ID:${sessionId}` : 'ACTIVE') : (err ? 'ERROR' : (connected ? 'READY' : 'WAITING'));

  return (
    <div 
      onClick={toggleRide}
      title={err ? `Error: ${err}` : ''}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '18px',
        gap: '6px',
        padding: '0 12px',
        borderRadius: '3px',
        background: pillBg,
        border: `1px solid ${pillBorder}`,
        cursor: (busy || !connected) ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s ease-out',
        boxShadow: rideActive ? '0 0 10px rgba(255,58,92,0.3) inset' : (connected ? '0 0 8px rgba(0,184,255,0.2) inset' : 'none'),
        opacity: busy ? 0.85 : 1,
        userSelect: 'none',
        WebkitTapHighlightColor: 'transparent',
        boxSizing: 'border-box'
      }}
      onPointerDown={(e) => {
         if(!connected || busy) return;
         e.currentTarget.style.transform = 'scale(0.95)';
         e.currentTarget.style.filter = 'brightness(1.5)';
      }}
      onPointerUp={(e) => {
         if(!connected || busy) return;
         e.currentTarget.style.transform = 'scale(1)';
         e.currentTarget.style.filter = 'brightness(1.2)';
      }}
      onPointerLeave={(e) => {
         e.currentTarget.style.transform = 'scale(1)';
         e.currentTarget.style.filter = 'brightness(1)';
      }}
    >
      <span style={{ 
        color: pillText, 
        fontSize: '10px', 
        textShadow: textGlow,
        animation: rideActive ? 'blink-dot 1.5s infinite' : 'none',
        marginTop: '-1px'
      }}>
        {icon}
      </span>
      <span style={{ 
        color: pillText, 
        fontFamily: "'Orbitron', sans-serif", 
        fontSize: '9px', 
        fontWeight: '800',
        letterSpacing: '1px',
        textShadow: textGlow,
        textTransform: 'uppercase',
      }}>
        {busy ? 'SYNC...' : mainText}
      </span>
    </div>
  );
}
