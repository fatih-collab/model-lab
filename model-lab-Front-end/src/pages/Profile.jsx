import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FiSave, FiCheck, FiArrowRight } from 'react-icons/fi';
import { useAnalysis } from '../context/AnalysisContext';
import SavedResults from '../components/SavedResults';

const DEFAULT_FORM = {
  name: 'Pengguna GlowMatch',
  gender: 'wanita',
  age: 22,
  notes: '',
};

const GENDERS = [
  { id: 'wanita', label: 'Wanita' },
  { id: 'pria', label: 'Pria' },
  { id: 'lainnya', label: 'Lainnya' },
];

const Profile = () => {
  // Bagian dipilih dari dropdown profil di navbar.
  const [searchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') === 'simpan' ? 'simpan' : 'profil';

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
    <div className="pt-8 pb-4 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-14">
        <h1 className="gm-display gm-rise text-display">Profil</h1>
        <nav className="gm-seg gm-rise self-start sm:self-auto" style={{ '--d': '120ms' }} aria-label="Bagian profil">
          <Link to="/profil" aria-current={activeTab === 'profil' ? 'page' : undefined}>Identitas</Link>
          <Link to="/profil?tab=simpan" aria-current={activeTab === 'simpan' ? 'page' : undefined}>Hasil tersimpan</Link>
        </nav>
      </div>

      {activeTab === 'simpan' && <SavedResults />}

      {activeTab === 'profil' && (
        <div className="space-y-8">

          {profileLoading && (
            <div className="gm-shimmer h-40 rounded-[28px]" />
          )}

          {!profileLoading && profileError && (
            <div className="gm-open rounded-2xl border border-[#ecc3d6] bg-[#fbeef3] p-5 flex flex-wrap items-center justify-between gap-3">
              <p className="text-small text-accent">
                Gagal mengambil profil: {profileError.message}
              </p>
              <button type="button" onClick={handleRetry} className="gm-link text-small font-medium text-accent">
                Muat ulang
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">

            {/* Form profil */}
            <div className="md:col-span-7 gm-card gm-rise p-7 sm:p-9" style={{ '--d': '160ms' }}>
              <div className="flex items-center gap-5 pb-7 border-b border-line">
                <span className="w-16 h-16 rounded-full bg-ink text-paper flex items-center justify-center text-title-lg">
                  {formData.name ? formData.name.charAt(0).toUpperCase() : 'G'}
                </span>
                <div className="min-w-0">
                  <h2 className="text-title-lg truncate">{formData.name || 'Tanpa nama'}</h2>
                  <p className="text-small text-gray-600 capitalize">
                    {formData.gender}{formData.age ? ` · ${formData.age} tahun` : ''}
                  </p>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6 pt-7">
                <div>
                  <label htmlFor="name" className="gm-label">Nama</label>
                  <input
                    id="name"
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
                    {GENDERS.map((g) => (
                      <button
                        key={g.id}
                        type="button"
                        aria-pressed={formData.gender === g.id}
                        onClick={() => {
                          setFormData((prev) => ({ ...prev, gender: g.id }));
                          setSaved(false);
                          setSaveError('');
                        }}
                        className="gm-choice"
                      >
                        {g.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label htmlFor="age" className="gm-label">Umur</label>
                  <input
                    id="age"
                    name="age"
                    type="number"
                    min="5"
                    max="100"
                    value={formData.age}
                    onChange={handleChange}
                    placeholder="Contoh: 23"
                    className="gm-input"
                  />
                </div>

                <div>
                  <label htmlFor="notes" className="gm-label">Preferensi gaya</label>
                  <textarea
                    id="notes"
                    name="notes"
                    rows="3"
                    value={formData.notes}
                    onChange={handleChange}
                    placeholder="Contoh: minimalis, hijab kasual, earthy tone..."
                    className="gm-input resize-none"
                  />
                </div>

                {saveError && (
                  <p className="gm-open text-small text-accent">{saveError}</p>
                )}

                <button
                  type="submit"
                  disabled={loading || profileLoading}
                  className="gm-btn w-full py-4"
                >
                  {loading ? (
                    <><FiSave /> Menyimpan...</>
                  ) : saved ? (
                    <><FiCheck className="text-[#c9d6a0]" /> Tersimpan</>
                  ) : (
                    <><FiSave /> Simpan perubahan</>
                  )}
                </button>
              </form>
            </div>

            {/* Hasil terkini */}
            <div className="md:col-span-5 gm-rise rounded-[28px] bg-ink text-paper p-8 relative overflow-hidden" style={{ '--d': '260ms' }}>
              <span className="absolute -right-16 -top-16 w-56 h-56 rounded-full bg-accent/45 blur-[70px] animate-[gm-drift-b_16s_ease-in-out_infinite]" aria-hidden="true" />
              {result ? (
                <div className="relative">
                  <p className="text-small font-medium text-[#d9b6d4]">Season kamu</p>
                  <h3 className="gm-display text-paper text-headline mt-2">{result.result.season.name}</h3>
                  <p className="text-small text-[#cdbfdc] capitalize mt-2">{result.result.gate.undertone}</p>
                  <div className="flex -space-x-2 mt-7">
                    {result.result.season.palette.palettes.utama.slice(0, 6).map((color, i) => (
                      <span
                        key={color.hex}
                        className="gm-pop w-10 h-10 rounded-full ring-2 ring-ink"
                        style={{ backgroundColor: color.hex, '--d': `${300 + i * 60}ms` }}
                        title={color.name}
                      />
                    ))}
                  </div>
                  <Link to="/hasil" className="gm-btn bg-paper text-ink hover:bg-white mt-9">
                    Buka hasil <FiArrowRight />
                  </Link>
                </div>
              ) : (
                <div className="relative">
                  <h3 className="gm-display text-paper text-headline">Belum ada season</h3>
                  <Link to="/scan-wajah" className="gm-btn bg-paper text-ink hover:bg-white mt-9">
                    Mulai analisis <FiArrowRight />
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
