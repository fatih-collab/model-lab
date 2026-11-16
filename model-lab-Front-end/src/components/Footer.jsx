import { Link } from 'react-router-dom';

// Footer fungsional: tautan + hak cipta. Tanpa slogan dan tanpa CTA,
// supaya ajakan "Mulai analisis" tidak muncul dua kali di setiap halaman.
const LINKS = [
  { name: 'Tentang', to: '/beranda' },
  { name: 'Hasil warna', to: '/hasil' },
  { name: 'Riwayat', to: '/riwayat' },
  { name: 'Teori warna', to: '/penjelasan-analisis' },
  { name: 'Profil', to: '/profil' },
];

export default function Footer() {
  return (
    // pb-24 di layar kecil: memberi ruang untuk tombol Chat AI yang mengambang.
    <footer className="relative z-[1] mt-24">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        <div className="border-t border-line pt-8 pb-24 sm:pb-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <p className="text-small text-gray-600">© {new Date().getFullYear()} GlowMatch</p>
          <nav aria-label="Navigasi bawah" className="flex flex-wrap gap-x-8 gap-y-2 text-small sm:pr-40">
            {LINKS.map((l) => (
              <Link key={l.name} to={l.to} className="gm-link text-gray-600 hover:text-ink">
                {l.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </footer>
  );
}
