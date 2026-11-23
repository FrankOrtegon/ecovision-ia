"""Análisis posterior a la evaluación: intervalos de confianza, calibración, confianza baja y errores.

Trabaja solo con los archivos ya generados por 05_run_evaluation.py (no vuelve a llamar al modelo).
Uso: python 06_analyze_results.py --tag v1
"""
from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ecovision_eval import CLASSES, compute_metrics
from PIL import Image

from common import DATASET_DIR, RESULTS_DIR, SEED, SPLITS_DIR, write_json

N_BOOT = 2000
LOW_CONF = 0.60


def load(split: str, tag: str) -> tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_csv(RESULTS_DIR / f"eval_{split}_{tag}" / "predictions.csv")
    proba = df[[f"prob_{c}" for c in CLASSES]].to_numpy()
    return df, proba


def bootstrap(df: pd.DataFrame, proba: np.ndarray) -> dict[str, list[float]]:
    rng = np.random.default_rng(SEED)
    y = df["true_label"].to_numpy()
    n = len(df)
    acc, f1, auc = [], [], []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        try:
            m = compute_metrics(y[idx].tolist(), proba[idx])
        except ValueError:
            continue
        acc.append(m.accuracy)
        f1.append(m.macro["f1"])
        if m.auc_macro is not None:
            auc.append(m.auc_macro)
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    return {"accuracy": ci(acc), "f1_macro": ci(f1), "auc_macro_approx": ci(auc)}


def per_class_f1_ci(df: pd.DataFrame, proba: np.ndarray) -> dict[str, list[float]]:
    rng = np.random.default_rng(SEED)
    y = df["true_label"].to_numpy()
    n = len(df)
    store: dict[str, list[float]] = {c: [] for c in CLASSES}
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        m = compute_metrics(y[idx].tolist(), proba[idx])
        for pc in m.per_class:
            if pc.f1 is not None:
                store[pc.label].append(pc.f1)
    return {c: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for c, v in store.items()}


def calibration(df: pd.DataFrame, proba: np.ndarray) -> dict[str, object]:
    conf = proba.max(axis=1)
    correct = (df["true_label"] == df["predicted_label"]).to_numpy()
    bins = np.linspace(0.0, 1.0, 11)
    rows, ece = [], 0.0
    for lo, hi in zip(bins[:-1], bins[1:], strict=True):
        mask = (conf > lo) & (conf <= hi) if lo > 0 else (conf >= lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        a, c = float(correct[mask].mean()), float(conf[mask].mean())
        ece += mask.mean() * abs(a - c)
        rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": int(mask.sum()), "accuracy": a, "mean_confidence": c})
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Calibración perfecta")
    ax.plot([r["mean_confidence"] for r in rows], [r["accuracy"] for r in rows], "o-", color="#16a34a", label="Modelo")
    ax.set_xlabel("Confianza media del modelo")
    ax.set_ylabel("Accuracy observada")
    ax.set_title("Diagrama de fiabilidad (prueba)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "figures" / "test_reliability.png", dpi=150)
    plt.close(fig)
    return {"ece": float(ece), "bins": rows, "mean_confidence": float(conf.mean()), "accuracy": float(correct.mean())}


def low_confidence(df: pd.DataFrame, proba: np.ndarray) -> dict[str, float]:
    conf = proba.max(axis=1)
    correct = (df["true_label"] == df["predicted_label"]).to_numpy()
    low = conf < LOW_CONF
    return {
        "threshold": LOW_CONF,
        "fraction_flagged": float(low.mean()),
        "n_flagged": int(low.sum()),
        "accuracy_flagged": float(correct[low].mean()) if low.any() else float("nan"),
        "accuracy_not_flagged": float(correct[~low].mean()),
        "errors_total": int((~correct).sum()),
        "errors_caught_by_flag": int(((~correct) & low).sum()),
    }


def error_grid(df: pd.DataFrame, proba: np.ndarray, split: str) -> list[dict[str, object]]:
    meta = pd.read_csv(SPLITS_DIR / f"{split}.csv").set_index("filename")
    wrong = df[df["true_label"] != df["predicted_label"]].copy()
    wrong["confidence"] = proba.max(axis=1)[wrong.index]
    wrong = wrong.sort_values("confidence", ascending=False)
    shown = wrong.head(12)
    cols = 4
    rows_n = int(np.ceil(len(shown) / cols))
    fig, axes = plt.subplots(rows_n, cols, figsize=(3 * cols, 2.6 * rows_n))
    for ax in np.atleast_1d(axes).ravel():
        ax.axis("off")
    for ax, (_, r) in zip(np.atleast_1d(axes).ravel(), shown.iterrows(), strict=False):
        with Image.open(DATASET_DIR / meta.loc[r["filename"], "relpath"]) as im:
            ax.imshow(im)
        ax.set_title(f"{r['filename']}\nreal: {r['true_label']} → pred: {r['predicted_label']} ({r['confidence']:.0%})", fontsize=7.5)
    fig.suptitle("Errores de mayor confianza en el conjunto de prueba", fontsize=10)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "figures" / "test_errors.png", dpi=140)
    plt.close(fig)
    return [
        {"filename": r["filename"], "true": r["true_label"], "predicted": r["predicted_label"], "confidence": float(r["confidence"])}
        for _, r in wrong.iterrows()
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    (RESULTS_DIR / "figures").mkdir(parents=True, exist_ok=True)
    test, p_test = load("test", args.tag)
    val, p_val = load("val", args.tag)

    out = {
        "n_test": len(test),
        "bootstrap_ci95": {"n_resamples": N_BOOT, "test": bootstrap(test, p_test), "per_class_f1_test": per_class_f1_ci(test, p_test)},
        "calibration_test": calibration(test, p_test),
        "low_confidence_test": low_confidence(test, p_test),
        "validation_vs_test": {
            "validation": {"accuracy": compute_metrics(val["true_label"].tolist(), p_val).accuracy},
            "test": {"accuracy": compute_metrics(test["true_label"].tolist(), p_test).accuracy},
        },
        "errors_test": error_grid(test, p_test, "test"),
    }
    write_json(RESULTS_DIR / f"eval_test_{args.tag}" / "extra_analysis.json", out)
    ci = out["bootstrap_ci95"]["test"]
    print("IC95% accuracy:", [round(x, 4) for x in ci["accuracy"]], "| F1 macro:", [round(x, 4) for x in ci["f1_macro"]], "| AUC macro:", [round(x, 4) for x in ci["auc_macro_approx"]])
    print("ECE:", round(out["calibration_test"]["ece"], 4), "| confianza media:", round(out["calibration_test"]["mean_confidence"], 4))
    print("Confianza baja:", out["low_confidence_test"])
    print("Errores:", len(out["errors_test"]))


if __name__ == "__main__":
    main()
