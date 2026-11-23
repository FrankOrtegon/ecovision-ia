"""Exploración de TrashNet: conteos, integridad, formatos, duplicados y balance."""
from __future__ import annotations

import warnings

import imagehash
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from common import (
    CLASSES,
    DATASET_DIR,
    FIGURES_DIR,
    IMAGE_EXTENSIONS,
    RESULTS_DIR,
    SEED,
    list_images,
    sha256_file,
    write_json,
)

NEAR_THRESHOLDS = [0, 2, 4, 6]


def build_index() -> pd.DataFrame:
    rows = []
    for label, path in list_images():
        row = {
            "filename": path.name,
            "label": label,
            "relpath": str(path.relative_to(DATASET_DIR)),
            "extension": path.suffix.lower(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "valid": False,
            "format": None,
            "mode": None,
            "width": None,
            "height": None,
            "phash": None,
            "error": None,
        }
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                with Image.open(path) as im:
                    im.verify()
            with Image.open(path) as im:
                im.load()
                row.update(
                    valid=True, format=im.format, mode=im.mode, width=im.width, height=im.height,
                    phash=str(imagehash.phash(im)),
                )
        except Exception as exc:  # noqa: BLE001 - se registra y se reporta
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return pd.DataFrame(rows)


def near_duplicate_pairs(df: pd.DataFrame, max_dist: int) -> pd.DataFrame:
    v = df[df["valid"]].reset_index(drop=True)
    bits = np.array(
        [[int(c) for c in format(int(h, 16), "064b")] for h in v["phash"]], dtype=np.uint8
    )
    # distancia de Hamming por pares: d = n1 + n2 - 2*(a·b)
    ones = bits.sum(axis=1)
    dot = bits.astype(np.int32) @ bits.T.astype(np.int32)
    dist = ones[:, None] + ones[None, :] - 2 * dot
    i, j = np.where(np.triu(dist <= max_dist, k=1))
    return pd.DataFrame(
        {
            "file_a": v["filename"].values[i],
            "label_a": v["label"].values[i],
            "file_b": v["filename"].values[j],
            "label_b": v["label"].values[j],
            "hamming": dist[i, j],
            "same_sha256": v["sha256"].values[i] == v["sha256"].values[j],
        }
    )


def plot_distribution(counts: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(counts.index, counts.values, color="#16a34a")
    ax.bar_label(bars)
    ax.set_title("Imágenes por clase (TrashNet)")
    ax.set_ylabel("Número de imágenes")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "class_distribution.png", dpi=150)
    plt.close(fig)


def plot_samples(df: pd.DataFrame, n: int = 5) -> None:
    rng = np.random.default_rng(SEED)
    fig, axes = plt.subplots(len(CLASSES), n, figsize=(2.2 * n, 2.0 * len(CLASSES)))
    for r, cls in enumerate(CLASSES):
        sub = df[(df["label"] == cls) & df["valid"]]
        pick = rng.choice(len(sub), size=min(n, len(sub)), replace=False)
        for c in range(n):
            ax = axes[r, c]
            ax.axis("off")
            if c < len(pick):
                with Image.open(DATASET_DIR / sub.iloc[pick[c]]["relpath"]) as im:
                    ax.imshow(im)
            if c == 0:
                ax.set_title(cls, loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "samples_per_class.png", dpi=130)
    plt.close(fig)


def plot_sizes(df: pd.DataFrame) -> None:
    v = df[df["valid"]]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(v["width"], v["height"], s=6, alpha=0.4, color="#16a34a")
    ax.set_xlabel("Ancho (px)")
    ax.set_ylabel("Alto (px)")
    ax.set_title("Dimensiones de las imágenes")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "image_sizes.png", dpi=150)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = build_index()
    df.to_csv(RESULTS_DIR / "image_index.csv", index=False)

    valid = df[df["valid"]]
    counts = df["label"].value_counts().reindex(CLASSES).fillna(0).astype(int)
    exact = df[df.duplicated("sha256", keep=False)].sort_values("sha256")
    exact[["sha256", "filename", "label"]].to_csv(RESULTS_DIR / "exact_duplicates.csv", index=False)
    exact_cross = exact.groupby("sha256")["label"].nunique().gt(1).sum()

    pairs = near_duplicate_pairs(df, max(NEAR_THRESHOLDS))
    pairs.to_csv(RESULTS_DIR / "near_duplicate_pairs.csv", index=False)
    near_summary = {
        str(t): {
            "pairs": int((pairs["hamming"] <= t).sum()),
            "cross_class_pairs": int(((pairs["hamming"] <= t) & (pairs["label_a"] != pairs["label_b"])).sum()),
        }
        for t in NEAR_THRESHOLDS
    }

    ratio = float(counts.max() / counts.min())
    summary = {
        "total_files": int(len(df)),
        "valid_images": int(len(valid)),
        "corrupt_images": df.loc[~df["valid"], ["filename", "error"]].to_dict("records"),
        "counts_per_class": counts.to_dict(),
        "proportion_per_class": (counts / counts.sum()).round(4).to_dict(),
        "imbalance_ratio_max_over_min": round(ratio, 2),
        "extensions": df["extension"].value_counts().to_dict(),
        "unsupported_extensions": sorted(set(df["extension"]) - IMAGE_EXTENSIONS),
        "formats": valid["format"].value_counts().to_dict(),
        "modes": valid["mode"].value_counts().to_dict(),
        "dimensions": {
            "width_min": int(valid["width"].min()), "width_max": int(valid["width"].max()),
            "height_min": int(valid["height"].min()), "height_max": int(valid["height"].max()),
            "most_common_sizes": {
                f"{w}x{h}": int(n)
                for (w, h), n in valid.groupby(["width", "height"]).size()
                .sort_values(ascending=False).head(5).items()
            },
        },
        "bytes": {"min": int(df["bytes"].min()), "max": int(df["bytes"].max()), "mean": round(float(df["bytes"].mean()), 1)},
        "exact_duplicates": {
            "files_in_duplicate_groups": int(len(exact)),
            "groups": int(exact["sha256"].nunique()),
            "groups_with_conflicting_labels": int(exact_cross),
        },
        "near_duplicates_phash": near_summary,
        "unique_filenames": bool(df["filename"].is_unique),
    }
    write_json(RESULTS_DIR / "dataset_summary.json", summary)

    plot_distribution(counts)
    plot_samples(df)
    plot_sizes(df)

    print(counts.to_string())
    print(f"Total: {len(df)}  válidas: {len(valid)}  razón desequilibrio: {ratio:.2f}")
    print("Duplicados exactos:", summary["exact_duplicates"])
    print("Casi duplicados:", near_summary)


if __name__ == "__main__":
    main()
