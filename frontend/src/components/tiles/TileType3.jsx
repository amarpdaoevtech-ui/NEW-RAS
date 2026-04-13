import React from 'react';

// TileType3 — Vertical Scale Indicator (128×128 px)
// Layout: 3 stacked rows — large glowing value + unit + horizontal bar + dot
// Colors: Green (low) → Amber (mid) → Red (high)
// No severity badges. Gradient communicates severity. No animations.
export default function TileType3({
  label = 'Temps',
  values = [42, 65, 80],
  unit = '°C',
  min = 0,
  max = 100,
}) {
  const rowData = [
    { val: values[0] ?? 0, color: '#00FF7F' }, // Low  → Neon Green
    { val: values[1] ?? 0, color: '#FFAA00' }, // Mid  → Amber
    { val: values[2] ?? 0, color: '#FF3B3B' }, // High → Red
  ];

  const toFill = (val) =>
    `${Math.min(Math.max((Number(val) - min) / ((max - min) || 1), 0), 1) * 100}%`;

  return (
    <div style={{
      width: '100%', height: '100%',
      background: '#030d07',
      border: '1px solid rgba(0,255,127,0.07)',
      borderRadius: 12,
      boxSizing: 'border-box',
      display: 'flex', flexDirection: 'column',
      padding: '7px 10px 6px',
      fontFamily: "'Inter', sans-serif",
      position: 'relative', overflow: 'hidden',
      gap: 0,
    }}>

      {/* Scanline texture */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0, borderRadius: 12,
        backgroundImage:
          'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.10) 3px, rgba(0,0,0,0.10) 4px)',
      }} />

      {/* LABEL — top left only, no badge */}
      <div style={{
        fontSize: 9, fontWeight: 700, letterSpacing: '0.13em',
        textTransform: 'uppercase', color: 'rgba(255, 255, 255, 0.95)',
        marginBottom: 4, zIndex: 1,
      }}>
        {label.slice(0, 14)}
      </div>

      {/* 3 ROWS */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-around', zIndex: 1 }}>
        {rowData.map(({ val, color }, i) => {
          const numStr = String(Number.isInteger(Number(val)) ? val : Number(val).toFixed(1));
          const valFs = numStr.length <= 2 ? 22 : numStr.length <= 3 ? 20 : 17;

          return (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Value row: number + unit + dot */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 0 }}>
                {/* Large glowing value */}
                <span style={{
                  fontSize: valFs,
                  fontWeight: 900,
                  fontFamily: "'Orbitron', sans-serif",
                  color: color,
                  lineHeight: 1,
                  textShadow: `0 0 14px ${color}88, 0 0 4px ${color}cc`,
                  letterSpacing: '-0.02em',
                }}>
                  {numStr.slice(0, 4)}
                </span>
                {/* Unit */}
                <span style={{
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: "'Orbitron', sans-serif",
                  color: 'rgba(255,255,255,0.4)',
                  marginLeft: 4,
                  lineHeight: 1,
                  alignSelf: 'center',
                }}>
                  {unit.slice(0, 3)}
                </span>
                {/* Spacer + dot on right */}
                <div style={{ flex: 1 }} />
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: color,
                  boxShadow: `0 0 8px ${color}cc`,
                  display: 'inline-block', alignSelf: 'center',
                  flexShrink: 0,
                }} />
              </div>

              {/* Horizontal progress bar */}
              <div style={{
                width: '100%', height: 4,
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 3, overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: toFill(val),
                  background: `linear-gradient(90deg, ${color}55, ${color})`,
                  borderRadius: 3,
                  boxShadow: `0 0 6px ${color}66`,
                }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
