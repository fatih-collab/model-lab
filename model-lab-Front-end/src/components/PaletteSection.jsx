import { Link } from 'react-router-dom';
import { FiArrowRight } from 'react-icons/fi';
import ColorSwatch from './ColorSwatch';

/**
 * Satu kelompok warna dengan bentuk kotak yang sama di semua halaman
 * (warna utama, netral, palet lengkap, warna yang dihindari).
 * link + limit: tampilkan sebagian dan tautan "Lihat semua".
 */
export default function PaletteSection({ title, subtitle, colors = [], link, limit }) {
  const shown = limit ? colors.slice(0, limit) : colors;
  if (colors.length === 0) return null;

  return (
    <div>
      <div className="flex justify-between items-end gap-4 mb-4 border-b border-gray-100 pb-3">
        <div>
          <h4 className="font-medium text-slate-700">{title}</h4>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        {link && colors.length > shown.length && (
          <Link to={link} className="text-sm font-medium text-glowmatch-primary flex items-center gap-1 hover:underline shrink-0">
            Lihat semua ({colors.length}) <FiArrowRight />
          </Link>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-4">
        {shown.map((c, i) => (
          <ColorSwatch key={`${c.hex}-${i}`} name={c.name} hex={c.hex} source={c.source} />
        ))}
      </div>
    </div>
  );
}

/**
 * Palet dari riwayat. Riwayat baru menyimpan snapshot season lengkap;
 * riwayat lama dibangun ulang dari data rekomendasi Excel.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function palettesFromHistory(item) {
  const groups = item.selected_season?.palette?.palettes;
  if (groups?.lengkap?.length) return groups;
  const rec = item.recommendations;
  if (!rec) return groups || null;
  return {
    utama: rec.flatter,
    netral: groups?.netral || [],
    lengkap: [...rec.chromatic, ...rec.neutral].map((hex) => ({ name: '', hex })),
    hindari: rec.avoid,
  };
}
