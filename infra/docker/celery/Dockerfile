FROM python:3.14-slim
WORKDIR /app

# Instalar dependencias del sistema para PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
RUN mkdir -p /app/media /app/staticfiles

# Argumento para elegir worker o beat
ARG CELERY_COMMAND=worker
ENV CELERY_COMMAND=${CELERY_COMMAND}

CMD celery -A config -l info ${CELERY_COMMAND} -B
