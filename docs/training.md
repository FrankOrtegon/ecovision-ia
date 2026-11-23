# Entrenamiento

Plataforma: Roboflow. Proyecto `ecovision-trashnet` (clasificación de una sola etiqueta), workspace `franks-workspace-2rfjw`. Guía de uso en `docs/roboflow-guide.md`. Registro estructurado en `ml/results/training_log.json`.

## Datos de entrada
Versión de dataset `v1-baseline-sin-aumento`: 2521 imágenes, Auto-Orient y Resize 224x224 (stretch), split respetado de nuestras carpetas: train 1764, valid 378, test 379. Las 6 clases (cardboard, glass, metal, paper, plastic, trash) coinciden con los conteos de `docs/dataset.md`.

## Modelo 1: línea base
| Campo | Valor |
|---|---|
| Nombre en Roboflow | `ecovision-trashnet-1-resnet50-t1` |
| Arquitectura | ResNet50 Classification (Apache-2.0) |
| Aumento de datos | Ninguno (ni en la versión ni en línea) |
| Hiperparámetros | Por defecto (épocas máximas 300; Roboflow no muestra el resto) |
| Finalización | 2026-11-22, 20:20 (hora local de la interfaz) |
| Épocas ejecutadas | 28 (curvas de 0 a 27); parece parada temprana, por confirmar |
| Créditos usados | 0,17 |
| Latencia de la API en la nube (Roboflow) | 3,5 ms |

Curvas (leídas de las gráficas, aproximadas): la accuracy de validación sube de ~72 % a ~90 % en las primeras 6 épocas, alcanza un máximo cercano a 93,6 % en la época 15 y termina cerca de 89,7 %. La pérdida de entrenamiento muestra picos repetidos de hasta ~1,4, señal de entrenamiento inestable.

### Aviso metodológico sobre el conjunto de prueba
Roboflow calculó automáticamente métricas sobre el conjunto de prueba (precision 87,2 %, recall 88,5 %, F1 87,6 % con un umbral de confianza de 34 %) y se vieron en pantalla. No se usaron para elegir modelo; la selección se hace con validación. Las métricas oficiales se calcularán con `ml/evaluation`. Se declara en el informe como limitación.
Las "Improvement Recommendations" de Roboflow se basan en un único objeto fallado y en conceptos de detección (objetos pequeños, SAHI); no se consideran evidencia.

## Comportamiento verificado de la API de inferencia
Verificado con llamadas reales el 2026-11-23 usando imágenes de validación:
- `ROBOFLOW_MODEL_ID` es `ecovision-trashnet/1`. Responde HTTP 200 y resuelve al modelo `franks-workspace-2rfjw/ecovision-trashnet-1-resnet50-t1`.
- La autenticación con `Authorization: Bearer <clave>` funciona; la clave no necesita ir en la URL.
- No aparece ninguna clase `placeholder` en la respuesta, aunque sí en el gráfico de evaluación de la interfaz de Roboflow.
- Con `confidence=0` el proveedor devuelve solo las clases con probabilidad de aproximadamente 1 % o más. En una imagen (`plastic117`) vinieron 5 clases con suma 0,9948 y faltó `metal`. Con `confidence` entre 0 y 1 (por ejemplo 0.1) devuelve solo la mejor clase, por lo que el backend envía exactamente `0`.
- Consecuencia: las probabilidades omitidas se estiman repartiendo el residuo (1 menos la suma) entre las clases que faltan. Cada respuesta lo indica con `estimated_probabilities`. Las curvas ROC y PR de la evaluación son por tanto aproximadas en la cola de probabilidades bajas. En la Fase 4 se cuantificará esa aproximación comparando la estimación por residuo con rellenar con 0.
- Alternativa descartada por ahora: descargar los pesos y calcular el softmax completo en local. Evitaría la aproximación pero se aparta del modelo desplegado.

## Modelo 2: con aumento de datos en línea
| Campo | Valor |
|---|---|
| Nombre en Roboflow | `ecovision-trashnet-2-resnet50-t1` (dataset `v2-aumento-en-linea`, mismos datos y split que la v1) |
| Arquitectura | ResNet50 Classification |
| Aumento en línea (solo train, confirmado en la receta) | Flip horizontal y vertical (prob. 100 %), rotación ±15° (50 %), brillo ±15 % (50 %), exposición ±10 % (50 %) |
| Hiperparámetros | Por defecto (igual que la v1) |
| Créditos | No registrados |

La única diferencia con el modelo 1 es el aumento de datos.

## Comparación y selección (solo validación)
Evaluación con `ml/scripts/05_run_evaluation.py` sobre las 378 imágenes de validación, con el mismo cliente y la misma estimación de probabilidades que el backend. Resultados en `ml/results/eval_val_v1/` y `eval_val_v2/`.

| Métrica (validación) | v1 sin aumento | v2 con aumento |
|---|---|---|
| Accuracy | 0,9365 | 0,9286 |
| Precision macro | 0,9168 | 0,9006 |
| Recall macro | 0,9175 | 0,8937 |
| F1 macro | 0,9168 | 0,8966 |
| AUC macro (aproximada) | 0,9888 | 0,9852 |
| AP macro (aproximada) | 0,9429 | 0,9301 |
| F1 de `trash` (21 imágenes) | 0,762 | 0,650 |

Comparación pareada: v1 acierta 13 imágenes que v2 falla y v2 acierta 10 que v1 falla (McNemar exacto, p = 0,678). La diferencia de accuracy v1 − v2 es +0,0079, con intervalo de confianza del 95 % por bootstrap de [−0,016, +0,032], que incluye el cero.

**Decisión (2026-11-23):** no hay evidencia de que el aumento de datos mejore el modelo, así que se conserva el **modelo 1 (`ecovision-trashnet/1`)** por ser más simple. La coincidencia entre la accuracy de validación del modelo 1 (0,9365) y el máximo de su curva (~93,6 %, época 15) indica que Roboflow desplegó el mejor punto del entrenamiento.

Interpretación: el aumento de datos no redujo el sobreajuste de forma apreciable en este conjunto. Con una pérdida de entrenamiento inestable y solo 21 imágenes de `trash` en validación, las diferencias entre modelos están dentro del ruido de muestreo. No se probó otra arquitectura ni otros hiperparámetros; queda como trabajo futuro.

### Aviso sobre el conjunto de prueba
Roboflow mostró sus evaluaciones automáticas sobre test para ambos modelos (v1: precision 87,2 %, recall 88,5 %, F1 87,6 % con umbral 34 %; v2: precision 94,6 %, recall 88,0 %, F1 91,0 % con umbral 65 %). Se vieron en pantalla pero **no se usaron para elegir**, y no son comparables entre sí porque usan umbrales distintos y otra definición de métrica. La evaluación oficial sobre test se ejecutará una sola vez con `05_run_evaluation.py --final`; cada ejecución sobre test se registra en `ml/results/test_run_log.json`.

## Pendiente
- Evaluación final sobre el conjunto de prueba con el modelo elegido (Fase 4).
