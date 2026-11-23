# Diseño técnico — EcoVision IA

## 1. Arquitectura

```
Navegador ── React SPA (Vercel)
                │  HTTPS, solo /api/*
                ▼
        FastAPI (Render)  ──► inference-sdk ──► Roboflow serverless (modelo)
                │
                └─ ecovision_eval (métricas scikit-learn, paquete compartido)
```

Capas del backend (`backend/app/`):

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Configuración | `core/config.py` | `pydantic-settings`, lectura de `.env` |
| Presentación (HTTP) | `api/routes/` | Rutas, códigos de estado |
| Contratos | `schemas/` | Modelos Pydantic |
| Servicios | `services/` | Validación de imágenes, orquestación de predicción y evaluación |
| Integración | `integrations/roboflow.py` | Cliente Roboflow con timeout, reintentos limitados y normalización de la respuesta |
| Evaluación | `ml/evaluation/ecovision_eval/` | Métricas y gráficos, reutilizado por backend y scripts |

Capas del frontend (`frontend/src/`): `pages/`, `components/`, `services/api.ts` (Axios), `types/`, `utils/` (CSV, formato).

## 2. Decisiones

| Decisión | Alternativas | Razón |
|---|---|---|
| `inference-sdk` (`InferenceHTTPClient`) contra `https://serverless.roboflow.com` | HTTP crudo, paquete `roboflow` | Es el cliente recomendado en la documentación actual. La llamada se aísla en un adaptador, por lo que cambiarla afecta un archivo. |
| Evaluación como paquete Python en `ml/evaluation` | Duplicar lógica en backend | Una sola fuente de métricas auditable. |
| Procesamiento en memoria | Guardar en disco | RNF-4. |
| Sin base de datos | PostgreSQL | No hay requisito de persistencia; YAGNI. |
| `model_info.json` versionado, generado a partir del entrenamiento real | Valores en código | Evita cifras inventadas. Si falta, `/api/model/info` marca los campos como pendientes. |

**Riesgo conocido**: un modelo de clasificación de Roboflow debe devolver las 6 probabilidades para calcular ROC. El formato documentado de clasificación monoetiqueta incluye `predictions` (lista de `class`/`confidence`) y `top`. En Fase 3 se verifica con una llamada real que se devuelvan todas las clases. Si no, se ajusta el umbral de confianza de la solicitud o se documenta la limitación de ROC.

## 3. Modelo de datos y contratos API

```python
ClassName = Literal["cardboard","glass","metal","paper","plastic","trash"]

class ClassProbability: label: ClassName; probability: float  # 0..1

class PredictionResult:
    filename: str
    predicted_label: ClassName
    confidence: float
    low_confidence: bool
    probabilities: list[ClassProbability]  # 6 elementos

class PredictResponse: result: PredictionResult; model_id: str; latency_ms: int

class BatchItem: filename: str; status: Literal["ok","error"]
                 result: PredictionResult | None; error: str | None
class BatchResponse: items: list[BatchItem]; total: int; succeeded: int; failed: int

class HealthResponse: status: Literal["ok","degraded"]; version: str
                      model_configured: bool

class ModelInfo: name, version, dataset, platform, classes, training_config: dict,
                 trained_at: date | None, metrics: dict | None, limitations: list[str],
                 status: Literal["ready","pending_training"]

class PerClassMetrics: label; precision; recall; f1; support
class RocCurve: label; fpr: list[float]; tpr: list[float]; auc: float | None; note: str | None
class EvaluationResponse:
    n_samples: int; n_matched: int; unmatched_images: list[str]; unmatched_labels: list[str]
    failed: list[BatchItem-like]; accuracy: float
    per_class: list[PerClassMetrics]
    macro: {precision, recall, f1}; weighted: {precision, recall, f1}
    confusion_matrix: {labels: list[str], matrix: list[list[int]]}
    roc: list[RocCurve]; auc_macro: float | None; warnings: list[str]
    top_confusions: list[{true, predicted, count}]
```

Errores: `{"detail": {"code": str, "message": str}}`. Códigos: `invalid_file`, `file_too_large`, `too_many_files`, `bad_csv`, `model_not_configured`, `upstream_error`, `upstream_timeout`.

Endpoints:
- `POST /api/predict`: `multipart/form-data`, campo `file`.
- `POST /api/predict/batch`: campo `files[]`.
- `POST /api/evaluate`: campos `files[]` y `labels_csv`. Formato CSV: UTF-8, cabecera `filename,true_label`, etiquetas en minúscula entre las 6 clases.

Configuración (`.env.example`): `ROBOFLOW_API_KEY`, `ROBOFLOW_API_URL`, `ROBOFLOW_MODEL_ID`, `ALLOWED_ORIGINS`, `MAX_IMAGE_MB`, `MAX_BATCH_FILES`, `MAX_EVAL_FILES`, `ROBOFLOW_TIMEOUT_S`, `LOW_CONFIDENCE_THRESHOLD`, `ENVIRONMENT`.

## 4. Estructura del repositorio

```
ecovision-ia/ (raíz del workspace)
├── .kiro/specs/ecovision-ia/{requirements,design,tasks}.md
├── backend/{app/, tests/, pyproject.toml, .env.example}
├── frontend/{src/, package.json, vite.config.ts, .env.example}
├── ml/{data/(ignorado), scripts/, notebooks/, evaluation/, results/}
├── docs/
├── tests/                # pruebas de integración transversales
├── .gitignore  README.md
```

## 5. Plan de datos, entrenamiento y evaluación

**Datos** (`ml/scripts/`): `01_download_dataset.py` → `02_explore_dataset.py` (conteos, integridad, duplicados, gráficos) → `03_split_dataset.py` (estratificado, seed 42, deduplicado antes de dividir) → `04_prepare_roboflow_upload.py` (estructura por carpetas `split/clase/` para importar con las particiones ya fijadas).

**Entrenamiento**: Roboflow, proyecto de clasificación multiclase. Se sube cada partición con su split asignado. Aumentos solo en `train` (los preprocesamientos de Roboflow se aplican a toda versión; las augmentations solo a train). Se entrena una versión base y una ajustada. Los parámetros disponibles se leen de la UI vigente y se registran. Se elige la versión por métricas de **validación**.

**Evaluación**: `05_run_evaluation.py` infiere sobre `test.csv` con el modelo seleccionado una sola vez y guarda `predictions.csv` (`filename,true,pred,prob_*`). `ecovision_eval` genera métricas y gráficos en `ml/results/`.

## 6. Pruebas

- Backend: pytest + `httpx` TestClient, con el adaptador Roboflow sustituido por un doble de prueba solo dentro de los tests. El servicio nunca incluye un modo simulado.
- Evaluación: casos con resultados calculables a mano, y caso con clase sin positivos.
- Frontend: Vitest + Testing Library para validación de archivos y exportación CSV; `tsc --noEmit` y `eslint`.

## 7. Seguridad

CORS con lista explícita; límites por archivo y por solicitud; validación del contenido real con Pillow (incluye límite de píxeles contra bombas de descompresión); sin logs de contenido de imágenes ni de la API key; cabeceras de seguridad básicas; el frontend solo conoce `VITE_API_BASE_URL`.

## 8. Despliegue

Backend en Render (Docker o runtime Python con `uvicorn`), frontend en Vercel con rewrite o `VITE_API_BASE_URL`. Se verifican planes, cold start y límites vigentes en Fase 8 antes de elegir.
