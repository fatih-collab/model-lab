/** Judul besar + penanda langkah, dipakai kedua halaman pindai. */
export function ScanHeader({ title, accent, step }) {
  return (
    <div className="grid lg:grid-cols-[1fr_auto] items-end gap-4 mb-10">
      <h1 className="gm-display gm-rise text-[52px] sm:text-[76px]">
        {title} <em>{accent}</em>
      </h1>
      <p className="gm-index gm-rise text-[40px] lg:text-right" style={{ '--d': '120ms' }}>{step} / 02</p>
    </div>
  );
}

export function ScanTips({ tips }) {
  return (
    <>
      <h2 className="gm-title text-[30px]">Sebelum memotret</h2>
      <ol className="mt-6 divide-y divide-line border-y border-line">
        {tips.map((tip, i) => (
          <li key={tip} className="py-4 grid grid-cols-[36px_1fr] gap-2 text-[15px] text-gray-600 leading-relaxed">
            <span className="gm-index text-[24px]">0{i + 1}</span>{tip}
          </li>
        ))}
      </ol>
    </>
  );
}
