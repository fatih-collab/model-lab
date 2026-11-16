import { useState } from 'react';
import { FiCopy, FiCheck } from 'react-icons/fi';

// name boleh kosong (warna palet lengkap hanya punya kode hex).
const ColorSwatch = ({ name, hex, index = 0 }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard?.writeText(hex).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      type="button"
      className="gm-pop flex flex-col text-left group"
      style={{ '--d': `${Math.min(index, 14) * 35}ms` }}
      onClick={handleCopy}
      aria-label={`Salin ${name ? `${name} ` : ''}${hex}`}
    >
      <span
        className="relative block w-full aspect-[4/5] rounded-[20px] transition-[transform,box-shadow] duration-500 ease-[cubic-bezier(.22,1,.36,1)] group-hover:-translate-y-1.5 group-hover:shadow-[0_18px_30px_-18px_rgba(42,29,59,.55)]"
        style={{ backgroundColor: hex }}
      >
        <span
          className={`absolute left-2 right-2 bottom-2 flex items-center justify-between gap-1 rounded-full bg-paper/90 backdrop-blur px-2.5 py-1 text-label text-ink transition-all duration-300 ${
            copied ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0'
          }`}
        >
          <span className="uppercase tracking-wide">{hex}</span>
          {copied ? <FiCheck className="text-olive" /> : <FiCopy />}
        </span>
      </span>
      <span className="mt-2.5 text-small text-ink">{name || hex}</span>
    </button>
  );
};

export default ColorSwatch;
