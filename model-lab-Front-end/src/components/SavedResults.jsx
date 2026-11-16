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
    <section className="space-y-5">
      {error && <p className="gm-open text-small text-accent">{error}</p>}

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="gm-shimmer h-40 rounded-[28px]" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="gm-rise text-center py-20 space-y-8 border-y border-line">
          <p className="text-title-lg text-gray-600">Belum ada hasil tersimpan</p>
          <Link to="/hasil" className="gm-btn">Buka hasil analisis <FiArrowRight /></Link>
        </div>
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item, i) => (
            <li
              key={item.id}
              className="gm-card gm-rise p-6 group"
              style={{ '--d': `${Math.min(i, 8) * 70}ms` }}
            >
              <div className="flex h-16 rounded-[18px] overflow-hidden">
                {item.palette.map((hex, j) => (
                  <span
                    key={`${hex}-${j}`}
                    className="flex-1 transition-[flex-grow] duration-500 hover:flex-[2.4]"
                    style={{ backgroundColor: hex }}
                    title={hex}
                  />
                ))}
              </div>
              <div className="flex items-center justify-between gap-3 mt-5">
                <h3 className="text-title flex items-center gap-2.5">
                  <BsBookmarkFill className="text-accent text-small shrink-0" aria-hidden="true" />
                  {item.season_name}
                </h3>
                <button
                  type="button"
                  onClick={() => handleDelete(item.id)}
                  aria-label={`Hapus ${item.season_name} dari Simpan Hasil`}
                  className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-accent hover:bg-chip transition"
                >
                  <FiTrash2 />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default SavedResults;
