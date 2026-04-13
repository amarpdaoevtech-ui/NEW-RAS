import React from 'react';

/**
 * TileType1 — Basic Display Tile (128×128 px)
 *
 * Fields  : label | value | unit
 * Format  : absolute (e.g. 1200 W) OR percentage (e.g. 75 %)
 *           — determined by the supplied unit & data, NOT re-calculated here
 * Fallback: null / undefined / NaN  → shows "N/A"
 */

// ─── Pure helpers ────────────────────────────────────────────────────────────

/**
 * Resolve a raw prop value to a safe number or null.
 * Returns null when the input is missing / non-numeric so the UI can show N/A.
 */
function toSafeNumber(raw) {
  if (raw === null || raw === undefined) return null;
  const n = Number(raw);
  return isNaN(n) ? null : n;
}

/**
 * Format a number for display.
 *  - Integers  → no decimal  (e.g. 82)
 *  - Floats    → 1 decimal   (e.g. 24.5)
 */
function formatValue(num) {
  return Number.isInteger(num) ? String(num) : num.toFixed(1);
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function TileType1({
  label = 'DATA',
  value,           // raw value from backend — may be null/undefined
  unit  = '',
  color = '#00ddff',
}) {
  // ── Step 1: Resolve value ──────────────────────────────────────────────────
  const num     = toSafeNumber(value);
  const isValid = num !== null;

  // ── Step 2: Format for display ─────────────────────────────────────────────
  //   • If valid  → format the number as-is (absolute or %)
  //   • If invalid → "N/A" fallback
  const displayValue = isValid ? formatValue(num) : 'N/A';

  // ── Step 3: Adaptive font size (Orbitron, 128px tile) ─────────────────────
  const len = displayValue.length;
  const fs  = len <= 3 ? 42 : len <= 5 ? 32 : 22;

  // ── Step 4: Render ─────────────────────────────────────────────────────────
  return (
    <div style={{
      width: '100%',
      height: '100%',
      background: 'linear-gradient(145deg, #0d121b 0%, #05080c 100%)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 14,
      padding: '14px 16px',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      fontFamily: "'Inter', sans-serif",
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* ── LABEL ── */}
      <div style={{
        fontSize: 9,
        fontWeight: 800,
        letterSpacing: '0.15em',
        textTransform: 'uppercase',
        color: 'rgba(255,255,255,0.38)',
        userSelect: 'none',
      }}>
        {label}
      </div>

      {/* ── VALUE + UNIT ── */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: 3,
      }}>
        {/* VALUE */}
        <div style={{
          fontSize: fs,
          fontWeight: 900,
          fontFamily: "'Orbitron', sans-serif",
          color: isValid ? color : 'rgba(255,255,255,0.25)',
          lineHeight: 1,
          textShadow: isValid ? `0 0 12px ${color}44` : 'none',
          letterSpacing: '-0.01em',
        }}>
          {displayValue}
        </div>

        {/* UNIT — only shown when there is a valid value */}
        {(unit && isValid) && (
          <div style={{
            fontSize: 11,
            fontWeight: 700,
            fontFamily: "'Orbitron', sans-serif",
            color: 'rgba(255,255,255,0.55)',
            letterSpacing: '0.06em',
          }}>
            {unit}
          </div>
        )}
      </div>

      {/* ── Decorative corner glow ── */}
      <div style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '55%',
        height: '55%',
        background: `radial-gradient(circle at top right, ${color}12, transparent 70%)`,
        pointerEvents: 'none',
      }} />
    </div>
  );
}
