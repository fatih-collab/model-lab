import { FiAlertTriangle, FiCameraOff, FiZap } from 'react-icons/fi';
import { FrameOverlay } from './RadialBurst';

/**
 * Video kamera live (atau foto yang dibekukan) + overlay SVG berkoordinat frame.
 * Mendukung lampu kilat/torch HP (jika didukung perangkat) atau pencahayaan eksternal.
 */
export default function CameraStage({
  videoRef,
  cameraStatus,
  cameraError,
  mirrored = true,
  frameSize,
  overlay,
  frozenSrc,
  chip,
  messages = [],
  highlight,
  className = '',
  hasTorch = false,
  torchOn = false,
  onToggleTorch,
  children,
}) {
  const flip = mirrored ? { transform: 'scaleX(-1)' } : undefined;

  return (
    <div
      className={`relative w-full aspect-[4/3] rounded-[30px] overflow-hidden bg-ink transition-[box-shadow] duration-500 ${
        highlight ? 'shadow-[0_0_0_4px_#fbf7ec,0_0_0_6px_#7e8a59]' : 'shadow-[0_30px_60px_-35px_rgba(42,29,59,.7)]'
      } ${className}`}
    >
      <div className="absolute inset-0" style={flip}>
        <video
          ref={videoRef}
          muted
          playsInline
          autoPlay
          className={`absolute inset-0 w-full h-full object-cover ${frozenSrc ? 'invisible' : ''}`}
        />
        {frozenSrc && (
          <img src={frozenSrc} alt="Foto yang diambil" className="gm-page absolute inset-0 w-full h-full object-cover" />
        )}
        <FrameOverlay frameSize={frameSize}>{overlay}</FrameOverlay>
      </div>

      {cameraStatus === 'starting' && !frozenSrc && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="gm-spinner" aria-label="Membuka kamera" />
        </div>
      )}
      {cameraStatus === 'error' && !frozenSrc && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-center text-paper px-10">
          <FiCameraOff className="text-4xl opacity-70" />
          <p className="text-body max-w-sm opacity-90">{cameraError}</p>
        </div>
      )}

      {chip && (
        <div className="gm-open absolute top-4 left-4 bg-ink/55 backdrop-blur-md text-paper text-small px-3.5 py-1.5 rounded-full flex items-center gap-2 z-10">
          {chip}
        </div>
      )}

      {!frozenSrc && cameraStatus === 'ready' && hasTorch && (
        <div className="absolute top-4 right-4 z-20">
          <button
            onClick={() => onToggleTorch && onToggleTorch(!torchOn)}
            type="button"
            aria-pressed={torchOn}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-small backdrop-blur-md transition-all ${
              torchOn ? 'bg-paper text-ink' : 'bg-ink/55 text-paper hover:bg-ink/75'
            }`}
          >
            <FiZap className={torchOn ? 'fill-current' : ''} />
            Flash
          </button>
        </div>
      )}

      {messages.length > 0 && (
        <div className="absolute bottom-4 left-4 right-4 z-10 flex flex-col items-center gap-1.5" aria-live="polite">
          {messages.slice(0, 2).map((m) => (
            <p key={m} className="gm-open bg-ink/65 backdrop-blur-md text-paper text-small px-4 py-2 rounded-full flex items-center gap-2">
              <FiAlertTriangle className="text-coral shrink-0" /> {m}
            </p>
          ))}
        </div>
      )}
      {children}
    </div>
  );
}

export function LiveChip({ label = 'Kamera aktif', color = 'bg-olive' }) {
  return (
    <>
      <span className={`w-2 h-2 ${color} rounded-full gm-breathe`} /> {label}
    </>
  );
}

export function LoadingOverlay({ title }) {
  return (
    <div className="absolute inset-0 bg-ink/75 backdrop-blur-sm flex flex-col items-center justify-center text-paper z-20 text-center px-6 gm-page">
      <span className="gm-spinner mb-6" />
      <h3 key={title} className="gm-rise text-title-lg">{title}</h3>
    </div>
  );
}
