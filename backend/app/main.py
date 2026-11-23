"""Aplicación FastAPI de EcoVision IA."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import evaluate, predict, system
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging

logger = logging.getLogger("ecovision.http")

DESCRIPTION = (
    "API de clasificación de residuos (TrashNet). Clasifica el **material aparente** de una imagen "
    "en seis categorías; no determina si un residuo es reciclable. Las imágenes se procesan en memoria "
    "y no se almacenan."
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.environment)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.http = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.roboflow_timeout_s),
            limits=httpx.Limits(max_connections=20),
        )
        if not settings.model_configured:
            logger.warning("Modelo no configurado: /api/predict* responderá 503 hasta definir ROBOFLOW_*.")
        yield
        await app.state.http.aclose()

    app = FastAPI(
        title="EcoVision IA API",
        version=settings.app_version,
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.state.settings = settings
    register_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
        max_age=600,
    )

    @app.middleware("http")
    async def security_and_access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        # Se registra solo la ruta, nunca la query string.
        logger.info(
            "%s %s -> %s (%d ms)",
            request.method,
            request.url.path,
            response.status_code,
            int((time.perf_counter() - started) * 1000),
        )
        return response

    for module in (system, predict, evaluate):
        app.include_router(module.router)
    return app


app = create_app()
