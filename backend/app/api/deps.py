from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.integrations.roboflow import Classifier, RoboflowClient


def settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_classifier(request: Request, settings: Annotated[Settings, Depends(settings_dep)]) -> Classifier:
    """Cliente real de Roboflow. Lanza 503 si el modelo no está configurado."""
    http: httpx.AsyncClient = request.app.state.http
    return RoboflowClient(http, settings)


__all__ = ["get_classifier", "get_settings", "settings_dep"]
