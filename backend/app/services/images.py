"""Lectura y validación de imágenes subidas. Todo se procesa en memoria."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import AppError

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class ValidatedImage:
    filename: str
    content: bytes
    format: str
    width: int
    height: int


def safe_filename(name: str | None) -> str:
    base = PurePosixPath((name or "").replace("\\", "/")).name
    base = _CONTROL.sub("", base).strip()[:120]
    return base or "sin_nombre"


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    """Lee el archivo sin superar max_bytes."""
    data = bytearray()
    while chunk := await upload.read(1024 * 1024):
        data.extend(chunk)
        if len(data) > max_bytes:
            raise AppError(
                "file_too_large",
                f"La imagen supera el tamaño máximo de {max_bytes / 1024 / 1024:.0f} MB.",
                413,
            )
    return bytes(data)


def validate_image(filename: str, content: bytes, settings: Settings) -> ValidatedImage:
    ext = PurePosixPath(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError("invalid_file", "Formato no permitido. Usa JPG, JPEG, PNG o WEBP.", 415)
    if not content:
        raise AppError("invalid_file", "El archivo está vacío.", 422)
    if len(content) > settings.max_image_bytes:
        raise AppError("file_too_large", f"La imagen supera el máximo de {settings.max_image_mb:g} MB.", 413)
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    try:
        with Image.open(io.BytesIO(content)) as im:
            fmt = im.format or ""
            width, height = im.size
            if fmt not in ALLOWED_FORMATS:
                raise AppError("invalid_file", "El contenido no es una imagen JPG, PNG o WEBP válida.", 415)
            if width * height > settings.max_image_pixels:
                raise AppError("invalid_file", "La imagen tiene demasiados píxeles.", 413)
            im.load()
    except AppError:
        raise
    except Image.DecompressionBombError:
        raise AppError("invalid_file", "La imagen tiene demasiados píxeles.", 413) from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise AppError("invalid_file", "El archivo no es una imagen válida o está dañado.", 422) from None
    return ValidatedImage(filename, content, fmt, width, height)
