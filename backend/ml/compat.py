"""
Kompatibilitas unpickle artefak notebook.

Class yang didefinisikan di sel notebook (mis. `SafePCA`) ter-pickle sebagai `__main__.SafePCA`.
Saat dimuat di luar notebook (uvicorn, pytest, script), `__main__` adalah modul lain sehingga unpickle gagal.
Fungsi di sini memasang class tersebut ke `__main__` sebelum `joblib.load`. Setelah `extract_models.py repack`,
pickle merujuk ke `ml.nb_generated.undertone_nb.SafePCA` sehingga shim ini tidak lagi diperlukan.
"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib

NOTEBOOK_CLASSES = {"SafePCA": "ml.nb_generated.undertone_nb"}


def register_notebook_classes() -> None:
    import importlib

    main = sys.modules["__main__"]
    for name, module in NOTEBOOK_CLASSES.items():
        if not hasattr(main, name):
            setattr(main, name, getattr(importlib.import_module(module), name))


def load_notebook_joblib(path: str | Path):
    register_notebook_classes()
    return joblib.load(path)
