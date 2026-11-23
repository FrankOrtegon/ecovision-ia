# Despliegue

## Estado (2026-11-23)
- **Modelo**: desplegado y accesible por API en Roboflow (`ecovision-trashnet/1`). Verificado con llamadas reales.
- **Backend**: imagen Docker (`backend/Dockerfile`) construida y probada localmente en modo producción: estado del servicio, información del modelo, predicción real, evaluación con scikit-learn, rechazo de orígenes CORS no permitidos y unos 148 MiB de memoria.
- **Frontend**: build de producción verificado (`npm run build`).
- **Publicación en Render y Vercel**: configuración lista (`render.yaml`, `frontend/vercel.json`); **pendiente de ejecutar con tus cuentas**.

## Qué verificar en las plataformas
Render (documentación consultada el 2026-11-23): los servicios gratuitos se suspenden tras 15 minutos sin tráfico y tardan cerca de un minuto en reactivarse; el blueprint admite `runtime: docker`, `dockerfilePath` y `dockerContext`.

## Pasos
1. **Backend en Render**
   1. En Render: New, Blueprint, conectar el repositorio `FrankOrtegon/ecovision-ia` (usa `render.yaml`).
   2. Cuando lo pida, definir los secretos: `ROBOFLOW_API_KEY` (tu clave vigente, solo aquí) y `ALLOWED_ORIGINS` (por ahora un valor temporal como `http://localhost:5173`).
   3. Esperar el despliegue y abrir `https://<servicio>.onrender.com/api/health`: debe mostrar `"model_configured": true`.
2. **Frontend en Vercel**
   1. En Vercel: Add New, Project, importar el repositorio y fijar **Root Directory = `frontend`**.
   2. Variable de entorno `VITE_API_BASE_URL` = la URL del backend en Render (sin barra final).
   3. Desplegar y anotar la URL pública.
3. **CORS**: en Render, cambiar `ALLOWED_ORIGINS` a la URL de Vercel (sin barra final) y redeplegar.
4. **Prueba de humo**: abrir la URL de Vercel, clasificar una imagen y evaluar unas imágenes con CSV.
5. **Registrar las URLs**: editar `docs/informe/despliegue.json` (`frontend_url`, `backend_url`, `verified_on` en formato AAAA-MM-DD) y ejecutar `.venv/bin/python docs/informe/build_informe.py` para regenerar el informe.

## Variables de entorno
Ver `backend/.env.example` y `frontend/.env.example`. La API key de Roboflow se configura solo en el backend. Nunca se escribe en archivos versionados.
