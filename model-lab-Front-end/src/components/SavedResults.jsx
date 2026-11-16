import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BsBookmarkFill } from 'react-icons/bs';
import { FiTrash2, FiArrowRight } from 'react-icons/fi';
import { api } from '../lib/api';

/**
 * Daftar "Simpan Hasil" (bookmark) di halaman Profil.
 * Hanya menampilkan nama season dan warnanya, tanpa tanggal.
 */
const SavedResults = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    api
      .getSaved(controller.signal)
      .then((data) => setItems(Array.isArray(data) ? data : []))
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Gagal memuat hasil tersimpan.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  const handleDelete = async (id) => {
    setError('');
    try {
      await api.deleteSaved(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err.message || 'Gagal menghapus hasil tersimpan.');
    }
  };

  return (
    <section className="bg-white p-6 sm:p-8 rounded-3xl border border-gray-100 shadow-[0_4px_25px_rgb(0,0,0,0.03)] space-y-5">
      {error && <p className="text-sm text-red-600">{error}</p>}

      {loading ? (
        <p className="text-sm text-gray-500">Memuat hasil tersimpan...</p>
      ) : items.length === 0 ? (
        <div className="text-sm text-gray-500 space-y-2">
          <p>Belum ada hasil yang disimpan.</p>
          <Link
            to="/hasil"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-glowmatch-primary hover:underline"
          >
            Buka halaman hasil analisis <FiArrowRight />
          </Link>
        </div>
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <li
              key={item.id}
              className="relative border border-gray-100 rounded-2xl p-4 space-y-3 bg-gradient-to-br from-white to-purple-50/40"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-bold text-glowmatch-secondary flex items-center gap-2">
                  <BsBookmarkFill className="text-glowmatch-primary text-sm shrink-0" />
                  {item.season_name}
                </h3>
                <button
                  type="button"
                  onClick={() => handleDelete(item.id)}
                  aria-label={`Hapus ${item.season_name} dari Simpan Hasil`}
                  className="text-gray-400 hover:text-red-500 transition p-1"
                >
                  <FiTrash2 />
                </button>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {item.palette.map((hex, i) => (
                  <span
                    key={`${hex}-${i}`}
                    className="w-7 h-7 rounded-full border-2 border-white shadow-sm"
                    style={{ backgroundColor: hex }}
                    title={hex}
                  />
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default SavedResults;
