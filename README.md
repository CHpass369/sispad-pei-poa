# PIP-GAMS Sacaba

**Plataforma Integral de Planificación del Gobierno Autónomo Municipal de Sacaba**

Sistema integrado de planificación municipal que articula tres dominios funcionales sobre
un núcleo transversal único:

| Dominio | Sigla | Alcance |
|---|---|---|
| **Planificación Estratégica** | SIS-PE | PGDES/PDESA, PAD, PEI, diagnóstico, participación, articulación estratégica, indicadores y metas, territorialización, seguimiento y evaluación estratégica |
| **Planificación Operativa Anual** | SIS-POA | POA institucional, POAU, acciones de corto plazo, operaciones/actividades/tareas, techos, recursos, presupuesto, modificaciones, seguimiento operativo |
| **Ciclo del Proyecto** | SIS-PRO | Cartera de proyectos, preinversión (ITCP/EDTP), costos, programación, contratación, ejecución, supervisión, cierre y evaluación |
| **Núcleo transversal** | PIP CORE | Identidad, organización, periodos, catálogos, codificación, normativa, territorio (GIS), indicadores, workflow, documentos, auditoría, notificaciones, reportes, interoperabilidad |

La base del sistema (SISPAD/PEI/POA) fue refactorizada de forma incremental hacia PIP-GAMS
sin reescritura ni pérdida de datos. Ver `PLAN_MAESTRO_REFAC_PIP_GAMS.md` (plan maestro),
`docs/refactor-pip/FINAL_REPORT.md` (informe del refactor, 10 fases) y `docs/pip_gams/`
(arquitectura objetivo).

## Stack

- **Backend**: Python 3.14, Django 6.0, DRF, PostgreSQL 17 + PostGIS 3.4
- **Frontend**: Angular 21 + Angular Material (lazy modules, CapabilityGuard)
- **GIS**: PostGIS, GeoServer
- **Infra**: Gunicorn, Nginx, Celery + Redis, MinIO (S3), Keycloak (OIDC)
- **Calidad**: pytest (1250+ tests), Karma/Jasmine

## Estructura

```
backend/
├── config/            # Configuración Django (settings, urls V1/V2)
├── apps/
│   ├── core/          # Núcleo transversal: modelos base, utilidades, servicios
│   ├── accounts/      # Usuarios, roles, JWT
│   ├── organizacion/  # Organigrama, DA, UE
│   ├── catalogos/     # Catálogos versionados
│   ├── codificacion/  # Codificación oficial PAD/PEI (códigos segmentados)
│   ├── normativa/     # Reglas legales
│   ├── territorio/    # PostGIS, distritos
│   ├── workflow/      # Envíos, revisiones
│   ├── documentos/    # Adjuntos con hash
│   ├── auditoria/     # Trazabilidad
│   ├── notificaciones/#
│   ├── reportes/      # Reportes generados
│   ├── gestion/       # Gestión fiscal, ciclos
│   ├── planificacion/ # SIS-PE: planes, AM/ACP
│   ├── pad/           # SIS-PE: PAD
│   ├── articulacion/  # PIP INTEGRACIÓN: motor de articulación
│   ├── indicadores/   # Indicadores y metas
│   ├── evaluacion/    # SIS-PE: evaluación estratégica
│   ├── acciones_correctivas/ #
│   ├── budget/        # SIS-POA V2: presupuesto canónico
│   ├── poau/          # SIS-POA: POAU por unidad
│   ├── recursos/      # SIS-POA: estimación de ingresos
│   ├── techos/        # SIS-POA (legacy V1): techos presupuestarios
│   ├── presupuesto/   # SIS-POA (legacy V1): programas y líneas
│   ├── modificaciones/# SIS-POA: modificaciones presupuestarias
│   ├── seguimiento/   # SIS-POA: seguimiento operativo
│   └── inversion/     # SIS-PRO: proyectos, preinversión
├── static_assets/     # Build del frontend servido por Django (ng build)
├── tests/
└── manage.py

frontend/sispoa/       # Aplicación Angular 21
├── src/app/features/  # 32 features lazy por dominio
├── src/app/core/      # Núcleo: auth, config, guards, servicios
├── src/app/layout/    # Sidebar (menú por capacidades), topbar
└── angular.json
```

## Inicio rápido (desarrollo local)

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # ajustar DB_NAME=gams_pip, credenciales locales

# Base de datos PostgreSQL + PostGIS local (puerto 5432)
#   crear DB gams_pip con extensión postgis

python manage.py migrate
python manage.py runserver   # http://localhost:8000

# Frontend (terminal 2)
cd frontend/sispoa
npm install
npm start                    # http://localhost:4200 (proxy a /api/)

# Alternativa: build de producción servido por Django
npm run build                # genera dist/sispoa
# copiar dist/sispoa/* a backend/static_assets/ (el patrón del repo versiona el build)
```

## API

- **API V1**: `/api/v1/docs/` — legado, con headers de deprecación (Sunset 2027-01-01)
- **API V2**: `/api/v2/` con namespaces `platform/`, `sis-pe/`, `sis-poa/`, `sis-pro/`, `me/`

## Gobernanza de desarrollo

El repositorio se desarrolla con tareas formales registradas en `tasks/`, reglas de trabajo en `AGENTS.md`, agentes/skills/comandos en `.opencode/` y arquitectura de referencia en `docs/architecture/`.

- [AGENTS.md](AGENTS.md) — reglas universales de desarrollo (search before create, plan before build, scope, commits)
- [docs/architecture/](docs/architecture/) — arquitectura de referencia (mapa del sistema, límites de dominio, propiedad de datos, contratos)
- [tasks/TASK_TEMPLATE.md](tasks/TASK_TEMPLATE.md) — plantilla obligatoria de tareas
- [.opencode/](.opencode/) — agentes, skills y comandos de desarrollo asistido

## Licencia

Uso institucional - GAM Sacaba
