"""Reproducible authorization baseline for modular POAU access."""

from django.db import migrations


# Keep this historical definition independent from the mutable operational
# command. Existing rows are matched by code and retain their metadata.
BASE_CAPABILITIES = (
    ('sis_poa.formulate', 'Formular POA/POAU', 'sis-poa'),
    ('sis_poa.poau.edit', 'Editar POAU', 'sis-poa'),
    ('sis_pe.pad.view', 'Ver PAD', 'sis_pe'),
    ('sis_pe.pei.view', 'Ver PEI', 'sis_pe'),
    ('sis_pe.articulacion.view', 'Ver articulacion', 'sis_pe'),
    ('sis_pe.articulacion.edit', 'Editar articulacion', 'sis_pe'),
    ('sis_pe.indicadores.view', 'Ver indicadores', 'sis_pe'),
    ('sis_pe.indicadores.edit', 'Editar indicadores', 'sis_pe'),
    ('sis_pe.evaluacion.view', 'Ver evaluacion', 'sis_pe'),
    ('sis_pe.evaluacion.edit', 'Editar evaluacion', 'sis_pe'),
    ('sis_poa.poau.view', 'Ver POAU', 'sis_poa'),
    ('sis_poa.poau.create', 'Crear POAU', 'sis_poa'),
    ('sis_poa.poau.submit', 'Enviar POAU', 'sis_poa'),
    ('sis_poa.poau.review', 'Revisar POAU', 'sis_poa'),
    ('sis_poa.poau.approve', 'Aprobar POAU', 'sis_poa'),
    ('sis_poa.poa.view', 'Ver POA', 'sis_poa'),
    ('sis_poa.poa.edit', 'Editar POA', 'sis_poa'),
    ('sis_poa.techos.view', 'Ver techos presupuestarios', 'sis_poa'),
    ('sis_poa.techos.edit', 'Editar techos presupuestarios', 'sis_poa'),
    ('sis_poa.distribuciones.view', 'Ver distribuciones', 'sis_poa'),
    ('sis_poa.distribuciones.edit', 'Editar distribuciones', 'sis_poa'),
    ('sis_poa.programacion.view', 'Ver programacion', 'sis_poa'),
    ('sis_poa.programacion.edit', 'Editar programacion', 'sis_poa'),
    ('sis_poa.reportes.view', 'Ver reportes operativos', 'sis_poa'),
    ('sis_poa.seguimiento.view', 'Ver seguimiento', 'sis_poa'),
    ('sis_poa.seguimiento.edit', 'Editar seguimiento', 'sis_poa'),
    ('accounts.usuario.view', 'Ver usuarios', 'accounts'),
    ('accounts.usuario.create', 'Crear usuarios', 'accounts'),
    ('accounts.usuario.edit', 'Editar usuarios', 'accounts'),
    ('accounts.usuario.activate', 'Activar o desactivar usuarios', 'accounts'),
    ('accounts.rol.view', 'Ver roles', 'accounts'),
    ('accounts.rol.create', 'Crear roles', 'accounts'),
    ('accounts.rol.edit', 'Editar roles', 'accounts'),
    ('accounts.capacidad.view', 'Ver capacidades', 'accounts'),
    ('accounts.capacidad.assign', 'Asignar capacidades', 'accounts'),
    ('accounts.alcance.view', 'Ver alcances organizacionales', 'accounts'),
    ('accounts.alcance.assign', 'Asignar alcances organizacionales', 'accounts'),
    ('accounts.solicitud.view', 'Ver solicitudes de acceso', 'accounts'),
    ('accounts.solicitud.approve', 'Aprobar solicitudes de acceso', 'accounts'),
)

BASE_ROLES = {
    'SUPER_ADMIN': (
        'Superadministrador', ('sis_pe.', 'sis_poa.', 'accounts.'), (),
    ),
    'SECRETARIO_MUNICIPAL': ('Secretario Municipal', ('sis_poa.',), ()),
    'DIRECTOR': ('Director', ('sis_poa.',), ()),
    'JEFE_POA': (
        'Jefe POA', ('sis_poa.',), (
            'accounts.usuario.view', 'accounts.usuario.create',
            'accounts.usuario.edit', 'accounts.usuario.activate',
        ),
    ),
    'JEFE_PE': (
        'Jefe PE', ('sis_pe.',), (
            'accounts.usuario.view', 'accounts.usuario.create',
            'accounts.usuario.edit', 'accounts.usuario.activate',
        ),
    ),
    'FORMULADOR_POAU': (
        'Formulador POAU', (), (
            'sis_poa.formulate', 'sis_poa.poau.view', 'sis_poa.poau.create',
            'sis_poa.poau.edit', 'sis_poa.poau.submit',
        ),
    ),
}


def seed_authorization_baseline(apps, schema_editor):
    Capability = apps.get_model('accounts', 'Capacidad')
    Role = apps.get_model('accounts', 'Rol')

    for order, (code, name, system) in enumerate(BASE_CAPABILITIES, start=100):
        Capability.objects.get_or_create(
            codigo=code,
            defaults={
                'nombre': name, 'sistema': system, 'activo': True,
                'orden': order,
            },
        )

    for order, (code, (name, prefixes, explicit)) in enumerate(
        BASE_ROLES.items(), start=1,
    ):
        role, _ = Role.objects.get_or_create(
            codigo=code,
            defaults={
                'nombre': name, 'descripcion': name, 'es_sistema': True,
                'orden': order,
            },
        )
        if not role.es_sistema:
            role.es_sistema = True
            role.save(update_fields=['es_sistema'])

        required_codes = set(explicit)
        for prefix in prefixes:
            required_codes.update(
                Capability.objects.filter(
                    codigo__startswith=prefix,
                ).values_list('codigo', flat=True),
            )
        existing_codes = set(
            role.capacidades.values_list('codigo', flat=True),
        )
        missing = Capability.objects.filter(
            codigo__in=required_codes - existing_codes,
        )
        role.capacidades.add(*missing)

    # The legacy role is created by 0002 and remains part of the operational
    # contract. Reconcile it additively so a clean migration matches the seed.
    legacy_role = Role.objects.filter(codigo='superadmin').first()
    if legacy_role:
        existing_codes = set(
            legacy_role.capacidades.values_list('codigo', flat=True),
        )
        legacy_role.capacidades.add(*Capability.objects.exclude(
            codigo__in=existing_codes,
        ))


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_repair_alcance_fiscal_year_nullability'),
    ]

    operations = [
        migrations.RunPython(
            seed_authorization_baseline,
            migrations.RunPython.noop,
        ),
    ]
