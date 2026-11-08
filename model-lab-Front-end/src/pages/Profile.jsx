
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FiUser,
  FiSave,
  FiCheck,
  FiArrowRight,
  FiSmile,
} from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import { useAnalysis } from '../context/AnalysisContext';

const DEFAULT_FORM = {
  name: 'Pengguna GlowMatch',
  gender: 'wanita',
  age: 22,
  notes: '',
};

const Profile = () => {
  const {
    profile,
    profileLoading,
    profileError,
    refreshProfile,
    updateProfile,
    result,
  } = useAnalysis();

  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saveError, setSaveError] = useState('');

  // Sinkronkan form ketika profil dari backend berhasil dimuat.
  useEffect(() => {
    if (!profile) return;

    setFormData({
      name: profile.name || DEFAULT_FORM.name,
      gender: profile.gender || DEFAULT_FORM.gender,
      age: profile.age ?? DEFAULT_FORM.age,
      notes: profile.notes || '',
    });
  }, [profile]);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]:
        name === 'age'
          ? value === ''
            ? ''
            : Number(value)
          : value,
    }));

    setSaved(false);
    setSaveError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setSaved(false);
    setSaveError('');

    try {
      const savedProfile = await updateProfile(formData);

      setFormData({
        name: savedProfile.name,
        gender: savedProfile.gender,
        age: savedProfile.age ?? 22,
        notes: savedProfile.notes || '',
      });

      setSaved(true);
    } catch (error) {
      setSaveError(
        error.message || 'Gagal menyimpan profil. Silakan coba lagi.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    try {
      await refreshProfile();
    } catch {
      // Error ditampilkan melalui profileError pada context.
    }
  };

  return (
    <div className="py-10 max-w-4xl mx-auto space-y-8">
      {/* Header Halaman */}
      <div>
        <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-2">
          Profil Pengguna
        </p>

        <h1 className="text-3xl font-semibold text-glowmatch-secondary mb-2">
          Identitas Personal
        </h1>

        <p className="text-gray-500 text-sm">
          Informasi ini digunakan untuk mempersonalisasi laporan dan
          sertifikat PDF analisis warna pribadimu.
        </p>
      </div>

      {/* Status pemuatan profil */}
      {profileLoading && (
        <p className="text-sm text-gray-500">
          Memuat profil pengguna...
        </p>
      )}

      {/* Error pemuatan profil dari backend */}
      {!profileLoading && profileError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-2">
          <p className="text-sm text-red-600">
            Gagal mengambil profil dari server: {profileError.message}
          </p>

          <button
            type="button"
            onClick={handleRetry}
            className="text-sm font-semibold text-red-700 hover:underline"
          >
            Coba muat ulang profil
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">

        {/* Kolom Kiri: Form Profil */}
        <div className="md:col-span-7 bg-white p-8 rounded-3xl border border-gray-100 shadow-[0_4px_25px_rgb(0,0,0,0.03)] space-y-6">

          <div className="flex items-center gap-4 pb-4 border-b border-gray-100">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-500 text-white flex items-center justify-center text-2xl font-bold shadow-md shadow-purple-200">
              {formData.name
                ? formData.name.charAt(0).toUpperCase()
                : 'G'}
            </div>

            <div>
              <h2 className="text-xl font-bold text-glowmatch-secondary">
                {formData.name || 'Nama Belum Diisi'}
              </h2>

              <p className="text-xs text-gray-400 capitalize">
                {formData.gender} ·{' '}
                {formData.age
                  ? `${formData.age} tahun`
                  : 'Umur belum disetel'}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Nama */}
            <div>
              <label
                htmlFor="name"
                className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
              >
                Nama Lengkap / Panggilan{' '}
                <span className="text-red-400">*</span>
              </label>

              <input
                id="name"
                name="name"
                type="text"
                required
                maxLength={120}
                value={formData.name}
                onChange={handleChange}
                placeholder="Contoh: Alya Maharani"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-glowmatch-primary/20 focus:border-glowmatch-primary transition text-sm"
              />
            </div>

            {/* Gender */}
            <div>
              <label
                htmlFor="gender"
                className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
              >
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
                      setFormData((prev) => ({
                        ...prev,
                        gender: g.id,
                      }));

                      setSaved(false);
                      setSaveError('');
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
                Membantu menyesuaikan saran outfit & busana harian
                (dress/blazer/hijab/jas/kemeja).
              </p>
            </div>

            {/* Umur */}
            <div>
              <label
                htmlFor="age"
                className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
              >
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

            {/* Catatan */}
            <div>
              <label
                htmlFor="notes"
                className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
              >
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

            {/* Error penyimpanan */}
            {saveError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3">
                <p className="text-sm text-red-600">
                  {saveError}
                </p>
              </div>
            )}

            {/* Tombol Simpan */}
            <div className="pt-2 flex items-center gap-4">
              <button
                type="submit"
                disabled={loading || profileLoading}
                className="flex-1 bg-glowmatch-primary hover:bg-purple-800 text-white py-3.5 px-6 rounded-xl font-semibold transition-all shadow-md flex items-center justify-center gap-2 text-sm disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <FiSave className="text-lg" />
                    Menyimpan...
                  </>
                ) : saved ? (
                  <>
                    <FiCheck className="text-lg" />
                    Tersimpan ke Database
                  </>
                ) : (
                  <>
                    <FiSave className="text-lg" />
                    Simpan Perubahan Profil
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
                <h3 className="text-2xl font-bold text-glowmatch-secondary">
                  {result.result.season.name}
                </h3>

                <p className="text-xs text-gray-600">
                  Undertone:{' '}
                  <strong className="capitalize">
                    {result.result.gate.undertone}
                  </strong>
                </p>

                <div className="flex -space-x-2 pt-1">
                  {result.result.season.palette.palettes.utama
                    .slice(0, 6)
                    .map((color) => (
                      <div
                        key={color.hex}
                        className="w-8 h-8 rounded-full border-2 border-white shadow-sm"
                        style={{ backgroundColor: color.hex }}
                        title={color.name}
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
                  Belum ada analisis sesi ini. Pindai wajahmu untuk
                  menemukan 12 musim warnamu.
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
              <FiSmile className="text-glowmatch-primary" />
              Mengapa Mengisi Profil?
            </h4>

            <ul className="space-y-2 text-xs text-gray-500 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-glowmatch-primary font-bold">•</span>
                <span>
                  <strong>Laporan PDF Personal:</strong> Nama dan
                  identitasmu akan tercantum rapi di kartu palet dan
                  file PDF unduhan.
                </span>
              </li>

              <li className="flex items-start gap-2">
                <span className="text-glowmatch-primary font-bold">•</span>
                <span>
                  <strong>Rekomendasi Gaya Busana:</strong> Saran
                  pakaian dan aksesori disesuaikan untuk wanita
                  maupun pria.
                </span>
              </li>

              <li className="flex items-start gap-2">
                <span className="text-glowmatch-primary font-bold">•</span>
                <span>
                  <strong>Sinkronisasi Otomatis:</strong> Data profil
                  tersimpan di database Neon PostgreSQL.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
