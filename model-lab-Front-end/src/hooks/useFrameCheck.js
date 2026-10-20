import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';

/**
 * Loop asinkron: ambil frame kecil -> POST /api/frame/check -> simpan hasil terbaru.
 * - Hanya satu request in-flight (frame tidak menumpuk walau server lambat).
 * - Interval minimum `intervalMs` antar request.
 * - `stableMs`: berapa lama frame berturut-turut lolos quality gate dan wajah tidak bergerak.
 */
export function useFrameCheck({ captureFrame, kind = 'face', active = true, intervalMs = 250, maxSide = 480 }) {
  const [check, setCheck] = useState(null); // respons terakhir /api/frame/check
  const [stableMs, setStableMs] = useState(0);
  const [error, setError] = useState(null);
  const prevRef = useRef(null);

  useEffect(() => {
    if (!active) return undefined;
    const controller = new AbortController();
    let stop = false;
    let stableSince = null;

    async function loop() {
      while (!stop) {
        const started = performance.now();
        try {
          const frame = await captureFrame(maxSide);
          if (frame) {
            const res = await api.checkFrame(frame.blob, kind, controller.signal);
            if (stop) return;
            const now = performance.now();
            if (res.ok && isSteady(prevRef.current, res)) stableSince ??= now;
            else stableSince = res.ok ? now : null;
            prevRef.current = res;
            setCheck(res);
            setStableMs(stableSince ? now - stableSince : 0);
            setError(null);
          }
        } catch (err) {
          if (err.name === 'AbortError' || stop) return;
          setError(err.message);
          stableSince = null;
          setStableMs(0);
          await sleep(1000); // server mati / error: mundur sebentar
        }
        await sleep(Math.max(0, intervalMs - (performance.now() - started)));
      }
    }

    loop();
    return () => {
      stop = true;
      controller.abort();
    };
  }, [active, kind, intervalMs, maxSide, captureFrame]);

  return { check, stableMs: active ? stableMs : 0, error };
}

/** Wajah dianggap diam bila pusat box bergeser < 6% lebar wajah dan ukurannya berubah < 10%. */
function isSteady(prev, cur) {
  if (!prev?.ok) return false;
  if (!cur.box || !prev.box) return true; // pergelangan: tidak ada box, cukup lolos berturut-turut
  const [x0, y0, w0, h0] = prev.box;
  const [x1, y1, w1, h1] = cur.box;
  const shift = Math.hypot(x1 + w1 / 2 - (x0 + w0 / 2), y1 + h1 / 2 - (y0 + h0 / 2));
  return shift < 0.06 * w1 && Math.abs(w1 - w0) < 0.1 * w0;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
