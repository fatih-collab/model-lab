import { useParams, Link } from 'react-router-dom';
import { FiArrowLeft } from 'react-icons/fi';
import ColorSwatch from '../components/ColorSwatch';
import { resultData } from '../data/colorData';
import { seasonOptions, useAnalysis } from '../context/AnalysisContext';

// Judul polos tanpa titik; sama dengan label di halaman hasil.
const TITLES = {
  utama: ['Warna', 'utama'],
  netral: ['Warna', 'netral'],
  lengkap: ['Semua', 'warna'],
  hindari: ['Warna yang sebaiknya', 'dihindari'],
};

const FullPalette = () => {
  // Parameter 'type' dari URL: utama, netral, lengkap, atau hindari
  const { type } = useParams();
  const { result, selectedId } = useAnalysis();

  // Palet season yang sedang dipilih di halaman hasil (fallback: data contoh bila belum ada analisis)
  const options = seasonOptions(result);
  const selected = options.find((o) => o.id === selectedId) ?? options[0];
  const palette = (selected ? selected.palette.palettes : resultData.palettes)[type] || [];
  const [title, accent] = TITLES[type] ?? ['Palet tidak', 'ditemukan'];

  return (
    <div className="pt-8 pb-4 max-w-6xl mx-auto">
      <Link to="/hasil" className="gm-link gm-rise text-small text-gray-600">
        <FiArrowLeft aria-hidden="true" /> Kembali ke hasil
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mt-8 mb-14">
        <div>
          {selected && <p className="gm-rise text-small font-medium text-gray-600">{selected.name}</p>}
          <h1 className="gm-display gm-rise text-display mt-2" style={{ '--d': '80ms' }}>
            {title} {accent}
          </h1>
        </div>
      </div>

      {palette.length > 0 ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-x-4 gap-y-7">
          {palette.map((color, idx) => (
            <ColorSwatch key={`${color.hex}-${idx}`} name={color.name} hex={color.hex} index={idx} />
          ))}
        </div>
      ) : (
        <p className="text-title text-gray-600 text-center py-16">Belum ada warna di sini</p>
      )}
    </div>
  );
};

export default FullPalette;
