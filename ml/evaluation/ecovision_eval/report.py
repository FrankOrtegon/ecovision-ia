"""Persistencia de resultados de evaluación."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .metrics import EvaluationResult
from .plots import plot_confusion_matrix, plot_pr, plot_roc


def _fmt(v: float | None) -> str:
    return "n/d" if v is None else f"{v:.4f}"


def classification_report_text(res: EvaluationResult) -> str:
    lines = [f"{'clase':<12}{'precision':>10}{'recall':>10}{'f1':>10}{'soporte':>10}"]
    for pc in res.per_class:
        lines.append(f"{pc.label:<12}{_fmt(pc.precision):>10}{_fmt(pc.recall):>10}{_fmt(pc.f1):>10}{pc.support:>10}")
    lines.append("")
    lines.append(f"{'accuracy':<12}{'':>20}{res.accuracy:>10.4f}{res.n_samples:>10}")
    for name, d in (("macro", res.macro), ("ponderado", res.weighted)):
        lines.append(f"{name:<12}{_fmt(d['precision']):>10}{_fmt(d['recall']):>10}{_fmt(d['f1']):>10}{res.n_samples:>10}")
    lines.append("")
    lines.append(f"AUC macro: {_fmt(res.auc_macro)}" + (f"  ({res.auc_macro_note})" if res.auc_macro_note else ""))
    lines.append(f"AP macro: {_fmt(res.ap_macro)}")
    if res.warnings:
        lines.append("")
        lines.append("Advertencias:")
        lines.extend(f"- {w}" for w in res.warnings)
    return "\n".join(lines) + "\n"


def save_results(
    res: EvaluationResult,
    filenames: Sequence[str],
    y_true: Sequence[str],
    proba: np.ndarray,
    out_dir: Path,
    config: dict[str, Any],
) -> None:
    """Guarda etiquetas, probabilidades, métricas, gráficos, reporte y configuración del modelo."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filename", "true_label", "predicted_label", *[f"prob_{c}" for c in res.classes]])
        for fn, t, pr, row in zip(filenames, y_true, res.predicted_labels, np.asarray(proba)):
            w.writerow([fn, t, pr, *[f"{x:.6f}" for x in row]])
    (out_dir / "metrics.json").write_text(json.dumps(res.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "classification_report.txt").write_text(classification_report_text(res), encoding="utf-8")
    (out_dir / "model_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plot_confusion_matrix(res, out_dir / "confusion_matrix.png")
    plot_confusion_matrix(res, out_dir / "confusion_matrix_normalized.png", normalize=True)
    plot_roc(res, out_dir / "roc_curves.png")
    plot_pr(res, out_dir / "pr_curves.png")
