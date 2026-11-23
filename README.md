# EcoVision IA

Sistema inteligente de clasificación de residuos mediante visión por computador. Proyecto de maestría.

Clasifica el **material aparente** de una imagen en seis categorías de TrashNet (cartón, vidrio, metal, papel, plástico, otros residuos). No determina si un residuo es reciclable.

## Estado

| Fase | Estado |
|---|---|
| 1. Requisitos, arquitectura, estructura | Completa |
| 2. Dataset | Completa |
| 3. Entrenamiento en Roboflow | Pendiente (requiere pasos manuales) |
| 4. Evaluación | Módulo listo; falta la ejecución sobre el conjunto de prueba |
| 5. Backend | Implementado y probado con dobles; falta probar con el modelo real |
| 6. Frontend | Pendiente |
| 7. Integración | Pendiente |
| 8. Despliegue | Pendiente |
| 9. Evidencias | Pendiente |

Los resultados del modelo se publican aquí solo después de ejecutarse.

## Estructura

```
backend/    API FastAPI
frontend/   SPA React + TypeScript + Vite + Tailwind
ml/         scripts de datos, evaluación y resultados
docs/       documentación académica y técnica
tests/      pruebas transversales
.kiro/specs/ecovision-ia/   requisitos, diseño y tareas
```

## Requisitos de entorno

- Python 3.12 (3.11 o superior), gestionado con `uv`
- Node.js 20 o superior
- Cuenta de Roboflow (Fase 3)

## Ejecutar el backend en desarrollo

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ml/evaluation -e "backend[dev]"
cp backend/.env.example backend/.env      # completar ROBOFLOW_* (Fase 3)
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload
```

Documentación interactiva en http://localhost:8000/docs.
Pruebas: `cd backend && ../.venv/bin/python -m pytest`, y `.venv/bin/python -m pytest tests` desde la raíz.

## Seguridad

La API key de Roboflow vive solo en `backend/.env`. Usa `backend/.env.example` como plantilla.

## Documentación

Ver `docs/` y `.kiro/specs/ecovision-ia/`.
