"""Evaluación del modelo con imágenes etiquetadas. Reutiliza el paquete ecovision_eval."""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
from ecovision_eval import compute_metrics

from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.roboflow import Classifier
from app.schemas.models import (
    CLASS_NAMES,
    AveragedMetrics,
    BatchItem,
    Confusion,
    ConfusionMatrix,
    Curve,
    EvaluationResponse,
    EvaluationRow,
    PerClassMetrics,
)
from app.services.images import safe_filename
from app.services.prediction import Upload, predict_many

MAX_CSV_BYTES = 1024 * 1024


def parse_labels_csv(raw: bytes, settings: Settings) -> dict[str, str]:
    """Devuelve {nombre_de_archivo: etiqueta}. Formato: cabecera 'filename,true_label', UTF-8."""
    if len(raw) > MAX_CSV_BYTES:
        raise AppError("bad_csv", "El CSV de etiquetas supera 1 MB.", 422)
    try:
        df = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")), dtype=str, keep_default_na=False)
    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError):
        raise AppError(
            "bad_csv", "El CSV no se pudo leer. Debe ser UTF-8 con cabecera filename,true_label.", 422
        ) from None
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"filename", "true_label"} <= set(df.columns):
        raise AppError("bad_csv", "El CSV debe tener las columnas 'filename' y 'true_label'.", 422)
    if df.empty:
        raise AppError("bad_csv", "El CSV no tiene filas.", 422)
    if len(df) > settings.max_eval_files:
        raise AppError("too_many_files", f"El CSV supera el máximo de {settings.max_eval_files} filas.", 422)
    names = [safe_filename(n) for n in df["filename"]]
    labels = [str(x).strip().lower() for x in df["true_label"]]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise AppError("bad_csv", f"Nombres de archivo repetidos en el CSV: {', '.join(dup[:5])}.", 422)
    bad = sorted({lbl for lbl in labels if lbl not in CLASS_NAMES})
    if bad:
        raise AppError(
            "bad_csv",
            f"Etiquetas no válidas: {', '.join(repr(b[:30]) for b in bad[:5])}. "
            f"Permitidas: {', '.join(CLASS_NAMES)}.",
            422,
        )
    return dict(zip(names, labels, strict=True))


async def evaluate(
    classifier: Classifier, uploads: list[Upload], labels: dict[str, str], settings: Settings
) -> EvaluationResponse:
    names = [u.filename for u in uploads]
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        raise AppError("invalid_file", f"Hay imágenes con el mismo nombre: {', '.join(dup[:5])}.", 422)

    matched = [u for u in uploads if u.filename in labels]
    unmatched_images = sorted(u.filename for u in uploads if u.filename not in labels)
    unmatched_labels = sorted(n for n in labels if n not in set(names))
    if not matched:
        raise AppError("no_matches", "Ningún nombre de imagen coincide con el CSV de etiquetas.", 422)

    items = await predict_many(classifier, matched, settings)
    ok = [it for it in items if it.status == "ok" and it.result is not None]
    failed: list[BatchItem] = [it for it in items if it.status != "ok"]
    if not ok:
        raise AppError("no_valid_predictions", "No se obtuvo ninguna predicción válida para evaluar.", 422)

    y_true = [labels[it.filename] for it in ok]
    proba = np.array(
        [[p.probability for p in it.result.probabilities] for it in ok if it.result], dtype=float
    )
    res = compute_metrics(y_true, proba, CLASS_NAMES)

    warnings = list(res.warnings)
    if unmatched_images:
        warnings.append(f"{len(unmatched_images)} imágenes no tienen etiqueta en el CSV y se omitieron.")
    if unmatched_labels:
        warnings.append(f"{len(unmatched_labels)} filas del CSV no tienen imagen y se omitieron.")
    if failed:
        warnings.append(f"{len(failed)} imágenes fallaron y no cuentan en las métricas.")
    if any(it.result and it.result.incomplete_probabilities for it in ok):
        warnings.append(
            "El proveedor no devolvió las seis clases en algunas imágenes; se completaron con 0. "
            "Las curvas ROC y PR pueden estar sesgadas."
        )

    rows = [
        EvaluationRow(
            filename=it.filename,
            true_label=labels[it.filename],
            predicted_label=it.result.predicted_label,
            confidence=it.result.confidence,
            probabilities=it.result.probabilities,
        )
        for it in ok
        if it.result
    ]
    return EvaluationResponse(
        model_id=classifier.model_id,
        n_requested=len(labels),
        n_evaluated=res.n_samples,
        accuracy=res.accuracy,
        per_class=[PerClassMetrics(**vars(pc)) for pc in res.per_class],
        macro=AveragedMetrics(**res.macro),
        weighted=AveragedMetrics(**res.weighted),
        confusion_matrix=ConfusionMatrix(labels=list(CLASS_NAMES), matrix=res.confusion_matrix),
        roc=[Curve(**vars(c)) for c in res.roc],
        auc_macro=res.auc_macro,
        auc_macro_note=res.auc_macro_note,
        pr=[Curve(**vars(c)) for c in res.pr],
        ap_macro=res.ap_macro,
        top_confusions=[Confusion(**c) for c in res.top_confusions],
        rows=rows,
        failed=failed,
        unmatched_images=unmatched_images,
        unmatched_labels=unmatched_labels,
        warnings=warnings,
    )
