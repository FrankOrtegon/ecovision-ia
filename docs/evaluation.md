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

## Estimación de probabilidades omitidas y su efecto
El proveedor omite las clases con probabilidad menor a ~1 %, incluso con `confidence=0`. El backend y el script de evaluación reparten el residuo (1 − suma) entre las clases omitidas (`ml/results/eval_val_*/sensitivity_fill.json`).

| Modelo (validación) | Imágenes con probabilidades estimadas | Imágenes con 0 o 1 clase omitida (estimación exacta) | AUC macro residuo / relleno con 0 | AP macro residuo / relleno con 0 |
|---|---|---|---|---|
| v1 | 373 de 378 | 10 (2,6 %) | 0,9888 / 0,9823 | 0,9429 / 0,9387 |
| v2 | 378 de 378 | 4 (1,1 %) | 0,9852 / 0,9743 | 0,9301 / 0,9218 |

La accuracy, la precision, el recall y el F1 no dependen de esta estimación (usan la clase de mayor probabilidad). La AUC, la AP y las curvas sí: la elección del método mueve la AUC macro entre 0,007 y 0,011 y la AUC de una clase hasta 0,04. Por eso la AUC se reporta como **aproximada**. Solo calcular el softmax completo con los pesos descargados eliminaría la aproximación.

## Resultados
- Validación (para elegir modelo): ver `docs/training.md` y `ml/results/eval_val_v1/`, `eval_val_v2/`.
- Prueba (evaluación oficial): **pendiente**, una sola ejecución con el modelo elegido.

## Análisis
Pendiente hasta ejecutar la evaluación sobre el conjunto de prueba.
