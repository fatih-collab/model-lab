import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { FiChevronDown } from 'react-icons/fi';
import logoTile from '../assets/logo-tile.webp';
import '../landing.css';

// Three.js (~600 KB) hanya diunduh ketika landing page dibuka.
const LogoSculpture = lazy(() => import('../components/LogoSculpture'));

// Menu yang muncul saat kursor menyentuh logo. Warna titik = empat lingkaran di logo.
const MENU_ITEMS = [
  { label: 'Mulai Analisis', to: '/scan-wajah', color: '#f69179', primary: true },
  { label: 'Hasil Warna', to: '/hasil', color: '#96a8e0' },
  { label: 'Riwayat', to: '/riwayat', color: '#aa2870' },
  { label: 'Simpan Hasil', to: '/profil?tab=simpan', color: '#7e8a59' },
  { label: 'Profil', to: '/profil', color: '#f69179' },
  { label: 'Teori Warna', to: '/penjelasan-analisis', color: '#96a8e0' },
  { label: 'Tentang GlowMatch', to: '/beranda', color: '#aa2870' },
];

const CLOSE_DELAY_MS = 320;

function LogoMenu({ open, onEnter, onLeave, onBlur }) {
  const count = MENU_ITEMS.length;
  return (
    <nav id="logo-menu" className={`logo-menu${open ? ' is-open' : ''}`} aria-label="Menu GlowMatch" onPointerEnter={onEnter} onPointerLeave={onLeave} onFocus={onEnter} onBlur={onBlur}>
      <ul>
        {MENU_ITEMS.map((item, i) => {
          // Lengkung tipis: item di ujung sedikit menjauh dari logo, item tengah paling dekat.
          const t = count > 1 ? (i / (count - 1)) * 2 - 1 : 0;
          const style = { '--i': i, '--n': count, '--x': `${Math.round(34 * t * t)}px` };
          return (
            <li key={item.label} style={style}>
              <Link to={item.to} className={item.primary ? 'is-primary' : undefined} tabIndex={open ? 0 : -1}>
                <span className="menu-dot" style={{ background: item.color }} aria-hidden="true" />
                <span className="menu-label">{item.label}</span>
              </Link>
            </li>
          );
        })}
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

  const menuButton = (
    <button
      type="button"
      className="spin-button"
      onClick={togglePinned}
      aria-expanded={open}
      aria-controls="logo-menu"
    >
      Menu
      <FiChevronDown className="chev" aria-hidden="true" size={14} />
    </button>
  );

  return (
    <div className="gm-landing">
      <main className="studio-footer" aria-label="GlowMatch — analisis warna personal">
        <div className="studio-topline">
          <div className="wordmark" role="img" aria-label="GlowMatch">
            <img className="wordmark-mark" src={logoTile} alt="" width="32" height="32" />
            <span>glowmatch<span className="wordmark-period">.</span></span>
          </div>
          <div className="studio-descriptor">WARNA YANG PAS.<br />PERCAYA DIRI, SETIAP HARI.</div>
          <div className="availability"><span aria-hidden="true" />AI SIAP MEMINDAI</div>
        </div>

        <div className="studio-main">
          <div className="studio-story">
            <div className="eyebrow"><span className="eyebrow-line" /> PERSONAL COLOR ANALYSIS BERTENAGA AI</div>
            <h1>Temukan warnamu.<br />Pancarkan <em>cahayamu.</em></h1>
            <p className="studio-intro">
              Kenali season warnamu lewat analisis AI.<br />
              Dari wajah, kulit, hingga undertone pergelangan tangan,<br className="desktop-break" /> hasilnya personal dan siap dipakai.
            </p>
            <Link to="/scan-wajah" className="conversation">
              <span className="conversation-icon" aria-hidden="true">↗</span>
              <div><span className="conversation-label">SIAP MULAI?</span><p>Mulai analisis sekarang.</p></div>
            </Link>
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
              <LogoSculpture menuOpen={open} onHoverChange={onLogoHover} onTap={togglePinned} controls={menuButton} />
            </Suspense>
            <LogoMenu open={open} onEnter={onMenuEnter} onLeave={onMenuLeave} onBlur={onBlurMenu} />
          </div>
        </div>

        <footer className="footer-bottom">
          <div className="footer-bottom-main">
            <p className="bottom-manifesto">Kenali warna.<br /><em>Percaya diri.</em></p>
            <div className="display-navigation" aria-label="Alur analisis">
              <span>Pindai wajah</span><span>Cek undertone</span><span>Palet season</span><span>Unduh PDF</span>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
