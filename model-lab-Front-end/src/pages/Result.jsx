import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FiBookmark, FiDownload, FiArrowRight, FiChevronDown,
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

  // Empty state: kenapa kosong + apa yang harus dilakukan, satu aksi.
  if (!result) {
    return (
      <div className="gm-rise min-h-[55svh] py-20 max-w-xl mx-auto flex flex-col items-center justify-center text-center">
        <h1 className="gm-display text-display">Belum ada hasil analisis</h1>
        <p className="gm-lead text-body-lg mt-5">
          Ambil dua foto singkat untuk melihat season dan palet warnamu.
        </p>
        <Link to="/scan-wajah" className="gm-btn mt-8">Mulai analisis <FiArrowRight aria-hidden="true" /></Link>
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
          <h1 key={selected.id} className="gm-display gm-rise text-display">
            Kamu adalah <em>{selected.name}</em>
          </h1>
          <p className="gm-lead gm-rise text-body-lg mt-5 max-w-md" style={{ '--d': '120ms' }}>
            {description}
          </p>
          <div className="gm-rise flex flex-wrap gap-2 mt-6" style={{ '--d': '200ms' }}>
            <span className="gm-tag">
              <span className="gm-dot" style={{ background: gate.undertone === 'warm' ? '#f69179' : gate.undertone === 'cool' ? '#96a8e0' : '#7e8a59' }} />
              {undertoneText}
            </span>
            {keywords.slice(0, 3).map((kw) => (
              <span key={kw} className="gm-tag">{kw}</span>
            ))}
          </div>

          {/* Aksi: satu primer (Unduh PDF), satu sekunder (Simpan), satu tersier (Analisis ulang). */}
          <div className="gm-rise flex flex-wrap items-center gap-3 mt-8" style={{ '--d': '260ms' }}>
            <button type="button" onClick={handleDownloadPdf} disabled={isDownloadingPdf} className="gm-btn">
              <FiDownload aria-hidden="true" /> {isDownloadingPdf ? 'Membuat PDF...' : 'Unduh PDF'}
            </button>
            {saved ? (
              <Link to="/profil?tab=simpan" className="gm-btn-ghost" title="Lihat di profil">
                <BsBookmarkFill className="text-olive" aria-hidden="true" /> Tersimpan
              </Link>
            ) : (
              <button type="button" onClick={handleSave} disabled={saving} className="gm-btn-ghost">
                <FiBookmark aria-hidden="true" /> {saving ? 'Menyimpan...' : 'Simpan'}
              </button>
            )}
            <button
              type="button"
              onClick={() => { reset(); navigate('/scan-wajah'); }}
              className="gm-link text-small font-medium ml-2 min-h-[44px]"
            >
              <FiRefreshCw aria-hidden="true" /> Analisis ulang
            </button>
          </div>
          {saveError && <p className="text-small text-[#a3452c] mt-3" role="alert">{saveError}</p>}

          {/* Detail teknis disembunyikan sampai diminta (progressive disclosure). */}
          {selected.palette.rekomendasi?.axis && (
            <details className="gm-rise group mt-8 border-t border-line pt-4" style={{ '--d': '320ms' }}>
              <summary className="flex items-center gap-2 cursor-pointer list-none text-small font-medium text-gray-600 hover:text-ink [&::-webkit-details-marker]:hidden">
                Detail analisis <FiChevronDown className="transition-transform group-open:rotate-180" aria-hidden="true" />
              </summary>
              <dl className="grid grid-cols-3 gap-4 mt-4">
                {Object.entries(selected.palette.rekomendasi.axis).map(([key, a]) => (
                  <div key={key}>
                    <dt className="text-small text-gray-600">{AXIS_NAME[key] ?? key}</dt>
                    <dd className="text-title mt-0.5">{AXIS_LABEL[a.label] ?? a.label}</dd>
                  </div>
                ))}
              </dl>
              <Link to="/penjelasan-analisis" className="gm-link text-small font-medium mt-4">
                Cara analisis ini bekerja <FiArrowRight aria-hidden="true" />
              </Link>
            </details>
          )}
        </div>
      </section>

      {/* 2. Season mendekati (mode Live di hero sudah menjadi cara membandingkan langsung) */}
      <Reveal as="section" className="mt-28">
        <h2 className="gm-display text-headline mb-8">Season terdekat</h2>
        <SeasonSwitcher options={options} selectedId={selected.id} onSelect={setSelectedId} />
      </Reveal>

      {/* 3. Warna rekomendasi — "Palet lengkap" adalah gabungan utama + netral, jadi cukup tautan */}
      <Reveal as="section" className="mt-28 space-y-12">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 className="gm-display text-headline">Warna terbaikmu</h2>
          <Link to="/full-palette/lengkap" className="gm-link text-small font-medium">
            Lihat semua warna <FiArrowRight aria-hidden="true" />
          </Link>
        </div>
        <PaletteSection title="Warna utama" link="/full-palette/utama" colors={palettes.utama} limit={7} />
        <PaletteSection title="Warna netral" link="/full-palette/netral" colors={palettes.netral} limit={7} />
      </Reveal>

      {/* 4. Warna hindari */}
      <Reveal as="section" className="mt-28 space-y-8">
        <h2 className="gm-display text-headline">Warna yang sebaiknya dihindari</h2>
        <PaletteSection link="/full-palette/hindari" colors={palettes.hindari} limit={7} />
      </Reveal>

    </div>
  );
};

export default Result;
