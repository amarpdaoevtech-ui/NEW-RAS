import React from 'react';

// TileType5 — Big Matrix Graph Visualization — No Animations
// Layout: Top label + legend, Large SVG graph with glowing multi-line streams,
//         Y-axis values left, X-axis ticks bottom, bottom stat cards
export default function TileType5({
  label = 'LIVE TELEMETRY',
  data = [
    { id: '1', label: 'SPD', value: 59,  unit: 'km/h', color: '#F59E0B', history: [30,35,42,40,55,58,52,59,57,59] },
    { id: '2', label: 'VOLT', value: 64,  unit: 'V',    color: '#38BDF8', history: [70,68,65,66,64,63,65,67,64,64] },
    { id: '3', label: 'CURR', value: 29,  unit: 'A',    color: '#00FF7F', history: [20,22,26,30,28,32,31,28,30,29] },
    { id: '4', label: 'TEMP', value: 28,  unit: '°C',   color: '#F43F5E', history: [24,25,26,26,27,28,27,28,28,28] },
  ],
}) {
  const streams = data.slice(0, 4);

  // Graph dimensions (in viewBox units)
  const GW = 520, GH = 270;
  const PAD_L = 38, PAD_R = 14, PAD_T = 28, PAD_B = 62;
  const PW = GW - PAD_L - PAD_R;
  const PH = GH - PAD_T - PAD_B;

  // Build a smooth cubic bezier path from a history array
  function buildPath(history, minV, maxV) {
    if (!history || history.length < 2) return null;
    const rng = (maxV - minV) || 1;
    const pts = history.map((v, i) => ({
      x: PAD_L + (i / (history.length - 1)) * PW,
      y: PAD_T + PH - ((v - minV) / rng) * PH,
    }));
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      const p = pts[i - 1], c = pts[i];
      const cpX = (p.x + c.x) / 2;
      d += ` C ${cpX} ${p.y}, ${cpX} ${c.y}, ${c.x} ${c.y}`;
    }
    return { d, pts, lastPt: pts[pts.length - 1] };
  }

  // Shared min/max across all streams for consistent Y axis
  const allVals = streams.flatMap(s => s.history || [s.value]);
  const globalMin = Math.floor(Math.min(...allVals, 0) / 10) * 10;
  const globalMax = Math.ceil(Math.max(...allVals, 100) / 10) * 10;

  // Y axis ticks: 5 evenly spaced
  const yTicks = Array.from({ length: 5 }, (_, i) =>
    Math.round(globalMin + (i / 4) * (globalMax - globalMin))
  );

  // X axis ticks
  const xSteps = 5;
  const xTicks = Array.from({ length: xSteps }, (_, i) => {
    const offset = (xSteps - 1 - i);
    return offset === 0 ? 'NOW' : `T-${offset}`;
  });

  return (
    <div style={{
      width: '100%', height: '100%',
      background: 'linear-gradient(160deg, #05120d 0%, #030a0f 100%)',
      border: '1px solid rgba(0,255,127,0.08)',
      borderRadius: 12,
      position: 'relative',
      overflow: 'hidden',
      fontFamily: "'Orbitron', sans-serif",
    }}>

      {/* Scanline texture */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0, borderRadius: 12,
        backgroundImage:
          'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.08) 3px, rgba(0,0,0,0.08) 4px)',
      }} />

      {/* SVG GRAPH */}
      <svg
        width="100%" height="100%"
        viewBox={`0 0 ${GW} ${GH}`}
        preserveAspectRatio="none"
        style={{ position: 'absolute', inset: 0, zIndex: 1 }}
      >
        <defs>
          {/* Area fill gradients per stream */}
          {streams.map(s => (
            <linearGradient key={s.id} id={`t5fg_${s.id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor={s.color} stopOpacity="0.30" />
              <stop offset="100%" stopColor={s.color} stopOpacity="0.02" />
            </linearGradient>
          ))}
          {/* Glow filters */}
          {streams.map(s => (
            <filter key={s.id} id={`t5gl_${s.id}`} x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          ))}
        </defs>

        {/* Y Axis line */}
        <line
          x1={PAD_L} y1={PAD_T} x2={PAD_L} y2={PAD_T + PH}
          stroke="rgba(255,255,255,0.18)" strokeWidth="1"
        />
        {/* X Axis line */}
        <line
          x1={PAD_L} y1={PAD_T + PH} x2={PAD_L + PW} y2={PAD_T + PH}
          stroke="rgba(255,255,255,0.18)" strokeWidth="1"
        />

        {/* Y axis grid + labels */}
        {yTicks.map((v, i) => {
          const y = PAD_T + PH - ((v - globalMin) / ((globalMax - globalMin) || 1)) * PH;
          return (
            <g key={i}>
              <line
                x1={PAD_L} y1={y} x2={PAD_L + PW} y2={y}
                stroke="rgba(255,255,255,0.05)" strokeWidth="1"
                strokeDasharray={i === 0 ? 'none' : '5 5'}
              />
              <text
                x={PAD_L - 5} y={y + 4}
                textAnchor="end" fontSize="9"
                fill="rgba(255,255,255,0.35)"
                fontFamily="'Orbitron', sans-serif"
              >{v}</text>
            </g>
          );
        })}

        {/* X axis grid + labels */}
        {xTicks.map((t, i) => {
          const x = PAD_L + (i / (xTicks.length - 1)) * PW;
          return (
            <g key={i}>
              {i > 0 && (
                <line
                  x1={x} y1={PAD_T} x2={x} y2={PAD_T + PH}
                  stroke="rgba(255,255,255,0.04)" strokeWidth="1"
                  strokeDasharray="5 5"
                />
              )}
              <text
                x={x} y={PAD_T + PH + 14}
                textAnchor="middle" fontSize="8.5"
                fill="rgba(255,255,255,0.3)"
                fontFamily="'Orbitron', sans-serif"
              >{t}</text>
            </g>
          );
        })}

        {/* Line paths + area fills */}
        {streams.map(s => {
          const res = buildPath(s.history || [s.value], globalMin, globalMax);
          if (!res) return null;
          const { d, lastPt } = res;
          const fillD = `${d} L ${lastPt.x} ${PAD_T + PH} L ${PAD_L} ${PAD_T + PH} Z`;
          return (
            <g key={s.id}>
              {/* Area fill */}
              <path d={fillD} fill={`url(#t5fg_${s.id})`} />
              {/* Glowing line */}
              <path
                d={d} fill="none"
                stroke={s.color} strokeWidth="2.5"
                strokeLinejoin="round" strokeLinecap="round"
                filter={`url(#t5gl_${s.id})`}
                opacity="0.95"
              />
              {/* End dot */}
              <circle cx={lastPt.x} cy={lastPt.y} r="4" fill={s.color}
                filter={`url(#t5gl_${s.id})`} />
            </g>
          );
        })}

        {/* TOP LABEL only — no legend (bottom cards already show streams) */}
        <text
          x={PAD_L} y={20}
          fontSize="11" fontWeight="700"
          fill="rgba(255,255,255,0.85)"
          fontFamily="'Orbitron', sans-serif"
          letterSpacing="2"
        >
          {label.slice(0, 20)}
        </text>

        {/* BOTTOM STAT CARDS */}
        {streams.map((s, i) => {
          const cardW = PW / 4;
          const cx = PAD_L + i * cardW;
          const cy = PAD_T + PH + 14;
          const cardH = 42;
          const valStr = String(Number.isInteger(Number(s.value)) ? s.value : Number(s.value).toFixed(1));
          return (
            <g key={s.id}>
              {/* Card bg */}
              <rect x={cx + 3} y={cy} width={cardW - 7} height={cardH}
                rx="6" fill="rgba(6,10,18,0.95)"
                stroke={s.color} strokeWidth="0.8" strokeOpacity="0.45"
              />
              {/* Label */}
              <text x={cx + 10} y={cy + 14} fontSize="8.5" fill="rgba(255,255,255,0.55)"
                fontFamily="'Orbitron', sans-serif" fontWeight="700"
                letterSpacing="1">
                {s.label.slice(0, 5)}
              </text>
              {/* Value */}
              <text x={cx + 10} y={cy + 32} fontSize="16" fill={s.color}
                fontFamily="'Orbitron', sans-serif" fontWeight="900">
                {valStr.slice(0, 5)}
              </text>
              {/* Unit */}
              <text x={cx + 10 + valStr.length * 9.5 + 2} y={cy + 32} fontSize="8.5"
                fill="rgba(255,255,255,0.35)" fontFamily="'Orbitron', sans-serif"
                dominantBaseline="auto">
                {s.unit.slice(0, 4)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
