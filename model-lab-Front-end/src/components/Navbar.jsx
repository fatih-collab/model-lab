import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiUser, FiChevronDown } from 'react-icons/fi';
import { BsBookmarkFill } from 'react-icons/bs';
import LogoGlowMatch from '../assets/logo.jpeg'; 
import { useAnalysis } from '../context/AnalysisContext';

const Navbar = () => {
  const location = useLocation();
  const { profile } = useAnalysis();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Tutup dropdown saat klik di luar atau tekan Escape.
  useEffect(() => {
    if (!menuOpen) return undefined;

    const onPointerDown = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setMenuOpen(false);
    };

    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [menuOpen]);

  const profileMenu = [
    { name: 'Profil', desc: 'Identitas personal', path: '/profil', icon: FiUser },
    { name: 'Simpan Hasil', desc: 'Season & warna tersimpan', path: '/profil?tab=simpan', icon: BsBookmarkFill },
  ];

  const navLinks = [
    { name: 'Beranda', path: '/beranda' },
    { name: 'Hasil Warna', path: '/hasil' },
    { name: 'Riwayat', path: '/riwayat' },
    { name: 'Profil', path: '/profil' },
  ];

  const displayName = profile?.name ? profile.name.split(' ')[0] : 'Profil';
  const initial = profile?.name ? profile.name.charAt(0).toUpperCase() : 'U';

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40 backdrop-blur-md bg-white/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          {/* Bagian Kiri: Logo GlowMatch */}
          <div className="flex-shrink-0 flex items-center">
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
          </div>

          {/* Bagian Tengah: Menu Navigasi */}
          <div className="hidden md:flex flex-1 justify-center items-center space-x-10">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path || 
                               (link.path !== '/' && location.pathname.startsWith(link.path));
              
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`text-sm font-semibold transition-colors duration-200 border-b-2 px-1 py-2 ${
                    isActive
                      ? 'border-glowmatch-primary text-glowmatch-primary' 
                      : 'border-transparent text-gray-500 hover:text-glowmatch-primary'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* Bagian Kanan: Profil Badge dengan dropdown */}
          <div className="relative flex items-center gap-3" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex items-center gap-2.5 pl-1.5 pr-3 py-1.5 rounded-full hover:bg-gray-100 transition border border-gray-200/80 bg-gray-50/50"
              title="Menu Profil"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 text-white flex items-center justify-center text-xs font-bold shadow-sm">
                {initial}
              </div>
              <span className="text-xs font-semibold text-gray-700 hidden sm:inline-block max-w-[120px] truncate">
                {displayName}
              </span>
              <FiChevronDown className={`text-gray-500 text-sm transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="absolute right-0 top-full mt-2 w-60 bg-white border border-gray-100 rounded-2xl shadow-lg p-1.5 z-50"
              >
                {profileMenu.map(({ name, desc, path, icon: Icon }) => (
                  <Link
                    key={name}
                    to={path}
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-purple-50 transition"
                  >
                    <span className="w-8 h-8 rounded-lg bg-purple-50 text-glowmatch-primary flex items-center justify-center text-sm">
                      <Icon />
                    </span>
                    <span>
                      <span className="block text-sm font-semibold text-glowmatch-secondary">{name}</span>
                      <span className="block text-[11px] text-gray-400">{desc}</span>
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;