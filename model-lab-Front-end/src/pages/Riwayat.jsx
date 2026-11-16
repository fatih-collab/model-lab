import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiArrowRight, FiTrash2, FiUser, FiDatabase, FiChevronDown } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import PaletteSection, { palettesFromHistory } from '../components/PaletteSection';
import { loadHistory, deleteFromHistory, useAnalysis } from '../context/AnalysisContext';
import { api } from '../lib/api';

const Riwayat = () => {
  const { result } = useAnalysis();
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openId, setOpenId] = useState(null);

  const fmtDate = new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'long', year: 'numeric' });
  const fmtTime = new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit' });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      // Coba ambil dari database backend
      const data = await api.getHistory(50);
      if (Array.isArray(data) && data.length > 0) {
        setHistoryList(
          data.map((item) => {
            const d = new Date(item.created_at || Date.now());
            return {
              ...item,
              season: item.season_name,
              detected: item.detected_season,
              palettes: palettesFromHistory({
                ...item,
                recommendations:
                  item.recommendations || item.selected_season?.palette?.rekomendasi || null,
              }),
              date: fmtDate.format(d),
              time: fmtTime.format(d),
            };
          })
        );
        setLoading(false);
        return;
      }
    } catch {
      // Backend offline, fallback ke localStorage
    }

    // Fallback localStorage
    const local = loadHistory().map((h) => {
      const d = new Date(h.savedAt);
      return { ...h, date: fmtDate.format(d), time: fmtTime.format(d) };
    });
    setHistoryList(local);
    setLoading(false);
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Hapus riwayat analisis ini dari database?')) return;
    await deleteFromHistory(id);
    setHistoryList((prev) => prev.filter((item) => item.id !== id && item.request_id !== id));
  };

  return (
    <div className="py-8 max-w-5xl mx-auto space-y-8">
      
      {/* Header Halaman */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-2">
        <div>
          <div className="flex items-center gap-2 text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-1">
            <FiDatabase /> Database Riwayat Analisis
          </div>
          <h1 className="text-3xl font-bold text-glowmatch-secondary mb-1">Riwayat Analisis Tersimpan</h1>
          <p className="text-slate-500 font-normal text-sm">
            Semua hasil analisis, season, dan rekomendasi warnamu yang sudah tersimpan.
          </p>
        </div>
        <Link 
          to="/scan-wajah" 
          className="inline-flex items-center gap-2 bg-glowmatch-primary text-white px-6 py-3.5 rounded-xl font-semibold hover:bg-purple-800 transition-all shadow-md self-start md:self-auto text-sm"
        >
          <HiSparkles className="text-lg" /> Analisis Baru
        </Link>
      </div>

      {/* Kontainer Daftar Riwayat */}
      <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-[0_4px_25px_rgb(0,0,0,0.03)]">
        
        {/* Header Tabel (Desktop saja) */}
        <div className="hidden md:grid grid-cols-12 gap-4 px-8 py-4 bg-slate-50/70 border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
          <div className="col-span-4">Tanggal & Profil</div>
          <div className="col-span-4">Season</div>
          <div className="col-span-4 text-right">Palet & Aksi</div>
        </div>

        {/* Isi Riwayat */}
        <div className="divide-y divide-slate-100">
          {loading && historyList.length === 0 && (
            <div className="px-8 py-16 text-center text-sm text-slate-400">Memuat riwayat...</div>
          )}

          {!loading && historyList.length === 0 && (
            <div className="px-8 py-16 text-center text-sm text-slate-400 space-y-3">
              <p>Belum ada riwayat tersimpan di database.</p>
              <Link to="/scan-wajah" className="inline-block text-glowmatch-primary font-bold hover:underline">
                Mulai analisis pertamamu sekarang →
              </Link>
            </div>
          )}

          {historyList.map((item) => {
            const rowId = item.id || item.request_id;
            const isOpen = openId === rowId;
            return (
            <div key={rowId}>
            <div 
              className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center px-6 md:px-8 py-6 hover:bg-slate-50/60 transition-colors group"
            >
              
              {/* Kolom 1: Tanggal & Profil */}
              <div className="col-span-4 flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-purple-50 text-glowmatch-primary flex items-center justify-center shrink-0 shadow-xs">
                  <FiClock className="text-xl" />
                </div>
                <div>
                  <h3 className="font-bold text-glowmatch-secondary text-sm md:text-base">{item.date}</h3>
                  <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                    <span>{item.time}</span>
                    {(item.user_name || item.user_gender) && (
                      <>
                        <span>•</span>
                        <span className="text-glowmatch-primary font-medium flex items-center gap-1">
                          <FiUser className="text-[10px]" /> {item.user_name || 'Pengguna'} ({item.user_gender || 'wanita'})
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Kolom 2: Season */}
              <div className="col-span-4 font-bold text-glowmatch-secondary text-sm md:text-base">
                <span className="md:hidden text-xs text-slate-400 uppercase font-normal mr-2">Season:</span>
                <span className="text-glowmatch-secondary">{item.season || item.season_name}</span>
                <div className="text-xs font-normal text-slate-400 mt-0.5">
                  Undertone: <strong className="capitalize text-slate-600">{item.undertone}</strong>
                  {item.detected && item.detected !== item.season && (
                    <span className="ml-2">(hasil awal: {item.detected})</span>
                  )}
                </div>
              </div>

              {/* Kolom 3: Palet Singkat & Tombol Hapus */}
              <div className="col-span-4 flex items-center justify-between md:justify-end gap-4 mt-2 md:mt-0">
                {/* Bulatan Warna */}
                <div className="flex -space-x-1.5">
                  {(item.palette || []).map((color, idx) => (
                    <div 
                      key={idx} 
                      className="w-7 h-7 rounded-full border-2 border-white shadow-xs"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
                
                <div className="flex items-center gap-2">
                  {/* Tautan Lihat Hasil */}
                  {result?.request_id === item.request_id || result?.request_id === item.id ? (
                    <Link 
                      to="/hasil" 
                      className="flex items-center gap-1 text-xs font-bold text-glowmatch-primary hover:underline px-2.5 py-1.5 bg-purple-50 rounded-lg"
                    >
                      Buka <FiArrowRight />
                    </Link>
                  ) : null}

                  {/* Tombol Rekomendasi Warna */}
                  {item.palettes && (
                    <button
                      type="button"
                      onClick={() => setOpenId(isOpen ? null : rowId)}
                      aria-expanded={isOpen}
                      className="flex items-center gap-1 text-xs font-bold text-glowmatch-primary px-2.5 py-1.5 bg-purple-50 rounded-lg hover:bg-purple-100 transition"
                    >
                      Warna <FiChevronDown className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                    </button>
                  )}

                  {/* Tombol Hapus Riwayat */}
                  <button
                    type="button"
                    onClick={(e) => handleDelete(item.id || item.request_id, e)}
                    className="text-gray-400 hover:text-red-500 p-2 rounded-lg hover:bg-red-50 transition"
                    title="Hapus dari database"
                  >
                    <FiTrash2 className="text-sm" />
                  </button>
                </div>
              </div>
              
            </div>

            {isOpen && item.palettes && (
              <div className="px-6 md:px-8 pb-8">
                <div className="rounded-2xl bg-white border border-slate-100 p-6 space-y-8">
                  <PaletteSection title="Warna Utama" colors={item.palettes.utama} />
                  <PaletteSection title="Warna Netral" colors={item.palettes.netral} />
                  <PaletteSection title={`Palet Lengkap ${item.season}`} colors={item.palettes.lengkap} />
                  <PaletteSection title="Warna yang Sebaiknya Dihindari" colors={item.palettes.hindari} />
                </div>
              </div>
            )}
            </div>
            );
          })}
        </div>

      </div>

    </div>
  );
};

export default Riwayat;