import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FiBookmark, FiDownload, FiArrowRight, FiArrowUpRight,
  FiVideo, FiImage, FiRefreshCw,
} from 'react-icons/fi';
import { BsBookmarkFill } from 'react-icons/bs';
import Reveal from '../components/Reveal';
import PaletteSection from '../components/PaletteSection';
import LiveTryOn from '../components/LiveTryOn';
import RadialBurst, { FrameOverlay } from '../components/RadialBurst';
import SeasonSwitcher from '../components/SeasonSwitcher';
import { saveToHistory, seasonOptions, useAnalysis } from '../context/AnalysisContext';
import { downloadColorReportPdf } from '../lib/exportPdf';
import { api } from '../lib/api';

const UNDERTONE_LABEL = { warm: 'Undertone hangat', cool: 'Undertone dingin', neutral: 'Undertone netral' };

const AXIS_NAME = { undertone: 'Undertone', value: 'Kedalaman', chroma: 'Kejernihan' };
const AXIS_LABEL = {
  'slight warm': 'sedikit hangat', 'strong warm': 'sangat hangat',
  'slight cool': 'sedikit dingin', 'strong cool': 'sangat dingin',
  'strongly light': 'sangat terang', 'slightly light': 'cenderung terang',
  'slightly deep': 'cenderung gelap', 'strongly deep': 'sangat gelap',
  'slight clarity': 'sedikit jernih', 'clear clarity': 'jernih', 'strong clarity': 'sangat jernih',
  'slight muting': 'sedikit redup', 'strong muting': 'sangat redup',
};

// request_id analisis yang sudah disimpan otomatis ke riwayat.
// Di level modul agar tidak tersimpan ulang saat halaman dibuka kembali.
const autoSavedRequests = new Set();

const Result = () => {
  const { result, face, selectedId, setSelectedId, reset, profile } = useAnalysis();
  const [mode, setMode] = useState('foto'); // foto | live
  // Season yang sudah ada di "Simpan Hasil" (bookmark).
  const [savedSeasonIds, setSavedSeasonIds] = useState(() => new Set());
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const navigate = useNavigate();

  // Simpan otomatis ke riwayat begitu analisis selesai.
  // Backend meng-upsert berdasarkan request_id, sehingga tombol
  // "Simpan Hasil" hanya memperbarui season pada record yang sama.
  useEffect(() => {
    const requestId = result?.request_id;
    if (!requestId || autoSavedRequests.has(requestId)) return;

    const options = seasonOptions(result);
    const season = options.find((o) => o.id === selectedId) ?? options[0];
    if (!season) return;

    autoSavedRequests.add(requestId);
    saveToHistory(result, season, profile).catch((err) => {
      // Dicoba lagi saat efek berjalan berikutnya.
      autoSavedRequests.delete(requestId);
      console.error('Gagal mencatat riwayat:', err);
    });
  }, [result, selectedId, profile]);

  // Tandai season yang sudah pernah disimpan.
  useEffect(() => {
    const controller = new AbortController();
    api
      .getSaved(controller.signal)
      .then((items) => {
        if (Array.isArray(items)) {
          setSavedSeasonIds(new Set(items.map((item) => item.season_id)));
        }
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  if (!result) {
    return (
      <div className="gm-rise py-28 max-w-xl mx-auto text-center space-y-8">
        <h1 className="gm-display text-[56px] sm:text-[72px]">Belum ada <em>hasil.</em></h1>
        <Link to="/scan-wajah" className="gm-btn">Mulai analisis <FiArrowRight /></Link>
      </div>
    );
  }

  const options = seasonOptions(result);
  const selected = options.find((o) => o.id === selectedId) ?? options[0];
  const { gate } = result.result;
  const { description, keywords, palettes } = selected.palette;
  const faceQ = result.quality.face;
  const saved = savedSeasonIds.has(selected.id);
  const undertoneText = `${UNDERTONE_LABEL[gate.undertone]}${result.undertone?.confidence ? ` · ${Math.round(result.undertone.confidence * 100)}%` : ''}`;

  // "Simpan Hasil": bookmark nama season dan warnanya ke halaman Profil.
  const handleSave = async () => {
    setSaveError(null);
    setSaving(true);
    try {
      await api.saveResult({
        season_id: selected.id,
        season_name: selected.name,
        palette: palettes.utama.map((color) => color.hex),
      });
      setSavedSeasonIds((prev) => new Set(prev).add(selected.id));
    } catch (err) {
      setSaveError(err?.message || 'Hasil belum tersimpan. Coba lagi sebentar lagi.');
    } finally {
      setSaving(false);
    }
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
    <div className="pt-8 pb-4 max-w-6xl mx-auto">

      {/* 1. Hero: foto/live + nama season */}
      <section className="grid lg:grid-cols-[1.05fr_1fr] gap-10 lg:gap-14 items-center">
        <div className="gm-rise order-2 lg:order-1 space-y-4" style={{ '--d': '120ms' }}>
          <div className="gm-seg" role="group" aria-label="Mode tampilan">
            {[['foto', FiImage, 'Fotomu'], ['live', FiVideo, 'Coba live']].map(([m, Icon, label]) => (
              <button key={m} type="button" onClick={() => setMode(m)} aria-pressed={mode === m}>
                <Icon /> {label}
              </button>
            ))}
          </div>
          {mode === 'live' ? (
            <div key="live" className="gm-page">
              <LiveTryOn options={options} selected={selected} onSelect={setSelectedId} />
            </div>
          ) : (
            <div key="foto" className="gm-page relative w-full aspect-[4/3] rounded-[30px] overflow-hidden bg-ink shadow-[0_30px_60px_-35px_rgba(42,29,59,.7)]">
              {face?.photo && (
                <div className="absolute inset-0" style={{ transform: 'scaleX(-1)' }}>
                  <img src={face.photo} alt="Foto pengguna" className="absolute inset-0 w-full h-full object-cover" />
                  <FrameOverlay frameSize={faceQ.frame_size}>
                    <RadialBurst box={faceQ.box} colors={palettes.utama} animationKey={selected.id} />
                  </FrameOverlay>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="order-1 lg:order-2">
          <h1 key={selected.id} className="gm-display gm-rise text-[56px] sm:text-[84px]">
            Kamu adalah<br /><em>{selected.name}.</em>
          </h1>
          <p className="gm-lead gm-rise text-[16px] mt-6 max-w-md" style={{ '--d': '120ms' }}>
            {description}
          </p>
          <div className="gm-rise flex flex-wrap gap-2 mt-7" style={{ '--d': '200ms' }}>
            <span className="gm-tag">
              <span className="gm-dot" style={{ background: gate.undertone === 'warm' ? '#f69179' : gate.undertone === 'cool' ? '#96a8e0' : '#7e8a59' }} />
              {undertoneText}
            </span>
            {keywords.map((kw) => (
              <span key={kw} className="gm-tag">{kw}</span>
            ))}
          </div>
          {selected.palette.rekomendasi?.axis && (
            <dl className="gm-rise grid grid-cols-3 gap-4 mt-9 border-t border-line pt-6" style={{ '--d': '280ms' }}>
              {Object.entries(selected.palette.rekomendasi.axis).map(([key, a]) => (
                <div key={key}>
                  <dt className="text-[14px] text-gray-500">{AXIS_NAME[key] ?? key}</dt>
                  <dd className="font-serif text-[24px] leading-tight mt-1">{AXIS_LABEL[a.label] ?? a.label}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </section>

      {/* 2. Season mendekati */}
      <Reveal as="section" className="mt-28">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
          <h2 className="gm-display text-[44px] sm:text-[56px]">Season <em>terdekat.</em></h2>
          <button type="button" onClick={() => setMode('live')} className="gm-btn-ghost gm-btn-sm self-start sm:self-auto">
            <FiVideo /> Bandingkan live
          </button>
        </div>
        <SeasonSwitcher options={options} selectedId={selected.id} onSelect={setSelectedId} />
      </Reveal>

      {/* 3. Warna rekomendasi */}
      <Reveal as="section" className="mt-28 space-y-14">
        <h2 className="gm-display text-[44px] sm:text-[56px]">Warna <em>terbaikmu.</em></h2>
        <PaletteSection title="Warna utama" link="/full-palette/utama" colors={palettes.utama} limit={7} />
        <PaletteSection title="Warna netral" link="/full-palette/netral" colors={palettes.netral} limit={7} />
        <PaletteSection title="Palet lengkap" link="/full-palette/lengkap" colors={palettes.lengkap} limit={14} />
      </Reveal>

      {/* 4. Warna hindari */}
      <Reveal as="section" className="mt-28 space-y-10">
        <h2 className="gm-display text-[44px] sm:text-[56px]">Sebaiknya <em>dihindari.</em></h2>
        <PaletteSection title={`Kurang cocok untuk ${selected.name}`} link="/full-palette/hindari" colors={palettes.hindari} limit={7} />
      </Reveal>

      {/* 5. Simpan & unduh */}
      <Reveal as="section" className="mt-28 rounded-[36px] bg-ink text-paper px-7 py-12 sm:px-12 sm:py-14 relative overflow-hidden">
        <span className="absolute -right-20 -top-28 w-80 h-80 rounded-full bg-accent/40 blur-[90px] animate-[gm-drift-b_18s_ease-in-out_infinite]" aria-hidden="true" />
        <div className="relative flex flex-col lg:flex-row lg:items-end justify-between gap-8">
          <div>
            <h2 className="gm-display text-paper text-[44px] sm:text-[56px]">
              Bawa palet ini<br /><em>ke mana saja.</em>
            </h2>
            {saved && (
              <Link to="/profil?tab=simpan" className="gm-link text-[#d9b6d4] text-[14px] mt-5">
                Lihat di profil <FiArrowRight />
              </Link>
            )}
            {saveError && <p className="text-[14px] text-[#f5c2b4] mt-4">{saveError}</p>}
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => { reset(); navigate('/scan-wajah'); }}
              className="gm-btn-ghost text-paper border-white/25 hover:bg-white/10 hover:border-white/40"
            >
              <FiRefreshCw /> Analisis ulang
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saved || saving}
              className="gm-btn-ghost text-paper border-white/25 hover:bg-white/10 hover:border-white/40"
            >
              {saved ? <><BsBookmarkFill className="text-[#c9d6a0]" /> Tersimpan</> : <><FiBookmark /> {saving ? 'Menyimpan...' : 'Simpan hasil'}</>}
            </button>
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={isDownloadingPdf}
              className="gm-btn bg-paper text-ink hover:bg-white"
            >
              <FiDownload /> {isDownloadingPdf ? 'Membuat PDF...' : 'Unduh PDF'}
            </button>
          </div>
        </div>
      </Reveal>

      {/* 6. Penjelasan lanjutan */}
      <Reveal>
        <Link to="/penjelasan-analisis" className="group mt-10 flex items-center justify-between gap-6 border-y border-line py-8">
          <span className="gm-title text-[30px] sm:text-[40px] transition-colors group-hover:text-accent">
            Cara analisis ini bekerja
          </span>
          <span className="gm-orb"><FiArrowUpRight /></span>
        </Link>
      </Reveal>

    </div>
  );
};

export default Result;
