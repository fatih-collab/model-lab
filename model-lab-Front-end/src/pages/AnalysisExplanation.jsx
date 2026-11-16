import { Link } from 'react-router-dom';
import { FiArrowLeft, FiArrowRight } from 'react-icons/fi';
import Reveal from '../components/Reveal';
import { useAnalysis } from '../context/AnalysisContext';

const UNDERTONE_LABEL = { warm: 'hangat (warm)', cool: 'dingin (cool)', neutral: 'netral (neutral)' };

const FAMILIES = [
  {
    name: 'Hangat',
    en: 'Warm',
    colors: ['#f7b267', '#f69179', '#d4a24c', '#c0663f'],
    desc: 'Rona dasar keemasan atau persik. Paling hidup dengan warna berpigmen kuning dan oranye.',
    seasons: [['Spring', 'Cerah, jernih, ringan'], ['Autumn', 'Hangat, pekat, membumi']],
  },
  {
    name: 'Dingin',
    en: 'Cool',
    colors: ['#96a8e0', '#c3aed6', '#e6b8cf', '#1f3a93'],
    desc: 'Rona dasar merah muda atau kebiruan. Paling hidup dengan warna berpigmen biru dan ungu.',
    seasons: [['Summer', 'Sejuk, lembut, redup'], ['Winter', 'Kontras, tegas, jernih']],
  },
];

const WRIST_REASONS = [
  { title: 'Wajah bisa menipu', desc: 'Kemerahan karena jerawat, sunburn, atau udara panas bisa membuat kulit hangat terbaca dingin.' },
  { title: 'Mengunci keluarga season', desc: 'Hangat membatasi hasil ke Spring & Autumn, dingin ke Summer & Winter.' },
  { title: 'Wajah memilih season', desc: 'Setelah itu, warna mata, bibir, rambut, dan kontras wajah menentukan season yang paling pas.' },
];

export default function AnalysisExplanation() {
  const { result } = useAnalysis();
  const gate = result?.result?.gate;
  const season = result?.result?.season;

  return (
    <div className="pt-8 pb-4 max-w-5xl mx-auto">

      {/* Satu tautan kembali, hanya bila memang ada hasil untuk dituju. */}
      {result && (
        <Link to="/hasil" className="gm-link gm-rise text-small text-gray-600">
          <FiArrowLeft aria-hidden="true" /> Kembali ke hasil
        </Link>
      )}

      <h1 className="gm-display gm-rise text-display mt-8 max-w-4xl" style={{ '--d': '80ms' }}>
        Di balik <em>season warnamu</em>
      </h1>
      <p className="gm-lead gm-rise text-body-lg max-w-xl mt-6" style={{ '--d': '180ms' }}>
        Undertone kulitmu, dipadukan dengan warna mata, rambut, dan kontras wajah, menentukan satu dari dua belas season.
      </p>

      {/* HANGAT VS DINGIN — subgrid menjaga baris season di kedua kartu tetap sejajar */}
      <section className="mt-20 grid md:grid-cols-2 gap-5">
        {FAMILIES.map((f, i) => (
          <Reveal key={f.name} delay={i * 60} className="gm-card p-8 sm:p-10 grid grid-rows-subgrid row-span-4 gap-0">
            <div className="flex -space-x-2" aria-hidden="true">
              {f.colors.map((c) => (
                <span key={c} className="w-11 h-11 rounded-full ring-[3px] ring-paper" style={{ background: c }} />
              ))}
            </div>
            <h2 className="mt-8 flex items-baseline gap-3">
              <span className="text-title-lg">{f.name}</span>
              <span className="text-small text-gray-600">{f.en}</span>
            </h2>
            <p className="text-body text-gray-600 mt-3">{f.desc}</p>
            <dl className="mt-6 border-t border-line divide-y divide-line">
              {f.seasons.map(([name, trait]) => (
                <div key={name} className="py-4">
                  <dt className="text-title">{name}</dt>
                  <dd className="text-small text-gray-600 mt-0.5">{trait}</dd>
                </div>
              ))}
            </dl>
          </Reveal>
        ))}
      </section>

      <Reveal className="mt-5 rounded-[28px] border border-dashed border-[#d6c6d6] p-8 sm:p-10">
        <h2 className="text-title-lg">Bagaimana dengan undertone netral?</h2>
        <p className="text-body text-gray-600 mt-3 max-w-2xl">
          Kulit netral seimbang di antara keduanya, jadi kamu bisa memakai warna dari dua keluarga. Fokus pada kontras dan kejernihannya.
        </p>
      </Reveal>

      {/* KENAPA PERGELANGAN TANGAN */}
      <section className="mt-32 grid lg:grid-cols-[1fr_1.4fr] gap-10 lg:gap-12">
        <Reveal>
          <h2 className="gm-display text-headline">Kenapa pergelangan tangan?</h2>
        </Reveal>
        <ol className="border-t border-line">
          {WRIST_REASONS.map((g, i) => (
            <li key={g.title} className="border-b border-line py-7 grid grid-cols-[48px_1fr] gap-4">
              <span className="gm-index text-headline" aria-hidden="true">0{i + 1}</span>
              <div>
                <h3 className="text-title">{g.title}</h3>
                <p className="text-body text-gray-600 mt-2">{g.desc}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* CATATAN SESI — hanya bila ada hasil */}
      {result && gate && (
        <Reveal as="section" className="mt-32 rounded-[36px] bg-ink text-paper px-7 py-12 sm:px-12 sm:py-14 relative overflow-hidden">
          <span className="absolute -left-24 -bottom-28 w-80 h-80 rounded-full bg-[#6b46c1]/45 blur-[90px] animate-[gm-drift-a_20s_ease-in-out_infinite]" aria-hidden="true" />
          <h2 className="gm-display text-paper text-headline relative">Catatan untuk hasilmu</h2>

          <div className="relative mt-10 grid md:grid-cols-2 gap-x-10 gap-y-8">
            <div className="border-t border-white/15 pt-6">
              <h3 className="text-title">Undertone</h3>
              <p className="text-body text-[#cdbfdc] mt-2">
                Terdeteksi {UNDERTONE_LABEL[gate.undertone] || gate.undertone}.
                {gate.applied
                  ? ` Palet dikunci ke keluarga ${gate.allowed_families.join(' / ')}.`
                  : ` Hasil mengikuti kecenderungan fitur wajah (${UNDERTONE_LABEL[gate.lean] || gate.lean}).`}
              </p>
            </div>

            {gate.conflict && (
              <div className="border-t border-coral/50 pt-6">
                <h3 className="text-title text-[#f5c2b4]">Wajah dan tangan berbeda</h3>
                <p className="text-body text-[#cdbfdc] mt-2">
                  Biasanya karena pantulan lampu atau bayangan. Ulangi di dekat jendela untuk hasil yang lebih presisi.
                </p>
              </div>
            )}

            {season?.confidence_status === 'perlu_konfirmasi' && !gate.conflict && (
              <div className="border-t border-coral/50 pt-6">
                <h3 className="text-title text-[#f5c2b4]">Coba season terdekat</h3>
                <p className="text-body text-[#cdbfdc] mt-2">
                  Pakai mode Live di halaman hasil untuk membandingkan palet season terdekat di wajahmu.
                </p>
              </div>
            )}

            <div className="border-t border-white/15 pt-6">
              <h3 className="text-title">Uji sendiri di cermin</h3>
              <p className="text-body text-[#cdbfdc] mt-2">
                Dekatkan kain emas dan perak ke bawah dagu. Warna yang membuat wajah tampak segar menunjukkan keluargamu.
              </p>
            </div>
          </div>
        </Reveal>
      )}

      <Reveal className="mt-20 border-t border-line pt-10">
        <Link to="/scan-wajah" className="gm-btn">
          {result ? 'Analisis ulang' : 'Mulai analisis'} <FiArrowRight aria-hidden="true" />
        </Link>
      </Reveal>
    </div>
  );
}
