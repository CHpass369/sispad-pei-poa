# =============================================================================
# Stage 1: Build — instalar dependencias
# =============================================================================
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Final — imagen liviana de producción
# =============================================================================
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000

# Instalar GDAL + librerías del sistema para PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar solo site-packages y binarios desde build stage
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código de la aplicación
COPY backend/ /app/

# Copiar entrypoint y config de gunicorn
COPY infra/docker/backend/entrypoint.sh /entrypoint.sh
COPY infra/docker/backend/gunicorn.conf.py /gunicorn.conf.py

RUN chmod +x /entrypoint.sh && mkdir -p /app/staticfiles /app/media

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
