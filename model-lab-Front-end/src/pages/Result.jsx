import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FiBookmark, FiDownload, FiArrowRight, FiXCircle, FiCircle, 
  FiVideo, FiImage, FiRefreshCw, FiCheck, FiBookOpen, FiUser
} from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import ColorSwatch from '../components/ColorSwatch';
import LiveTryOn from '../components/LiveTryOn';
import RadialBurst, { FrameOverlay } from '../components/RadialBurst';
import SeasonSwitcher from '../components/SeasonSwitcher';
import { saveToHistory, seasonOptions, useAnalysis } from '../context/AnalysisContext';
import { downloadColorReportPdf } from '../lib/exportPdf';

const UNDERTONE_LABEL = { warm: 'Warm (Hangat)', cool: 'Cool (Dingin)', neutral: 'Neutral (Netral)' };
const SOURCE_LABEL = {
  wrist_model: 'pemindaian pergelangan tangan',
  season_model: 'estimasi fitur wajah',
};

function PaletteSection({ title, link, colors }) {
  return (
    <div>
      <div className="flex justify-between items-end mb-4 border-b border-gray-100 pb-3">
        <h4 className="font-medium text-slate-700">{title}</h4>
        <Link to={link} className="text-sm font-medium text-glowmatch-primary flex items-center gap-1 hover:underline">
          Lihat semua <FiArrowRight />
        </Link>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-4">
        {colors.slice(0, 7).map((c) => <ColorSwatch key={c.hex} name={c.name} hex={c.hex} />)}
      </div>
    </div>
  );
}

const Result = () => {
  const { result, face, selectedId, setSelectedId, reset, profile } = useAnalysis();
  const [mode, setMode] = useState('foto'); // foto | live
  const [savedId, setSavedId] = useState(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const navigate = useNavigate();

  if (!result) {
    return (
      <div className="py-24 max-w-md mx-auto text-center space-y-4">
        <HiSparkles className="text-4xl text-glowmatch-primary mx-auto" />
        <h1 className="text-2xl font-semibold text-glowmatch-secondary">Belum ada hasil analisis</h1>
        <p className="text-gray-500 text-sm">Pindai wajah dan pergelanganmu untuk menemukan musim warnamu.</p>
        <Link to="/scan-wajah" className="inline-block bg-glowmatch-primary text-white px-6 py-3 rounded-xl font-medium">Mulai analisis</Link>
      </div>
    );
  }

  const options = seasonOptions(result);
  const selected = options.find((o) => o.id === selectedId) ?? options[0];
  const { gate } = result.result;
  const { description, keywords, palettes } = selected.palette;
  const faceQ = result.quality.face;
  const saved = savedId === selected.id;
  const undertoneText = `${UNDERTONE_LABEL[gate.undertone]}${result.undertone?.confidence ? ` · ${Math.round(result.undertone.confidence * 100)}%` : ''}`;

  const handleSave = async () => {
    await saveToHistory(result, selected, profile);
    setSavedId(selected.id);
  };

  const handleDownloadPdf = async () => {
    setIsDownloadingPdf(true);
    try {
      await downloadColorReportPdf({
        result,
        selectedSeason: selected,
        profile,
        facePhoto: face?.photo,
      });
    } catch (err) {
      console.error('Gagal mengunduh PDF:', err);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div className="py-8 max-w-5xl mx-auto space-y-10">
      
      {/* 1. Header & Ringkasan Personal */}
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-1">
              <HiSparkles /> Hasil Analisis Personal
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-glowmatch-secondary">
              Harmoni Warnamu Ditemukan
            </h1>
            <p className="text-gray-500 text-sm mt-1">
              {profile?.name ? `Analisis khusus untuk ${profile.name}` : 'Palet yang dirancang untuk menonjolkan keanggunan alami kulitmu.'}
            </p>
          </div>

          <Link
            to="/profil"
            className="inline-flex items-center gap-2 text-xs font-semibold text-gray-500 hover:text-glowmatch-primary self-start sm:self-auto bg-gray-50 border border-gray-200 px-3.5 py-2 rounded-xl"
          >
            <FiUser /> {profile?.name || 'Setel Profil'}
          </Link>
        </div>

        {/* 2 Banner Kartu Utama: Musim Terdeteksi & Undertone */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-[#FFF0E0] border border-orange-200/60 rounded-2xl p-5 flex items-center gap-4 shadow-xs">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-orange-500 shadow-sm shrink-0">
              <HiSparkles className="text-2xl" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
                {selected.id === result.result.season.id ? 'Musim Hasil Analisis' : 'Musim Pilihanmu'}
              </p>
              <h2 className="text-lg font-bold text-glowmatch-secondary">{selected.name}</h2>
              <span className="text-xs text-orange-600 font-medium">{keywords.join(' · ')}</span>
            </div>
          </div>

          <div className="bg-[#E5F5F3] border border-teal-200/60 rounded-2xl p-5 flex items-center gap-4 shadow-xs">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-teal-600 shadow-sm shrink-0">
              <FiCircle className="text-2xl" />
            </div>
            <div>
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
                Undertone ({SOURCE_LABEL[gate.undertone_source] ?? 'terverifikasi'})
              </p>
              <h2 className="text-lg font-bold text-glowmatch-secondary">{undertoneText}</h2>
              <span className="text-xs text-teal-700 font-medium">Rona Dasar Kulit Alami</span>
            </div>
          </div>
        </div>

        {/* Penjelasan Karakteristik Musim */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-xs text-xs sm:text-sm text-gray-600 space-y-2">
          <h3 className="font-bold text-glowmatch-secondary text-base flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-glowmatch-primary" />
            Mengapa Palet {selected.name} Sangat Cocok Untukmu?
          </h3>
          <p className="leading-relaxed">
            {description} Warna-warna dalam palet ini memiliki saturasi dan suhu yang selaras dengan pigmen mata, bibir, serta rona dasar kulitmu, sehingga bayangan lelah pada wajah tersamarkan secara natural tanpa perlu riasan yang tebal.
          </p>
        </div>
      </div>

      {/* 2. Hero: foto + cincin palet / coba live */}
      <div className="bg-gradient-to-br from-[#FFE8DD] to-[#F7E1E8] rounded-3xl flex flex-col md:flex-row overflow-hidden border border-rose-50 shadow-sm">
        <div className="w-full md:w-[48%] p-4 space-y-3">
          <div className="flex bg-white/70 rounded-full p-1 text-xs font-medium w-fit">
            {[['foto', FiImage, 'Fotomu'], ['live', FiVideo, 'Coba live']].map(([m, Icon, label]) => (
              <button key={m} onClick={() => setMode(m)}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full transition ${mode === m ? 'bg-white shadow text-glowmatch-secondary' : 'text-slate-500'}`}>
                <Icon /> {label}
              </button>
            ))}
          </div>
          {mode === 'live' ? (
            <LiveTryOn options={options} selected={selected} onSelect={setSelectedId} />
          ) : (
            <div className="relative w-full aspect-[4/3] rounded-3xl overflow-hidden bg-gray-900">
              {face?.photo && (
                <div className="absolute inset-0" style={{ transform: 'scaleX(-1)' }}>
                  <img src={face.photo} alt="Foto Pengguna" className="absolute inset-0 w-full h-full object-cover" />
                  <FrameOverlay frameSize={faceQ.frame_size}>
                    <RadialBurst box={faceQ.box} colors={palettes.utama} animationKey={selected.id} />
                  </FrameOverlay>
                </div>
              )}
              <p className="absolute bottom-4 left-5 text-white text-sm font-medium tracking-wide drop-shadow">{keywords.join(' · ')}</p>
            </div>
          )}
        </div>

        <div className="w-full md:w-[52%] p-8 md:p-10 flex flex-col justify-center">
          <p className="text-rose-400 text-xs font-bold tracking-widest uppercase mb-4 flex items-center gap-2">
            <HiSparkles /> 12 SEASONAL COLOR HARMONY
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-glowmatch-secondary mb-4">
            Kamu adalah <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-500 to-purple-600">{selected.name}</span>
          </h2>
          <p className="text-slate-500 leading-relaxed mb-8 font-normal text-sm md:text-base">{description}</p>
          <div className="flex flex-wrap gap-2.5">
            {keywords.map((kw) => (
              <span key={kw} className="bg-white border border-orange-100/60 text-slate-600 text-xs font-semibold px-4 py-2 rounded-full shadow-xs">{kw}</span>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Visual swapping musim tetangga */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 shadow-[0_4px_20px_rgb(0,0,0,0.02)] space-y-5">
        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Bandingkan</p>
          <h3 className="text-xl font-bold text-glowmatch-secondary">Musim Tetangga yang Berdekatan</h3>
          <p className="text-sm text-slate-500 mt-1">
            Musim yang berbagi karakter dengan hasilmu. Pilih musim di bawah untuk menukar palet, lalu bandingkan di wajahmu lewat <button onClick={() => setMode('live')} className="text-glowmatch-primary font-bold hover:underline">Coba Live</button>.
          </p>
        </div>
        <SeasonSwitcher options={options} selectedId={selected.id} onSelect={setSelectedId} />
      </div>

      {/* 4. Warna rekomendasi (Utama & Netral) */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 space-y-10 shadow-[0_4px_20px_rgb(0,0,0,0.02)]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-50 text-glowmatch-primary rounded-xl flex items-center justify-center">
            <HiSparkles className="text-2xl" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Palet yang Direkomendasikan</p>
            <h3 className="text-xl font-bold text-glowmatch-secondary">Warna Terbaik Untuk Penampilanmu</h3>
          </div>
        </div>
        <PaletteSection title="Warna Utama (Statement & Accent Colors)" link="/full-palette/utama" colors={palettes.utama} />
        <PaletteSection title="Warna Netral (Wardrobe Foundation & Celana/Blazer)" link="/full-palette/netral" colors={palettes.netral} />
      </div>

      {/* 5. Warna hindari */}
      <div className="bg-white border border-gray-100 rounded-3xl p-8 shadow-[0_4px_20px_rgb(0,0,0,0.02)] space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-red-50 text-red-400 rounded-xl flex items-center justify-center">
            <FiXCircle className="text-2xl" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Panduan Menghindari Tabrakan Warna</p>
            <h3 className="text-xl font-bold text-glowmatch-secondary">Warna yang Sebaiknya Dihindari di Area Wajah</h3>
          </div>
        </div>
        <PaletteSection title={`Kurang cocok untuk ${selected.name}`} link="/full-palette/hindari" colors={palettes.hindari} />
      </div>

      {/* 6. Aksi Simpan & Download PDF */}
      <div className="bg-purple-50/60 border border-purple-100 rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row justify-between items-center gap-6 shadow-sm">
        <div className="text-center md:text-left space-y-1">
          <h4 className="text-lg font-bold text-glowmatch-secondary">Simpan & Unduh Laporan Lengkap</h4>
          <p className="text-xs sm:text-sm text-slate-500 font-normal">
            Unduh laporan format PDF untuk dibawa saat berbelanja baju, jilbab, atau makeup.
          </p>
        </div>
        <div className="flex flex-wrap w-full md:w-auto gap-3">
          <button 
            onClick={() => { reset(); navigate('/scan-wajah'); }}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-white border border-gray-200 text-glowmatch-secondary px-5 py-3.5 rounded-xl font-semibold hover:bg-gray-50 transition shadow-xs text-sm"
          >
            <FiRefreshCw /> Analisis Ulang
          </button>
          
          <button 
            onClick={handleSave} 
            disabled={saved}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-white border border-gray-200 text-glowmatch-secondary px-5 py-3.5 rounded-xl font-semibold hover:bg-gray-50 transition shadow-xs disabled:text-emerald-700 disabled:border-emerald-200 text-sm"
          >
            {saved ? <><FiCheck className="text-emerald-600" /> Tersimpan ke Database</> : <><FiBookmark /> Simpan Hasil</>}
          </button>

          {/* Download PDF Button */}
          <button 
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-glowmatch-primary text-white px-6 py-3.5 rounded-xl font-semibold hover:bg-purple-800 transition shadow-md hover:shadow-lg disabled:opacity-70 text-sm active:scale-95"
          >
            <FiDownload className="text-base" /> 
            {isDownloadingPdf ? 'Membuat PDF...' : 'Unduh Laporan PDF'}
          </button>
        </div>
      </div>

      {/* 8. BAGIAN INGIN LEBIH TAHU PENJELASAN SELANJUTNYA? (DIPINDAHKAN KE PALING BAWAH) */}
      <div className="bg-gradient-to-r from-purple-50 via-indigo-50/60 to-purple-100/70 border border-purple-200/80 rounded-3xl p-8 sm:p-10 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 max-w-xl text-center md:text-left">
          <div className="inline-flex items-center gap-2 text-glowmatch-primary font-bold text-xs uppercase tracking-wider">
            <FiBookOpen className="text-base" /> Penjelasan Lanjutan & Catatan Sistem
          </div>
          <h3 className="text-2xl sm:text-3xl font-bold text-glowmatch-secondary">
            Ingin lebih tahu penjelasan selanjutnya?
          </h3>
          <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
            Pelajari lebih dalam bagaimana undertone keluarga Warm vs Cool mengunci hasil musim warnamu, prinsip sistem Gatekeeper AI, serta catatan validasi diagnostik selengkapnya di halaman khusus.
          </p>
        </div>
        
        <Link
          to="/penjelasan-analisis"
          className="inline-flex items-center gap-2.5 bg-glowmatch-primary hover:bg-purple-800 text-white px-8 py-4 rounded-2xl font-bold transition shadow-md hover:shadow-lg text-sm shrink-0 active:scale-95"
        >
          Masuk ke Halaman Penjelasan <FiArrowRight className="text-lg" />
        </Link>
      </div>

    </div>
  );
};

export default Result;
