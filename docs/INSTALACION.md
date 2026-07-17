# Guia de Instalacion — SISPAD-PEI-POA

## Prerequisitos

| Componente     | Version minima | Verificacion              |
| -------------- | -------------- | ------------------------- |
| Python         | 3.12+          | `python --version`        |
| Node.js        | 20+            | `node --version`          |
| PostgreSQL     | 16+            | `psql --version`          |
| PostGIS        | 3.4+           | `SELECT PostGIS_Version()`|
| Redis          | 7+             | `redis-cli ping`          |
| Keycloak       | 24+            | `http://localhost:8081`   |
| Docker         | 24+            | `docker --version`        |
| Docker Compose | 2.20+          | `docker compose version`  |

## Instalacion con Docker (recomendado)

### 1. Clonar repositorio

```bash
git clone https://github.com/municipio/sispad-pei-poa.git
cd sispad-pei-poa
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con los valores apropiados para su entorno.

### 3. Levantar servicios

```bash
# Perfil dev: backend + frontend + postgres + redis
make setup

# O manualmente:
docker compose --profile dev build
docker compose --profile dev up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py shell -c "exec(open('scripts/seed.py').read())"
```

### 4. Crear superusuario

```bash
docker compose exec backend python manage.py createsuperuser
```

### 5. Acceder al sistema

- Frontend: `http://localhost`
- Backend API: `http://localhost:8000/api/v1/`
- API Docs (Swagger): `http://localhost:8000/api/v1/docs/`
- Django Admin: `http://localhost:8000/admin/`

### Perfiles Docker

| Perfil | Servicios                                    |
| ------ | -------------------------------------------- |
| `dev`  | PostgreSQL, Redis, Backend, Frontend         |
| `full` | Todos los servicios (incluye GeoServer, MinIO, Keycloak, Celery) |

```bash
# Levantar todo (produccion-like)
docker compose --profile full up -d
```

## Instalacion Local (desarrollo)

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp ../.env.example ../.env
# Editar ../.env con valores locales

# Crear base de datos (requiere PostgreSQL + PostGIS)
# CREATE DATABASE gams_sis_poa WITH POSTGIS;

# Ejecutar migraciones
python manage.py migrate

# Semilla de datos
python manage.py shell -c "exec(open('scripts/seed.py').read())"

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver
```

### Frontend

```bash
cd frontend/sispoa

# Instalar dependencias
npm install

# Configurar proxy (ver seccion Proxy)
# Crear archivo proxy.conf.json

# Ejecutar servidor de desarrollo
ng serve
```

### Proxy (Frontend -> Backend)

Crear `frontend/sispoa/proxy.conf.json`:

```json
{
  "/api": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true
  },
  "/static": {
    "target": "http://localhost:8000",
    "secure": false
  },
  "/media": {
    "target": "http://localhost:8000",
    "secure": false
  }
}
```

Actualizar `angular.json` para usar el proxy:

```json
"serve": {
  "options": {
    "proxyConfig": "proxy.conf.json"
  }
}
```

## Variables de Entorno

| Variable                          | Descripcion                                        | Valor por defecto                                  |
| --------------------------------- | -------------------------------------------------- | -------------------------------------------------- |
| `DJANGO_SECRET_KEY`               | Clave secreta de Django                            | `changeme-generar-clave-segura`                    |
| `DJANGO_DEBUG`                    | Modo debug                                         | `False`                                            |
| `DJANGO_ALLOWED_HOSTS`            | Hosts permitidos                                   | `localhost,127.0.0.1`                              |
| `DJANGO_SETTINGS_MODULE`          | Modulo de settings                                 | `config.settings`                                  |
| `DB_ENGINE`                       | Backend de base de datos                           | `django.contrib.gis.db.backends.postgis`           |
| `DB_NAME`                         | Nombre de la base de datos                         | `gams_sis_poa`                                     |
| `DB_USER`                         | Usuario de la base de datos                        | `sispoa_user`                                      |
| `DB_PASSWORD`                     | Contrasena de la base de datos                     | `changeme-segura`                                  |
| `DB_HOST`                         | Host de la base de datos                           | `sispoa-postgres`                                  |
| `DB_PORT`                         | Puerto de la base de datos                         | `5432`                                             |
| `POSTGRES_DB`                     | DB para el contenedor postgres                     | `gams_sis_poa`                                     |
| `POSTGRES_USER`                   | User para el contenedor postgres                   | `sispoa_user`                                      |
| `POSTGRES_PASSWORD`               | Password para el contenedor postgres               | `changeme-segura`                                  |
| `REDIS_HOST`                      | Host de Redis                                      | `sispoa-redis`                                     |
| `REDIS_PORT`                      | Puerto de Redis                                    | `6379`                                             |
| `REDIS_URL`                       | URL de Redis (cache)                               | `redis://sispoa-redis:6379/1`                      |
| `CORS_ALLOWED_ORIGINS`            | Origenes CORS permitidos                           | `http://localhost:4200,http://127.0.0.1:4200`      |
| `CELERY_BROKER_URL`               | Broker de Celery                                   | `redis://sispoa-redis:6379/0`                      |
| `CELERY_RESULT_BACKEND`           | Backend de resultados Celery                       | `redis://sispoa-redis:6379/0`                      |
| `USE_S3`                          | Habilitar MinIO S3                                 | `False`                                            |
| `MINIO_ENDPOINT`                  | Endpoint de MinIO                                  | `http://sispoa-minio:9000`                         |
| `MINIO_ROOT_USER`                 | Usuario MinIO                                      | `sispoa_admin`                                     |
| `MINIO_ROOT_PASSWORD`             | Contrasena MinIO                                   | `changeme-minio-segura`                            |
| `MINIO_BUCKET_NAME`               | Bucket de MinIO                                    | `sispoa-docs`                                      |
| `AWS_ACCESS_KEY_ID`               | Access Key (MinIO)                                 | `sispoa_admin`                                     |
| `AWS_SECRET_ACCESS_KEY`           | Secret Key (MinIO)                                 | `changeme-minio-segura`                            |
| `AWS_STORAGE_BUCKET_NAME`         | Bucket name (MinIO)                                | `sispoa-docs`                                      |
| `AWS_S3_REGION_NAME`              | Region S3                                          | `us-east-1`                                        |
| `GEOSERVER_ADMIN_USER`            | Usuario GeoServer                                  | `admin`                                            |
| `GEOSERVER_ADMIN_PASSWORD`        | Contrasena GeoServer                               | `changeme-geoserver`                               |
| `GEOSERVER_URL`                   | URL de GeoServer                                   | `http://sispoa-geoserver:8080/geoserver`           |
| `OIDC_RP_CLIENT_ID`               | Client ID OIDC                                     | `sispoa-frontend`                                  |
| `OIDC_RP_CLIENT_SECRET`           | Client Secret OIDC                                 | `changeme-oidc-secret`                             |
| `OIDC_OP_AUTHORITY`               | Authority OIDC                                     | `http://sispoa-keycloak:8080/realms/sispoa`        |
| `KEYCLOAK_ADMIN`                  | Admin Keycloak                                     | `admin`                                            |
| `KEYCLOAK_ADMIN_PASSWORD`         | Password Keycloak                                  | `changeme-keycloak`                                |
| `KC_BOOTSTRAP_ADMIN_USERNAME`     | Bootstrap admin username                           | `admin`                                            |
| `KC_BOOTSTRAP_ADMIN_PASSWORD`     | Bootstrap admin password                           | `changeme-keycloak`                                |

## PostGIS Setup

### Docker (automatico)

El servicio `postgres-postgis` usa la imagen `postgis/postgis:17-3.4` que incluye PostGIS pre-instalado.

### Instalacion local

```bash
# Ubuntu/Debian
sudo apt install postgresql-16-postgis-3

# macOS (Homebrew)
brew install postgis

# Crear extension PostGIS
psql -d gams_sis_poa -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

## GeoServer Setup

GeoServer provee servicios OGC (WMS, WFS, WCS) para capas geograficas municipales.

```bash
# Docker (perfil full)
docker compose --profile full up -d geoserver

# Acceder
# URL: http://localhost:8080/geoserver
# Usuario: admin / Password: (configurado en .env)
```

### Configuracion basica

1. Crear workspace: `sispoa`
2. Agregar Store PostGIS apuntando a la base de datos
3. Publicar capas de distritos y OTBs

## MinIO Setup

MinIO provee almacenamiento S3-compatible para documentos adjuntos.

```bash
# Docker (perfil full)
docker compose --profile full up -d minio

# Acceder a la consola
# URL: http://localhost:9001
# Usuario: (MINIO_ROOT_USER) / Password: (MINIO_ROOT_PASSWORD)
```

### Configuracion basica

1. Crear bucket `sispoa-docs`
2. Configurar policy `readwrite` para el bucket
3. Activar `USE_S3=True` en `.env`

## Keycloak Setup

Keycloak provee autenticacion OIDC/SSO para el sistema.

```bash
# Docker (perfil full)
docker compose --profile full up -d keycloak

# Acceder a la consola
# URL: http://localhost:8081
# Usuario: admin / Password: (KC_BOOTSTRAP_ADMIN_PASSWORD)
```

### Importar realm

El realm `sispoa` se importa automaticamente al iniciar Keycloak con `--import-realm`.

Archivo de importacion: `infra/keycloak/realm-export.json`

### Configuracion OIDC en Django

1. Crear variable `OIDC_RP_CLIENT_ID=sispoa-frontend` en `.env`
2. El backend detecta OIDC cuando `OIDC_RP_CLIENT_ID` esta presente
3. SimpleJWT sigue siendo el metodo de autenticacion API principal

## Ejecutar Pruebas

```bash
# Backend
docker compose exec backend python -m pytest apps/ -v

# Frontend
docker compose exec frontend npm test -- --watch=false

# Make targets
make test-backend
make test-frontend
```

## Comandos Utiles (Makefile)

| Comando              | Descripcion                              |
| -------------------- | ---------------------------------------- |
| `make setup`         | Build + up + migrate + seed              |
| `make build`         | Construir imagenes Docker                |
| `make up`            | Levantar servicios dev                   |
| `make down`          | Detener servicios                        |
| `make restart`       | Detener y levantar                       |
| `make logs`          | Ver logs en tiempo real                  |
| `make migrate`       | Ejecutar migraciones                     |
| `make seed`          | Ejecutar semilla de datos                |
| `make createsuperuser` | Crear superusuario admin               |
| `make test`          | Ejecutar todas las pruebas               |
| `make test-backend`  | Pruebas del backend                      |
| `make test-frontend` | Pruebas del frontend                     |
| `make lint`          | Verificar estilo de codigo               |
| `make format`        | Formatear codigo                         |
| `make shell`         | Shell de Django                          |
| `make dbshell`       | Shell de PostgreSQL                      |
| `make openapi`       | Generar schema OpenAPI                   |
| `make backup`        | Backup completo del sistema              |
| `make restore-db`    | Restaurar base de datos                  |
| `make full-reset`    | Reset completo (rebuild + migrate + seed)|

## Troubleshooting

### Error: `relation "accounts_usuario" does not exist`

Las migraciones no se ejecutaron. Ejecutar:

```bash
docker compose exec backend python manage.py migrate
```

### Error: `No module named 'psycopg2'`

Instalar psycopg2-binary:

```bash
pip install psycopg2-binary
```

### Error: `GIS extensions not available`

PostGIS no esta instalado o la extension no fue creada:

```bash
psql -d gams_sis_poa -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Error: `CORS origin not allowed`

Agregar el origen del frontend a `CORS_ALLOWED_ORIGINS` en `.env`:

```
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

### Error: `Connection refused` a Redis

Verificar que Redis esta corriendo:

```bash
docker compose ps redis
docker compose logs redis
```

### Frontend no conecta al backend

Verificar que el proxy esta configurado correctamente y que el backend esta corriendo en el puerto 8000.

### Puerto 8080 en uso (GeoServer)

El contenedor Keycloak usa puerto 8081 en el host para evitar conflicto con GeoServer en 8080.

### Migraciones pendientes despues de pull

```bash
docker compose exec backend python manage.py migrate
```

### Limpiar todo y empezar de cero

```bash
make full-reset
```
