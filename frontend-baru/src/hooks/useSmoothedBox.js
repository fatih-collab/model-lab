import { useEffect, useRef, useState } from 'react';

/**
 * Box wajah dari server datang ~4x/detik; interpolasi tiap animation frame supaya cincin palet
 * mengikuti wajah dengan halus, bukan melompat.
 */
export function useSmoothedBox(target, factor = 0.25) {
  const [box, setBox] = useState(target);
  const goal = useRef(target);

  useEffect(() => {
    goal.current = target;
  }, [target]);

  useEffect(() => {
    let raf;
    let cur = goal.current;
    const tick = () => {
      const g = goal.current;
      const next = g && cur ? cur.map((v, i) => v + (g[i] - v) * factor) : g;
      const moved = !next || !cur ? next !== cur : next.some((v, i) => Math.abs(v - cur[i]) > 0.1);
      if (moved) {
        cur = next;
        setBox(next);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [factor]);

  return box;
}
