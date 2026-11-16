"""
Mengubah "Color Season Palette.xlsx" menjadi app/color_recommendations.py.

Pemakaian (dari folder backend):
    python scripts/import_color_palette.py "../Color Season Palette.xlsx"

Jalankan ulang setiap kali file Excel diperbarui. Hasilnya berupa modul Python biasa,
jadi backend tidak perlu membaca Excel (dan tidak butuh openpyxl) saat berjalan.
"""
from __future__ import annotations

import pprint
import re
import sys
from pathlib import Path

import openpyxl

# Nama sheet Excel -> id kelas model (lihat rules_engine.WHEEL).
SHEET_TO_ID = {
    "Light Spring": "primavera_light",
    "True Spring": "primavera_warm",
    "Bright Spring": "primavera_bright",
    "Bright Winter": "inverno_bright",
    "True Winter": "inverno_cool",
    "Deep Winter": "inverno_deep",
    "Deep Autumn": "autunno_deep",
    "True Autumn": "autunno_warm",
    "Soft Autumn": "autunno_soft",
    "Soft Summer": "estate_soft",
    "True Summer": "estate_cool",
    "Light Summer": "estate_light",
}

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
AXIS = re.compile(r"(Undertone|Value|Chroma)\s+([+-]?\d+(?:\.\d+)?)\s*\(([^)]*)\)")


def _section_rows(ws, title_prefix: str):
    """Baris data di bawah judul seksi sampai baris kosong berikutnya."""
    start = None
    for row in range(1, ws.max_row + 1):
        v = ws.cell(row, 1).value
        if isinstance(v, str) and v.startswith(title_prefix):
            start = row
            break
    if start is None:
        raise ValueError(f"[{ws.title}] seksi '{title_prefix}' tidak ditemukan")
    # Lewati judul, (catatan), dan header "No".
    row = start + 1
    while ws.cell(row, 1).value != "No":
        row += 1
    row += 1
    while row <= ws.max_row and ws.cell(row, 1).value is not None:
        yield row
        row += 1


def _hex(value, where: str) -> str:
    value = str(value).strip().upper()
    if not HEX.match(value):
        raise ValueError(f"hex tidak valid {value!r} di {where}")
    return value


def parse(path: Path) -> dict:
    wb = openpyxl.load_workbook(path, data_only=True)
    out: dict[str, dict] = {}
    for ws in wb:
        sid = SHEET_TO_ID.get(ws.title)
        if sid is None:
            raise ValueError(f"sheet tidak dikenal: {ws.title}")
        axis = {
            m.group(1).lower(): {"value": float(m.group(2)), "label": m.group(3).strip()}
            for m in AXIS.finditer(str(ws["A2"].value or ""))
        }
        chromatic = [_hex(ws.cell(r, 2).value, f"{ws.title}!B{r}") for r in _section_rows(ws, "Chromatic Colors")]
        neutral = [_hex(ws.cell(r, 2).value, f"{ws.title}!B{r}") for r in _section_rows(ws, "Neutral Colors")]

        def named(prefix: str) -> list[dict]:
            return [
                {
                    "name": str(ws.cell(r, 2).value).strip(),
                    "hex": _hex(ws.cell(r, 3).value, f"{ws.title}!C{r}"),
                    "source": str(ws.cell(r, 5).value or "").strip().lower() or "official",
                }
                for r in _section_rows(ws, prefix)
            ]

        out[sid] = {
            "season": ws.title,
            "axis": axis,
            "chromatic": chromatic,
            "neutral": neutral,
            "flatter": named("Colors That Flatter"),
            "avoid": named("Colors to Avoid"),
        }
    missing = set(SHEET_TO_ID.values()) - set(out)
    if missing:
        raise ValueError(f"season belum ada di Excel: {sorted(missing)}")
    return out


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "../Color Season Palette.xlsx")
    dst = Path(__file__).resolve().parents[1] / "app" / "color_recommendations.py"
    data = parse(src)
    body = pprint.pformat(data, width=110, sort_dicts=False)
    dst.write_text(
        '"""\n'
        "Rekomendasi warna 12 season dari \"Color Season Palette.xlsx\" (sumber: colorme.style).\n"
        "FILE INI DIBUAT OTOMATIS oleh scripts/import_color_palette.py. Jangan diedit manual.\n\n"
        "  chromatic : 28 warna palet season (OKLab)\n"
        "  neutral   : 4 warna netral\n"
        "  flatter   : warna yang paling mendukung, lengkap dengan nama\n"
        "  avoid     : warna yang sebaiknya dihindari\n"
        "  source    : official = hex dari situs, estimasi = hex diperkirakan dari nama warna\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        f"RECOMMENDATIONS: dict[str, dict] = {body}\n\n\n"
        "def recommendations_for(season_id: str) -> dict:\n"
        "    return RECOMMENDATIONS[season_id]\n",
        encoding="utf-8",
    )
    print(f"{len(data)} season ditulis ke {dst}")


if __name__ == "__main__":
    main()
