import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FiArrowRight, FiCheck, FiCamera, FiSun, FiLayers, FiShield, 
  FiChevronDown, FiBookOpen, FiSmile, FiTrendingUp, FiShoppingBag, FiAward 
} from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import HeroModel from '../assets/hero-model.jpg';

const FAQS = [
  {
    q: 'Apa itu Seasonal Color Analysis (Analisis Warna 12 Musim)?',
    a: 'Seasonal Color Analysis adalah metode pengelompokan warna berdasarkan teori warna alamiah manusia (suhu undertone, kejernihan, dan kedalaman kontras). Sistem ini membagi warna menjadi 12 musim (Spring, Summer, Autumn, Winter beserta variannya) untuk menentukan palet busana dan riasan yang paling menyempurnakan rona kulit alami Anda.',
  },
  {
    q: 'Apakah warna personal saya bisa berubah seiring bertambahnya usia?',
    a: 'Undertone dasar kulit Anda (Warm, Cool, atau Neutral) bersifat genetik dan cenderung permanen sepanjang hidup. Namun, tingkat kontras rambut atau kecerahan kulit bisa mengalami sedikit penyesuaian, yang mungkin menggeser preferensi Anda ke musim tetangga dalam keluarga yang sama.',
  },
  {
    q: 'Mengapa GlowMatch memverifikasi pergelangan tangan selain wajah?',
    a: 'Wajah manusia sering mengalami kemerahan sementara (sunburn, bekas jerawat, rosacea) atau pigmentasi luar yang bisa menipu kamera. Vena dan bagian dalam pergelangan tangan merupakan area paling terlindung yang mencerminkan rona dasar darah dan melanin sejati Anda, sehingga undertone dapat terkunci dengan akurat.',
  },
  {
    q: 'Bagaimana jika ruangan saya kurang terang saat mengambil foto?',
    a: 'Anda dapat memanfaatkan lampu kilat/torch dari HP atau membawa lighting sendiri (seperti ring light atau lampu meja) dengan pencahayaan putih netral merata ke arah wajah, serta algoritma Gray-World White Balance kami yang siap mengoreksi bias temperatur warna.',
  },
  {
    q: 'Apakah hasil analisis warna ini bisa diunduh?',
    a: 'Tentu saja! Anda dapat langsung mengunduh Dokumen Laporan Analisis Warna Lengkap dalam format PDF berkualitas tinggi, yang mencakup identitas profil, palet warna utama, warna netral, serta warna yang sebaiknya dihindari untuk panduan praktis.',
  },
];

const SEASONS_OVERVIEW = [
  {
    name: 'Spring (Musim Semi)',
    family: 'Warm & Clear',
    color: 'from-amber-400 to-rose-400',
    desc: 'Cerah, hangat, dan berenergi. Cocok dengan warna peach, coral cerah, warm turquoise, dan emas kuning berkilau.',
    tags: ['Light Spring', 'True Spring', 'Bright Spring'],
  },
  {
    name: 'Summer (Musim Panas)',
    family: 'Cool & Soft',
    color: 'from-sky-400 to-pink-400',
    desc: 'Sejuk, lembut, dan elegan. Menyatu indah dengan lavender, baby pink, powder blue, soft navy, dan perak.',
    tags: ['Light Summer', 'True Summer', 'Soft Summer'],
  },
  {
    name: 'Autumn (Musim Gugur)',
    family: 'Warm & Muted',
    color: 'from-amber-600 to-orange-700',
    desc: 'Hangat, kaya, dan membumi. Memancarkan aura mewah dengan terracotta, olive, mustard, rust, dan bronze.',
    tags: ['Soft Autumn', 'True Autumn', 'Deep Autumn'],
  },
  {
    name: 'Winter (Musim Dingin)',
    family: 'Cool & Deep / Bright',
    color: 'from-blue-600 to-fuchsia-600',
    desc: 'Kontras tajam, tegas, dan jernih. Sempurna dengan warna permata seperti ruby, sapphire, emerald, true black, dan icy white.',
    tags: ['Bright Winter', 'True Winter', 'Deep Winter'],
  },
];

const Home = () => {
  const [openFaq, setOpenFaq] = useState(null);

  const toggleFaq = (idx) => {
    setOpenFaq((prev) => (prev === idx ? null : idx));
  };

  return (
    <div className="space-y-24 py-8 lg:py-12">
      
      {/* 1. HERO SECTION */}
      <div className="flex flex-col lg:flex-row items-center justify-between gap-12 pt-4">
        
        {/* Kolom Kiri: Teks & CTA */}
        <div className="flex-1 max-w-2xl">
          <div className="inline-flex items-center gap-2 bg-purple-50 text-glowmatch-primary font-bold text-xs tracking-widest uppercase mb-6 px-4 py-2 rounded-full border border-purple-100">
            <HiSparkles className="text-base" />
            Personal Color Analysis AI Terdepan
          </div>
          
          <div className="flex flex-col gap-2 mb-6">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-glowmatch-secondary tracking-tight leading-tight">
              Temukan warna
            </h1>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-glowmatch-secondary tracking-tight leading-tight">
              yang membuatmu
            </h1>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-tight">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 via-purple-500 to-orange-400">
                lebih bercahaya.
              </span>
            </h1>
          </div>
          
          <p className="text-base sm:text-lg text-gray-500 mb-8 leading-relaxed max-w-xl">
            Kenali 12 musim warna terbaikmu melalui analisis AI cerdas—memadukan fitur wajah, rona kulit, dan verifikasi undertone pergelangan tangan untuk hasil personal yang presisi.
          </p>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5 mb-12">
            <Link 
              to="/scan-wajah" 
              className="inline-flex items-center gap-3 bg-glowmatch-primary hover:bg-purple-800 text-white px-8 py-4 rounded-2xl font-semibold transition-all shadow-lg shadow-purple-200 active:scale-95"
            >
              Mulai Analisis Sekarang
              <FiArrowRight className="text-xl" />
            </Link>
            <div className="text-xs text-gray-400 font-medium space-y-0.5">
              <p className="flex items-center gap-1.5 text-gray-600 font-semibold">
                <FiCheck className="text-emerald-500" /> Pengambilan kamera manual
              </p>
              <p>Hanya butuh waktu sekitar 2 menit</p>
            </div>
          </div>

          {/* Indikator Langkah-langkah */}
          <div className="flex flex-wrap items-center gap-3 md:gap-5 text-xs font-semibold text-gray-400">
            <div className="flex items-center gap-2">
              <span className="bg-purple-100 text-glowmatch-primary px-2.5 py-1 rounded-lg">01</span>
              Pindai Wajah
            </div>
            <div className="hidden md:block w-8 h-[2px] bg-gray-200"></div>
            <div className="flex items-center gap-2">
              <span className="bg-purple-100 text-glowmatch-primary px-2.5 py-1 rounded-lg">02</span>
              Cek Undertone
            </div>
            <div className="hidden md:block w-8 h-[2px] bg-gray-200"></div>
            <div className="flex items-center gap-2">
              <span className="bg-purple-100 text-glowmatch-primary px-2.5 py-1 rounded-lg">03</span>
              Dapatkan Palet & PDF
            </div>
          </div>
        </div>

        {/* Kolom Kanan: Gambar Model dengan Frame Oval dan Efek Scanline */}
        <div className="flex-1 flex justify-center w-full lg:justify-end">
          <div className="relative w-full max-w-[380px] aspect-[3/4] rounded-t-full rounded-b-full overflow-hidden shadow-2xl ring-8 ring-purple-50 bg-orange-50 group">
            
            <img 
              src={HeroModel} 
              alt="Model GlowMatch" 
              className="w-full h-full object-cover scale-95 object-top transition-transform duration-700 group-hover:scale-100"
            />

            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute w-full h-1 bg-glowmatch-primary opacity-50 blur-[1px] animate-[scan_3s_ease-in-out_infinite]" />
              <div className="absolute w-full h-16 bg-gradient-to-b from-glowmatch-primary/0 via-glowmatch-primary/20 to-glowmatch-primary/0 animate-[scan_3s_ease-in-out_infinite] -translate-y-8" />
            </div>

            <div className="absolute bottom-6 left-6 right-6 bg-white/90 backdrop-blur-md p-4 rounded-2xl shadow-lg border border-white/50 text-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-glowmatch-secondary">12 Seasonal Palette</span>
                <span className="text-[10px] bg-purple-100 text-glowmatch-primary font-bold px-2 py-0.5 rounded-full">AI Match</span>
              </div>
              <p className="text-gray-500 text-[11px]">Harmoni warna yang mempertegas keanggunan alaminya.</p>
            </div>

          </div>
        </div>

      </div>

      {/* 2. PENJELASAN: APA ITU PERSONAL COLOR ANALYSIS? */}
      <section className="bg-white rounded-3xl p-8 sm:p-12 border border-gray-100 shadow-[0_4px_30px_rgb(0,0,0,0.02)] space-y-8">
        <div className="max-w-3xl">
          <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-2">Konsep & Teori Dasar</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-glowmatch-secondary mb-4">
            Apa Itu Personal Color Analysis?
          </h2>
          <p className="text-gray-600 leading-relaxed text-sm sm:text-base">
            Pernahkah Anda mengenakan pakaian tertentu dan tiba-tiba orang mengatakan Anda terlihat segar bersinar, namun di pakaian lain wajah Anda tampak lelah atau kusam? Itulah keajaiban <strong>Personal Color</strong>.
          </p>
          <p className="text-gray-600 leading-relaxed text-sm sm:text-base mt-3">
            Warna personal ditentukan oleh interaksi antara rona dasar kulit (undertone), pigmen mata, warna rambut alami, dan tingkat kontras wajah. Sistem <strong>12 Seasonal Color</strong> mengelompokkannya menjadi 4 keluarga besar musim yang disempurnakan:
          </p>
        </div>

        {/* Grid 4 Keluarga Musim */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pt-2">
          {SEASONS_OVERVIEW.map((season) => (
            <div key={season.name} className="bg-gray-50/70 border border-gray-100 rounded-2xl p-6 space-y-4 hover:shadow-md transition">
              <div className={`w-12 h-2.5 rounded-full bg-gradient-to-r ${season.color}`} />
              <div>
                <h3 className="font-bold text-glowmatch-secondary text-base">{season.name}</h3>
                <span className="text-xs font-semibold text-glowmatch-primary">{season.family}</span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{season.desc}</p>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {season.tags.map((tag) => (
                  <span key={tag} className="text-[10px] bg-white border border-gray-200 text-gray-600 px-2.5 py-1 rounded-md font-medium">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. MANFAAT MENGETAHUI WARNA PERSONAL */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto">
          <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-2">Nilai Tambah</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-glowmatch-secondary mb-4">
            Mengapa Mengetahui Warnamu Begitu Berharga?
          </h2>
          <p className="text-gray-500 text-sm">
            Warna bukan sekadar tren sesaat—warna yang harmonis mengubah caramu melihat dirimu di cermin.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-7 rounded-3xl border border-gray-100 shadow-sm space-y-3">
            <div className="w-12 h-12 bg-rose-50 text-rose-500 rounded-2xl flex items-center justify-center text-xl">
              <FiSmile />
            </div>
            <h3 className="font-bold text-glowmatch-secondary text-lg">Wajah Tampak Cerah Alami</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Warna yang tepat merefleksikan cahaya positif ke wajah, menyamarkan lingkaran hitam mata dan membuat kulit tampak glowing alami.
            </p>
          </div>

          <div className="bg-white p-7 rounded-3xl border border-gray-100 shadow-sm space-y-3">
            <div className="w-12 h-12 bg-amber-50 text-amber-500 rounded-2xl flex items-center justify-center text-xl">
              <FiShoppingBag />
            </div>
            <h3 className="font-bold text-glowmatch-secondary text-lg">Belanja Hemat & Tepat Sasaran</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Hindari membeli pakaian, jilbab, atau lipstik mahal yang akhirnya mengendap di lemari karena warnanya membuat wajah terlihat pucat.
            </p>
          </div>

          <div className="bg-white p-7 rounded-3xl border border-gray-100 shadow-sm space-y-3">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-500 rounded-2xl flex items-center justify-center text-xl">
              <FiLayers />
            </div>
            <h3 className="font-bold text-glowmatch-secondary text-lg">Mix & Match Lebih Praktis</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Membangun capsule wardrobe menjadi sangat mudah karena seluruh palet warna utama dan netralmu saling menyatu tanpa tabrakan warna.
            </p>
          </div>

          <div className="bg-white p-7 rounded-3xl border border-gray-100 shadow-sm space-y-3">
            <div className="w-12 h-12 bg-emerald-50 text-emerald-500 rounded-2xl flex items-center justify-center text-xl">
              <FiAward />
            </div>
            <h3 className="font-bold text-glowmatch-secondary text-lg">Pancaran Percaya Diri</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Tampil memukau dan berkesan profesional dalam setiap momentum penting: presentasi kerja, wawancara, kencan, hingga foto formal.
            </p>
          </div>
        </div>
      </section>

      {/* 4. CARA KERJA GLOWMATCH AI */}
      <section className="bg-gradient-to-br from-purple-900 to-indigo-950 text-white rounded-3xl p-8 sm:p-14 shadow-xl space-y-10">
        <div className="max-w-2xl">
          <p className="text-amber-300 text-xs font-bold tracking-widest uppercase mb-2">Teknologi Mutakhir</p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Bagaimana GlowMatch AI Bekerja?
          </h2>
          <p className="text-purple-200 text-sm sm:text-base leading-relaxed">
            Tidak seperti filter sederhana, GlowMatch mengombinasikan computer vision dan deep learning ensemble untuk hasil analisis objektif.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white/10 backdrop-blur-md border border-white/10 p-6 rounded-2xl space-y-3">
            <span className="text-xs font-bold text-amber-300 uppercase tracking-wider block">Langkah 01</span>
            <h3 className="text-lg font-bold text-white">Deteksi Wajah & White Balance</h3>
            <p className="text-xs text-purple-200 leading-relaxed">
              Algoritma YuNet memetakan kontur wajah, sementara filter Gray-World menetralkan bias temperatur lampu ruangan agar warna kulit terbebas dari distorsi.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md border border-white/10 p-6 rounded-2xl space-y-3">
            <span className="text-xs font-bold text-amber-300 uppercase tracking-wider block">Langkah 02</span>
            <h3 className="text-lg font-bold text-white">Verifikasi Undertone Ganda</h3>
            <p className="text-xs text-purple-200 leading-relaxed">
              Sistem Gatekeeper menganalisis pergelangan tangan untuk mengonfirmasi rona darah dasar (Warm/Cool/Neutral), mengunci musim agar tidak tertipu kemerahan kulit sesaat.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md border border-white/10 p-6 rounded-2xl space-y-3">
            <span className="text-xs font-bold text-amber-300 uppercase tracking-wider block">Langkah 03</span>
            <h3 className="text-lg font-bold text-white">Ensemble 12-Musim & Swatch</h3>
            <p className="text-xs text-purple-200 leading-relaxed">
              Kombinasi model klasifikasi menghasilkan musim terbaik, pilihan musim tetangga untuk visual try-on secara langsung, serta rekomendasi busana yang dapat diunduh ke PDF.
            </p>
          </div>
        </div>
      </section>

      {/* 5. PANDUAN PERSIAPAN SEBELUM ANALISIS */}
      <section className="bg-white rounded-3xl p-8 sm:p-12 border border-gray-100 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-1">Tips Akurasi Maksimal</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-glowmatch-secondary">
              Persiapan Sebelum Memulai Kamera
            </h2>
          </div>
          <Link to="/scan-wajah" className="text-sm font-semibold text-glowmatch-primary hover:underline flex items-center gap-1.5 self-start md:self-auto">
            Langsung ke Kamera <FiArrowRight />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div className="flex gap-4 items-start p-4 bg-purple-50/50 rounded-2xl border border-purple-100/50">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-glowmatch-primary flex items-center justify-center shrink-0 text-lg">
              <FiSun />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-sm text-glowmatch-secondary">Pencahayaan Cukup</h4>
              <p className="text-xs text-gray-500 leading-relaxed">
                Gunakan pencahayaan alami dekat jendela, bawa lighting sendiri (ring light), atau gunakan lampu HP agar wajah terang merata tanpa bayangan gelap.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start p-4 bg-purple-50/50 rounded-2xl border border-purple-100/50">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-glowmatch-primary flex items-center justify-center shrink-0 text-lg">
              <FiSmile />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-sm text-glowmatch-secondary">Wajah Bersih Alami</h4>
              <p className="text-xs text-gray-500 leading-relaxed">
                Sebaiknya tanpa foundation tebal agar warna asli pigmen kulit terlihat jelas oleh model kecerdasan buatan.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start p-4 bg-purple-50/50 rounded-2xl border border-purple-100/50">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-glowmatch-primary flex items-center justify-center shrink-0 text-lg">
              <FiCamera />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-sm text-glowmatch-secondary">Lepaskan Kacamata</h4>
              <p className="text-xs text-gray-500 leading-relaxed">
                Buka kacamata dan rapikan rambut dari area dahi agar sistem dapat membaca kontur dan proporsi wajah secara utuh.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. FAQ INTERAKTIF */}
      <section className="max-w-3xl mx-auto space-y-6">
        <div className="text-center">
          <p className="text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-2">Tanya & Jawab</p>
          <h2 className="text-3xl font-bold text-glowmatch-secondary">Pertanyaan yang Sering Diajukan</h2>
        </div>

        <div className="space-y-3 pt-4">
          {FAQS.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div 
                key={idx} 
                className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm transition"
              >
                <button
                  type="button"
                  onClick={() => toggleFaq(idx)}
                  className="w-full text-left px-6 py-5 flex items-center justify-between gap-4 font-semibold text-glowmatch-secondary text-sm hover:text-glowmatch-primary transition"
                >
                  <span>{faq.q}</span>
                  <FiChevronDown className={`text-base shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180 text-glowmatch-primary' : 'text-gray-400'}`} />
                </button>
                {isOpen && (
                  <div className="px-6 pb-5 pt-1 text-xs text-gray-500 leading-relaxed border-t border-gray-50">
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 7. BOTTOM BANNER CTA */}
      <section className="bg-gradient-to-r from-purple-700 via-indigo-600 to-purple-800 text-white rounded-3xl p-10 sm:p-14 text-center space-y-6 shadow-xl">
        <div className="max-w-xl mx-auto space-y-3">
          <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center mx-auto text-2xl text-amber-300">
            <HiSparkles />
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Siap Menemukan Warna Personalmu?
          </h2>
          <p className="text-purple-100 text-sm leading-relaxed">
            Mulailah perjalanan gaya baru Anda hari ini. Ambil foto secara manual dengan kontrol penuh dan temukan palet yang memancarkan pesona terbaik Anda.
          </p>
        </div>

        <div className="pt-2">
          <Link
            to="/scan-wajah"
            className="inline-flex items-center gap-2.5 bg-white text-glowmatch-primary hover:bg-purple-50 px-8 py-4 rounded-xl font-bold transition shadow-lg text-sm sm:text-base active:scale-95"
          >
            Mulai Analisis Sekarang <FiArrowRight className="text-lg" />
          </Link>
        </div>
      </section>

    </div>
  );
};

export default Home;