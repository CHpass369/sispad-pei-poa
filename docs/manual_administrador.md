# Manual del Administrador del Sistema — SISPAD-PEI-POA

Guia completa para administradores tecnicos del sistema.

---

## 1. Vista General del Sistema

### 1.1 Descripcion

SISPAD-PEI-POA es un sistema integrado para la formulacion, seguimiento y administracion del Plan Operativo Anual (POA) del GAM Sacaba. Incluye:

- **24 aplicaciones Django** en el backend
- **23 modulos funcionales** en el frontend Angular
- **Base de datos** PostgreSQL 17 + PostGIS 3.4
- **Almacenamiento** MinIO S3 para documentos
- **Tareas asincronas** Celery (worker + beat)
- **Cache** Redis 7
- **Autenticacion** JWT + OIDC (Keycloak)
- **Servicios de mapas** GeoServer

### 1.2 Credenciales de Acceso

| Servicio | URL | Credenciales |
|----------|-----|-------------|
| Aplicacion | https://tu-dominio.gob.bo | email + password |
| Django Admin | https://tu-dominio.gob.bo/admin/ | superadmin |
| MinIO Console | http://localhost:9001 (solo servidor) | MINIO_ROOT_USER/PASSWORD |
| GeoServer | http://localhost:8080/geoserver (solo servidor) | GEOSERVER_ADMIN_USER/PASSWORD |
| Keycloak Admin | http://localhost:8010 (solo servidor) | KEYCLOAK_ADMIN/PASSWORD |

---

## 2. Configuracion Inicial

### 2.1 Primer inicio

Despues del despliegue, realizar los siguientes pasos:

1. Ingresar al sistema con el superusuario creado
2. Cambiar la contrasena del superusuario
3. Verificar que los catalogos esten cargados (Catalogos > Verificar)
4. Crear la gestion fiscal actual (Gestion Fiscal > Nueva Gestion)
5. Verificar la estructura organizacional (Organizacion > Estructura)
6. Configurar los roles y permisos si es necesario

### 2.2 Configuracion de Gestion Fiscal

```python
# Desde Django shell
docker compose exec backend python manage.py shell

from apps.gestion.models import GestionFiscal
gestion = GestionFiscal.objects.create(
    anio=2026,
    estado='abierta',
    descripcion='Gestion fiscal 2026',
    anio_inicio_plurianual=2024,
    anio_fin_plurianual=2028,
    creado_por=usuario_admin
)
```

### 2.3 Configuracion de Umbrales de Alerta

Los umbrales controlan cuando se generan alertas automaticas:

| Umbral | Minimo | Maximo | Default |
|--------|:------:|:------:|:-------:|
| ejecucion_fisica_baja | 0% | 50% | Activo |
| ejecucion_financiera_baja | 0% | 50% | Activo |
| sobreejecucion | 100% | 200% | Activo |
| sin_evidencia | 0% | 0% | Activo |

Para modificar umbrales:
1. Navegar a Seguimiento > Configuracion de Umbrales
2. Editar el umbral deseado
3. Ajustar porcentaje_minimo y porcentaje_maximo
4. Guardar cambios

---

## 3. Gestion de Usuarios

### 3.1 Crear Usuario

**Via interfaz:**
1. Navegar a Usuarios > Nuevo Usuario
2. Completar: email, nombre, apellido, cargo, telefono
3. Seleccionar rol(es)
4. Guardar
5. El usuario recibe contrasena temporal y debe cambiarla en el primer login

**Via Django Admin:**
1. Navegar a /admin/accounts/usuario/
2. Hacer clic en "Add Usuario"
3. Completar campos
4. En "Roles", seleccionar el rol correspondiente
5. Guardar

**Via API:**
```bash
curl -X POST https://tu-dominio.gob.bo/api/v1/accounts/usuarios/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@gam-sacaba.gob.bo",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "cargo": "Tecnico",
    "roles": ["<rol_uuid>"]
  }'
```

### 3.2 Roles del Sistema

| Rol | Descripcion | Nivel de acceso |
|-----|-------------|:---------------:|
| superadmin | Super Administrador | Total |
| tecnico_admin | Tecnico Administrativo | Alto |
| planificador | Planificador | Alto |
| evaluador | Evaluador | Medio |
| jefe_ue | Jefe de Unidad Ejecutora | Medio |
| director | Director Institucional | Medio |
| tecnico_ue | Tecnico de Unidad Ejecutora | Bajo |
| operador | Operador del POA | Bajo |
| beneficiario | Beneficiario (Portal) | Solo lectura |
| proveedor | Proveedor Externo | Limitado |
| control_interno | Control Interno | Solo lectura |
| control_social | Control Social | Pronunciamiento |

### 3.3 Asignar Usuario a Unidad Organizacional

1. Navegar a Usuarios > [Usuario] > Asignaciones
2. Seleccionar la unidad organizacional
3. Indicar si es responsable POA
4. Seleccionar gestion
5. Guardar

### 3.4 Restablecer Contrasena

1. Navegar a Usuarios > [Usuario] > Editar
2. Hacer clic en "Restablecer contrasena"
3. Ingresar nueva contrasena
4. Marcar "Requiere cambio en proximo login"
5. Guardar

---

## 4. Gestion de la Estructura Organizacional

### 4.1 Arbol Organizacional

```
GAM Sacaba
├── Direccion Administrativa (DA)
│   ├── Unidad Ejecutora (UE) 1
│   │   ├── Unidad Organizacional 1.1
│   │   └── Unidad Organizacional 1.2
│   └── Unidad Ejecutora (UE) 2
│       └── Unidad Organizacional 2.1
├── Direccion Administrativa (DA) 2
│   └── ...
└── ...
```

### 4.2 Crear Tipo de Unidad

1. Navegar a Organizacion > Tipos de Unidad
2. Hacer clic en "Nuevo Tipo"
3. Completar: codigo, nombre, nivel jerarquico
4. Guardar

### 4.3 Crear Direccion Administrativa

1. Navegar a Organizacion > Direcciones Administrativas
2. Hacer clic en "Nueva DA"
3. Completar: codigo, nombre, gestion, responsable
4. Guardar

### 4.4 Crear Unidad Ejecutora

1. Navegar a Organizacion > Unidades Ejecutoras
2. Hacer clic en "Nueva UE"
3. Completar: codigo, nombre, DA padre, unidad organizacional, gestion, responsable
4. Guardar

### 4.5 Crear Unidad Organizacional

1. Navegar a Organizacion > Unidades Organizacionales
2. Hacer clic en "Nueva Unidad"
3. Completar: codigo, nombre, sigla, tipo, padre (si aplica), responsable, gestion
4. Guardar

---

## 5. Gestion de Catalogos

### 5.1 Tipos de Catalogo

| Catalogo | Uso | Ejemplo |
|----------|-----|---------|
| Clasificador Institucional | Clasificacion de la entidad | Codigo institucional |
| Rubro de Recurso | Fuentes de recursos | Recursos propios, transferencias |
| Objeto del Gasto | Clasificacion del gasto | Personal, bienes, servicios |
| Fuente de Financiamiento | Origen de fondos | Propios, bonos, credito |
| Organismo Financiador | Entidad que financia | Gobiernos regionales, internacional |
| Entidad de Transferencia | Entidad otorgante | MAE, Gobernacion |
| Finalidad/Funcion | Funcion del gasto | Educacion, salud, infraestructura |
| Unidad de Medida | Medida de indicadores | Unidades, porcentaje, km |
| Tipo de Operacion | Tipo de operacion POA | Ejecucion, supervision |
| Tipo de Producto | Clasificacion de producto | Terminal, intermedio |
| Tipo de Proyecto | Clasificacion de proyecto | Inversion nueva, ampliacion |

### 5.2 Importar Catalogo

1. Navegar al catalogo correspondiente
2. Hacer clic en "Importar Excel"
3. Descargar plantilla (recomendado)
4. Llenar plantilla con datos
5. Subir archivo
6. Validar (revisar errores si los hay)
7. Confirmar importacion

### 5.3 Versionar Catalogo

1. Navegar a Catalogos > Versiones
2. Hacer clic en "Nueva Version"
3. Seleccionar gestion
4. Subir archivo con datos actualizados
5. Aplicar version
6. Verificar que los datos se actualizaron correctamente

---

## 6. Configuracion del Sistema

### 6.1 Variables de Entorno

Las variables de entorno se configuran en el archivo `.env`. Las mas importantes:

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| DJANGO_SECRET_KEY | Clave secreta de Django | (generar con secrets.token_urlsafe) |
| DJANGO_DEBUG | Modo debug | False en produccion |
| DJANGO_ALLOWED_HOSTS | Dominios permitidos | tu-dominio.gob.bo |
| DB_PASSWORD | Contrasena de PostgreSQL | (generar con secrets.token_urlsafe) |
| CORS_ALLOWED_ORIGINS | Origenes CORS permitidos | https://tu-dominio.gob.bo |
| USE_S3 | Habilitar MinIO | True |

### 6.2 Configuracion de Gunicorn

Archivo: `infra/docker/backend/gunicorn.conf.py`

```python
bind = "0.0.0.0:8000"
workers = 4          # 2 * CPU cores + 1
timeout = 120       # Segundos para requests largos
accesslog = "-"     # stdout
errorlog = "-"      # stdout
loglevel = "info"
```

### 6.3 Configuracion de Nginx

El archivo principal es `infra/nginx/nginx.conf`. Puntos clave:

- **Rate limiting:** 10 requests/segundo por IP
- **Buffer sizes:** client_max_body_size 50M
- **Compresion:** gzip habilitado
- **Cache:** 30 dias para archivos estaticos y media
- **Security headers:** X-Content-Type-Options, X-Frame-Options, etc.

### 6.4 Configuracion de Celery

- **Broker:** Redis (puerto 6379, db 0)
- **Result backend:** Redis (puerto 6379, db 0)
- **Worker:** 4 procesos (configurable via docker-compose)
- **Beat:** Tareas programadas (diarias, semanales)

---

## 7. Monitoreo y Logs

### 7.1 Ver Logs en Tiempo Real

```bash
# Todos los servicios
docker compose -f docker-compose.prod.yml logs -f

# Solo backend
docker compose -f docker-compose.prod.yml logs -f backend

# Solo nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Errores del backend
docker compose -f docker-compose.prod.yml logs backend 2>&1 | grep -i error
```

### 7.2 Verificar Estado de Servicios

```bash
docker compose -f docker-compose.prod.yml ps
```

Salida esperada:
```
NAME                  STATUS                   PORTS
sispoa-postgres       running (healthy)        5432/tcp
sispoa-redis          running (healthy)        6379/tcp
sispoa-backend        running                  0.0.0.0:8000->8000/tcp
sispoa-nginx          running (healthy)        0.0.0.0:80->80/tcp
sispoa-celery-worker  running                  8000/tcp
sispoa-celery-beat    running                  8000/tcp
sispoa-minio          running (healthy)        0.0.0.0:9001->9001/tcp
```

### 7.3 Uso de Recursos

```bash
docker stats --no-stream
```

### 7.4 Logs de Auditoria

Los eventos de auditoria se almacenan en la tabla `auditoria_eventoauditoria`.

**Desde Django shell:**
```python
from apps.auditoria.models import EventoAuditoria

# Ultimos 10 eventos
Eventos = EventoAuditoria.objects.all()[:10]

# Filtrar por usuario
Eventos = EventoAuditoria.objects.filter(usuario__email='usuario@email.com')

# Filtrar por entidad
Eventos = EventoAuditoria.objects.filter(entidad='POAU')
```

**Desde PostgreSQL:**
```sql
-- Ultimos eventos de auditoria
SELECT creado_en, usuario_id, accion, entidad, entidad_id, resumen
FROM auditoria_eventoauditoria
ORDER BY creado_en DESC
LIMIT 50;

-- Eventos de un usuario especifico
SELECT creado_en, accion, entidad, entidad_id, resumen
FROM auditoria_eventoauditoria
WHERE usuario_id = 'uuid-del-usuario'
ORDER BY creado_en DESC;
```

### 7.5 Verificar Base de Datos

```bash
# Conectar a PostgreSQL
docker compose exec postgres-postgis psql -U sispoa_user -d gams_sis_poa

# Comandos utiles dentro de psql
\dt                          -- listar tablas
\di                          -- listar indices
SELECT count(*) FROM accounts_usuario;  -- contar usuarios
SELECT count(*) FROM poau_poau;         -- contar POAUs
\q                            -- salir
```

---

## 8. Solucion de Problemas

### 8.1 Backend no inicia

```bash
# Verificar logs
docker compose -f docker-compose.prod.yml logs backend

# Verificar conexion a base de datos
docker compose exec backend python manage.py dbshell

# Verificar migraciones
docker compose exec backend python manage.py showmigrations
```

### 8.2 Errores de migracion

```bash
# Verificar estado de migraciones
docker compose exec backend python manage.py showmigrations

# Aplicar migraciones pendientes
docker compose exec backend python manage.py migrate

# Si hay conflictos, recrear migraciones
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

### 8.3 Archivos estaticos no se cargan

```bash
# Recolectar estaticos
docker compose exec backend python manage.py collectstatic --noinput

# Verificar que el volumen tiene archivos
docker compose exec backend ls -la /app/staticfiles/
```

### 8.4 Problemas con MinIO

```bash
# Verificar estado de MinIO
docker compose exec minio mc alias set sispoa http://localhost:9000 sispoa_admin password
docker compose exec minio mc admin info sispoa

# Verificar bucket
docker compose exec minio mc ls sispoa/sispoa-docs/
```

### 8.5 Redis sin conexion

```bash
# Verificar estado de Redis
docker compose exec redis redis-cli ping
# Debe responder: PONG

# Ver uso de memoria
docker compose exec redis redis-cli info memory
```

### 8.6 Problemas de rendimiento

```bash
# Ver consultas lentas en PostgreSQL
docker compose exec postgres-postgis psql -U sispoa_user -d gams_sis_poa -c "
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Ver indices faltantes
docker compose exec postgres-postgis psql -U sispoa_user -d gams_sis_poa -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public' AND n_distinct > 100
ORDER BY n_distinct DESC;
"
```

---

## 9. Tareas de Mantenimiento

### 9.1 Mantenimiento Semanal

| Tarea | Comando | Descripcion |
|-------|---------|-------------|
| Verificar backups | `ls -la backups/` | Confirmar que se generaron |
| Revisar logs | `docker compose logs --tail=100` | Buscar errores |
| Verificar espacio | `df -h` | Asegurar >= 20% libre |
| Limpiar cache Redis | `docker compose exec redis redis-cli FLUSHDB` | Si hay problemas de memoria |

### 9.2 Mantenimiento Mensual

| Tarea | Comando | Descripcion |
|-------|---------|-------------|
| Backup de prueba | Restaurar en BD temporal | Verificar integridad de backups |
| Vacuum PostgreSQL | `vacuumdb --full --analyze` | Optimizar base de datos |
| Actualizar Docker | `docker compose pull` | Actualizar imagenes |
| Revisar auditoria | SQL de eventos | Verificar actividad sospechosa |
| Limpiar backups antiguos | `find backups -mtime +30 -delete` | Liberar espacio |

### 9.3 Mantenimiento Trimestral

| Tarea | Descripcion |
|-------|-------------|
| Revision de permisos | Verificar que roles y permisos estan correctos |
| Actualizacion de catálogos | Cargar nuevos catalogos si hay cambios normativos |
| Revision de umbrales | Ajustar umbrales de alertas segun desempeno |
| Prueba de recuperacion | Ejecutar DRP completo en entorno de prueba |

---

## 10. Comandos Utiles de Makefile

| Comando | Descripcion |
|---------|-------------|
| `make setup` | Build + up + migrate + seed |
| `make build` | Construir imagenes Docker |
| `make up` | Iniciar servicios |
| `make down` | Detener servicios |
| `make restart` | Reiniciar servicios |
| `make logs` | Ver logs en tiempo real |
| `make migrate` | Ejecutar migraciones |
| `make shell` | Shell de Python/Django |
| `make dbshell` | Shell de PostgreSQL |
| `make test` | Ejecutar pruebas |
| `make lint` | Verificar codigo con ruff |
| `make format` | Formatear codigo con ruff |
| `make openapi` | Generar esquema OpenAPI |
| `make backup` | Backup completo |
| `make full-reset` | Reconstruir todo desde cero |
