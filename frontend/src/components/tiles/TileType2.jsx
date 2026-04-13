import React from 'react';

/**
 * TileType2 — Progress Bar Display Tile (128×128 px)
 *
 * Fields : label | value | unit | min | max
 *
 * Core logic:
 *   normalizedValue = (currentValue - min) / (max - min)
 *   → clamp result to [0, 1]
 *   → controls progress bar fill width
 *
 * Edge cases:
 *   min === max          → progress = 1  (neutral/full state, avoids ÷0)
 *   value < min          → progress = 0  (clamp bottom)
 *   value > max          → progress = 1  (clamp top)
 *   missing/null value   → N/A fallback, bar shows empty track
 *
 * Important:
 *   The displayed value is ALWAYS the raw value + unit (never re-calculated).
 *   The normalization ONLY drives the progress bar — not the displayed text.
 *   This means a % value (e.g. soc=82) shows "82 %" and bar at 82/100 — no double-percentage.
 */

// ─── Pure helpers ────────────────────────────────────────────────────────────

function toSafeNumber(raw, fallback = null) {
  if (raw === null || raw === undefined) return fallback;
  const n = Number(raw);
  return isNaN(n) ? fallback : n;
}

function formatValue(num) {
  return Number.isInteger(num) ? String(num) : num.toFixed(1);
}

/**
 * Core: Min-Max Normalization
 * Returns a value in [0, 1] — always clamped, always safe.
 */
function normalize(value, min, max) {
  const range = max - min;

  // Edge case: min === max → avoid division by zero, return neutral full state
  if (range === 0) return 1;

  // Core formula
  const raw = (value - min) / range;

  // Clamp: value < min → 0, value > max → 1
  return Math.min(Math.max(raw, 0), 1);
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function TileType2({
  label = 'DATA',
  value,         // current value — may be null/undefined
  unit  = '',
  min   = 0,
  max   = 100,
}) {
  // ── Step 1: Resolve all inputs to safe numbers ────────────────────────────
  const num     = toSafeNumber(value, null);
  const safeMin = toSafeNumber(min, 0);
  const safeMax = toSafeNumber(max, 100);
  const isValid = num !== null;

  // ── Step 2: Min-Max Normalization (ONLY for bar — NOT for displayed value) ─
  const progress = isValid
    ? normalize(num, safeMin, safeMax)
    : 0; // if no valid value, bar stays empty

  // ── Step 3: Format display value ──────────────────────────────────────────
  //   Raw value is shown AS-IS with its unit.
  //   No re-normalization of percentage values.
  const displayValue = isValid ? formatValue(num) : 'N/A';

  // ── Step 4: Bar color based on progress position ───────────────────────────
  //   low (0–20%)  = red | mid (20–60%) = amber | high (60–100%) = green
  const barColor = !isValid
    ? 'rgba(255,255,255,0.15)'
    : progress < 0.2  ? '#FF3B3B'
    : progress < 0.6  ? '#F59E0B'
    :                   '#00e87a';

  // ── Step 5: Adaptive font size (128px tile) ───────────────────────────────
  const len = displayValue.length;
  const fs  = len <= 3 ? 36 : len <= 5 ? 26 : 18;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{
      width: '100%',
      height: '100%',
      background: 'linear-gradient(145deg, #0d121b 0%, #05080c 100%)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 14,
      padding: '12px',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Inter', sans-serif",
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* ── LABEL ── */}
      <div style={{
        fontSize: 8,
        fontWeight: 800,
        letterSpacing: '0.15em',
        textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.38)',
        userSelect: 'none',
        marginBottom: 4,
      }}>
        {label}
      </div>

      {/* ── VALUE + UNIT (raw, never re-normalized) ── */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'baseline',
        gap: 4,
        marginTop: 2,
      }}>
        <span style={{
          fontSize: fs,
          fontWeight: 900,
          fontFamily: "'Orbitron', sans-serif",
          color: isValid ? '#ffffff' : 'rgba(255,255,255,0.25)',
          lineHeight: 1,
        }}>
          {displayValue}
        </span>
        {(unit && isValid) && (
          <span style={{
            fontSize: 9,
            fontWeight: 700,
            fontFamily: "'Orbitron', sans-serif",
            color: 'rgba(255,255,255,0.38)',
          }}>
            {unit}
          </span>
        )}
      </div>

      {/* ── PROGRESS BAR ── */}
      <div style={{ marginTop: 'auto' }}>

        {/* Track — always visible so tile shape is clear even at value=0 */}
        <div style={{
          position: 'relative',
          height: 8,
          background: 'rgba(255,255,255,0.08)',
          borderRadius: 4,
          overflow: 'visible',
        }}>

          {/* Fill — width driven purely by normalized value */}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            height: '100%',
            width: `${progress * 100}%`,
            background: `linear-gradient(90deg, ${barColor}70, ${barColor})`,
            borderRadius: 4,
            boxShadow: isValid ? `0 0 8px ${barColor}55` : 'none',
            // Smooth transition when live data updates
            transition: 'width 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
          }} />

          {/* Knob — always visible at current position, anchored via clamp */}
          <div style={{
            position: 'absolute',
            top: '50%',
            left: `clamp(3px, calc(${progress * 100}% ), calc(100% - 4px))`,
            transform: 'translate(-50%, -50%)',
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: isValid ? '#ffffff' : 'rgba(255,255,255,0.25)',
            boxShadow: isValid
              ? `0 0 5px ${barColor}, 0 0 10px ${barColor}55`
              : 'none',
            zIndex: 2,
          }} />
        </div>

        {/* Min / Max labels — always show the range for context */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 5,
          fontSize: 7,
          fontWeight: 800,
          fontFamily: "'Orbitron', sans-serif",
          color: 'rgba(255,255,255,0.22)',
          letterSpacing: '0.05em',
          userSelect: 'none',
        }}>
          <span>{safeMin}</span>
          <span>{safeMax}</span>
        </div>
      </div>
    </div>
  );
}
