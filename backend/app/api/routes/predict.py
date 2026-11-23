from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_classifier, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.roboflow import Classifier
from app.schemas.models import BatchResponse, ErrorResponse, PredictResponse
from app.services.images import read_upload, safe_filename
from app.services.prediction import predict_bytes, predict_many, read_uploads

router = APIRouter(prefix="/api", tags=["predicción"])

_ERRORS: dict[int | str, dict[str, object]] = {
    413: {"model": ErrorResponse, "description": "Archivo demasiado grande"},
    415: {"model": ErrorResponse, "description": "Formato no permitido"},
    422: {"model": ErrorResponse, "description": "Entrada inválida"},
    502: {"model": ErrorResponse, "description": "Error del proveedor del modelo"},
    503: {"model": ErrorResponse, "description": "Modelo no configurado o proveedor saturado"},
    504: {"model": ErrorResponse, "description": "Tiempo de espera agotado"},
}


@router.post("/predict", response_model=PredictResponse, responses=_ERRORS, summary="Clasificar una imagen")
async def predict(
    file: Annotated[UploadFile, File(description="Imagen JPG, JPEG, PNG o WEBP")],
    settings: Annotated[Settings, Depends(settings_dep)],
    classifier: Annotated[Classifier, Depends(get_classifier)],
) -> PredictResponse:
    started = time.perf_counter()
    content = await read_upload(file, settings.max_image_bytes)
    result = await predict_bytes(classifier, safe_filename(file.filename), content, settings)
    return PredictResponse(
        result=result, model_id=classifier.model_id, latency_ms=int((time.perf_counter() - started) * 1000)
    )


@router.post(
    "/predict/batch", response_model=BatchResponse, responses=_ERRORS, summary="Clasificar varias imágenes"
)
async def predict_batch(
    files: Annotated[list[UploadFile], File(description="Imágenes a clasificar")],
    settings: Annotated[Settings, Depends(settings_dep)],
    classifier: Annotated[Classifier, Depends(get_classifier)],
) -> BatchResponse:
    if not files:
        raise AppError("invalid_file", "No se envió ninguna imagen.", 422)
    if len(files) > settings.max_batch_files:
        raise AppError("too_many_files", f"Máximo {settings.max_batch_files} imágenes por lote.", 422)
    started = time.perf_counter()
    uploads = await read_uploads(files, settings)
    items = await predict_many(classifier, uploads, settings)
    ok = sum(1 for i in items if i.status == "ok")
    return BatchResponse(
        items=items,
        total=len(items),
        succeeded=ok,
        failed=len(items) - ok,
        model_id=classifier.model_id,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
