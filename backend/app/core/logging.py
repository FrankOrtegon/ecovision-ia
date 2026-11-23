"""Configuración de logging. Los logs de httpx se silencian porque incluyen URLs completas."""

from __future__ import annotations

import logging


def setup_logging(environment: str) -> None:
    level = logging.DEBUG if environment == "development" else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
