import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiArrowRight, FiPlus } from 'react-icons/fi';
import HeroModel from '../assets/hero-model.jpg';
import Reveal from '../components/Reveal';

// Halaman "Tentang": satu pesan per section, tanpa jargon teknis.
// Tips memotret sengaja tidak di sini — tampil di halaman scan, saat dibutuhkan.

const SEASONS = [
  { name: 'Spring', family: 'Hangat & cerah', colors: ['#f7b267', '#f79d84', '#f25c54', '#7bc9a6'] },
  { name: 'Summer', family: 'Sejuk & lembut', colors: ['#b8c4e8', '#e6b8cf', '#9fb7c9', '#c3aed6'] },
  { name: 'Autumn', family: 'Hangat & redup', colors: ['#c0663f', '#8a8a4a', '#d4a24c', '#7a4a32'] },
  { name: 'Winter', family: 'Sejuk & kontras', colors: ['#9b1d3a', '#1f3a93', '#0f7b5f', '#1b1b2f'] },
];

const STEPS = [
  { title: 'Foto wajah', desc: 'AI membaca warna kulit, mata, rambut, dan bibirmu.' },
  { title: 'Foto pergelangan tangan', desc: 'Memastikan undertone: hangat, dingin, atau netral.' },
  { title: 'Dapatkan paletmu', desc: 'Season, warna terbaik, warna yang dihindari, dan PDF.' },
];

const FAQS = [
  {
    q: 'Apa itu analisis warna personal?',
    a: 'Metode yang mengelompokkan warna ke dalam 12 season berdasarkan undertone, kontras, dan kejernihan, untuk menemukan palet busana dan riasan yang paling cocok denganmu.',
  },
  {
    q: 'Apakah season bisa berubah seiring usia?',
    a: 'Undertone kulit cenderung tetap. Perubahan warna rambut atau kulit bisa menggeser hasilmu ke season terdekat dalam keluarga yang sama.',
  },
  {
    q: 'Bagaimana kalau ruangan kurang terang?',
    a: 'Gunakan cahaya putih yang merata, misalnya dari jendela atau lampu HP. Sisa bias warna lampu dikoreksi otomatis.',
  },
];

const Home = () => {
  const [openFaq, setOpenFaq] = useState(null);

  return (
    <div className="pb-8">

      {/* HERO */}
      <section className="grid lg:grid-cols-[1.15fr_1fr] items-center gap-14 pt-10 lg:pt-16 lg:min-h-[min(calc(100svh-140px),760px)]">
        <div>
          <h1 className="gm-display gm-rise text-display-xl" style={{ '--d': '60ms' }}>
            Warna yang<br />membuatmu<br /><em>bercahaya.</em>
          </h1>
          <p className="gm-lead gm-rise text-body-lg max-w-md mt-8" style={{ '--d': '200ms' }}>
            Dua foto singkat, lalu kamu tahu season dan palet warna yang paling cocok.
          </p>
          <div className="gm-rise mt-10" style={{ '--d': '320ms' }}>
            <Link to="/scan-wajah" className="gm-btn">
              Mulai analisis <FiArrowRight aria-hidden="true" />
            </Link>
          </div>
        </div>

        <div className="gm-rise relative flex justify-center lg:justify-end" style={{ '--d': '180ms' }}>
          <div className="relative w-full max-w-[400px]">
            {/* Empat titik warna logo mengorbit bingkai */}
            {['#f69179', '#96a8e0', '#aa2870', '#7e8a59'].map((c, i) => (
              <span
                key={c}
                className="absolute w-5 h-5 rounded-full shadow-md z-10 animate-[gm-drift-a_9s_ease-in-out_infinite]"
                style={{
                  background: c,
                  animationDelay: `${i * -2.2}s`,
                  ...[{ top: '6%', left: '-2%' }, { top: '18%', right: '-4%' }, { bottom: '20%', left: '-5%' }, { bottom: '4%', right: '8%' }][i],
                }}
                aria-hidden="true"
              />
            ))}
            <div className="relative aspect-[3/4] rounded-[999px] overflow-hidden bg-[#f3e2d4] shadow-[0_40px_80px_-40px_rgba(90,40,100,.55)] group">
              <img
                src={HeroModel}
                alt="Model GlowMatch"
                className="w-full h-full object-cover object-top scale-105 transition-transform duration-[1.4s] ease-out group-hover:scale-100"
              />
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute w-full h-px bg-paper/80 animate-scan" />
                <div className="absolute w-full h-20 -translate-y-10 bg-gradient-to-b from-transparent via-paper/25 to-transparent animate-scan" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* EMPAT KELUARGA */}
      <section className="mt-36 grid lg:grid-cols-[1fr_1.4fr] gap-12 lg:gap-20">
        <Reveal>
          <h2 className="gm-display text-headline">Empat keluarga, dua belas season</h2>
          <p className="gm-lead text-body-lg mt-5 max-w-md">
            Season ditentukan oleh undertone kulit, warna mata dan rambut, serta kontras wajahmu.
          </p>
          <Link to="/penjelasan-analisis" className="gm-link text-small font-medium mt-6">
            Pelajari teori warna <FiArrowRight aria-hidden="true" />
          </Link>
        </Reveal>

        <div className="grid grid-cols-2 gap-4 sm:gap-5">
          {SEASONS.map((s, i) => (
            <Reveal key={s.name} delay={i * 60} className="gm-card p-6 sm:p-7">
              <div className="flex gap-1.5 mb-6" aria-hidden="true">
                {s.colors.map((c) => (
                  <span key={c} className="w-7 h-7 sm:w-9 sm:h-9 rounded-full ring-2 ring-paper" style={{ background: c }} />
                ))}
              </div>
              <h3 className="text-title-lg">{s.name}</h3>
              <p className="text-small text-gray-600 mt-1">{s.family}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CARA KERJA */}
      <Reveal as="section" id="cara-kerja" className="scroll-mt-24 mt-36 rounded-[36px] bg-ink text-paper px-7 py-14 sm:px-14 sm:py-20 relative overflow-hidden">
        <span className="absolute -right-24 -top-24 w-80 h-80 rounded-full bg-accent/40 blur-[90px] animate-[gm-drift-b_18s_ease-in-out_infinite]" aria-hidden="true" />
        <span className="absolute -left-20 bottom-0 w-72 h-72 rounded-full bg-[#6b46c1]/40 blur-[90px] animate-[gm-drift-a_22s_ease-in-out_infinite]" aria-hidden="true" />
        <h2 className="gm-display text-paper text-headline relative">Cara kerjanya</h2>
        <ol className="grid md:grid-cols-3 gap-10 mt-12 relative">
          {STEPS.map((s, i) => (
            <li key={s.title} className="border-t border-white/15 pt-6">
              <span className="gm-index text-headline text-[#d9b6d4]" aria-hidden="true">0{i + 1}</span>
              <h3 className="text-title text-paper mt-4">{s.title}</h3>
              <p className="text-body text-[#cdbfdc] mt-2">{s.desc}</p>
            </li>
          ))}
        </ol>
      </Reveal>

      {/* FAQ */}
      <section className="mt-36 max-w-3xl mx-auto">
        <Reveal>
          <h2 className="gm-display text-headline text-center">Pertanyaan umum</h2>
        </Reveal>
        <div className="mt-10 border-t border-line">
          {FAQS.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={faq.q} className="border-b border-line">
                <button
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                  className="w-full text-left py-6 flex items-center justify-between gap-6 text-body-lg font-medium hover:text-accent transition-colors"
                >
                  <span>{faq.q}</span>
                  <FiPlus aria-hidden="true" className={`shrink-0 text-xl transition-transform duration-500 ${isOpen ? 'rotate-45 text-accent' : 'text-gray-600'}`} />
                </button>
                <div className={`grid transition-[grid-template-rows,opacity] duration-500 ease-out ${isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
                  <div className="overflow-hidden">
                    <p className="pb-6 pr-10 text-body text-gray-600">{faq.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* CTA penutup — satu-satunya ajakan di bawah halaman (footer tidak lagi punya CTA) */}
      <Reveal as="section" className="mt-36 text-center">
        <h2 className="gm-display text-display">Siap menemukan warnamu?</h2>
        <Link to="/scan-wajah" className="gm-btn mt-10">
          Mulai analisis <FiArrowRight aria-hidden="true" />
        </Link>
      </Reveal>

    </div>
  );
};

export default Home;
