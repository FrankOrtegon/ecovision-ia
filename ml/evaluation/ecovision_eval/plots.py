"""Gráficos de evaluación (matriz de confusión, ROC y Precision-Recall)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .metrics import EvaluationResult

GREEN = "#16a34a"


def plot_confusion_matrix(res: EvaluationResult, path: Path, normalize: bool = False) -> None:
    cm = np.array(res.confusion_matrix, dtype=float)
    shown = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1) if normalize else cm
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(shown, cmap="Greens")
    ax.set_xticks(range(len(res.classes)), res.classes, rotation=45, ha="right")
    ax.set_yticks(range(len(res.classes)), res.classes)
    ax.set_xlabel("Clase predicha")
    ax.set_ylabel("Clase real")
    ax.set_title("Matriz de confusión" + (" (normalizada por fila)" if normalize else ""))
    thr = shown.max() / 2 if shown.max() > 0 else 0.5
    for i in range(shown.shape[0]):
        for j in range(shown.shape[1]):
            txt = f"{shown[i, j]:.2f}" if normalize else f"{int(shown[i, j])}"
            ax.text(j, i, txt, ha="center", va="center", color="white" if shown[i, j] > thr else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_roc(res: EvaluationResult, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for cv in res.roc:
        if cv.score is None:
            continue
        ax.plot(cv.x, cv.y, label=f"{cv.label} (AUC = {cv.score:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Azar")
    ax.set_xlabel("Tasa de falsos positivos")
    ax.set_ylabel("Tasa de verdaderos positivos")
    title = "Curvas ROC uno contra el resto"
    if res.auc_macro is not None:
        title += f"\nAUC macro = {res.auc_macro:.3f}"
    ax.set_title(title)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_pr(res: EvaluationResult, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for cv in res.pr:
        if cv.score is None:
            continue
        ax.plot(cv.x, cv.y, label=f"{cv.label} (AP = {cv.score:.3f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_ylim(0, 1.02)
    ax.set_title("Curvas Precision-Recall uno contra el resto")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
