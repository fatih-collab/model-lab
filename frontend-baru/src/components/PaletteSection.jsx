import { Link } from 'react-router-dom';
import { FiArrowRight } from 'react-icons/fi';
import ColorSwatch from './ColorSwatch';

/**
 * Satu kelompok warna dengan bentuk kotak yang sama di semua halaman
 * (warna utama, netral, palet lengkap, warna yang dihindari).
 * link + limit: tampilkan sebagian dan tautan "Lihat semua".
 */
export default function PaletteSection({ title, colors = [], link, limit }) {
  const shown = limit ? colors.slice(0, limit) : colors;
  if (colors.length === 0) return null;

  return (
    <div>
      <div className="flex justify-between items-end gap-4 mb-5 border-b border-line pb-3">
        <h4 className="gm-title text-[26px]">{title}</h4>
        {link && colors.length > shown.length && (
          <Link to={link} className="gm-link text-[14px] shrink-0">
            Lihat semua ({colors.length}) <FiArrowRight />
          </Link>
        )}
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-7 gap-x-4 gap-y-6">
        {shown.map((c, i) => (
          <ColorSwatch key={`${c.hex}-${i}`} name={c.name} hex={c.hex} index={i} />
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
