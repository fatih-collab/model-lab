// src/components/ColorSwatch.jsx
import { useState } from 'react';
import { FiCopy, FiCheck } from 'react-icons/fi';

// name boleh kosong (warna palet lengkap hanya punya kode hex).
// source "estimasi" = kode hex diperkirakan dari nama warna.
const ColorSwatch = ({ name, hex, source }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard?.writeText(hex).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000); // Kembali ke icon copy setelah 2 detik
  };

  return (
    <div
      className="flex flex-col group cursor-pointer"
      onClick={handleCopy}
      title="Klik untuk menyalin kode Hex"
    >
      <div
        className="w-full h-24 md:h-28 rounded-xl shadow-sm relative transition-transform transform group-hover:-translate-y-1"
        style={{ backgroundColor: hex }}
      >
        {/* Tombol Copy yang muncul saat di-hover */}
        <div className={`absolute top-2 right-2 bg-white/90 text-gray-700 p-1.5 rounded-lg transition-opacity ${copied ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
          {copied ? <FiCheck className="text-green-600" /> : <FiCopy />}
        </div>
      </div>
      <div className="mt-2">
        {name ? (
          <>
            <p className="text-sm font-semibold text-glowmatch-secondary">{name}</p>
            <p className="text-xs text-gray-400">
              {hex}
              {source === 'estimasi' && (
                <span className="ml-1.5 text-[10px] bg-gray-100 text-gray-500 px-1.5 rounded" title="Kode hex diperkirakan dari nama warna">
                  perkiraan
                </span>
              )}
            </p>
          </>
        ) : (
          <p className="text-sm font-semibold text-glowmatch-secondary">{hex}</p>
        )}
      </div>
    </div>
  );
};

export default ColorSwatch;
