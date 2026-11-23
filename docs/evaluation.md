# Evaluación

Estado: pendiente (Fase 4). No hay resultados todavía.

## Protocolo
- Conjunto: `test.csv`, usado una sola vez con el modelo ya seleccionado.
- Métricas: accuracy, precision/recall/F1 por clase, macro y ponderadas, matriz de confusión, ROC one-vs-rest y AUC calculadas con probabilidades por clase.
- Si una clase no tiene positivos o negativos, su AUC no se calcula y se explica.
- Salidas en `ml/results/`: etiquetas reales y predichas, probabilidades, métricas, gráficos, reporte y versión del modelo.

## Formato del CSV de evaluación de la aplicación
```
filename,true_label
img001.jpg,plastic
img002.jpg,glass
```
UTF-8, cabecera obligatoria, etiquetas entre: cardboard, glass, metal, paper, plastic, trash.

## Implementación
Paquete `ml/evaluation/ecovision_eval` (instalable con `uv pip install -e ml/evaluation`). Pruebas en `tests/test_eval_metrics.py` con casos calculados a mano. Además de lo anterior se calculan curvas Precision-Recall y AP por clase, porque el curso (Unidad 2, RED4) las recomienda cuando las clases están desbalanceadas, como ocurre con `trash` (5,4 % del dataset).

Reglas de cálculo:
- La clase predicha es el argmax de las probabilidades.
- Si una clase no tiene ejemplos reales, sus métricas se reportan como no disponibles y los promedios se calculan sin ella.
- La AUC macro solo se reporta si la AUC está definida para todas las clases.

## Resultados y análisis
Pendiente de ejecución.
