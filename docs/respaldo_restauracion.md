# Respaldo y Restauracion — SISPAD-PEI-POA

Procedimientos completos para respaldo, restauracion y recuperacion ante desastres del sistema.

---

## 1. Componentes del Respaldo

El sistema SISPAD-PEI-POA requiere respaldar tres componentes criticos:

| Componente | Contenido | Herramienta | Formato |
|------------|-----------|-------------|---------|
| PostgreSQL + PostGIS | Base de datos completa (esquema + datos) | `pg_dump` | `.dump` (custom format) |
| MinIO (S3) | Archivos subidos (documentos, reportes, normativa) | `mc mirror` | Directorio con archivos |
| GeoServer | Configuracion de workspaces, capas, estilos | REST API + data dir | JSON + archivos |

---

## 2. Respaldo de PostgreSQL

### 2.1 Respaldo Automatico (Script)

**Ubicacion del script:** `infra/backup/backup_database.sh`

```bash
# Ejecucion manual
./infra/backup/backup_database.sh backups

# Salida esperada:
# [2026-07-17 02:00:00] Iniciando backup de gams_sis_poa...
# Backup creado: backups/sispoa_db_20260717_020000.dump
# 15M    backups/sispoa_db_20260717_020000.dump
# Backup validado correctamente
```

**Que hace el script:**
1. Ejecuta `pg_dump` dentro del contenedor PostgreSQL en formato custom (comprimido)
2. Copia el archivo `.dump` del contenedor al host
3. Limpia el archivo temporal en el contenedor
4. Valida la integridad del backup con `pg_restore --list`
5. Genera un archivo de log

**Parametros configurables:**

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `BACKUP_DIR` | `./backups` | Directorio de salida |
| `DB_CONTAINER` | `postgres-postgis` | Nombre del contenedor |
| `DB_NAME` | `gams_sis_poa` | Nombre de la base de datos |
| `DB_USER` | `sispoa_user` | Usuario de PostgreSQL |

### 2.2 Respaldo Manual

```bash
# Backup directo con docker compose
docker compose exec -T postgres-postgis pg_dump \
  -U sispoa_user \
  -d gams_sis_poa \
  -F c \
  -v \
  -f /tmp/sispoa_manual.dump

# Copiar al host
docker compose cp postgres-postgis:/tmp/sispoa_manual.dump ./backups/
docker compose exec -T postgres-postgis rm -f /tmp/sispoa_manual.dump
```

### 2.3 Backup en formato SQL (texto)

```bash
# Solo si se necesita formato legible (sin compresion)
docker compose exec -T postgres-postgis pg_dump \
  -U sispoa_user \
  -d gams_sis_poa \
  -F p \
  -v \
  -f /tmp/sispoa_text.sql
```

### 2.4 Backup solo de esquema (sin datos)

```bash
docker compose exec -T postgres-postgis pg_dump \
  -U sispoa_user \
  -d gams_sis_poa \
  --schema-only \
  -F c \
  -f /tmp/sispoa_schema.dump
```

---

## 3. Respaldo de MinIO

### 3.1 Respaldo Automatico (Script)

**Ubicacion del script:** `infra/backup/backup_minio.sh`

```bash
# Ejecucion manual
./infra/backup/backup_minio.sh backups/minio

# Salida esperada:
# [date] Iniciando backup de MinIO bucket 'sispoa-docs'...
# Backup MinIO completado: backups/minio/20260717_020000
#    Archivos: 156
```

**Que hace el script:**
1. Configura un alias `mc` dentro del contenedor MinIO
2. Ejecuta `mc mirror` del bucket al host via volumen temporal
3. Copia los archivos al directorio de backup
4. Limpia archivos temporales del contenedor

**Parametros configurables:**

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `MINIO_CONTAINER` | `minio` | Nombre del contenedor |
| `MINIO_ALIAS` | `sispoa` | Alias de mc |
| `MINIO_BUCKET_NAME` | `sispoa-docs` | Nombre del bucket |

### 3.2 Respaldo Manual

```bash
# Configurar alias
docker compose exec minio mc alias set sispoa http://localhost:9000 sispoa_admin password

# Mirror del bucket
docker compose exec minio mc mirror sispoa/sispoa-docs /tmp/minio_backup

# Copiar al host
docker compose cp minio:/tmp/minio_backup ./backups/minio/
docker compose exec minio rm -rf /tmp/minio_backup
```

---

## 4. Respaldo de GeoServer

### 4.1 Respaldo Automatico (Script)

**Ubicacion del script:** `infra/backup/backup_geoserver.sh`

```bash
# Ejecucion manual
./infra/backup/backup_geoserver.sh backups/geoserver

# Salida esperada:
# [date] Iniciando backup de GeoServer...
# Exportando configuracion REST...
# Respaldando data directory...
# Backup GeoServer completado: backups/geoserver/20260717_020000
```

**Que hace el script:**
1. Exporta workspaces via REST API
2. Exporta layers via REST API
3. Exporta estilos via REST API
4. Copia el data directory completo del contenedor

### 4.2 Respaldo Manual

```bash
# Exportar configuracion
curl -s -u admin:password http://localhost:8080/geoserver/rest/workspaces.json -o workspaces.json
curl -s -u admin:password http://localhost:8080/geoserver/rest/layers.json -o layers.json
curl -s -u admin:password http://localhost:8080/geoserver/rest/styles.json -o styles.json

# Copiar data directory
docker compose cp geoserver:/var/geoserver/data ./backups/geoserver/data
```

---

## 5. Respaldo Completo del Sistema

### 5.1 Comando unico

```bash
# Ejecutar todos los backups
make backup

# O manualmente:
./infra/backup/backup_database.sh backups
./infra/backup/backup_minio.sh backups/minio
./infra/backup/backup_geoserver.sh backups/geoserver
```

### 5.2 Estructura de directorios de backup

```
backups/
├── sispoa_db_20260717_020000.dump          # PostgreSQL
├── backup_20260717_020000.log              # Log del backup DB
├── minio/
│   └── 20260717_020000/                   # MinIO files
│       ├── documentos/
│       │   ├── 2026/
│       │   │   ├── file1.pdf
│       │   │   └── file2.xlsx
│       │   └── catalogos/
│       └── reportes/
└── geoserver/
    └── 20260717_020000/                   # GeoServer config
        ├── workspaces.json
        ├── layers.json
        ├── styles.json
        └── data/
            ├── sispoa/
            └── ...
```

---

## 6. Restauracion de PostgreSQL

### 6.1 Restauracion Automatica (Script)

**Ubicacion del script:** `infra/backup/restore_database.sh`

```bash
# Ejecucion
./infra/backup/restore_database.sh backups/sispoa_db_20260717_020000.dump

# Salida esperada:
# [date] Iniciando restauracion de backups/sispoa_db_20260717_020000.dump...
# Copiando backup al contenedor...
# Restaurando base de datos gams_sis_poa...
# Restauracion completada
```

**Que hace el script:**
1. Verifica que el archivo de backup exista
2. Copia el archivo al contenedor PostgreSQL
3. Ejecuta `pg_restore` con las opciones:
   - `--clean`: Elimina objetos existentes antes de recrear
   - `--if-exists`: No falla si el objeto no existe
   - `--no-owner`: No intenta restaurar ownership
   - `--no-acl`: No restaura permisos ACL
4. Limpia el archivo temporal

### 6.2 Restauracion Manual

```bash
# Copiar backup al contenedor
docker compose cp backups/sispoa_db.dump postgres-postgis:/tmp/restore.dump

# Restaurar
docker compose exec -T postgres-postgis pg_restore \
  -U sispoa_user \
  -d gams_sis_poa \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  -v \
  /tmp/restore.dump

# Limpiar
docker compose exec -T postgres-postgis rm -f /tmp/restore.dump
```

### 6.3 Restauracion en base de datos limpia

Si la base de datos esta vacia o se necesita una restauracion limpia:

```bash
# Crear base de datos si no existe
docker compose exec postgres-postgis \
  psql -U sispoa_user -d postgres -c "CREATE DATABASE gams_sis_poa;"

# Restaurar
docker compose exec -T postgres-postgis pg_restore \
  -U sispoa_user \
  -d gams_sis_poa \
  --no-owner \
  --no-acl \
  -v \
  /tmp/restore.dump
```

### 6.4 Verificar restauracion

```bash
# Contar tablas
docker compose exec postgres-postgis \
  psql -U sispoa_user -d gams_sis_poa -c "\dt" | wc -l

# Contar registros en tablas principales
docker compose exec postgres-postgis \
  psql -U sispoa_user -d gams_sis_poa -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC
  LIMIT 20;
  "
```

---

## 7. Restauracion de MinIO

### 7.1 Restauracion Automatica (Script)

**Ubicacion del script:** `infra/backup/restore_minio.sh`

```bash
# Ejecucion
./infra/backup/restore_minio.sh backups/minio/20260717_020000

# Salida esperada:
# [date] Restaurando MinIO bucket 'sispoa-docs' desde backups/minio/20260717_020000...
# Restauracion MinIO completada
```

### 7.2 Restauracion Manual

```bash
# Copiar archivos al contenedor
docker compose cp backups/minio/20260717_020000/. minio:/tmp/minio_restore/

# Configurar alias
docker compose exec minio mc alias set sispoa http://localhost:9000 sispoa_admin password

# Restaurar (sobreescribe existentes)
docker compose exec minio mc mirror --overwrite /tmp/minio_restore sispoa/sispoa-docs

# Limpiar
docker compose exec minio rm -rf /tmp/minio_restore
```

---

## 8. Restauracion de GeoServer

### 8.1 Restauracion Automatica (Script)

**Ubicacion del script:** `infra/backup/restore_geoserver.sh`

```bash
# Ejecucion
./infra/backup/restore_geoserver.sh backups/geoserver/20260717_020000

# Salida esperada:
# [date] Restaurando GeoServer desde backups/geoserver/20260717_020000...
# GeoServer reiniciado con la configuracion restaurada
```

### 8.2 Restauracion Manual

```bash
# Copiar data directory
docker compose cp backups/geoserver/20260717_020000/data/. geoserver:/var/geoserver/data/

# Reiniciar GeoServer para recargar configuracion
docker compose restart geoserver
```

---

## 9. Plan de Recuperacion ante Desastres (DRP)

### 9.1 Clasificacion de Escenarios

| Escenario | Tiempo objetivo recuperacion | RPO (perdida datos maxima) | Pasos |
|-----------|:---------------------------:|:--------------------------:|-------|
| Corrupcion de datos | 2 horas | 24 horas (backup diario) | Restaurar DB + MinIO |
| Fallo de disco | 4 horas | 24 horas | Restaurar en nuevo disco |
| Fallo de servidor | 8 horas | 24 horas | Provisionar nuevo servidor + restaurar |
| Borrado accidental | 1 hora | 0 (si hay backups incrementales) | Restaurar tablas afectadas |

### 9.2 Procedimiento de Recuperacion Completa

**Paso 1: Provisionar nuevo servidor**

Seguir la seccion 2-5 de la guia de despliegue (`despliegue.md`).

**Paso 2: Restaurar base de datos**

```bash
# Copiar el backup mas reciente al nuevo servidor
scp backups/sispoa_db_*.dump sispoa@nuevo-servidor:/home/sispoa/backups/

# Ejecutar restauracion
./infra/backup/restore_database.sh backups/sispoa_db_*.dump
```

**Paso 3: Restaurar archivos MinIO**

```bash
# Copiar respaldo de MinIO
scp -r backups/minio/ sispoa@nuevo-servidor:/home/sispoa/backups/minio/

# Restaurar
./infra/backup/restore_minio.sh backups/minio/ultima_fecha
```

**Paso 4: Restaurar GeoServer (si aplica)**

```bash
scp -r backups/geoserver/ sispoa@nuevo-servidor:/home/sispoa/backups/geoserver/
./infra/backup/restore_geoserver.sh backups/geoserver/ultima_fecha
```

**Paso 5: Ejecutar migraciones**

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py migrate --noinput
```

**Paso 6: Recolectar estaticos**

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py collectstatic --noinput
```

**Paso 7: Reiniciar servicios**

```bash
docker compose -f docker-compose.prod.yml restart
```

**Paso 8: Verificar**

```bash
# Verificar API
curl -k https://tu-dominio.gob.bo/api/v1/schema/

# Verificar login
# Abrir navegador y hacer login con credenciales de superadmin
```

### 9.3 Recuperacion de Tabla Individual

Si solo se necesita recuperar una tabla especifica:

```bash
# Extraer tabla del backup
docker compose exec -T postgres-postgis pg_restore -l /tmp/backup.dump | grep tabla_nombre

# Restaurar solo esa tabla
docker compose exec -T postgres-postgis pg_restore \
  -U sispoa_user \
  -d gams_sis_poa \
  --data-only \
  --table=tabla_nombre \
  -v \
  /tmp/backup.dump
```

### 9.4 Punto de Recuperacion

Para crear un punto de recuperacion antes de una operacion riesgosa:

```bash
# Crear backup pre-operacion
./infra/backup/backup_database.sh /home/sispoa/backups/pre_operacion

# Si la operacion falla, restaurar
./infra/backup/restore_database.sh /home/sispoa/backups/pre_operacion/sispoa_db_*.dump
```

---

## 10. Verificacion de Backups

### 10.1 Verificacion Automatica

```bash
# Verificar integridad de un dump
docker compose exec -T postgres-postgis pg_restore --list /tmp/backup.dump > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "Backup valido"
else
  echo "Backup corrupto"
fi
```

### 10.2 Verificacion Periodica (recomendada)

Ejecutar mensualmente una restauracion de prueba en un entorno aislado:

```bash
# 1. Crear base de datos temporal
docker compose exec postgres-postgis \
  psql -U sispoa_user -d postgres -c "CREATE DATABASE sispoa_test;"

# 2. Restaurar en la base temporal
docker compose exec -T postgres-postgis pg_restore \
  -U sispoa_user \
  -d sispoa_test \
  --no-owner \
  -v \
  /tmp/backup.dump

# 3. Verificar conteos
docker compose exec postgres-postgis \
  psql -U sispoa_user -d sispoa_test -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  WHERE schemaname = 'public'
  ORDER BY n_live_tup DESC;
  "

# 4. Limpiar
docker compose exec postgres-postgis \
  psql -U sispoa_user -d postgres -c "DROP DATABASE sispoa_test;"
```

### 10.3 Checklist de Verificacion

| Item | Metodo | Frecuencia |
|------|--------|:----------:|
| Backup DB existe y tiene tamano razonable | `ls -lh backups/*.dump` | Diaria |
| Backup DB es restaurable | `pg_restore --list` | Semanal |
| Backup MinIO tiene archivos | `find backups/minio -type f | wc -l` | Semanal |
| Backup GeoServer tiene config | `ls backups/geoserver/*.json` | Semanal |
| Restore de prueba exitosa | Restaurar en BD temporal | Mensual |
| Backups antiguos se limpian | Verificar cron de limpieza | Mensual |
| Logs de backup sin errores | Revisar `backups/cron.log` | Semanal |

---

## 11. Almacenamiento de Backups Offsite

### 11.1 Copia a almacenamiento externo

Recomendado: copiar backups a un segundo servidor o almacenamiento en la nube.

```bash
# Ejemplo: copiar a servidor remoto via rsync
rsync -avz --progress \
  /home/sispoa/backups/ \
  backup-remoto@servidor-secundario:/backups/sispoa/

# Ejemplo: copiar a S3 compatido (aws cli)
aws s3 sync /home/sispoa/backups/ s3://mi-bucket-backups/sispoa/ \
  --endpoint-url https://s3.amazonaws.com
```

### 11.2 Retencion de backups

| Tipo | Cantidad a mantener | Almacenamiento |
|------|:-------------------:|----------------|
| Diarios | 30 dias | Local |
| Semanales | 12 semanas (3 meses) | Local + Offsite |
| Mensuales | 12 meses (1 ano) | Offsite |
| Anuales | 5 anos | Archivo historico |

---

## 12. Comandos Rapidos de Makefile

| Comando | Descripcion |
|---------|-------------|
| `make backup` | Backup completo (DB + MinIO + GeoServer) |
| `make backup-db` | Solo backup de PostgreSQL |
| `make backup-minio` | Solo backup de MinIO |
| `make backup-geoserver` | Solo backup de GeoServer |
| `make restore-db FILE=backups/archivo.dump` | Restaurar PostgreSQL |
| `make restore-minio DIR=backups/minio/fecha` | Restaurar MinIO |
| `make restore-geoserver DIR=backups/geoserver/fecha` | Restaurar GeoServer |
