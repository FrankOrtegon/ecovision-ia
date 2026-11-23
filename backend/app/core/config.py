"""Configuración leída de variables de entorno (.env). Ningún secreto vive en el código."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MODEL_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/\d+$")
DEFAULT_MODEL_INFO = Path(__file__).resolve().parents[1] / "data" / "model_info.json"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production", "test"] = "development"
    app_version: str = "0.1.0"

    roboflow_api_key: SecretStr | None = None
    roboflow_api_url: str = "https://serverless.roboflow.com"
    roboflow_model_id: str | None = None
    roboflow_timeout_s: float = 30.0
    # Umbral que se envía a Roboflow (0-100). 0 pide todas las clases para poder calcular ROC.
    roboflow_confidence_percent: int = 0

    allowed_origins: str = "http://localhost:5173"

    max_image_mb: float = 5.0
    max_batch_files: int = 20
    max_eval_files: int = 500
    max_total_upload_mb: float = 100.0
    max_image_pixels: int = 40_000_000
    batch_concurrency: int = 4
    low_confidence_threshold: float = 0.60

    model_info_path: Path = DEFAULT_MODEL_INFO

    @field_validator("roboflow_api_key", "roboflow_model_id", mode="before")
    @classmethod
    def _empty_to_none(cls, v: object) -> object:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("roboflow_model_id")
    @classmethod
    def _valid_model_id(cls, v: str | None) -> str | None:
        if v is not None and not MODEL_ID_PATTERN.match(v):
            raise ValueError(
                "ROBOFLOW_MODEL_ID debe tener el formato 'proyecto/versión', por ejemplo 'mi-proyecto/1'"
            )
        return v

    @model_validator(mode="after")
    def _check(self) -> Settings:
        if self.environment == "production" and ("*" in self.origins or not self.origins):
            raise ValueError("En producción ALLOWED_ORIGINS debe listar orígenes explícitos, sin '*'")
        if not 0 <= self.low_confidence_threshold <= 1:
            raise ValueError("LOW_CONFIDENCE_THRESHOLD debe estar entre 0 y 1")
        return self

    @property
    def origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_image_bytes(self) -> int:
        return int(self.max_image_mb * 1024 * 1024)

    @property
    def max_total_bytes(self) -> int:
        return int(self.max_total_upload_mb * 1024 * 1024)

    @property
    def model_configured(self) -> bool:
        return self.roboflow_api_key is not None and self.roboflow_model_id is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
