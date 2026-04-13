import React from 'react';

// TileType6 — Multistate Indicator (128×128 px) — No Animations
// Design: Ruggedized dark metal module with:
//   - Glowing border (teal-cyan bottom-left → red-orange top-right)
//   - Large segmented LED display showing active state label
//   - Bank of 4 circular port indicators (active one glows)
//   - Faux hex-screw corners for industrial realism
//   - Top-left label badge
export default function TileType6({
  label         = 'GEAR STATE',
  state         = 4,
  state_1_label = 'PARK',    state_2_label = 'REV',
  state_3_label = 'NEUT',   state_4_label = 'DRIVE',
  state_1_color = '#64748B', state_2_color = '#F59E0B',
  state_3_color = '#38BDF8', state_4_color = '#00e5a0',
}) {
  const stateList = [
    { id: 1, label: state_1_label, color: state_1_color },
    { id: 2, label: state_2_label, color: state_2_color },
    { id: 3, label: state_3_label, color: state_3_color },
    { id: 4, label: state_4_label, color: state_4_color },
  ].filter(s => s.label);

  const active = stateList.find(s => s.id === state) || stateList[stateList.length - 1];
  const ac = active.color; // active color shorthand

  // Screw positions (corner offsets)
  const screws = [
    { cx: 8,  cy: 8  },
    { cx: 120, cy: 8  },
    { cx: 8,  cy: 120 },
    { cx: 120, cy: 120 },
  ];

  return (
    <div style={{
      width: '100%', height: '100%',
      position: 'relative',
      borderRadius: 12,
      boxSizing: 'border-box',
      overflow: 'hidden',
      // Brushed metal dark background with subtle texture
      background: 'linear-gradient(160deg, #131a1f 0%, #0a1014 50%, #111820 100%)',
      // Multi-stop glowing border: teal bottom-left → red-orange top-right
      border: '1.5px solid transparent',
      backgroundClip: 'padding-box',
    }}>

      {/* Glowing border overlay using box-shadow + gradient border trick */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: 12, zIndex: 0, pointerEvents: 'none',
        boxShadow: `
          inset 0 0 0 1.5px rgba(0,229,160,0.0),
          0 0 0 1.5px transparent,
          -2px 2px 0 0 #00e5a0,
          2px -2px 0 0 #ff5533
        `,
        // Actual gradient border via outline trick
        background: 'linear-gradient(#131a1f, #0a1014) padding-box, linear-gradient(135deg, #00e5a066 0%, #00cfff44 30%, #ff553366 70%, #ff330066 100%) border-box',
        border: '1.5px solid transparent',
      }} />

      {/* Subtle brushed-metal scanline texture */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1, borderRadius: 12,
        backgroundImage:
          'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.015) 2px, rgba(255,255,255,0.015) 3px)',
      }} />

      {/* Ambient glow halo matching active color */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: 12, zIndex: 0, pointerEvents: 'none',
        boxShadow: `inset 0 0 40px ${ac}10, 0 0 30px ${ac}18`,
      }} />

      {/* SVG for corner hex screws + all layout */}
      <svg
        width="100%" height="100%"
        viewBox="0 0 128 128"
        style={{ position: 'absolute', inset: 0, zIndex: 2 }}
      >
        {/* ── HEX SCREWS (4 corners) ── */}
        {screws.map((s, i) => (
          <g key={i}>
            <circle cx={s.cx} cy={s.cy} r="4.5"
              fill="#0d1419" stroke="rgba(255,255,255,0.12)" strokeWidth="0.8" />
            {/* Hex pattern inside screw */}
            <line x1={s.cx - 2} y1={s.cy} x2={s.cx + 2} y2={s.cy}
              stroke="rgba(255,255,255,0.18)" strokeWidth="0.7" />
            <line x1={s.cx - 1} y1={s.cy - 2} x2={s.cx + 1} y2={s.cy + 2}
              stroke="rgba(255,255,255,0.18)" strokeWidth="0.7" />
            <line x1={s.cx - 1} y1={s.cy + 2} x2={s.cx + 1} y2={s.cy - 2}
              stroke="rgba(255,255,255,0.18)" strokeWidth="0.7" />
          </g>
        ))}

        {/* ── LABEL BADGE (top-left) ── */}
        <rect x="14" y="5" width="60" height="13"
          rx="3" fill="rgba(0,0,0,0.5)" stroke="rgba(255,255,255,0.08)" strokeWidth="0.6" />
        <text x="17" y="14.5"
          fontSize="7.5" fontWeight="700"
          fill="rgba(255,255,255,0.45)"
          fontFamily="'Orbitron', sans-serif"
          letterSpacing="1"
        >
          {label.slice(0, 10).toUpperCase()}
        </text>

        {/* ── RECESSED LED DISPLAY (center) ── */}
        {/* Display bezel */}
        <rect x="16" y="24" width="96" height="44"
          rx="5"
          fill="rgba(0,0,0,0.75)"
          stroke="rgba(255,255,255,0.07)" strokeWidth="1"
        />
        {/* Inner glass effect */}
        <rect x="17" y="25" width="94" height="42"
          rx="4" fill="rgba(0,0,0,0.4)"
          stroke={`${ac}22`} strokeWidth="0.5"
        />
        {/* Subtle scanline on LED glass */}
        <rect x="17" y="25" width="94" height="21"
          rx="4" fill="rgba(255,255,255,0.015)" />

        {/* Active state text — large segmented LED font */}
        <text
          x="64" y="54"
          textAnchor="middle" dominantBaseline="middle"
          fontSize="26" fontWeight="900"
          fontFamily="'Orbitron', sans-serif"
          letterSpacing="3"
          fill={ac}
          style={{ filter: `drop-shadow(0 0 8px ${ac}) drop-shadow(0 0 4px ${ac}88)` }}
        >
          {active.label.toUpperCase().slice(0, 6)}
        </text>

        {/* ── INDICATOR BANK (4 circular ports) ── */}
        {/* Bank tray background */}
        <rect x="18" y="76" width="92" height="34"
          rx="6"
          fill="rgba(0,0,0,0.55)"
          stroke="rgba(255,255,255,0.06)" strokeWidth="0.8"
        />

        {stateList.map((s, i) => {
          const isActive = s.id === state;
          const cx = 32 + i * 22;
          const cy = 93;

          return (
            <g key={s.id}>
              {/* Recessed port outer ring */}
              <circle cx={cx} cy={cy} r="9"
                fill="rgba(0,0,0,0.7)"
                stroke={isActive ? `${s.color}60` : 'rgba(255,255,255,0.07)'}
                strokeWidth={isActive ? '1.2' : '0.7'}
              />
              {/* Inner indicator face */}
              <circle cx={cx} cy={cy} r="6.5"
                fill={isActive ? s.color : '#0d1419'}
                style={isActive ? {
                  filter: `drop-shadow(0 0 6px ${s.color}) drop-shadow(0 0 3px ${s.color}aa)`,
                } : {}}
              />
              {/* Shine glint on active */}
              {isActive && (
                <ellipse cx={cx - 1.5} cy={cy - 2} rx="2.5" ry="1.5"
                  fill="rgba(255,255,255,0.35)" />
              )}
              {/* State number label */}
              <text
                x={cx} y={cy + 0.5}
                textAnchor="middle" dominantBaseline="middle"
                fontSize="6" fontWeight="800"
                fontFamily="'Orbitron', sans-serif"
                fill={isActive ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.15)'}
              >
                {s.id}
              </text>
            </g>
          );
        })}

        {/* ── BOTTOM ACCENT LINE ── */}
        <line x1="18" y1="116" x2="110" y2="116"
          stroke={`${ac}33`} strokeWidth="0.8" />
      </svg>
    </div>
  );
}
