import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

# PENTING: harus diset SEBELUM `import register_experiment`.
# Tanpa ini Python membuat scripts/__pycache__/register_experiment.cpython-311.pyc,
# lalu `git add -A` di workflow ikut meng-commit file biner tsb. File biner itu
# berubah di tiap run & tiap branch -> konflik biner saat merge Master <-> model_history.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import register_experiment  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def process_notebook(nb_path: Path) -> bool:
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            nb_data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR membaca {nb_path.name}: {e}", file=sys.stderr)
        return False

    payload_str = None
    
    # Cari payload di output sel kode
    for cell in nb_data.get('cells', []):
        if cell.get('cell_type') == 'code':
            for output in cell.get('outputs', []):
                if output.get('output_type') == 'stream' and output.get('name') == 'stdout':
                    raw_text = output.get('text', [])
                    text = raw_text if isinstance(raw_text, str) else "".join(raw_text)
                    match = re.search(r'===REGISTRY_PAYLOAD_START===\n(.*?)\n===REGISTRY_PAYLOAD_END===', text, re.DOTALL)
                    if match:
                        payload_str = match.group(1)
                        break
        if payload_str:
            break

    if not payload_str:
        print(f"Abaikan {nb_path.name}: Tidak ada cetakan payload.")
        return False

    try:
        metadata = json.loads(payload_str)
        topic = metadata["topic"]
        exp_id = register_experiment.generate_experiment_id()

        experiment = {
            "experiment_id": exp_id,
            "topic": topic,
            "model": metadata["model"],
            "objective": metadata["objective"],
            "dataset": metadata["dataset"],
            "created_at": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
            "metrics": metadata["metrics"],
            "status": "SUCCESS",
            "owner": metadata["owner"],
            "kaggle": {"version": None, "url": None},
            "notebook": f"{exp_id}.ipynb",
            "previous_experiment": None
        }

        # 1. Validasi dan simpan JSON ke registry/
        register_experiment.validate_experiment(experiment)
        register_experiment.save_experiment(experiment)

        # 2. Pindahkan dan rename notebook ke experiments/
        dest_dir = PROJECT_ROOT / "experiments" / topic
        dest_dir.mkdir(parents=True, exist_ok=True)
        new_nb_path = dest_dir / f"{exp_id}.ipynb"
        nb_path.rename(new_nb_path)
        
        print(f"SUCCESS: Ekstrak {exp_id}, lalu dipindahkan ke {new_nb_path.relative_to(PROJECT_ROOT)}")
        return True

    except Exception as e:
        print(f"ERROR saat memproses {nb_path.name}: {e}", file=sys.stderr)
        return False

def main():
    # Pindai file .ipynb di root directory saja (tempat Kaggle membuang file).
    # sorted() agar urutan proses sama di setiap mesin/branch.
    for nb_path in sorted(PROJECT_ROOT.glob("*.ipynb")):
        process_notebook(nb_path)

if __name__ == '__main__':
    main()
