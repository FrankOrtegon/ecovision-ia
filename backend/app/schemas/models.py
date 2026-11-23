"""Contratos de la API (Pydantic)."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

ClassName = Literal["cardboard", "glass", "metal", "paper", "plastic", "trash"]
CLASS_NAMES: tuple[ClassName, ...] = ("cardboard", "glass", "metal", "paper", "plastic", "trash")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail


class Limits(BaseModel):
    max_image_mb: float
    max_batch_files: int
    max_eval_files: int
    low_confidence_threshold: float
    allowed_extensions: list[str]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    environment: str
    model_configured: bool
    limits: Limits


class ClassProbability(BaseModel):
    label: ClassName
    probability: float = Field(ge=0, le=1)


class PredictionResult(BaseModel):
    filename: str
    predicted_label: ClassName
    confidence: float = Field(ge=0, le=1)
    low_confidence: bool
    probabilities: list[ClassProbability]
    estimated_probabilities: bool = Field(
        default=False,
        description=(
            "True si el proveedor omitió clases con probabilidad muy baja (menos de ~1 %) y se "
            "estimaron repartiendo el residuo 1 - suma entre ellas."
        ),
    )
    resolved_model: str | None = Field(
        default=None, description="Modelo que el proveedor resolvió para esta predicción."
    )


class PredictResponse(BaseModel):
    result: PredictionResult
    model_id: str
    latency_ms: int


class BatchItem(BaseModel):
    filename: str
    status: Literal["ok", "error"]
    result: PredictionResult | None = None
    error: str | None = None
    error_code: str | None = None


class BatchResponse(BaseModel):
    items: list[BatchItem]
    total: int
    succeeded: int
    failed: int
    model_id: str
    latency_ms: int


class ModelInfo(BaseModel):
    status: Literal["ready", "pending_training"]
    name: str
    version: str | None = None
    model_id: str | None = None
    dataset: str
    dataset_url: str
    platform: str
    architecture: str | None = None
    classes: list[ClassName]
    training_config: dict[str, Any] = Field(default_factory=dict)
    trained_at: date | None = None
    metrics: dict[str, Any] | None = None
    limitations: list[str] = Field(default_factory=list)
    notes: str | None = None


class PerClassMetrics(BaseModel):
    label: ClassName
    support: int
    predicted: int
    precision: float | None
    recall: float | None
    f1: float | None


class AveragedMetrics(BaseModel):
    precision: float | None
    recall: float | None
    f1: float | None


class ConfusionMatrix(BaseModel):
    labels: list[ClassName]
    matrix: list[list[int]]


class Curve(BaseModel):
    label: ClassName
    x: list[float] | None
    y: list[float] | None
    score: float | None
    note: str | None = None


class Confusion(BaseModel):
    true: ClassName
    predicted: ClassName
    count: int
    share_of_true_class: float


class EvaluationRow(BaseModel):
    filename: str
    true_label: ClassName
    predicted_label: ClassName
    confidence: float
    probabilities: list[ClassProbability]


class EvaluationResponse(BaseModel):
    model_id: str
    resolved_models: list[str]
    n_requested: int
    n_evaluated: int
    n_estimated_probabilities: int
    accuracy: float
    per_class: list[PerClassMetrics]
    macro: AveragedMetrics
    weighted: AveragedMetrics
    confusion_matrix: ConfusionMatrix
    roc: list[Curve]
    auc_macro: float | None
    auc_macro_note: str | None
    pr: list[Curve]
    ap_macro: float | None
    top_confusions: list[Confusion]
    rows: list[EvaluationRow]
    failed: list[BatchItem]
    unmatched_images: list[str]
    unmatched_labels: list[str]
    warnings: list[str]
