import { Link } from 'react-router-dom';
import { 
  FiArrowLeft, FiInfo, FiAlertTriangle, FiCheck, FiSun, FiDroplet, 
  FiShield, FiBookOpen, FiLayers, FiHelpCircle, FiCheckCircle 
} from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import { useAnalysis, seasonOptions } from '../context/AnalysisContext';

const UNDERTONE_LABEL = { warm: 'Warm (Hangat)', cool: 'Cool (Dingin)', neutral: 'Neutral (Netral)' };

export default function AnalysisExplanation() {
  const { result, selectedId } = useAnalysis();
  const options = seasonOptions(result);
  const selected = options.find((o) => o.id === selectedId) ?? options[0];

  const gate = result?.result?.gate;
  const season = result?.result?.season;

  return (
    <div className="py-10 max-w-4xl mx-auto space-y-12">
      
      {/* Tombol Navigasi Kembali */}
      <div>
        <Link
          to="/hasil"
          className="inline-flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-glowmatch-primary transition-colors"
        >
          <FiArrowLeft className="text-lg" /> Kembali ke Halaman Hasil
        </Link>
      </div>

      {/* Header Halaman */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 bg-purple-50 text-glowmatch-primary px-3.5 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase border border-purple-100">
          <FiBookOpen /> Panduan Lengkap & Catatan Analisis
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-glowmatch-secondary tracking-tight">
          Penjelasan Lanjutan Teori Warna & Catatan Sistem
        </h1>
        <p className="text-gray-500 text-sm sm:text-base leading-relaxed">
          Pahami bagaimana kombinasi rona dasar kulit (undertone) dan fitur wajahmu menentukan 12 musim warna secara presisi.
        </p>
      </div>

      {/* SECTION 1: KELUARGA WARM VS COOL */}
      <section className="bg-white rounded-3xl p-8 sm:p-10 border border-gray-100 shadow-[0_4px_30px_rgb(0,0,0,0.02)] space-y-8">
        <div>
          <span className="text-xs font-bold text-glowmatch-primary uppercase tracking-wider block mb-1">
            Dasar Pembagian Suhu Warna
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-glowmatch-secondary mb-3">
            Mengapa Ada Keluarga Warm dan Cool?
          </h2>
          <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
            Dalam teori warna personal, setiap manusia memiliki rona dasar kulit (undertone) yang ditentukan oleh kadar hemoglobin (merah kebiruan) dan karoten/melanin (kuning keemasan) di bawah lapisan epidermis kulit.
          </p>
        </div>

        {/* Perbandingan Warm vs Cool */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Card Warm */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50/70 border border-amber-200/60 p-6 rounded-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-400 text-white flex items-center justify-center text-xl shadow-sm">
                <FiSun />
              </div>
              <div>
                <h3 className="font-bold text-glowmatch-secondary text-lg">Keluarga Warm (Hangat)</h3>
                <span className="text-xs text-amber-700 font-semibold">Rona dasar keemasan, persik, & kuning</span>
              </div>
            </div>

            <p className="text-xs text-gray-600 leading-relaxed">
              Orang dengan undertone warm tampak paling memukau saat mengenakan warna-warna dengan pigmen kuning atau oranye. Rona kulit mereka akan terlihat bercahaya dan sehat.
            </p>

            <div className="bg-white/80 p-4 rounded-xl border border-amber-100 text-xs space-y-1.5">
              <strong className="text-amber-900 block font-bold">Mengunci ke 2 Musim:</strong>
              <p className="text-gray-600">• <strong>Spring (Musim Semi):</strong> Karakter cerah, jernih, dan ringan.</p>
              <p className="text-gray-600">• <strong>Autumn (Musim Gugur):</strong> Karakter hangat, pekat, dan membumi (earthy).</p>
            </div>
          </div>

          {/* Card Cool */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50/70 border border-blue-200/60 p-6 rounded-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500 text-white flex items-center justify-center text-xl shadow-sm">
                <FiDroplet />
              </div>
              <div>
                <h3 className="font-bold text-glowmatch-secondary text-lg">Keluarga Cool (Dingin)</h3>
                <span className="text-xs text-blue-700 font-semibold">Rona dasar biru, merah muda, & sejuk</span>
              </div>
            </div>

            <p className="text-xs text-gray-600 leading-relaxed">
              Orang dengan undertone cool tampak paling menawan dengan warna-warna dengan pigmen biru atau ungu. Warna ini menetralisir kemerahan dan menonjolkan kejernihan kulit.
            </p>

            <div className="bg-white/80 p-4 rounded-xl border border-blue-100 text-xs space-y-1.5">
              <strong className="text-blue-900 block font-bold">Mengunci ke 2 Musim:</strong>
              <p className="text-gray-600">• <strong>Summer (Musim Panas):</strong> Karakter sejuk, lembut, dan berdebu (muted).</p>
              <p className="text-gray-600">• <strong>Winter (Musim Dingin):</strong> Karakter kontras tinggi, tegas, dan jernih.</p>
            </div>
          </div>

        </div>

        {/* Penjelasan Neutral */}
        <div className="bg-purple-50/50 border border-purple-100 p-5 rounded-2xl text-xs text-gray-600 space-y-2">
          <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2">
            <HiSparkles className="text-glowmatch-primary" /> Bagaimana dengan Undertone Netral (Neutral)?
          </h4>
          <p className="leading-relaxed">
            Jika undertone Anda netral, kulit Anda memiliki keseimbangan antara pigmen keemasan dan merah muda kebiruan. Anda memiliki kebebasan mengeksplorasi warna dari kedua keluarga, dengan fokus utama pada tingkat kontras (terang vs gelap) dan kejernihan warna (jernih vs redup).
          </p>
        </div>
      </section>

      {/* SECTION 2: SISTEM GATEKEEPER GLOWMATCH */}
      <section className="bg-white rounded-3xl p-8 sm:p-10 border border-gray-100 shadow-[0_4px_30px_rgb(0,0,0,0.02)] space-y-6">
        <div>
          <span className="text-xs font-bold text-glowmatch-primary uppercase tracking-wider block mb-1">
            Mekanisme Kecerdasan Buatan
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-glowmatch-secondary mb-3">
            Sistem Gatekeeper GlowMatch
          </h2>
          <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
            Mengapa model kami menggunakan foto pergelangan tangan selain wajah? Ini adalah inovasi penting yang membedakan GlowMatch dari aplikasi biasa.
          </p>
        </div>

        <div className="space-y-4 text-xs sm:text-sm text-gray-600 leading-relaxed">
          <div className="flex gap-4 items-start p-4 bg-gray-50 rounded-2xl border border-gray-100">
            <div className="w-8 h-8 rounded-lg bg-purple-100 text-glowmatch-primary flex items-center justify-center shrink-0 font-bold">
              1
            </div>
            <div>
              <strong className="text-glowmatch-secondary block font-bold mb-1">Menghindari Bias Kemerahan Wajah Sementara</strong>
              Wajah manusia sering mengalami sunburn (terbakar sinar matahari), kemerahan akibat jerawat, rosacea, atau cuaca panas. Jika AI hanya melihat wajah, seseorang yang sebenarnya memiliki undertone Warm bisa salah diklasifikasikan sebagai Cool karena warna merah di permukaan pipi.
            </div>
          </div>

          <div className="flex gap-4 items-start p-4 bg-gray-50 rounded-2xl border border-gray-100">
            <div className="w-8 h-8 rounded-lg bg-purple-100 text-glowmatch-primary flex items-center justify-center shrink-0 font-bold">
              2
            </div>
            <div>
              <strong className="text-glowmatch-secondary block font-bold mb-1">Penguncian Keluarga Musim (Rule-based Gatekeeper)</strong>
              Ketika pergelangan tangan terdeteksi <strong>Warm</strong>, Gatekeeper secara ketat membatasi hasil akhir hanya pada keluarga <strong>Spring & Autumn</strong>. Begitu pula jika <strong>Cool</strong>, hasil dikunci ke <strong>Summer & Winter</strong>.
            </div>
          </div>

          <div className="flex gap-4 items-start p-4 bg-gray-50 rounded-2xl border border-gray-100">
            <div className="w-8 h-8 rounded-lg bg-purple-100 text-glowmatch-primary flex items-center justify-center shrink-0 font-bold">
              3
            </div>
            <div>
              <strong className="text-glowmatch-secondary block font-bold mb-1">Fitur Wajah Menentukan Subtipe & Musim Spesifik</strong>
              Setelah keluarga musim terkunci oleh pergelangan tangan, model AI wajah (DINOv3 + SegFormer) menganalisis warna mata, bibir, rambut, dan kontras untuk memilih musim paling ideal di antara varian yang ada.
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: CATATAN TEKNIS & PERINGATAN ANALISIS PENGGUNA */}
      {result && gate && (
        <section className="bg-white rounded-3xl p-8 sm:p-10 border border-gray-100 shadow-[0_4px_30px_rgb(0,0,0,0.02)] space-y-6">
          <div>
            <span className="text-xs font-bold text-glowmatch-primary uppercase tracking-wider block mb-1">
              Status Khusus Sesi Anda
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-glowmatch-secondary mb-3">
              Catatan Diagnostik Hasil Analisis Anda
            </h2>
            <p className="text-gray-500 text-xs sm:text-sm">
              Berikut adalah transparansi hasil pembacaan sensor dan model AI untuk foto yang baru saja Anda ambil:
            </p>
          </div>

          <div className="space-y-4">
            {/* Status Gatekeeper */}
            <div className="border border-purple-100 bg-purple-50/50 rounded-2xl p-5 flex items-start gap-3.5">
              <FiInfo className="text-glowmatch-primary text-xl shrink-0 mt-0.5" />
              <div className="space-y-1 text-xs sm:text-sm">
                <strong className="text-glowmatch-secondary font-bold block">Status Penguncian Undertone</strong>
                <p className="text-gray-600 leading-relaxed">
                  Undertone Anda terdeteksi <strong>{UNDERTONE_LABEL[gate.undertone] || gate.undertone}</strong>.
                  {gate.applied ? (
                    ` Hasil ini mengunci palet Anda ke keluarga musim ${gate.allowed_families.join(' / ')}.`
                  ) : (
                    ` Hasil mengikuti kecenderungan alami fitur wajah (${UNDERTONE_LABEL[gate.lean] || gate.lean}).`
                  )}
                </p>
              </div>
            </div>

            {/* Jika Ada Peringatan Konflik atau Konfirmasi */}
            {gate.conflict && (
              <div className="border border-amber-200 bg-amber-50/80 rounded-2xl p-5 flex items-start gap-3.5">
                <FiAlertTriangle className="text-amber-600 text-xl shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs sm:text-sm">
                  <strong className="text-amber-900 font-bold block">Catatan Pencahayaan: Potensi Konflik Wajah & Tangan</strong>
                  <p className="text-amber-800 leading-relaxed">
                    Sistem mendeteksi sedikit perbedaan rona temperatur antara foto pergelangan tangan dan wajah. Hal ini umumnya disebabkan oleh sudut pantulan lampu ruangan atau bayangan ponsel. Anda dapat mencoba analisis ulang dengan pencahayaan alami di dekat jendela untuk hasil yang semakin presisi.
                  </p>
                </div>
              </div>
            )}

            {season?.confidence_status === 'perlu_konfirmasi' && !gate.conflict && (
              <div className="border border-amber-200 bg-amber-50/80 rounded-2xl p-5 flex items-start gap-3.5">
                <FiAlertTriangle className="text-amber-600 text-xl shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs sm:text-sm">
                  <strong className="text-amber-900 font-bold block">Eksplorasi Musim Tetangga</strong>
                  <p className="text-amber-800 leading-relaxed">
                    Fitur wajah Anda memiliki karakteristik yang sangat fleksibel mendekati musim tetangga. Kami menyarankan untuk memanfaatkan fitur <strong>"Coba Live"</strong> di halaman hasil untuk membandingkan palet musim tetangga Anda di layar secara langsung.
                  </p>
                </div>
              </div>
            )}

            {/* Info Validasi Mandiri (Draping Kain) */}
            <div className="border border-emerald-100 bg-emerald-50/50 rounded-2xl p-5 flex items-start gap-3.5">
              <FiCheckCircle className="text-emerald-600 text-xl shrink-0 mt-0.5" />
              <div className="space-y-1 text-xs sm:text-sm">
                <strong className="text-emerald-950 font-bold block">Tips Validasi Mandiri di Rumah (Fabric Draping)</strong>
                <p className="text-emerald-900 leading-relaxed">
                  Ambil kain atau baju berwarna emas kuning dan perak (atau oranye dan fuchsia). Dekatkan ke bawah dagu di depan cermin saat pagi hari. Warna yang membuat kantung mata memudar dan bibir terlihat lebih segar adalah konfirmasi nyata dari keluarga warnamu!
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Tombol Aksi Bawah */}
      <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <Link
          to="/hasil"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-glowmatch-primary hover:bg-purple-800 text-white px-8 py-4 rounded-xl font-bold transition shadow-md"
        >
          <FiArrowLeft /> Kembali ke Palet Hasil Analisis
        </Link>
        <Link
          to="/scan-wajah"
          className="text-xs text-gray-500 hover:text-glowmatch-primary font-medium"
        >
          Ingin mencoba pemindaian foto baru? Klik di sini
        </Link>
      </div>

    </div>
  );
}
