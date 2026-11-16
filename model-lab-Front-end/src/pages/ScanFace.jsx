import { useCallback, useRef, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FiCamera, FiRefreshCw, FiArrowRight } from 'react-icons/fi';
import CameraStage, { LiveChip } from '../components/CameraStage';
import { FaceGuide } from '../components/RadialBurst';
import { ScanHeader, ScanTips } from '../components/ScanParts';
import { useAnalysis } from '../context/AnalysisContext';
import { blobToDataURL, useCamera } from '../hooks/useCamera';
import { useFrameCheck } from '../hooks/useFrameCheck';
import { useSmoothedBox } from '../hooks/useSmoothedBox';

const TIPS = [
  'Cahaya merata dari lampu HP atau lampu sendiri.',
  'Lepas kacamata dan makeup tebal.',
  'Tatap lurus ke kamera dengan rileks.',
];

const ScanFace = () => {
  const [status, setStatus] = useState('kamera'); // kamera | diambil
  const [photo, setPhoto] = useState(null);
  const navigate = useNavigate();
  const { captureFace } = useAnalysis();
  const capturing = useRef(false);

  const camera = useCamera();
  const { captureFrame } = camera;
  const live = status === 'kamera' && camera.status === 'ready';
  const { check, error } = useFrameCheck({ captureFrame, kind: 'face', active: live });
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

  return (
    <div className="pt-8 pb-4 max-w-6xl mx-auto">
      <ScanHeader title="Analisis" accent="wajahmu." step="01" />

      <div className="grid lg:grid-cols-[1fr_360px] gap-8 items-start">
        <div className="gm-rise" style={{ '--d': '160ms' }}>
          <CameraStage
            videoRef={camera.videoRef} cameraStatus={camera.status} cameraError={camera.error}
            frameSize={frameSize}
            frozenSrc={status === 'diambil' ? photo?.photo : null}
            highlight={status === 'diambil'}
            hasTorch={camera.hasTorch}
            torchOn={camera.torchOn}
            onToggleTorch={camera.setTorch}
            chip={status === 'kamera' && camera.status === 'ready' && (
              check?.ok ? <LiveChip label="Wajah terdeteksi" />
                : <LiveChip label="Arahkan wajah ke lingkaran" color="bg-coral" />
            )}
            messages={messages}
            overlay={<FaceGuide box={box} frameSize={frameSize} ok={status === 'diambil' || check?.ok}
              progress={status === 'diambil' ? 1 : 0} />}
          />
        </div>

        <aside className="gm-card gm-rise p-7 sm:p-8" style={{ '--d': '260ms' }}>
          <ScanTips tips={TIPS} />

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
            ) : (
              <div className="gm-open flex gap-3">
                <button type="button" onClick={handleUlangi} className="gm-btn-ghost flex-1">
                  <FiRefreshCw /> Ulangi
                </button>
                <button type="button" onClick={() => navigate('/scan-undertone')} className="gm-btn flex-[1.3]">
                  Lanjut <FiArrowRight />
                </button>
              </div>
            )}
            <Link to="/beranda" className="gm-link self-center text-[14px] text-gray-500 mt-2">Kembali</Link>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default ScanFace;
