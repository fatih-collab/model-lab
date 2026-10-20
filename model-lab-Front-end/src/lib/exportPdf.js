import { jsPDF } from 'jspdf';

/** Helper konversi HEX ke RGB [r, g, b] */
function hexToRgb(hex) {
  let c = hex.replace('#', '');
  if (c.length === 3) c = c.split('').map((x) => x + x).join('');
  const num = parseInt(c, 16);
  return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
}

/**
 * Menghasilkan dan mengunduh laporan PDF Personal Color Analysis GlowMatch (1 Halaman Ringkas & Elegan).
 */
export async function downloadColorReportPdf({ result, selectedSeason, profile }) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 14;
  const contentWidth = pageWidth - margin * 2;

  const season = selectedSeason || result.result.season;
  const gate = result?.result?.gate || {};
  const palettes = season.palette.palettes;
  const userGender = profile?.gender || 'wanita';

  const fmtDate = new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());

  // === HEADER DENGAN WARNA BRAND GLOWMATCH ===
  doc.setFillColor(107, 70, 193); // #6B46C1
  doc.rect(0, 0, pageWidth, 26, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.text('GLOWMATCH', margin, 12);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.text('Laporan Resmi Analisis Warna Personal (12 Seasonal Color Analysis)', margin, 18);

  doc.setFontSize(8);
  doc.text(`Tanggal Cetak: ${fmtDate}`, pageWidth - margin - 35, 18);

  let y = 33;

  // === BOX PROFIL PENGGUNA ===
  doc.setFillColor(250, 250, 252);
  doc.setDrawColor(228, 230, 235);
  doc.roundedRect(margin, y, contentWidth, 20, 3, 3, 'FD');

  doc.setTextColor(45, 55, 72);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.text('PROFIL PENGGUNA', margin + 6, y + 6);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(74, 85, 104);
  const nameText = `Nama: ${profile?.name || 'Pengguna GlowMatch'}`;
  const genderText = `Gender: ${userGender === 'pria' ? 'Pria' : 'Wanita'}`;
  const ageText = `Umur: ${profile?.age ? `${profile.age} tahun` : '-'}`;
  doc.text(`${nameText}   |   ${genderText}   |   ${ageText}`, margin + 6, y + 12);
  doc.text(`ID Analisis: ${result?.request_id || 'GM-AUTO'}   |   Model: Gatekeeper 12-Season AI`, margin + 6, y + 16.5);

  y += 25;

  // === BANNER HASIL SEASON & UNDERTONE ===
  doc.setFillColor(255, 245, 235); // Soft Warm Peach
  doc.setDrawColor(254, 215, 180);
  doc.roundedRect(margin, y, contentWidth, 24, 3, 3, 'FD');

  doc.setTextColor(221, 107, 32);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.text('HASIL ANALISIS WARNA ALAMIMU', margin + 6, y + 6);

  doc.setTextColor(26, 32, 44);
  doc.setFontSize(13);
  doc.text(season.name, margin + 6, y + 13.5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(113, 128, 150);
  const undertoneLabel = gate.undertone === 'warm' ? 'Warm (Hangat)' : gate.undertone === 'cool' ? 'Cool (Dingin)' : 'Neutral (Netral)';
  doc.text(`Undertone: ${undertoneLabel}   ·   Karakteristik: ${season.palette.keywords.join(', ')}`, margin + 6, y + 19.5);

  y += 29;

  // === DESKRIPSI SINGKAT MUSIM ===
  doc.setFont('helvetica', 'italic');
  doc.setFontSize(8);
  doc.setTextColor(80, 90, 105);
  const splitDesc = doc.splitTextToSize(`"${season.palette.description}"`, contentWidth);
  doc.text(splitDesc, margin, y);
  y += splitDesc.length * 4 + 4;

  // === FUNGSI GAMBAR SWATCH WARNA ===
  const drawSwatches = (title, colorList, startY, countPerRow = 7) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(26, 32, 44);
    doc.text(title, margin, startY);

    let curY = startY + 3.5;
    const swatchW = (contentWidth - (countPerRow - 1) * 3) / countPerRow;
    const swatchH = 10;

    colorList.slice(0, 14).forEach((color, idx) => {
      const col = idx % countPerRow;
      const row = Math.floor(idx / countPerRow);
      const x = margin + col * (swatchW + 3);
      const sy = curY + row * (swatchH + 7.5);

      const [r, g, b] = hexToRgb(color.hex);
      doc.setFillColor(r, g, b);
      doc.setDrawColor(215, 220, 230);
      doc.roundedRect(x, sy, swatchW, swatchH, 1.8, 1.8, 'FD');

      // Teks HEX & Nama di bawah swatch
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(6.2);
      doc.setTextColor(45, 55, 72);
      const cleanName = color.name.length > 11 ? color.name.substring(0, 10) + '..' : color.name;
      doc.text(cleanName, x + swatchW / 2, sy + swatchH + 3, { align: 'center' });

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(5.2);
      doc.setTextColor(130, 140, 155);
      doc.text(color.hex.toUpperCase(), x + swatchW / 2, sy + swatchH + 5.8, { align: 'center' });
    });

    const rowsCount = Math.ceil(Math.min(colorList.length, 14) / countPerRow);
    return curY + rowsCount * (swatchH + 7.5) + 3;
  };

  // Swatch Warna Utama
  y = drawSwatches('1. Palet Warna Utama (Best Colors - Menonjolkan Kesegaran Alami Wajah)', palettes.utama, y, 7);
  y += 1.5;

  // Swatch Warna Netral
  y = drawSwatches('2. Palet Warna Netral (Dasar Pakaian, Jas/Blazer, Celana & Capsule Wardrobe)', palettes.netral, y, 7);
  y += 1.5;

  // Swatch Warna Hindari
  y = drawSwatches('3. Warna yang Sebaiknya Dihindari (Dapat Membuat Wajah Kusam atau Pucat)', palettes.hindari, y, 7);
  y += 2;

  // === PANDUAN PRAKTIS PENERAPAN WARNA ===
  doc.setFillColor(248, 249, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(margin, y, contentWidth, 28, 2.5, 2.5, 'FD');

  doc.setTextColor(45, 55, 72);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.text('PANDUAN APLIKASI WARNA:', margin + 5, y + 5.5);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.2);
  doc.setTextColor(70, 80, 95);
  doc.text('• Warna Utama: Sangat ideal untuk busana atasan, gaun/dress, hijab, syal, dan aksesori yang berada tepat di dekat area wajah.', margin + 5, y + 11.5);
  doc.text('• Warna Netral: Gunakan sebagai fondasi busana seperti celana panjang, rok, outer/blazer, jaket, dan tas sehari-hari.', margin + 5, y + 16.5);
  doc.text('• Warna Dihindari: Sebaiknya dijauhkan dari lingkar leher dan wajah agar tidak menimbulkan bayangan gelap atau kesan kusam.', margin + 5, y + 21.5);

  // === FOOTER DOKUMEN ===
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(7.2);
  doc.setTextColor(160, 174, 192);
  doc.text('GlowMatch AI Personal Color Analysis  ·  Dokumen Resmi Pribadi', margin, pageHeight - 8);
  doc.text('www.glowmatch.id', pageWidth - margin - 22, pageHeight - 8);

  // Simpan file
  const safeName = (profile?.name || 'Pengguna').replace(/[^a-zA-Z0-9]/g, '_');
  const filename = `GlowMatch-Analisis-Warna-${safeName}-${season.id}.pdf`;
  doc.save(filename);
  return filename;
}
