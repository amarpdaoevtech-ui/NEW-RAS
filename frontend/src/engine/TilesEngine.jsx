// TilesEngine — EV Dashboard  1024 × 600
// Grid: 7 cols × 4 rows | 128px square tiles | 16px gap | 16px side padding
// Header: 24px | Footer: 16px

import React, { useEffect, useState, useRef } from 'react';

import TileType1 from '../components/tiles/TileType1';
import TileType2 from '../components/tiles/TileType2';
import TileType3 from '../components/tiles/TileType3';
import TileType4 from '../components/tiles/TileType4';
import TileType5 from '../components/tiles/TileType5';
import TileType6 from '../components/tiles/TileType6';
import TileType7 from '../components/tiles/TileType7';
import tilesConfig from '../config/tilesConfig.json';
import { useVehicleStore } from '../store/useVehicleStore';

const REGISTRY = { 
  TileType1, 
  TileType2, 
  TileType3, 
  TileType4, 
  TileType5, 
  TileType6,
  TileType7
};
const { grid, tiles } = tilesConfig;

const ANIM = `
  @keyframes pulse-ring {
    0%   { transform:scale(1); opacity:.65 }
    100% { transform:scale(2.4); opacity:0 }
  }
`;

// Disconnect timeout: show overlay if no bms_update for 3+ seconds
const DISCONNECT_TIMEOUT_MS = 3000;

export default function TilesEngine() {
  // Use the existing Zustand store for telemetry & connection
  const telemetry = useVehicleStore((s) => s.telemetry);
  const rawTelemetry = useVehicleStore((s) => s.rawTelemetry);
  const connectionStatus = useVehicleStore((s) => s.connectionStatus);
  const initialize = useVehicleStore((s) => s.initialize);
  const cleanup = useVehicleStore((s) => s.cleanup);

  const isConnected = connectionStatus === 'CONNECTED';

  // Live clock
  const [clock, setClock] = useState('--:--:--');

  // Stale-data detection (no bms_update for >3s)
  const [isStale, setIsStale] = useState(false);
  const lastUpdateRef = useRef(0);

  // Initialize WebSocket on mount
  useEffect(() => {
    initialize();
    return () => cleanup();
  }, []);

  // Clock tick
  useEffect(() => {
    const id = setInterval(() => {
      const now = new Date();
      setClock(now.toLocaleTimeString('en-GB', { hour12: false }));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // Track staleness based on telemetry timestamp
  useEffect(() => {
    if (telemetry._ts) {
      lastUpdateRef.current = telemetry._ts;
      setIsStale(false);
    }
  }, [telemetry._ts]);

  useEffect(() => {
    const id = setInterval(() => {
      if (lastUpdateRef.current > 0 && Date.now() - lastUpdateRef.current > DISCONNECT_TIMEOUT_MS) {
        setIsStale(true);
      }
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // Build the live data object by merging normalized telemetry with raw payload
  // This ensures all backend keys are available for dataKey lookups
  const liveData = { ...telemetry, ...rawTelemetry };

  /**
   * Hydrate tile props from live backend data.
   * Reads the tile config's dataKey/numberKey/statusKey/uptimeKey and
   * injects the live value into the correct prop for each tile component.
   */
  function hydrateTileProps(tileConfig) {
    const props = { ...tileConfig.props };

    // dataKey → value (for TileType1, TileType2, TileType4) and state (for TileType6)
    if (props.dataKey && liveData[props.dataKey] !== undefined) {
      const raw = liveData[props.dataKey];
      props.value = raw;

      // TileType6 needs `state` — map speed_mode string to numeric
      if (tileConfig.type === 'TileType6') {
        const modeMap = { 'LOW': 1, 'MED': 2, 'HIGH': 3 };
        props.state = modeMap[raw] ?? 1;
        props.state_1_label = 'LOW';
        props.state_2_label = 'MED';
        props.state_3_label = 'HIGH';
        props.state_4_label = '';
        props.state_1_color = '#38BDF8';
        props.state_2_color = '#F59E0B';
        props.state_3_color = '#FF3B3B';
        props.label = props.label || 'Ride Mode';
      }

      // TileType3 needs `values` array — replicate single temp into 3 display rows
      if (tileConfig.type === 'TileType3') {
        const temp = Number(raw) || 0;
        // Use temperature + slight offsets to simulate multi-sensor display
        const t2 = liveData['temperature2'] ?? temp;
        const t3 = liveData['temperature3'] ?? temp;
        props.values = [temp, t2, t3];
        props.min = props.ui?.min ?? 0;
        props.max = props.ui?.max ?? 85;
      }
    }

    // numberKey → value (TileType4 uses this for current_ride_distance)
    if (props.numberKey && liveData[props.numberKey] !== undefined) {
      props.value = liveData[props.numberKey];
    }

    // statusKey → for TileType7 connection indicator
    if (props.statusKey && liveData[props.statusKey] !== undefined) {
      const connected = liveData[props.statusKey];
      props.state = connected ? 2 : 1;
      props.state_1_label = 'OFF';
      props.state_2_label = 'ON';
      props.state_3_label = '';
      props.state_4_label = '';
      props.state_1_color = '#FF3B3B';
      props.state_2_color = '#00e87a';
    }

    // uptimeKey → if TileType7 wants uptime display
    if (props.uptimeKey && liveData[props.uptimeKey] !== undefined) {
      props.uptime = liveData[props.uptimeKey];
    }

    // Apply precision from config
    if (props.precision !== undefined && typeof props.value === 'number') {
      props.value = Number(props.value.toFixed(props.precision));
    }

    // Apply min/max from ui config to props if tile expects them
    if (props.ui) {
      if (props.ui.min !== undefined) props.min = props.ui.min;
      if (props.ui.max !== undefined) props.max = props.ui.max;
    }

    return props;
  }

  return (
    <div style={{
      width: 1024,
      height: 600,
      display: 'flex',
      flexDirection: 'column',
      background: '#0b0f14',
      overflow: 'hidden',
      fontFamily: "'Inter', 'SF Mono', monospace",
      color: '#fff',
      position: 'relative',
    }}>
      <style>{ANIM}</style>




      {/* ── HEADER (24px) ── */}
      <div style={{
        height: grid.headerH,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingLeft: grid.paddingX,
        paddingRight: grid.paddingX,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'linear-gradient(180deg,rgba(255,255,255,0.025) 0%,transparent 100%)',
        boxSizing: 'border-box',
      }}>
        {/* Left — Brand */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 900, letterSpacing: 2, color: '#00e87a', fontFamily: 'Orbitron, sans-serif' }}>
            EV TELEMETRY
          </span>
          <span style={{ fontSize: 7, letterSpacing: 1, color: 'rgba(255,255,255,0.3)' }}>V3.1 · RACING EDITION</span>
        </div>

        {/* Right — Live indicator + clock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ position: 'relative', width: 6, height: 6 }}>
              <div style={{
                position: 'absolute', inset: -2, borderRadius: '50%',
                background: isConnected ? '#00e87a' : '#FF3B3B',
                animation: 'pulse-ring 2s ease-out infinite', opacity: 0.6,
              }} />
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: isConnected ? '#00e87a' : '#FF3B3B',
                boxShadow: `0 0 6px ${isConnected ? '#00e87a' : '#FF3B3B'}`,
              }} />
            </div>
            <span style={{
              fontSize: 8, fontWeight: 700,
              color: isConnected ? '#00e87a' : '#FF3B3B',
              letterSpacing: 1,
            }}>
              {isConnected ? 'LIVE DATA' : 'OFFLINE'}
            </span>
          </div>
          <span style={{ fontSize: 11, fontWeight: 700, fontFamily: 'Orbitron, sans-serif', color: 'rgba(255,255,255,0.8)' }}>
            {clock}
          </span>
        </div>
      </div>

      {/* ── GRID (fills remaining height between header and footer) ── */}
      <div style={{
        flex: 1,
        minHeight: 0,
        display: 'grid',
        gridTemplateColumns: `repeat(${grid.columns}, ${grid.colWidth}px)`,
        gridTemplateRows:    `repeat(${grid.rows}, ${grid.rowHeight}px)`,
        gap: grid.gap,
        paddingLeft: grid.paddingX,
        paddingRight: grid.paddingX,
        paddingTop: grid.paddingY,
        paddingBottom: grid.paddingY,
        alignContent: 'center',
        justifyContent: 'center',
        boxSizing: 'border-box',
      }}>
        {tiles.map((tile) => {
          const Comp = REGISTRY[tile.type];
          if (!Comp) return null;
          const sw = tile.w ?? 1;
          const sh = tile.h ?? 1;
          const cellW = sw * grid.colWidth + (sw - 1) * grid.gap;
          const cellH = sh * grid.rowHeight + (sh - 1) * grid.gap;
          // Big tile: spans ≥4 cols AND ≥2 rows → cap at 512×256, center in cell
          // Remaining space distributes equally: (560-512)/2=24px left/right, (272-256)/2=8px top/bottom
          const isBig = sw >= 4 && sh >= 2;
          const tileW = isBig ? 512 : cellW;
          const tileH = isBig ? 256 : cellH;

          // Hydrate props from live backend data
          const hydratedProps = hydrateTileProps(tile);

          return (
            <div
              key={tile.id}
              style={{
                gridColumn: `${tile.col} / span ${sw}`,
                gridRow:    `${tile.row} / span ${sh}`,
                width:  cellW,
                height: cellH,
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div style={{ width: tileW, height: tileH, overflow: 'hidden', flexShrink: 0 }}>
                <Comp {...hydratedProps} />
              </div>
            </div>
          );
        })}
      </div>

      {/* ── FOOTER (16px) ── */}
      <div style={{
        height: grid.footerH,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingLeft: grid.paddingX,
        paddingRight: grid.paddingX,
        borderTop: '1px solid rgba(255,255,255,0.06)',
        background: 'linear-gradient(0deg,rgba(255,255,255,0.015) 0%,transparent 100%)',
        boxSizing: 'border-box',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {[
            `SYS · ${isConnected ? 'NOMINAL' : 'OFFLINE'}`,
            `CAN · ${isConnected ? 'OK' : '--'}`,
            `BMS · ${isConnected ? 'ACTIVE' : 'WAIT'}`,
          ].map((t, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {i > 0 && <div style={{ width: 1, height: 6, background: 'rgba(255,255,255,0.08)' }} />}
              <span style={{ fontSize: 6, letterSpacing: 1.5, color: 'rgba(255,255,255,0.18)', textTransform: 'uppercase' }}>{t}</span>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {[
            isConnected ? '#00e87a' : '#FF3B3B',
            '#00b4ff',
            '#ff8c00',
          ].map((c, i) => (
            <div key={i} style={{ width: 4, height: 4, borderRadius: '50%', background: c, boxShadow: i === 0 ? `0 0 4px ${c}` : 'none' }} />
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {[
            `MODE · ${telemetry.speed_mode || '--'}`,
            `SOC · ${telemetry.soc ?? '--'}%`,
          ].map((t, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {i > 0 && <div style={{ width: 1, height: 6, background: 'rgba(255,255,255,0.08)' }} />}
              <span style={{ fontSize: 6, letterSpacing: 1.5, color: 'rgba(255,255,255,0.18)', textTransform: 'uppercase' }}>{t}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
