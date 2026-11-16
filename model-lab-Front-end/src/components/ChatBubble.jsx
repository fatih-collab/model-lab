import { useEffect, useMemo, useRef, useState } from 'react';
import { FiMessageCircle, FiSend, FiX } from 'react-icons/fi';

import { api } from '../lib/api';
import { seasonOptions, useAnalysis } from '../context/AnalysisContext';

const SUGGESTIONS = [
  'Outfit kerja yang cocok?',
  'Outfit santai akhir pekan',
  'Baju untuk kondangan',
];

// Riwayat yang dikirim ke backend dibatasi agar hemat token.
const MAX_HISTORY = 4;

/** Foto outfit; bila gagal dimuat, tampilkan ilustrasi warna sebagai cadangan. */
function OutfitImage({ outfit }) {
  const [state, setState] = useState(outfit.image_url ? 'loading' : 'error');

  return (
    <div className="relative aspect-[4/5] w-full overflow-hidden rounded-lg bg-gray-100">
      {state !== 'error' && (
        <img
          src={outfit.image_url}
          alt={`Contoh outfit: ${outfit.name}`}
          loading="lazy"
          onLoad={() => setState('ok')}
          onError={() => setState('error')}
          className={`h-full w-full object-cover transition-opacity ${state === 'ok' ? 'opacity-100' : 'opacity-0'}`}
        />
      )}
      {state === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400 animate-pulse">
          Membuat foto outfit...
        </div>
      )}
      {state === 'error' && (
        <div className="absolute inset-0 flex flex-col">
          {outfit.colors.map((hex) => (
            <div key={hex} className="flex-1" style={{ background: hex }} />
          ))}
        </div>
      )}
    </div>
  );
}

function OutfitCard({ outfit }) {
  return (
    <div className="w-40 shrink-0 rounded-xl border border-gray-200 bg-white p-2">
      <OutfitImage outfit={outfit} />
      <p className="mt-2 text-xs font-semibold text-glowmatch-secondary">{outfit.name}</p>
      <div className="mt-1 flex gap-1">
        {outfit.colors.map((hex) => (
          <span
            key={hex}
            title={hex}
            className="h-4 w-4 rounded-full border border-black/10"
            style={{ background: hex }}
          />
        ))}
      </div>
      {outfit.items.length > 0 && (
        <ul className="mt-1 list-disc pl-4 text-[11px] leading-snug text-gray-600">
          {outfit.items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      )}
    </div>
  );
}

export default function ChatBubble() {
  const { result, selectedId } = useAnalysis();
  const [open, setOpen] = useState(false);
  const [allSeasons, setAllSeasons] = useState([]);
  const [seasonId, setSeasonId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const listRef = useRef(null);
  const abortRef = useRef(null);

  // Season dari hasil analisis (hasil akhir + season mendekati), bila ada.
  const analysisSeasons = useMemo(() => seasonOptions(result), [result]);
  const options = analysisSeasons.length ? analysisSeasons : allSeasons;

  // Tanpa hasil analisis: muat daftar 12 season sekali saat chat dibuka.
  useEffect(() => {
    if (!open || analysisSeasons.length || allSeasons.length) return;
    const ctrl = new AbortController();
    api.seasons(ctrl.signal).then(setAllSeasons).catch(() => {});
    return () => ctrl.abort();
  }, [open, analysisSeasons.length, allSeasons.length]);

  const activeId =
    (seasonId && options.some((o) => o.id === seasonId) && seasonId) ||
    (selectedId && options.some((o) => o.id === selectedId) && selectedId) ||
    options[0]?.id ||
    null;
  const activeSeason = options.find((o) => o.id === activeId);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const changeSeason = (id) => {
    setSeasonId(id);
    setMessages([]); // konteks baru untuk season berbeda
    setError('');
  };

  const send = async (text) => {
    const message = text.trim();
    if (!message || loading || !activeId) return;

    const history = messages
      .slice(-MAX_HISTORY)
      .map(({ role, content }) => ({ role, content: content.slice(0, 300) }));

    setMessages((m) => [...m, { role: 'user', content: message }]);
    setInput('');
    setError('');
    setLoading(true);

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const res = await api.chat({ season_id: activeId, message, history }, ctrl.signal);
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, outfits: res.outfits }]);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Gagal menghubungi Chat AI.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      {open && (
        <section
          aria-label="Chat AI rekomendasi outfit"
          className="flex h-[70vh] max-h-[600px] w-[calc(100vw-2rem)] max-w-sm flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl"
        >
          <header className="flex items-center justify-between gap-2 bg-glowmatch-primary px-4 py-3 text-white">
            <div className="min-w-0">
              <p className="text-sm font-semibold">Stylist AI GlowMatch</p>
              <p className="text-[11px] opacity-80">Rekomendasi outfit sesuai season</p>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Tutup chat" className="rounded-full p-1 hover:bg-white/20">
              <FiX size={18} />
            </button>
          </header>

          <div className="border-b border-gray-100 px-4 py-2">
            <label className="flex items-center gap-2 text-xs text-gray-500">
              Season
              <select
                value={activeId ?? ''}
                onChange={(e) => changeSeason(e.target.value)}
                disabled={!options.length}
                className="min-w-0 flex-1 rounded-lg border border-gray-200 bg-white px-2 py-1 text-xs text-glowmatch-secondary"
              >
                {!options.length && <option value="">Memuat season...</option>}
                {options.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}{o.id === result?.result?.season?.id ? ' (hasil kamu)' : ''}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {messages.length === 0 && (
              <div className="space-y-2 text-sm text-gray-500">
                <p>
                  Hai! Tanyakan outfit yang cocok untuk season
                  {' '}<b className="text-glowmatch-secondary">{activeSeason?.name ?? '...'}</b>.
                </p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => send(s)}
                      disabled={!activeId}
                      className="rounded-full border border-glowmatch-primary/30 px-3 py-1 text-xs text-glowmatch-primary hover:bg-glowmatch-primary/5 disabled:opacity-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'space-y-2'}>
                <p
                  className={`max-w-[85%] whitespace-pre-line rounded-2xl px-3 py-2 text-sm ${
                    m.role === 'user'
                      ? 'bg-glowmatch-primary text-white'
                      : 'bg-gray-100 text-glowmatch-secondary'
                  }`}
                >
                  {m.content}
                </p>
                {m.outfits?.length > 0 && (
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {m.outfits.map((o) => <OutfitCard key={o.name} outfit={o} />)}
                  </div>
                )}
              </div>
            ))}

            {loading && <p className="text-xs text-gray-400 animate-pulse">Stylist sedang mengetik...</p>}
            {error && <p className="text-xs text-red-600">{error}</p>}
          </div>

          <form
            onSubmit={(e) => { e.preventDefault(); send(input); }}
            className="flex items-center gap-2 border-t border-gray-100 p-3"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={500}
              placeholder="Tanya outfit untuk season-mu..."
              className="min-w-0 flex-1 rounded-full border border-gray-200 px-4 py-2 text-sm focus:border-glowmatch-primary focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !activeId}
              aria-label="Kirim"
              className="rounded-full bg-glowmatch-primary p-2.5 text-white disabled:opacity-50"
            >
              <FiSend size={16} />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full bg-glowmatch-primary px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:scale-105"
      >
        {open ? <FiX size={18} /> : <FiMessageCircle size={18} />}
        Chat AI
      </button>
    </div>
  );
}
