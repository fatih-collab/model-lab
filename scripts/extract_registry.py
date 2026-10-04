import json
import re
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import register_experiment

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def process_notebook(nb_path: Path) -> bool:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb_data = json.load(f)

    payload_str = None
    
    # Cari cetakan payload di dalam output sel kode
    for cell in nb_data.get('cells', []):
        if cell.get('cell_type') == 'code':
            for output in cell.get('outputs', []):
                if output.get('output_type') == 'stream' and output.get('name') == 'stdout':
                    text = "".join(output.get('text', []))
                    match = re.search(r'===REGISTRY_PAYLOAD_START===\n(.*?)\n===REGISTRY_PAYLOAD_END===', text, re.DOTALL)
                    if match:
                        payload_str = match.group(1)
                        break
        if payload_str:
            break

    if not payload_str:
        print(f"Skipping {nb_path.name}: Tidak ada cetakan registry payload.")
        return False

    try:
        metadata = json.loads(payload_str)
        exp_id = register_experiment.generate_experiment_id()

        experiment = {
            "experiment_id": exp_id,
            "topic": metadata["topic"],
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

        # Validasi dan simpan menggunakan source of truth
        register_experiment.validate_experiment(experiment)
        register_experiment.save_experiment(experiment)

        # Ubah nama notebook menyesuaikan Experiment ID
        new_nb_path = nb_path.parent / f"{exp_id}.ipynb"
        nb_path.rename(new_nb_path)
        
        print(f"SUCCESS: Diekstrak {exp_id} dari {nb_path.name}")
        return True

    except Exception as e:
        print(f"ERROR memproses {nb_path.name}: {e}", file=sys.stderr)
        return False

def main():
    # Loop semua file .ipynb di folder experiments yang belum berformat EXP-
    for topic in ['topic-a', 'topic-b']:
        topic_dir = PROJECT_ROOT / 'experiments' / topic
        if not topic_dir.exists():
            continue
            
        for nb_path in topic_dir.glob("*.ipynb"):
            if not nb_path.name.startswith("EXP-"):
                process_notebook(nb_path)

if __name__ == '__main__':
    main()
