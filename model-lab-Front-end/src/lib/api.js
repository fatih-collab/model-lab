
// Client untuk GlowMatch API (backend FastAPI).
// Development: Vite mem-proxy /api ke backend localhost:8000.
// Production: set VITE_API_URL sesuai alamat backend.

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status, options = {}) {
    super(message);

    this.name = 'ApiError';
    this.status = status;
    this.code = options.code || null;
    this.detail = options.detail ?? null;
  }
}

/**
 * Mengirim request ke backend GlowMatch.
 *
 * credentials: include digunakan agar browser
 * mengirim dan menerima cookie session pengguna.
 */
async function request(
  path,
  { method = 'GET', form, json, signal } = {}
) {
  let res;

  const headers = {};
  let body = form;

  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  }

  try {
    res = await fetch(`${API_BASE}/api${path}`, {
      method,
      headers,
      body,
      signal,
      credentials: 'include',
    });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw err;
    }

    throw new ApiError(
      'Tidak dapat terhubung ke server analisis. Pastikan backend berjalan.',
      0
    );
  }

  const resBody = await res.json().catch(() => ({}));

  if (!res.ok) {
    const detail = resBody?.detail;

    let message = null;
    let code = null;

    if (Array.isArray(detail)) {
      message = detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join(', ');
    } else if (detail && typeof detail === 'object') {
      message = detail.message || detail.msg || null;
      code = detail.code || null;
    } else if (typeof detail === 'string') {
      message = detail;
    }

    const fallback =
      res.status === 503
        ? 'Model analisis belum siap di server.'
        : `Server error (${res.status}).`;

    throw new ApiError(message || fallback, res.status, {
      code,
      detail,
    });
  }

  return resBody;
}

/**
 * Membuat FormData untuk endpoint yang menerima gambar.
 */
function formOf(fields) {
  const fd = new FormData();

  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) {
      continue;
    }

    if (value instanceof Blob) {
      fd.append(key, value, `${key}.jpg`);
    } else {
      fd.append(key, String(value));
    }
  }

  return fd;
}

// ============================================================
// GLOWMATCH API
// ============================================================

export const api = {
  // ----------------------------------------------------------
  // HEALTH DAN SEASON
  // ----------------------------------------------------------

  health: (signal) =>
    request('/health', { signal }),

  seasons: (signal) =>
    request('/seasons', { signal }),

  // ----------------------------------------------------------
  // FACE FRAME DAN UNDERTONE
  // ----------------------------------------------------------

  /** Preprocessing: kualitas frame dan box wajah. */
  checkFrame: (image, kind = 'face', signal) =>
    request('/frame/check', {
      method: 'POST',
      form: formOf({ image, kind }),
      signal,
    }),

  analyzeUndertone: (wrist, signal) =>
    request('/undertone', {
      method: 'POST',
      form: formOf({ wrist }),
      signal,
    }),

  /** Face wajib; wrist atau undertone bersifat opsional. */
  analyze: ({ face, wrist, undertone, debug = false }, signal) =>
    request('/analyze', {
      method: 'POST',
      form: formOf({
        face,
        wrist,
        undertone,
        debug,
      }),
      signal,
    }),

  // ----------------------------------------------------------
  // USER PROFILE (NEON POSTGRESQL)
  // ----------------------------------------------------------

  getProfile: (signal) =>
    request('/profile', { signal }),

  updateProfile: (profile, signal) =>
    request('/profile', {
      method: 'POST',
      json: profile,
      signal,
    }),

  // ----------------------------------------------------------
  // ANALYSIS HISTORY (NEON POSTGRESQL)
  // ----------------------------------------------------------

  getHistory: (limit = 50, signal) =>
    request(`/history?limit=${limit}`, { signal }),

  addHistory: (data, signal) =>
    request('/history', {
      method: 'POST',
      json: data,
      signal,
    }),

  deleteHistory: (id, signal) =>
    request(`/history/${id}`, {
      method: 'DELETE',
      signal,
    }),
};
