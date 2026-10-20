// src/components/ColorSwatch.jsx
import { useState } from 'react';
import { FiCopy, FiCheck } from 'react-icons/fi';

const ColorSwatch = ({ name, hex }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(hex);
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
        <div className="absolute top-2 right-2 bg-white/90 text-gray-700 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
          {copied ? <FiCheck className="text-green-600" /> : <FiCopy />}
        </div>
      </div>
      <div className="mt-2">
        <p className="text-sm font-semibold text-glowmatch-secondary">{name}</p>
        <p className="text-xs text-gray-400">{hex}</p>
      </div>
    </div>
  );
};

export default ColorSwatch;