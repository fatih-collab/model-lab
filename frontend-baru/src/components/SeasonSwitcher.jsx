/**
 * Pilihan season untuk visual swapping (hasil akhir + season mendekati).
 * compact: chip kecil untuk ditumpuk di atas video live.
 */
export default function SeasonSwitcher({ options, selectedId, onSelect, compact = false }) {
  if (compact) {
    return (
      <div className="flex flex-wrap justify-center gap-2">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            onClick={() => onSelect(o.id)}
            aria-pressed={o.id === selectedId}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[13px] border transition-all duration-300 ${
              o.id === selectedId ? 'bg-ink border-ink text-paper' : 'border-line bg-paper/70 hover:border-[#b498b8]'}`}
          >
            <span className="flex">
              {o.palette.palettes.utama.slice(0, 3).map((c) => (
                <span key={c.hex} className="w-3 h-3 rounded-full -ml-1 first:ml-0 ring-1 ring-paper" style={{ backgroundColor: c.hex }} />
              ))}
            </span>
            {o.name}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {options.map((o, i) => {
        const active = o.id === selectedId;
        return (
          <button
            key={o.id}
            type="button"
            onClick={() => onSelect(o.id)}
            aria-pressed={active}
            className={`gm-pop text-left rounded-[24px] border p-5 transition-all duration-500 ease-[cubic-bezier(.22,1,.36,1)] ${
              active
                ? 'border-ink bg-ink text-paper shadow-[0_20px_40px_-24px_rgba(42,29,59,.8)]'
                : 'border-line bg-paper/60 hover:-translate-y-1 hover:border-[#b498b8]'}`}
            style={{ '--d': `${i * 70}ms` }}
          >
            <span className="flex h-7 rounded-full overflow-hidden mb-5">
              {o.palette.palettes.utama.slice(0, 6).map((c) => (
                <span key={c.hex} className="flex-1" style={{ backgroundColor: c.hex }} />
              ))}
            </span>
            <span className="flex items-baseline justify-between gap-3">
              <span className="font-serif text-[24px] leading-tight">{o.name}</span>
              <span className={`font-serif italic text-[22px] ${active ? 'text-[#d9b6d4]' : 'text-[#b394b9]'}`}>
                {Math.round(o.model_probability * 100)}%
              </span>
            </span>
            {!o.matches_undertone && (
              <span className={`mt-3 inline-flex items-center gap-1.5 text-[13px] ${active ? 'text-[#f5c2b4]' : 'text-[#c0603f]'}`}>
                <span className="w-1.5 h-1.5 rounded-full bg-coral" /> Beda undertone
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
