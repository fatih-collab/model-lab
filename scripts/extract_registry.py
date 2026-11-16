import json
import re
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import register_experiment

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = PROJECT_ROOT / "registry"
WIB = ZoneInfo("Asia/Jakarta")

# File di root yang bukan notebook walaupun berformat teks/JSON.
ROOT_IGNORE = {"README.md", "research_log.md", ".gitignore"}

KAGGLE_LINK = re.compile(
    r"kaggle\.com/code/([\w-]+/[\w-]+)(?:\?scriptVersionId=(\d+))?"
)


def load_notebook(path: Path) -> dict | None:
    """Isi notebook bila `path` adalah notebook Jupyter (dengan atau tanpa ekstensi .ipynb)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and "cells" in data and "nbformat" in data:
        return data
    return None


def find_payload(nb_data: dict) -> dict | None:
    """Payload registry yang dicetak notebook di antara penanda START/END."""
    for cell in nb_data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream" and output.get("name") == "stdout":
                text = output.get("text", [])
                text = "".join(text) if isinstance(text, list) else text
                match = re.search(
                    r"===REGISTRY_PAYLOAD_START===\n(.*?)\n===REGISTRY_PAYLOAD_END===",
                    text,
                    re.DOTALL,
                )
                if match:
                    return json.loads(match.group(1))
    return None


def run_finished_at(nb_data: dict) -> datetime | None:
    """Waktu notebook selesai dijalankan di Kaggle.

    Sumber: metadata papermill (end_time), lalu stempel eksekusi sel terakhir.
    Dipakai untuk ID dan created_at supaya tanggal eksperimen mengikuti kapan
    pemodelan dijalankan, bukan kapan GitHub Action kebetulan berjalan.
    """
    stamps = []
    end_time = (nb_data.get("metadata") or {}).get("papermill", {}).get("end_time")
    if isinstance(end_time, str):
        stamps.append(end_time)
    if not stamps:
        for cell in nb_data.get("cells", []):
            execution = (cell.get("metadata") or {}).get("execution") or {}
            stamps += [v for v in execution.values() if isinstance(v, str)]

    parsed = []
    for stamp in stamps:
        # Kaggle kadang menulis pecahan detik 5 digit (mis. .77494); Python < 3.11 hanya menerima 3 atau 6.
        stamp = re.sub(r"\.(\d+)", lambda m: "." + m.group(1)[:6].ljust(6, "0"), stamp.replace("Z", "+00:00"), count=1)
        try:
            parsed.append(datetime.fromisoformat(stamp))
        except ValueError:
            continue
    parsed = [p for p in parsed if p.tzinfo is not None]
    return max(parsed).astimezone(WIB) if parsed else None


def kaggle_source(nb_data: dict) -> dict:
    """URL kernel Kaggle dan nomor versinya, bila notebook menyimpan tautan 'Open in Kaggle'."""
    for cell in nb_data.get("cells", [])[:3]:
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else source
        match = KAGGLE_LINK.search(source)
        if match:
            version = int(match.group(2)) if match.group(2) else None
            return {"version": version, "url": f"https://www.kaggle.com/code/{match.group(1)}"}
    return {"version": None, "url": None}


def unique_experiment_id(when: datetime | None) -> str:
    """ID baru yang belum dipakai file registry mana pun."""
    existing = {p.stem for p in REGISTRY_DIR.rglob("EXP-*.json")}
    while True:
        exp_id = register_experiment.generate_experiment_id(when)
        if exp_id not in existing:
            return exp_id


def process_notebook(nb_path: Path) -> bool:
    nb_data = load_notebook(nb_path)
    if nb_data is None:
        print(f"Skipping {nb_path.name}: bukan notebook Jupyter.")
        return False

    try:
        metadata = find_payload(nb_data)
    except json.JSONDecodeError as e:
        print(f"ERROR memproses {nb_path.name}: payload bukan JSON valid ({e})", file=sys.stderr)
        return False

    if not metadata:
        print(f"Skipping {nb_path.name}: Tidak ada cetakan registry payload.")
        return False

    try:
        finished_at = run_finished_at(nb_data)
        exp_id = unique_experiment_id(finished_at)
        created_at = finished_at or datetime.now(WIB)

        experiment = {
            "experiment_id": exp_id,
            "topic": metadata["topic"],
            "model": metadata["model"],
            "objective": metadata["objective"],
            "dataset": metadata["dataset"],
            "created_at": created_at.isoformat(),
            "metrics": metadata["metrics"],
            "status": "SUCCESS",
            "owner": metadata["owner"],
            "kaggle": kaggle_source(nb_data),
            "notebook": f"{exp_id}.ipynb",
            "previous_experiment": None
        }

        # Validasi dan simpan menggunakan source of truth
        register_experiment.validate_experiment(experiment)
        register_experiment.save_experiment(experiment)

        # Pindahkan notebook ke experiments/<topic>/ dan ubah nama sesuai Experiment ID.
        # Kaggle "Link to GitHub" menaruh notebook di root repo (kadang tanpa ekstensi .ipynb),
        # jadi notebook harus dipindahkan, bukan hanya di-rename di tempat.
        dest_dir = PROJECT_ROOT / "experiments" / metadata["topic"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        new_nb_path = dest_dir / f"{exp_id}.ipynb"
        nb_path.rename(new_nb_path)

        source = "waktu selesai di Kaggle" if finished_at else "waktu sekarang (notebook tanpa stempel waktu)"
        print(f"SUCCESS: Diekstrak {exp_id} ({source}) dari {nb_path.name} -> {new_nb_path.relative_to(PROJECT_ROOT)}")
        return True

    except Exception as e:
        print(f"ERROR memproses {nb_path.name}: {e}", file=sys.stderr)
        return False


def registered_notebooks() -> set[str]:
    """Nama file notebook yang sudah punya catatan registry."""
    names = set()
    for record_path in REGISTRY_DIR.rglob("EXP-*.json"):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        names.add(record.get("notebook") or f"{record_path.stem}.ipynb")
    return names


def find_candidate_notebooks() -> list[Path]:
    """
    Notebook yang belum diproses:
    1. Root repo -> tempat Kaggle "Link to GitHub" menyimpan notebook,
       termasuk file tanpa ekstensi .ipynb (nama file diketik bebas di Kaggle).
    2. experiments/<topic>/ yang namanya belum berformat EXP- -> penggunaan lokal/manual.
    3. experiments/<topic>/EXP-*.ipynb yang belum punya catatan registry
       (mis. diunggah langsung dengan nama EXP- buatan sendiri).
    """
    candidates = []
    for path in sorted(PROJECT_ROOT.iterdir()):
        if not path.is_file() or path.name.startswith(".") or path.name in ROOT_IGNORE:
            continue
        if path.suffix == ".ipynb" or (path.suffix == "" and load_notebook(path) is not None):
            candidates.append(path)

    registered = registered_notebooks()
    for topic in sorted(register_experiment.VALID_TOPICS):
        topic_dir = PROJECT_ROOT / "experiments" / topic
        if topic_dir.exists():
            candidates += sorted(
                nb for nb in topic_dir.glob("*.ipynb")
                if not nb.name.startswith("EXP-") or nb.name not in registered
            )

    return candidates


def main():
    for nb_path in find_candidate_notebooks():
        process_notebook(nb_path)

if __name__ == '__main__':
    main()
