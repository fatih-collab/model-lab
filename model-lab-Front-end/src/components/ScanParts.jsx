/** Judul besar + penanda langkah, dipakai kedua halaman pindai. */
export function ScanHeader({ title, step }) {
  return (
    <div className="mb-10">
      <p className="gm-rise text-small font-medium text-gray-600">Langkah {step} dari 2</p>
      <h1 className="gm-display gm-rise text-display mt-2" style={{ '--d': '80ms' }}>{title}</h1>
    </div>
  );
}

export function ScanTips({ tips }) {
  return (
    <>
      <h2 className="text-title">Sebelum memotret</h2>
      <ol className="mt-4 divide-y divide-line border-y border-line">
        {tips.map((tip, i) => (
          <li key={tip} className="py-4 grid grid-cols-[32px_1fr] gap-2 text-body text-gray-600">
            <span className="text-small font-medium tabular-nums" aria-hidden="true">0{i + 1}</span>{tip}
          </li>
        ))}
      </ol>
    </>
  );
}
