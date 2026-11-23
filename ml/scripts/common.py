"""Constantes y utilidades compartidas por los scripts de datos."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SEED = 42
CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

ML_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ML_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DATASET_DIR = RAW_DIR / "dataset-resized"
RESULTS_DIR = ML_DIR / "results"
SPLITS_DIR = RESULTS_DIR / "splits"
FIGURES_DIR = RESULTS_DIR / "figures"


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def list_images() -> list[tuple[str, Path]]:
    """Devuelve (clase, ruta) de todas las imágenes del dataset, ordenadas."""
    items: list[tuple[str, Path]] = []
    for cls in CLASSES:
        for p in sorted((DATASET_DIR / cls).glob("*")):
            if p.is_file() and not p.name.startswith("."):
                items.append((cls, p))
    return items
