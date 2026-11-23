# Requisitos — EcoVision IA

Sistema de clasificación de residuos mediante visión por computador (TrashNet + Roboflow + FastAPI + React).

## Glosario

- **Backend**: servicio FastAPI. Único componente que posee la API key de Roboflow.
- **Frontend**: SPA React/TypeScript. Solo consume el Backend.
- **Modelo**: clasificador multiclase entrenado y alojado en Roboflow.
- **Clases**: `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`.
- **Confianza baja**: probabilidad máxima menor que `LOW_CONFIDENCE_THRESHOLD` (configurable, valor inicial 0.60; se justificará con los resultados reales de validación).

## Alcance y restricciones

- El sistema clasifica el material aparente. No determina si un residuo es reciclable.
- Ninguna métrica, captura o conclusión se escribe antes de obtenerse de una ejecución real.
- Una operación en Roboflow que requiera acción manual detiene solo esa etapa hasta recibir credenciales o identificadores.

## Requisitos funcionales

### RF-1 Dataset (Fase 2)
1. WHEN se ejecuta el script de descarga, THE sistema SHALL obtener TrashNet, registrar origen y fecha, y calcular el conteo real por clase.
2. THE sistema SHALL verificar integridad (apertura con Pillow), formatos, dimensiones y duplicados exactos (hash SHA-256) y casi exactos (hash perceptual).
3. THE sistema SHALL generar particiones estratificadas 70/15/15 con semilla 42, sin imágenes duplicadas entre particiones.
4. THE sistema SHALL exportar `train.csv`, `val.csv`, `test.csv` con `filename,label,split,sha256`.
5. THE sistema SHALL aplicar aumento de datos únicamente sobre entrenamiento.
6. THE sistema SHALL mantener `test` sin uso hasta la evaluación definitiva.
7. THE sistema SHALL generar gráficos de distribución por clase y una cuadrícula de ejemplos por clase.

### RF-2 Entrenamiento (Fase 3)
1. THE proyecto SHALL documentar instrucciones verificadas contra la documentación vigente de Roboflow para crear el proyecto, importar las particiones y entrenar.
2. THE proyecto SHALL registrar en `ml/results/training_log.json` la configuración, versión, fecha real y métricas de cada entrenamiento.
3. WHERE sea viable, THE proyecto SHALL comparar un modelo inicial y uno ajustado, justificando el ajuste.
4. THE proyecto SHALL identificar la versión seleccionada y su `model_id` (`proyecto/versión`).

### RF-3 Evaluación científica (Fase 4)
1. THE módulo `ml/evaluation` SHALL calcular accuracy, precision/recall/F1 por clase, macro y ponderados, matriz de confusión, curvas ROC one-vs-rest, AUC por clase y AUC macro.
2. THE módulo SHALL usar probabilidades por clase para ROC/AUC, nunca etiquetas predichas.
3. IF una clase carece de positivos o negativos, THEN THE módulo SHALL omitir su AUC e informar el motivo.
4. THE módulo SHALL guardar etiquetas reales, predichas, probabilidades, métricas, gráficos, reporte de clasificación y configuración/versión del modelo.
5. THE módulo SHALL listar las confusiones más frecuentes entre clases.
6. THE módulo SHALL ser importable por el Backend (una sola implementación de métricas).

### RF-4 API (Fase 5)
| Endpoint | Función |
|---|---|
| `GET /api/health` | Estado del servicio y de la configuración (sin exponer secretos). |
| `GET /api/model/info` | Metadatos del modelo leídos de `model_info.json` real. |
| `POST /api/predict` | Una imagen → clase, confianza, probabilidades por clase. |
| `POST /api/predict/batch` | Varias imágenes → resultados por archivo y errores por archivo. |
| `POST /api/evaluate` | Imágenes + CSV `filename,true_label` → métricas completas. |

1. THE API SHALL validar extensión (JPG, JPEG, PNG, WEBP), tipo real del contenido (Pillow), tamaño máximo y cantidad máxima.
2. THE API SHALL exponer OpenAPI y Swagger (`/docs`).
3. THE API SHALL usar modelos Pydantic para toda solicitud y respuesta.
4. IF Roboflow falla o excede el timeout, THEN THE API SHALL responder 502/504 con un mensaje claro sin filtrar secretos.
5. THE API SHALL NOT persistir imágenes; el procesamiento ocurre en memoria.
6. IF el Modelo no está configurado, THEN `/api/predict*` SHALL responder 503 con un mensaje explícito, no una predicción falsa.

### RF-5 Frontend (Fase 6)
1. **Inicio**: nombre, contexto, objetivo, seis categorías, funcionamiento, enlace al clasificador.
2. **Clasificador**: carga, vista previa, validación, predicción real, barras de probabilidad, aviso de confianza baja, errores no bloqueantes.
3. **Lotes**: múltiples imágenes, tabla (archivo, categoría, confianza), estado, exportación CSV, listado de fallos.
4. **Evaluación**: carga de imágenes y CSV, tablas de métricas, matriz de confusión, ROC con AUC, exportación.
5. **Acerca del modelo**: datos de `/api/model/info`; campos no disponibles se muestran como "Pendiente", nunca inventados.
6. Interfaz en español, responsive, verde/blanco/gris, estados vacíos, carga y error.

### RF-6 Documentación (todas las fases)
`docs/` SHALL contener requirements, architecture, dataset, training, evaluation, deployment, evidence-checklist y video-script. Las secciones de resultados se completan solo con datos reales.

## Requisitos no funcionales

- **RNF-1 Seguridad**: API key solo en backend vía `.env`; `.env.example` sin secretos; CORS con orígenes explícitos; límites de tamaño y cantidad; timeouts en llamadas externas.
- **RNF-2 Reproducibilidad**: semilla 42, versiones fijadas, scripts ejecutables de principio a fin.
- **RNF-3 Calidad**: tipado (mypy/tsc estricto), pytest, ruff, logging estructurado.
- **RNF-4 Privacidad**: sin almacenamiento permanente de imágenes ni datos personales.
- **RNF-5 Rendimiento**: lote con concurrencia acotada; mensaje de progreso en la UI.
- **RNF-6 Despliegue**: dev y prod configurables; frontend en Vercel, backend en Render (o equivalente), modelo en Roboflow. Planes y límites se verifican en la Fase 8.
- **RNF-7 Mantenibilidad**: capas separadas (presentación, servicios, integración, evaluación, configuración).

## Criterios de aceptación globales

| Id | Criterio | Verificación |
|---|---|---|
| CA-1 | Conteos por clase del dataset coinciden con los archivos descargados | `ml/results/dataset_summary.json` generado por script |
| CA-2 | Ninguna imagen (hash) aparece en dos particiones | Prueba automatizada |
| CA-3 | Predicción devuelve 6 probabilidades que suman ≈ 1 | pytest + prueba manual real |
| CA-4 | ROC/AUC calculadas desde probabilidades | Prueba con datos sintéticos conocidos (solo en tests) |
| CA-5 | La API key no aparece en el bundle del frontend ni en respuestas | Búsqueda en `dist/` y revisión de respuestas |
| CA-6 | Frontend desplegado clasifica una imagen real vía backend desplegado | Captura y video |
| CA-7 | Cada criterio de la rúbrica tiene evidencia enlazada | `docs/evidence-checklist.md` |
