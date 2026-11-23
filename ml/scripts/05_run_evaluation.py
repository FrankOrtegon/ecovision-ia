"""Evalúa un modelo de Roboflow sobre una partición con el paquete ecovision_eval.

Usa exactamente el mismo cliente y la misma estimación de probabilidades omitidas que el backend.

Uso:
    python 05_run_evaluation.py --split val  --model-id ecovision-trashnet/1 --tag v1
    python 05_run_evaluation.py --split test --model-id ecovision-trashnet/2 --tag v2 --final

El conjunto de prueba solo se evalúa con --final, una vez elegido el modelo con la validación.
Cada evaluación sobre test queda registrada en ml/results/test_run_log.json.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
from ecovision_eval import CLASSES, compute_metrics, save_results

from app.core.config import Settings
from app.integrations.roboflow import ProviderResult, RoboflowClient
from app.services.prediction import build_result
from common import DATASET_DIR, ML_DIR, RESULTS_DIR, SEED, SPLITS_DIR, write_json

ENV_PATH = ML_DIR.parent / "backend" / ".env"


async def classify_all(client: RoboflowClient, paths: list[Path], concurrency: int) -> list[ProviderResult | Exception]:
    sem = asyncio.Semaphore(concurrency)

    async def one(p: Path) -> ProviderResult | Exception:
        async with sem:
            try:
                return await client.classify(p.read_bytes())
            except Exception as exc:  # noqa: BLE001 - se reporta y se aborta más abajo
                return exc

    return list(await asyncio.gather(*(one(p) for p in paths)))


def zero_fill(raw: ProviderResult) -> list[float]:
    return [raw.probabilities.get(c, 0.0) for c in CLASSES]


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ML_DIR, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "desconocido"


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["val", "test"], required=True)
    ap.add_argument("--model-id", required=True, help="proyecto/versión, por ejemplo ecovision-trashnet/1")
    ap.add_argument("--tag", required=True, help="etiqueta corta para la carpeta de resultados")
    ap.add_argument("--final", action="store_true", help="obligatorio para evaluar el conjunto de prueba")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    if args.split == "test" and not args.final:
        sys.exit("El conjunto de prueba solo se evalúa con --final, después de elegir el modelo con la validación.")

    df = pd.read_csv(SPLITS_DIR / f"{args.split}.csv")
    paths = [DATASET_DIR / rel for rel in df["relpath"]]
    settings = Settings(_env_file=str(ENV_PATH), roboflow_model_id=args.model_id)  # type: ignore[call-arg]
    if not settings.model_configured:
        sys.exit("Falta ROBOFLOW_API_KEY en backend/.env")

    started = dt.datetime.now(dt.timezone.utc)
    async with httpx.AsyncClient(timeout=httpx.Timeout(settings.roboflow_timeout_s)) as http:
        client = RoboflowClient(http, settings)
        print(f"Evaluando {len(paths)} imágenes de '{args.split}' con {args.model_id}…")
        raw = await classify_all(client, paths, args.concurrency)

    failures = [(df["filename"][i], type(r).__name__) for i, r in enumerate(raw) if isinstance(r, Exception)]
    if failures:
        sys.exit(f"{len(failures)} imágenes fallaron (ej.: {failures[:3]}). Evaluación abortada, no se guardó nada.")
    provider: list[ProviderResult] = [r for r in raw if isinstance(r, ProviderResult)]

    results = [build_result(fn, pr, settings.low_confidence_threshold) for fn, pr in zip(df["filename"], provider, strict=True)]
    proba = np.array([[p.probability for p in r.probabilities] for r in results])
    y_true = df["label"].tolist()
    metrics = compute_metrics(y_true, proba)

    # Sensibilidad: estimación por residuo (principal) frente a rellenar con 0.
    metrics_zero = compute_metrics(y_true, np.array([zero_fill(p) for p in provider]))
    sens = {
        "method_primary": "residuo (1 - suma) repartido entre las clases omitidas",
        "method_alternative": "rellenar con 0 las clases omitidas",
        "images_with_estimated_probabilities": sum(r.estimated_probabilities for r in results),
        "n_images": len(results),
        "auc_macro": {"residual": metrics.auc_macro, "zero_fill": metrics_zero.auc_macro},
        "ap_macro": {"residual": metrics.ap_macro, "zero_fill": metrics_zero.ap_macro},
        "auc_per_class": {
            c.label: {"residual": c.score, "zero_fill": z.score} for c, z in zip(metrics.roc, metrics_zero.roc, strict=True)
        },
        "accuracy_identical": metrics.accuracy == metrics_zero.accuracy,
    }

    resolved = sorted({p.resolved_model for p in provider if p.resolved_model})
    out_dir = RESULTS_DIR / f"eval_{args.split}_{args.tag}"
    config: dict[str, Any] = {
        "model_id_requested": args.model_id,
        "resolved_models": resolved,
        "split": args.split,
        "n_images": len(results),
        "split_csv": f"ml/results/splits/{args.split}.csv",
        "seed": SEED,
        "provider": "Roboflow Serverless API",
        "request_confidence_param": settings.roboflow_confidence_percent,
        "probability_estimation": sens["method_primary"],
        "evaluated_at_utc": started.isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "final_evaluation": bool(args.final),
    }
    save_results(metrics, df["filename"].tolist(), y_true, proba, out_dir, config)
    write_json(out_dir / "sensitivity_fill.json", sens)
    (out_dir / "raw_provider_probabilities.json").write_text(
        json.dumps({fn: pr.probabilities for fn, pr in zip(df["filename"], provider, strict=True)}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.split == "test":
        log_path = RESULTS_DIR / "test_run_log.json"
        log = json.loads(log_path.read_text()) if log_path.exists() else []
        log.append({"at_utc": config["evaluated_at_utc"], "model_id": args.model_id, "resolved": resolved, "tag": args.tag})
        write_json(log_path, log)

    print(f"\nModelo(s): {', '.join(resolved)}")
    print(f"Accuracy {metrics.accuracy:.4f} | P macro {metrics.macro['precision']:.4f} | R macro {metrics.macro['recall']:.4f} | "
          f"F1 macro {metrics.macro['f1']:.4f} | AUC macro {metrics.auc_macro} | AP macro {metrics.ap_macro}")
    for pc in metrics.per_class:
        print(f"  {pc.label:<10} P={pc.precision:.3f} R={pc.recall:.3f} F1={pc.f1:.3f} n={pc.support}")
    print(f"Guardado en {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
