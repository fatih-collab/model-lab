import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiArrowRight, FiTrash2, FiChevronDown } from 'react-icons/fi';
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
    <div className="pt-8 pb-4 max-w-5xl mx-auto">

      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-14">
        <h1 className="gm-display gm-rise text-[56px] sm:text-[84px]">
          Riwayat <em>analisis.</em>
        </h1>
        <Link to="/scan-wajah" className="gm-btn gm-rise self-start sm:self-auto" style={{ '--d': '120ms' }}>
          Analisis baru <FiArrowRight />
        </Link>
      </div>

      {loading && historyList.length === 0 && (
        <div className="space-y-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="gm-shimmer h-[104px] rounded-[28px]" style={{ animationDelay: `${i * 120}ms` }} />
          ))}
        </div>
      )}

      {!loading && historyList.length === 0 && (
        <div className="gm-rise text-center py-20 space-y-8 border-y border-line">
          <p className="gm-title text-[34px] text-gray-500">Belum ada riwayat.</p>
          <Link to="/scan-wajah" className="gm-btn">Mulai analisis pertama <FiArrowRight /></Link>
        </div>
      )}

      <ul className="space-y-4">
        {historyList.map((item, index) => {
          const rowId = item.id || item.request_id;
          const isOpen = openId === rowId;
          const isCurrent = result?.request_id === item.request_id || result?.request_id === item.id;
          return (
            <li
              key={rowId}
              className="gm-card gm-rise overflow-hidden transition-[border-color,box-shadow] duration-500 hover:border-[#d8c4d4] hover:shadow-[0_18px_40px_-26px_rgba(90,40,100,.35)]"
              style={{ '--d': `${Math.min(index, 8) * 70}ms` }}
            >
              <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center px-6 sm:px-8 py-6">

                <div className="md:col-span-4">
                  <p className="font-serif text-[26px] leading-tight">{item.date}</p>
                  <p className="text-[14px] text-gray-500 mt-1">
                    {item.time}
                    {item.user_name && <> · {item.user_name}</>}
                  </p>
                </div>

                <div className="md:col-span-4">
                  <p className="font-serif text-[26px] leading-tight">{item.season || item.season_name}</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {item.undertone && <span className="gm-tag py-1 capitalize">{item.undertone}</span>}
                    {item.detected && item.detected !== item.season && (
                      <span className="gm-tag py-1 text-gray-500">awal: {item.detected}</span>
                    )}
                  </div>
                </div>

                <div className="md:col-span-4 flex items-center justify-between md:justify-end gap-4">
                  <div className="flex -space-x-2">
                    {(item.palette || []).map((color, idx) => (
                      <span
                        key={idx}
                        className="w-8 h-8 rounded-full ring-2 ring-paper transition-transform duration-300 hover:-translate-y-1"
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>

                  <div className="flex items-center gap-1.5">
                    {isCurrent && (
                      <Link to="/hasil" className="gm-btn-ghost gm-btn-sm">
                        Buka <FiArrowRight />
                      </Link>
                    )}
                    {item.palettes && (
                      <button
                        type="button"
                        onClick={() => setOpenId(isOpen ? null : rowId)}
                        aria-expanded={isOpen}
                        className="gm-btn-ghost gm-btn-sm"
                      >
                        Warna <FiChevronDown className={`transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={(e) => handleDelete(item.id || item.request_id, e)}
                      className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-accent hover:bg-chip transition"
                      aria-label="Hapus riwayat ini"
                    >
                      <FiTrash2 />
                    </button>
                  </div>
                </div>
              </div>

              {isOpen && item.palettes && (
                <div className="gm-open px-6 sm:px-8 pb-10 pt-2 space-y-12 border-t border-line">
                  <div className="pt-8 space-y-12">
                    <PaletteSection title="Warna utama" colors={item.palettes.utama} />
                    <PaletteSection title="Warna netral" colors={item.palettes.netral} />
                    <PaletteSection title="Palet lengkap" colors={item.palettes.lengkap} />
                    <PaletteSection title="Sebaiknya dihindari" colors={item.palettes.hindari} />
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default Riwayat;
