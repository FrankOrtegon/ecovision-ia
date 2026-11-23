"""Utilidades de prueba. Los dobles de Roboflow viven SOLO aquí, nunca en el código de la aplicación."""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import get_classifier
from app.core.config import Settings
from app.integrations.roboflow import ProviderResult
from app.main import create_app

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]


def make_image(fmt: str = "JPEG", size: tuple[int, int] = (32, 24), color: str = "green") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


class FakeClassifier:
    """Devuelve probabilidades según el nombre del archivo recibido por contenido (ver `script`)."""

    model_id = "proyecto-prueba/1"

    def __init__(self) -> None:
        self.calls = 0
        self.queue: list[dict[str, float] | Exception] = []

    async def classify(self, image_bytes: bytes) -> ProviderResult:
        self.calls += 1
        item = self.queue.pop(0) if self.queue else peaked("plastic", 0.9)
        if isinstance(item, Exception):
            raise item
        return ProviderResult(item, "workspace-prueba/modelo-falso")


def peaked(label: str, p: float) -> dict[str, float]:
    rest = (1 - p) / (len(CLASSES) - 1)
    return {c: (p if c == label else rest) for c in CLASSES}


def make_settings(**over: object) -> Settings:
    base: dict[str, object] = {
        "environment": "test",
        "roboflow_api_key": "clave-secreta-de-prueba",
        "roboflow_model_id": "proyecto-prueba/1",
        "allowed_origins": "http://localhost:5173",
        "max_image_mb": 1,
        "max_batch_files": 3,
        "max_eval_files": 10,
        "batch_concurrency": 1,
    }
    base.update(over)
    return Settings(_env_file=None, **base)  # type: ignore[arg-type]


@pytest.fixture
def fake() -> FakeClassifier:
    return FakeClassifier()


@pytest.fixture
def client(fake: FakeClassifier) -> Iterator[TestClient]:
    app = create_app(make_settings())
    app.dependency_overrides[get_classifier] = lambda: fake
    with TestClient(app) as c:
        yield c


@pytest.fixture
def unconfigured_client() -> Iterator[TestClient]:
    app = create_app(make_settings(roboflow_api_key=None, roboflow_model_id=None))
    with TestClient(app) as c:
        yield c
