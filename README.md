# SISPOA Sacaba

**Sistema Integrado de Formulación, Seguimiento y Administración del POA**

Plataforma institucional para gestionar la formulación del Plan Operativo Anual (POA) y su articulación presupuestaria en el Gobierno Autónomo Municipal de Sacaba.

## Stack

- **Backend**: Python 3.14, Django 6.0, DRF, PostgreSQL 18 + PostGIS 3.6
- **Frontend**: Angular (en desarrollo)
- **GIS**: PostGIS, GeoServer (en configuración)
- **Infra**: Gunicorn, Nginx, Celery + Redis

## Inicio rápido

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env

# Base de datos (local)
initdb -D /tmp/pg_data
pg_ctl -D /tmp/pg_data -o "-p 5433" start
createdb -p 5433 gams_sis_poa
psql -p 5433 -d gams_sis_poa -c "CREATE EXTENSION postgis;"

# Migraciones y semilla
python manage.py migrate
python manage.py shell -c "exec(open('scripts/seed.py').read())"

# Servidor
python manage.py runserver
```

## API

Documentación disponible en `/api/v1/docs/` al ejecutar el servidor.

## Estructura

```
backend/
├── config/           # Configuración Django
├── apps/
│   ├── core/         # Modelos base, utilidades
│   ├── accounts/     # Usuarios, roles, JWT
│   ├── gestion/      # Gestión fiscal, ciclos
│   ├── organizacion/ # Organigrama, DA, UE
│   ├── catalogos/    # Catálogos versionados
│   ├── normativa/    # Reglas legales
│   ├── planificacion/# Planes, AM/ACP
│   ├── indicadores/  # Indicadores y metas
│   ├── recursos/     # Estimación de ingresos
│   ├── techos/       # Techos presupuestarios
│   ├── presupuesto/  # Programas y líneas
│   ├── inversion/    # Proyectos SISIN
│   ├── territorio/   # PostGIS, distritos
│   ├── workflow/     # Envíos, revisiones
│   ├── documentos/   # Adjuntos con hash
│   ├── reportes/     # Reportes generados
│   └── auditoria/    # Trazabilidad
├── tests/
└── manage.py
```

## Licencia

Uso institucional - GAM Sacaba
