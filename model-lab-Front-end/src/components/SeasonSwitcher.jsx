const RELATION_LABEL = {
  final: 'Hasil analisis',
  same_family: 'Satu keluarga',
  cross_undertone: 'Tetangga beda undertone',
  opposite_side_best: 'Terbaik dari sisi seberang',
};

/**
 * Pilihan musim untuk visual swapping (hasil akhir + musim tetangga).
 * compact: chip kecil untuk ditumpuk di atas video live.
 */
export default function SeasonSwitcher({ options, selectedId, onSelect, compact = false }) {
  if (compact) {
    return (
      <div className="flex flex-wrap justify-center gap-2">
        {options.map((o) => (
          <button key={o.id} onClick={() => onSelect(o.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-md transition ${
              o.id === selectedId ? 'bg-white text-glowmatch-secondary shadow' : 'bg-black/45 text-white hover:bg-black/60'}`}>
            <span className="flex">
              {o.palette.palettes.utama.slice(0, 3).map((c) => (
                <span key={c.hex} className="w-3 h-3 rounded-full -ml-1 first:ml-0 ring-1 ring-white" style={{ backgroundColor: c.hex }} />
              ))}
            </span>
            {o.name}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {options.map((o) => {
        const active = o.id === selectedId;
        return (
          <button key={o.id} onClick={() => onSelect(o.id)} aria-pressed={active}
            className={`text-left rounded-2xl border p-4 transition ${
              active ? 'border-glowmatch-primary bg-purple-50/60 shadow-sm' : 'border-gray-100 bg-white hover:border-purple-200'}`}>
            <div className="flex h-6 rounded-lg overflow-hidden mb-3">
              {o.palette.palettes.utama.slice(0, 6).map((c) => (
                <span key={c.hex} className="flex-1" style={{ backgroundColor: c.hex }} />
              ))}
            </div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{RELATION_LABEL[o.relation] ?? o.relation}</p>
            <p className="font-semibold text-glowmatch-secondary">{o.name}</p>
            <div className="flex items-center justify-between mt-1 text-xs text-gray-500">
              <span>Kecocokan model {Math.round(o.model_probability * 100)}%</span>
              {!o.matches_undertone && (
                <span className="bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full">di luar undertone</span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
