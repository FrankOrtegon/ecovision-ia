"""Descarga TrashNet (dataset-resized.zip) y registra su procedencia."""
from __future__ import annotations

import datetime as dt
import zipfile

import requests

from common import DATASET_DIR, RAW_DIR, RESULTS_DIR, sha256_file, write_json

URL = "https://raw.githubusercontent.com/garythung/trashnet/master/data/dataset-resized.zip"
REPO = "https://github.com/garythung/trashnet"
ZIP_PATH = RAW_DIR / "dataset-resized.zip"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not ZIP_PATH.exists():
        print(f"Descargando {URL}")
        with requests.get(URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            with ZIP_PATH.open("wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    else:
        print("ZIP ya existe, se reutiliza.")

    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"ZIP corrupto, primer archivo dañado: {bad}")
        for member in zf.namelist():
            if member.startswith("__MACOSX") or ".." in member:
                continue
            zf.extract(member, RAW_DIR)

    if not DATASET_DIR.is_dir():
        raise RuntimeError(f"No se encontró {DATASET_DIR} tras extraer")

    write_json(
        RESULTS_DIR / "dataset_source.json",
        {
            "name": "TrashNet",
            "authors": "Gary Thung, Mindy Yang",
            "repository": REPO,
            "license": "MIT (según la API de GitHub)",
            "file": "data/dataset-resized.zip",
            "download_url": URL,
            "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "zip_size_bytes": ZIP_PATH.stat().st_size,
            "zip_sha256": sha256_file(ZIP_PATH),
        },
    )
    print("Descarga y extracción completas.")


if __name__ == "__main__":
    main()
