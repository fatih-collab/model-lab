
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSave, FiArrowRight, FiRefreshCw } from 'react-icons/fi';
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
      <div className="py-32 flex justify-center">
        <span className="text-title text-gray-600 gm-breathe">Memuat profil…</span>
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <div className="gm-rise py-28 max-w-md mx-auto text-center space-y-6">
        <h1 className="gm-display text-headline">Profil belum terbaca</h1>
        <p className="gm-lead text-body">
          Pastikan server GlowMatch dan database sedang berjalan, lalu coba lagi.
        </p>
        {error && <p className="text-sm text-accent">{error}</p>}
        <button type="button" onClick={handleRetry} className="gm-btn">
          <FiRefreshCw /> Coba lagi
        </button>
      </div>
    );
  }

  return (
    <div className="pt-8 pb-4 max-w-5xl mx-auto grid lg:grid-cols-[1fr_1.1fr] gap-12 lg:gap-16 items-start">

      <div className="lg:sticky lg:top-28">
        <h1 className="gm-display gm-rise text-display">Lengkapi profil</h1>
        <p className="gm-lead gm-rise text-body-lg max-w-sm mt-5" style={{ '--d': '120ms' }}>
          Nama dan preferensimu dipakai untuk riwayat dan laporan PDF.
        </p>
        <div className="gm-rise flex gap-2 mt-10" style={{ '--d': '220ms' }} aria-hidden="true">
          {['#f69179', '#96a8e0', '#aa2870', '#7e8a59'].map((c, i) => (
            <span key={c} className="w-4 h-4 rounded-full gm-breathe" style={{ background: c, animationDelay: `${i * 220}ms` }} />
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="gm-card gm-rise p-7 sm:p-9 space-y-6" style={{ '--d': '180ms' }}>
        <div>
          <label htmlFor="setup-name" className="gm-label">Nama</label>
          <input
            id="setup-name"
            name="name"
            type="text"
            required
            maxLength={120}
            value={formData.name}
            onChange={handleChange}
            placeholder="Contoh: Alya Maharani"
            className="gm-input"
          />
        </div>

        <div>
          <span className="gm-label">Gender</span>
          <div className="grid grid-cols-3 gap-2.5">
            {[
              { id: 'wanita', label: 'Wanita' },
              { id: 'pria', label: 'Pria' },
              { id: 'lainnya', label: 'Lainnya' },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={formData.gender === item.id}
                onClick={() => {
                  setFormData((prev) => ({ ...prev, gender: item.id }));
                  setError('');
                }}
                className="gm-choice"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="setup-age" className="gm-label">Umur</label>
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
            className="gm-input"
          />
        </div>

        <div>
          <label htmlFor="setup-notes" className="gm-label">Preferensi gaya</label>
          <textarea
            id="setup-notes"
            name="notes"
            rows="3"
            value={formData.notes}
            onChange={handleChange}
            placeholder="Contoh: minimalis, earthy tone..."
            className="gm-input resize-none"
          />
        </div>

        {error && <p className="gm-open text-small text-accent">{error}</p>}

        <button type="submit" disabled={loading} className="gm-btn w-full py-4">
          {loading ? (
            <><FiSave /> Menyimpan...</>
          ) : (
            <>Simpan dan mulai <FiArrowRight /></>
          )}
        </button>
      </form>
    </div>
  );
};

export default ProfileSetup;
