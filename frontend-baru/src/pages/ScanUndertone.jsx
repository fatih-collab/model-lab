import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiCamera, FiRefreshCw, FiArrowRight, FiRepeat } from 'react-icons/fi';
import CameraStage, { LiveChip, LoadingOverlay } from '../components/CameraStage';
import { ScanHeader, ScanTips } from '../components/ScanParts';
import { useAnalysis } from '../context/AnalysisContext';
import { api } from '../lib/api';
import { blobToDataURL, useCamera } from '../hooks/useCamera';
import { useFrameCheck } from '../hooks/useFrameCheck';

const LOADING_STEPS = [
  'Membaca undertone pergelangan...',
  'Memetakan warna kulit, rambut, mata, dan bibir...',
  'Mencocokkan dengan 12 season warna...',
];

const TIPS = [
  'Cahaya cukup dari lampu HP atau lampu sendiri.',
  'Lepas jam tangan dan gelang.',
  'Buka telapak tangan menghadap atas.',
];

/** Panduan area pergelangan (oval bawah) + progres auto-capture. */
function WristGuide({ frameSize, ok, progress }) {
  if (!frameSize) return null;
  const [w, h] = frameSize;
  const color = ok ? '#c9d6a0' : '#fbf7ec';
  const props = { cx: w / 2, cy: h * 0.62, rx: w * 0.25, ry: h * 0.24, fill: 'none' };
  return (
    <g>
      <ellipse {...props} stroke={color} strokeOpacity="0.8" strokeWidth={h * 0.006} strokeDasharray={`${h * 0.02} ${h * 0.015}`} />
      {progress > 0 && (
        <ellipse {...props} stroke={color} strokeWidth={h * 0.012} strokeLinecap="round" pathLength="1"
          strokeDasharray={`${Math.min(1, progress)} 1`} />
      )}
    </g>
  );
}

const ScanUndertone = () => {
  const [status, setStatus] = useState('kamera'); // kamera | diambil | loading
  const [facing, setFacing] = useState('user');
  const [wrist, setWrist] = useState(null); // { blob, photo }
  const [failure, setFailure] = useState(null); // { message, backToFace }
  const [step, setStep] = useState(0);
  const capturing = useRef(false);
  const navigate = useNavigate();
  const { face, faceBlob, finishAnalysis } = useAnalysis();

  const camera = useCamera({ facingMode: facing, enabled: Boolean(face) });
  const { captureFrame } = camera;
  const live = status === 'kamera' && camera.status === 'ready';
  const { check, error } = useFrameCheck({ captureFrame, kind: 'wrist', active: live });
  const frameSize = check?.frame_size ?? (camera.videoSize && [camera.videoSize.w, camera.videoSize.h]);

  const ambilFoto = useCallback(async () => {
    if (capturing.current) return;
    capturing.current = true;
    try {
      const frame = await captureFrame(1280, 0.92);
      if (!frame) return;
      setWrist({ blob: frame.blob, photo: await blobToDataURL(frame.blob) });
      setFailure(null);
      setStatus('diambil');
    } finally {
      capturing.current = false;
    }
  }, [captureFrame]);

  useEffect(() => {
    if (status !== 'loading') return undefined;
    const id = setInterval(() => setStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1)), 1800);
    return () => clearInterval(id);
  }, [status]);

  /** Wajah + pergelangan -> /api/analyze (satu request: undertone dulu, lalu season, lalu gatekeeper). */
  const analyze = async (withWrist) => {
    setStatus('loading');
    setStep(0);
    setFailure(null);
    try {
      const faceData = faceBlob ?? (await (await fetch(face.photo)).blob()); // blob hilang setelah refresh
      const res = await api.analyze({ face: faceData, wrist: withWrist ? wrist.blob : undefined });
      if (res.status === 'rejected') {
        setFailure({
          message: res.messages?.join(' ') || 'Foto belum memenuhi syarat kualitas.',
          backToFace: res.stage === 'face',
        });
        setStatus(res.stage === 'wrist' ? 'kamera' : 'diambil');
        return;
      }
      finishAnalysis(res);
      navigate('/hasil');
    } catch (err) {
      setFailure({ message: err.message });
      setStatus(withWrist ? 'diambil' : 'kamera');
    }
  };

  if (!face) {
    return (
      <div className="gm-rise py-28 max-w-lg mx-auto text-center space-y-8">
        <h1 className="gm-display text-[52px] sm:text-[64px]">Foto wajah <em>belum ada.</em></h1>
        <Link to="/scan-wajah" className="gm-btn">Ke langkah pertama <FiArrowRight /></Link>
      </div>
    );
  }

  const messages = status === 'kamera' ? (error ? [error] : check?.messages ?? []) : [];

  return (
    <div className="pt-8 pb-4 max-w-6xl mx-auto">
      <ScanHeader title="Verifikasi" accent="undertone." step="02" />

      <div className="grid lg:grid-cols-[1fr_360px] gap-8 items-start">
        <div className="gm-rise space-y-4" style={{ '--d': '160ms' }}>
          <CameraStage
            videoRef={camera.videoRef} cameraStatus={camera.status} cameraError={camera.error}
            mirrored={facing === 'user'}
            frameSize={frameSize}
            frozenSrc={status !== 'kamera' ? wrist?.photo : null}
            highlight={status === 'diambil'}
            hasTorch={camera.hasTorch}
            torchOn={camera.torchOn}
            onToggleTorch={camera.setTorch}
            chip={live && (check?.ok ? <LiveChip label="Pergelangan terdeteksi" />
              : <LiveChip label="Posisikan pergelangan di oval" color="bg-coral" />)}
            messages={messages}
            overlay={status === 'kamera' && <WristGuide frameSize={frameSize} ok={check?.ok} progress={0} />}
          >
            {status === 'loading' && <LoadingOverlay title={LOADING_STEPS[step]} />}
          </CameraStage>
          {status === 'kamera' && (
            <button
              type="button"
              onClick={() => setFacing((f) => (f === 'user' ? 'environment' : 'user'))}
              className="gm-btn-ghost gm-btn-sm"
            >
              <FiRepeat /> Ganti kamera
            </button>
          )}
        </div>

        <aside className="gm-card gm-rise p-7 sm:p-8" style={{ '--d': '260ms' }}>
          <ScanTips tips={TIPS} />

          {failure && (
            <div className="gm-open mt-6 rounded-2xl border border-[#ecc3d6] bg-[#fbeef3] text-accent text-[14px] p-4 leading-relaxed">
              {failure.message}
              {failure.backToFace && <Link to="/scan-wajah" className="gm-link block mt-2 text-accent">Ulangi foto wajah</Link>}
            </div>
          )}

          <div className="flex flex-col gap-3 mt-8">
            {status === 'kamera' ? (
              <button
                type="button"
                onClick={ambilFoto}
                disabled={camera.status !== 'ready'}
                className="gm-btn w-full py-4"
              >
                <FiCamera className="text-lg" /> Ambil foto
              </button>
            ) : status === 'diambil' ? (
              <div className="gm-open flex gap-3">
                <button type="button" onClick={() => setStatus('kamera')} className="gm-btn-ghost flex-1">
                  <FiRefreshCw /> Ulangi
                </button>
                <button type="button" onClick={() => analyze(true)} className="gm-btn flex-[1.3]">
                  Analisis <FiArrowRight />
                </button>
              </div>
            ) : (
              <button type="button" disabled className="gm-btn w-full py-4">Memproses...</button>
            )}
            {status !== 'loading' && (
              <button type="button" onClick={() => analyze(false)} className="gm-btn-ghost w-full">
                Analisis dari wajah saja
              </button>
            )}
            <Link to="/scan-wajah" className="gm-link self-center text-[14px] text-gray-500 mt-2">Kembali</Link>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default ScanUndertone;
