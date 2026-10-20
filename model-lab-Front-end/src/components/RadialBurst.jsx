// Cincin palet "radial burst" di sekeliling wajah.
// Dirender di dalam <FrameOverlay>, jadi semua koordinat memakai piksel frame kamera (sama dengan box dari server).

/** SVG yang menumpuk tepat di atas <video>/<img> object-cover: viewBox = ukuran frame, "slice" = object-cover. */
export function FrameOverlay({ frameSize, children, className = '' }) {
  if (!frameSize) return null;
  const [w, h] = frameSize;
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="xMidYMid slice"
      className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
    >
      {children}
    </svg>
  );
}

function sector(cx, cy, r0, r1, a0, a1) {
  const p = (r, a) => `${cx + r * Math.cos(a)} ${cy + r * Math.sin(a)}`;
  const large = a1 - a0 > Math.PI ? 1 : 0;
  return `M ${p(r1, a0)} A ${r1} ${r1} 0 ${large} 1 ${p(r1, a1)} L ${p(r0, a1)} A ${r0} ${r0} 0 ${large} 0 ${p(r0, a0)} Z`;
}

/** Geometri cincin dari box wajah (x, y, w, h): mengelilingi wajah + rambut. */
function ringGeometry([x, y, w, h]) {
  const cx = x + w / 2;
  const cy = y + h * 0.42;
  const r0 = Math.max(w, h) * 0.82;
  return { cx, cy, r0, r1: r0 * 1.42 };
}

export default function RadialBurst({ box, colors, animationKey, gapDeg = 2.2 }) {
  if (!box || !colors?.length) return null;
  const { cx, cy, r0, r1 } = ringGeometry(box);
  const n = colors.length;
  const step = (2 * Math.PI) / n;
  const gap = (gapDeg * Math.PI) / 180;
  const start = -Math.PI / 2 - step / 2; // warna pertama tepat di atas kepala
  const origin = { transformOrigin: `${cx}px ${cy}px`, transformBox: 'view-box' };

  return (
    <g key={animationKey}>
      <circle cx={cx} cy={cy} r={r1 + r0 * 0.06} fill="none" stroke="white" strokeOpacity="0.35" strokeWidth={r0 * 0.012} />
      {colors.map((c, i) => {
        const a0 = start + i * step + gap / 2;
        const a1 = start + (i + 1) * step - gap / 2;
        const mid = (a0 + a1) / 2;
        const rDot = r1 + r0 * 0.14;
        return (
          <g key={`${c.hex}-${i}`} className="burst-wedge" style={{ ...origin, animationDelay: `${i * 45}ms` }}>
            <path d={sector(cx, cy, r0, r1, a0, a1)} fill={c.hex} stroke="white" strokeOpacity="0.9" strokeWidth={r0 * 0.01}>
              <title>{`${c.name} ${c.hex}`}</title>
            </path>
            <circle cx={cx + rDot * Math.cos(mid)} cy={cy + rDot * Math.sin(mid)} r={r0 * 0.045} fill={c.hex} opacity="0.85" />
          </g>
        );
      })}
    </g>
  );
}

/** Panduan saat scan: oval bergaris (belum ada wajah) atau cincin + progres auto-capture di sekitar wajah. */
export function FaceGuide({ box, frameSize, ok, progress = 0 }) {
  if (!frameSize) return null;
  if (!box) {
    const [w, h] = frameSize;
    return (
      <ellipse cx={w / 2} cy={h / 2} rx={h * 0.3} ry={h * 0.4} fill="none" stroke="white" strokeOpacity="0.8"
        strokeWidth={h * 0.006} strokeDasharray={`${h * 0.02} ${h * 0.015}`} />
    );
  }
  const { cx, cy, r0 } = ringGeometry(box);
  const r = r0 * 0.95;
  const circ = 2 * Math.PI * r;
  const color = ok ? '#88BCA0' : '#F6B26B';
  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeOpacity="0.45" strokeWidth={r * 0.03} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={r * 0.045} strokeLinecap="round"
        strokeDasharray={`${circ * Math.min(1, progress)} ${circ}`} transform={`rotate(-90 ${cx} ${cy})`} />
    </g>
  );
}
