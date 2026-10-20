/**
 * Data rekomendasi fashion, perhiasan, makeup/grooming, dan inspirasi outfit
 * untuk 12 seasonal personal color system.
 */

export const FASHION_RECOMMENDATIONS = {
  // SPRING (WARM & CLEAR / BRIGHT / LIGHT)
  primavera_light: {
    metals: {
      best: 'Emas Muda (Light Yellow Gold), Rose Gold, Enamel Peach',
      avoid: 'Perak gelap, Besi hitam pekat (Gunmetal)',
      notes: 'Pilih perhiasan berkilau halus dengan rona hangat yang tidak terlalu berat.',
    },
    fabrics: 'Kain ringan dan bernapas seperti katun sutra, linen halus, sifon, dan rajut kasmir lembut.',
    women: {
      tops: 'Blouse warna peach pastel, kemeja ivory, kardigan butter yellow, top coral lembut.',
      bottoms: 'Celana kulot light camel, rok A-line cream, celana bahan warm grey.',
      dresses: 'Midi dress floral rona aprikot, wrap dress warna light aqua.',
      hijab: 'Pashmina warna dusty peach, segiempat ivory crepe, cornflower chiffon.',
      makeup: {
        lips: 'Peach sorbet, coral pink cerah, soft apricot gloss.',
        cheeks: 'Warm peach blush, soft golden shimmer.',
        eyes: 'Champagne, light golden brown, peach shimmer.',
      },
    },
    men: {
      tops: 'Kemeja linen ivory, polo shirt light coral, sweater rajut cream.',
      bottoms: 'Chino pants light camel, celana kain warm taupe, light khaki.',
      accessories: 'Jam tangan strap kulit cokelat muda/tan dengan bezel gold, dasi warna apricot.',
      grooming: 'Frame kacamata tortoiseshell terang atau light gold, leather shoes rona cognac.',
    },
    looks: [
      { name: 'Kasual Santai', colors: ['#FFCBA4', '#FFF6E5', '#8FD8D2'], desc: 'Atasan peach dengan celana ivory dan tote bag aqua lembut.' },
      { name: 'Kerja / Formal', colors: ['#4D6A8C', '#FFF6E5', '#F8E38A'], desc: 'Blazer soft navy dengan inner ivory dan aksen syal butter.' },
      { name: 'Pesta / Acara Spesial', colors: ['#F7A08C', '#D7B48A', '#FFB878'], desc: 'Gaun atau kemeja light coral dipadu bawahan light camel berkilau.' },
    ],
  },

  primavera_warm: {
    metals: {
      best: 'Emas Kuning 18K/24K, Kuningan Berkilau (Polished Brass), Amber',
      avoid: 'Perak dingin, Platinum, Titanium abu-abu',
      notes: 'Logam keemasan hangat menyatu sempurna memancarkan kilau kulit cerahmu.',
    },
    fabrics: 'Katun premium, sutra halus, tweed hangat, dan bahan bertekstur cerah.',
    women: {
      tops: 'Blouse coral cerah, sweater golden yellow, kemeja tangerine, atasan kelly green.',
      bottoms: 'Celana camel, rok plisket warm taupe, celana palazzo warm ivory.',
      dresses: 'Sundress oranye bata cerah, maxi dress motif floral warm turquoise.',
      hijab: 'Jilbab warna mustard cerah, pashmina terracotta lembut, voal warm peach.',
      makeup: {
        lips: 'Warm coral, poppy red bernuansa oranye, bright peach satin.',
        cheeks: 'Warm coral blush, golden bronze highlighter.',
        eyes: 'Golden amber, warm bronze, copper satin.',
      },
    },
    men: {
      tops: 'Kemeja oxford warm ivory, kemeja polo kelly green, sweater mustard hangat.',
      bottoms: 'Chino camel, celana corduroy warm taupe, celana wool warm navy.',
      accessories: 'Jam tangan bezel emas kuning strap cokelat tua, ikat pinggang chestnut.',
      grooming: 'Sepatu loafers cokelat cognac hangat, kacamata warm brown horn rim.',
    },
    looks: [
      { name: 'Kasual Weekend', colors: ['#FF7F5E', '#FFF4DC', '#2EC4B6'], desc: 'T-shirt coral dengan celana santai warm ivory dan aksesoris turquoise.' },
      { name: 'Smart Casual / Kantor', colors: ['#2E4A7D', '#FFC93C', '#C9986B'], desc: 'Blazer warm navy dipadu inner golden yellow dan celana camel.' },
      { name: 'Evening Dinner', colors: ['#FA8E6E', '#8A4B2F', '#C6D93B'], desc: 'Setelan salmon lembut berpadu aksen chestnut dan perhiasan emas kuning.' },
    ],
  },

  primavera_bright: {
    metals: {
      best: 'Emas Kuning Mengkilap, Rose Gold Berkilau, Batu Permata Zamrud & Turquoise',
      avoid: 'Logam kusam (matte oxidised), tembaga berkarat gelap',
      notes: 'Gunakan logam cerah mengkilap (high shine) yang mengimbangi kontras tinggimu.',
    },
    fabrics: 'Satin mengkilap, poplin katun jernih, scuba berstruktur tajam, kulit jernih.',
    women: {
      tops: 'Atasan hot coral, blouse emerald green jernih, kemeja bright turquoise, top clear yellow.',
      bottoms: 'Celana bahan bright white, rok pensil navy jernih, kulot camel berstruktur.',
      dresses: 'Cocktail dress fuchsia coral, jumpsuit warna royal bright blue.',
      hijab: 'Pashmina warna bright coral, segiempat sutra emerald, jilbab clear watermelon.',
      makeup: {
        lips: 'Bright watermelon pink, hot coral glossy, clear warm red.',
        cheeks: 'Bright peach-pink blush berkilau segar.',
        eyes: 'Clear champagne eyeliner, shimmer emas terang, maskara tegas.',
      },
    },
    men: {
      tops: 'Kemeja putih bersih berkilau, kemeja bright blue, polo emerald jernih.',
      bottoms: 'Celana navy jernih, celana tailored camel, celana espresso gelap.',
      accessories: 'Jam tangan stainless steel gold mengkilap, dasi sutra bright turquoise.',
      grooming: 'Sepatu oxford cokelat tua mengkilap, kacamata frame transparan tebal atau gold.',
    },
    looks: [
      { name: 'Pop Kasual', colors: ['#00C2C7', '#FFFDF7', '#FF5A5F'], desc: 'Atasan bright turquoise dengan celana bright white dan aksen tas coral.' },
      { name: 'Power Business', colors: ['#1F3A6B', '#FFFDF7', '#00A86B'], desc: 'Jas navy jernih dengan kemeja putih dan dasi/syal emerald memukau.' },
      { name: 'Gala & Selebrasi', colors: ['#FF4FA0', '#FFE135', '#2B211C'], desc: 'Gaun fuchsia hangat atau jas malam beraksen dasi emas cerah.' },
    ],
  },

  // SUMMER (COOL & SOFT / LIGHT)
  estate_light: {
    metals: {
      best: 'Perak (Silver), Emas Putih (White Gold), Platinum, Mutiara Dingin',
      avoid: 'Emas kuning tua pekat, Tembaga oranye',
      notes: 'Logam bernuansa sejuk dan berkilau lembut memperkuat kehalusan kulit dinginmu.',
    },
    fabrics: 'Chiffon halus, sutra lembut, katun voile, rajutan tipis rona pastel dingin.',
    women: {
      tops: 'Blouse powder blue, atasan lavender dingin, kemeja baby pink, knit cool mint.',
      bottoms: 'Celana kulot light grey, rok midi blue grey, celana bahan soft white.',
      dresses: 'A-line dress warna lilac, sundress periwinkle dengan motif floral lembut.',
      hijab: 'Pashmina baby blue, jilbab segiempat dusty lilac, voal powder pink.',
      makeup: {
        lips: 'Soft rose, baby pink, cool sheer berry gloss.',
        cheeks: 'Cool petal pink blush lembut.',
        eyes: 'Soft lilac, cool taupe, shimmer perak halus.',
      },
    },
    men: {
      tops: 'Kemeja katun powder blue, kaos polo lavender muda, sweater rajut light grey.',
      bottoms: 'Celana bahan soft navy, chino light grey, celana denim washed biru muda.',
      accessories: 'Jam tangan strap kulit abu-abu perak, dasi warna periwinkle satin.',
      grooming: 'Kacamata frame silver matte atau abu-abu transparan, sepatu grey suede.',
    },
    looks: [
      { name: 'Brunch Kasual', colors: ['#B0D0E8', '#F7F7F5', '#F7C6D9'], desc: 'Blouse powder blue berpadu bawahan soft white dan tas baby pink.' },
      { name: 'Kantor Elegan', colors: ['#4E6280', '#D3D6DA', '#C9B8E6'], desc: 'Blazer soft navy dengan celana light grey dan inner lavender dingin.' },
      { name: 'Malam Romantis', colors: ['#E8A0B4', '#9AA9B8', '#A3AEEB'], desc: 'Gaun midi soft rose berpadu aksesori perak dan clutch blue grey.' },
    ],
  },

  estate_cool: {
    metals: {
      best: 'Perak Murni (Sterling Silver), Platinum Berkilau, Batu Safir & Amethyst',
      avoid: 'Emas kuning, Kuningan, Tembaga merah',
      notes: 'Dominasi nuansa dingin mutlak pada perhiasan agar kulit terlihat bersih bercahaya.',
    },
    fabrics: 'Wol halus, sutra dingin, katun mercerized, kashmir sejuk.',
    women: {
      tops: 'Blouse warna raspberry, atasan periwinkle dingin, kemeja cool blue, knit soft fuchsia.',
      bottoms: 'Celana bahan soft navy, rok pensil blue charcoal, celana bahan cool taupe.',
      dresses: 'Midi dress cool watermelon, dress berkerah warna spruce green.',
      hijab: 'Jilbab warna raspberry tua, pashmina denim blue, jilbab periwinkle cerah.',
      makeup: {
        lips: 'Cool raspberry, berry pink, mauve berona biru sejuk.',
        cheeks: 'Cool rose pink blush.',
        eyes: 'Cool grey taupe, lavender abu-abu, eyeliner navy.',
      },
    },
    men: {
      tops: 'Kemeja biru denim terang, polo shirt raspberry sejuk, sweater biru laut dingin.',
      bottoms: 'Celana tailored soft navy, celana kain blue charcoal, chino abu-abu sejuk.',
      accessories: 'Jam tangan stainless steel perak murni, dasi warna cool blue bertekstur.',
      grooming: 'Sepatu kulit hitam dove atau cool charcoal, frame kacamata titanium perak.',
    },
    looks: [
      { name: 'Gaya Santai Modis', colors: ['#4F7CAC', '#F4F4F2', '#B3446C'], desc: 'Kemeja cool blue dengan bawahan soft white dan aksen tas raspberry.' },
      { name: 'Rapat Eksekutif', colors: ['#2F4566', '#8A7F80', '#8E9BD9'], desc: 'Setelan jas soft navy berpadu kemeja periwinkle dan dasi cool taupe.' },
      { name: 'Gala & Resepsi', colors: ['#C45B9A', '#3C4552', '#F4F4F2'], desc: 'Gaun fuchsia dingin dengan perhiasan perak berkilau dan clutch navy.' },
    ],
  },

  estate_soft: {
    metals: {
      best: 'Perak Antik / Matte Silver, Emas Putih Halus, Rose Gold Sejuk',
      avoid: 'Emas kuning sangat cerah, Logam neon berkilau menyilaukan',
      notes: 'Finishing matte atau satin pada logam melengkapi kelembutan kulit berona debu.',
    },
    fabrics: 'Linen bertekstur lembut, suede halus, katun combed halus, rajut wol merino.',
    women: {
      tops: 'Blouse dusty rose, atasan soft teal, kemeja slate blue, cardigan mauve lembut.',
      bottoms: 'Celana kulot rose beige, rok plisket cool taupe, celana soft charcoal.',
      dresses: 'Midi dress dusty rose, wrap dress warna blue spruce.',
      hijab: 'Pashmina dusty rose, pashmina soft teal, segiempat warna cool cocoa.',
      makeup: {
        lips: 'Dusty mauve, soft plum nude, muted berry pink.',
        cheeks: 'Dusty rose blush matte.',
        eyes: 'Muted taupe, soft grey rose, cokelat keabuan lembut.',
      },
    },
    men: {
      tops: 'Kemeja linen slate blue, polo shirt soft teal, knit sweater cool taupe.',
      bottoms: 'Chino rose beige, celana wool soft charcoal, celana grey blue.',
      accessories: 'Jam tangan dengan strap abu-abu suede, dasi tenun bertekstur dusty rose.',
      grooming: 'Sepatu suede abu-abu/cool cocoa, frame kacamata matte grey tortoise.',
    },
    looks: [
      { name: 'Kencan Santai', colors: ['#C3949B', '#F2F0EA', '#6D9A9F'], desc: 'Atasan dusty rose berpadu celana soft white dan aksen syal soft teal.' },
      { name: 'Smart Office', colors: ['#4E5359', '#CDB7AE', '#6F84A8'], desc: 'Blazer soft charcoal dengan inner rose beige dan celana slate blue.' },
      { name: 'Kumpul Akhir Pekan', colors: ['#A27B92', '#7D8A96', '#94A89A'], desc: 'Sweater mauve dipadu celana grey blue dan sepatu berona cool sage.' },
    ],
  },

  // AUTUMN (WARM & MUTED / DEEP)
  autunno_soft: {
    metals: {
      best: 'Emas Antik (Brushed Gold), Tembaga Halus (Soft Copper), Perunggu Lembut',
      avoid: 'Perak putih berkilau tajam, Platinum dingin',
      notes: 'Pilih logam dengan sentuhan matte atau brushed berona keemasan hangat.',
    },
    fabrics: 'Linen berserat alami, katun crinkle, rajut wol hangat, corduroy lembut.',
    women: {
      tops: 'Atasan sage green, blouse dusty coral, kemeja soft teal, atasan muted salmon.',
      bottoms: 'Celana kulot oatmeal, rok A-line soft camel, celana mushroom.',
      dresses: 'Midi dress rona warm rose, linen dress warna muted olive.',
      hijab: 'Pashmina warna sage green, voal dusty coral, jilbab segiempat oatmeal.',
      makeup: {
        lips: 'Warm nude rose, muted terracotta, dusty coral peach.',
        cheeks: 'Muted peach rose blush hangat.',
        eyes: 'Soft olive brown, warm matte taupe, golden hazelnut.',
      },
    },
    men: {
      tops: 'Kemeja linen sage green, kemeja polo soft teal, knit sweater soft camel.',
      bottoms: 'Chino oatmeal, celana corduroy cocoa, celana bahan warm grey.',
      accessories: 'Jam tangan strap kulit cokelat bertekstur, ikat pinggang soft camel.',
      grooming: 'Sepatu desert boot suede cokelat, frame kacamata amber/tortoiseshell lembut.',
    },
    looks: [
      { name: 'Gaya Earthy Kasual', colors: ['#9CAF88', '#DDCDB4', '#CF8E7C'], desc: 'Kemeja sage green dengan celana oatmeal dan tas aksen dusty coral.' },
      { name: 'Kasual Kerja Kreatif', colors: ['#6E5646', '#F1E8D6', '#6E9C9A'], desc: 'Kardigan cocoa dengan kaos soft ivory dan celana bahan soft teal.' },
      { name: 'Wisata Santai', colors: ['#B6847E', '#A08F7A', '#79A391'], desc: 'Tunik warm rose dengan celana kulot mushroom dan aksesori muted jade.' },
    ],
  },

  autunno_warm: {
    metals: {
      best: 'Emas Kuning Tua (Rich Yellow Gold), Tembaga (Copper), Perunggu Tua (Bronze)',
      avoid: 'Perak mengkilap, Emas putih, Logam abu-abu es',
      notes: 'Logam rempah keemasan menonjolkan kekayaan pigmen hangat alami wajahmu.',
    },
    fabrics: 'Wol tweed tebal, beludru hangat, korduroi, kulit asli rona tan & saddle.',
    women: {
      tops: 'Atasan warna pumpkin, blouse mustard pekat, kemeja terracotta, knit olive green.',
      bottoms: 'Celana kulot camel tebal, rok span coffee brown, celana bahan khaki hangat.',
      dresses: 'Maxi dress motif dedaunan rust, wrap dress warna warm turquoise.',
      hijab: 'Pashmina warna terracotta, jilbab mustard emas, voal olive hijau hangat.',
      makeup: {
        lips: 'Terracotta hangat, burnt orange, warm brick red, cinnamon satin.',
        cheeks: 'Warm amber bronzer & terracotta blush.',
        eyes: 'Kuning keemasan, warm copper, perunggu rempah.',
      },
    },
    men: {
      tops: 'Flannel shirt warna rust, kemeja mustard, sweater rajut olive green.',
      bottoms: 'Chino camel tua, celana corduroy coffee, celana jeans wash gelap hangat.',
      accessories: 'Jam tangan bezel emas kuning strap kulit tan gelap, suspender kulit.',
      grooming: 'Sepatu boots kulit cokelat saddle, frame kacamata warm tortoise pekat.',
    },
    looks: [
      { name: 'Hangat Musim Gugur', colors: ['#D2691E', '#F1E2C3', '#708238'], desc: 'Atasan pumpkin cerah dipadu bawahan cream dan luaran olive green.' },
      { name: 'Gaya Profesional Karismatik', colors: ['#5A3A29', '#C19A6B', '#D4A017'], desc: 'Blazer cokelat tua pekat dengan celana camel dan dasi mustard emas.' },
      { name: 'Makan Malam Spesial', colors: ['#C0583A', '#2A7B79', '#8F7A62'], desc: 'Setelan terracotta berpadu aksen syal teal dan tas kulit warm taupe.' },
    ],
  },

  autunno_deep: {
    metals: {
      best: 'Emas Antik Pekat, Perunggu (Bronze), Tembaga Gelap, Batu Tiger Eye & Giok',
      avoid: 'Perak platinum terang benderang, Logam pastel pucat',
      notes: 'Pilihlah logam berona berat dan megah untuk mengimbangi kedalaman warnamu.',
    },
    fabrics: 'Beludru pekat, wool tebal, jacquard bermotif mewah, kulit gelap premium.',
    women: {
      tops: 'Blouse rust tua, atasan deep teal, kemeja burnt orange, knit forest green.',
      bottoms: 'Celana bahan espresso, rok span dark chocolate, celana warm charcoal.',
      dresses: 'Evening gown aubergine hangat, jumpsuit warna deep moss.',
      hijab: 'Pashmina warna deep teal, jilbab rust pekat, segiempat espresso gelap.',
      makeup: {
        lips: 'Deep brick red, warm burgundy, burnt plum, spiced chocolate.',
        cheeks: 'Deep warm bronze terracotta highlighter.',
        eyes: 'Deep bronze, forest green smokey, espresso brown.',
      },
    },
    men: {
      tops: 'Kemeja deep teal, sweater forest green, kemeja kasual rust pekat.',
      bottoms: 'Celana wool espresso, celana tailored dark chocolate, chino camel tua.',
      accessories: 'Jam tangan bezel emas antik strap kulit buaya cokelat gelap pekat.',
      grooming: 'Sepatu monk strap cokelat espresso gelap, kacamata dark tortoiseshell.',
    },
    looks: [
      { name: 'Kasual Berkelas', colors: ['#A54A2A', '#EFE1C6', '#0F5257'], desc: 'Sweater rajut rust tua dengan celana cream dan luaran deep teal.' },
      { name: 'Eksekutif Elegan', colors: ['#3B2A20', '#B07D4F', '#C1561B'], desc: 'Jas espresso dengan kemeja camel dan dasi burnt orange bertekstur.' },
      { name: 'Acara Malam Mewah', colors: ['#5B2333', '#2C4A2E', '#3C3836'], desc: 'Gaun malam aubergine hangat berpadu clutch forest green dan perhiasan perunggu.' },
    ],
  },

  // WINTER (COOL & DEEP / BRIGHT / CLEAR)
  inverno_bright: {
    metals: {
      best: 'Platinum Mengkilap, Perak Murni Berkaca (High Polish Silver), Emas Putih',
      avoid: 'Emas kuning tua kusam, Tembaga berkarat',
      notes: 'Kilau logam dingin dengan kontras ultra jernih membuat fitur wajahmu tegas.',
    },
    fabrics: 'Sutra mengkilap, satin tajam, kulit mengkilap (patent leather), wol kontras.',
    women: {
      tops: 'Atasan true red, blouse fuchsia cerah, kemeja royal blue, knit emerald green.',
      bottoms: 'Celana bahan pure white, celana hitam pekat (black), rok pensil navy jernih.',
      dresses: 'Gaun malam magenta cerah, cocktail dress cobalt blue kontras.',
      hijab: 'Pashmina fuchsia cerah, jilbab royal blue, segiempat pure white satin.',
      makeup: {
        lips: 'True bright red, vivid fuchsia, bright cool magenta.',
        cheeks: 'Bright cool pink blush merona segar.',
        eyes: 'Cat-eye eyeliner tajam hitam, eyeshadow icy silver, maskara pekat.',
      },
    },
    men: {
      tops: 'Kemeja pure white berkerah tajam, sweater cobalt blue, polo royal blue.',
      bottoms: 'Celana bahan jet black, celana navy pekat, celana tailored charcoal.',
      accessories: 'Jam tangan stainless steel perak berkilau tinggi, dasi fuchsia/merah permata.',
      grooming: 'Sepatu pantofel hitam mengkilap, frame kacamata hitam pekat atau silver tebal.',
    },
    looks: [
      { name: 'Kontras Tajam Kasual', colors: ['#D2042D', '#0B0B0B', '#FFFFFF'], desc: 'Atasan true red berpadu celana hitam pekat dan sneaker putih bersih.' },
      { name: 'Power Dressing', colors: ['#2049D6', '#FFFFFF', '#2F3135'], desc: 'Blazer royal blue dengan inner putih bersih dan celana charcoal.' },
      { name: 'Glamour Evening', colors: ['#FF0090', '#0B0B0B', '#00B5C9'], desc: 'Gaun malam fuchsia kontras dengan clutch hitam dan perhiasan turquoise dingin.' },
    ],
  },

  inverno_cool: {
    metals: {
      best: 'Perak Murni (Sterling Silver), Platinum, Emas Putih, Batu Safir Biru',
      avoid: 'Emas kuning, Kuningan, Oranye tembaga',
      notes: 'Pilihlah logam berwarna perak es murni yang bebas dari nuansa kekuningan.',
    },
    fabrics: 'Kashmir sejuk, wol merino halus, sutra dingin berbobot, velvet dingin.',
    women: {
      tops: 'Blouse warna ruby red, kemeja sapphire blue, atasan magenta, knit emerald.',
      bottoms: 'Celana bahan hitam pekat, rok pensil cool grey, celana tailored navy dingin.',
      dresses: 'Midi dress warna pine green, gaun royal purple dingin.',
      hijab: 'Pashmina sapphire blue, jilbab segiempat cool red, voal icy pink.',
      makeup: {
        lips: 'Cool blue-red, deep raspberry, wine red sejuk.',
        cheeks: 'Cool rosewood blush.',
        eyes: 'Silver smoke, navy liner, icy blue highlighter halus.',
      },
    },
    men: {
      tops: 'Kemeja sapphire blue, knit sweater pine green, kemeja putih bersih berkancing perak.',
      bottoms: 'Celana wool hitam murni, celana charcoal abu-abu sejuk, celana formal navy dingin.',
      accessories: 'Jam tangan perak rantai logam padat, dasi sutra motif ruby red.',
      grooming: 'Sepatu kulit hitam pekat bertali, frame kacamata silver titanium ramping.',
    },
    looks: [
      { name: 'Kasual Dingin Berkelas', colors: ['#0F52BA', '#FFFFFF', '#8E9297'], desc: 'Kemeja sapphire blue dengan celana putih bersih dan mantel cool grey.' },
      { name: 'Formal Bisnis Dingin', colors: ['#0B1F4B', '#FFFFFF', '#9B111E'], desc: 'Jas navy dingin dengan kemeja putih murni dan dasi sutra ruby red.' },
      { name: 'Gala Malam Dingin', colors: ['#6A0DAD', '#000000', '#CFE8F7'], desc: 'Gaun royal purple berpadu luaran hitam pekat dan perhiasan perak berkilau.' },
    ],
  },

  inverno_deep: {
    metals: {
      best: 'Emas Putih Berat, Platinum Pekat, Perak Oksidasi Gelap (Gunmetal), Onyx',
      avoid: 'Emas kuning pucat, Tembaga oranye menyala',
      notes: 'Logam dingin berbobot pekat dengan batu permata gelap menyempurnakan auramu.',
    },
    fabrics: 'Beludru hitam pekat, wol tebal, kulit domba gelap, satin sutra pekat.',
    women: {
      tops: 'Atasan warna burgundy, kemeja deep teal, blouse cranberry, knit deep fuchsia.',
      bottoms: 'Celana bahan jet black, rok pensil cool chocolate, celana bahan navy pekat.',
      dresses: 'Gaun aubergine gelap, jumpsuit warna true red berpotongan tegas.',
      hijab: 'Pashmina warna burgundy tua, jilbab sapphire pekat, jilbab hitam satin mewah.',
      makeup: {
        lips: 'Deep burgundy, blackberry, dark cherry, cool dark plum.',
        cheeks: 'Deep berry blush sejuk.',
        eyes: 'Charcoal smokey eye, eyeliner hitam tajam, deep plum accents.',
      },
    },
    men: {
      tops: 'Kemeja burgundy gelap, sweater deep teal pekat, kemeja hitam pekat.',
      bottoms: 'Celana bahan jet black, celana wool charcoal gelap, celana tailored navy tua.',
      accessories: 'Jam tangan gunmetal hitam dengan dial onyx, ikat pinggang kulit hitam tebal.',
      grooming: 'Sepatu oxford kulit hitam bertekstur, frame kacamata hitam glossy tebal.',
    },
    looks: [
      { name: 'Kasual Misterius', colors: ['#800020', '#0A0A0A', '#FFFFFF'], desc: 'Sweater burgundy pekat dipadu celana hitam pekat dan sneakers putih.' },
      { name: 'Petinggi Bisnis', colors: ['#101B3B', '#FFFFFF', '#00494F'], desc: 'Jas navy tua pekat dengan kemeja putih murni dan dasi deep teal.' },
      { name: 'Gala Malam Spektakuler', colors: ['#4B1248', '#0A0A0A', '#9E003A'], desc: 'Gaun aubergine gelap atau tuksedo hitam malam dengan aksen merah cranberry.' },
    ],
  },
};

export function getFashionForSeason(seasonId) {
  return FASHION_RECOMMENDATIONS[seasonId] || FASHION_RECOMMENDATIONS.primavera_warm;
}
