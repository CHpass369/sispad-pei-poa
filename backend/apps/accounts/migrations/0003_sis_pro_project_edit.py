# WP-11 (SIS-PRO V2): nueva capacidad de edición de proyectos.
# Idempotente: get_or_create + adición a roles con acceso a proyectos.

from django.db import migrations


def seed_capacidad_edicion_proyecto(apps, schema_editor):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Rol = apps.get_model('accounts', 'Rol')

    cap, _ = Capacidad.objects.get_or_create(
        codigo='sis_pro.project.edit',
        defaults={
            'nombre': 'Editar proyectos',
            'sistema': 'sis-pro',
            'orden': 18,
        },
    )
    for rol_codigo in ('superadmin', 'mae', 'revisor_inversion', 'admin_presupuesto'):
        rol = Rol.objects.filter(codigo=rol_codigo).first()
        if rol and not rol.capacidades.filter(pk=cap.pk).exists():
            rol.capacidades.add(cap)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_capacidad_alcanceorganizacional_rol_capacidades'),
    ]

    operations = [
        migrations.RunPython(seed_capacidad_edicion_proyecto, migrations.RunPython.noop),
    ]
