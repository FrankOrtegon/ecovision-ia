"""Evaluación de clasificación multiclase con probabilidades por clase."""
from .constants import CLASSES
from .metrics import EvaluationResult, compute_metrics
from .report import save_results

__all__ = ["CLASSES", "EvaluationResult", "compute_metrics", "save_results"]
