import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiCamera, FiRefreshCw, FiCheck, FiArrowRight, FiRepeat, FiAlertCircle } from 'react-icons/fi';
import CameraStage, { LiveChip, LoadingOverlay } from '../components/CameraStage';
import { useAnalysis } from '../context/AnalysisContext';
import { api } from '../lib/api';
import { blobToDataURL, useCamera } from '../hooks/useCamera';
import { useFrameCheck } from '../hooks/useFrameCheck';

const AUTO_CAPTURE_MS = 1250;
const LOADING_STEPS = [
  'Membaca undertone pergelangan...',
  'Memetakan warna kulit, rambut, mata, dan bibir...',
  'Mencocokkan dengan 12 musim warna...',
];

/** Panduan area pergelangan (oval bawah) + progres auto-capture. */
function WristGuide({ frameSize, ok, progress }) {
  if (!frameSize) return null;
  const [w, h] = frameSize;
  const color = ok ? '#88BCA0' : 'white';
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
  const { check, stableMs, error } = useFrameCheck({ captureFrame, kind: 'wrist', active: live });
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
      <div className="py-24 max-w-md mx-auto text-center space-y-4">
        <FiAlertCircle className="text-4xl text-glowmatch-primary mx-auto" />
        <h1 className="text-2xl font-semibold text-glowmatch-secondary">Foto wajah belum ada</h1>
        <p className="text-gray-500 text-sm">Selesaikan langkah 1 terlebih dahulu.</p>
        <Link to="/scan-wajah" className="inline-block bg-glowmatch-primary text-white px-6 py-3 rounded-xl font-medium">Ke langkah 1</Link>
      </div>
    );
  }

  const messages = status === 'kamera' ? (error ? [error] : check?.messages ?? []) : [];
  const ready = live && (check?.ok || camera.status === 'ready');

  return (
    <div className="py-10 max-w-5xl mx-auto">
      <div className="text-center mb-10">
        <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-3">Langkah 2 Dari 2</p>
        <h1 className="text-4xl font-semibold text-glowmatch-secondary mb-4">Verifikasi undertone</h1>
        <p className="text-gray-500">Arahkan bagian dalam pergelangan tangan ke area panduan, lalu tekan tombol ambil foto.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-start">
        <div className="flex-1 w-full space-y-3">
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
              : <LiveChip label="Posisikan pergelangan di oval" color="bg-amber-400" />)}
            messages={messages}
            overlay={status === 'kamera' && <WristGuide frameSize={frameSize} ok={check?.ok} progress={0} />}
          >
            {status === 'loading' && <LoadingOverlay title={LOADING_STEPS[step]} subtitle="Biasanya beberapa detik" />}
          </CameraStage>
          {status === 'kamera' && (
            <button onClick={() => setFacing((f) => (f === 'user' ? 'environment' : 'user'))}
              className="text-sm text-gray-500 hover:text-glowmatch-primary inline-flex items-center gap-2">
              <FiRepeat /> Ganti kamera depan/belakang
            </button>
          )}
        </div>

        <div className="w-full md:w-[340px] bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
          <div className="w-12 h-12 bg-purple-50 text-glowmatch-primary rounded-2xl flex items-center justify-center mb-6">
            <FiCamera className="text-2xl" />
          </div>
          <h3 className="text-lg font-semibold text-glowmatch-secondary mb-5">Panduan Pengambilan Foto</h3>
          <ul className="space-y-4 mb-6 text-sm text-gray-500">
            <li className="flex items-start gap-3"><FiCheck className="text-[#88BCA0] text-lg mt-0.5 shrink-0" /> Pastikan cahaya cukup: gunakan <strong>lampu HP</strong> atau <strong>bawa lighting sendiri</strong></li>
            <li className="flex items-start gap-3"><FiCheck className="text-[#88BCA0] text-lg mt-0.5 shrink-0" /> Hindari jam tangan atau aksesori gelang</li>
            <li className="flex items-start gap-3"><FiCheck className="text-[#88BCA0] text-lg mt-0.5 shrink-0" /> Buka telapak tangan menghadap atas dengan santai</li>
          </ul>

          {status === 'kamera' && (
            <p className="text-xs text-gray-500 bg-purple-50/70 p-3 rounded-xl mb-6 border border-purple-100">
              📸 <strong>Manual Capture:</strong> Posisikan pergelangan tanganmu, lalu klik tombol ungu di bawah.
            </p>
          )}

          {failure && (
            <div className="mb-5 bg-red-50 border border-red-100 text-red-600 text-sm rounded-xl p-3">
              {failure.message}
              {failure.backToFace && <Link to="/scan-wajah" className="block mt-2 font-semibold underline">Ulangi foto wajah</Link>}
            </div>
          )}

          <div className="flex flex-col gap-3">
            {status === 'kamera' ? (
              <button 
                onClick={ambilFoto} 
                disabled={camera.status !== 'ready'}
                className="w-full bg-glowmatch-primary hover:bg-purple-800 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed text-white py-4 rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 text-base active:scale-95"
              >
                <FiCamera className="text-xl" /> Ambil Foto Sekarang
              </button>
            ) : status === 'diambil' ? (
              <div className="flex gap-3">
                <button onClick={() => setStatus('kamera')} className="flex-1 bg-white border border-gray-200 hover:bg-gray-50 text-gray-600 py-3.5 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 text-sm">
                  <FiRefreshCw className="text-base" /> Ulangi
                </button>
                <button onClick={() => analyze(true)} className="flex-[1.2] bg-glowmatch-primary hover:bg-purple-800 text-white py-3.5 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 text-sm">
                  Analisis <FiArrowRight className="text-base" />
                </button>
              </div>
            ) : (
              <button disabled className="w-full bg-gray-200 text-gray-400 py-3.5 rounded-xl font-semibold cursor-not-allowed">Memproses...</button>
            )}
            {status !== 'loading' && (
              <button onClick={() => analyze(false)} className="text-center text-sm text-gray-500 hover:text-glowmatch-primary font-medium">
                Lewati, analisis dari wajah saja
              </button>
            )}
            <Link to="/scan-wajah" className="text-center text-sm text-gray-400 hover:text-gray-600 mt-1 font-medium">Kembali ke langkah 1</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanUndertone;
