import { useState, useEffect, useRef } from 'react';

/**
 * Hook that animates a number from a start value to a target value.
 * Uses requestAnimationFrame for smooth 60 fps animation.
 * @param {number} target   Final value to animate to.
 * @param {object} options  { duration: ms, start: initialValue }
 * @returns {number} Current animated value (rounded).
 */
export const useCountUp = (target, { duration = 800, start = 0 } = {}) => {
  const [value, setValue] = useState(start);
  const startTimestamp = useRef(null);

  useEffect(() => {
    const step = (timestamp) => {
      if (!startTimestamp.current) startTimestamp.current = timestamp;
      const elapsed = timestamp - startTimestamp.current;
      const progress = Math.min(elapsed / duration, 1);
      const current = start + (target - start) * progress;
      setValue(current);
      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };
    requestAnimationFrame(step);
    return () => {
      startTimestamp.current = null;
    };
  }, [target, duration, start]);

  return Math.round(value);
};
