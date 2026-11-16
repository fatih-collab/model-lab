
import { useEffect, useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
} from 'react-router-dom';
import { FiRefreshCw } from 'react-icons/fi';

import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ChatBubble from './components/ChatBubble';

import Landing from './pages/Landing';
import Home from './pages/Home';
import ScanFace from './pages/ScanFace';
import ScanUndertone from './pages/ScanUndertone';
import ProfileSetup from './pages/ProfileSetup';
import Result from './pages/Result';
import FullPalette from './pages/FullPalette';
import Riwayat from './pages/Riwayat';
import Profile from './pages/Profile';
import AnalysisExplanation from './pages/AnalysisExplanation';

import { useAnalysis } from './context/AnalysisContext';


// ============================================================
// PROFILE ROUTE PROTECTION
// ============================================================

function RequireCompleteProfile({ children }) {
  const {
    profile,
    profileLoading,
    profileError,
    refreshProfile,
  } = useAnalysis();

  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState('');

  // Tunggu sampai status profil dari backend tersedia.
  if (profileLoading) {
    return (
      <div className="py-32 flex justify-center">
        <span className="gm-display text-[34px] text-gray-400 gm-breathe">Sebentar…</span>
      </div>
    );
  }

  // Jangan membuka kamera ketika profil gagal dimuat.
  if (profileError || !profile) {
    const handleRetry = async () => {
      setRetrying(true);
      setRetryError('');

      try {
        await refreshProfile();
      } catch (error) {
        setRetryError(
          error.message || 'Gagal mengambil profil pengguna.'
        );
      } finally {
        setRetrying(false);
      }
    };

    return (
      <div className="gm-rise py-28 max-w-md mx-auto text-center space-y-6">
        <h1 className="gm-display text-[48px]">
          Profil belum <em>terbaca.</em>
        </h1>

        <p className="gm-lead text-[15px]">
          Pastikan server GlowMatch dan database sedang berjalan, lalu coba lagi.
        </p>

        {retryError && (
          <p className="text-sm text-accent">
            {retryError}
          </p>
        )}

        <button
          type="button"
          onClick={handleRetry}
          disabled={retrying}
          className="gm-btn"
        >
          <FiRefreshCw className={retrying ? 'animate-spin' : ''} />
          {retrying ? 'Memeriksa...' : 'Coba lagi'}
        </button>
      </div>
    );
  }

  // Pengguna yang belum melengkapi profil diarahkan ke onboarding.
  if (!profile.is_complete) {
    return (
      <Navigate
        to="/lengkapi-profil"
        replace
      />
    );
  }

  // Hanya profil lengkap yang boleh membuka halaman scan.
  return children;
}


// ============================================================
// LAYOUT SITUS (Navbar + Footer + Chat) untuk semua halaman selain landing
// ============================================================

function SiteLayout() {
  const location = useLocation();

  // Halaman baru dibuka dari atas, kecuali tautan menunjuk ke bagian tertentu (mis. /beranda#cara-kerja).
  useEffect(() => {
    const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (target) target.scrollIntoView();
    else window.scrollTo({ top: 0 });
  }, [location.pathname, location.hash]);

  return (
    <div className="relative min-h-screen bg-paper flex flex-col justify-between overflow-x-clip">
      <div className="gm-ambient" aria-hidden="true">
        <span className="a1" /><span className="a2" /><span className="a3" /><span className="a4" />
      </div>

      <div className="relative z-[1]">
        <Navbar />

        <main key={location.pathname} className="gm-page max-w-7xl mx-auto px-5 sm:px-8">
          <Outlet />
        </main>
      </div>

      <Footer />

      {/* Chat AI rekomendasi outfit (bubble kanan bawah) */}
      <ChatBubble />
    </div>
  );
}


// ============================================================
// MAIN APPLICATION
// ============================================================

function App() {
  return (
    <Router>
      <Routes>
        {/* Landing page: layar penuh, menu muncul saat kursor menyentuh logo 3D */}
        <Route
          path="/"
          element={<Landing />}
        />

        <Route element={<SiteLayout />}>
          {/* Beranda lama (fitur, season, FAQ) */}
          <Route
            path="/beranda"
            element={<Home />}
          />

          {/* Profile Onboarding */}
          <Route
            path="/lengkapi-profil"
            element={<ProfileSetup />}
          />

          {/* Face Scan: hanya setelah profil lengkap */}
          <Route
            path="/scan-wajah"
            element={
              <RequireCompleteProfile>
                <ScanFace />
              </RequireCompleteProfile>
            }
          />

          {/* Undertone Scan: hanya setelah profil lengkap */}
          <Route
            path="/scan-undertone"
            element={
              <RequireCompleteProfile>
                <ScanUndertone />
              </RequireCompleteProfile>
            }
          />

          {/* Existing Features */}
          <Route
            path="/hasil"
            element={<Result />}
          />

          <Route
            path="/full-palette/:type"
            element={<FullPalette />}
          />

          <Route
            path="/riwayat"
            element={<Riwayat />}
          />

          <Route
            path="/profil"
            element={<Profile />}
          />

          <Route
            path="/penjelasan-analisis"
            element={<AnalysisExplanation />}
          />

          {/* Route fallback */}
          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
