"""Pruebas del adaptador con transporte HTTP simulado (httpx.MockTransport) y de que la clave no se filtre."""

from __future__ import annotations

import base64
import logging

import httpx
import pytest
from conftest import make_settings

from app.core.errors import AppError
from app.integrations.roboflow import RoboflowClient, parse_classification

SECRET = "clave-secreta-de-prueba"
GOOD = {
    "predictions": [{"class": "glass", "confidence": 0.7}, {"class": "metal", "confidence": 0.3}],
    "top": "glass",
    "confidence": 0.7,
}


def make_client(handler, **over) -> RoboflowClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return RoboflowClient(http, make_settings(**over))


async def test_success_and_request_shape() -> None:
    seen: dict[str, object] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["url"] = req.url
        seen["body"] = req.content
        seen["ct"] = req.headers["content-type"]
        return httpx.Response(200, json=GOOD)

    probs = await make_client(handler).classify(b"imagen")
    assert probs == {"glass": 0.7, "metal": 0.3}
    url = seen["url"]
    assert str(url).startswith("https://serverless.roboflow.com/proyecto-prueba/1?")
    assert url.params["api_key"] == SECRET and url.params["confidence"] == "0"
    assert seen["body"] == base64.b64encode(b"imagen")
    assert seen["ct"] == "application/x-www-form-urlencoded"


@pytest.mark.parametrize(
    "status,code,http_status",
    [
        (401, "upstream_error", 502),
        (403, "upstream_error", 502),
        (404, "upstream_error", 502),
        (413, "file_too_large", 413),
        (429, "upstream_busy", 503),
        (500, "upstream_error", 502),
    ],
)
async def test_http_errors_are_mapped(status: int, code: str, http_status: int) -> None:
    client = make_client(lambda req: httpx.Response(status))
    with pytest.raises(AppError) as exc:
        await client.classify(b"x")
    assert exc.value.code == code and exc.value.status_code == http_status
    assert SECRET not in exc.value.message


async def test_timeout_maps_to_504() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento", request=req)

    with pytest.raises(AppError) as exc:
        await make_client(handler).classify(b"x")
    assert exc.value.status_code == 504 and exc.value.code == "upstream_timeout"


async def test_retries_once_on_503_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] == 1 else httpx.Response(200, json=GOOD)

    assert await make_client(handler).classify(b"x") == {"glass": 0.7, "metal": 0.3}
    assert calls["n"] == 2


async def test_connection_error_maps_to_502_without_leaking_key(caplog: pytest.LogCaptureFixture) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"fallo conectando a {req.url}", request=req)

    caplog.set_level(logging.DEBUG)
    with pytest.raises(AppError) as exc:
        await make_client(handler).classify(b"x")
    assert exc.value.status_code == 502
    assert SECRET not in exc.value.message
    assert SECRET not in caplog.text


async def test_invalid_json_maps_to_502() -> None:
    with pytest.raises(AppError) as exc:
        await make_client(lambda req: httpx.Response(200, content=b"<html>")).classify(b"x")
    assert exc.value.status_code == 502


def test_client_requires_configuration() -> None:
    with pytest.raises(AppError) as exc:
        RoboflowClient(httpx.AsyncClient(), make_settings(roboflow_api_key=None))
    assert exc.value.status_code == 503 and exc.value.code == "model_not_configured"


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"predictions": {"glass": {"confidence": 0.5}}},  # multietiqueta
        {"predictions": []},
        {"predictions": [{"class": "vidrio", "confidence": 0.5}]},
        {"predictions": [{"class": "glass", "confidence": 1.5}]},
        {"predictions": [{"class": "glass"}]},
    ],
)
def test_parse_rejects_unexpected_payloads(payload) -> None:
    with pytest.raises(AppError) as exc:
        parse_classification(payload)
    assert exc.value.status_code == 502


def test_invalid_model_id_is_rejected_at_startup() -> None:
    with pytest.raises(ValueError):
        make_settings(roboflow_model_id="sin-version")
