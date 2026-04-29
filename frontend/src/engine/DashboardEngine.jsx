// ─────────────────────────────────────────────────────────────────────────────
// DashboardEngine — 1024 × 600 px  (7-inch Raspberry Pi display)
//
//  LAYOUT:  Full-bleed, zero side padding
//  Header:  44 px
//  Footer:  20 px
//  Body pad: 4 px top / 4 px bottom
//  Gap:     6 px (H and V)
//
//  COLUMN WIDTH:  (1024 − 4×6) / 5 = 200 px
//  ROW HEIGHT:    (600 − 44 − 20 − 8 − 12) / 3 = 172 px
//  Pixel verification:
//    Width:  5×200 + 4×6           = 1024 ✓
//    Height: 44 + 4 + 172+6+172+6+172 + 4 + 20 = 600 ✓
//
//  7 × 4  GRID:
// ─────────────────────────────────────────────────────────────────────────────

import React, { useEffect, useState } from 'react';
import { useVehicleStore } from '../store/useVehicleStore';
import TileType6  from '../components/tiles/TileType6';
import TileType4    from '../components/tiles/TileType4';
import TileType2    from '../components/tiles/TileType2';
import TileType5   from '../components/tiles/TileType5';
import TileType3   from '../components/tiles/TileType3';
import TileType1 from '../components/tiles/TileType1';
import TileType7 from '../components/tiles/TileType7';
import HeaderRideToggle from '../components/HeaderRideToggle';

// ── Layout numbers ────────────────────────────────────────────────────────────
const W      = 1024;
const H      = 600;
const T_COL  = 128;
const T_ROW  = 128;
const COLS   = 7;
const ROWS   = 4;
const GAP    = 16;
const PADDING_SIDE = 16;
// Grid height = 4*128 + 3*16 = 560. 600 - 560 = 40.
const HDR    = 24;
const FTR    = 16;
const BPAD   = 0;   // body top / bottom padding

// Big tile (cols 1-2, rows 2-3)
const BIG_W  = T_COL * 2 + GAP;   
const BIG_H  = T_ROW * 2 + GAP;   

// ── Colour tokens ─────────────────────────────────────────────────────────────
const C = {
  bg:     '#080C12',
  hdr:    '#0C1320',
  border: '#1A2535',
  green:  '#10FF80',
  blue:   '#00B8FF',
  amber:  '#FFAA00',
  red:    '#FF3A5C',
  purple: '#A78BFA',
  muted:  '#334155',
  dim:    '#1E3050',
};

// ── Keyframes ─────────────────────────────────────────────────────────────────
const ANIM = `
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700;800;900&display=swap');
  
  @keyframes blink-dot {
    0%,100%{opacity:1} 50%{opacity:.25}
  }
  @keyframes pulse-ring {
    0%  {transform:scale(1);opacity:.65}
    100%{transform:scale(2.4);opacity:0}
  }
`;

// ─────────────────────────────────────────────────────────────────────────────
export default function DashboardEngine() {
  const telemetry = useVehicleStore((state) => state.telemetry);
  const connStatus = useVehicleStore((state) => state.connectionStatus);
  const history = useVehicleStore((state) => state.history);

  // Map mode string to state id for TileType6
  let modeState = 4; // Default DRIVE
  if (telemetry.mode === 'LOW' || telemetry.mode === 'PARK') modeState = 1;
  else if (telemetry.mode === 'MED' || telemetry.mode === 'REVERSE') modeState = 2;
  else if (telemetry.mode === 'HIGH' || telemetry.mode === 'NEUTRAL') modeState = 3;

  // Map system status for cooling TileType7
  const coolingState = telemetry.system_status === 'COOLING' ? 4 : 1;

  // Prepare graph data for TileType5
  const graphData = [
    { id: '1', label: 'SPD', value: telemetry.speed_kmph,  unit: 'km/h', color: '#F59E0B', history: history.speed_kmph?.map(h => h.value) || [] },
    { id: '2', label: 'VOLT', value: telemetry.voltage,  unit: 'V',    color: '#38BDF8', history: [telemetry.voltage] }, // mock history if unavailable
    { id: '3', label: 'CURR', value: Math.abs(telemetry.current),  unit: 'A',    color: '#00FF7F', history: [Math.abs(telemetry.current)] },
    { id: '4', label: 'TEMP', value: telemetry.temperature,  unit: '°C',   color: '#F43F5E', history: [telemetry.temperature] },
  ];

  return (
    <div style={{
      width: W, height: H,
      background: C.bg,
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      fontFamily: "'Share Tech Mono','Courier New',monospace",
      color: '#E2E8F0',
    }}>
      <style>{ANIM}</style>

      {/* ── HEADER ─────────────────────────────────── */}
      <Header telemetry={telemetry} connStatus={connStatus} />

      {/* ── TILE GRID BODY ─────────────────────────── */}
      <div style={{
        flex: 1, minHeight: 0,
        padding: \`\${BPAD}px \${PADDING_SIDE}px\`,
        display: 'grid',
        gridTemplateColumns: \`repeat(\${COLS}, \${T_COL}px)\`,
        gridTemplateRows:    \`repeat(\${ROWS}, \${T_ROW}px)\`,
        gap: GAP,
        boxSizing: 'border-box',
      }}>

        {/* Row 1 — 7 standard tiles ─────────────── */}
        <Cell col={1} row={1} w={T_COL} h={T_ROW}>
          <TileType4   label="STATE OF CHARGE"    unit="%" value={telemetry.soc} color={C.green} />
        </Cell>
        <Cell col={2} row={1} w={T_COL} h={T_ROW}>
          <TileType2   label="THROTTLE"  unit="%" value={telemetry.throttle} color={C.green} />
        </Cell>
        <Cell col={3} row={1} w={T_COL} h={T_ROW}>
          <TileType1 label="DTE" unit="KM" value={telemetry.dte} color={C.amber} big />
        </Cell>
        <Cell col={4} row={1} w={T_COL} h={T_ROW}>
          <TileType3  label="BATTERY TEMP"        unit="°C" value={telemetry.temperature} />
        </Cell>
        <Cell col={5} row={1} w={T_COL} h={T_ROW}>
          <TileType6  
            label="DRIVE MODE"          
            state={modeState}
            state_1_label="LOW" state_2_label="MED" state_3_label="HIGH" state_4_label="DRIVE"
          />
        </Cell>
        <Cell col={6} row={1} w={T_COL} h={T_ROW}>
          <TileType1 label="INVERTER TEMP" unit="°C" value={telemetry.temperature2 || 38.4} color={C.amber} big />
        </Cell>
        <Cell col={7} row={1} w={T_COL} h={T_ROW}>
          <TileType7 
            label="SYS COOLING" 
            state={coolingState}
            state_1_label="IDLE" state_2_label="LOW" state_3_label="MED" state_4_label="MAX"
          />
        </Cell>

        {/* Rows 2-3, Cols 1-2 — ONE BIG TILE ─────── */}
        <Cell col={1} row={2} spanW={2} spanH={2} w={BIG_W} h={BIG_H}>
          <div style={{ width: '100%', height: '100%', margin: 'auto', display: 'flex' }}>
            <TileType5 label="LIVE TELEMETRY STREAM" data={graphData} />
          </div>
        </Cell>

        {/* Row 2, Cols 3-7 ────────────────────────── */}
        <Cell col={3} row={2} w={T_COL} h={T_ROW}>
          <TileType4   label="STATE OF HEALTH"    unit="%" value={telemetry.soh} color={C.blue} />
        </Cell>
        <Cell col={4} row={2} w={T_COL} h={T_ROW}>
          <TileType1 label="MOTOR POWER"       unit="W"  value={telemetry.power}  color={C.red}  big />
        </Cell>
        <Cell col={5} row={2} w={T_COL} h={T_ROW}>
          <TileType1 label="VOLTAGE"           unit="V"  value={telemetry.voltage} color={C.amber} big />
        </Cell>
        <Cell col={6} row={2} w={T_COL} h={T_ROW}>
          <TileType1 label="AUX VOLTAGE"       unit="V"  value={telemetry.pi_battery_percent || 12.1} color={C.muted} big />
        </Cell>
        <Cell col={7} row={2} w={T_COL} h={T_ROW}>
          <TileType1 label="CELL BALANCE"       unit="mV"  value={14} color={C.green} big />
        </Cell>

        {/* Row 3, Cols 3-7 ────────────────────────── */}
        <Cell col={3} row={3} w={T_COL} h={T_ROW}>
          <TileType1 label="SPEED"             unit="KM/H" value={telemetry.speed_kmph}   color={C.green} big />
        </Cell>
        <Cell col={4} row={3} w={T_COL} h={T_ROW}>
          <TileType1 label="CURRENT"           unit="A"    value={telemetry.current} color={C.blue}  big />
        </Cell>
        <Cell col={5} row={3} w={T_COL} h={T_ROW}>
          <TileType1 label="ODOMETER"          unit="KM"   value={telemetry.total_distance} color={C.purple} big />
        </Cell>
        <Cell col={6} row={3} w={T_COL} h={T_ROW}>
          <TileType1 label="MOTOR TEMP"        unit="°C"   value={telemetry.temperature3 || 62} color={C.red} big />
        </Cell>
        <Cell col={7} row={3} w={T_COL} h={T_ROW}>
          <TileType1 label="COOLANT"        unit="°C"   value={telemetry.temperature2 || 88} color={C.amber} big />
        </Cell>
        
        {/* Row 4, Cols 1-7 ────────────────────────── */}
        <Cell col={1} row={4} w={T_COL} h={T_ROW}>
          <TileType1 label="PEAK KW"        unit="KW"   value={Math.max(0, telemetry.power / 1000).toFixed(1)} color={C.red} big />
        </Cell>
        <Cell col={2} row={4} w={T_COL} h={T_ROW}>
          <TileType1 label="REGEN PWR"      unit="KW"   value={Math.min(0, telemetry.power / 1000).toFixed(1)} color={C.green} big />
        </Cell>
        <Cell col={3} row={4} w={T_COL} h={T_ROW}>
          <TileType2 label="BRAKE PEDAL"    unit="%"    value={telemetry.brake_state === 'BRAKE ON' ? 100 : 0}  color={C.blue} />
        </Cell>
        <Cell col={4} row={4} w={T_COL} h={T_ROW}>
          <TileType4 label="EFFICIENCY"     unit="%"    value={94}  color={C.green} />
        </Cell>
        <Cell col={5} row={4} w={T_COL} h={T_ROW}>
          <TileType3 label="AMBIENT TEMP"   unit="°C"   value={24} />
        </Cell>
        <Cell col={6} row={4} w={T_COL} h={T_ROW}>
          <TileType1 label="LATERAL G"      unit="G"    value={0.8} color={C.purple} big />
        </Cell>
        <Cell col={7} row={4} w={T_COL} h={T_ROW}>
          <TileType1 label="LONG G"         unit="G"    value={1.2} color={C.amber} big />
        </Cell>
      </div>

      {/* ── FOOTER ─────────────────────────────────── */}
      <Footer connStatus={connStatus} />
    </div>
  );
}

// ── Grid cell wrapper ──────────────────────────────────────────────────────────
function Cell({ col, row, spanW = 1, spanH = 1, w, h, children }) {
  return (
    <div style={{
      gridColumn: \`\${col} / span \${spanW}\`,
      gridRow:    \`\${row} / span \${spanH}\`,
      width: w, height: h,
      overflow: 'hidden',
    }}>
      {children}
    </div>
  );
}

// ── Header ────────────────────────────────────────────────────────────────────
function Header({ telemetry, connStatus }) {
  const isConnected = connStatus === 'CONNECTED';
  const liveColor = isConnected ? C.green : C.red;
  const [timeStr, setTimeStr] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }));
  
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeStr(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);
  
  return (
    <div style={{
      height: HDR, flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 16px',
      background: \`linear-gradient(180deg, \${C.hdr} 0%, transparent 100%)\`,
      borderBottom: \`1px solid \${C.border}\`,
      boxSizing: 'border-box',
    }}>
      {/* Brand */}
      <div>
        <div style={{ fontSize: 15, fontWeight: 900, letterSpacing: '0.2em', color: C.green,
          textShadow: \`0 0 12px \${C.green}80\`, fontFamily: 'Orbitron, monospace' }}>
          EV TELEMETRY
        </div>
        <div style={{ fontSize: 6.5, letterSpacing: '0.24em', color: C.muted, marginTop: 1 }}>
          RACING EDITION · DASHBOARD V3.0 · LIVE TELEMETRY
        </div>
      </div>

      {/* Quick stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {[
          { v: Math.round(telemetry?.speed_kmph || 0).toString(),  u: 'KM/H',  c: C.green },
          { v: Math.round(telemetry?.soc || 0) + '%',  u: 'SOC %', c: C.red   },
          { v: telemetry?.mode || 'ECO', u: 'MODE',  c: C.green },
        ].map(({ v, u, c }, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
            <span style={{ fontSize: 16, fontWeight: 900, color: c, letterSpacing: '0.06em',
              textShadow: \`0 0 8px \${c}90\`, fontFamily: 'Orbitron, monospace' }}>{v}</span>
            <span style={{ fontSize: 6, letterSpacing: '0.16em', color: C.muted }}>{u}</span>
          </div>
        ))}
      </div>

      {/* Time + Live */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <HeaderRideToggle />
        <span style={{ fontSize: 18, fontWeight: 700, color: '#E2E8F0',
          letterSpacing: '0.06em', fontFamily: 'Orbitron, monospace' }}>
          {timeStr}
        </span>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 5,
          padding: '3px 9px', borderRadius: 20,
          background: \`\${liveColor}14\`, border: \`1px solid \${liveColor}44\`,
        }}>
          <div style={{ position: 'relative', width: 7, height: 7 }}>
            <div style={{ position: 'absolute', inset: -2, borderRadius: '50%',
              background: liveColor, animation: isConnected ? 'pulse-ring 1.8s ease-out infinite' : 'none', opacity: .5 }}/>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: liveColor,
              boxShadow: \`0 0 5px \${liveColor}\` }}/>
          </div>
          <span style={{ fontSize: 7.5, fontWeight: 700, color: liveColor, letterSpacing: '0.14em' }}>
            {isConnected ? 'LIVE BMS' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────────
function Footer({ connStatus }) {
  return (
    <div style={{
      height: FTR, flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 16px',
      borderTop: \`1px solid \${C.border}\`,
      boxSizing: 'border-box',
    }}>
      <span style={{ fontSize: 6.5, letterSpacing: '0.18em', color: C.dim }}>
        EV TELEMETRY DASHBOARD · TILE SPEC V3.0 · {W}×{H} · 5 DATA CHANNELS
      </span>
      <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        {[C.green, C.blue, C.amber, C.red].map((c, i) => (
          <div key={i} style={{ width: 5, height: 5, borderRadius: '50%',
            background: c, boxShadow: \`0 0 4px \${c}\`, opacity: connStatus === 'CONNECTED' ? 1 : 0.3 }}/>
        ))}
      </div>
      <span style={{ fontSize: 6.5, letterSpacing: '0.18em', color: C.dim }}>
        20 FPS · {connStatus === 'CONNECTED' ? 'WEBSOCKET ACTIVE' : 'WEBSOCKET DISCONNECTED'}
      </span>
    </div>
  );
}
