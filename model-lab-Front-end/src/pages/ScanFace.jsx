import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiCamera, FiRefreshCw, FiCheck, FiArrowRight } from 'react-icons/fi';
import CameraStage, { LiveChip } from '../components/CameraStage';
import { FaceGuide } from '../components/RadialBurst';
import { useAnalysis } from '../context/AnalysisContext';
import { blobToDataURL, useCamera } from '../hooks/useCamera';
import { useFrameCheck } from '../hooks/useFrameCheck';
import { useSmoothedBox } from '../hooks/useSmoothedBox';

const ScanFace = () => {
  const [status, setStatus] = useState('kamera'); // kamera | diambil
  const [photo, setPhoto] = useState(null);
  const navigate = useNavigate();
  const { captureFace } = useAnalysis();
  const capturing = useRef(false);

  const camera = useCamera();
  const { captureFrame } = camera;
  const live = status === 'kamera' && camera.status === 'ready';
  const { check, stableMs, error } = useFrameCheck({ captureFrame, kind: 'face', active: live });
  const box = useSmoothedBox(live ? check?.box ?? null : photo?.box ?? null);
  const frameSize = status === 'diambil' ? photo?.frameSize : check?.frame_size ?? (camera.videoSize && [camera.videoSize.w, camera.videoSize.h]);

  const ambilFoto = useCallback(async () => {
    if (capturing.current) return;
    capturing.current = true;
    try {
      const frame = await captureFrame(1280, 0.92);
      if (!frame) return;
      const s = check?.frame_size ? frame.width / check.frame_size[0] : 1;
      const info = {
        photo: await blobToDataURL(frame.blob),
        box: check?.box?.map((v) => v * s) ?? null,
        frameSize: [frame.width, frame.height],
      };
      captureFace(frame.blob, info);
      setPhoto(info);
      setStatus('diambil');
    } finally {
      capturing.current = false;
    }
  }, [captureFrame, check, captureFace]);

  const handleUlangi = () => {
    setPhoto(null);
    setStatus('kamera');
  };

  const messages = status === 'kamera' ? (error ? [error] : check?.messages ?? []) : [];
  const ready = live && (check?.ok || camera.status === 'ready');

  return (
    <div className="py-10 max-w-5xl mx-auto">
      <div className="text-center mb-10">
        <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-3">Langkah 1 Dari 2</p>
        <h1 className="text-4xl font-semibold text-glowmatch-secondary mb-4">Analisis wajahmu</h1>
        <p className="text-gray-500">Posisikan wajah di dalam garis panduan, gunakan pencahayaan cukup (lampu HP atau bawa lighting sendiri), lalu tekan tombol ambil foto.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-start">
        <div className="flex-1 w-full">
          <CameraStage
            videoRef={camera.videoRef} cameraStatus={camera.status} cameraError={camera.error}
            frameSize={frameSize}
            frozenSrc={status === 'diambil' ? photo?.photo : null}
            highlight={status === 'diambil'}
            hasTorch={camera.hasTorch}
            torchOn={camera.torchOn}
            onToggleTorch={camera.setTorch}
            chip={status === 'kamera' && camera.status === 'ready' && (
              check?.ok ? <LiveChip label="Wajah terdeteksi (Siap Foto)" />
                : <LiveChip label="Arahkan wajah ke lingkaran" color="bg-amber-400" />
            )}
            messages={messages}
            overlay={<FaceGuide box={box} frameSize={frameSize} ok={status === 'diambil' || check?.ok}
              progress={status === 'diambil' ? 1 : 0} />}
          />
        </div>

        <div className="w-full md:w-[340px] bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100">
          <div className="w-12 h-12 bg-purple-50 text-glowmatch-primary rounded-2xl flex items-center justify-center mb-6">
            <FiCamera className="text-2xl" />
          </div>
          <h3 className="text-lg font-semibold text-glowmatch-secondary mb-5">Panduan Pengambilan Foto</h3>
          <ul className="space-y-4 mb-6 text-sm text-gray-500">
            <li className="flex items-start gap-3"><FiCheck className="text-[#88BCA0] text-lg mt-0.5 shrink-0" /> Pastikan cahaya merata: gunakan <strong>lampu HP</strong> atau <strong>bawa lighting sendiri</strong></li>
            <li className="flex items-start gap-3"><FiCheck className="text-[#88BCA0] text-lg mt-0.5 shrink-0" /> Lepaskan kacamata dan makeup tebal</li>
            <li className="flex items-start gap-3"><FiCheck className="text-[#88BCA0] text-lg mt-0.5 shrink-0" /> Tatap lurus ke arah kamera secara rileks</li>
          </ul>
          {status === 'kamera' && (
            <p className="text-xs text-gray-500 bg-purple-50/70 p-3 rounded-xl mb-6 border border-purple-100">
              📸 <strong>Manual Capture:</strong> Foto tidak diambil otomatis. Tekan tombol ungu di bawah saat kamu sudah siap.
            </p>
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
            ) : (
              <div className="flex gap-3">
                <button onClick={handleUlangi} className="flex-1 bg-white border border-gray-200 hover:bg-gray-50 text-gray-600 py-3.5 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 text-sm">
                  <FiRefreshCw className="text-base" /> Ulangi
                </button>
                <button onClick={() => navigate('/scan-undertone')} className="flex-[1.2] bg-glowmatch-primary hover:bg-purple-800 text-white py-3.5 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 text-sm">
                  Gunakan foto <FiArrowRight className="text-base" />
                </button>
              </div>
            )}
            <Link to="/" className="text-center text-sm text-gray-400 hover:text-gray-600 mt-3 font-medium">Kembali</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanFace;
