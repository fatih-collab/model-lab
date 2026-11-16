#!/usr/bin/env python3
"""
Fase 1 — MLOps: ekstraksi model dari notebook Kaggle.

File .ipynb hanya berisi KODE + output (plot/log); bobot model tersimpan terpisah di /kaggle/working.
Karena itu "ekstraksi" dibagi menjadi:

  code      Ambil fungsi pre-processing / fitur / post-processing dari sel notebook via AST (beserta
            dependensinya) -> ml/nb_generated/{undertone_nb,season_nb}.py. Kode inferensi memakai fungsi
            yang PERSIS sama dengan saat training (tidak ditulis ulang manual -> tidak ada train/serve skew).
            Notebook season v3 menulis modulnya lewat sel `%%writefile` (armo_common/prep/train/driver.py);
            baris magic dibuang sehingga isi sel itu terbaca sebagai kode biasa.
  manifest  Simpan konfigurasi, nama kelas, label 12-season, bobot ensemble & metrik yang dilaporkan
            notebook -> models/manifest.json.
  collect   Salin artefak dari folder output Kaggle (hasil `kaggle kernels output ...`) -> models/<modul>/.
  repack    Undertone: muat ulang joblib (perbaiki `__main__.SafePCA`), buang komponen berbobot 0.
            Season v3: pilih bobot convnext_t vs LightGBM, ambang 'yakin' & himpunan konformal dari prediksi
            OOF (armo_v3_hasil.joblib + meta.csv) -> models/<modul>/<modul>_bundle.joblib.
  verify    Cek artefak lengkap, bobot ensemble cocok dengan notebook, kunci & shape checkpoint benar,
            booster LightGBM terbaca, bobot pyfacer utuh, tulis models/artifacts.lock.json (sha256).
  fetch     Unduh bobot pretrained (HF: DINOv2) + detektor wajah YuNet + pyfacer (RetinaFace, FaRL LaPa).
  all       code + manifest (+ collect, repack, verify bila --src diberikan).

Contoh:
  python scripts/extract_models.py all
  kaggle kernels output <user>/<kernel-undertone> -p ~/kaggle_out/undertone
  kaggle kernels output <user>/<kernel-season>    -p ~/kaggle_out/season_v3
  python scripts/extract_models.py all --src ~/kaggle_out/undertone ~/kaggle_out/season_v3
  python scripts/extract_models.py fetch
  python scripts/extract_models.py fetch --skip-hf      # hanya YuNet + pyfacer
"""
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import sys
import warnings
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_NB_DIR = BACKEND_DIR.parent / "Model"
GEN_DIR = BACKEND_DIR / "ml" / "nb_generated"
MODELS_DIR = BACKEND_DIR / "models"
HF_CACHE_DIR = MODELS_DIR / "hf_cache"
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
             "face_detection_yunet/face_detection_yunet_2023mar.onnx")
YUNET_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
PYFACER_DIR = MODELS_DIR / "pyfacer"
# Bobot pyfacer 0.0.5 (URL bawaan facer/face_detection/retinaface.py & facer/face_parsing/farl.py), di-pin sha256.
PYFACER_FILES = {
    "mobilenet0.25_Final.pth": (
        "https://github.com/elliottzheng/face-detection/releases/download/0.0.1/mobilenet0.25_Final.pth",
        "2979b33ffafda5d74b6948cd7a5b9a7a62f62b949cef24e95fd15d2883a65220"),
    "face_parsing.farl.lapa.main_ema_136500_jit191.pt": (
        "https://github.com/FacePerceiver/facer/releases/download/models-v1/"
        "face_parsing.farl.lapa.main_ema_136500_jit191.pt",
        "f5a874906795ef89fadd7cf3b5b218ed8550fa9dbb383b7c0f95726c3a352914"),
}
SEASON_FOLDS = 5
SEASON_DEEP = "convnext_t"           # model deep yang dilayani (terbaik di OOF; ensemble 7 model terlalu lambat di CPU)
LGB_FILES = ([f"lgb_flat_f{k}.txt" for k in range(SEASON_FOLDS)]
             + [f"lgb_hier_season_f{k}.txt" for k in range(SEASON_FOLDS)]
             + [f"lgb_hier_expert{s}_f{k}.txt" for s in range(4) for k in range(SEASON_FOLDS)])
sys.path.insert(0, str(BACKEND_DIR))

# Deep Armocromia memakai nama musim berbahasa Italia.
FAMILY_EN = {"primavera": "Spring", "estate": "Summer", "autunno": "Autumn", "inverno": "Winter"}
SUBTYPE_EN = {"light": "Light", "warm": "Warm", "bright": "Bright", "soft": "Soft", "cool": "Cool", "deep": "Deep"}

SPECS = {
    "undertone": {
        "notebook": "EXP-20261008-163613-7e87.ipynb",
        "module": "undertone_nb",
        "input": "foto bagian dalam pergelangan tangan (urat)",
        "prelude": (
            "import math\n"
            "import numpy as np\n"
            "import cv2\n"
            "from PIL import Image, ImageFilter, ImageOps\n"
            "from sklearn.decomposition import PCA\n"
        ),
        "targets": [
            "CLASS_NAMES", "IMG_SIZE", "N_TTA", "CACHE_MAX", "USE_ROI_CROP", "ROI_SIZE", "MEAN", "STD",
            "srgb_to_linear", "skin_mask", "crop_roi", "segment", "color_features",
            "sharpen", "load_image", "resize_short", "center_crop", "tta_views", "SafePCA",
        ],
        "config_keys": ["CLASS_NAMES", "IMG_SIZE", "N_TTA", "CACHE_MAX", "USE_ROI_CROP", "ROI_SIZE", "MEAN", "STD"],
        "required": ["undertone_ensemble.joblib"] + [f"convnext_ft_fold{k}.pth" for k in range(5)],
        "optional": [],
        "bundle": "undertone_bundle.joblib",
        "pretrained": [{"repo": "timm/vit_small_patch14_dinov2.lvd142m", "gated": False,
                        "used_by": "svm (tuned) — fitur DINOv2 frozen"}],
    },
    "season": {
        "notebook": "armocromia_season_detection_v3.ipynb",
        "module": "season_nb",
        "input": "crop wajah -> masker organ pyfacer FaRL -> RGB-M (wajah + rambut, latar hitam) + fitur warna per organ",
        "prelude": (
            "import math\n"
            "import os\n"
            "import numpy as np\n"
            "import cv2\n"
            "import torch\n"
            "import torch.nn as nn\n"
            "import torch.nn.functional as F\n"
            "import timm\n"
        ),
        "targets": [
            "SEASONS", "SUBCLASSES", "SUB_NAMES", "NUM_SEASONS", "NUM_CLASSES", "SUB2SEASON", "WARM_SEASONS",
            "PART_ID", "N_PARTS", "PATCH", "CACHE_SIDE", "MODEL_ZOO",
            "season_probs", "hierarchical_decode", "temp_scale",
            "LAPA2ID", "heuristic_labelmap", "REGIONS", "srgb_to_lab", "region_pixels", "region_features",
            "extract_color_features", "crop_bbox", "letterbox", "gpu_aug", "HierCls",
        ],
        "config_keys": ["NUM_CLASSES", "NUM_SEASONS", "SUB_NAMES", "PART_ID", "REGIONS", "PATCH", "CACHE_SIDE",
                        "MODEL_ZOO"],
        "required": (["armo_v3_hasil.joblib", "meta.csv"] + [f"{SEASON_DEEP}_f{k}.pt" for k in range(SEASON_FOLDS)]
                     + LGB_FILES),
        "optional": ["ensemble_config.json"],
        "bundle": "season_bundle.joblib",
        "pretrained": [],                    # bobot timm ikut di checkpoint; face parsing = pyfacer (PYFACER_FILES)
    },
}


# =====================================================================================================
# Membaca notebook
# =====================================================================================================
def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def read_notebook(path: Path) -> tuple[list[str], list[str]]:
    """Kembalikan (sumber tiap sel kode, teks output tiap sel kode). Baris magic IPython (%/!) dibuang."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    sources, outputs = [], []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        src = "\n".join("" if line.lstrip().startswith(("%", "!")) else line for line in src.splitlines())
        sources.append(src)
        text = []
        for o in cell.get("outputs", []):
            t = o.get("text") or o.get("data", {}).get("text/plain")
            if t:
                text.append("".join(t) if isinstance(t, list) else t)
        outputs.append("".join(text))
    return sources, outputs


# =====================================================================================================
# Ekstraksi kode via AST (+ penutupan dependensi)
# =====================================================================================================
def _bound_names(stmt: ast.stmt) -> set[str]:
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {stmt.name}
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return {(a.asname or a.name).split(".")[0] for a in stmt.names}
    return {n.id for n in ast.walk(stmt) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}


def _free_names(stmt: ast.stmt) -> set[str]:
    loads, local = set(), set()
    for n in ast.walk(stmt):
        if isinstance(n, ast.Name):
            (loads if isinstance(n.ctx, ast.Load) else local).add(n.id)
        elif isinstance(n, ast.arg):
            local.add(n.arg)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            local.add(n.name)                       # fungsi/class bersarang
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            local |= {(a.asname or a.name).split(".")[0] for a in n.names}
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        local.discard(stmt.name)
    return loads - local


def extract_module_source(sources: list[str], targets: list[str], prelude: str, header: str) -> str:
    trees = [ast.parse(s) for s in sources]
    bindings: dict[str, list[tuple[int, int]]] = {}
    for ci, tree in enumerate(trees):
        for si, stmt in enumerate(tree.body):
            for name in _bound_names(stmt):
                bindings.setdefault(name, []).append((ci, si))

    resolved = set(dir(builtins))
    for stmt in ast.parse(prelude).body:
        resolved |= _bound_names(stmt)

    selected: set[tuple[int, int]] = set()
    queue, missing = list(targets), []
    while queue:
        name = queue.pop()
        if name in resolved:
            continue
        resolved.add(name)
        if name not in bindings:
            missing.append(name)
            continue
        # Pakai definisi dari sel TERAKHIR yang mendefinisikan nama ini (semua statement pengikatnya di sel itu,
        # mis. REGION_COLS = [] lalu beberapa `REGION_COLS += ...`).
        last_cell = bindings[name][-1][0]
        for key in (k for k in bindings[name] if k[0] == last_cell):
            if key not in selected:
                selected.add(key)
                queue.extend(_free_names(trees[key[0]].body[key[1]]))
    if missing:
        raise RuntimeError(f"Nama tidak ditemukan di notebook maupun prelude: {sorted(missing)}")

    parts = [header, prelude]
    for ci, si in sorted(selected):
        seg = ast.get_source_segment(sources[ci], trees[ci].body[si])
        parts.append(f"\n# --- sel kode #{ci} ---\n{seg}\n")
    code = "\n".join(parts)
    compile(code, "<generated>", "exec")
    return code


def import_generated(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"_gen_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_code(args) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    init = out_dir / "__init__.py"
    if not init.exists():
        init.write_text('"""Kode yang di-generate dari notebook training. Jangan diedit manual."""\n')
    for name, spec in SPECS.items():
        nb_path = Path(args.nb_dir) / spec["notebook"]
        sources, _ = read_notebook(nb_path)
        header = (
            "# AUTO-GENERATED oleh backend/scripts/extract_models.py — JANGAN DIEDIT MANUAL.\n"
            f"# Sumber : Model/{spec['notebook']}\n"
            f"# sha256 : {sha256_file(nb_path)}\n"
            f"# Input  : {spec['input']}\n"
            "# Fungsi & konstanta diambil apa adanya dari sel notebook (+ dependensinya) agar inferensi\n"
            "# identik dengan training. Regenerasi: python scripts/extract_models.py code\n"
        )
        code = extract_module_source(sources, spec["targets"], spec["prelude"], header)
        path = out_dir / f"{spec['module']}.py"
        path.write_text(code, encoding="utf-8")
        mod = import_generated(path, spec["module"])
        absent = [t for t in spec["targets"] if not hasattr(mod, t)]
        if absent:
            raise RuntimeError(f"{path.name}: target tidak terdefinisi setelah import: {absent}")
        print(f"[code] {path.relative_to(BACKEND_DIR) if path.is_relative_to(BACKEND_DIR) else path}"
              f" — {len(spec['targets'])} target, {code.count(chr(10))} baris")


# =====================================================================================================
# Manifest: konfigurasi + angka yang dilaporkan notebook
# =====================================================================================================
def _literal_after(pattern: str, text: str):
    m = re.search(pattern, text, flags=re.S)
    return ast.literal_eval(m.group(1)) if m else None


def _float_after(pattern: str, text: str):
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def parse_reported(name: str, outputs: list[str]) -> dict:
    text = "\n".join(outputs)
    reg = re.search(r"===REGISTRY_PAYLOAD_START===\s*(\{.*?\})\s*===REGISTRY_PAYLOAD_END===", text, flags=re.S)
    out = {"registry": json.loads(reg.group(1)) if reg else None}
    if name == "undertone":
        out["ensemble_weights"] = _literal_after(r"Bobot ensemble:\s*(\{.*?\})", text)
        out["test_accuracy_pct"] = _float_after(r"Test accuracy ([\d.]+)%", text)
    else:
        # Notebook v3 dijalankan di Kaggle; salinan lokal biasanya tanpa output -> nilai None. Angka yang benar-benar
        # dipakai server (temperatur, bobot, ambang, metrik) dihitung `repack` dari armo_v3_hasil.joblib.
        out["temperatures"] = _literal_after(r"Temperatur:\s*(\{.*?\})", text)
        out["family_weights_optuna"] = _literal_after(r"Bobot family \(Optuna\):\s*(\{.*?\})", text)
        m = re.search(r"METODE TERBAIK\s*:\s*(.+)", text)
        out["final_method"] = m.group(1).strip() if m else None
        out["official_test_season_acc"] = _float_after(r"OFFICIAL TEST\s*:\s*season acc ([\d.]+)", text)
    return out


def season_ids(sub_names) -> list[str]:
    """Nama kelas notebook v3 ('autunno-deep') -> id kelas backend ('autunno_deep'); urutan dipertahankan."""
    return [str(n).replace("-", "_") for n in sub_names]


def season_label_table(class_names: list[str]) -> dict:
    table = {}
    for c in class_names:
        fam, sub = c.split("_", 1)
        table[c] = {"name": f"{SUBTYPE_EN[sub]} {FAMILY_EN[fam]}", "family": FAMILY_EN[fam], "subtype": sub,
                    "undertone": "warm" if fam in ("primavera", "autunno") else "cool"}
    return table


def cmd_manifest(args) -> None:
    manifest = {"generated_by": "backend/scripts/extract_models.py", "modules": {}}
    for name, spec in SPECS.items():
        nb_path = Path(args.nb_dir) / spec["notebook"]
        _, outputs = read_notebook(nb_path)
        gen_path = Path(args.out_dir) / f"{spec['module']}.py"
        if not gen_path.exists():
            raise FileNotFoundError(f"{gen_path} belum ada. Jalankan perintah `code` dulu.")
        mod = import_generated(gen_path, spec["module"])
        reported = parse_reported(name, outputs)
        entry = {
            "notebook": spec["notebook"], "notebook_sha256": sha256_file(nb_path), "input": spec["input"],
            "generated_module": f"ml.nb_generated.{spec['module']}",
            "config": {k: getattr(mod, k) for k in spec["config_keys"]},
            "reported": reported,
            "artifacts": {"dir": f"models/{name}", "required": spec["required"], "optional": spec["optional"],
                          "bundle": spec["bundle"]},
            "pretrained": spec["pretrained"],
        }
        if name == "undertone":
            entry["class_names"] = list(mod.CLASS_NAMES)
        else:
            entry["class_names"] = season_ids(mod.SUB_NAMES)
            entry["labels"] = season_label_table(entry["class_names"])
            entry["serving"] = {"deep": SEASON_DEEP, "folds": SEASON_FOLDS, "lgb": ["lgb_flat", "lgb_hier"],
                                "face_parser": "pyfacer retinaface/mobilenet + farl/lapa/448",
                                "pyfacer_files": sorted(PYFACER_FILES)}
        manifest["modules"][name] = entry
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=list), encoding="utf-8")
    print(f"[manifest] {path.relative_to(BACKEND_DIR)}")
    for name, e in manifest["modules"].items():
        extra = (f"bobot ensemble notebook={e['reported']['ensemble_weights']}" if name == "undertone"
                 else f"dilayani={e['serving']['deep']} + {'/'.join(e['serving']['lgb'])}")
        print(f"   {name:9s} kelas={len(e['class_names'])} | {extra}")


def load_manifest() -> dict:
    path = MODELS_DIR / "manifest.json"
    if not path.exists():
        raise FileNotFoundError("models/manifest.json belum ada. Jalankan `manifest` dulu.")
    return json.loads(path.read_text(encoding="utf-8"))


# =====================================================================================================
# Artefak: collect, repack, verify
# =====================================================================================================
def cmd_collect(args) -> None:
    srcs = [Path(s).expanduser() for s in args.src]
    for s in srcs:
        if not s.is_dir():
            raise NotADirectoryError(s)
    for name, spec in SPECS.items():
        dest = MODELS_DIR / name
        dest.mkdir(parents=True, exist_ok=True)
        for fname in spec["required"] + spec["optional"]:
            hits = sorted((p for s in srcs for p in s.rglob(fname)), key=lambda p: p.stat().st_mtime)
            if not hits:
                print(f"[collect] {'HILANG' if fname in spec['required'] else 'tidak ada (opsional)'}: {name}/{fname}")
                continue
            if len(hits) > 1:
                print(f"[collect] {fname}: {len(hits)} salinan, dipakai yang terbaru: {hits[-1]}")
            how = _link_or_copy(hits[-1], dest / fname)
            print(f"[collect] {name}/{fname} <- {hits[-1]} ({how})")


def _link_or_copy(src: Path, dst: Path) -> str:
    """Hardlink bila satu partisi (artefak read-only, tidak memakan ruang disk lagi), selain itu salin."""
    if dst.exists() or dst.is_symlink():
        if dst.exists() and os.path.samefile(src, dst):
            return "sudah sama"
        dst.unlink()
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "salin"


def _load_joblib_quiet(path: Path):
    from ml.compat import load_notebook_joblib
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        obj = load_notebook_joblib(path)
    for w in caught:
        if "version" in str(w.message).lower():
            print(f"   PERINGATAN versi ({path.name}): {str(w.message)[:220]}")
    return obj


def _weights_match(actual: dict, reported: dict | None, tol: float = 2e-3) -> bool:
    if not reported:
        return True
    keys = {k for k, v in {**actual, **reported}.items() if v > tol}
    return all(abs(actual.get(k, 0.0) - reported.get(k, 0.0)) <= tol for k in keys)


def cmd_repack(args) -> None:
    import joblib

    manifest = load_manifest()["modules"]

    # ---- Undertone: buang komponen berbobot 0, pickle ulang (SafePCA -> ml.nb_generated.undertone_nb)
    src = MODELS_DIR / "undertone" / "undertone_ensemble.joblib"
    if src.exists():
        raw = _load_joblib_quiet(src)
        weights = {k: float(w) for k, w in raw["weights"].items() if w >= 1e-3}
        n_folds = len(SPECS["undertone"]["required"]) - 1
        bundle = {
            **raw,
            "weights": weights,
            "models": {k: m for k, m in raw["models"].items() if k in weights},
            "ft_arch": "convnext_tiny",
            "ft_ckpts": [f"convnext_ft_fold{k}.pth" for k in range(n_folds)] if "convnext_finetune" in weights else [],
            "source": {"file": src.name, "sha256": sha256_file(src)},
        }
        dst = MODELS_DIR / "undertone" / SPECS["undertone"]["bundle"]
        joblib.dump(bundle, dst)
        print(f"[repack] {dst.relative_to(BACKEND_DIR)} | komponen aktif: {weights}")
    else:
        print(f"[repack] dilewati: {src.relative_to(BACKEND_DIR)} tidak ada")

    # ---- Season v3: convnext_t + LightGBM, bobot & kalibrasi dari prediksi OOF.
    src, meta_path = MODELS_DIR / "season" / "armo_v3_hasil.joblib", MODELS_DIR / "season" / "meta.csv"
    if src.exists() and meta_path.exists():
        import pandas as pd

        raw = _load_joblib_quiet(src)
        bundle = build_season_bundle(raw, pd.read_csv(meta_path), manifest["season"])
        bundle["source"] = {"file": src.name, "sha256": sha256_file(src), "meta_sha256": sha256_file(meta_path)}
        dst = MODELS_DIR / "season" / SPECS["season"]["bundle"]
        joblib.dump(bundle, dst)
        m = bundle["metrics"]
        print(f"[repack] {dst.relative_to(BACKEND_DIR)} | {bundle['deep']['tag']} {bundle['weights']['deep']:.2f} + "
              f"LightGBM {bundle['weights']['lgb']:.2f} | ambang 'yakin'={bundle['conf_high']:.4f} | "
              f"qhat={bundle['conformal_qhat']}")
        print(f"   TEST season acc: dilayani={m['test']['served']['season_acc']:.4f} | "
              f"{bundle['deep']['tag']} saja={m['test']['deep']['season_acc']:.4f} | "
              f"LightGBM saja={m['test']['lgb']['season_acc']:.4f} | "
              f"ensemble resmi notebook (7 model)={m['official_test'].get('season_acc', float('nan')):.4f}")
    else:
        print(f"[repack] dilewati: {src.relative_to(BACKEND_DIR)} atau meta.csv tidak ada")


# Ambang 'yakin' & konformal: aturan yang sama dengan notebook season sebelumnya (sel 8.3), dihitung pada OOF
# subset CelebA. Prediksi berlabel 'yakin' bila akurasinya >= 50% dan mencakup >= 5% gambar.
TARGET_SELECTIVE_ACC, MIN_SELECTIVE_COVERAGE, CONFORMAL_ALPHAS = 0.50, 0.05, (0.10, 0.20)


def _season_decision(p):
    """Keputusan hierarkis (season dulu, lalu sub-season) — sama dengan notebook dan app/rules_engine.family_first."""
    from ml.nb_generated import season_nb as snb

    return snb.hierarchical_decode(p)[1]


def _season_metrics(y, p) -> dict:
    from sklearn.metrics import f1_score
    from ml.nb_generated import season_nb as snb

    sub = _season_decision(p)
    return {"season_acc": float((snb.SUB2SEASON[sub] == snb.SUB2SEASON[y]).mean()),
            "sub_acc": float((sub == y).mean()),
            "sub_f1": float(f1_score(y, sub, average="macro", labels=list(range(snb.NUM_CLASSES)), zero_division=0))}


def _selective_threshold(correct, conf, target, min_cov):
    order = np.argsort(-conf, kind="stable")
    k = np.arange(1, len(conf) + 1)
    cov, acc = k / len(conf), np.cumsum(correct[order].astype(float)) / k
    ok = np.where((acc >= target) & (cov >= min_cov))[0]
    return (float(conf[order][ok.max()]), float(cov[ok.max()])) if len(ok) else (1.01, 0.0)


def _conformal_qhat(y, p, alpha):
    s = 1.0 - p[np.arange(len(y)), y]
    n = len(s)
    return float(np.quantile(s, min(1.0, math.ceil((n + 1) * (1 - alpha)) / n), method="higher"))


def build_season_bundle(raw: dict, meta, manifest_season: dict, deep: str = SEASON_DEEP, step: float = 0.05) -> dict:
    """Bundle siap-layani dari armo_v3_hasil.joblib + meta.csv:
    P = w * T(deep) + (1-w) * mean(T(lgb_flat), T(lgb_hier)); w dipilih dari OOF dengan kriteria notebook
    (sub-season macro F1, keputusan hierarkis), lalu ambang 'yakin' + qhat konformal dari OOF subset CelebA.
    Test hanya dilaporkan, tidak dipakai memilih."""
    from ml.nb_generated import season_nb as snb

    class_names = season_ids(raw["class_names"])
    if class_names != manifest_season["class_names"]:
        raise ValueError(f"season: class_names joblib {class_names} != manifest {manifest_season['class_names']}")
    tr, te = (meta.partition == "train").values, (meta.partition != "train").values
    y_tr, y_te = meta.y_sub.values[tr], meta.y_sub.values[te]
    celeba = meta.celeba.astype(str).str.lower().eq("true").values[tr]
    if len(raw["pred_oof"][deep]) != len(y_tr) or not np.array_equal(np.asarray(raw["y_te"]), y_te):
        raise ValueError("season: meta.csv tidak cocok dengan armo_v3_hasil.joblib (run Kaggle berbeda?)")
    missing = [t for t in (deep, "lgb_flat", "lgb_hier") if t not in raw["models"]]
    if missing or "lgb_models" not in raw:
        raise ValueError(f"season: joblib tidak memuat {missing or 'lgb_models'} — jalankan notebook v3 terbaru")

    T = {t: float(raw["temps"][t]) for t in (deep, "lgb_flat", "lgb_hier")}
    cal = {t: (snb.temp_scale(np.asarray(raw["pred_oof"][t]), T[t]), snb.temp_scale(np.asarray(raw["pred_test"][t]), T[t]))
           for t in T}
    lgb = tuple((cal["lgb_flat"][i] + cal["lgb_hier"][i]) / 2 for i in (0, 1))
    grid = np.round(np.arange(0.0, 1.0 + 1e-9, step), 4)
    scores = [(_season_metrics(y_tr, w * cal[deep][0] + (1 - w) * lgb[0])["sub_f1"], w) for w in grid]
    w = float(max(scores)[1])
    P_oof, P_te = w * cal[deep][0] + (1 - w) * lgb[0], w * cal[deep][1] + (1 - w) * lgb[1]

    pc, yc = P_oof[celeba], y_tr[celeba]
    top = _season_decision(pc)
    conf_high, coverage = _selective_threshold(top == yc, pc[np.arange(len(pc)), top], TARGET_SELECTIVE_ACC,
                                               MIN_SELECTIVE_COVERAGE)
    qhat = {a: _conformal_qhat(yc, pc, a) for a in CONFORMAL_ALPHAS}

    zoo = raw["model_zoo"][deep]
    base = lambda p: str(p).replace("\\", "/").rsplit("/", 1)[-1]
    return {
        "class_names": class_names, "labels": manifest_season["labels"],
        "warm_of": np.array([int(manifest_season["labels"][c]["undertone"] == "warm") for c in class_names]),
        "deep": {"tag": deep, "kind": zoo["kind"], "backbone": zoo["backbone"], "img_size": int(zoo["img_size"]),
                 "ckpts": [f"{deep}_f{k}.pt" for k in range(len(raw["deep_ckpts"][deep]))]},
        "lgb": {"flat": [base(f) for fold in raw["lgb_models"]["lgb_flat"] for f in fold],
                "hier": [[base(f) for f in fold] for fold in raw["lgb_models"]["lgb_hier"]],
                "feature_cols": list(raw["lgb_feature_cols"]),
                "hier_kids": {int(s): [int(c) for c in kids] for s, kids in raw["lgb_hier_kids"].items()}},
        "cache_side": int(snb.CACHE_SIDE), "temps": T, "weights": {"deep": w, "lgb": round(1.0 - w, 4)},
        "conf_high": conf_high, "conf_high_coverage": coverage, "conformal_qhat": qhat,
        "metrics": {
            "oof": {"served": _season_metrics(y_tr, P_oof), "deep": _season_metrics(y_tr, cal[deep][0]),
                    "lgb": _season_metrics(y_tr, lgb[0])},
            "test": {"served": _season_metrics(y_te, P_te), "deep": _season_metrics(y_te, cal[deep][1]),
                     "lgb": _season_metrics(y_te, lgb[1])},
            "official_test": {k: float(v) for k, v in raw.get("official_test_metrics", {}).items()},
            "official_method": raw.get("final_name"), "weight_grid_oof_sub_f1": {float(g): float(s) for s, g in scores},
        },
    }


def _check_ckpt(path: Path, expect: dict[str, tuple], prefix: str | None = None) -> list[str]:
    import torch

    errors = []
    sd = torch.load(path, map_location="cpu", weights_only=True)
    if isinstance(sd, dict) and "state_dict" in sd:
        sd = sd["state_dict"]
    for key, shape in expect.items():
        if key not in sd:
            errors.append(f"{path.name}: kunci '{key}' tidak ada")
        elif tuple(sd[key].shape) != shape:
            errors.append(f"{path.name}: shape {key} = {tuple(sd[key].shape)}, seharusnya {shape}")
    if prefix and not any(k.startswith(prefix) for k in sd):
        errors.append(f"{path.name}: tidak ada parameter berawalan '{prefix}'")
    return errors


def verify_season_bundle(b: dict, d: Path, manifest_season: dict) -> list[str]:
    """Bundle season v3 konsisten dengan manifest, checkpoint HierCls & booster LightGBM terbaca dengan bentuk benar."""
    import lightgbm as lgb
    import timm

    errors = []
    n_cls = len(manifest_season["class_names"])
    if list(b["class_names"]) != manifest_season["class_names"]:
        errors.append(f"season: class_names {b['class_names']} != manifest")
    if abs(b["weights"]["deep"] + b["weights"]["lgb"] - 1) > 1e-3:
        errors.append(f"season: bobot {b['weights']} tidak berjumlah 1")
    n_feat = timm.create_model(b["deep"]["backbone"], pretrained=False, num_classes=0).num_features
    for name in b["deep"]["ckpts"]:
        p = d / name
        if p.exists():
            errors += [f"season: {e}" for e in _check_ckpt(p, {"head_sub.weight": (n_cls, n_feat),
                                                                "head_season.weight": (4, n_feat)}, prefix="backbone.")]
    n_cols, kids = len(b["lgb"]["feature_cols"]), b["lgb"]["hier_kids"]
    expect = [(f, n_cls) for f in b["lgb"]["flat"]]
    for fold in b["lgb"]["hier"]:
        expect += [(fold[0], len(kids))] + [(f, len(kids[s])) for s, f in enumerate(fold[1:])]
    for fname, n_out in expect:
        p = d / fname
        if not p.exists():
            continue                                            # sudah dilaporkan sebagai file hilang
        booster = lgb.Booster(model_file=str(p))
        if booster.num_feature() != n_cols:
            errors.append(f"season: {fname} memakai {booster.num_feature()} fitur, bundle {n_cols}")
        if booster.num_model_per_iteration() != n_out:
            errors.append(f"season: {fname} keluaran {booster.num_model_per_iteration()} kelas, seharusnya {n_out}")
    return errors


def cmd_verify(args) -> int:
    manifest = load_manifest()["modules"]
    errors, lock = [], {}

    for name, spec in SPECS.items():
        d = MODELS_DIR / name
        for fname in spec["required"] + spec["optional"] + [spec["bundle"]]:
            p = d / fname
            if p.exists():
                lock[f"{name}/{fname}"] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            elif fname in spec["required"]:
                errors.append(f"{name}/{fname} tidak ada")

    # ---- Undertone
    d = MODELS_DIR / "undertone"
    bpath = d / SPECS["undertone"]["bundle"]
    bpath = bpath if bpath.exists() else d / "undertone_ensemble.joblib"
    if bpath.exists():
        b = _load_joblib_quiet(bpath)
        if list(b["class_names"]) != manifest["undertone"]["class_names"]:
            errors.append(f"undertone: class_names {b['class_names']} != manifest")
        w = {k: float(v) for k, v in b["weights"].items()}
        if not _weights_match(w, manifest["undertone"]["reported"]["ensemble_weights"]):
            errors.append(f"undertone: bobot ensemble {w} != notebook {manifest['undertone']['reported']['ensemble_weights']} "
                          "(artefak dari run yang berbeda?)")
        missing_models = [k for k in w if k != "convnext_finetune" and k not in b["models"]]
        if missing_models:
            errors.append(f"undertone: model sklearn tidak ada di bundle: {missing_models}")
        print(f"[verify] undertone bundle OK: {bpath.name} | {w}")
    for k in range(5):
        p = d / f"convnext_ft_fold{k}.pth"
        if p.exists():
            errors += _check_ckpt(p, {"classifier.2.1.weight": (3, 768), "classifier.2.1.bias": (3,)})

    # ---- Season v3
    d = MODELS_DIR / "season"
    bpath = d / SPECS["season"]["bundle"]
    if bpath.exists():
        b = _load_joblib_quiet(bpath)
        errors += verify_season_bundle(b, d, manifest["season"])
        if not any(e.startswith("season") for e in errors):
            print(f"[verify] season bundle OK: {bpath.name} | {b['deep']['tag']} {b['weights']['deep']:.2f} + "
                  f"LightGBM {b['weights']['lgb']:.2f} | {len(b['deep']['ckpts'])} fold deep, "
                  f"{len(b['lgb']['flat'])} fold LightGBM, {len(b['lgb']['feature_cols'])} fitur warna")
    else:
        errors.append(f"season/{bpath.name} tidak ada — jalankan `repack`")

    # ---- pyfacer (face parsing modul season)
    for fname, (_, sha) in PYFACER_FILES.items():
        p = PYFACER_DIR / fname
        if not p.exists():
            errors.append(f"pyfacer/{fname} tidak ada — jalankan `fetch`")
            continue
        actual = sha256_file(p)
        lock[f"pyfacer/{fname}"] = {"sha256": actual, "bytes": p.stat().st_size}
        if actual != sha:
            errors.append(f"pyfacer/{fname}: sha256 {actual[:12]}… != {sha[:12]}… (unduhan rusak?)")

    (MODELS_DIR / "artifacts.lock.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    if errors:
        print("\n[verify] GAGAL:")
        for e in errors:
            print("   -", e)
        return 1
    print(f"\n[verify] SEMUA OK — {len(lock)} file tercatat di models/artifacts.lock.json")
    return 0


# =====================================================================================================
# Bobot pretrained
# =====================================================================================================
def fetch_pyfacer() -> bool:
    """Unduh bobot pyfacer ke models/pyfacer/ (sekali, ±650 MB) dan cek sha256. Kembalikan True bila ada yang gagal."""
    import urllib.request

    PYFACER_DIR.mkdir(parents=True, exist_ok=True)
    failed = False
    for fname, (url, sha) in PYFACER_FILES.items():
        dst = PYFACER_DIR / fname
        if dst.exists() and sha256_file(dst) == sha:
            print(f"[fetch] pyfacer/{fname} sudah ada (sha256 cocok)")
            continue
        tmp = dst.with_suffix(dst.suffix + ".part")
        try:
            print(f"[fetch] mengunduh {url}")
            urllib.request.urlretrieve(url, tmp)
            actual = sha256_file(tmp)
            if actual != sha:
                raise ValueError(f"sha256 {actual} != {sha}")
            tmp.replace(dst)
            print(f"[fetch] pyfacer/{fname} -> {dst.relative_to(BACKEND_DIR)}")
        except Exception as e:
            failed = True
            tmp.unlink(missing_ok=True)
            print(f"[fetch] GAGAL pyfacer/{fname}: {type(e).__name__}: {str(e)[:200]}")
    return failed


def cmd_fetch(args) -> int:
    from huggingface_hub import snapshot_download

    token = os.environ.get("HF_TOKEN")
    resolved, failed = {}, False
    for spec in ([] if args.skip_hf else SPECS.values()):
        for item in spec["pretrained"]:
            repo = item["repo"]
            try:
                path = snapshot_download(repo, cache_dir=str(HF_CACHE_DIR / "hub"), token=token,
                                         allow_patterns=["*.json", "*.safetensors", "*.txt"])
                resolved[repo] = str(Path(path).relative_to(BACKEND_DIR))
                print(f"[fetch] {repo} -> {resolved[repo]}")
            except Exception as e:
                failed = True
                hint = (" | repo ini GATED: setujui lisensinya di huggingface.co lalu set HF_TOKEN"
                        if item["gated"] else "")
                print(f"[fetch] GAGAL {repo}: {type(e).__name__}: {str(e)[:200]}{hint}")
    if not YUNET_PATH.exists():
        import urllib.request
        try:
            urllib.request.urlretrieve(YUNET_URL, YUNET_PATH)
            print(f"[fetch] YuNet -> {YUNET_PATH.relative_to(BACKEND_DIR)}")
        except Exception as e:
            failed = True
            print(f"[fetch] GAGAL YuNet ({e}); preprocess akan memakai Haar cascade sebagai fallback.")
    failed |= fetch_pyfacer()
    if not args.skip_hf:
        (MODELS_DIR / "pretrained.json").write_text(json.dumps(resolved, indent=2), encoding="utf-8")
    return 1 if failed else 0


# =====================================================================================================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["code", "manifest", "collect", "repack", "verify", "fetch", "all"])
    ap.add_argument("--nb-dir", default=str(DEFAULT_NB_DIR), help="folder berisi .ipynb (default: ../Model)")
    ap.add_argument("--out-dir", default=str(GEN_DIR), help="folder output kode hasil generate")
    ap.add_argument("--src", nargs="+", default=[], help="folder output Kaggle berisi artefak model")
    ap.add_argument("--skip-hf", action="store_true", help="fetch: hanya unduh detektor wajah YuNet")
    args = ap.parse_args(argv)

    if args.command == "code":
        cmd_code(args)
    elif args.command == "manifest":
        cmd_manifest(args)
    elif args.command == "collect":
        if not args.src:
            ap.error("collect butuh --src")
        cmd_collect(args)
    elif args.command == "repack":
        cmd_repack(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "fetch":
        return cmd_fetch(args)
    elif args.command == "all":
        cmd_code(args)
        cmd_manifest(args)
        if args.src:
            cmd_collect(args)
            cmd_repack(args)
            return cmd_verify(args)
        print("\n(Lewati collect/repack/verify: berikan --src <folder output Kaggle> untuk memproses artefak.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
