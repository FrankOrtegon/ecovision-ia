"""Cliente del modelo de clasificación alojado en Roboflow (API serverless).

Endpoint documentado: POST {api_url}/{proyecto}/{versión}?api_key=...
con el cuerpo de la imagen en base64. Respuesta de clasificación monoetiqueta:
{"predictions": [{"class": "...", "confidence": 0.9}, ...], "top": "...", "confidence": 0.9}.

Seguridad: la URL contiene la API key. Por eso nunca se registra la URL ni el texto de
las excepciones de httpx; solo su tipo.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any, Protocol

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.models import CLASS_NAMES

logger = logging.getLogger("ecovision.roboflow")

RETRY_STATUS = {502, 503, 504}


class Classifier(Protocol):
    model_id: str

    async def classify(self, image_bytes: bytes) -> dict[str, float]:
        """Devuelve probabilidad por clase. Puede omitir clases que el proveedor no devuelva."""
        ...


def parse_classification(payload: Any) -> dict[str, float]:
    """Normaliza la respuesta de Roboflow a {clase: probabilidad}."""
    if not isinstance(payload, dict):
        raise AppError("upstream_error", "Respuesta inesperada del proveedor del modelo.", 502)
    preds = payload.get("predictions")
    if not isinstance(preds, list):
        raise AppError(
            "upstream_error",
            "El modelo no devolvió una clasificación de una sola etiqueta. "
            "Revisa el tipo de proyecto en Roboflow.",
            502,
        )
    probs: dict[str, float] = {}
    for item in preds:
        try:
            name = str(item["class"])
            conf = float(item["confidence"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AppError("upstream_error", "Respuesta inesperada del proveedor del modelo.", 502) from exc
        if name not in CLASS_NAMES:
            raise AppError(
                "upstream_error",
                f"El modelo devolvió una clase desconocida ('{name[:40]}'). "
                "Debe usar las seis clases del proyecto.",
                502,
            )
        if not 0.0 <= conf <= 1.0:
            raise AppError("upstream_error", "El proveedor devolvió una confianza fuera de rango.", 502)
        probs[name] = conf
    if not probs:
        raise AppError("upstream_error", "El modelo no devolvió ninguna predicción.", 502)
    return probs


class RoboflowClient:
    def __init__(self, http: httpx.AsyncClient, settings: Settings) -> None:
        if settings.roboflow_api_key is None or settings.roboflow_model_id is None:
            raise AppError(
                "model_not_configured",
                "El modelo no está configurado en el servidor (faltan ROBOFLOW_API_KEY o ROBOFLOW_MODEL_ID).",
                503,
            )
        self._http = http
        self._key = settings.roboflow_api_key.get_secret_value()
        self._url = f"{settings.roboflow_api_url.rstrip('/')}/{settings.roboflow_model_id}"
        self._confidence = settings.roboflow_confidence_percent
        self._timeout = settings.roboflow_timeout_s
        self.model_id = settings.roboflow_model_id

    async def classify(self, image_bytes: bytes) -> dict[str, float]:
        body = base64.b64encode(image_bytes)
        params = {"api_key": self._key, "confidence": str(self._confidence)}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        last: AppError | None = None
        for attempt in (1, 2):
            try:
                resp = await self._http.post(
                    self._url, params=params, content=body, headers=headers, timeout=self._timeout
                )
            except httpx.TimeoutException as exc:
                logger.warning("Timeout al consultar el modelo (%s)", type(exc).__name__)
                raise AppError("upstream_timeout", "El modelo tardó demasiado en responder.", 504) from None
            except httpx.HTTPError as exc:
                logger.warning("Fallo de red al consultar el modelo (%s)", type(exc).__name__)
                last = AppError("upstream_error", "No se pudo contactar al proveedor del modelo.", 502)
            else:
                if resp.status_code in RETRY_STATUS and attempt == 1:
                    logger.warning("Proveedor respondió %s; se reintenta una vez", resp.status_code)
                    last = self._status_error(resp.status_code)
                else:
                    if resp.status_code != 200:
                        raise self._status_error(resp.status_code)
                    try:
                        data = resp.json()
                    except ValueError:
                        raise AppError(
                            "upstream_error", "Respuesta inesperada del proveedor del modelo.", 502
                        ) from None
                    return parse_classification(data)
            await asyncio.sleep(0.5)
        assert last is not None
        raise last

    @staticmethod
    def _status_error(status: int) -> AppError:
        logger.warning("El proveedor del modelo respondió HTTP %s", status)
        if status in (401, 403):
            return AppError("upstream_error", "El proveedor rechazó las credenciales del servidor.", 502)
        if status == 404:
            return AppError("upstream_error", "El modelo configurado no existe en el proveedor.", 502)
        if status == 413:
            return AppError("file_too_large", "El proveedor rechazó la imagen por su tamaño.", 413)
        if status == 429:
            return AppError("upstream_busy", "El proveedor alcanzó su límite de uso. Intenta más tarde.", 503)
        return AppError(
            "upstream_error", f"El proveedor del modelo respondió con un error (HTTP {status}).", 502
        )
