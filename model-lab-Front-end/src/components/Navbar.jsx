import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiUser, FiChevronDown, FiMenu, FiX } from 'react-icons/fi';
import { BsBookmarkFill } from 'react-icons/bs';
import logoTile from '../assets/logo-tile.webp';
import { useAnalysis } from '../context/AnalysisContext';

// Label sentence case dan sama dengan navigasi di landing.
const NAV_LINKS = [
  { name: 'Tentang', path: '/beranda' },
  { name: 'Hasil warna', path: '/hasil' },
  { name: 'Riwayat', path: '/riwayat' },
  { name: 'Teori warna', path: '/penjelasan-analisis' },
];

const PROFILE_MENU = [
  { name: 'Profil', path: '/profil', icon: FiUser },
  { name: 'Hasil tersimpan', path: '/profil?tab=simpan', icon: BsBookmarkFill },
];

const Navbar = () => {
  const location = useLocation();
  const { profile } = useAnalysis();
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
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

  // Garis bawah navbar muncul setelah halaman digulir.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const displayName = profile?.name ? profile.name.split(' ')[0] : 'Profil';
  const initial = profile?.name ? profile.name.charAt(0).toUpperCase() : 'G';
  const isActive = (path) => location.pathname === path || location.pathname.startsWith(`${path}/`);

  return (
    <nav
      className={`sticky top-0 z-40 transition-[background-color,border-color,backdrop-filter] duration-300 border-b ${
        scrolled ? 'bg-paper/95 backdrop-blur-xl border-line' : 'bg-transparent border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        <div className="flex justify-between items-center h-[72px] gap-6">

          <Link to="/" className="flex items-center gap-2.5 shrink-0 group" aria-label="GlowMatch, ke halaman awal">
            <img
              src={logoTile}
              alt=""
              width="30"
              height="30"
              className="w-[30px] h-[30px] rounded-[9px] shadow-[0_2px_8px_rgba(120,60,120,.18)] transition-transform duration-500 group-hover:rotate-[-8deg] group-hover:scale-105"
            />
            <span className="text-[26px] leading-none tracking-[-1.4px]">
              glowmatch<span className="text-accent">.</span>
            </span>
          </Link>

          <div className="hidden md:flex flex-1 justify-center items-center gap-9">
            {NAV_LINKS.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`relative text-small font-medium py-2 transition-colors ${active ? 'text-ink' : 'text-gray-600 hover:text-ink'}`}
                >
                  {link.name}
                  <span
                    className={`absolute left-0 right-0 -bottom-0.5 h-px bg-ink origin-left transition-transform duration-500 ${active ? 'scale-x-100' : 'scale-x-0'}`}
                  />
                </Link>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((open) => !open)}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="flex items-center gap-2.5 pl-1.5 pr-3.5 py-1.5 rounded-full border border-[#d6c6d6] hover:bg-[#f0e5ef] transition"
              >
                <span className="w-7 h-7 rounded-full bg-ink text-paper flex items-center justify-center text-label">
                  {initial}
                </span>
                <span className="text-small font-medium hidden sm:inline-block max-w-[120px] truncate">{displayName}</span>
                <FiChevronDown className={`text-gray-500 text-sm transition-transform duration-300 ${menuOpen ? 'rotate-180' : ''}`} />
              </button>

              {menuOpen && (
                <div
                  role="menu"
                  className="gm-open absolute right-0 top-full mt-2 w-52 bg-paper/95 backdrop-blur-xl border border-line rounded-3xl shadow-[0_20px_40px_-20px_rgba(42,29,59,.35)] p-1.5 z-50"
                >
                  {PROFILE_MENU.map(({ name, path, icon: Icon }) => (
                    <Link
                      key={name}
                      to={path}
                      role="menuitem"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-2xl text-small hover:bg-chip transition"
                    >
                      <Icon className="text-accent text-small" aria-hidden="true" />
                      {name}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <button
              type="button"
              className="md:hidden w-10 h-10 rounded-full border border-[#d6c6d6] flex items-center justify-center"
              onClick={() => setMobileOpen((v) => !v)}
              aria-expanded={mobileOpen}
              aria-label={mobileOpen ? 'Tutup menu' : 'Buka menu'}
            >
              {mobileOpen ? <FiX /> : <FiMenu />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <div className="md:hidden gm-open pb-5 flex flex-col">
            {NAV_LINKS.map((link, i) => (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setMobileOpen(false)}
                className={`gm-rise py-3 border-b border-line text-title ${isActive(link.path) ? 'text-ink' : 'text-gray-600'}`}
                style={{ '--d': `${i * 50}ms` }}
              >
                {link.name}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
