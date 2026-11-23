from __future__ import annotations

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.api.deps import settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.models import HealthResponse, Limits, ModelInfo
from app.services.images import ALLOWED_EXTENSIONS

router = APIRouter(prefix="/api", tags=["sistema"])
logger = logging.getLogger("ecovision.system")


@router.get("/health", response_model=HealthResponse, summary="Estado del servicio")
def health(settings: Annotated[Settings, Depends(settings_dep)]) -> HealthResponse:
    return HealthResponse(
        status="ok" if settings.model_configured else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        model_configured=settings.model_configured,
        limits=Limits(
            max_image_mb=settings.max_image_mb,
            max_batch_files=settings.max_batch_files,
            max_eval_files=settings.max_eval_files,
            low_confidence_threshold=settings.low_confidence_threshold,
            allowed_extensions=sorted(ALLOWED_EXTENSIONS),
        ),
    )


@router.get("/model/info", response_model=ModelInfo, summary="Información del modelo")
def model_info(settings: Annotated[Settings, Depends(settings_dep)]) -> ModelInfo:
    """Lee los metadatos de `model_info.json`, que se completa solo con datos de entrenamientos reales."""
    try:
        data = json.loads(settings.model_info_path.read_text(encoding="utf-8"))
        return ModelInfo.model_validate(data)
    except (OSError, ValueError, ValidationError) as exc:
        logger.error("No se pudo leer model_info.json (%s)", type(exc).__name__)
        raise AppError(
            "model_info_unavailable", "La información del modelo no está disponible.", 500
        ) from None
