
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiUser,
  FiSave,
  FiCheck,
  FiArrowRight,
  FiRefreshCw,
} from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import { useAnalysis } from '../context/AnalysisContext';

const INITIAL_FORM = {
  name: '',
  gender: 'wanita',
  age: '',
  notes: '',
};

const ProfileSetup = () => {
  const navigate = useNavigate();

  const {
    profile,
    profileLoading,
    profileError,
    refreshProfile,
    updateProfile,
  } = useAnalysis();

  const [formData, setFormData] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Mengisi form dari data profil backend jika tersedia.
  useEffect(() => {
    if (!profile || profileLoading || profile.is_complete) {
      return;
    }

    setFormData({
      name:
        profile.name === 'Pengguna GlowMatch'
          ? ''
          : profile.name || '',
      gender: profile.gender || 'wanita',
      age:
        profile.name === 'Pengguna GlowMatch'
          ? ''
          : profile.age ?? '',
      notes:
        profile.notes === 'Profil utama'
          ? ''
          : profile.notes || '',
    });
  }, [profile, profileLoading]);

  // Pengguna yang sudah memiliki profil lengkap
  // tidak perlu mengisi onboarding kembali.
  useEffect(() => {
    if (!profileLoading && profile?.is_complete) {
      navigate('/scan-wajah', { replace: true });
    }
  }, [profile, profileLoading, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: name === 'age'
        ? value === ''
          ? ''
          : Number(value)
        : value,
    }));

    setError('');
  };

  const handleRetry = async () => {
    setError('');

    try {
      await refreshProfile();
    } catch (err) {
      setError(err.message || 'Gagal mengambil profil.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError('');

    const name = formData.name.trim();
    const age = Number(formData.age);

    if (!name) {
      setError('Nama wajib diisi.');
      return;
    }

    if (
      !Number.isInteger(age) ||
      age < 5 ||
      age > 100
    ) {
      setError('Usia harus berada antara 5 sampai 100 tahun.');
      return;
    }

    setLoading(true);

    try {
      const savedProfile = await updateProfile({
        name,
        gender: formData.gender,
        age,
        notes: formData.notes,
      });

      if (!savedProfile?.is_complete) {
        throw new Error(
          'Profil belum berhasil dikonfirmasi oleh server.'
        );
      }

      // Kamera baru akan dimuat setelah profil berhasil disimpan.
      navigate('/scan-wajah', { replace: true });
    } catch (err) {
      setError(
        err.message || 'Gagal menyimpan profil. Silakan coba lagi.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (profileLoading) {
    return (
      <div className="py-24 max-w-md mx-auto text-center">
        <p className="text-gray-500 text-sm">
          Memeriksa profil pengguna...
        </p>
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <div className="py-24 max-w-md mx-auto text-center space-y-5">
        <FiUser className="text-4xl text-glowmatch-primary mx-auto" />

        <h1 className="text-2xl font-semibold text-glowmatch-secondary">
          Profil belum dapat dimuat
        </h1>

        <p className="text-sm text-gray-500">
          Pastikan server backend GlowMatch berjalan dan koneksi
          database tersedia.
        </p>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <button
          type="button"
          onClick={handleRetry}
          className="inline-flex items-center gap-2 bg-glowmatch-primary text-white px-6 py-3 rounded-xl font-semibold"
        >
          <FiRefreshCw /> Coba Lagi
        </button>
      </div>
    );
  }

  return (
    <div className="py-10 max-w-4xl mx-auto space-y-8">

      {/* Header onboarding */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 bg-purple-50 text-glowmatch-primary px-4 py-2 rounded-full text-xs font-bold uppercase tracking-widest border border-purple-100">
          <HiSparkles />
          Personal Color Profile
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold text-glowmatch-secondary">
          Kenali Dirimu Sebelum Analisis
        </h1>

        <p className="text-sm text-gray-500 leading-relaxed">
          Lengkapi informasi profil terlebih dahulu agar hasil
          analisis dan riwayat personal color dapat tersimpan
          sesuai dengan identitasmu.
        </p>
      </div>

      {/* Form */}
      <div className="max-w-2xl mx-auto bg-white p-6 sm:p-8 rounded-3xl border border-gray-100 shadow-[0_4px_25px_rgb(0,0,0,0.03)] space-y-6">

        <div className="flex items-center gap-4 pb-4 border-b border-gray-100">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-500 text-white flex items-center justify-center text-2xl shadow-md shadow-purple-200">
            <FiUser />
          </div>

          <div>
            <h2 className="text-xl font-bold text-glowmatch-secondary">
              Informasi Pengguna
            </h2>

            <p className="text-xs text-gray-400">
              Data profil akan disimpan ke database GlowMatch.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Nama */}
          <div>
            <label
              htmlFor="setup-name"
              className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
            >
              Nama Lengkap / Panggilan
              <span className="text-red-400"> *</span>
            </label>

            <input
              id="setup-name"
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
            <label className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">
              Gender <span className="text-red-400">*</span>
            </label>

            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'wanita', label: 'Wanita' },
                { id: 'pria', label: 'Pria' },
                { id: 'lainnya', label: 'Lainnya' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setFormData((prev) => ({
                      ...prev,
                      gender: item.id,
                    }));
                    setError('');
                  }}
                  className={`py-3 px-3 rounded-xl border text-sm font-semibold transition text-center ${
                    formData.gender === item.id
                      ? 'border-glowmatch-primary bg-purple-50 text-glowmatch-primary shadow-sm'
                      : 'border-gray-200 hover:bg-gray-50 text-gray-600'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Usia */}
          <div>
            <label
              htmlFor="setup-age"
              className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
            >
              Umur (Tahun)
              <span className="text-red-400"> *</span>
            </label>

            <input
              id="setup-age"
              name="age"
              type="number"
              required
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
              htmlFor="setup-notes"
              className="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2"
            >
              Catatan Personal / Preferensi Gaya (Opsional)
            </label>

            <textarea
              id="setup-notes"
              name="notes"
              rows="3"
              value={formData.notes}
              onChange={handleChange}
              placeholder="Contoh: Menyukai gaya minimalis dan warna earthy tone..."
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-glowmatch-primary/20 focus:border-glowmatch-primary transition text-sm"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3">
              <p className="text-sm text-red-600">
                {error}
              </p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-glowmatch-primary hover:bg-purple-800 disabled:bg-gray-300 text-white py-4 px-6 rounded-xl font-semibold transition-all shadow-md flex items-center justify-center gap-2 text-sm"
          >
            {loading ? (
              <>
                <FiSave />
                Menyimpan Profil...
              </>
            ) : (
              <>
                <FiCheck />
                Simpan Profil dan Mulai Analisis
                <FiArrowRight />
              </>
            )}
          </button>
        </form>
      </div>

      <p className="text-center text-xs text-gray-400">
        Foto wajah dan gambar kamera tidak disimpan sebagai
        data profil di database.
      </p>
    </div>
  );
};

export default ProfileSetup;
