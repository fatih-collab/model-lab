// Client untuk GlowMatch API (backend FastAPI, Fase 2).
// Dev: Vite mem-proxy /api -> http://localhost:8000 (lihat vite.config.js). Produksi: set VITE_API_URL.
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = 'GET', form, json, signal } = {}) {
  let res;
  const headers = {};
  let body = form;
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  }
  try {
    res = await fetch(`${API_BASE}/api${path}`, { method, headers, body, signal });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Tidak dapat terhubung ke server analisis. Pastikan backend berjalan.', 0);
  }
  const resBody = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(resBody.detail) ? resBody.detail.map((d) => d.msg).join(', ') : resBody.detail;
    const fallback = res.status === 503 ? 'Model analisis belum siap di server.' : `Server error (${res.status}).`;
    throw new ApiError(detail || fallback, res.status);
  }
  return resBody;
}

function formOf(fields) {
  const fd = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) continue;
    if (value instanceof Blob) fd.append(key, value, `${key}.jpg`);
    else fd.append(key, String(value));
  }
  return fd;
}

export const api = {
  health: (signal) => request('/health', { signal }),
  seasons: (signal) => request('/seasons', { signal }),

  /** Preprocessing saja (cepat): kualitas frame + box wajah untuk cincin palet. */
  checkFrame: (image, kind = 'face', signal) =>
    request('/frame/check', { method: 'POST', form: formOf({ image, kind }), signal }),

  analyzeUndertone: (wrist, signal) =>
    request('/undertone', { method: 'POST', form: formOf({ wrist }), signal }),

  /** face wajib; wrist (Blob) ATAU undertone ('warm'|'cool'|'neutral') opsional. */
  analyze: ({ face, wrist, undertone, debug = false }, signal) =>
    request('/analyze', { method: 'POST', form: formOf({ face, wrist, undertone, debug }), signal }),

  // Profil pengguna (Database SQLite backend)
  getProfile: (signal) => request('/profile', { signal }),
  updateProfile: (profile, signal) => request('/profile', { method: 'POST', json: profile, signal }),

  // Riwayat analisis (Database SQLite backend)
  getHistory: (limit = 50, signal) => request(`/history?limit=${limit}`, { signal }),
  addHistory: (data, signal) => request('/history', { method: 'POST', json: data, signal }),
  deleteHistory: (id, signal) => request(`/history/${id}`, { method: 'DELETE', signal }),
};

