import { Link } from 'react-router-dom';
import { FiArrowLeft, FiArrowRight } from 'react-icons/fi';
import Reveal from '../components/Reveal';
import { useAnalysis } from '../context/AnalysisContext';

const UNDERTONE_LABEL = { warm: 'hangat (warm)', cool: 'dingin (cool)', neutral: 'netral (neutral)' };

const FAMILIES = [
  {
    name: 'Warm',
    accent: 'hangat.',
    colors: ['#f7b267', '#f69179', '#d4a24c', '#c0663f'],
    desc: 'Rona dasar keemasan, persik, dan kuning. Kulit tampak paling hidup dengan warna berpigmen kuning atau oranye.',
    seasons: [['Spring', 'cerah, jernih, ringan'], ['Autumn', 'hangat, pekat, membumi']],
  },
  {
    name: 'Cool',
    accent: 'dingin.',
    colors: ['#96a8e0', '#c3aed6', '#e6b8cf', '#1f3a93'],
    desc: 'Rona dasar biru dan merah muda. Warna berpigmen biru atau ungu menetralkan kemerahan dan menonjolkan kejernihan kulit.',
    seasons: [['Summer', 'sejuk, lembut, redup'], ['Winter', 'kontras, tegas, jernih']],
  },
];

const GATEKEEPER = [
  {
    title: 'Menghindari bias kemerahan wajah',
    desc: 'Sunburn, jerawat, rosacea, atau cuaca panas bisa membuat undertone Warm terbaca sebagai Cool bila AI hanya melihat wajah.',
  },
  {
    title: 'Mengunci keluarga season',
    desc: 'Pergelangan Warm membatasi hasil ke Spring & Autumn. Pergelangan Cool membatasinya ke Summer & Winter.',
  },
  {
    title: 'Wajah menentukan season spesifik',
    desc: 'Setelah keluarga terkunci, model wajah (DINOv3 + SegFormer) membaca mata, bibir, rambut, dan kontras untuk memilih season yang paling pas.',
  },
];

export default function AnalysisExplanation() {
  const { result } = useAnalysis();
  const gate = result?.result?.gate;
  const season = result?.result?.season;

  return (
    <div className="pt-8 pb-4 max-w-5xl mx-auto">

      <Link to="/hasil" className="gm-link gm-rise text-[14px] text-gray-500">
        <FiArrowLeft /> Kembali ke hasil
      </Link>

      <h1 className="gm-display gm-rise text-[56px] sm:text-[88px] mt-8 max-w-4xl" style={{ '--d': '80ms' }}>
        Di balik <em>season warnamu.</em>
      </h1>
      <p className="gm-lead gm-rise text-[16px] sm:text-[17px] max-w-xl mt-8" style={{ '--d': '180ms' }}>
        Undertone kulit ditentukan oleh hemoglobin (merah kebiruan) dan karoten serta melanin (kuning keemasan) di bawah lapisan kulit.
        Kombinasinya dengan fitur wajah menentukan satu dari dua belas season.
      </p>

      {/* WARM VS COOL */}
      <section className="mt-28 grid md:grid-cols-2 gap-5">
        {FAMILIES.map((f, i) => (
          <Reveal key={f.name} delay={i * 120} className="gm-card gm-card-hover p-8 sm:p-10 group">
            <div className="flex -space-x-2 mb-10">
              {f.colors.map((c, j) => (
                <span
                  key={c}
                  className="w-11 h-11 rounded-full ring-[3px] ring-paper transition-transform duration-500 group-hover:-translate-y-1.5"
                  style={{ background: c, transitionDelay: `${j * 60}ms` }}
                />
              ))}
            </div>
            <h2 className="gm-display text-[48px]">
              {f.name}, <em>{f.accent}</em>
            </h2>
            <p className="text-[15px] text-gray-500 leading-relaxed mt-5">{f.desc}</p>
            <dl className="mt-8 border-t border-line divide-y divide-line">
              {f.seasons.map(([name, trait]) => (
                <div key={name} className="flex items-baseline justify-between gap-4 py-4">
                  <dt className="font-serif text-[26px]">{name}</dt>
                  <dd className="text-[14px] text-gray-500 text-right">{trait}</dd>
                </div>
              ))}
            </dl>
          </Reveal>
        ))}
      </section>

      <Reveal className="mt-5 rounded-[28px] border border-dashed border-[#d6c6d6] p-8 sm:p-10">
        <h2 className="gm-title text-[32px]">Bagaimana dengan undertone netral?</h2>
        <p className="text-[15px] text-gray-500 leading-relaxed mt-4 max-w-3xl">
          Kulit netral menyeimbangkan pigmen keemasan dan merah muda kebiruan. Kamu bebas menjelajah kedua keluarga,
          dengan fokus pada tingkat kontras (terang atau gelap) dan kejernihan warna (jernih atau redup).
        </p>
      </Reveal>

      {/* GATEKEEPER */}
      <section className="mt-32 grid lg:grid-cols-[1fr_1.4fr] gap-12">
        <Reveal>
          <h2 className="gm-display text-[48px] sm:text-[60px]">
            Kenapa <em>pergelangan tangan?</em>
          </h2>
        </Reveal>
        <div className="border-t border-line">
          {GATEKEEPER.map((g, i) => (
            <Reveal key={g.title} delay={i * 100} className="border-b border-line py-8 grid grid-cols-[56px_1fr] gap-4 group">
              <span className="gm-index text-[38px] transition-colors group-hover:text-accent">0{i + 1}</span>
              <div>
                <h3 className="gm-title text-[28px]">{g.title}</h3>
                <p className="text-[15px] text-gray-500 leading-relaxed mt-3">{g.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CATATAN SESI */}
      {result && gate && (
        <Reveal as="section" className="mt-32 rounded-[36px] bg-ink text-paper px-7 py-12 sm:px-12 sm:py-14 relative overflow-hidden">
          <span className="absolute -left-24 -bottom-28 w-80 h-80 rounded-full bg-[#6b46c1]/45 blur-[90px] animate-[gm-drift-a_20s_ease-in-out_infinite]" aria-hidden="true" />
          <h2 className="gm-display text-paper text-[44px] sm:text-[56px] relative">
            Catatan untuk <em>hasilmu.</em>
          </h2>

          <div className="relative mt-10 grid md:grid-cols-2 gap-x-10 gap-y-8">
            <div className="border-t border-white/15 pt-6">
              <h3 className="font-serif text-[26px]">Undertone</h3>
              <p className="text-[15px] text-[#cdbfdc] leading-relaxed mt-3">
                Terdeteksi {UNDERTONE_LABEL[gate.undertone] || gate.undertone}.
                {gate.applied
                  ? ` Palet dikunci ke keluarga ${gate.allowed_families.join(' / ')}.`
                  : ` Hasil mengikuti kecenderungan fitur wajah (${UNDERTONE_LABEL[gate.lean] || gate.lean}).`}
              </p>
            </div>

            {gate.conflict && (
              <div className="border-t border-coral/50 pt-6">
                <h3 className="font-serif text-[26px] text-[#f5c2b4]">Wajah dan tangan berbeda</h3>
                <p className="text-[15px] text-[#cdbfdc] leading-relaxed mt-3">
                  Rona wajah dan pergelangan sedikit berbeda, biasanya karena pantulan lampu atau bayangan ponsel.
                  Coba ulangi di dekat jendela untuk hasil yang lebih presisi.
                </p>
              </div>
            )}

            {season?.confidence_status === 'perlu_konfirmasi' && !gate.conflict && (
              <div className="border-t border-coral/50 pt-6">
                <h3 className="font-serif text-[26px] text-[#f5c2b4]">Coba season terdekat</h3>
                <p className="text-[15px] text-[#cdbfdc] leading-relaxed mt-3">
                  Fitur wajahmu cukup fleksibel. Pakai &ldquo;Coba live&rdquo; di halaman hasil untuk membandingkan palet season terdekat langsung di wajahmu.
                </p>
              </div>
            )}

            <div className="border-t border-white/15 pt-6">
              <h3 className="font-serif text-[26px]">Uji sendiri di cermin</h3>
              <p className="text-[15px] text-[#cdbfdc] leading-relaxed mt-3">
                Dekatkan kain emas dan perak (atau oranye dan fuchsia) ke bawah dagu di pagi hari.
                Warna yang membuat kantung mata memudar dan bibir tampak segar adalah keluargamu.
              </p>
            </div>
          </div>
        </Reveal>
      )}

      <Reveal className="mt-20 flex flex-wrap items-center justify-between gap-6 border-t border-line pt-10">
        <Link to="/hasil" className="gm-btn">
          <FiArrowLeft /> Kembali ke palet
        </Link>
        <Link to="/scan-wajah" className="gm-link text-[15px]">
          Pindai foto baru <FiArrowRight />
        </Link>
      </Reveal>
    </div>
  );
}
