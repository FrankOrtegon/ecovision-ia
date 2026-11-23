# EcoVision IA

Sistema inteligente de clasificación de residuos mediante visión por computador. Proyecto de maestría.

Clasifica el **material aparente** de una imagen en seis categorías de TrashNet (cartón, vidrio, metal, papel, plástico, otros residuos). No determina si un residuo es reciclable.

## Estado

| Fase | Estado |
|---|---|
| 1. Requisitos, arquitectura, estructura | Completa |
| 2. Dataset | Completa |
| 3. Entrenamiento en Roboflow | Completa (modelo `ecovision-trashnet/1` seleccionado) |
| 4. Evaluación | Completa (exactitud 0,8865, F1 macro 0,856, AUC macro aprox. 0,980 en prueba) |
| 5. Backend | Completa (100 pruebas en total; verificado con el modelo real y en contenedor Docker) |
| 6. Frontend | Implementado y probado contra el backend y el modelo reales (prueba de humo local) |
| 7. Integración | Completa en local (extremo a extremo con el modelo real) |
| 8. Despliegue | Modelo en Roboflow; app lista para Render y Vercel (publicación pendiente) |
| 9. Evidencias | Informe APA 7 listo (`docs/Informe_EcoVision_IA.pdf`); falta el video |

Todas las cifras provienen de ejecuciones reales (`ml/results/`). Informe final: `docs/Informe_EcoVision_IA.pdf`.

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

## Ejecutar el frontend en desarrollo

```
cd frontend
cp .env.example .env      # VITE_API_BASE_URL apunta al backend
npm install
npm start
```

`npm start` es un alias de desarrollo (Vite en http://localhost:5173). Calidad: `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`.
El backend debe tener `ALLOWED_ORIGINS` con la URL del frontend (CORS).

## Seguridad

La API key de Roboflow vive solo en `backend/.env`. Usa `backend/.env.example` como plantilla.

## Documentación

Ver `docs/` y `.kiro/specs/ecovision-ia/`.
