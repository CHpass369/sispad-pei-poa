# Guia de Despliegue en Produccion — SISPAD-PEI-POA

Guia paso a paso para desplegar el sistema en un servidor de produccion usando Docker Compose.

---

## 1. Prerequisitos

### 1.1 Conocimientos Requeridos

- Linux administration (Ubuntu 22.04+ o Debian 12+ recomendado)
- Docker y Docker Compose v2
- Administracion basica de PostgreSQL
- Configuracion de Nginx
- Manejo de certificados SSL/TLS

### 1.2 Software Requerido

| Componente | Version Minima | Version Recomendada |
|------------|:--------------:|:-------------------:|
| Docker | 24.0 | 27.x |
| Docker Compose | 2.20 | 2.29+ |
| Git | 2.30 | 2.40+ |
| Certbot (Let's Encrypt) | 2.0 | 2.7+ |
| Editor de texto | cualquier | nano, vim |

---

## 2. Requisitos del Servidor

### 2.1 Hardware Minimo

| Recurso | Minimo | Recomendado |
|---------|:------:|:-----------:|
| CPU | 2 nucleos | 4+ nucleos |
| RAM | 4 GB | 8+ GB |
| Disco | 40 GB SSD | 100+ GB SSD |
| Ancho de banda | 10 Mbps | 50+ Mbps |

### 2.2 Puertos Requeridos

| Puerto | Servicio | Protocolo |
|--------|----------|:---------:|
| 80 | HTTP (Nginx) | TCP |
| 443 | HTTPS (Nginx) | TCP |
| 22 | SSH (admin) | TCP |

### 2.3 Cuenta de usuario del sistema

```bash
# Crear usuario dedicado (no root)
sudo adduser sispoa --disabled-password
sudo usermod -aG docker sispoa
sudo su - sispoa
```

---

## 3. Instalacion de Docker

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y ca-certificates curl gnupg lsb-release

# Agregar clave GPG oficial de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar repositorio
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalacion
docker --version
docker compose version
```

---

## 4. Clonar el Repositorio

```bash
# Como usuario sispoa
cd /home/sispoa
git clone https://github.com/tu-org/sispad-pei-poa.git
cd sispad-pei-poa
```

---

## 5. Configuracion del Entorno

### 5.1 Crear archivo .env

```bash
cp .env.example .env
```

### 5.2 Generar secrets seguros

```bash
# Generar DJANGO_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Generar DB_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar MINIO_ROOT_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar KEYCLOAK_ADMIN_PASSWORD (si usa OIDC)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar OIDC_RP_CLIENT_SECRET (si usa OIDC)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar GEOSERVER_ADMIN_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 5.3 Editar .env con valores reales

```bash
nano .env
```

Configuracion minima para produccion:

```env
# Django
DJANGO_SECRET_KEY=<generado arriba>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.gob.bo,localhost,127.0.0.1

# Base de datos
DB_ENGINE=django.contrib.gis.db.backends.postgis
DB_NAME=gams_sis_poa
DB_USER=sispoa_user
DB_PASSWORD=<generado arriba>
DB_HOST=sispoa-postgres
DB_PORT=5432

POSTGRES_DB=gams_sis_poa
POSTGRES_USER=sispoa_user
POSTGRES_PASSWORD=<generado arriba>

# CORS
CORS_ALLOWED_ORIGINS=https://tu-dominio.gob.bo

# Redis
REDIS_URL=redis://sispoa-redis:6379/1
CELERY_BROKER_URL=redis://sispoa-redis:6379/0
CELERY_RESULT_BACKEND=redis://sispoa-redis:6379/0

# MinIO
USE_S3=True
MINIO_ENDPOINT=http://sispoa-minio:9000
MINIO_ROOT_USER=sispoa_admin
MINIO_ROOT_PASSWORD=<generado arriba>
MINIO_BUCKET_NAME=sispoa-docs
AWS_ACCESS_KEY_ID=sispoa_admin
AWS_SECRET_ACCESS_KEY=<generado arriba>
AWS_STORAGE_BUCKET_NAME=sispoa-docs
AWS_S3_REGION_NAME=us-east-1

# GeoServer
GEOSERVER_ADMIN_USER=admin
GEOSERVER_ADMIN_PASSWORD=<generado arriba>

# OIDC (opcional)
OIDC_RP_CLIENT_ID=sispoa-frontend
OIDC_RP_CLIENT_SECRET=<generado arriba>
OIDC_OP_AUTHORITY=https://tu-dominio.gob.bo/auth/realms/sispoa
```

---

## 6. Configuracion de DNS

Configurar registros DNS apuntando a la IP del servidor:

```
tu-dominio.gob.bo        A     <IP_DEL_SERVIDOR>
www.tu-dominio.gob.bo    CNAME tu-dominio.gob.bo
```

Verificar propagacion:

```bash
dig tu-dominio.gob.bo +short
```

---

## 7. Construccion e Inicio

### 7.1 Construir las imagenes

```bash
docker compose -f docker-compose.prod.yml build
```

### 7.2 Iniciar servicios core

```bash
docker compose -f docker-compose.prod.yml up -d postgres-postgis redis
```

Esperar a que esten saludables:

```bash
docker compose -f docker-compose.prod.yml ps
# Esperar que postgres-postgis y redis muestren "healthy"
```

### 7.3 Iniciar backend

```bash
docker compose -f docker-compose.prod.yml up -d backend
```

El entrypoint ejecutara automaticamente:
1. Migraciones de base de datos
2. Recoleccion de archivos estaticos
3. Carga de datos iniciales (seed)
4. Inicio de Gunicorn (puerto 8000)

### 7.4 Iniciar servicios auxiliares

```bash
docker compose -f docker-compose.prod.yml up -d celery-worker celery-beat minio
```

### 7.5 Iniciar Nginx (sin SSL aun)

```bash
docker compose -f docker-compose.prod.yml up -d nginx
```

### 7.6 Verificar estado

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

---

## 8. Configuracion SSL/TLS con Let's Encrypt

### 8.1 Instalar Certbot

```bash
sudo apt install -y certbot
```

### 8.2 Obtener certificado (modo standalone)

Primero, detener Nginx temporalmente:

```bash
docker compose -f docker-compose.prod.yml stop nginx
```

Obtener certificado:

```bash
sudo certbot certonly --standalone \
  -d tu-dominio.gob.bo \
  -d www.tu-dominio.gob.bo \
  --email admin@tu-dominio.gob.bo \
  --agree-tos \
  --non-interactive
```

### 8.3 Configurar certificados en Nginx

Copiar certificados a una ubicacion accesible:

```bash
sudo mkdir -p /home/sispoa/sispad-pei-poa/certs
sudo cp /etc/letsencrypt/live/tu-dominio.gob.bo/fullchain.pem /home/sispoa/sispad-pei-poa/certs/
sudo cp /etc/letsencrypt/live/tu-dominio.gob.bo/privkey.pem /home/sispoa/sispad-pei-poa/certs/
sudo chown -R sispoa:sispoa /home/sispoa/sispad-pei-poa/certs/
```

### 8.4 Crear configuracion Nginx con SSL

Crear el archivo `infra/nginx/prod/nginx.conf` con soporte HTTPS:

```nginx
# En el bloque http, agregar:
# Rate limiting
limit_req_zone $binary_remote_addr zone=main_limit:10m rate=10r/s;

# Upstreams
upstream backend_cluster {
    server backend:8000;
}

upstream frontend_cluster {
    server frontend:80;
}

# Redirect HTTP a HTTPS
server {
    listen 80;
    server_name tu-dominio.gob.bo www.tu-dominio.gob.bo;
    return 301 https://$host$request_uri;
}

# Servidor HTTPS principal
server {
    listen 443 ssl http2;
    server_name tu-dominio.gob.bo www.tu-dominio.gob.bo;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # ... (resto de la configuracion similar a nginx.conf)
}
```

### 8.5 Habilitar HTTPS en docker-compose.prod.yml

Descomentar las lineas de SSL en `docker-compose.prod.yml`:

```yaml
nginx:
  volumes:
    - ./certs:/etc/nginx/certs:ro
  ports:
    - "80:80"
    - "443:443"
```

Reiniciar Nginx:

```bash
docker compose -f docker-compose.prod.yml up -d nginx
```

### 8.6 Renovacion automatica de certificados

```bash
# Agregar cron job para renovacion
sudo crontab -e

# Agregar linea (renueva cada 12 horas, verifica si necesita renovacion)
0 */12 * * * certbot renew --quiet --deploy-hook "docker compose -f /home/sispoa/sispad-pei-poa/docker-compose.prod.yml exec -T nginx nginx -s reload"
```

---

## 9. Configuracion de GeoServer (Opcional)

### 9.1 Agregar GeoServer al docker-compose

Crear `docker-compose.geo.yml` o agregar servicios al compose principal:

```yaml
geoserver:
  container_name: sispoa-geoserver
  image: geoserver/geoserver:latest
  restart: always
  environment:
    GEOSERVER_ADMIN_USER: ${GEOSERVER_ADMIN_USER:-admin}
    GEOSERVER_ADMIN_PASSWORD: ${GEOSERVER_ADMIN_PASSWORD}
  volumes:
    - geoserver_data:/var/geoserver/data
  ports:
    - "127.0.0.1:8080:8080"
  networks:
    - backend-net
```

### 9.2 Workspace inicial

```bash
# Crear workspace via REST API
curl -u admin:password -X POST \
  -H "Content-Type: application/json" \
  -d '{"workspace":{"name":"sispoa"}}' \
  http://localhost:8080/geoserver/rest/workspaces
```

---

## 10. Configuracion de Keycloak (Opcional)

### 10.1 Agregar Keycloak al docker-compose

```yaml
keycloak:
  container_name: sispoa-keycloak
  image: quay.io/keycloak/keycloak:latest
  command: start
  restart: always
  environment:
    KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN:-admin}
    KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
  ports:
    - "127.0.0.1:8010:8080"
  volumes:
    - keycloak_data:/opt/keycloak/data
  networks:
    - backend-net
```

### 10.2 Importar realm

```bash
docker cp infra/keycloak/realm-export.json sispoa-keycloak:/tmp/
docker exec sispoa-keycloak /opt/keycloak/bin/kc.sh import --dir /tmp --override false
```

---

## 11. Monitoreo

### 11.1 Health Checks

El sistema incluye health checks para servicios criticos:

| Servicio | Comando | Intervalo | Timeout |
|----------|---------|:---------:|:-------:|
| PostgreSQL | `pg_isready` | 10s | 5s |
| Redis | `redis-cli ping` | 10s | 5s |
| Nginx | `curl -f http://localhost/health` | 30s | 5s |
| MinIO | `mc ready local` | 10s | 5s |

### 11.2 Monitoreo de contenedores

```bash
# Ver estado de todos los servicios
docker compose -f docker-compose.prod.yml ps

# Ver uso de recursos
docker stats --no-stream

# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio especifico
docker compose -f docker-compose.prod.yml logs -f backend
```

### 11.3 Verificacion de servicios

```bash
# Backend API
curl -k https://tu-dominio.gob.bo/api/v1/schema/

# Frontend
curl -k -o /dev/null -s -w "%{http_code}" https://tu-dominio.gob.bo/

# MinIO Console (solo desde servidor)
curl -s http://localhost:9001/minio/health/live

# GeoServer (solo desde servidor)
curl -s http://localhost:8080/geoserver/web/
```

### 11.4 Uso de disco

```bash
# Verificar volumenes
docker system df -v

# Limpiar imagenes no usadas
docker image prune -f
docker container prune -f
```

---

## 12. Carga de Datos Iniciales

### 12.1 Datos semilla (seed)

El seed se ejecuta automaticamente al iniciar el backend. Para ejecutarlo manualmente:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py shell -c "exec(open('scripts/seed.py').read())"
```

### 12.2 Crear superusuario

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py createsuperuser
```

Seguir las indicaciones para ingresar email, nombre y contraseña.

### 12.3 Cargar catalogos via Excel

1. Ingresar al sistema como superadmin
2. Navegar a Catalogos
3. Importar cada catalogo usando los archivos Excel correspondientes
4. Verificar que todos los catalogos esten cargados

### 12.4 Cargar normativa

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py shell -c "
from apps.normativa.models import VersionNormativa
VersionNormativa.objects.get_or_create(
    titulo='DS 0727 - Directriz de Formulacion POA 2026',
    tipo='directriz',
    gestion=2026,
    defaults={'resumen': 'Directriz para formulacion del POA 2026'}
)
"
```

---

## 13. Programacion de Respaldos Automaticos

### 13.1 Instalar cron

```bash
sudo apt install -y cron
sudo systemctl enable cron
sudo systemctl start cron
```

### 13.2 Configurar cron para respaldos

```bash
# Editar crontab del usuario sispoa
crontab -e
```

Agregar las siguientes lineas:

```cron
# Backup diario de base de datos a las 2:00 AM
0 2 * * * /home/sispoa/sispad-pei-poa/infra/backup/backup_database.sh /home/sispoa/backups >> /home/sispoa/backups/cron.log 2>&1

# Backup semanal de MinIO (domingos a las 3:00 AM)
0 3 * * 0 /home/sispoa/sispad-pei-poa/infra/backup/backup_minio.sh /home/sispoa/backups >> /home/sispoa/backups/cron.log 2>&1

# Backup semanal de GeoServer (domingos a las 4:00 AM)
0 4 * * 0 /home/sispoa/sispad-pei-poa/infra/backup/backup_geoserver.sh /home/sispoa/backups >> /home/sispoa/backups/cron.log 2>&1

# Limpieza de backups antiguos (mantener 30 dias, ejecutar el dia 1 de cada mes)
0 5 1 * * find /home/sispoa/backups -name "*.dump" -mtime +30 -delete
0 5 1 * * find /home/sispoa/backups -name "*.log" -mtime +30 -delete
```

### 13.3 Verificar cron

```bash
crontab -l
```

---

## 14. Tareas de Mantenimiento

### 14.1 Actualizaciones

```bash
# Pull de ultimos cambios
cd /home/sispoa/sispad-pei-poa
git pull origin main

# Reconstruir imagenes
docker compose -f docker-compose.prod.yml build

# Re-iniciar servicios (con zero-downtime si es posible)
docker compose -f docker-compose.prod.yml up -d --force-recreate backend celery-worker celery-beat

# Verificar estado
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail=20
```

### 14.2 Limpieza de cache

```bash
# Limpiar cache de Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB
```

### 14.3 Compaction de base de datos

```bash
docker compose -f docker-compose.prod.yml exec postgres-postgis \
  vacuumdb -U sispoa_user -d gams_sis_poa --full --analyze
```

### 14.4 Monitoreo de logs

```bash
# Ver logs de nginx
docker compose -f docker-compose.prod.yml exec nginx cat /var/log/nginx/access.log

# Ver logs de backend
docker compose -f docker-compose.prod.yml logs backend --tail=100

# Buscar errores
docker compose -f docker-compose.prod.yml logs backend 2>&1 | grep -i error
```

---

## 15. Resumen de Comandos Utiles

| Comando | Descripcion |
|---------|-------------|
| `docker compose -f docker-compose.prod.yml ps` | Ver estado de servicios |
| `docker compose -f docker-compose.prod.yml logs -f` | Ver logs en tiempo real |
| `docker compose -f docker-compose.prod.yml restart backend` | Reiniciar backend |
| `docker compose -f docker-compose.prod.yml exec backend python manage.py shell` | Shell de Django |
| `docker compose -f docker-compose.prod.yml exec postgres-postgis psql -U sispoa_user -d gams_sis_poa` | Shell de PostgreSQL |
| `docker compose -f docker-compose.prod.yml stop` | Detener todos los servicios |
| `docker compose -f docker-compose.prod.yml start` | Iniciar todos los servicios |
| `docker system df` | Ver uso de disco |
| `docker stats --no-stream` | Ver uso de recursos |
