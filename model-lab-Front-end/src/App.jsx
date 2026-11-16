
import { useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';

import Navbar from './components/Navbar';
import Footer from './components/Footer';

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
      <div className="py-24 max-w-md mx-auto text-center space-y-3">
        <p className="text-sm text-gray-500">
          Memeriksa profil pengguna...
        </p>
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
      <div className="py-24 max-w-md mx-auto text-center space-y-4">
        <h1 className="text-2xl font-semibold text-glowmatch-secondary">
          Profil belum dapat diperiksa
        </h1>

        <p className="text-sm text-gray-500">
          Pastikan backend GlowMatch berjalan dan koneksi
          database tersedia sebelum memulai analisis.
        </p>

        {retryError && (
          <p className="text-sm text-red-600">
            {retryError}
          </p>
        )}

        <button
          type="button"
          onClick={handleRetry}
          disabled={retrying}
          className="bg-glowmatch-primary text-white px-6 py-3 rounded-xl font-semibold disabled:opacity-60"
        >
          {retrying ? 'Memeriksa...' : 'Coba Lagi'}
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
// MAIN APPLICATION
// ============================================================

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-glowmatch-background flex flex-col justify-between">

        <div>
          <Navbar />

          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

            <Routes>
              {/* Landing Page */}
              <Route
                path="/"
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
            </Routes>

          </main>
        </div>

        <Footer />
      </div>
    </Router>
  );
}

export default App;
