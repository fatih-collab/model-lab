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
    <div className="space-y-3">
      {/* Container Kamera Utama */}
      <div 
        className={`relative w-full aspect-[4/3] rounded-3xl overflow-hidden bg-gray-900 transition-all duration-300 ${
          highlight ? 'ring-4 ring-[#88BCA0]' : ''
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
            <img src={frozenSrc} alt="Foto yang diambil" className="absolute inset-0 w-full h-full object-cover" />
          )}
          <FrameOverlay frameSize={frameSize}>{overlay}</FrameOverlay>
        </div>

        {cameraStatus === 'starting' && !frozenSrc && (
          <div className="absolute inset-0 flex items-center justify-center text-white/80 text-sm">
            Membuka kamera...
          </div>
        )}
        {cameraStatus === 'error' && !frozenSrc && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center text-white px-10">
            <FiCameraOff className="text-4xl text-white/70" />
            <p className="text-sm text-white/90 max-w-sm">{cameraError}</p>
          </div>
        )}

        {/* Chip Status Kamera di Kiri Atas */}
        {chip && (
          <div className="absolute top-4 left-4 bg-black/50 backdrop-blur-md text-white text-xs px-3.5 py-1.5 rounded-full flex items-center gap-2 z-10 shadow-sm">
            {chip}
          </div>
        )}

        {/* Tombol Flash HP di Kanan Atas (jika didukung kamera perangkat) */}
        {!frozenSrc && cameraStatus === 'ready' && hasTorch && (
          <div className="absolute top-4 right-4 z-20">
            <button
              onClick={() => onToggleTorch && onToggleTorch(!torchOn)}
              type="button"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold backdrop-blur-md transition-all shadow-md ${
                torchOn ? 'bg-amber-400 text-gray-900 shadow-amber-300/40' : 'bg-black/50 text-white hover:bg-black/70'
              }`}
              title="Nyalakan/matikan lampu flash HP"
            >
              <FiZap className={`text-sm ${torchOn ? 'fill-current' : ''}`} />
              <span>{torchOn ? 'Flash HP ON' : 'Flash HP'}</span>
            </button>
          </div>
        )}

        {messages.length > 0 && (
          <div className="absolute bottom-4 left-4 right-4 z-10 flex flex-col items-center gap-1.5" aria-live="polite">
            {messages.slice(0, 2).map((m) => (
              <p key={m} className="bg-black/60 backdrop-blur-md text-white text-xs sm:text-sm px-4 py-2 rounded-full flex items-center gap-2">
                <FiAlertTriangle className="text-amber-300 shrink-0" /> {m}
              </p>
            ))}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

export function LiveChip({ label = 'Kamera aktif', color = 'bg-green-500' }) {
  return (
    <>
      <span className={`w-2.5 h-2.5 ${color} rounded-full animate-pulse`} /> {label}
    </>
  );
}

export function LoadingOverlay({ title, subtitle }) {
  return (
    <div className="absolute inset-0 bg-gray-900/70 backdrop-blur-sm flex flex-col items-center justify-center text-white z-20 text-center px-6">
      <div className="w-12 h-12 border-4 border-gray-400 border-t-white rounded-full animate-spin mb-4" />
      <h3 className="text-lg font-bold">{title}</h3>
      {subtitle && <p className="text-sm text-white/70 mt-1">{subtitle}</p>}
    </div>
  );
}
