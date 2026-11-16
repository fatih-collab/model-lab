import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiArrowRight, FiArrowUpRight, FiPlus } from 'react-icons/fi';
import HeroModel from '../assets/hero-model.jpg';
import Reveal from '../components/Reveal';

const FAQS = [
  {
    q: 'Apa itu Seasonal Color Analysis?',
    a: 'Seasonal Color Analysis adalah metode pengelompokan warna berdasarkan suhu undertone, kejernihan, dan kedalaman kontras. Sistem ini membagi warna menjadi 12 season (Spring, Summer, Autumn, Winter, masing-masing dengan tiga varian) untuk menentukan palet busana dan riasan yang paling cocok dengan warna kulit alamimu.',
  },
  {
    q: 'Apakah warna personal bisa berubah seiring usia?',
    a: 'Undertone dasar kulit (Warm, Cool, atau Neutral) bersifat genetik dan cenderung permanen. Kontras rambut atau kecerahan kulit bisa sedikit berubah, sehingga hasilmu bisa bergeser ke season terdekat dalam keluarga yang sama.',
  },
  {
    q: 'Kenapa pergelangan tangan juga dipindai?',
    a: 'Wajah sering mengalami kemerahan sementara (sunburn, bekas jerawat, rosacea) yang bisa menipu kamera. Bagian dalam pergelangan tangan lebih terlindung, sehingga rona dasar kulitmu terbaca lebih jujur dan undertone bisa dikunci dengan akurat.',
  },
  {
    q: 'Bagaimana kalau ruangan kurang terang?',
    a: 'Gunakan lampu HP atau lampu sendiri (ring light, lampu meja) dengan cahaya putih netral yang merata ke wajah. Algoritma Gray-World White Balance kami akan mengoreksi sisa bias temperatur warna.',
  },
  {
    q: 'Apakah hasil analisis bisa diunduh?',
    a: 'Bisa. Kamu dapat mengunduh laporan PDF yang berisi profil, palet warna utama, warna netral, dan warna yang sebaiknya dihindari.',
  },
];

const SEASONS = [
  { name: 'Spring', family: 'Hangat & cerah', colors: ['#f7b267', '#f79d84', '#f25c54', '#7bc9a6'], desc: 'Peach, coral cerah, warm turquoise, dan emas kuning.' },
  { name: 'Summer', family: 'Sejuk & lembut', colors: ['#b8c4e8', '#e6b8cf', '#9fb7c9', '#c3aed6'], desc: 'Lavender, baby pink, powder blue, dan soft navy.' },
  { name: 'Autumn', family: 'Hangat & redup', colors: ['#c0663f', '#8a8a4a', '#d4a24c', '#7a4a32'], desc: 'Terracotta, olive, mustard, rust, dan bronze.' },
  { name: 'Winter', family: 'Sejuk & kontras', colors: ['#9b1d3a', '#1f3a93', '#0f7b5f', '#1b1b2f'], desc: 'Ruby, sapphire, emerald, hitam pekat, dan icy white.' },
];

const BENEFITS = [
  { title: 'Wajah tampak cerah', desc: 'Warna yang tepat memantulkan cahaya ke wajah dan menyamarkan lingkar mata.', color: '#f69179' },
  { title: 'Belanja lebih tepat', desc: 'Tidak ada lagi baju, hijab, atau lipstik yang akhirnya mengendap di lemari.', color: '#96a8e0' },
  { title: 'Padu padan mudah', desc: 'Warna utama dan netralmu saling menyatu, jadi capsule wardrobe terbentuk sendiri.', color: '#aa2870' },
  { title: 'Lebih percaya diri', desc: 'Tampil meyakinkan di presentasi, wawancara, kencan, sampai foto formal.', color: '#7e8a59' },
];

const STEPS = [
  { title: 'Deteksi wajah & white balance', desc: 'YuNet memetakan kontur wajah, Gray-World menetralkan bias lampu ruangan.' },
  { title: 'Verifikasi undertone', desc: 'Pergelangan tangan mengonfirmasi Warm, Cool, atau Neutral lalu mengunci keluarga season.' },
  { title: 'Season & palet', desc: 'Model ensemble memilih season terbaik, lengkap dengan palet, busana, dan PDF.' },
];

const TIPS = [
  { title: 'Cahaya merata', desc: 'Dekat jendela, ring light, atau lampu HP. Hindari bayangan gelap di wajah.' },
  { title: 'Wajah natural', desc: 'Tanpa foundation tebal supaya warna asli kulit terbaca jelas.' },
  { title: 'Lepas kacamata', desc: 'Rapikan rambut dari dahi agar proporsi wajah terlihat utuh.' },
];

const Home = () => {
  const [openFaq, setOpenFaq] = useState(0);

  return (
    <div className="pb-8">

      {/* HERO */}
      <section className="grid lg:grid-cols-[1.15fr_1fr] items-center gap-14 pt-10 lg:pt-16 lg:min-h-[min(calc(100svh-140px),760px)]">
        <div>
          <h1 className="gm-display gm-rise text-[56px] sm:text-[84px] lg:text-[112px]" style={{ '--d': '60ms' }}>
            Warna yang<br />membuatmu<br /><em>bercahaya.</em>
          </h1>
          <p className="gm-lead gm-rise text-[15px] sm:text-[17px] max-w-md mt-8" style={{ '--d': '200ms' }}>
            Season warnamu dibaca dari wajah, kulit, dan undertone pergelangan tangan. Hasilnya personal dan langsung bisa dipakai.
          </p>
          <div className="gm-rise flex flex-wrap items-center gap-4 mt-10" style={{ '--d': '320ms' }}>
            <Link to="/scan-wajah" className="gm-btn">
              Mulai analisis <FiArrowRight />
            </Link>
            <Link to="/penjelasan-analisis" className="gm-btn-ghost">
              Pelajari teorinya
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

      {/* ALUR SINGKAT */}
      <Reveal className="mt-20 border-y border-line py-6 flex flex-wrap justify-between gap-x-10 gap-y-3 text-[15px]">
        {['Pindai wajah', 'Cek undertone', 'Palet season', 'Unduh PDF'].map((s, i) => (
          <span key={s} className="flex items-baseline gap-3">
            <span className="gm-index text-[22px]">0{i + 1}</span>{s}
          </span>
        ))}
      </Reveal>

      {/* APA ITU PERSONAL COLOR */}
      <section className="mt-32 grid lg:grid-cols-[1fr_1.4fr] gap-12 lg:gap-20">
        <Reveal>
          <h2 className="gm-display text-[48px] sm:text-[64px]">
            Empat keluarga,<br /><em>dua belas season.</em>
          </h2>
          <p className="gm-lead text-[15px] mt-6 max-w-md">
            Warna personal ditentukan oleh undertone kulit, pigmen mata, warna rambut alami, dan kontras wajah.
            Pernah merasa satu baju membuatmu segar, tapi baju lain membuatmu tampak lelah? Itulah alasannya.
          </p>
        </Reveal>

        <div className="grid sm:grid-cols-2 gap-5">
          {SEASONS.map((s, i) => (
            <Reveal key={s.name} delay={i * 90} className="gm-card gm-card-hover p-7 group">
              <div className="flex gap-1.5 mb-8">
                {s.colors.map((c, j) => (
                  <span
                    key={c}
                    className="w-9 h-9 rounded-full ring-2 ring-paper transition-transform duration-500 group-hover:-translate-y-1"
                    style={{ background: c, transitionDelay: `${j * 50}ms` }}
                  />
                ))}
              </div>
              <h3 className="gm-title text-[34px]">{s.name}</h3>
              <p className="text-[14px] text-accent mt-1">{s.family}</p>
              <p className="text-[14px] text-gray-500 leading-relaxed mt-4">{s.desc}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* MANFAAT */}
      <section className="mt-36">
        <Reveal>
          <h2 className="gm-display text-[48px] sm:text-[64px] max-w-3xl">
            Warna yang harmonis mengubah caramu <em>melihat cermin.</em>
          </h2>
        </Reveal>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-12 mt-16">
          {BENEFITS.map((b, i) => (
            <Reveal key={b.title} delay={i * 90} className="border-t border-line pt-6">
              <span className="block w-3 h-3 rounded-full mb-6" style={{ background: b.color }} />
              <h3 className="gm-title text-[28px]">{b.title}</h3>
              <p className="text-[14px] text-gray-500 leading-relaxed mt-3">{b.desc}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CARA KERJA */}
      <Reveal as="section" className="mt-36 rounded-[36px] bg-ink text-paper px-7 py-14 sm:px-14 sm:py-20 relative overflow-hidden">
        <span className="absolute -right-24 -top-24 w-80 h-80 rounded-full bg-accent/40 blur-[90px] animate-[gm-drift-b_18s_ease-in-out_infinite]" aria-hidden="true" />
        <span className="absolute -left-20 bottom-0 w-72 h-72 rounded-full bg-[#6b46c1]/40 blur-[90px] animate-[gm-drift-a_22s_ease-in-out_infinite]" aria-hidden="true" />
        <h2 className="gm-display text-paper text-[44px] sm:text-[60px] relative">
          Cara GlowMatch <em>membaca warnamu.</em>
        </h2>
        <div className="grid md:grid-cols-3 gap-10 mt-14 relative">
          {STEPS.map((s, i) => (
            <Reveal key={s.title} delay={i * 120} className="border-t border-white/15 pt-6">
              <span className="gm-index text-[44px] text-[#d9b6d4]">0{i + 1}</span>
              <h3 className="gm-title text-paper text-[26px] mt-4">{s.title}</h3>
              <p className="text-[14px] text-[#cdbfdc] leading-relaxed mt-3">{s.desc}</p>
            </Reveal>
          ))}
        </div>
      </Reveal>

      {/* PERSIAPAN */}
      <section className="mt-36 grid lg:grid-cols-[1fr_1.5fr] gap-12">
        <Reveal>
          <h2 className="gm-display text-[48px] sm:text-[60px]">
            Sebelum <em>kamera menyala.</em>
          </h2>
          <Link to="/scan-wajah" className="group mt-8 inline-flex items-center gap-3">
            <span className="gm-orb"><FiArrowUpRight /></span>
            <span className="text-[15px]">Langsung ke kamera</span>
          </Link>
        </Reveal>
        <div className="divide-y divide-line border-y border-line">
          {TIPS.map((t, i) => (
            <Reveal key={t.title} delay={i * 90} className="py-7 grid grid-cols-[56px_1fr] gap-4 group">
              <span className="gm-index text-[34px] transition-colors group-hover:text-accent">0{i + 1}</span>
              <div>
                <h3 className="gm-title text-[26px]">{t.title}</h3>
                <p className="text-[14px] text-gray-500 leading-relaxed mt-2">{t.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="mt-36 max-w-3xl mx-auto">
        <Reveal>
          <h2 className="gm-display text-[48px] sm:text-[60px] text-center">
            Yang sering <em>ditanyakan.</em>
          </h2>
        </Reveal>
        <div className="mt-12 border-t border-line">
          {FAQS.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <Reveal key={faq.q} delay={idx * 60} className="border-b border-line">
                <button
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                  className="w-full text-left py-6 flex items-center justify-between gap-6 text-[17px] sm:text-[19px] hover:text-accent transition-colors"
                >
                  <span>{faq.q}</span>
                  <FiPlus className={`shrink-0 text-xl transition-transform duration-500 ${isOpen ? 'rotate-45 text-accent' : 'text-gray-400'}`} />
                </button>
                <div className={`grid transition-[grid-template-rows,opacity] duration-500 ease-out ${isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
                  <div className="overflow-hidden">
                    <p className="pb-7 pr-10 text-[15px] text-gray-500 leading-relaxed">{faq.a}</p>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <Reveal as="section" className="mt-36 text-center">
        <h2 className="gm-display text-[52px] sm:text-[88px]">
          Siap menemukan<br /><em>warnamu?</em>
        </h2>
        <Link to="/scan-wajah" className="gm-btn mt-10">
          Mulai analisis sekarang <FiArrowRight />
        </Link>
      </Reveal>

    </div>
  );
};

export default Home;
