# Arquitectura del Sistema — SISPAD-PEI-POA

## Diagrama del Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Navegador)                             │
│  Angular 19 + Angular Material + TypeScript                             │
│  http://localhost (Nginx) / http://localhost:4200 (ng serve)            │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTP/HTTPS (JWT Bearer)
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     REVERSO PROXY (Nginx)                                │
│  /api/* → Backend   /static/* → Backend   /media/* → Backend           │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Django 6.0 + DRF 3.17)                     │
│  Gunicorn (WSGI) — Puerto 8000                                         │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ accounts │ │  pad     │ │  poau    │ │  techos  │ │ workflow │    │
│  │ organiz  │ │ planif   │ │ indic    │ │ presupt  │ │ reportes │    │
│  │ catalogos│ │evaluacion│ │seguimie  │ │modificac │ │notificac │    │
│  │ core     │ │ acc_corr │ │ auditoria│ │invencion │ │documentos│    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
└─────┬───────────────────┬──────────────────┬───────────────────────────┘
      │                   │                  │
      ▼                   ▼                  ▼
┌───────────┐    ┌────────────┐    ┌─────────────┐
│ PostgreSQL │    │   Redis    │    │    MinIO    │
│ + PostGIS  │    │ (cache +   │    │  (S3 docs) │
│ Puerto 5432│    │  Celery)   │    │  Puerto 9000│
│            │    │ Puerto 6379│    └─────────────┘
└───────────┘    └────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     SERVICIOS AUXILIARES (Perfil full)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │GeoServer │  │ Keycloak │  │Celery    │  │Celery    │              │
│  │Puerto 8080│  │Puerto 801│  │Worker    │  │Beat      │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Arquitectura Backend

### Stack Tecnologico

- **Framework**: Django 6.0.7 + Django REST Framework 3.17.1
- **Base de datos**: PostgreSQL 16 + PostGIS 3.4
- **Cache/Celery**: Redis 7
- **Auth**: SimpleJWT + mozilla-django-oidc
- **Docs API**: drf-spectacular (OpenAPI 3.0)
- **Archivos**: django-storages + boto3 (MinIO S3)
- **GIS**: djangorestframework-gis
- **Testing**: pytest + pytest-django
- **Task Queue**: Celery 5.6 (worker + beat)

### Aplicaciones Django (25 modulos)

```
apps/
├── core/                   # Modelos abstractos, validadores, alertas, dashboard
├── accounts/               # Usuarios, roles, permisos (RBAC)
├── organizacion/           # Estructura jerarquica: DA → UE → Unidad
├── gestion/                # Gestion fiscal (ciclo vida 8 estados)
├── catalogos/              # 13 clasificadores presupuestarios versionados
├── normativa/              # Normativa legal
├── planificacion/          # Planes (PEI, PTDI, PDES), nodos, AMP, ACP, PlanVersion
├── indicadores/            # Indicadores, metas programadas, operaciones, tareas
├── recursos/               # Estimacion de recursos anual/plurianual
├── techos/                 # Techos presupuestarios, distribuciones, movimientos
├── presupuesto/            # Lineas presupuestarias, programas, proyectos, actividades
├── inversion/              # Proyectos de inversion, SISIN
├── territorio/             # Distritos, OTBs, localizaciones PostGIS
├── pad/                    # Plan Anual de Desarrollo: sectores, politicas, lineamientos
├── poau/                   # Plan Operativo Anual por Unidad, actividades, ejecucion
├── workflow/               # Envio, revision, observaciones, aprobacion, consolidacion
├── documentos/             # Documentos adjuntos, hashes SHA-256
├── reportes/               # 20+ funciones de reporte (XLSX, CSV, PDF, GeoJSON)
├── auditoria/              # Audit trail completo
├── evaluacion/             # Evaluaciones con criterios ponderados
├── modificaciones/         # Solicitudes de modificacion con trazabilidad
├── notificaciones/         # Notificaciones internas y por correo
├── seguimiento/            # Reportes de seguimiento, entradas, alertas
└── acciones_correctivas/   # Acciones correctivas y compromisos
```

### Patron de Arquitectura por App

Cada app sigue el patron:

```
apps/<app>/
├── __init__.py
├── admin.py           # Registro en Django Admin
├── apps.py            # Configuracion de la app
├── models.py          # Modelos de dominio
├── serializers.py     # Serializadores DRF
├── views.py           # ViewSets / APIViews
├── urls.py            # Rutas URL
├── services.py        # Logica de negocio (opcional)
├── tests.py           # Pruebas unitarias
└── migrations/        # Migraciones de BD
```

### Modelos Abstractos Base (core/models.py)

- **TimeStampedModel**: `created_at`, `updated_at`, `created_by`, `updated_by`
- **UUIDModel**: `id = UUIDField(primary_key=True)`
- **ActivableModel**: `activo = BooleanField`
- **VigenciaModel**: `fecha_vigencia_desde`, `fecha_vigencia_hasta`
- **VersionableModel**: `version`, `gestion`

### API REST

- Prefijo base: `/api/v1/`
- Autenticacion: JWT Bearer (`Authorization: Bearer <token>`)
- Paginacion: `PageNumberPagination` (25 elementos por pagina)
- Filtros: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- Schema: `/api/v1/schema/` (OpenAPI 3.0)
- Docs interactivas: `/api/v1/docs/` (Swagger UI)

## Arquitectura Frontend

### Stack Tecnologico

- **Framework**: Angular 19
- **UI**: Angular Material 19
- **Estado**: BehaviorSubject (RxJS)
- **HTTP**: HttpClient + Interceptor JWT
- **Routing**: Lazy loading por modulos
- **Testing**: Jasmine + Karma

### Modulos Funcionales (23 features)

```
features/
├── auth/                 # Login, registro
├── dashboard/            # Panel principal (basado en rol)
├── admin-usuarios/       # Gestion de usuarios y roles
├── organizacion/         # Estructura DA → UE → Unidad
├── catalogos/            # Clasificadores presupuestarios
├── gestion/              # Gestion fiscal
├── planificacion/        # PEI, PTDI, PDES, nodos
├── indicadores/          # Indicadores y metas
├── presupuesto/          # Lineas presupuestarias
├── techos/               # Techos y distribuciones
├── inversion/            # Proyectos de inversion
├── territorio/           # Mapas y distritos
├── pad/                  # Plan Anual de Desarrollo
├── poau/                 # Plan Operativo Anual
├── workflow/             # Flujo de aprobacion
├── reportes/             # Generacion de reportes
├── auditoria/            # Log de auditoria
├── evaluacion/           # Evaluaciones
├── modificaciones/       # Solicitudes de modificacion
├── consolidacion/        # Consolidacion institucional
├── seguimiento/          # Dashboard de seguimiento
├── notificaciones/       # Centro de notificaciones
└── portal-publico/       # Portal publico (sin auth)
```

### Servicios Core

- **AuthService**: Login/logout, JWT tokens, usuario actual
- **ApiService**: Wrapper de HttpClient con manejo de errores
- **PermissionsService**: RBAC en frontend (roles, permisos por modulo)

### Guards y Interceptors

- **AuthGuard**: Protege rutas que requieren autenticacion
- **JWT Interceptor**: Anexa token Bearer a cada peticion HTTP
- **Error Interceptor**: Maneja 401 (refresh/logout), 403, 500

### Layout

- **Sidebar**: Navegacion lateral con menus colapsables
- **Header**: Barra superior con usuario, notificaciones, logout
- **Breadcrumbs**: Navegacion jerarquica

## Esquema de Base de Datos

### Modelo de Relaciones Clave

```
Secretaría → Dirección Administrativa → Unidad Ejecutora → Unidad Organizacional

Plan (PEI/PTDI/PDES)
  └── NodoPlanificacion (Pilar → Eje → Meta → Resultado → AMP → ACP)
       ├── AccionMedianoPlazo (AMP)
       │    └── AccionCortoPlazo (ACP)
       │         ├── Operacion
       │         │    └── Tarea
       │         ├── Indicador → MetaProgramada
       │         ├── Producto
       │         └── Supuesto

PAD
  ├── PoliticaPAD
  │    └── LineamientoEstrategico
  │         └── ResultadoTerritorial
  │              ├── ProductoTerritorial
  │              └── ProgramacionAnualPAD
  └── ArticulacionSIPEB (vinculo con PGDESA/PDES/ODS/NDC)

POAU (Plan Operativo Anual por Unidad)
  ├── UnidadOrganizacional
  ├── ProductoTerritorial (articulacion con PAD)
  └── POAUActividad
       ├── EjecucionFisica (programado vs ejecutado)
       ├── EjecucionFinanciera (programado vs ejecutado)
       └── EntradaSeguimiento

TechoPresupuestario
  └── DistribucionTecho (DA/UE/Programa/Fuente)
       └── MovimientoTecho

LineaPresupuestaria (llave completa)
  ├── Entidad + DA + UE + Programa + Proyecto + Actividad
  ├── Finalidad/Funcion + Fuente + Organismo + Objeto
  ├── Entidad de Transferencia
  └── Importe + Importe Plurianual + Importe Gestion Anterior

Workflow
  ├── EnvioFormulacion → Revision → Observacion
  ├── Aprobacion (con huella SHA-256)
  └── Consolidacion

Evaluacion
  ├── CriterioEvaluacion (ponderado: eficacia, eficiencia, etc.)
  ├── ResultadoEvaluacion
  ├── LeccionAprendida
  └── Recomendacion

Seguimiento
  ├── ReporteSeguimiento → EntradaSeguimiento
  ├── Alerta (generada automaticamente)
  └── UmbralConfiguracion
```

### Modelo de Datos Clave (50+ entidades)

| Modelo                    | App              | Descripcion                              |
| ------------------------- | ---------------- | ---------------------------------------- |
| `Usuario`                 | accounts         | Usuarios con email como USERNAME_FIELD   |
| `Rol`                     | accounts         | 12 roles del sistema                     |
| `UnidadOrganizacional`    | organizacion     | Estructura jerarquica de la entidad      |
| `DireccionAdministrativa` | organizacion     | Direcciones (SMFA, CM, etc.)             |
| `UnidadEjecutora`         | organizacion     | Unidades ejecutoras                      |
| `Plan`                    | planificacion    | PEI, PTDI, PDES, etc.                   |
| `NodoPlanificacion`       | planificacion    | Arbol jerarquico del plan                |
| `AccionMedianoPlazo`      | planificacion    | AMP del PEI                              |
| `AccionCortoPlazo`        | planificacion    | ACP del POA                             |
| `PlanVersion`             | planificacion    | Versionado de planes                     |
| `Indicador`               | indicadores      | Indicadores con formula y meta           |
| `MetaProgramada`          | indicadores      | Programacion trimestral de metas         |
| `TechoPresupuestario`     | techos           | Techo municipal por fuente               |
| `DistribucionTecho`       | techos           | Distribucion a DA/UE/Programa            |
| `MovimientoTecho`         | techos           | Transferencias y ajustes de techo        |
| `LineaPresupuestaria`     | presupuesto      | Llave presupuestaria completa            |
| `ProgramaPresupuestario`  | presupuesto      | Estructura programatica                  |
| `POAU`                    | poau             | Plan Operativo Anual por Unidad          |
| `POAUActividad`           | poau             | Actividades con programacion trimestral  |
| `EjecucionFisica`         | poau             | Seguimiento fisico                       |
| `EjecucionFinanciera`     | poau             | Seguimiento financiero                   |
| `SectorPAD`               | pad              | Sectores del PAD                         |
| `PoliticaPAD`             | pad              | Politicas del PAD                        |
| `ResultadoTerritorial`    | pad              | Resultados territoriales                 |
| `ProductoTerritorial`     | pad              | Productos del PAD                        |
| `EnvioFormulacion`        | workflow         | Envio de formulacion                     |
| `Revision`                | workflow         | Proceso de revision                      |
| `Observacion`             | workflow         | Observaciones con tipo y severidad       |
| `Aprobacion`              | workflow         | Aprobaciones con huella SHA-256          |
| `Evaluacion`              | evaluacion       | Evaluaciones (anual, medio termino, etc.)|
| `CriterioEvaluacion`      | evaluacion       | Criterios ponderados                     |
| `SolicitudModificacion`   | modificaciones   | Solicitudes de modificacion              |
| `Notificacion`            | notificaciones   | Notificaciones internas                  |
| `ReporteSeguimiento`      | seguimiento      | Reportes de seguimiento periodico        |
| `EntradaSeguimiento`      | seguimiento      | Detalle por actividad                    |
| `Alerta`                  | seguimiento      | Alertas generadas automaticamente        |
| `AccionCorrectiva`        | acciones_correctivas | Acciones correctivas con compromisos |

## Diseno de API REST

### Convenciones

- **Prefijo**: `/api/v1/`
- **CRUD basico**: `GET/POST/PUT/PATCH/DELETE /api/v1/<recurso>/`
- **Detalle**: `GET /api/v1/<recurso>/<id>/`
- **Acciones custom**: `POST /api/v1/<recurso>/<id>/<accion>/`
- **Paginacion**: `?page=2&page_size=10`
- **Busqueda**: `?search=nombre`
- **Ordenamiento**: `?ordering=-created_at,codigo`
- **Filtros**: `?gestion=2026&estado=aprobado`

### Formato de Respuesta (Paginado)

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/poau/?page=3",
  "previous": "http://localhost:8000/api/v1/poau/?page=1",
  "results": [...]
}
```

### Formato de Error

```json
{
  "detail": "Mensaje de error",
  "code": "error_code"
}
```

### Formato de Error (Validacion)

```json
{
  "field_name": ["Este campo es requerido."]
}
```

## Flujo de Autenticacion

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │     │ Backend  │     │ Keycloak │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                 │
     │ POST /auth/login/                │
     │ {email, password}               │
     │───────────────>│                 │
     │                │                 │
     │  JWT Access Token (4h)           │
     │  JWT Refresh Token (1d)          │
     │<───────────────│                 │
     │                │                 │
     │ GET /api/v1/anything             │
     │ Authorization: Bearer <token>    │
     │───────────────>│                 │
     │                │                 │
     │  200 OK + data │                 │
     │<───────────────│                 │
     │                │                 │
     │ POST /auth/token/refresh/        │
     │ {refresh: <token>}              │
     │───────────────>│                 │
     │                │                 │
     │  Nuevo access token              │
     │<───────────────│                 │
     │                │                 │
     │ (OIDC flow)    │                 │
     │─────────────────────────────────>│
     │  ID Token + Access Token         │
     │<─────────────────────────────────│
```

### JWT Configuration

- Access Token: 4 horas
- Refresh Token: 1 dia
- Rotacion de refresh tokens habilitada
- Header: `Authorization: Bearer <access_token>`

## Flujo de Estados del PAD

```
borrador ──> enviado ──> aprobado
    │            │
    │            └──> rechazado (con observaciones)
    │                    │
    │                    └──> borrador (resubir)
    │
    └──> (edicion libre)

ResultadoTerritorial:
borrador → enviado → aprobado / rechazado
```

## Cadena Presupuestaria

```
┌─────────────────────────────────────────────────────────────────┐
│                    CADENA PRESUPUESTARIA                         │
│                                                                  │
│  TechoPresupuestario (monto_total por fuente/organismo)         │
│       │                                                          │
│       └── DistribucionTecho (monto_asignado a DA/UE/Programa)  │
│               │                                                  │
│               └── LineaPresupuestaria (llave completa)          │
│                       │                                          │
│                       ├── DA + UE + Programa                    │
│                       ├── Proyecto + Actividad                  │
│                       ├── Fuente + Organismo                    │
│                       ├── Objeto Gasto                          │
│                       └── Importe (Bs)                          │
│                                │                                 │
│                                └── POAUActividad                │
│                                        │                        │
│                                        ├── presupuesto_anual    │
│                                        ├── EjecucionFisica      │
│                                        └── EjecucionFinanciera  │
└─────────────────────────────────────────────────────────────────┘

Validaciones:
1. Suma de distribuciones <= Techo total
2. Suma de lineas presupuestarias <= Distribucion
3. Presupuesto actividad <= Linea presupuestaria
4. Reglas legales: funcionamiento <= 60%, SUS >= 10%, Renta Dignidad >= 0.75%
```

## Formulas de Indicadores

### Tipos de Comportamiento

| Tipo          | Formula                                              |
| ------------- | ---------------------------------------------------- |
| Acumulable    | `Avance = (Suma valores registrados / Meta) * 100`  |
| No acumulable | `Avance = (Valor ultimo registro / Meta) * 100`     |
| Promedio      | `Avance = (Promedio registros / Meta) * 100`        |
| Hito          | `Avance = (Hits completados / Total hits) * 100`    |
| Porcentaje    | `Avance = Valor directo (0-100)`                    |
| Cualitativo   | `Avance = Descripcion cualitativa`                  |

### Avance Fisico vs Financiero

```
Avance Fisico (%)   = (Ejecutado Fisico / Programado Fisico) * 100
Avance Financiero (%) = (Ejecutado Financiero / Programado Financiero) * 100
Desviacion (%)      = Avance Fisico - Avance Financiero
```

### Semaforo de Alertas

```
Verde:   >= 80% avance
Amarillo: >= 50% avance y < 80%
Rojo:    < 50% avance
```

## Motor de Alertas

### Alertas Automaticas (core/alerts.py)

El motor genera alertas automaticamente al evaluar entradas de seguimiento:

| Alerta                          | Condicion                                            | Severidad |
| ------------------------------- | ---------------------------------------------------- | --------- |
| `ejecucion_fisica_baja`        | Avance fisico < 50%                                  | Rojo      |
| `ejecucion_financiera_baja`    | Avance financiero < 50%                              | Rojo      |
| `avance_sin_financiera`        | Avance fisico > 0 y financiero = 0                   | Amarillo  |
| `financiera_sin_avance`        | Avance financiero > 0 y fisico = 0                   | Amarillo  |
| `sobreejecucion_fisica`        | Avance fisico > 100%                                 | Rojo      |
| `sobreejecucion_financiera`    | Avance financiero > 100%                             | Rojo      |
| `meta_vencida`                 | Fecha fin < hoy y avance < 100%                      | Rojo      |
| `sin_evidencia`                | Sin evidencia documental registrada                  | Amarillo  |
| `presupuesto_sin_actividad`    | Distribucion con techo pero sin actividades           | Amarillo  |
| `actividad_sin_presupuesto`    | Actividad sin distribucion de techo                   | Amarillo  |

### Configuracion de Umbrales

Los umbrales son configurables via `UmbralConfiguracion`:
- `porcentaje_minimo`: Limite inferior para generar alerta
- `porcentaje_maximo`: Limite superior
- `activo`: Habilitar/deshabilitar verificacion

## Validaciones Criticas (Seccion 37)

```python
# validators.py
validar_ponderaciones_suma_100(items)      # Ponderaciones = 100%
validar_fechas_consistentes(inicio, fin)   # Inicio < Fin
validar_codigo_unico(modelo, cod, gestion) # Unicidad por gestion
validar_meta_no_negativa(valor)            # Meta >= 0
validar_lineas_igual_total(lineas, total)  # Suma lineas = Total
validar_sin_circulares(origen, destino)    # Sin referencias circulares
validar_accion_poa_sin_pei(accion)         # ACP articulada a AMP
validar_accion_pei_sin_pad(accion)         # AMP articulada a PAD
validar_meta_sin_indicador(meta)           # Meta con indicadores
validar_indicador_sin_unidad(ind)          # Indicador con unidad
validar_actividad_fuera_periodo(act, g)    # Actividad dentro de gestion
validar_presupuesto_mayor_techo(pres, techo) # Presupuesto <= Techo
```
