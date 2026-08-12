"""Seed S2: agrega `sis_poa.budget.manage` al Rol.admin_poa (design §11, R9.2).

Aditivo e idempotente: hoy admin_poa NO tiene budget.manage (solo
admin_presupuesto lo tiene); el seed lo agrega con get_or_create + add.
Re-ejecutarlo no duplica la capacidad ni el mapeo.

La capacidad `sis_poa.budget.manage` ya existe (creada en 0002); el
get_or_create cubre instalaciones sin el seed previo.
"""

from django.db import migrations

CODIGO_CAPACIDAD = 'sis_poa.budget.manage'
CODIGO_ROL = 'admin_poa'


def seed_budget_manage_admin_poa(apps, schema_editor):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Rol = apps.get_model('accounts', 'Rol')

    cap, _ = Capacidad.objects.get_or_create(
        codigo=CODIGO_CAPACIDAD,
        defaults={
            'nombre': 'Gestionar presupuesto',
            'sistema': 'sis-poa',
            'orden': 0,
        },
    )
    rol = Rol.objects.filter(codigo=CODIGO_ROL).first()
    if rol is None:
        rol = Rol.objects.create(
            codigo=CODIGO_ROL,
            nombre='Administrador POA',
            es_sistema=True,
        )
    if not rol.capacidades.filter(pk=cap.pk).exists():
        rol.capacidades.add(cap)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_sis_pro_project_edit'),
    ]

    operations = [
        migrations.RunPython(seed_budget_manage_admin_poa, migrations.RunPython.noop),
    ]
