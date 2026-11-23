"""Diagnóstico: averigua qué ruta de Roboflow responde y con qué estructura.

Usa UNA imagen del conjunto de validación (nunca de test). Lee la clave de backend/.env.
No imprime la clave, las cabeceras ni las URLs con credenciales.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import httpx
import pandas as pd

from common import DATASET_DIR, ML_DIR, SPLITS_DIR

ENV_PATH = ML_DIR.parent / "backend" / ".env"
API = "https://serverless.roboflow.com"


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def summarize(payload: object) -> str:
    """Resume la estructura sin volcar contenido grande."""
    if isinstance(payload, list):
        return f"lista de {len(payload)} elementos; primer elemento: {summarize(payload[0]) if payload else '-'}"
    if isinstance(payload, dict):
        parts = []
        for k, v in payload.items():
            if k == "predictions" and isinstance(v, list):
                items = [(p.get("class"), round(float(p.get("confidence", 0)), 4)) for p in v if isinstance(p, dict)]
                parts.append(f"predictions({len(v)}): {items}")
            elif isinstance(v, (dict, list)):
                parts.append(f"{k}: {summarize(v)}")
            elif isinstance(v, str) and len(v) > 60:
                parts.append(f"{k}: <texto de {len(v)} caracteres>")
            else:
                parts.append(f"{k}: {v!r}")
        return "{" + "; ".join(parts) + "}"
    return repr(payload)


def main() -> None:
    env = load_env()
    key = env.get("ROBOFLOW_API_KEY", "")
    if not key:
        sys.exit("Falta ROBOFLOW_API_KEY en backend/.env")
    row = pd.read_csv(SPLITS_DIR / "val.csv").iloc[0]
    img = (DATASET_DIR / row["relpath"]).read_bytes()
    b64 = base64.b64encode(img)
    print(f"Imagen de validación: {row['filename']} (etiqueta real: {row['label']})\n")
    auth = {"Authorization": f"Bearer {key}"}
    workspace = env.get("ROBOFLOW_WORKSPACE", "franks-workspace-2rfjw")
    workflow = env.get(
        "ROBOFLOW_WORKFLOW_ID",
        "ecovision-trashnet-1-resnet50-t1-vecovision-trashnet-1-resnet50-t1-logic",
    )
    tests: list[tuple[str, httpx.Request]] = []
    for model_id in ("ecovision-trashnet/1", "ecovision-trashnet-1-resnet50-t1"):
        for conf in ("0", "1"):
            tests.append(
                (
                    f"modelo '{model_id}' confidence={conf} (cabecera Bearer)",
                    httpx.Request(
                        "POST", f"{API}/{model_id}", params={"confidence": conf},
                        headers={**auth, "Content-Type": "application/x-www-form-urlencoded"}, content=b64,
                    ),
                )
            )
    tests.append(
        (
            "workflow (cabecera Bearer)",
            httpx.Request(
                "POST", f"{API}/{workspace}/workflows/{workflow}", headers=auth,
                json={"inputs": {"image": {"type": "base64", "value": b64.decode()}}},
            ),
        )
    )
    with httpx.Client(timeout=60) as http:
        for label, req in tests:
            try:
                resp = http.send(req)
            except httpx.HTTPError as exc:
                print(f"[{label}] error de red: {type(exc).__name__}\n")
                continue
            try:
                body = summarize(resp.json())
            except (json.JSONDecodeError, ValueError):
                body = resp.text[:200]
            print(f"[{label}] HTTP {resp.status_code}\n  {body[:900]}\n")


if __name__ == "__main__":
    main()
