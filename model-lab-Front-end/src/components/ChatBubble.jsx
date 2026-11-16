import { useEffect, useMemo, useRef, useState } from 'react';
import { FiMessageCircle, FiSend, FiX } from 'react-icons/fi';

import { api } from '../lib/api';
import { seasonOptions, useAnalysis } from '../context/AnalysisContext';

const pickSeason = (id, name) => (id ? { id, name: name || id } : null);

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
  // Season terakhir yang dipakai percakapan (bisa berganti jika pengguna menulis season lain).
  const [chatSeason, setChatSeason] = useState(null);
  const [latestSeason, setLatestSeason] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const listRef = useRef(null);
  const abortRef = useRef(null);

  // Season hasil analisis yang sedang dibuka (pilihan pengguna di halaman hasil).
  const currentSeason = useMemo(() => {
    const options = seasonOptions(result);
    const s = options.find((o) => o.id === selectedId) ?? options[0];
    return s ? pickSeason(s.id, s.name) : null;
  }, [result, selectedId]);

  // Tanpa hasil analisis aktif: ambil season terbaru dari riwayat saat chat dibuka.
  useEffect(() => {
    if (!open || currentSeason || latestSeason) return;
    const ctrl = new AbortController();
    api.getHistory(1, ctrl.signal)
      .then((rows) => {
        const row = Array.isArray(rows) ? rows[0] : null;
        if (row) setLatestSeason(pickSeason(row.season_id, row.season_name));
      })
      .catch(() => {});
    return () => ctrl.abort();
  }, [open, currentSeason, latestSeason]);

  // Season percakapan hanya berlaku selama hasil analisis aktif tidak berganti.
  const convoSeason = chatSeason && chatSeason.base === (currentSeason?.id ?? null)
    ? chatSeason.season
    : null;
  const activeSeason = convoSeason ?? currentSeason ?? latestSeason;

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const send = async (text) => {
    const message = text.trim();
    if (!message || loading) return;

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
      // Backend memprioritaskan season yang ditulis di pesan, lalu season ini,
      // lalu season terbaru di riwayat.
      const res = await api.chat({ season_id: activeSeason?.id ?? null, message, history }, ctrl.signal);
      if (res.season_id) {
        setChatSeason({
          season: pickSeason(res.season_id, res.season_name),
          base: currentSeason?.id ?? null,
        });
      }
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
              <p className="truncate text-[11px] opacity-80">
                {activeSeason ? `Season: ${activeSeason.name}` : 'Rekomendasi outfit sesuai season'}
              </p>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Tutup chat" className="rounded-full p-1 hover:bg-white/20">
              <FiX size={18} />
            </button>
          </header>

          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {messages.length === 0 && (
              <div className="space-y-2 text-sm text-gray-500">
                {activeSeason ? (
                  <p>
                    Hai! Aku pakai season terbarumu,
                    {' '}<b className="text-glowmatch-secondary">{activeSeason.name}</b>.
                    {' '}Mau season lain? Tulis saja namanya, misalnya &ldquo;outfit untuk Deep Autumn&rdquo;.
                  </p>
                ) : (
                  <p>
                    Hai! Lakukan analisis wajah dulu, atau tulis season-mu di pesan,
                    misalnya &ldquo;outfit kerja untuk Light Spring&rdquo;.
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => send(s)}
                      disabled={!activeSeason}
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
              disabled={loading || !input.trim()}
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
