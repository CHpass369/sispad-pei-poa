# FASE 11 (Auditoría de trazabilidad): capacidad de consulta del registro de
# auditoría del ciclo presupuestario. Idempotente: get_or_create; preserva
# mapeos manuales posteriores (patrón de 0004).

from django.db import migrations


# (codigo, nombre, sistema, orden)
NUEVA_CAPACIDAD = ('sis_poa.budget.audit_read', 'Consultar auditoría del presupuesto', 'sis-poa', 29)

# Mapeo a roles estándar (solo adiciones; no revoca existentes).
# tecnico_admin puede no existir en el seed estándar (rol V1): get_or_create
# de roles no, solo se agrega si el rol existe (patrón de 0004).
ROL_CAPACIDADES = {
    'superadmin': [NUEVA_CAPACIDAD[0]],
    'tecnico_admin': [NUEVA_CAPACIDAD[0]],
    'admin_presupuesto': [NUEVA_CAPACIDAD[0]],
    'auditor': [NUEVA_CAPACIDAD[0]],
}


def seed_capacidad_audit_read(apps, schema_editor):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Rol = apps.get_model('accounts', 'Rol')

    codigo, nombre, sistema, orden = NUEVA_CAPACIDAD
    capacidad, _ = Capacidad.objects.get_or_create(
        codigo=codigo,
        defaults={'nombre': nombre, 'sistema': sistema, 'orden': orden},
    )

    for rol_codigo in ROL_CAPACIDADES:
        rol = Rol.objects.filter(codigo=rol_codigo).first()
        if not rol:
            continue
        if not rol.capacidades.filter(pk=capacidad.pk).exists():
            rol.capacidades.add(capacidad)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_sis_poa_budget_capacidades'),
    ]

    operations = [
        migrations.RunPython(seed_capacidad_audit_read, migrations.RunPython.noop),
    ]
