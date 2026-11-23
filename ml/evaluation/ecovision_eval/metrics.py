"""Cálculo de métricas de clasificación multiclase.

Todas las curvas (ROC y Precision-Recall) se calculan con las probabilidades por clase,
nunca con las etiquetas predichas. La etiqueta predicha es el argmax de las probabilidades.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

import numpy as np
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve

from .constants import CLASSES

SUM_TOLERANCE = 0.01


@dataclass
class PerClass:
    label: str
    support: int
    predicted: int
    precision: float | None
    recall: float | None
    f1: float | None


@dataclass
class Curve:
    label: str
    x: list[float] | None  # ROC: fpr. PR: recall
    y: list[float] | None  # ROC: tpr. PR: precision
    score: float | None  # ROC: AUC. PR: AP
    note: str | None = None


@dataclass
class EvaluationResult:
    classes: list[str]
    n_samples: int
    accuracy: float
    per_class: list[PerClass]
    macro: dict[str, float | None]
    weighted: dict[str, float | None]
    confusion_matrix: list[list[int]]  # filas = real, columnas = predicho
    roc: list[Curve]
    auc_macro: float | None
    auc_macro_note: str | None
    pr: list[Curve]
    ap_macro: float | None
    top_confusions: list[dict[str, Any]]
    predicted_labels: list[str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate(y_true: Sequence[str], proba: np.ndarray, classes: Sequence[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    warnings: list[str] = []
    classes = list(classes)
    if len(set(classes)) != len(classes):
        raise ValueError("Las clases no pueden repetirse")
    y = np.asarray(list(y_true), dtype=object)
    p = np.asarray(proba, dtype=float)
    if len(y) == 0:
        raise ValueError("No hay muestras para evaluar")
    if p.ndim != 2 or p.shape != (len(y), len(classes)):
        raise ValueError(f"Se esperaba proba con forma ({len(y)}, {len(classes)}), se recibió {p.shape}")
    if not np.isfinite(p).all():
        raise ValueError("Las probabilidades contienen NaN o infinitos")
    if (p < 0).any() or (p > 1 + 1e-9).any():
        raise ValueError("Las probabilidades deben estar entre 0 y 1")
    unknown = sorted(set(y.tolist()) - set(classes))
    if unknown:
        raise ValueError(f"Etiquetas reales desconocidas: {unknown}")
    off = np.abs(p.sum(axis=1) - 1.0) > SUM_TOLERANCE
    if off.any():
        warnings.append(
            f"{int(off.sum())} de {len(y)} filas de probabilidades no suman 1 (tolerancia {SUM_TOLERANCE}). "
            "Las curvas ROC y PR no dependen de esa suma, pero la fuente de las probabilidades debe revisarse."
        )
    return y, p, warnings


def _safe_div(a: float, b: float) -> float | None:
    return a / b if b > 0 else None


def compute_metrics(
    y_true: Sequence[str], proba: np.ndarray, classes: Sequence[str] = CLASSES
) -> EvaluationResult:
    """Calcula todas las métricas a partir de etiquetas reales y probabilidades por clase."""
    classes = list(classes)
    y, p, warnings = _validate(y_true, proba, classes)
    n, k = p.shape
    idx = {c: i for i, c in enumerate(classes)}
    true_idx = np.array([idx[c] for c in y])
    pred_idx = p.argmax(axis=1)

    cm = np.zeros((k, k), dtype=int)
    np.add.at(cm, (true_idx, pred_idx), 1)
    support = cm.sum(axis=1)
    predicted = cm.sum(axis=0)
    tp = np.diag(cm)

    per_class: list[PerClass] = []
    for i, c in enumerate(classes):
        if support[i] == 0:
            per_class.append(PerClass(c, 0, int(predicted[i]), None, None, None))
            warnings.append(f"La clase '{c}' no tiene ejemplos reales: precision, recall y F1 no se pueden calcular.")
            continue
        recall = tp[i] / support[i]
        precision = _safe_div(tp[i], predicted[i])
        if precision is None:
            precision = 0.0
            warnings.append(f"La clase '{c}' nunca fue predicha: precision se fija en 0 por convención.")
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        per_class.append(PerClass(c, int(support[i]), int(predicted[i]), float(precision), float(recall), float(f1)))

    present = [pc for pc in per_class if pc.support > 0]
    if len(present) < k:
        warnings.append("Los promedios macro y ponderados se calculan solo sobre las clases con ejemplos reales.")
    total = sum(pc.support for pc in present)

    def avg(attr: str, weighted: bool) -> float | None:
        if not present:
            return None
        vals = np.array([getattr(pc, attr) for pc in present], dtype=float)
        w = np.array([pc.support for pc in present], dtype=float) if weighted else None
        return float(np.average(vals, weights=w))

    macro = {m: avg(m, False) for m in ("precision", "recall", "f1")}
    weighted = {m: avg(m, True) for m in ("precision", "recall", "f1")}

    roc: list[Curve] = []
    pr: list[Curve] = []
    for i, c in enumerate(classes):
        pos = int(support[i])
        neg = n - pos
        if pos == 0 or neg == 0:
            reason = "sin ejemplos positivos" if pos == 0 else "sin ejemplos negativos"
            roc.append(Curve(c, None, None, None, f"ROC/AUC no definida: {reason}"))
            warnings.append(f"ROC/AUC de '{c}' no calculable: {reason}.")
        else:
            binary = (true_idx == i).astype(int)
            fpr, tpr, _ = roc_curve(binary, p[:, i], drop_intermediate=False)
            roc.append(Curve(c, fpr.tolist(), tpr.tolist(), float(roc_auc_score(binary, p[:, i]))))
        if pos == 0:
            pr.append(Curve(c, None, None, None, "PR/AP no definida: sin ejemplos positivos"))
        else:
            binary = (true_idx == i).astype(int)
            prec, rec, _ = precision_recall_curve(binary, p[:, i])
            pr.append(Curve(c, rec.tolist(), prec.tolist(), float(average_precision_score(binary, p[:, i]))))

    undefined = [cv.label for cv in roc if cv.score is None]
    if undefined:
        auc_macro, auc_note = None, f"AUC macro no calculable: AUC indefinida para {undefined}"
    else:
        auc_macro, auc_note = float(np.mean([cv.score for cv in roc])), None
    ap_vals = [cv.score for cv in pr if cv.score is not None]
    ap_macro = float(np.mean(ap_vals)) if ap_vals else None

    confusions = [
        {"true": classes[i], "predicted": classes[j], "count": int(cm[i, j]),
         "share_of_true_class": float(cm[i, j] / support[i])}
        for i in range(k) for j in range(k) if i != j and cm[i, j] > 0
    ]
    confusions.sort(key=lambda d: (-d["count"], d["true"], d["predicted"]))

    return EvaluationResult(
        classes=classes,
        n_samples=n,
        accuracy=float(tp.sum() / n),
        per_class=per_class,
        macro=macro,
        weighted=weighted,
        confusion_matrix=cm.tolist(),
        roc=roc,
        auc_macro=auc_macro,
        auc_macro_note=auc_note,
        pr=pr,
        ap_macro=ap_macro,
        top_confusions=confusions,
        predicted_labels=[classes[i] for i in pred_idx],
        warnings=warnings,
    )
