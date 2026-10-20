"""
Palet 12 musim. Format sama dengan model-lab-Front-end/src/data/colorData.js:
  utama   : warna terbaik (dipakai cincin radial burst di sekitar wajah)
  netral  : warna dasar / basic wardrobe
  hindari : warna yang melawan karakter musim
Titik awal kurasi berdasarkan karakter tiap musim (nilai, suhu, kejernihan); silakan disesuaikan tim desain.
"""
from __future__ import annotations

_RAW = {
    "primavera_light": {
        "description": "Terang, hangat, dan lembut. Warna pastel hangat yang jernih membuat wajah tampak segar.",
        "keywords": ["Light", "Warm", "Clear"],
        "utama": [("Peach", "#FFCBA4"), ("Light Coral", "#F7A08C"), ("Butter", "#F8E38A"), ("Mint", "#B4E3C2"),
                  ("Light Aqua", "#8FD8D2"), ("Sky", "#8CC8EC"), ("Warm Pink", "#F6A6B9"), ("Apricot", "#FFB878"),
                  ("Lime Cream", "#D8E98C"), ("Light Periwinkle", "#AEB8F0")],
        "netral": [("Ivory", "#FFF6E5"), ("Cream", "#F3E3C6"), ("Light Camel", "#D7B48A"), ("Warm Grey", "#B9ADA0"),
                   ("Soft Navy", "#4D6A8C"), ("Milk Chocolate", "#8B6447")],
        "hindari": [("Black", "#1C1C1C"), ("Burgundy", "#6E1F35"), ("Icy Grey", "#D5DCE3"), ("Dark Olive", "#4A4A2A"),
                    ("Charcoal", "#36383C"), ("Plum", "#5E2A4E")],
    },
    "primavera_warm": {
        "description": "Hangat, cerah, dan penuh energi. Warna bernuansa keemasan yang jernih menyatu dengan kulitmu.",
        "keywords": ["Warm", "Light", "Clear"],
        "utama": [("Coral", "#FF7F5E"), ("Golden Yellow", "#FFC93C"), ("Warm Turquoise", "#2EC4B6"),
                  ("Kelly Green", "#4CBB17"), ("Tangerine", "#FF9933"), ("Poppy", "#F04E37"),
                  ("Golden Lime", "#C6D93B"), ("Aqua", "#3CC8C8"), ("Salmon", "#FA8E6E"), ("Warm Violet", "#8E7CE0")],
        "netral": [("Warm Ivory", "#FFF4DC"), ("Golden Beige", "#E1C29A"), ("Camel", "#C9986B"), ("Warm Taupe", "#A98467"),
                   ("Warm Navy", "#2E4A7D"), ("Chestnut", "#8A4B2F")],
        "hindari": [("Black", "#121212"), ("Icy Lavender", "#C8C2DB"), ("Dusty Mauve", "#A9869B"),
                    ("Blue Grey", "#8293A0"), ("Charcoal", "#424A51"), ("Burgundy", "#5C1A33")],
    },
    "primavera_bright": {
        "description": "Cerah, kontras, dan hangat. Warna jenuh yang bersih menonjolkan kilau alami wajahmu.",
        "keywords": ["Bright", "Warm", "Clear"],
        "utama": [("Hot Coral", "#FF5A5F"), ("Bright Turquoise", "#00C2C7"), ("Clear Yellow", "#FFE135"),
                  ("Emerald", "#00A86B"), ("Bright Blue", "#2F7DE1"), ("Hot Pink", "#FF4FA0"),
                  ("Bright Orange", "#FF8C00"), ("Lime", "#9BD72C"), ("Violet", "#8A4FFF"), ("Watermelon", "#F45B69")],
        "netral": [("Bright White", "#FFFDF7"), ("Light Warm Grey", "#CFC8BE"), ("Camel", "#C49A6C"),
                   ("Navy", "#1F3A6B"), ("Charcoal Brown", "#4A3B32"), ("Espresso", "#2B211C")],
        "hindari": [("Dusty Rose", "#C39BA3"), ("Muted Olive", "#8C8A5E"), ("Mauve Grey", "#9E8F98"),
                    ("Muted Beige", "#CDBFA8"), ("Muted Slate", "#7D8A94"), ("Muddy Brown", "#7B6656")],
    },
    "inverno_bright": {
        "description": "Kontras tinggi, jernih, dan dingin. Warna permata yang tajam membuat wajahmu tampak hidup.",
        "keywords": ["Bright", "Cool", "Clear"],
        "utama": [("True Red", "#D2042D"), ("Fuchsia", "#FF0090"), ("Royal Blue", "#2049D6"), ("Emerald", "#009B77"),
                  ("Icy Pink", "#F9D3E3"), ("Lemon Ice", "#F3F59A"), ("Bright Violet", "#8F00FF"),
                  ("Turquoise", "#00B5C9"), ("Magenta", "#D1007A"), ("Cobalt", "#0047AB")],
        "netral": [("Pure White", "#FFFFFF"), ("Black", "#0B0B0B"), ("Charcoal", "#2F3135"), ("Cool Grey", "#9EA3A8"),
                   ("Navy", "#14213D"), ("Icy Grey", "#E3E7EC")],
        "hindari": [("Camel", "#C19A6B"), ("Rust", "#A0522D"), ("Mustard", "#C9A227"), ("Olive", "#6B6B3A"),
                    ("Peach", "#F8C3A0"), ("Warm Beige", "#D9C2A0")],
    },
    "inverno_cool": {
        "description": "Dingin, tegas, dan jernih. Warna dengan dasar biru yang kuat paling menyatu dengan kulitmu.",
        "keywords": ["Cool", "Deep", "Clear"],
        "utama": [("Ruby", "#9B111E"), ("Sapphire", "#0F52BA"), ("Emerald", "#00875A"), ("Magenta", "#C2185B"),
                  ("Royal Purple", "#6A0DAD"), ("Icy Blue", "#CFE8F7"), ("Icy Pink", "#F4D6E4"), ("Cool Red", "#C8102E"),
                  ("Pine", "#01796F"), ("Hot Pink", "#E0218A")],
        "netral": [("Pure White", "#FFFFFF"), ("Black", "#000000"), ("Charcoal", "#333438"), ("Cool Grey", "#8E9297"),
                   ("Navy", "#0B1F4B"), ("Cool Taupe", "#7F7679")],
        "hindari": [("Orange", "#F28C28"), ("Camel", "#C19A6B"), ("Mustard", "#D4A017"), ("Warm Brown", "#8B5A2B"),
                    ("Peach", "#F5B994"), ("Olive", "#707035")],
    },
    "inverno_deep": {
        "description": "Gelap, dingin, dan dramatis. Warna pekat yang kaya memberi kedalaman pada wajahmu.",
        "keywords": ["Deep", "Cool", "Clear"],
        "utama": [("Burgundy", "#800020"), ("Deep Teal", "#00494F"), ("Emerald", "#00704A"), ("Royal Blue", "#1F3FA6"),
                  ("Cranberry", "#9E003A"), ("Aubergine", "#4B1248"), ("True Red", "#C40233"), ("Pine", "#01563F"),
                  ("Deep Fuchsia", "#A0005A"), ("Sapphire", "#0E3D8C")],
        "netral": [("Black", "#0A0A0A"), ("Charcoal", "#2B2B2E"), ("Cool Chocolate", "#3B2A2A"), ("Navy", "#101B3B"),
                   ("Pure White", "#FFFFFF"), ("Cool Grey", "#7D8086")],
        "hindari": [("Pastel Peach", "#FFD3B6"), ("Light Camel", "#D2B48C"), ("Mustard", "#CFA52C"),
                    ("Soft Coral", "#F4A38C"), ("Light Warm Grey", "#CFC7BB"), ("Butter", "#F6E3A1")],
    },
    "autunno_deep": {
        "description": "Gelap, hangat, dan kaya. Warna bumi yang pekat membingkai wajahmu dengan elegan.",
        "keywords": ["Deep", "Warm", "Muted"],
        "utama": [("Rust", "#A54A2A"), ("Burnt Orange", "#C1561B"), ("Olive", "#6B6A24"), ("Deep Teal", "#0F5257"),
                  ("Tomato", "#C23B22"), ("Mustard", "#C99A2E"), ("Forest", "#2C4A2E"), ("Warm Aubergine", "#5B2333"),
                  ("Bronze", "#8C6239"), ("Deep Moss", "#4F5D2F")],
        "netral": [("Espresso", "#3B2A20"), ("Dark Chocolate", "#4A2F22"), ("Camel", "#B07D4F"),
                   ("Olive Brown", "#5C4F33"), ("Warm Charcoal", "#3C3836"), ("Cream", "#EFE1C6")],
        "hindari": [("Icy Pink", "#F5D7E3"), ("Pastel Lavender", "#D7CCF0"), ("Baby Blue", "#BFD9F2"),
                    ("Fuchsia", "#FF2AA0"), ("Silver Grey", "#C7CBD1"), ("Pure White", "#FFFFFF")],
    },
    "autunno_warm": {
        "description": "Hangat, kaya, dan membumi. Warna rempah dan dedaunan musim gugur paling menyatu denganmu.",
        "keywords": ["Warm", "Muted", "Deep"],
        "utama": [("Pumpkin", "#D2691E"), ("Mustard", "#D4A017"), ("Olive", "#708238"), ("Terracotta", "#C0583A"),
                  ("Teal", "#2A7B79"), ("Rust", "#B7410E"), ("Moss", "#8A9A5B"), ("Gold", "#C9A44C"),
                  ("Brick", "#9C3D2E"), ("Warm Turquoise", "#3A9C8F")],
        "netral": [("Cream", "#F1E2C3"), ("Camel", "#C19A6B"), ("Khaki", "#A8986B"), ("Warm Taupe", "#8F7A62"),
                   ("Coffee", "#6F4E37"), ("Chocolate", "#5A3A29")],
        "hindari": [("Black", "#101010"), ("Icy Blue", "#D6ECF7"), ("Hot Pink", "#FF4FA0"), ("Cool Grey", "#9EA3A8"),
                    ("Royal Purple", "#6A0DAD"), ("Pure White", "#FFFFFF")],
    },
    "autunno_soft": {
        "description": "Lembut, hangat, dan redup. Warna berdebu yang tenang membuat kulitmu tampak halus dan menyatu.",
        "keywords": ["Soft", "Warm", "Muted"],
        "utama": [("Sage", "#9CAF88"), ("Dusty Coral", "#CF8E7C"), ("Soft Teal", "#6E9C9A"), ("Muted Olive", "#8A8A5C"),
                  ("Muted Salmon", "#D9967E"), ("Warm Rose", "#B6847E"), ("Soft Gold", "#C9AE6E"), ("Moss", "#7A8460"),
                  ("Soft Terracotta", "#B3735A"), ("Muted Jade", "#79A391")],
        "netral": [("Soft Ivory", "#F1E8D6"), ("Oatmeal", "#DDCDB4"), ("Soft Camel", "#B89874"), ("Mushroom", "#A08F7A"),
                   ("Warm Grey", "#8C8278"), ("Cocoa", "#6E5646")],
        "hindari": [("Black", "#0F0F0F"), ("Pure White", "#FFFFFF"), ("Fuchsia", "#FF1493"), ("Electric Blue", "#1E5BFF"),
                    ("Bright Orange", "#FF7F00"), ("Icy Grey", "#DDE3EA")],
    },
    "estate_soft": {
        "description": "Lembut, sejuk, dan redup. Warna berdebu dengan dasar keabuan membuat wajahmu tampak tenang.",
        "keywords": ["Soft", "Cool", "Muted"],
        "utama": [("Dusty Rose", "#C3949B"), ("Soft Teal", "#6D9A9F"), ("Lavender Grey", "#A39BB8"),
                  ("Slate Blue", "#6F84A8"), ("Cool Sage", "#94A89A"), ("Mauve", "#A27B92"),
                  ("Soft Raspberry", "#B05C7A"), ("Powder Blue", "#A9BCD0"), ("Muted Plum", "#7E5A7A"),
                  ("Blue Spruce", "#5E7F7A")],
        "netral": [("Soft White", "#F2F0EA"), ("Rose Beige", "#CDB7AE"), ("Cool Taupe", "#9A8C88"),
                   ("Grey Blue", "#7D8A96"), ("Cool Cocoa", "#6E5C5A"), ("Soft Charcoal", "#4E5359")],
        "hindari": [("Black", "#0B0B0B"), ("Orange", "#FF7F00"), ("Mustard", "#D4A017"), ("Bright Yellow", "#FFE135"),
                    ("Rust", "#B7410E"), ("Pure White", "#FFFFFF")],
    },
    "estate_cool": {
        "description": "Sejuk, lembut, dan elegan. Warna dengan dasar biru-merah muda menyatu alami dengan kulitmu.",
        "keywords": ["Cool", "Soft", "Light"],
        "utama": [("Raspberry", "#B3446C"), ("Periwinkle", "#8E9BD9"), ("Cool Blue", "#4F7CAC"),
                  ("Soft Fuchsia", "#C45B9A"), ("Powder Pink", "#F1B6C9"), ("Spruce", "#3E7A72"),
                  ("Lavender", "#B4A7D6"), ("Cool Watermelon", "#E0607E"), ("Denim", "#5A7BA8"),
                  ("Cool Sea Green", "#5FA39A")],
        "netral": [("Soft White", "#F4F4F2"), ("Cool Taupe", "#8A7F80"), ("Blue Grey", "#7A8B9A"),
                   ("Rose Brown", "#8C6B6B"), ("Soft Navy", "#2F4566"), ("Blue Charcoal", "#3C4552")],
        "hindari": [("Orange", "#F28C28"), ("Camel", "#C19A6B"), ("Mustard", "#D4A017"), ("Olive", "#6B6B3A"),
                    ("Rust", "#A0522D"), ("Black", "#000000")],
    },
    "estate_light": {
        "description": "Terang, sejuk, dan halus. Warna pastel dingin membuat wajahmu tampak cerah dan lembut.",
        "keywords": ["Light", "Cool", "Soft"],
        "utama": [("Powder Blue", "#B0D0E8"), ("Lavender", "#C9B8E6"), ("Baby Pink", "#F7C6D9"), ("Cool Mint", "#B6E2D3"),
                  ("Periwinkle", "#A3AEEB"), ("Cool Aqua", "#9FD8DB"), ("Rose", "#E8A0B4"), ("Lilac", "#D5B8E0"),
                  ("Sky Blue", "#8DBCE6"), ("Soft Watermelon", "#F09AAA")],
        "netral": [("Soft White", "#F7F7F5"), ("Light Grey", "#D3D6DA"), ("Rose Beige", "#DCC5BE"),
                   ("Blue Grey", "#9AA9B8"), ("Cool Cocoa", "#8C7672"), ("Soft Navy", "#4E6280")],
        "hindari": [("Black", "#0A0A0A"), ("Orange", "#F28C28"), ("Mustard", "#C9A227"), ("Chocolate", "#4A2F22"),
                    ("Olive", "#6B6B3A"), ("Burgundy", "#6E1F35")],
    },
}

PALETTES: dict[str, dict] = {
    sid: {
        "description": v["description"],
        "keywords": v["keywords"],
        "palettes": {k: [{"name": n, "hex": h} for n, h in v[k]] for k in ("utama", "netral", "hindari")},
    }
    for sid, v in _RAW.items()
}


def palette_for(season_id: str) -> dict:
    return PALETTES[season_id]
