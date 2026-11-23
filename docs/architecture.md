# Arquitectura

El diseño detallado está en `.kiro/specs/ecovision-ia/design.md`. Resumen:

```
React SPA (Vercel) → FastAPI (Render) → Roboflow serverless (modelo)
                          └─ ecovision_eval (scikit-learn)
```

- El frontend solo llama a `/api/*` del backend.
- El backend guarda la API key de Roboflow y procesa las imágenes en memoria.
- La evaluación estadística vive en un paquete Python compartido por el backend y los scripts de `ml/`.

## Endpoints
`GET /api/health`, `GET /api/model/info`, `POST /api/predict`, `POST /api/predict/batch`, `POST /api/evaluate`. Contratos Pydantic en el diseño.

## Decisiones y riesgos
Ver secciones 2 y 3 del diseño. Pendiente de verificar en Fase 3: que el modelo devuelva las seis probabilidades por imagen.
