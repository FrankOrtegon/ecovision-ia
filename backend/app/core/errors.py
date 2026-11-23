"""Errores de aplicación con formato uniforme: {"detail": {"code": ..., "message": ...}}."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("ecovision")


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"detail": {"code": code, "message": message, **extra}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [".".join(str(p) for p in e["loc"] if p != "body") for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content=_body(
                "validation_error", "La solicitud no es válida. Revisa los campos enviados.", fields=fields
            ),
        )

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Solo se registra el tipo: el mensaje podría contener URLs con credenciales.
        logger.error("Error no controlado: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content=_body("internal_error", "Error interno del servidor."))
