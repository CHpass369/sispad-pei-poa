"""
Script de datos semilla idempotente.
Ejecutar: python manage.py shell < scripts/seed.py
"""
import datetime
from apps.accounts.models import Usuario, Rol
from apps.gestion.models import GestionFiscal
from apps.planificacion.models import Plan, NodoPlanificacion, ArticulacionPlanificacion

# Roles del sistema
roles = [
    ('superadmin', 'Superadministrador Técnico', True),
    ('admin_poa', 'Administrador POA', True),
    ('admin_presupuesto', 'Administrador de Presupuesto', True),
    ('responsable_unidad', 'Responsable POA de Unidad', True),
    ('revisor_planificacion', 'Revisor de Planificación', True),
    ('revisor_presupuesto', 'Revisor de Presupuesto', True),
    ('revisor_inversion', 'Revisor de Proyectos', True),
    ('revisor_juridico', 'Revisor Jurídico', True),
    ('mae', 'Máxima Autoridad Ejecutiva', True),
    ('auditor', 'Auditor', True),
    ('consulta', 'Usuario de Consulta', True),
    ('control_social', 'Participación y Control Social', True),
]

for codigo, nombre, sistema in roles:
    Rol.objects.get_or_create(
        codigo=codigo,
        defaults={'nombre': nombre, 'es_sistema': sistema, 'descripcion': nombre}
    )

# Superusuario
# Idempotente: también repara instalaciones existentes (password y flags de
# sistema siempre asegurados, no solo al crear el usuario).
admin, created = Usuario.objects.get_or_create(
    email='admin@gamsacaba.gob.bo',
    defaults={
        'first_name': 'Admin',
        'last_name': 'SISPOA',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created or not admin.check_password('admin2026'):
    admin.set_password('admin2026')
admin.is_staff = True
admin.is_superuser = True
admin.save()

# Rol de sistema del superusuario (el frontend consume roles/capacidades)
rol_super, _ = Rol.objects.get_or_create(
    codigo='superadmin',
    defaults={'nombre': 'Superadministrador Técnico', 'es_sistema': True,
              'descripcion': 'Superadministrador Técnico'}
)
if not admin.roles.filter(pk=rol_super.pk).exists():
    admin.roles.add(rol_super)

# Gestión 2026
GestionFiscal.objects.get_or_create(
    anio=2026,
    defaults={
        'estado': 'preparacion',
        'anio_inicio_plurianual': 2026,
        'anio_fin_plurianual': 2028,
    }
)

# ──────────────────────────────────────────────
# PGDESA y PDESA (Matriz de Articulación Completa)
# ──────────────────────────────────────────────

plan_pgdesa, created = Plan.objects.get_or_create(
    codigo='PGDESA-2026-2050', tipo='pgdesa',
    defaults={
        'nombre': 'Plan General de Desarrollo Sostenible del Estado 2026-2050',
        'gestion_inicio': 2026, 'gestion_fin': 2050,
        'fecha_vigencia_desde': datetime.date(2026, 1, 1),
    }
)

plan_pdesa, created = Plan.objects.get_or_create(
    codigo='PDESA-2026-2030', tipo='pdesa',
    defaults={
        'nombre': 'Plan de Desarrollo Económico y Social 2026-2030',
        'gestion_inicio': 2026, 'gestion_fin': 2030,
        'fecha_vigencia_desde': datetime.date(2026, 1, 1),
    }
)

# 7 ejes PGDESA
ejes_data = [
    'Erradicación de la pobreza',
    'Desarrollo social universal',
    'Desarrollo económico y productivo',
    'Desarrollo integral del hábitat',
    'Desarrollo de las capacidades productivas',
    'Gestión de riesgos y cambio climático',
    'Gestión institucional y participación social',
]

ejes = []
for i, nombre in enumerate(ejes_data, 1):
    codigo = f'{i:02d}'
    eje, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pgdesa, codigo=codigo, nivel='eje',
        defaults={'nombre': nombre, 'gestion': 2026, 'orden': i},
    )
    ejes.append(eje)

# 3 metas + 2 resultados por cada eje PGDESA
resultados_pgdesa = []
for eje in ejes:
    for j in range(1, 4):
        codigo_meta = f'{eje.codigo}.{j:02d}'
        meta, _ = NodoPlanificacion.objects.get_or_create(
            plan=plan_pgdesa, codigo=codigo_meta, nivel='meta',
            defaults={
                'nombre': f'Meta {eje.codigo}.{j:02d} - {eje.nombre}',
                'gestion': 2026, 'padre': eje, 'orden': j,
            },
        )
        for k in range(1, 3):
            codigo_res = f'{codigo_meta}.{k:02d}'
            resultado, _ = NodoPlanificacion.objects.get_or_create(
                plan=plan_pgdesa, codigo=codigo_res, nivel='resultado',
                defaults={
                    'nombre': f'Resultado {codigo_res}',
                    'gestion': 2026, 'padre': meta, 'orden': k,
                },
            )
            resultados_pgdesa.append(resultado)

# ~24 componentes PDESA
componentes_data = [
    'Desarrollo normativo institucional',
    'Fortalecimiento de capacidades institucionales',
    'Planificación y gestión territorial',
    'Infraestructura productiva',
    'Desarrollo agropecuario',
    'Seguridad alimentaria',
    'Promoción del empleo digno',
    'Fomento a la micro y pequeña empresa',
    'Turismo sostenible',
    'Desarrollo industrial',
    'Energías renovables',
    'Conectividad vial',
    'Agua potable y saneamiento',
    'Vivienda social',
    'Gestión de residuos sólidos',
    'Protección de cuencas y recursos hídricos',
    'Conservación de la biodiversidad',
    'Educación y capacitación técnica',
    'Salud preventiva',
    'Cultura y deporte',
    'Participación ciudadana',
    'Transparencia y lucha contra la corrupción',
    'Gestión de riesgos',
    'Desarrollo urbano sostenible',
]

componentes = []
for i, nombre in enumerate(componentes_data, 1):
    codigo = f'{i:02d}'
    componente, _ = NodoPlanificacion.objects.get_or_create(
        plan=plan_pdesa, codigo=codigo, nivel='componente',
        defaults={'nombre': nombre, 'gestion': 2026, 'orden': i},
    )
    componentes.append(componente)

# 2-3 acciones por componente PDESA
for comp in componentes:
    num_acciones = 3 if componentes.index(comp) % 2 == 0 else 2
    for j in range(1, num_acciones + 1):
        codigo_acc = f'{comp.codigo}.{j:02d}'
        NodoPlanificacion.objects.get_or_create(
            plan=plan_pdesa, codigo=codigo_acc, nivel='accion',
            defaults={
                'nombre': f'Acción {comp.codigo}.{j:02d} - {comp.nombre}',
                'gestion': 2026, 'padre': comp, 'orden': j,
            },
        )

# Articulaciones PGDESA resultado → PDESA componente (round-robin)
for i, resultado in enumerate(resultados_pgdesa):
    componente = componentes[i % len(componentes)]
    ArticulacionPlanificacion.objects.get_or_create(
        nodo_origen=resultado,
        nodo_destino=componente,
        gestion=2026,
        defaults={'es_principal': True},
    )

print('Semilla ejecutada correctamente.')
print(f'  - {Rol.objects.count()} roles')
print(f'  - {Usuario.objects.count()} usuarios')
print(f'  - {GestionFiscal.objects.count()} gestiones fiscales')
print(f'  - {Plan.objects.filter(tipo__in=["pgdesa","pdesa"]).count()} planes PGDESA/PDESA')
print(f'  - {NodoPlanificacion.objects.filter(plan=plan_pgdesa).count()} nodos PGDESA')
print(f'  - {NodoPlanificacion.objects.filter(plan=plan_pdesa).count()} nodos PDESA')
print(f'  - {ArticulacionPlanificacion.objects.filter(gestion=2026).count()} articulaciones')
