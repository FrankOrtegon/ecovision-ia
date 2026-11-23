"""Orquestación de predicciones individuales y por lotes."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.roboflow import Classifier
from app.schemas.models import (
    CLASS_NAMES,
    BatchItem,
    ClassProbability,
    PredictionResult,
)
from app.services.images import read_upload, safe_filename, validate_image

logger = logging.getLogger("ecovision.prediction")


def build_result(filename: str, probs: dict[str, float], threshold: float) -> PredictionResult:
    full = [probs.get(c, 0.0) for c in CLASS_NAMES]
    incomplete = any(c not in probs for c in CLASS_NAMES)
    best = max(range(len(CLASS_NAMES)), key=lambda i: full[i])
    return PredictionResult(
        filename=filename,
        predicted_label=CLASS_NAMES[best],
        confidence=full[best],
        low_confidence=full[best] < threshold,
        probabilities=[
            ClassProbability(label=c, probability=p) for c, p in zip(CLASS_NAMES, full, strict=True)
        ],
        incomplete_probabilities=incomplete,
    )


async def predict_bytes(
    classifier: Classifier, filename: str, content: bytes, settings: Settings
) -> PredictionResult:
    img = validate_image(filename, content, settings)
    probs = await classifier.classify(img.content)
    return build_result(filename, probs, settings.low_confidence_threshold)


@dataclass(frozen=True)
class Upload:
    filename: str
    content: bytes | None
    error: AppError | None = None


async def read_uploads(files: list[UploadFile], settings: Settings) -> list[Upload]:
    """Lee los archivos aplicando el límite por archivo y el límite total de la solicitud."""
    out: list[Upload] = []
    total = 0
    for f in files:
        name = safe_filename(f.filename)
        try:
            data = await read_upload(f, settings.max_image_bytes)
        except AppError as err:
            out.append(Upload(name, None, err))
            continue
        total += len(data)
        if total > settings.max_total_bytes:
            raise AppError(
                "request_too_large",
                f"El total de archivos supera {settings.max_total_upload_mb:g} MB.",
                413,
            )
        out.append(Upload(name, data))
    return out


async def predict_many(classifier: Classifier, uploads: list[Upload], settings: Settings) -> list[BatchItem]:
    """Predice cada archivo con concurrencia acotada. Un fallo no detiene el resto."""
    sem = asyncio.Semaphore(settings.batch_concurrency)

    async def one(up: Upload) -> BatchItem:
        if up.error is not None:
            return BatchItem(
                filename=up.filename, status="error", error=up.error.message, error_code=up.error.code
            )
        assert up.content is not None
        try:
            async with sem:
                res = await predict_bytes(classifier, up.filename, up.content, settings)
        except AppError as err:
            return BatchItem(filename=up.filename, status="error", error=err.message, error_code=err.code)
        return BatchItem(filename=up.filename, status="ok", result=res)

    return list(await asyncio.gather(*(one(u) for u in uploads)))
