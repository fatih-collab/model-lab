import CameraStage, { LiveChip } from './CameraStage';
import RadialBurst from './RadialBurst';
import SeasonSwitcher from './SeasonSwitcher';
import { useCamera } from '../hooks/useCamera';
import { useFrameCheck } from '../hooks/useFrameCheck';
import { useSmoothedBox } from '../hooks/useSmoothedBox';

/**
 * Coba palet secara live: cincin radial burst mengikuti wajah real-time (box dari /api/frame/check,
 * dihaluskan per animation frame), dan musim bisa ditukar langsung untuk membandingkan di wajah sendiri.
 */
export default function LiveTryOn({ options, selected, onSelect }) {
  const camera = useCamera();
  const { check, error } = useFrameCheck({
    captureFrame: camera.captureFrame, kind: 'face', active: camera.status === 'ready', intervalMs: 200, maxSide: 400,
  });
  const box = useSmoothedBox(check?.box ?? null, 0.3);
  const frameSize = check?.frame_size ?? (camera.videoSize && [camera.videoSize.w, camera.videoSize.h]);
  const noFace = check && !check.box;

  return (
    <div className="space-y-3">
      <CameraStage
        videoRef={camera.videoRef} cameraStatus={camera.status} cameraError={camera.error}
        frameSize={frameSize}
        chip={camera.status === 'ready' && <LiveChip label={`Live · ${selected.name}`} />}
        messages={error ? [error] : noFace ? check.messages : []}
        overlay={<RadialBurst box={box} colors={selected.palette.palettes.utama} animationKey={selected.id} />}
      />
      <SeasonSwitcher compact options={options} selectedId={selected.id} onSelect={onSelect} />
    </div>
  );
}
