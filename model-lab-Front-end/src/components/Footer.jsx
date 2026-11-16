import { Link } from 'react-router-dom';
import { FiArrowUpRight } from 'react-icons/fi';
import Reveal from './Reveal';

const LINKS = [
  { name: 'Pindai wajah', to: '/scan-wajah' },
  { name: 'Hasil warna', to: '/hasil' },
  { name: 'Riwayat', to: '/riwayat' },
  { name: 'Teori warna', to: '/penjelasan-analisis' },
  { name: 'Profil', to: '/profil' },
];

export default function Footer() {
  return (
    <footer className="relative z-[1] mt-28">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        <Reveal className="border-t border-line pt-10 pb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-10">
          <div>
            <p className="gm-display text-[44px] sm:text-[56px]">
              Kenali warna.<br /><em>Percaya diri.</em>
            </p>
            <Link to="/scan-wajah" className="group mt-7 inline-flex items-center gap-3">
              <span className="gm-orb"><FiArrowUpRight /></span>
              <span className="text-[15px]">Mulai analisis baru</span>
            </Link>
          </div>

          <nav aria-label="Navigasi bawah" className="flex flex-wrap gap-x-9 gap-y-3 text-[14px]">
            {LINKS.map((l) => (
              <Link key={l.name} to={l.to} className="gm-link text-gray-600 hover:text-ink">
                {l.name}
              </Link>
            ))}
          </nav>
        </Reveal>
      </div>
    </footer>
  );
}
