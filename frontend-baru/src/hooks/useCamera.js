import { useCallback, useEffect, useRef, useState } from 'react';

const ERRORS = {
  NotAllowedError: 'Akses kamera ditolak. Izinkan kamera di pengaturan browser lalu muat ulang halaman.',
  NotFoundError: 'Kamera tidak ditemukan di perangkat ini.',
  NotReadableError: 'Kamera sedang dipakai aplikasi lain.',
  OverconstrainedError: 'Kamera tidak mendukung resolusi yang diminta.',
  SecurityError: 'Kamera hanya bisa diakses lewat HTTPS atau localhost.',
};

/**
 * Kamera live via getUserMedia.
 * captureFrame() mengambil frame APA ADANYA (tidak di-mirror) sebagai JPEG Blob; mirror hanya di tampilan.
 */
export function useCamera({ facingMode = 'user', enabled = true } = {}) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const [status, setStatus] = useState('idle'); // idle | starting | ready | error
  const [error, setError] = useState(null);
  const [videoSize, setVideoSize] = useState(null); // { w, h }

  useEffect(() => {
    const video = videoRef.current;
    if (!enabled || !video) return undefined;
    let cancelled = false;

    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setStatus('error');
        setError(ERRORS.SecurityError);
        return;
      }
      setStatus('starting');
      setError(null);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        video.srcObject = stream;
        await video.play().catch(() => {});
        const onReady = () => {
          setVideoSize({ w: video.videoWidth, h: video.videoHeight });
          setStatus('ready');
          try {
            const track = stream.getVideoTracks()[0];
            const caps = track?.getCapabilities?.() || {};
            setHasTorch(Boolean(caps.torch));
          } catch {
            setHasTorch(false);
          }
        };
        if (video.videoWidth) onReady();
        else video.addEventListener('loadedmetadata', onReady, { once: true });
      } catch (err) {
        if (cancelled) return;
        setStatus('error');
        setError(ERRORS[err.name] || `Kamera gagal dibuka (${err.name || err.message}).`);
      }
    }

    start();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (video) video.srcObject = null;
      setStatus('idle');
    };
  }, [facingMode, enabled]);

  const [hasTorch, setHasTorch] = useState(false);
  const [torchOn, setTorchOnState] = useState(false);

  const setTorch = useCallback(async (on) => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (track && track.applyConstraints) {
      try {
        await track.applyConstraints({ advanced: [{ torch: Boolean(on) }] });
        setTorchOnState(Boolean(on));
      } catch (e) {
        console.warn('Gagal mengatur torch kamera:', e);
      }
    }
  }, []);

  /** Frame saat ini -> { blob, width, height } dengan sisi terpanjang <= maxSide. */
  const captureFrame = useCallback(async (maxSide = 640, quality = 0.85) => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return null;
    const scale = Math.min(1, maxSide / Math.max(video.videoWidth, video.videoHeight));
    const width = Math.round(video.videoWidth * scale);
    const height = Math.round(video.videoHeight * scale);
    const canvas = canvasRef.current || (canvasRef.current = document.createElement('canvas'));
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d').drawImage(video, 0, 0, width, height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality));
    return blob ? { blob, width, height } : null;
  }, []);

  return { videoRef, status, error, videoSize, captureFrame, hasTorch, torchOn, setTorch };
}

export function blobToDataURL(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
