import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import ScanFace from './pages/ScanFace';
import ScanUndertone from './pages/ScanUndertone';
import Result from './pages/Result';
import FullPalette from './pages/FullPalette';
import Riwayat from './pages/Riwayat';
import Profile from './pages/Profile';
import AnalysisExplanation from './pages/AnalysisExplanation';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-glowmatch-background flex flex-col justify-between">
        <div>
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/scan-wajah" element={<ScanFace />} />
              <Route path="/scan-undertone" element={<ScanUndertone />} />
              <Route path="/hasil" element={<Result />} />
              <Route path="/full-palette/:type" element={<FullPalette />} />
              <Route path="/riwayat" element={<Riwayat />} />
              <Route path="/profil" element={<Profile />} />
              <Route path="/penjelasan-analisis" element={<AnalysisExplanation />} />
            </Routes>
          </main>
        </div>
        <Footer />
      </div>
    </Router>
  );
}

export default App;