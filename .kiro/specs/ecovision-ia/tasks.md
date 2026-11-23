# Plan de implementación — EcoVision IA

Ordenado por dependencias. Un punto "BLOQUEO MANUAL" detiene solo esa etapa.

## Fase 1: Requisitos, arquitectura y estructura
- [x] 1.1 Especificación (requirements, design, tasks)
- [x] 1.2 Estructura de carpetas, `.gitignore`, `README.md`, `.env.example`, `git init`
- [x] 1.3 Documentos base en `docs/` (los resultados quedan marcados "pendiente de ejecución")
- [x] 1.4 Entorno Python 3.12 con `uv` (`.venv` en la raíz con las dependencias de `ml/pyproject.toml`; versiones se fijarán con lockfile al cerrar la Fase 2)
- [x] 1.5 Verificación: estructura completa y documentos presentes

## Fase 2: Dataset
- [x] 2.1 `01_download_dataset.py`: descarga TrashNet y registra origen, fecha y hashes. Verificar licencia y forma de distribución (el repositorio ofrece el dataset redimensionado en `dataset-resized.zip`).
- [x] 2.2 `02_explore_dataset.py`: conteos, integridad, formatos, dimensiones, duplicados, balance, gráficos, cuadrícula de ejemplos
- [x] 2.3 `03_split_dataset.py`: 70/15/15 estratificado, seed 42, sin fuga; CSV
- [x] 2.4 Pruebas de fuga y estratificación
- [x] 2.5 `04_prepare_roboflow_upload.py`
- [x] 2.6 `docs/dataset.md` con cifras reales

## Fase 3: Entrenamiento en Roboflow
- [x] 3.1 Verificar documentación vigente de Roboflow (UI, límites del plan, formatos de carga)
- [x] 3.2 BLOQUEO MANUAL (modelos 1 y 2 entrenados; v1 seleccionada con validación): crear cuenta/proyecto, subir particiones, entrenar versión base y ajustada. Entregar al agente: workspace, project id, versión, API key en `.env`
- [x] 3.3 Registrar `ml/results/training_log.json` y `backend/app/data/model_info.json` con datos reales
- [x] 3.4 Llamada de prueba real: el proveedor omite clases con p < ~1 % incluso con confidence=0; se estiman con el residuo y se marca (ver docs/training.md)
- [x] 3.5 `docs/training.md`

## Fase 4: Evaluación
- [x] 4.1 Paquete `ecovision_eval` (métricas, ROC OvR, AUC, matriz, confusiones, gráficos; se añadió Precision-Recall y AP por clase, recomendado en RED4 para clases desbalanceadas)
- [x] 4.2 Pruebas con casos calculables a mano y clase sin positivos (15 pruebas)
- [x] 4.3 `05_run_evaluation.py` ejecutado sobre `test.csv` (una vez, con `--final`) y `06_analyze_results.py`
- [x] 4.4 `docs/evaluation.md` con resultados reales y análisis

## Fase 5: Backend
- [x] 5.1 Configuración, logging, CORS, manejo de errores
- [x] 5.2 Schemas Pydantic
- [x] 5.3 Validación de imágenes
- [x] 5.4 Adaptador Roboflow (timeout, errores). Verificación contra el modelo real pendiente de Fase 3 (3.4)
- [x] 5.5 Endpoints health, model/info, predict, predict/batch, evaluate
- [x] 5.6 Pruebas: éxito, error, entradas inválidas, límites
- [x] 5.7 Ruff + mypy limpios

## Fase 6: Frontend
- [x] 6.1 Vite + React + TS + Tailwind + Router + Recharts + Axios
- [x] 6.2 Layout, navegación, tema verde
- [x] 6.3 Inicio · 6.4 Clasificador · 6.5 Lotes · 6.6 Evaluación · 6.7 Acerca del modelo
- [x] 6.8 Vitest, `tsc`, `eslint`, build

## Fase 7: Integración
- [x] 7.1 Ejecución local completa con modelo real
- [x] 7.2 Pruebas de extremo a extremo manuales documentadas
- [x] 7.3 Revisión de seguridad (CA-5)

## Fase 8: Despliegue
- [x] 8.1 Verificar planes y límites vigentes de Render y Vercel
- [ ] 8.2 BLOQUEO MANUAL: cuentas y variables de entorno en los proveedores
- [ ] 8.3 Despliegue backend, luego frontend, ajuste de CORS
- [ ] 8.4 Prueba de humo en producción
- [ ] 8.5 `docs/deployment.md`

## Fase 9: Evidencias
- [~] 9.1 Capturas reales y `docs/evidence-checklist.md` completo
- [x] 9.2 `docs/video-script.md` (máx. 10 min)
- [x] 9.3 Insumos del informe APA 7 con referencias verificadas

## Evidencias por criterio de la rúbrica

| Criterio | Evidencia concreta |
|---|---|
| 1 Contexto (1 pt) | `docs/requirements.md`, página Inicio, sección del informe |
| 2 Dataset (1 pt) | `docs/dataset.md`, `ml/results/dataset_summary.json`, gráficos, CSV de particiones, script de partición |
| 3 Entrenamiento y evaluación (1 pt) | `training_log.json`, capturas de Roboflow, `ml/results/` (matriz, ROC, AUC, reporte), `docs/evaluation.md` |
| 4 Interfaz (1 pt) | URL desplegada, `/docs` del backend, capturas de cada módulo, pruebas pasando |
| 5 Video (1 pt) | `docs/video-script.md`, lista de tomas, grabación ≤ 10 min |
