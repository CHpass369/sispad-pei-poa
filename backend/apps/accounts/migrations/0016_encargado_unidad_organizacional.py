"""Organizational-unit leadership declared during public registration.

Two things:

1. ``Usuario.solicita_encargado_unidad``: the checkbox the applicant ticks
   under the organizational unit. It is a DECLARATION, not a grant —
   ``/api/v2/auth/register/`` is ``AllowAny``, so the flag only preselects the
   default role for the administrator who approves the request.

2. ``ENCARGADO_UO`` and ``VALIDADOR_POAU``: the POAU roles that separate an
   approver from a validator. Both are seeded here (not only in
   ``seed_roles_permisos``) so an installation that just runs ``migrate`` has
   them available when it approves its first request.

``BASE_ROLES`` extends the 0015 baseline and keeps its exact shape
``{code: (name, capability_prefixes, explicit_capabilities)}``, so the seed
command stays comparable against the union of both migrations. Every capability
these roles need already exists in ``0015.BASE_CAPABILITIES``.

Idempotent: ``get_or_create`` plus additive ``add()`` of the missing
capabilities, the same contract as 0015. The territorial scope (``SELF``) is
not stored here — ``SCOPES_FIJOS_ROLES_SISTEMA`` applies it when the
``AlcanceOrganizacional`` is created.
"""
from django.db import migrations, models


# Sin `sis_poa.formulate` a proposito: esa capacidad tambien abre Presupuesto
# de Gastos, Presupuesto de Recursos, el Dashboard POA, Priorizacion POA y el
# POA completo. Estos perfiles solo alcanzan las tres pantallas POAU de su
# unidad, gobernadas por `sis_poa.poau.*`.
VALIDATOR_CAPABILITIES = (
    'sis_poa.poau.view',
    'sis_poa.poau.create',
    'sis_poa.poau.edit',
    'sis_poa.poau.submit',
    'sis_poa.poau.review',
)
LEAD_CAPABILITIES = VALIDATOR_CAPABILITIES + ('sis_poa.poau.approve',)

BASE_ROLES = {
    'VALIDADOR_POAU': (
        'Validador POAU de unidad', (), VALIDATOR_CAPABILITIES,
    ),
    'ENCARGADO_UO': (
        'Encargado de Unidad Organizacional', (), LEAD_CAPABILITIES,
    ),
}


def seed_unit_leadership_roles(apps, schema_editor):
    Capability = apps.get_model('accounts', 'Capacidad')
    Role = apps.get_model('accounts', 'Rol')

    for order, (code, (name, prefixes, explicit)) in enumerate(
        BASE_ROLES.items(), start=70,
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


def drop_unused_unit_leadership_roles(apps, schema_editor):
    """Withdraw the roles only when nobody uses them; a role in use stays."""
    Role = apps.get_model('accounts', 'Rol')
    Role.objects.filter(
        codigo__in=BASE_ROLES,
        usuarios__isnull=True,
        alcances__isnull=True,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_access_authorization_baseline'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='solicita_encargado_unidad',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            seed_unit_leadership_roles,
            drop_unused_unit_leadership_roles,
        ),
    ]
