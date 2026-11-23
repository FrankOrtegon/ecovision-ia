"""Prepara el directorio y el ZIP para importar en Roboflow con las particiones ya fijadas.

Estructura (el nombre de carpeta define el split y la clase, según la documentación de Roboflow):
    roboflow_upload/{train,valid,test}/{clase}/{archivo}.jpg
"""
from __future__ import annotations

import shutil
import zipfile

import pandas as pd

from common import CLASSES, DATA_DIR, DATASET_DIR, SPLITS_DIR, write_json, RESULTS_DIR

OUT_DIR = DATA_DIR / "roboflow_upload"
ZIP_PATH = DATA_DIR / "roboflow_upload.zip"
FOLDER = {"train": "train", "val": "valid", "test": "test"}


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    counts: dict[str, dict[str, int]] = {}
    for split, folder in FOLDER.items():
        df = pd.read_csv(SPLITS_DIR / f"{split}.csv")
        counts[folder] = {c: 0 for c in CLASSES}
        for row in df.itertuples():
            dst = OUT_DIR / folder / row.label
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(DATASET_DIR / row.relpath, dst / row.filename)
            counts[folder][row.label] += 1

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_STORED) as zf:  # JPEG ya está comprimido
        for p in sorted(OUT_DIR.rglob("*.jpg")):
            zf.write(p, p.relative_to(OUT_DIR))

    write_json(RESULTS_DIR / "roboflow_upload_manifest.json", {"zip": ZIP_PATH.name, "counts": counts})
    total = sum(sum(v.values()) for v in counts.values())
    print(f"{total} imágenes en {ZIP_PATH} ({ZIP_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
