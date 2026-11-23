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

## Pendiente
- Versión con aumento de datos (misma arquitectura) y comparación con la línea base usando la validación.
- Opcional: otra arquitectura (ViT Base o DINOv3) si los créditos alcanzan.
- Registrar la versión seleccionada en `backend/app/data/model_info.json`.
