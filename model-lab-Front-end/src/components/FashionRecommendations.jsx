import { useState } from 'react';
import { FiCheck, FiX, FiLayers, FiSun, FiSmile, FiEye } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import { getFashionForSeason } from '../data/fashionData';

export default function FashionRecommendations({ seasonId, userGender = 'wanita' }) {
  const [activeGender, setActiveGender] = useState(userGender === 'pria' ? 'pria' : 'wanita');
  const fashion = getFashionForSeason(seasonId);
  const data = activeGender === 'pria' ? fashion.men : fashion.women;

  return (
    <div className="bg-white border border-gray-100 rounded-3xl p-6 sm:p-8 space-y-8 shadow-[0_4px_25px_rgb(0,0,0,0.02)]">
      
      {/* Header & Gender Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-5">
        <div>
          <div className="flex items-center gap-2 text-glowmatch-primary text-xs font-bold tracking-widest uppercase mb-1">
            <HiSparkles /> Wardrobe & Styling Guide
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-glowmatch-secondary">
            Panduan Gaya & Rekomendasi Busana
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Kombinasi pakaian, perhiasan, dan tata rias terbaik yang menyatu dengan rona musim warnamu.
          </p>
        </div>

        {/* Tab Gender */}
        <div className="flex bg-gray-100 p-1 rounded-xl self-start sm:self-auto text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveGender('wanita')}
            className={`px-4 py-2 rounded-lg transition-all ${
              activeGender === 'wanita'
                ? 'bg-white text-glowmatch-primary shadow-sm font-bold'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Busana Wanita
          </button>
          <button
            type="button"
            onClick={() => setActiveGender('pria')}
            className={`px-4 py-2 rounded-lg transition-all ${
              activeGender === 'pria'
                ? 'bg-white text-glowmatch-primary shadow-sm font-bold'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Busana Pria
          </button>
        </div>
      </div>

      {/* Grid 1: Busana & Bahan */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Atasan & Bawahan */}
        <div className="bg-purple-50/40 border border-purple-100/60 p-6 rounded-2xl space-y-3">
          <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-glowmatch-primary" />
            Pilihan Atasan (Tops) & Luaran
          </h4>
          <p className="text-xs text-gray-600 leading-relaxed">
            {data.tops}
          </p>

          <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2 pt-2">
            <span className="w-2.5 h-2.5 rounded-full bg-glowmatch-primary" />
            Pilihan Bawahan (Bottoms)
          </h4>
          <p className="text-xs text-gray-600 leading-relaxed">
            {data.bottoms}
          </p>
        </div>

        {/* Dress / Hijab (Wanita) ATAU Grooming & Aksesori (Pria) */}
        <div className="bg-orange-50/40 border border-orange-100/60 p-6 rounded-2xl space-y-3">
          {activeGender === 'wanita' ? (
            <>
              <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
                Dress & Gaun
              </h4>
              <p className="text-xs text-gray-600 leading-relaxed">
                {data.dresses}
              </p>

              <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2 pt-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
                Rekomendasi Warna Hijab (Bagi Hijabers)
              </h4>
              <p className="text-xs text-gray-600 leading-relaxed">
                {data.hijab}
              </p>
            </>
          ) : (
            <>
              <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
                Aksesori Pria & Jam Tangan
              </h4>
              <p className="text-xs text-gray-600 leading-relaxed">
                {data.accessories}
              </p>

              <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2 pt-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
                Grooming, Sepatu & Kacamata
              </h4>
              <p className="text-xs text-gray-600 leading-relaxed">
                {data.grooming}
              </p>
            </>
          )}
        </div>

      </div>

      {/* Grid 2: Logam Perhiasan & Tata Rias */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Logam & Aksesori */}
        <div className="bg-gray-50 border border-gray-100 p-6 rounded-2xl space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-glowmatch-secondary uppercase tracking-wider">
            <FiSun className="text-amber-500 text-sm" /> Rekomendasi Logam Perhiasan
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-start gap-2 text-emerald-800 bg-emerald-50/80 p-2.5 rounded-xl border border-emerald-100">
              <FiCheck className="text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong>Sangat Disarankan:</strong> {fashion.metals.best}
              </div>
            </div>
            <div className="flex items-start gap-2 text-rose-800 bg-rose-50/80 p-2.5 rounded-xl border border-rose-100">
              <FiX className="text-rose-600 shrink-0 mt-0.5" />
              <div>
                <strong>Sebaiknya Dihindari:</strong> {fashion.metals.avoid}
              </div>
            </div>
            <p className="text-gray-500 text-[11px] pt-1 italic">
              💡 {fashion.metals.notes}
            </p>
          </div>
        </div>

        {/* Tata Rias / Grooming */}
        <div className="bg-gray-50 border border-gray-100 p-6 rounded-2xl space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-glowmatch-secondary uppercase tracking-wider">
            <FiSmile className="text-purple-500 text-sm" /> 
            {activeGender === 'wanita' ? 'Rekomendasi Makeup Alami' : 'Karakter Bahan & Tekstur Kain'}
          </div>
          {activeGender === 'wanita' ? (
            <div className="space-y-2 text-xs text-gray-600">
              <p>
                <strong className="text-glowmatch-secondary">Warna Bibir (Lips):</strong> {data.makeup.lips}
              </p>
              <p>
                <strong className="text-glowmatch-secondary">Pipi (Blush):</strong> {data.makeup.cheeks}
              </p>
              <p>
                <strong className="text-glowmatch-secondary">Rias Mata (Eyes):</strong> {data.makeup.eyes}
              </p>
              <p className="text-gray-400 text-[11px] pt-1">
                Kain terbaik: {fashion.fabrics}
              </p>
            </div>
          ) : (
            <div className="space-y-2 text-xs text-gray-600">
              <p className="leading-relaxed">
                <strong className="text-glowmatch-secondary">Tekstur & Serat Terbaik:</strong> {fashion.fabrics}
              </p>
              <p className="text-gray-500 leading-relaxed text-[11px] pt-1">
                Pilihlah kemeja dan luaran dengan bobot bahan yang harmonis dengan intensitas warna musimmu untuk kesan rapi dan proporsional.
              </p>
            </div>
          )}
        </div>

      </div>

      {/* 3 Inspirasi Palet Outfit Harian */}
      <div className="space-y-4 pt-2">
        <h4 className="font-bold text-glowmatch-secondary text-sm flex items-center gap-2">
          <FiLayers className="text-glowmatch-primary" /> 3 Inspirasi Formula Padu Padan Harian
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {fashion.looks.map((look) => (
            <div key={look.name} className="bg-gray-50/70 border border-gray-200/60 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-glowmatch-secondary">{look.name}</span>
                <div className="flex -space-x-1.5">
                  {look.colors.map((c, i) => (
                    <div
                      key={i}
                      className="w-5 h-5 rounded-full border border-white shadow-xs"
                      style={{ backgroundColor: c }}
                      title={c}
                    />
                  ))}
                </div>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{look.desc}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
