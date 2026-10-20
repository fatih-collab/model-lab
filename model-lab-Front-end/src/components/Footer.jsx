import { Link } from 'react-router-dom';
import { FiHeart, FiShield, FiCamera, FiBookOpen, FiUser, FiClock } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import LogoGlowMatch from '../assets/logo.jpeg';

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-20 text-gray-600">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-12">
          
          {/* Kolom 1-2: Brand & Misi */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="flex items-center gap-3">
              <img 
                src={LogoGlowMatch} 
                alt="GlowMatch Logo" 
                className="w-9 h-9 object-cover rounded-xl shadow-sm" 
              />
              <span className="font-bold text-xl text-glowmatch-secondary tracking-tight">
                GlowMatch
              </span>
            </Link>
            <p className="text-sm text-gray-500 leading-relaxed max-w-sm">
              Platform analisis warna personal (Seasonal Color Analysis) bertenaga AI. Temukan harmoni warna kulit alami untuk meningkatkan rasa percaya diri dalam berbusana, makeup, dan gaya sehari-hari.
            </p>
            <div className="flex items-center gap-2 text-xs text-gray-500 bg-purple-50/70 border border-purple-100/60 p-3 rounded-xl max-w-sm">
              <FiShield className="text-glowmatch-primary shrink-0 text-base" />
              <span>
                <strong>Privasi Terjamin:</strong> Citra wajah diproses secara aman untuk analisis warna dan tidak disimpan ke server publik.
              </span>
            </div>
          </div>

          {/* Kolom 3: Layanan & Fitur */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-glowmatch-secondary uppercase tracking-wider">Fitur Utama</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/scan-wajah" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <FiCamera className="text-xs text-gray-400" /> Analisis Wajah
                </Link>
              </li>
              <li>
                <Link to="/scan-undertone" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <HiSparkles className="text-xs text-gray-400" /> Verifikasi Undertone
                </Link>
              </li>
              <li>
                <Link to="/hasil" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <HiSparkles className="text-xs text-gray-400" /> Palet Musim Saya
                </Link>
              </li>
              <li>
                <Link to="/riwayat" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <FiClock className="text-xs text-gray-400" /> Riwayat Analisis
                </Link>
              </li>
            </ul>
          </div>

          {/* Kolom 4: Edukasi Warna */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-glowmatch-secondary uppercase tracking-wider">Edukasi Warna</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/penjelasan-analisis" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <FiBookOpen className="text-xs text-gray-400" /> Teori 12 Musim Warna
                </Link>
              </li>
              <li>
                <Link to="/penjelasan-analisis" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <FiBookOpen className="text-xs text-gray-400" /> Warm vs Cool Undertone
                </Link>
              </li>
              <li>
                <Link to="/full-palette/utama" className="hover:text-glowmatch-primary transition">
                  Koleksi Warna Utama
                </Link>
              </li>
              <li>
                <Link to="/full-palette/netral" className="hover:text-glowmatch-primary transition">
                  Koleksi Warna Netral
                </Link>
              </li>
            </ul>
          </div>

          {/* Kolom 5: Profil & Akun */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-glowmatch-secondary uppercase tracking-wider">Pengguna</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/profil" className="hover:text-glowmatch-primary transition flex items-center gap-1.5">
                  <FiUser className="text-xs text-gray-400" /> Pengaturan Profil
                </Link>
              </li>
              <li>
                <Link to="/profil" className="hover:text-glowmatch-primary transition">
                  Gender & Preferensi Gaya
                </Link>
              </li>
              <li>
                <Link to="/riwayat" className="hover:text-glowmatch-primary transition">
                  Database Tersimpan
                </Link>
              </li>
            </ul>
          </div>

        </div>

        {/* Garis batas bawah */}
        <div className="border-t border-gray-100 mt-12 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-400">
          <p>© {new Date().getFullYear()} GlowMatch. Semua hak dilindungi.</p>
          <div className="flex items-center gap-1 text-gray-500">
            Dibuat dengan <FiHeart className="text-rose-400 inline" /> untuk pancaran kilau warna alami Anda.
          </div>
        </div>
      </div>
    </footer>
  );
}
