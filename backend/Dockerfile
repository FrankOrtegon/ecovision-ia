# Contexto de construcción: la raíz del repositorio (el backend usa el paquete ml/evaluation).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    ENVIRONMENT=production

WORKDIR /srv
COPY ml/evaluation /srv/ml/evaluation
COPY backend /srv/backend
RUN pip install /srv/ml/evaluation /srv/backend \
    && useradd --create-home --uid 10001 appuser

USER appuser
WORKDIR /srv/backend
EXPOSE 8000
# Render define PORT; en local se usa 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
