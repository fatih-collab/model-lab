"""
Rules engine: Logic Gatekeeper + musim tetangga (visual swapping).

Aturan bisnis:
  WARM    -> hasil akhir WAJIB keluarga Spring / Autumn
  COOL    -> hasil akhir WAJIB keluarga Summer / Winter
  NEUTRAL -> tidak dikunci; mengikuti kecenderungan hangat/dingin model Season sendiri, dan musim tetangga dari
             KEDUA sisi ditampilkan (mis. Soft Summer <-> Soft Autumn).
  (tanpa foto pergelangan -> diperlakukan seperti NEUTRAL, sumber undertone = model season)

Musim tetangga mengikuti roda 12-season: tiap musim bertetangga dengan 2 musim yang berbagi satu karakter
dominan. Empat pasangan menyeberang undertone: Light Spring–Light Summer, Bright Spring–Bright Winter,
Deep Winter–Deep Autumn, Soft Autumn–Soft Summer.

Gatekeeper hanya mengikat HASIL OTOMATIS. Tetangga lintas undertone tetap dikirim (ditandai
matches_undertone=false) supaya pengguna bisa menukar secara manual (aturan bisnis #4).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

WARM_FAMILIES = ("Spring", "Autumn")
COOL_FAMILIES = ("Summer", "Winter")

# Urutan melingkar roda 12-season (id kelas Deep Armocromia).
WHEEL = [
    "primavera_light", "primavera_warm", "primavera_bright",
    "inverno_bright", "inverno_cool", "inverno_deep",
    "autunno_deep", "autunno_warm", "autunno_soft",
    "estate_soft", "estate_cool", "estate_light",
]


@dataclass
class SeasonOption:
    id: str
    name: str
    family: str
    undertone: str
    probability: float               # setelah gatekeeper (dinormalisasi ulang pada musim yang diizinkan)
    model_probability: float         # keluaran model season sebelum gatekeeper
    relation: str = ""               # final | same_family | cross_undertone | opposite_side_best
    matches_undertone: bool = True


@dataclass
class GateDecision:
    final: SeasonOption
    undertone: str                   # warm | cool | neutral (yang dipakai gatekeeper)
    undertone_source: str            # wrist_model | season_model
    gate_applied: bool
    rule: str
    allowed_families: list[str]
    model_choice: str                # argmax model season tanpa gatekeeper
    overridden: bool                 # hasil akhir berbeda dari pilihan model season
    conflict: bool                   # undertone pergelangan sangat bertentangan dengan model season
    season_p_warm: float
    lean: str                        # kecenderungan model season: warm | cool
    neighbors: list[SeasonOption] = field(default_factory=list)
    ranking: list[SeasonOption] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def wheel_neighbors(season_id: str) -> list[str]:
    i = WHEEL.index(season_id)
    return [WHEEL[(i - 1) % len(WHEEL)], WHEEL[(i + 1) % len(WHEEL)]]


def decide(season_probs: dict[str, float], labels: dict[str, dict], undertone: str | None = None,
           conflict_threshold: float = 0.25) -> GateDecision:
    """
    season_probs : {id_kelas: probabilitas} dari model season (12 kelas, jumlah = 1)
    labels       : {id_kelas: {"name", "family", "undertone", ...}} (manifest / bundle)
    undertone    : 'warm' | 'cool' | 'neutral' dari model pergelangan, atau None bila tidak ada
    """
    if set(season_probs) != set(WHEEL):
        raise ValueError(f"season_probs harus berisi tepat 12 kelas: {sorted(WHEEL)}")
    side = lambda c: labels[c]["undertone"]
    p_warm = sum(p for c, p in season_probs.items() if side(c) == "warm")
    lean = "warm" if p_warm >= 0.5 else "cool"

    if undertone in ("warm", "cool"):
        allowed = {c for c in season_probs if side(c) == undertone}
        families = list(WARM_FAMILIES if undertone == "warm" else COOL_FAMILIES)
        rule = f"{undertone.upper()} -> {' / '.join(families)}"
        applied, used, source = True, undertone, "wrist_model"
        side_mass = p_warm if undertone == "warm" else 1.0 - p_warm
        conflict = side_mass < conflict_threshold
    else:
        allowed = set(season_probs)
        families = list(WARM_FAMILIES + COOL_FAMILIES)
        rule = f"NEUTRAL -> tidak dikunci, mengikuti kecenderungan model season ({lean.upper()})"
        applied, used, conflict = False, "neutral", False
        source = "wrist_model" if undertone == "neutral" else "season_model"

    mass = sum(season_probs[c] for c in allowed)
    gated = {c: (season_probs[c] / mass if mass > 0 else 1.0 / len(allowed)) if c in allowed else 0.0
             for c in season_probs}

    def option(c: str, relation: str = "") -> SeasonOption:
        lab = labels[c]
        return SeasonOption(id=c, name=lab["name"], family=lab["family"], undertone=lab["undertone"],
                            probability=round(gated[c], 4), model_probability=round(season_probs[c], 4),
                            relation=relation, matches_undertone=c in allowed)

    final_id = max(gated, key=gated.get)
    model_choice = max(season_probs, key=season_probs.get)

    neighbors = []
    for n in wheel_neighbors(final_id):
        relation = "same_family" if labels[n]["family"] == labels[final_id]["family"] else "cross_undertone"
        neighbors.append(option(n, relation))
    if not applied and all(labels[n]["undertone"] == side(final_id) for n in wheel_neighbors(final_id)):
        # NEUTRAL + musim "true" (mis. Warm Spring) yang kedua tetangganya satu sisi: tambahkan kandidat
        # terbaik dari sisi seberang supaya pengguna tetap bisa membandingkan kedua sisi.
        other = max((c for c in season_probs if side(c) != side(final_id)), key=season_probs.get)
        neighbors.append(option(other, "opposite_side_best"))

    ranking = [option(c) for c in sorted(season_probs, key=lambda c: (-gated[c], -season_probs[c]))]
    return GateDecision(
        final=option(final_id, "final"), undertone=used, undertone_source=source, gate_applied=applied, rule=rule,
        allowed_families=families, model_choice=model_choice, overridden=final_id != model_choice,
        conflict=conflict, season_p_warm=round(p_warm, 4), lean=lean, neighbors=neighbors, ranking=ranking)
