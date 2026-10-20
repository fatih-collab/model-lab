import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';

// State alur analisis lintas halaman & profil pengguna.
const SESSION_KEY = 'glowmatch.analysis';
const HISTORY_KEY = 'glowmatch.history';
const PROFILE_KEY = 'glowmatch.profile';

const DEFAULT_PROFILE = {
  name: 'Pengguna GlowMatch',
  gender: 'wanita',
  age: 22,
  notes: '',
};

const AnalysisContext = createContext(null);

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
    /* kuota penuh / mode privat: abaikan */
  }
}

export function AnalysisProvider({ children }) {
  const saved = useMemo(() => readJSON(sessionStorage, SESSION_KEY, {}), []);
  const [face, setFace] = useState(saved.face ?? null); // { photo: dataURL, box, frameSize }
  const [faceBlob, setFaceBlob] = useState(null);
  const [result, setResult] = useState(saved.result ?? null); // respons /api/analyze (status ok)
  const [selectedId, setSelectedId] = useState(saved.selectedId ?? null);

  // Profil pengguna
  const savedProfile = useMemo(() => readJSON(localStorage, PROFILE_KEY, DEFAULT_PROFILE), []);
  const [profile, setProfileState] = useState(savedProfile);

  // Load profil dari backend saat awal jika tersedia
  useEffect(() => {
    let ignore = false;
    api.getProfile().then((data) => {
      if (!ignore && data && data.name) {
        setProfileState(data);
        writeJSON(localStorage, PROFILE_KEY, data);
      }
    }).catch(() => {
      // Backend offline: pakai profil dari localStorage
    });
    return () => { ignore = true; };
  }, []);

  const updateProfile = useCallback(async (newProfile) => {
    const merged = { ...profile, ...newProfile };
    setProfileState(merged);
    writeJSON(localStorage, PROFILE_KEY, merged);
    try {
      const savedBackend = await api.updateProfile(merged);
      if (savedBackend) {
        setProfileState(savedBackend);
        writeJSON(localStorage, PROFILE_KEY, savedBackend);
      }
    } catch {
      // Offline fallback tetap aktif
    }
    return merged;
  }, [profile]);

  useEffect(() => {
    writeJSON(sessionStorage, SESSION_KEY, { face, result, selectedId });
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

  const value = useMemo(
    () => ({
      face, faceBlob, result, selectedId, setSelectedId,
      profile, updateProfile,
      captureFace, finishAnalysis, reset,
    }),
    [face, faceBlob, result, selectedId, profile, updateProfile, captureFace, finishAnalysis, reset],
  );
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error('useAnalysis harus dipakai di dalam <AnalysisProvider>');
  return ctx;
}

/** Semua musim yang bisa dipilih pengguna: hasil akhir + musim tetangga (visual swapping). */
// eslint-disable-next-line react-refresh/only-export-components
export function seasonOptions(result) {
  if (!result) return [];
  return [result.result.season, ...result.result.neighbors];
}

// eslint-disable-next-line react-refresh/only-export-components
export function loadHistory() {
  return readJSON(localStorage, HISTORY_KEY, []);
}

// eslint-disable-next-line react-refresh/only-export-components
export async function saveToHistory(result, season, currentProfile = null) {
  const paletteHexes = season.palette.palettes.utama.slice(0, 5).map((c) => c.hex);
  const entry = {
    id: result.request_id || `gm_${Date.now()}`,
    savedAt: new Date().toISOString(),
    seasonId: season.id,
    season: season.name,
    detected: result.result.season.name,
    undertone: result.result.gate.undertone,
    undertoneSource: result.result.gate.undertone_source,
    palette: paletteHexes,
    user_name: currentProfile?.name || 'Pengguna GlowMatch',
    user_gender: currentProfile?.gender || 'wanita',
    user_age: currentProfile?.age || 22,
  };

  const localHistory = [entry, ...loadHistory().filter((h) => h.id !== entry.id)].slice(0, 50);
  writeJSON(localStorage, HISTORY_KEY, localHistory);

  // Simpan ke database backend
  try {
    await api.addHistory({
      season_id: season.id,
      season_name: season.name,
      undertone: result.result.gate.undertone,
      request_id: entry.id,
      detected_season: result.result.season.name,
      undertone_source: result.result.gate.undertone_source,
      confidence: result.undertone?.confidence ?? 1.0,
      palette: paletteHexes,
      notes: `Profil: ${entry.user_name} (${entry.user_gender}, ${entry.user_age} th)`,
      profile_id: currentProfile?.id,
    });
  } catch {
    // Abaikan jika server offline, data sudah tersimpan di localStorage
  }

  return localHistory;
}

// eslint-disable-next-line react-refresh/only-export-components
export async function deleteFromHistory(id) {
  const updated = loadHistory().filter((h) => h.id !== id && String(h.id) !== String(id));
  writeJSON(localStorage, HISTORY_KEY, updated);
  try {
    await api.deleteHistory(id);
  } catch {
    // Abaikan error jika backend offline
  }
  return updated;
}

