# FASE 2 (Techo Directivo): capacidades del ciclo presupuestario.
# Idempotente: get_or_create; preserva mapeos manuales posteriores.
# `sis_poa.budget.manage` ya existe (migración 0002); se agregan las del
# flujo de aprobación/importación/reformulación para fases posteriores.

from django.db import migrations


# (codigo, nombre, sistema, orden)
NUEVAS_CAPACIDADES = [
    ('sis_poa.budget.approve', 'Aprobar presupuesto', 'sis-poa', 26),
    ('sis_poa.budget.import', 'Importar presupuesto', 'sis-poa', 27),
    ('sis_poa.budget.reform', 'Reformular presupuesto', 'sis-poa', 28),
]

# Mapeo a roles estándar (solo adiciones; no revoca existentes).
ROL_CAPACIDADES = {
    'superadmin': [c[0] for c in NUEVAS_CAPACIDADES],
    'admin_presupuesto': [
        'sis_poa.budget.approve',
        'sis_poa.budget.import',
        'sis_poa.budget.reform',
    ],
    'revisor_presupuesto': [
        'sis_poa.budget.approve',
    ],
}


def seed_capacidades_budget(apps, schema_editor):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Rol = apps.get_model('accounts', 'Rol')

    por_codigo = {}
    for codigo, nombre, sistema, orden in NUEVAS_CAPACIDADES:
        cap, _ = Capacidad.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'sistema': sistema, 'orden': orden},
        )
        por_codigo[codigo] = cap

    for rol_codigo, cap_codigos in ROL_CAPACIDADES.items():
        rol = Rol.objects.filter(codigo=rol_codigo).first()
        if not rol:
            continue
        actuales = set(rol.capacidades.values_list('codigo', flat=True))
        nuevas = [por_codigo[c] for c in cap_codigos if c not in actuales]
        if nuevas:
            rol.capacidades.add(*nuevas)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_sis_pro_project_edit'),
    ]

    operations = [
        migrations.RunPython(seed_capacidades_budget, migrations.RunPython.noop),
    ]
