import React from 'react';

function polarXY(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx, cy, r, startDeg, endDeg) {
  const s = polarXY(cx, cy, r, startDeg);
  const e = polarXY(cx, cy, r, endDeg);
  const large = (endDeg - startDeg) > 180 ? 1 : 0;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
}

// TileType4 — Circular Arc Gauge matching user reference image
// Layout: top label, large 270° neon green arc in upper half, value + unit inside arc center
export default function TileType4({
  label = 'Gauge',
  value = 0,
  unit = '%',
  min = 0,
  max = 100,
}) {
  const num = Number(value);
  const pct = Math.min(Math.max((num - min) / ((max - min) || 100), 0), 1);

  const neonGreen = '#20ed38ef';

  const disp = Number.isInteger(num) ? String(num) : num.toFixed(1);
  const valFs = disp.length <= 2 ? 40 : disp.length <= 3 ? 32 : 24;

  // Arc geometry — centered in the SVG viewbox
  // 270° arc: starts at ~135° (bottom-left) sweeps clockwise to ~45° (bottom-right)
  const CX = 56, CY = 60, R = 44;
  const START = 225, SWEEP = 270; // Gap centered at bottom (180°)
  const endAngle = START + pct * SWEEP;

  return (
    <div style={{
      width: '100%',
      height: '100%',
      background: '#080f1a',
      border: '1px solid rgba(0,255,127,0.08)',
      borderRadius: 12,
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      padding: '10px 12px 8px',
      fontFamily: "'Inter', sans-serif",
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* TOP: Label */}
      <div style={{
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color: 'rgba(249, 246, 246, 0.97)',
        lineHeight: 1,
        marginBottom: 4,
      }}>
        {label.slice(0, 14)}
      </div>

      {/* UPPER HALF: Arc + centered value/unit */}
      <div style={{
        flex: 1,
        position: 'relative',
      }}>
        {/* SVG arc */}
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 112 112"
          style={{ display: 'block' }}
        >
          <defs>
            <filter id="t4glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Track */}
          <path
            d={arcPath(CX, CY, R, START, START + SWEEP)}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Active neon green arc */}
          {pct > 0 && (
            <path
              d={arcPath(CX, CY, R, START, endAngle)}
              fill="none"
              stroke={neonGreen}
              strokeWidth="12"
              strokeLinecap="round"
              filter="url(#t4glow)"
            />
          )}

          {/* Value text — positioned at arc center, shifted up to sit inside arc */}
          <text
            x={CX}
            y={CY - 4}
            textAnchor="middle"
            dominantBaseline="middle"
            fontFamily="'Orbitron', sans-serif"
            fontSize={valFs * 0.90}
            fontWeight="900"
            fill="#FFFFFF"
            style={{ filter: 'drop-shadow(0 0 4px rgba(255,255,255,0.5))' }}
          >
            {disp.slice(0, 5)}
          </text>

          {/* Unit text — below value, clearly visible */}
          <text
            x={CX}
            y={CY + valFs * 0.62 * 0.6 + 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fontFamily="'Orbitron', sans-serif"
            fontSize="10"
            fontWeight="700"
            fill="rgba(255,255,255,0.7)"
            letterSpacing="1"
          >
            {unit.slice(0, 6)}
          </text>
        </svg>
      </div>

    </div>
  );
}
