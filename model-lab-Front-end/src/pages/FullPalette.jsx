import { useParams, Link } from 'react-router-dom';
import { FiArrowLeft } from 'react-icons/fi';
import ColorSwatch from '../components/ColorSwatch';
import { resultData } from '../data/colorData';
import { seasonOptions, useAnalysis } from '../context/AnalysisContext';

const FullPalette = () => {
  // Mengambil parameter 'type' dari URL (utama, netral, atau hindari)
  const { type } = useParams(); 
  const { result, selectedId } = useAnalysis();

  // Palet musim yang sedang dipilih di halaman hasil (fallback: data contoh bila belum ada analisis)
  const options = seasonOptions(result);
  const selected = options.find((o) => o.id === selectedId) ?? options[0];
  const palette = (selected ? selected.palette.palettes : resultData.palettes)[type] || [];
  
  // Menyesuaikan judul dan deskripsi berdasarkan tipe
  let title;
  let description;
  
  if (type === 'utama') {
    title = "Warna Utama";
    description = "Deretan warna terbaik yang akan memancarkan aura alami dan membuat wajahmu tampak segar.";
  } else if (type === 'netral') {
    title = "Warna Netral";
    description = "Warna dasar yang elegan, aman, dan sangat mudah dipadukan dengan warna utamamu.";
  } else if (type === 'hindari') {
    title = "Warna yang Dihindari";
    description = "Warna yang sebaiknya dihindari untuk atasan atau hijab agar kulitmu tidak terlihat kusam atau pucat.";
  } else {
    title = "Palet Tidak Ditemukan";
    description = "Kategori warna yang kamu cari tidak tersedia.";
  }

  return (
    <div className="py-8 max-w-5xl mx-auto space-y-8">
      
      {/* Tombol Kembali */}
      <Link 
        to="/hasil" 
        className="inline-flex items-center gap-2 text-slate-500 hover:text-glowmatch-primary transition-colors font-medium text-sm"
      >
        <FiArrowLeft className="text-lg" /> Kembali ke Hasil Analisis
      </Link>
      
      {/* Header Halaman */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 shadow-[0_4px_20px_rgb(0,0,0,0.02)]">
        <h1 className="text-3xl font-semibold text-glowmatch-secondary mb-3 capitalize">{title}</h1>
        {selected && <p className="text-sm font-medium text-glowmatch-primary mb-2">{selected.name}</p>}
        <p className="text-slate-500 font-normal">{description}</p>
      </div>
      
      {/* Grid Seluruh Warna */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 shadow-[0_4px_20px_rgb(0,0,0,0.02)]">
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-4">
          {palette.length > 0 ? (
            palette.map((color, idx) => (
              <ColorSwatch key={idx} name={color.name} hex={color.hex} />
            ))
          ) : (
            <p className="text-slate-400 col-span-full text-center py-10">Data warna tidak ditemukan.</p>
          )}
        </div>
      </div>
      
    </div>
  );
};

export default FullPalette;