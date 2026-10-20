#!/usr/bin/env python3
"""
Fase 1 — MLOps: ekstraksi model dari notebook Kaggle.

File .ipynb hanya berisi KODE + output (plot/log); bobot model tersimpan terpisah di /kaggle/working.
Karena itu "ekstraksi" dibagi menjadi:

  code      Ambil fungsi pre-processing / fitur / post-processing dari sel notebook via AST (beserta
            dependensinya) -> ml/nb_generated/{undertone_nb,season_nb}.py. Kode inferensi memakai fungsi
            yang PERSIS sama dengan saat training (tidak ditulis ulang manual -> tidak ada train/serve skew).
  manifest  Simpan konfigurasi, nama kelas, label 12-season, bobot ensemble & metrik yang dilaporkan
            notebook -> models/manifest.json.
  collect   Salin artefak dari folder output Kaggle (hasil `kaggle kernels output ...`) -> models/<modul>/.
  repack    Muat ulang joblib (perbaiki referensi `__main__.SafePCA`), buang komponen berbobot 0
            -> models/<modul>/<modul>_bundle.joblib.
  verify    Cek artefak lengkap, bobot ensemble cocok dengan notebook, kunci & shape checkpoint benar,
            tulis models/artifacts.lock.json (sha256).
  fetch     Unduh bobot pretrained (HF: DINOv2, DINOv3, SegFormer face-parsing) + detektor wajah YuNet.
  all       code + manifest (+ collect, repack, verify bila --src diberikan).

Contoh:
  python scripts/extract_models.py all
  kaggle kernels output <user>/<kernel-undertone> -p ~/kaggle_out/undertone
  kaggle kernels output <user>/<kernel-season>    -p ~/kaggle_out/season
  python scripts/extract_models.py all --src ~/kaggle_out/undertone ~/kaggle_out/season
  HF_TOKEN=hf_xxx python scripts/extract_models.py fetch
  python scripts/extract_models.py fetch --skip-hf      # hanya YuNet
"""
from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import warnings
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_NB_DIR = BACKEND_DIR.parent / "Model"
GEN_DIR = BACKEND_DIR / "ml" / "nb_generated"
MODELS_DIR = BACKEND_DIR / "models"
HF_CACHE_DIR = MODELS_DIR / "hf_cache"
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
             "face_detection_yunet/face_detection_yunet_2023mar.onnx")
YUNET_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
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
        "notebook": "EXP-20261012-191927-3fc3.ipynb",
        "module": "season_nb",
        "input": "foto wajah + rambut, latar dihitamkan (format RGB-M Deep Armocromia)",
        "prelude": (
            "import numpy as np\n"
            "from PIL import Image, ImageOps\n"
        ),
        "targets": [
            "NUM_CLASSES", "NUM_SEASONS", "WARM_SEASONS", "BACKBONE_HF_ID", "PARSER_HF_ID",
            "PARSE_SIZE", "CACHE_SIZE", "MASK_THRESH", "EMB_IMG_SIZE", "FT_IMG_SIZE", "EXTRA_MEAN_LAYERS",
            "FT_DROPOUT", "IMNET_MEAN", "IMNET_STD",
            "rgb2lab_np", "REGION_PARTS", "REGION_MIN_PIX", "REGION_COLS", "COL_IX",
            "region_color_features", "load_squares",
            "apply_temperature", "pool", "proba_full", "stack_features", "final_predict", "conformal_sets",
        ],
        "config_keys": ["NUM_CLASSES", "NUM_SEASONS", "BACKBONE_HF_ID", "PARSER_HF_ID", "PARSE_SIZE", "CACHE_SIZE",
                        "MASK_THRESH", "EMB_IMG_SIZE", "FT_IMG_SIZE", "EXTRA_MEAN_LAYERS", "FT_DROPOUT",
                        "IMNET_MEAN", "IMNET_STD"],
        "required": ["E12_artifacts.joblib"] + [f"ft_s42_f{k}.pt" for k in range(5)],
        "optional": ["E12_summary.json"],
        "bundle": "season_bundle.joblib",
        "pretrained": [{"repo": "facebook/dinov3-vits16-pretrain-lvd1689m", "gated": True,
                        "used_by": "emb_lr (frozen) + arsitektur ArmoNet (ft)"},
                       {"repo": "jonathandinu/face-parsing", "gated": False,
                        "used_by": "SegFormer face parsing (mask wajah + fitur warna per region)"}],
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
        out["class_names"] = _literal_after(r"Kelas\s*:\s*(\[.*?\])", text)
        out["char_names"] = _literal_after(r"Karakteristik\s*:\s*(\[.*?\])", text)
        out["component_temperatures"] = _literal_after(r"Temperature per komponen:\s*(\{.*?\})", text)
        out["ensemble_weights"] = _literal_after(r"Bobot ensemble:\s*(\{.*?\})", text)
        out["ensemble_temperature"] = _float_after(r"Temperature ensemble T = ([\d.]+)", text)
        out["conf_high"] = _float_after(r"Ambang 'yakin' = ([\d.]+)", text)
        m = re.search(r"METODE AKHIR: (\w+)", text)
        out["final_method"] = m.group(1) if m else None
    return out


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
            entry["class_names"] = reported["class_names"]
            entry["labels"] = season_label_table(reported["class_names"])
            entry["region_cols"] = list(mod.REGION_COLS)
        manifest["modules"][name] = entry
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=list), encoding="utf-8")
    print(f"[manifest] {path.relative_to(BACKEND_DIR)}")
    for name, e in manifest["modules"].items():
        print(f"   {name:9s} kelas={len(e['class_names'])} | bobot ensemble notebook={e['reported']['ensemble_weights']}")


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
            shutil.copy2(hits[-1], dest / fname)
            print(f"[collect] {name}/{fname} <- {hits[-1]}")


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

    # ---- Season: komponen berbobot 0 (mis. emb_lr_orig) tidak menyumbang ke pooling log-linear,
    #      jadi aman dibuang -> foto RGB asli tidak lagi diperlukan saat inferensi.
    src = MODELS_DIR / "season" / "E12_artifacts.joblib"
    if src.exists():
        raw = _load_joblib_quiet(src)
        bundle = dict(raw)
        if raw["method"] == "ensemble":
            keep = [(n, float(w)) for n, w in zip(raw["comp_names"], raw["ens_weights"]) if w > 0]
            bundle["comp_names"] = [n for n, _ in keep]
            bundle["ens_weights"] = tuple(w for _, w in keep)
            bundle["models"] = {k: m for k, m in raw["models"].items() if k in bundle["comp_names"]}
        else:
            print("[repack] season memakai xgb_stack: semua komponen dipertahankan (stacker butuh semuanya).")
        bundle["labels"] = manifest["season"]["labels"]
        bundle["source"] = {"file": src.name, "sha256": sha256_file(src)}
        dst = MODELS_DIR / "season" / SPECS["season"]["bundle"]
        joblib.dump(bundle, dst)
        print(f"[repack] {dst.relative_to(BACKEND_DIR)} | metode={bundle['method']} | komponen aktif: "
              f"{dict(zip(bundle['comp_names'], bundle['ens_weights']))}")
    else:
        print(f"[repack] dilewati: {src.relative_to(BACKEND_DIR)} tidak ada")


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

    # ---- Season
    d = MODELS_DIR / "season"
    bpath = d / SPECS["season"]["bundle"]
    bpath = bpath if bpath.exists() else d / "E12_artifacts.joblib"
    if bpath.exists():
        b = _load_joblib_quiet(bpath)
        if list(b["class_names"]) != manifest["season"]["class_names"]:
            errors.append(f"season: class_names {b['class_names']} != manifest")
        w = dict(zip(b["comp_names"], map(float, b["ens_weights"])))
        if b["method"] == "ensemble" and not _weights_match(w, manifest["season"]["reported"]["ensemble_weights"]):
            errors.append(f"season: bobot ensemble {w} != notebook {manifest['season']['reported']['ensemble_weights']}")
        rep_t = manifest["season"]["reported"]["ensemble_temperature"]
        if b["method"] == "ensemble" and rep_t and abs(float(b["temperature"]) - rep_t) > 2e-3:
            errors.append(f"season: temperature {b['temperature']:.4f} != notebook {rep_t}")
        need = [n for n in b["comp_names"] if n != "ft" and n not in b["models"]]
        if need:
            errors.append(f"season: model komponen tidak ada di bundle: {need}")
        print(f"[verify] season bundle OK: {bpath.name} | metode={b['method']} | {w} | T={float(b['temperature']):.3f}")
    n_cls, d2 = len(manifest["season"]["class_names"]), 2 * 384      # head memakai concat(CLS, mean patch)
    for k in range(5):
        p = d / f"ft_s42_f{k}.pt"
        if p.exists():
            errors += _check_ckpt(p, {"head12.weight": (n_cls, d2), "headS.weight": (4, d2),
                                      "headC.weight": (6, d2), "headU.weight": (2, d2)}, prefix="backbone.")

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
