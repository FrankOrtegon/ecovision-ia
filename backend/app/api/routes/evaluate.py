from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_classifier, settings_dep
from app.api.routes.predict import _ERRORS
from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.roboflow import Classifier
from app.schemas.models import EvaluationResponse
from app.services.evaluation import MAX_CSV_BYTES, evaluate, parse_labels_csv
from app.services.images import read_upload
from app.services.prediction import read_uploads

router = APIRouter(prefix="/api", tags=["evaluación"])


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    responses=_ERRORS,
    summary="Evaluar el modelo con imágenes etiquetadas",
)
async def evaluate_model(
    files: Annotated[list[UploadFile], File(description="Imágenes etiquetadas")],
    labels_csv: Annotated[UploadFile, File(description="CSV UTF-8 con columnas filename,true_label")],
    settings: Annotated[Settings, Depends(settings_dep)],
    classifier: Annotated[Classifier, Depends(get_classifier)],
) -> EvaluationResponse:
    if not files:
        raise AppError("invalid_file", "No se enviaron imágenes.", 422)
    if len(files) > settings.max_eval_files:
        raise AppError("too_many_files", f"Máximo {settings.max_eval_files} imágenes por evaluación.", 422)
    raw_csv = await read_upload(labels_csv, MAX_CSV_BYTES)
    labels = parse_labels_csv(raw_csv, settings)
    uploads = await read_uploads(files, settings)
    return await evaluate(classifier, uploads, labels, settings)
