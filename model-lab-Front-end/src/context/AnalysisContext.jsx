
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api } from '../lib/api';

// ============================================================
// SESSION STORAGE
// ============================================================

// Hanya untuk data sementara proses analisis.
// Profil dan riwayat menggunakan backend sebagai sumber utama.

const SESSION_KEY = 'glowmatch.analysis';

const AnalysisContext = createContext(null);

// Cache riwayat hanya untuk kompatibilitas fungsi lama.
// Data utama tetap berasal dari API backend.
let historyCache = [];

// ============================================================
// STORAGE HELPERS
// ============================================================

function readJSON(storage, key, fallback) {
  try {
    return JSON.parse(storage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function writeJSON(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value));
  } catch {
    // Kegagalan penyimpanan sementara tidak mengubah
    // status penyimpanan profil maupun riwayat di backend.
  }
}

// ============================================================
// ANALYSIS PROVIDER
// ============================================================

export function AnalysisProvider({ children }) {
  // ----------------------------------------------------------
  // TEMPORARY ANALYSIS STATE
  // ----------------------------------------------------------

  const saved = useMemo(
    () => readJSON(sessionStorage, SESSION_KEY, {}),
    []
  );

  const [face, setFace] = useState(saved.face ?? null);
  const [faceBlob, setFaceBlob] = useState(null);
  const [result, setResult] = useState(saved.result ?? null);
  const [selectedId, setSelectedId] = useState(
    saved.selectedId ?? null
  );

  // ----------------------------------------------------------
  // USER PROFILE STATE
  // ----------------------------------------------------------

  const [profile, setProfileState] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);

  /**
   * Memuat profil dari backend berdasarkan session browser.
   */
  const refreshProfile = useCallback(async (signal) => {
    setProfileLoading(true);
    setProfileError(null);

    try {
      const data = await api.getProfile(signal);

      setProfileState(data);

      return data;
    } catch (error) {
      setProfileError(error);
      throw error;
    } finally {
      setProfileLoading(false);
    }
  }, []);

  // Memuat profil saat aplikasi pertama kali dibuka.
  useEffect(() => {
    let ignore = false;

    api.getProfile()
      .then((data) => {
        if (!ignore) {
          setProfileState(data);
          setProfileError(null);
        }
      })
      .catch((error) => {
        if (!ignore && error.name !== 'AbortError') {
          setProfileError(error);
        }
      })
      .finally(() => {
        if (!ignore) {
          setProfileLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  /**
   * Menyimpan atau memperbarui profil melalui backend.
   *
   * State frontend baru diperbarui setelah backend
   * mengonfirmasi bahwa profil berhasil disimpan.
   */
  const updateProfile = useCallback(async (newProfile) => {
    setProfileError(null);

    const payload = {
      name: String(newProfile.name ?? '').trim(),
      gender: newProfile.gender ?? 'wanita',
      age:
        newProfile.age === '' || newProfile.age == null
          ? 22
          : Number(newProfile.age),
      notes: newProfile.notes ?? '',
    };

    try {
      const savedBackend = await api.updateProfile(payload);

      if (!savedBackend || savedBackend.is_complete !== true) {
        throw new Error(
          'Profil belum dikonfirmasi lengkap oleh server.'
        );
      }

      setProfileState(savedBackend);

      return savedBackend;
    } catch (error) {
      setProfileError(error);

      // Jangan menganggap penyimpanan berhasil
      // jika backend mengembalikan error.
      throw error;
    }
  }, []);

  // ----------------------------------------------------------
  // ANALYSIS SESSION PERSISTENCE
  // ----------------------------------------------------------

  useEffect(() => {
    writeJSON(sessionStorage, SESSION_KEY, {
      face,
      result,
      selectedId,
    });
  }, [face, result, selectedId]);

  const captureFace = useCallback((blob, info) => {
    setFaceBlob(blob);
    setFace(info);
    setResult(null);
    setSelectedId(null);
  }, []);

  const finishAnalysis = useCallback((res) => {
    setResult(res);
    setSelectedId(res.result.season.id);
  }, []);

  const reset = useCallback(() => {
    setFace(null);
    setFaceBlob(null);
    setResult(null);
    setSelectedId(null);
  }, []);

  // ----------------------------------------------------------
  // ANALYSIS HISTORY STATE
  // ----------------------------------------------------------

  const [history, setHistoryState] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);

  /**
   * Mengambil seluruh riwayat dari backend.
   */
  const refreshHistory = useCallback(async (limit = 50) => {
    setHistoryLoading(true);
    setHistoryError(null);

    try {
      const data = await api.getHistory(limit);

      const records = Array.isArray(data) ? data : [];

      historyCache = records;
      setHistoryState(records);

      return records;
    } catch (error) {
      setHistoryError(error);
      throw error;
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // ----------------------------------------------------------
  // CONTEXT VALUE
  // ----------------------------------------------------------

  const value = useMemo(
    () => ({
      // Data analisis sementara.
      face,
      faceBlob,
      result,
      selectedId,
      setSelectedId,

      // Profil pengguna dari backend.
      profile,
      profileLoading,
      profileError,
      refreshProfile,
      updateProfile,

      // Riwayat pengguna dari backend.
      history,
      historyLoading,
      historyError,
      refreshHistory,

      // Proses analisis.
      captureFace,
      finishAnalysis,
      reset,
    }),
    [
      face,
      faceBlob,
      result,
      selectedId,
      profile,
      profileLoading,
      profileError,
      refreshProfile,
      updateProfile,
      history,
      historyLoading,
      historyError,
      refreshHistory,
      captureFace,
      finishAnalysis,
      reset,
    ]
  );

  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  );
}

// ============================================================
// USE ANALYSIS
// ============================================================

// eslint-disable-next-line react-refresh/only-export-components
export function useAnalysis() {
  const ctx = useContext(AnalysisContext);

  if (!ctx) {
    throw new Error(
      'useAnalysis harus dipakai di dalam <AnalysisProvider>'
    );
  }

  return ctx;
}

// ============================================================
// SEASON OPTIONS
// ============================================================

/**
 * Semua musim yang bisa dipilih pengguna:
 * hasil akhir + musim tetangga.
 */

// eslint-disable-next-line react-refresh/only-export-components
export function seasonOptions(result) {
  if (!result) return [];

  return [
    result.result.season,
    ...result.result.neighbors,
  ];
}

// ============================================================
// HISTORY COMPATIBILITY
// ============================================================

/**
 * Mengambil cache riwayat yang sudah dimuat dari backend.
 *
 * Dipertahankan agar import pada halaman lama
 * tidak langsung rusak selama proses integrasi.
 */

// eslint-disable-next-line react-refresh/only-export-components
export function loadHistory() {
  return [...historyCache];
}

/**
 * Menyimpan hasil analisis dan season pilihan ke backend.
 *
 * Foto wajah dan frame kamera tidak ikut dikirim.
 * Backend akan membuat profile_snapshot berdasarkan
 * session pengguna yang sedang aktif.
 */

// eslint-disable-next-line react-refresh/only-export-components
export async function saveToHistory(
  result,
  season,
  currentProfile = null
) {
  if (!result?.result || !season?.palette) {
    throw new Error(
      'Hasil analisis atau season yang dipilih tidak valid.'
    );
  }

  const paletteHexes = season.palette.palettes.utama
    .slice(0, 5)
    .map((color) => color.hex);

  const requestId =
    result.request_id || `gm_${Date.now()}`;

  // Hilangkan informasi debug yang dapat berisi
  // representasi gambar hasil preprocessing.
  const analysisSnapshot = { ...result };
  delete analysisSnapshot.debug;

  const payload = {
    season_id: season.id,
    season_name: season.name,
    undertone: result.result.gate.undertone,
    request_id: requestId,
    detected_season: result.result.season.name,
    undertone_source: result.result.gate.undertone_source,
    confidence: result.undertone?.confidence ?? 1.0,
    palette: paletteHexes,
    notes: `Profil: ${currentProfile?.name || 'Pengguna GlowMatch'} (${currentProfile?.gender || 'wanita'}, ${currentProfile?.age || 22} th)`,

    // Snapshot klasifikasi lengkap tanpa gambar debug.
    analysis_result: analysisSnapshot,

    // Snapshot season yang dipilih pengguna.
    selected_season: season,
  };

  // Data hanya dianggap tersimpan setelah backend berhasil.
  const savedRecord = await api.addHistory(payload);

  historyCache = [
    savedRecord,
    ...historyCache.filter(
      (item) =>
        item.request_id !== savedRecord.request_id &&
        item.id !== savedRecord.id
    ),
  ];

  return savedRecord;
}

/**
 * Menghapus riwayat melalui backend.
 *
 * Cache baru diperbarui setelah backend mengonfirmasi
 * penghapusan berhasil.
 */

// eslint-disable-next-line react-refresh/only-export-components
export async function deleteFromHistory(id) {
  await api.deleteHistory(id);

  historyCache = historyCache.filter(
    (item) =>
      String(item.id) !== String(id) &&
      String(item.request_id) !== String(id)
  );

  return [...historyCache];
}
