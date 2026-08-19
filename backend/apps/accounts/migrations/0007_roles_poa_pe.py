# Seed IAM: perfiles funcionales POA/PE (jefatura y tecnicos).
#
# El sidebar de SIS-POA filtra sus herramientas por estos cuatro codigos desde
# ed23f24, pero ninguno existia en el catalogo de Rol: el menu quedaba vacio
# para todo el equipo salvo superusuarios, y CapabilityGuard bloqueaba las
# rutas aunque el item se mostrara.
#
# Idempotente: get_or_create + add() solo de las capacidades faltantes, de modo
# que preserva cualquier ajuste manual posterior.
from django.db import migrations


ROLES = {
    'jefe_poa': (
        'Jefe de POA',
        [
            'sis_pe.instrumento.read',
            'sis_poa.formulate',
            'sis_poa.poau.edit',
            'sis_poa.budget.manage',
            'sis_poa.budget.validate',
            'sis_poa.seguimiento.manage',
            'sis_poa.approve',
            'platform.reportes.read',
        ],
    ),
    'tecnico_poa': (
        'Tecnico de POA',
        [
            'sis_pe.instrumento.read',
            'sis_poa.formulate',
            'sis_poa.poau.edit',
            'sis_poa.seguimiento.manage',
            'platform.reportes.read',
        ],
    ),
    'jefe_pe': (
        'Jefe de Planificacion Estrategica',
        [
            'sis_pe.instrumento.read',
            'sis_pe.instrumento.create',
            'sis_pe.pad.edit',
            'sis_pe.pad.validate',
            'sis_pe.pei.edit',
            'sis_pe.articulacion.manage',
            'sis_pe.indicadores.read',
            'sis_pe.approve',
            'sis_poa.formulate',
            'platform.reportes.read',
        ],
    ),
    'tecnico_pe': (
        'Tecnico de Planificacion Estrategica',
        [
            'sis_pe.instrumento.read',
            'sis_pe.instrumento.create',
            'sis_pe.pad.edit',
            'sis_pe.pei.edit',
            'sis_pe.articulacion.manage',
            'sis_pe.indicadores.read',
            'sis_poa.formulate',
            'platform.reportes.read',
        ],
    ),
}


def seed_roles_poa_pe(apps, schema_editor):
    Rol = apps.get_model('accounts', 'Rol')
    Capacidad = apps.get_model('accounts', 'Capacidad')

    for codigo, (nombre, capacidades) in ROLES.items():
        rol, _ = Rol.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'es_sistema': True,
                'descripcion': nombre,
            },
        )
        actuales = set(rol.capacidades.values_list('codigo', flat=True))
        faltantes = list(
            Capacidad.objects.filter(codigo__in=capacidades).exclude(
                codigo__in=actuales
            )
        )
        if faltantes:
            rol.capacidades.add(*faltantes)


def quitar_roles_poa_pe(apps, schema_editor):
    """Solo borra los roles que quedaron sin usuarios asignados."""
    Rol = apps.get_model('accounts', 'Rol')
    for rol in Rol.objects.filter(codigo__in=ROLES):
        if not rol.usuarios.exists():
            rol.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_rol_capacidades_alter_usuario_groups_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_roles_poa_pe, quitar_roles_poa_pe),
    ]
