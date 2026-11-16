import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiArrowRight } from 'react-icons/fi';
import logoTile from '../assets/logo-tile.webp';
import '../landing.css';

// Three.js (~600 KB) hanya diunduh ketika landing page dibuka.
const LogoSculpture = lazy(() => import('../components/LogoSculpture'));

// Satu daftar tujuan untuk navigasi atas DAN menu logo, supaya label selalu sama.
// Aksi utama ("Mulai analisis") sengaja tidak masuk sini: ia punya tombol sendiri di hero.
const SITE_LINKS = [
  { label: 'Tentang', to: '/beranda' },
  { label: 'Hasil warna', to: '/hasil' },
  { label: 'Riwayat', to: '/riwayat' },
  { label: 'Teori warna', to: '/penjelasan-analisis' },
  { label: 'Profil', to: '/profil' },
];

const CLOSE_DELAY_MS = 320;

// Menu tambahan yang muncul saat kursor menyentuh logo 3D (atau logo diketuk di layar sentuh).
// Navigasi utama tetap terlihat di bagian atas; menu ini hanya jalan pintas.
function LogoMenu({ open, onEnter, onLeave, onBlur }) {
  const count = SITE_LINKS.length;
  return (
    <nav id="logo-menu" className={`logo-menu${open ? ' is-open' : ''}`} aria-label="Menu logo GlowMatch" onPointerEnter={onEnter} onPointerLeave={onLeave} onFocus={onEnter} onBlur={onBlur}>
      <ul>
        {SITE_LINKS.map((item, i) => (
          <li key={item.to} style={{ '--i': i, '--n': count }}>
            <Link to={item.to} tabIndex={open ? 0 : -1}>
              <span className="menu-label">{item.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export default function Landing() {
  const [open, setOpen] = useState(false);
  const artRef = useRef(null);
  const closeTimer = useRef(0);
  const overMenu = useRef(false); // kursor sedang di atas menu: jangan menutup karena logo kehilangan hover
  const pinned = useRef(false); // true bila dibuka lewat tombol/ketukan: tidak menutup sendiri saat kursor pergi

  const cancelClose = useCallback(() => window.clearTimeout(closeTimer.current), []);
  const openMenu = useCallback(() => {
    cancelClose();
    setOpen(true);
  }, [cancelClose]);
  const scheduleClose = useCallback(() => {
    cancelClose();
    if (pinned.current || overMenu.current) return;
    closeTimer.current = window.setTimeout(() => setOpen(false), CLOSE_DELAY_MS);
  }, [cancelClose]);
  const togglePinned = useCallback(() => {
    cancelClose();
    if (open && pinned.current) {
      pinned.current = false;
      setOpen(false);
    } else {
      pinned.current = true;
      setOpen(true);
    }
  }, [open, cancelClose]);

  const onMenuEnter = useCallback(() => {
    overMenu.current = true;
    openMenu();
  }, [openMenu]);
  const onMenuLeave = useCallback(() => {
    overMenu.current = false;
  }, []);
  const onLogoHover = useCallback((hit) => (hit ? openMenu() : scheduleClose()), [openMenu, scheduleClose]);
  const onBlurMenu = useCallback((event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) scheduleClose();
  }, [scheduleClose]);

  // Escape menutup menu; klik di luar area logo menutup menu yang dibuka lewat tombol/ketukan.
  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        pinned.current = false;
        setOpen(false);
      }
    };
    const onPointerDown = (event) => {
      if (pinned.current && artRef.current && !artRef.current.contains(event.target)) {
        pinned.current = false;
        setOpen(false);
      }
    };
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('pointerdown', onPointerDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('pointerdown', onPointerDown);
    };
  }, [open]);

  useEffect(() => () => window.clearTimeout(closeTimer.current), []);

  // Prinsip halaman ini: satu pesan (judul), satu kalimat penjelas, satu aksi utama.
  // Tanpa eyebrow, pill status, slogan kedua, atau petunjuk interaksi dekoratif.
  return (
    <div className="gm-landing">
      <main className="studio-footer" aria-label="GlowMatch — analisis warna personal">
        <header className="studio-topline">
          <div className="wordmark" role="img" aria-label="GlowMatch">
            <img className="wordmark-mark" src={logoTile} alt="" width="32" height="32" />
            <span>glowmatch<span className="wordmark-period">.</span></span>
          </div>
          <nav className="site-nav" aria-label="Navigasi utama">
            <ul>
              {SITE_LINKS.map((item) => (
                <li key={item.to}><Link to={item.to}>{item.label}</Link></li>
              ))}
            </ul>
          </nav>
        </header>

        <div className="studio-main">
          <div className="studio-story">
            <h1>Temukan warnamu.<br />Pancarkan <em>cahayamu.</em></h1>
            <p className="studio-intro">
              Foto wajah dan pergelangan tanganmu, lalu AI menentukan season dan palet warna
              yang paling cocok.
            </p>
            <div className="hero-actions">
              <Link to="/scan-wajah" className="gm-btn">
                Mulai analisis <FiArrowRight aria-hidden="true" />
              </Link>
              <Link to="/beranda#cara-kerja" className="gm-btn-ghost">Lihat cara kerjanya</Link>
            </div>
          </div>

          <div
            ref={artRef}
            className={`studio-art${open ? ' is-menu-open' : ''}`}
            onPointerLeave={(event) => event.pointerType !== 'touch' && scheduleClose()}
          >
            <Suspense
              fallback={(
                <div className="sculpture-wrap">
                  <img className="fallback-logo" src={logoTile} alt="" width="330" height="330" />
                </div>
              )}
            >
              <LogoSculpture menuOpen={open} onHoverChange={onLogoHover} onTap={togglePinned} showSpinButton={false} />
            </Suspense>
            <LogoMenu open={open} onEnter={onMenuEnter} onLeave={onMenuLeave} onBlur={onBlurMenu} />
          </div>
        </div>
      </main>
    </div>
  );
}
