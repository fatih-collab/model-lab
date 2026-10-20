import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiUser, FiSave, FiCheck, FiArrowRight, FiClock, FiHeart, FiSmile } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import { useAnalysis, loadHistory } from '../context/AnalysisContext';

const Profile = () => {
  const { profile, updateProfile, result } = useAnalysis();
  const [formData, setFormData] = useState({
    name: profile?.name || 'Pengguna GlowMatch',
    gender: profile?.gender || 'wanita',
    age: profile?.age || 22,
    notes: profile?.notes || '',
  });
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  const history = loadHistory();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'age' ? (value === '' ? '' : Number(value)) : value,
    }));
    setSaved(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updateProfile(formData);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-10 max-w-4xl mx-auto space-y-8">
      {/* Header Halaman */}
      <div>
        <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-2">Profil Pengguna</p>
        <h1 className="text-3xl font-semibold text-glowmatch-secondary mb-2">Identitas Personal</h1>
        <p className="text-gray-500 text-sm">
          Informasi ini digunakan untuk mempersonalisasi laporan dan sertifikat PDF analisis warna pribadimu.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Kolom Kiri: Form Profil */}
        <div className="md:col-span-7 bg-white p-8 rounded-3xl border border-gray-100 shadow-[0_4px_25px_rgb(0,0,0,0.03)] space-y-6">
          <div className="flex items-center gap-4 pb-4 border-b border-gray-100">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-500 text-white flex items-center justify-center text-2xl font-bold shadow-md shadow-purple-200">
              {formData.name ? formData.name.charAt(0).toUpperCase() : 'G'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-glowmatch-secondary">{formData.name || 'Nama Belum Diisi'}</h2>
              <p className="text-xs text-gray-400 capitalize">
                {formData.gender} · {formData.age ? `${formData.age} tahun` : 'Umur belum disetel'}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Nama */}
            <div>
              <label htmlFor="name" className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
                Nama Lengkap / Panggilan <span className="text-red-400">*</span>
              </label>
              <input
                id="name"
                name="name"
                type="text"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="Contoh: Alya Maharani"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-glowmatch-primary/20 focus:border-glowmatch-primary transition text-sm"
              />
            </div>

            {/* Gender */}
            <div>
              <label htmlFor="gender" className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
                Gender <span className="text-red-400">*</span>
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'wanita', label: 'Wanita' },
                  { id: 'pria', label: 'Pria' },
                  { id: 'lainnya', label: 'Lainnya' },
                ].map((g) => (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => {
                      setFormData((prev) => ({ ...prev, gender: g.id }));
                      setSaved(false);
                    }}
                    className={`py-3 px-3 rounded-xl border text-sm font-semibold transition text-center ${
                      formData.gender === g.id
                        ? 'border-glowmatch-primary bg-purple-50 text-glowmatch-primary shadow-sm'
                        : 'border-gray-200 hover:bg-gray-50 text-gray-600'
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-gray-400 mt-1.5">
                Membantu menyesuaikan saran outfit & busana harian (dress/blazer/hijab/jas/kemeja).
              </p>
            </div>

            {/* Umur */}
            <div>
              <label htmlFor="age" className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
                Umur (Tahun)
              </label>
              <input
                id="age"
                name="age"
                type="number"
                min="5"
                max="100"
                value={formData.age}
                onChange={handleChange}
                placeholder="Contoh: 23"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-glowmatch-primary/20 focus:border-glowmatch-primary transition text-sm"
              />
            </div>

            {/* Catatan / Preferensi Gaya */}
            <div>
              <label htmlFor="notes" className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
                Catatan Personal / Preferensi Gaya (Opsional)
              </label>
              <textarea
                id="notes"
                name="notes"
                rows="3"
                value={formData.notes}
                onChange={handleChange}
                placeholder="Contoh: Menyukai gaya minimalis, hijab kasual, dan warna earthy tone..."
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-glowmatch-primary/20 focus:border-glowmatch-primary transition text-sm"
              />
            </div>

            <div className="pt-2 flex items-center gap-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-glowmatch-primary hover:bg-purple-800 text-white py-3.5 px-6 rounded-xl font-semibold transition-all shadow-md flex items-center justify-center gap-2 text-sm disabled:opacity-60"
              >
                {saved ? (
                  <>
                    <FiCheck className="text-lg" /> Tersimpan ke Database
                  </>
                ) : (
                  <>
                    <FiSave className="text-lg" /> Simpan Perubahan Profil
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Kolom Kanan: Status & Riwayat Terkait */}
        <div className="md:col-span-5 space-y-6">
          {/* Card Hasil Terkini */}
          <div className="bg-gradient-to-br from-purple-50 via-rose-50 to-orange-50 p-6 rounded-3xl border border-purple-100 shadow-sm space-y-4">
            <div className="flex items-center gap-3 text-glowmatch-primary font-bold text-xs uppercase tracking-wider">
              <HiSparkles className="text-lg" />
              <span>Analisis Warna Anda</span>
            </div>

            {result ? (
              <div className="space-y-3">
                <h3 className="text-2xl font-bold text-glowmatch-secondary">{result.result.season.name}</h3>
                <p className="text-xs text-gray-600">
                  Undertone: <strong className="capitalize">{result.result.gate.undertone}</strong>
                </p>
                <div className="flex -space-x-2 pt-1">
                  {result.result.season.palette.palettes.utama.slice(0, 6).map((c) => (
                    <div
                      key={c.hex}
                      className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                      style={{ backgroundColor: c.hex }}
                      title={c.name}
                    />
                  ))}
                </div>
                <div className="pt-2">
                  <Link
                    to="/hasil"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-glowmatch-primary hover:underline"
                  >
                    Buka Halaman Hasil Analisis <FiArrowRight />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  Belum ada analisis sesi ini. Pindai wajahmu untuk menemukan 12 musim warnamu.
                </p>
                <Link
                  to="/scan-wajah"
                  className="inline-flex items-center gap-2 bg-glowmatch-primary text-white text-xs font-semibold px-4 py-2.5 rounded-xl hover:bg-purple-800 transition"
                >
                  Mulai Analisis Sekarang <FiArrowRight />
                </Link>
              </div>
            )}
          </div>

          {/* Card Manfaat Profil */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-3 text-sm">
            <h4 className="font-bold text-glowmatch-secondary flex items-center gap-2">
              <FiSmile className="text-glowmatch-primary" /> Mengapa Mengisi Profil?
            </h4>
            <ul className="space-y-2 text-xs text-gray-500 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-glowmatch-primary font-bold">•</span>
                <strong>Laporan PDF Personal:</strong> Nama dan identitasmu akan tercantum rapi di kartu palet dan file PDF unduhan.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-glowmatch-primary font-bold">•</span>
                <strong>Rekomendasi Gaya Busana:</strong> Saran pakaian dan aksesori disesuaikan untuk wanita maupun pria.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-glowmatch-primary font-bold">•</span>
                <strong>Sinkronisasi Otomatis:</strong> Data tersimpan secara aman di database SQLite GlowMatch lokalmu.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
