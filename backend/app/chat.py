"""
Chat AI rekomendasi outfit per season (RAG ringan + 9router).

Alur:
  1. Retrieval : knowledge base (palet season + data fashion) dipecah menjadi
     potongan kecil per season. Potongan difilter keras berdasarkan season,
     lalu diberi skor keyword terhadap pertanyaan. Hanya top-k yang dikirim
     ke LLM, sehingga prompt tetap pendek (hemat token).
  2. Generation: 9router (endpoint OpenAI-compatible) dipanggil dengan system
     prompt ketat agar tidak keluar konteks dan menjawab dalam JSON.
  3. Post-process: warna dari LLM divalidasi terhadap palet season, lalu
     dibuatkan URL foto outfit (generator gambar dapat dikonfigurasi).

Tidak ada dependensi tambahan: HTTP memakai urllib bawaan Python.
"""
from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict, deque
from functools import lru_cache
from pathlib import Path

from app.palettes import PALETTES
from app.settings import settings

logger = logging.getLogger(__name__)

KB_FILE = Path(__file__).resolve().parent / "data" / "fashion_kb.json"

NO_SEASON_REPLY = (
    "Aku belum tahu season kamu. Lakukan analisis wajah dulu, atau tulis "
    "season-mu, misalnya: \"Outfit kerja untuk Deep Autumn\"."
)

OFF_TOPIC_REPLY = (
    "Maaf, aku hanya bisa membantu rekomendasi outfit dan warna "
    "sesuai season kamu. Coba tanyakan, misalnya: "
    "\"Outfit kerja untuk season-ku apa?\""
)

# Sinonim/kata kunci per kategori potongan (bahasa sehari-hari Indonesia).
_TAGS: dict[str, list[str]] = {
    "palette": ["warna", "palet", "cocok", "hindari", "netral", "color", "season"],
    "tops": ["atasan", "baju", "kemeja", "blouse", "kaos", "sweater", "polo", "top", "kardigan", "outer", "jaket", "blazer"],
    "bottoms": ["bawahan", "celana", "rok", "jeans", "chino", "kulot", "bottom"],
    "dresses": ["dress", "gaun", "terusan", "pesta", "kondangan"],
    "hijab": ["hijab", "jilbab", "kerudung", "pashmina"],
    "makeup": ["makeup", "make", "lipstik", "lip", "blush", "eyeshadow", "riasan"],
    "accessories": ["aksesoris", "jam", "dasi", "sabuk", "ikat", "tas", "sepatu", "kacamata"],
    "grooming": ["sepatu", "kacamata", "grooming", "rambut"],
    "metals": ["perhiasan", "emas", "perak", "kalung", "cincin", "anting", "logam", "gold", "silver"],
    "fabrics": ["bahan", "kain", "material", "tekstur", "linen", "katun", "sutra"],
    "looks": ["outfit", "ootd", "look", "padu", "padan", "kasual", "santai", "kerja", "kantor",
              "formal", "pesta", "acara", "kuliah", "kampus", "jalan", "date", "kencan", "liburan"],
}

# Kata yang menandakan pertanyaan masih dalam konteks fashion/warna.
_ON_TOPIC = {w for words in _TAGS.values() for w in words} | {
    "pakai", "pakaian", "gaya", "style", "fashion", "busana", "mix", "match", "rekomendasi",
    "saran", "tampil", "penampilan", "kulit", "undertone", "cerah", "gelap", "pastel",
    "pria", "wanita", "cowok", "cewek", "laki", "perempuan", "hari", "acara", "musim",
    "hujan", "panas", "pantai", "nikah", "wisuda", "interview", "wawancara", "lebaran",
}

_WORD = re.compile(r"[a-zA-Z]+")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ============================================================
# DETEKSI SEASON DARI PESAN PENGGUNA
# ============================================================

_FAMILY = {
    # Hanya nama season baku; kata cuaca ("panas", "dingin") sengaja tidak dipakai
    # agar "cuaca panas terang" tidak dianggap season.
    "primavera": "primavera", "spring": "primavera",
    "estate": "estate", "summer": "estate",
    "autunno": "autunno", "autumn": "autunno", "fall": "autunno",
    "inverno": "inverno", "winter": "inverno",
}
_SUBTYPE = {
    "light": "light", "terang": "light", "warm": "warm", "hangat": "warm",
    "bright": "bright", "clear": "bright", "cerah": "bright",
    "cool": "cool", "sejuk": "cool", "soft": "soft", "lembut": "soft",
    "deep": "deep", "dark": "deep", "gelap": "deep", "true": "true",
}
_TRUE = {"primavera": "warm", "autunno": "warm", "estate": "cool", "inverno": "cool"}


def detect_season(text: str) -> str | None:
    """Season yang ditulis pengguna, mis. "Deep Autumn", "autumn deep", "true summer"."""
    words = [w.lower() for w in _WORD.findall(text)]
    for i, w in enumerate(words):
        fam = _FAMILY.get(w)
        if not fam:
            continue
        # Kata sifat tepat sebelum atau sesudah nama family.
        for j in (i - 1, i + 1):
            sub = _SUBTYPE.get(words[j]) if 0 <= j < len(words) else None
            if sub == "true":
                sub = _TRUE[fam]
            if sub and f"{fam}_{sub}" in PALETTES:
                return f"{fam}_{sub}"
    return None


def season_name(season_id: str) -> str:
    return PALETTES[season_id]["rekomendasi"]["season"]


# ============================================================
# KNOWLEDGE BASE
# ============================================================

@lru_cache(maxsize=1)
def _fashion() -> dict:
    with KB_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _names(items: list[dict], n: int) -> str:
    return ", ".join(f"{c['name']} {c['hex']}" for c in items[:n] if c.get("name"))


@lru_cache(maxsize=None)
def chunks_for(season_id: str) -> tuple[tuple[str, str, str], ...]:
    """Potongan knowledge (kategori, gender, teks) untuk satu season."""
    pal = PALETTES[season_id]
    groups = pal["palettes"]
    fash = _fashion().get(season_id, {})
    out: list[tuple[str, str, str]] = [(
        "palette", "all",
        f"Karakter: {pal['description']} Warna terbaik: {_names(groups['utama'], 10)}. "
        f"Netral: {_names(groups['netral'], 6)}. Hindari: {_names(groups['hindari'], 6)}.",
    )]
    if fash.get("metals"):
        m = fash["metals"]
        out.append(("metals", "all", f"Perhiasan terbaik: {m['best']}. Hindari: {m['avoid']}."))
    if fash.get("fabrics"):
        out.append(("fabrics", "all", f"Bahan: {fash['fabrics']}"))
    for gender in ("women", "men"):
        for key, val in fash.get(gender, {}).items():
            if key == "makeup":
                val = "; ".join(f"{k}: {v}" for k, v in val.items())
            g = "wanita" if gender == "women" else "pria"
            out.append((key, g, f"{key.capitalize()} ({g}): {val}"))
    for look in fash.get("looks", []):
        out.append(("looks", "all", f"Look {look['name']}: {look['desc']} Warna {' '.join(look['colors'])}."))
    return tuple(out)


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)}


def retrieve(season_id: str, question: str, gender: str | None, k: int = 4) -> list[str]:
    """Top-k potongan relevan. Potongan palet selalu ikut sebagai dasar."""
    q = _tokens(question)
    g = (gender or "").lower()
    gender = "pria" if g in {"pria", "laki-laki", "male", "cowok"} else "wanita" if g else ""
    if q & {"pria", "cowok", "laki", "cowo"}:
        gender = "pria"
    elif q & {"wanita", "cewek", "perempuan", "cewe", "hijab", "jilbab"}:
        gender = "wanita"

    scored: list[tuple[float, int, str]] = []
    palette_text = ""
    for i, (cat, cg, text) in enumerate(chunks_for(season_id)):
        if cat == "palette":
            palette_text = text
            continue
        if gender and cg not in ("all", gender):
            continue
        score = 2.0 * len(q & set(_TAGS.get(cat, []))) + 0.5 * len(q & _tokens(text))
        if cat == "looks":
            score += 0.5  # contoh outfit jadi selalu berguna
        scored.append((score, -i, text))
    scored.sort(reverse=True)
    picked: list[str] = []
    looks = 0
    for _, _, text in scored:
        if text.startswith("Look "):
            if looks >= 2:
                continue
            looks += 1
        picked.append(text)
        if len(picked) >= k - 1:
            break
    return [palette_text] + picked


def is_on_topic(question: str, history: list[dict]) -> bool:
    """Penyaring murah sebelum memanggil LLM (tidak membuang token)."""
    if _tokens(question) & _ON_TOPIC or detect_season(question):
        return True
    # Pertanyaan lanjutan pendek ("yang lebih gelap?") diizinkan bila sudah ada percakapan.
    return bool(history) and len(question) <= 80


# ============================================================
# LLM (9router, OpenAI-compatible)
# ============================================================

SYSTEM_PROMPT = (
    "Kamu stylist GlowMatch. HANYA bahas outfit/warna/aksesoris/makeup untuk season pengguna. "
    "Jika di luar topik, balas reply: \"{off}\" dan outfits kosong. "
    "Gunakan KONTEKS saja; warna wajib hex dari konteks. Bahasa Indonesia, singkat (maks 80 kata). "
    "Sebut \"season\", jangan \"musim\". Jawab HANYA JSON valid: "
    "{{\"reply\":str,\"outfits\":[{{\"name\":str,\"items\":[str],\"colors\":[\"#RRGGBB\"],"
    "\"image_prompt\":str (bahasa Inggris, deskripsi pakaian saja)}}]}} maks 2 outfit."
).format(off=OFF_TOPIC_REPLY)


class ChatUnavailable(RuntimeError):
    """Chat AI belum dikonfigurasi atau 9router tidak dapat dihubungi."""


def _call_llm(messages: list[dict]) -> str:
    if not settings.ai_api_key or not settings.ai_model:
        raise ChatUnavailable(
            "Chat AI belum dikonfigurasi. Isi GLOWMATCH_AI_API_KEY dan GLOWMATCH_AI_MODEL di .env."
        )
    body = json.dumps({
        "model": settings.ai_model,
        "messages": messages,
        "max_tokens": settings.ai_max_tokens,
        "temperature": 0.4,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{settings.ai_base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.ai_api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.ai_timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        logger.warning("9router HTTP %s: %s", exc.code, exc.read()[:300])
        raise ChatUnavailable(f"Layanan AI menolak permintaan (HTTP {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("9router tidak dapat dihubungi: %s", exc)
        raise ChatUnavailable("Layanan AI tidak dapat dihubungi. Coba lagi nanti.") from exc

    text, finish = _read_completion(raw)
    if finish == "length":
        logger.warning("Jawaban AI terpotong (max_tokens=%s).", settings.ai_max_tokens)
    if not text.strip():
        raise ChatUnavailable(
            "AI tidak memberi jawaban. Naikkan GLOWMATCH_AI_MAX_TOKENS atau pakai model non-thinking."
        )
    return text


def _read_completion(raw: str) -> tuple[str, str | None]:
    """Teks & finish_reason dari respons JSON biasa ATAU streaming SSE (9router kadang mengirim SSE)."""
    raw = raw.strip()
    if raw.startswith("data:") or "\ndata:" in raw[:200]:
        parts, finish = [], None
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            try:
                choice = json.loads(line[5:])["choices"][0]
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                continue
            parts.append((choice.get("delta") or {}).get("content") or "")
            finish = choice.get("finish_reason") or finish
        return "".join(parts), finish
    try:
        choice = json.loads(raw)["choices"][0]
        return choice["message"]["content"] or "", choice.get("finish_reason")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise ChatUnavailable("Respons layanan AI tidak valid.") from exc


def _parse(raw: str) -> dict:
    """Ambil objek JSON dari jawaban LLM; jatuh ke teks biasa bila gagal."""
    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        try:
            obj = json.loads(match.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    # JSON terpotong: selamatkan isi "reply" agar pengguna tidak melihat JSON mentah.
    partial = re.search(r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)', raw, re.S)
    if partial:
        try:
            text = json.loads(f'"{partial.group(1)}"')
        except json.JSONDecodeError:
            text = partial.group(1)
        return {"reply": text.rstrip() + ("…" if not partial.group(0).endswith('"') else ""), "outfits": []}
    return {"reply": raw.strip(), "outfits": []}


def outfit_image_url(season_name: str, prompt: str, colors: list[str]) -> str | None:
    template = settings.outfit_image_url
    if not template:
        return None
    text = (
        f"fashion flat lay photo, {prompt[:220]}, color palette {' '.join(colors[:4])}, "
        f"{season_name} seasonal color, clean neutral background, no person, no text"
    )
    seed = sum(ord(ch) for ch in text) % 100000  # stabil -> gambar sama untuk prompt sama
    return template.format(prompt=urllib.parse.quote(text), seed=seed)


def _clean(obj: dict, season_id: str) -> dict:
    pal = PALETTES[season_id]
    groups = pal["palettes"]
    allowed = {c["hex"].upper() for g in ("utama", "netral", "lengkap") for c in groups[g]}
    allowed |= {h.upper() for look in _fashion().get(season_id, {}).get("looks", []) for h in look["colors"]}
    name = pal["rekomendasi"]["season"]

    outfits = []
    for o in (obj.get("outfits") or [])[:2]:
        if not isinstance(o, dict):
            continue
        colors = [c.upper() for c in o.get("colors", []) if isinstance(c, str) and _HEX.match(c)]
        colors = [c for c in colors if c in allowed][:4] or [c["hex"].upper() for c in groups["utama"][:3]]
        items = [str(i)[:80] for i in (o.get("items") or []) if i][:5]
        prompt = str(o.get("image_prompt") or ", ".join(items))[:240]
        outfits.append({
            "name": str(o.get("name") or "Outfit")[:60],
            "items": items,
            "colors": colors,
            "image_url": outfit_image_url(name, prompt, colors) if prompt else None,
        })
    reply = str(obj.get("reply") or "").strip()[:1200] or "Berikut rekomendasiku."
    return {"reply": reply, "outfits": outfits}


def answer(season_id: str, message: str, history: list[dict], gender: str | None) -> dict:
    """Pipeline lengkap RAG -> 9router -> validasi."""
    base = {"season_id": season_id, "season_name": season_name(season_id)}
    if not is_on_topic(message, history):
        return {**base, "reply": OFF_TOPIC_REPLY, "outfits": [], "off_topic": True}

    context = "\n".join(f"- {c}" for c in retrieve(season_id, message, gender))
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Riwayat dibatasi 4 pesan terakhir & dipangkas agar hemat token.
    for h in history[-4:]:
        messages.append({"role": h["role"], "content": h["content"][:300]})
    messages.append({
        "role": "user",
        "content": f"Season: {base['season_name']}. Gender: {gender or '-'}.\nKONTEKS:\n{context}\n\nPertanyaan: {message}",
    })
    return {**base, **_clean(_parse(_call_llm(messages)), season_id), "off_topic": False}


# ============================================================
# RATE LIMIT SEDERHANA (per sesi, in-memory)
# ============================================================

class RateLimiter:
    def __init__(self, limit: int, window_s: float) -> None:
        self.limit, self.window = limit, window_s
        self._hits: dict[int, deque] = defaultdict(deque)

    def allow(self, key: int) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True
