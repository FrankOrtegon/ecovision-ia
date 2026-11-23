"""Genera las figuras del informe en español a partir de los resultados guardados (no recalcula nada)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "ml" / "results"
OUT = Path(__file__).resolve().parent / "fig"
DATASET = ROOT / "ml" / "data" / "raw" / "dataset-resized"
OUT.mkdir(exist_ok=True)

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
ES = {"cardboard": "Cartón", "glass": "Vidrio", "metal": "Metal", "paper": "Papel", "plastic": "Plástico", "trash": "Otros residuos"}
COLOR = {"cardboard": "#92400e", "glass": "#0891b2", "metal": "#64748b", "paper": "#d97706", "plastic": "#2563eb", "trash": "#7c3aed"}
GREEN = "#16a34a"

plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
comma = FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))


def c3(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=200)
    plt.close(fig)


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def fig_distribution() -> None:
    s = load(RES / "dataset_summary.json")["counts_per_class"]
    sp = load(RES / "split_summary.json")["per_class"]
    fig, ax = plt.subplots(figsize=(7.2, 4))
    x = np.arange(len(CLASSES))
    bottoms = np.zeros(len(CLASSES))
    for key, col, lab in (("train", GREEN, "Entrenamiento"), ("val", "#86efac", "Validación"), ("test", "#bbf7d0", "Prueba")):
        vals = np.array([sp[c][key] for c in CLASSES])
        ax.bar(x, vals, bottom=bottoms, color=col, label=lab, edgecolor="white")
        bottoms += vals
    for i, c in enumerate(CLASSES):
        ax.text(i, bottoms[i] + 6, f"{s[c]}", ha="center", fontsize=9)
    ax.set_xticks(x, [ES[c] for c in CLASSES])
    ax.set_ylabel("Número de imágenes")
    ax.legend(frameon=False)
    ax.set_title("Imágenes por categoría (total original sobre cada barra)", fontsize=10)
    save(fig, "distribucion.png")


def fig_samples() -> None:
    idx = pd.read_csv(RES / "image_index.csv")
    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(len(CLASSES), 5, figsize=(8.5, 9.2))
    for r, c in enumerate(CLASSES):
        sub = idx[(idx["label"] == c) & idx["valid"]]
        pick = rng.choice(len(sub), size=5, replace=False)
        for k in range(5):
            ax = axes[r, k]
            ax.axis("off")
            with Image.open(DATASET / sub.iloc[pick[k]]["relpath"]) as im:
                ax.imshow(im)
            if k == 0:
                ax.set_title(ES[c], loc="left", fontsize=10, fontweight="bold")
    save(fig, "ejemplos.png")


def fig_confusion(m: dict) -> None:
    cm = np.array(m["confusion_matrix"], dtype=float)
    norm = cm / cm.sum(axis=1, keepdims=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))
    for ax, data, title, fmt in ((axes[0], cm, "Conteos", "{:.0f}"), (axes[1], norm, "Proporción por clase real", "{:.2f}")):
        im = ax.imshow(data, cmap="Greens", vmin=0)
        ax.set_xticks(range(6), [ES[c] for c in CLASSES], rotation=40, ha="right")
        ax.set_yticks(range(6), [ES[c] for c in CLASSES])
        ax.set_xlabel("Clase predicha")
        ax.set_ylabel("Clase real")
        ax.set_title(title, fontsize=10)
        thr = data.max() * 0.6
        for i in range(6):
            for j in range(6):
                t = fmt.format(data[i, j]).replace(".", ",")
                ax.text(j, i, t, ha="center", va="center", color="white" if data[i, j] > thr else "black", fontsize=8.5)
        fig.colorbar(im, ax=ax, fraction=0.046)
    save(fig, "matriz_confusion.png")


def curve_fig(m: dict, key: str, name: str, xlabel: str, ylabel: str, score_name: str, diagonal: bool) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    for cv in m[key]:
        if cv["score"] is None:
            continue
        lab = f"{ES[cv['label']]} ({score_name} = {c3(cv['score'])})"
        if key == "pr":  # curva en escalones, como la define scikit-learn (sin interpolación lineal)
            ax.step(cv["x"], cv["y"], where="post", color=COLOR[cv["label"]], linewidth=1.6, label=lab)
        else:
            ax.plot(cv["x"], cv["y"], color=COLOR[cv["label"]], linewidth=1.6, label=lab)
    if diagonal:
        ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Clasificador aleatorio")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(0, 1.02)
    ax.xaxis.set_major_formatter(comma)
    ax.yaxis.set_major_formatter(comma)
    ax.legend(loc="lower right" if diagonal else "lower left", fontsize=8, frameon=False)
    save(fig, name)


def fig_reliability(extra: dict) -> None:
    bins = extra["calibration_test"]["bins"]
    fig, ax = plt.subplots(figsize=(5.4, 4.8))
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Calibración perfecta")
    ax.plot([b["mean_confidence"] for b in bins], [b["accuracy"] for b in bins], "o-", color=GREEN, label="Modelo")
    for b in bins:
        ax.annotate(str(b["n"]), (b["mean_confidence"], b["accuracy"]), textcoords="offset points", xytext=(4, -11), fontsize=7)
    ax.set_xlabel("Confianza media por intervalo")
    ax.set_ylabel("Exactitud observada")
    ax.xaxis.set_major_formatter(comma)
    ax.yaxis.set_major_formatter(comma)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "fiabilidad.png")


def fig_errors(extra: dict) -> None:
    meta = pd.read_csv(RES / "splits" / "test.csv").set_index("filename")
    errs = extra["errors_test"][:12]
    fig, axes = plt.subplots(3, 4, figsize=(10, 7.6))
    for ax, e in zip(axes.ravel(), errs, strict=False):
        with Image.open(DATASET / meta.loc[e["filename"], "relpath"]) as im:
            ax.imshow(im)
        ax.axis("off")
        ax.set_title(f"Real: {ES[e['true']]}\nPredicho: {ES[e['predicted']]} ({e['confidence']*100:.0f} %)".replace(".", ","), fontsize=8)
    save(fig, "errores.png")


if __name__ == "__main__":
    test = load(RES / "eval_test_v1" / "metrics.json")
    extra = load(RES / "eval_test_v1" / "extra_analysis.json")
    fig_distribution()
    fig_samples()
    fig_confusion(test)
    curve_fig(test, "roc", "roc.png", "Tasa de falsos positivos", "Tasa de verdaderos positivos", "AUC", True)
    curve_fig(test, "pr", "pr.png", "Recall (exhaustividad)", "Precisión", "AP", False)
    fig_reliability(extra)
    fig_errors(extra)
    print("figuras:", sorted(p.name for p in OUT.iterdir()))
