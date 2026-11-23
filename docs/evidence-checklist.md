# Lista de evidencias por criterio de la rúbrica

Estado al 2026-11-23. "Listo" significa que existe y se puede verificar en el repositorio.

| Criterio | Evidencia | Estado |
|---|---|---|
| 1. Contexto y área (1 pt) | `docs/requirements.md`; secciones Introducción y Contexto del informe | Listo |
| 1. Contexto y área | Captura del módulo Inicio (`docs/evidence/app_01_inicio.png`) | Listo |
| 2. Dataset (1 pt) | `docs/dataset.md`, `ml/results/dataset_summary.json`, `dataset_source.json` | Listo |
| 2. Dataset | Distribución y ejemplos por clase (`docs/informe/fig/distribucion.png`, `ejemplos.png`) | Listo |
| 2. Dataset | `ml/results/splits/{train,val,test}.csv`, scripts `01`–`04`, `tests/test_dataset_splits.py` | Listo |
| 3. Entrenamiento y evaluación (1 pt) | `ml/results/training_log.json` y `docs/training.md` | Listo |
| 3. Entrenamiento y evaluación | Capturas de Roboflow (proyecto, versiones, curvas, receta de aumento) | **Pendiente: guardar en `docs/evidence/` las capturas que ya tienes** |
| 3. Entrenamiento y evaluación | Matriz de confusión, ROC, PR, AUC, reporte (`ml/results/eval_test_v1/`) | Listo |
| 3. Entrenamiento y evaluación | `docs/evaluation.md` y secciones Evaluación y Discusión del informe | Listo |
| 4. Interfaz (1 pt) | Capturas de Inicio, Clasificador, Lotes, Evaluación, Modelo (`docs/evidence/app_*.png`) | Listo |
| 4. Interfaz | Pruebas automatizadas pasando (100) | Listo |
| 4. Interfaz | URL del frontend y del backend (`/docs`) desplegados | **Pendiente: publicar en Render y Vercel (`docs/deployment.md`)** |
| 5. Video (1 pt) | `docs/video-script.md` | Listo |
| 5. Video | Grabación de 10 minutos como máximo | **Pendiente** |
| Informe | `docs/Informe_EcoVision_IA.pdf` (APA 7); datos de portada | **Pendiente: completar segundo integrante, universidad y docente** |
