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

**Validación** (378 imágenes; para elegir modelo): ver `docs/training.md` y `ml/results/eval_val_v1/`, `eval_val_v2/`.

**Prueba (evaluación oficial, una sola ejecución con `--final`, modelo `ecovision-trashnet/1`)**, 379 imágenes, `ml/results/eval_test_v1/`:

| Métrica | Valor |
|---|---|
| Exactitud | 0,8865 (IC 95 % bootstrap: 0,8549 a 0,9182) |
| Precisión macro / recall macro | 0,8523 / 0,8620 |
| F1 macro | 0,8561 (IC 95 %: 0,812 a 0,896) |
| F1 ponderado | 0,8871 |
| AUC macro (aproximada) | 0,9805 (IC 95 %: 0,964 a 0,993) |
| AP macro (aproximada) | 0,9176 |

Por clase (F1): cartón 0,906, vidrio 0,899, metal 0,900, papel 0,875, plástico 0,937, otros residuos 0,619 (20 imágenes). AUC por clase entre 0,940 (otros residuos) y 0,997 (plástico).

La aplicación reproduce las mismas cifras al evaluar el conjunto de prueba a través de `POST /api/evaluate` (18 s para 379 imágenes).

## Análisis

- La exactitud de prueba (0,8865) es menor que la de validación (0,9365). Es coherente con que el mejor punto del entrenamiento se eligió con la validación, lo que la hace optimista; la prueba es la estimación insesgada.
- Confusión principal: papel clasificado como cartón (9 imágenes, 9,9 % de la clase). Otros residuos es la clase más débil (F1 0,619; AP 0,706): es la minoritaria y la más heterogénea.
- Calibración: el modelo es sobreconfiado (confianza media 94,8 % frente a 88,65 % de exactitud; ECE 0,064).
- Confianza baja (< 60 %): marca 13 de 379 imágenes; en ellas la exactitud es 23,1 % frente a 91,0 % en el resto, y captura 10 de los 43 errores.
- Las probabilidades omitidas por el proveedor (< ~1 %) se estimaron en 376 de 379 imágenes; el efecto en el AUC macro es de 0,002.

Análisis completo, figuras y referencias: `docs/Informe_EcoVision_IA.pdf`.
