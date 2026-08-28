"""Make POAU organizational scopes year-safe before scope hardening.

Domain-aware contract: ``fiscal_year`` stays nullable because yearless
SIS-PE scopes are valid persisted state. The backfill infers fiscal years
ONLY for SIS-POA roles (from the unit's exact gestion) and from exact
legacy POAU assignments; yearless SIS-PE rows never receive a synthetic
year, and ambiguous or conflicting data fails loudly.

Restart safety: PostgreSQL transactional DDL keeps data normalization, schema
changes, and migration recording in one transaction. Django's deferred FK
checks are forced before the uniqueness DDL so PostgreSQL has no pending
trigger events when the constraint is added.
"""

from collections import defaultdict

import django.db.models.deletion
from django.db import migrations, models


CONSTRAINT_NAME = 'uniq_alcance_usuario_rol_unidad_gestion'

# Real data mixes the new 'sis_poa' capacity system (seeds) with the legacy
# 'sis-poa' spelling (accounts migrations 0002-0008); both mark SIS-POA roles.
SIS_POA_SISTEMAS = ('sis_poa', 'sis-poa')


def _unique_constraint():
    return models.UniqueConstraint(
        fields=('usuario', 'rol', 'unidad', 'fiscal_year'),
        name=CONSTRAINT_NAME,
        nulls_distinct=False,
    )


def _sis_poa_role_ids(apps):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    return set(
        Capacidad.objects.filter(
            sistema__in=SIS_POA_SISTEMAS,
        ).values_list('roles', flat=True),
    )


def _normalize_existing_years(AlcanceOrganizacional, sis_poa_role_ids):
    """Give yearless SIS-POA scopes the unit's exact fiscal year.

    Yearless scopes without a SIS-POA role are valid SIS-PE state and must
    never receive a synthetic fiscal year.
    """
    for alcance in AlcanceOrganizacional.objects.filter(
        fiscal_year__isnull=True,
        rol_id__in=sis_poa_role_ids,
    ).select_related('unidad').order_by('pk'):
        alcance.fiscal_year_id = alcance.unidad.gestion_id
        alcance.save(update_fields=['fiscal_year'])


def _reject_year_mismatches(AlcanceOrganizacional):
    # Only rows with an explicit year can mismatch; yearless rows are valid.
    mismatches = [
        str(alcance.pk)
        for alcance in AlcanceOrganizacional.objects.filter(
            fiscal_year__isnull=False,
        ).select_related(
            'unidad',
        ).order_by('pk')
        if alcance.fiscal_year_id != alcance.unidad.gestion_id
    ]
    if mismatches:
        raise RuntimeError(
            'POAU scope migration requires a data decision: fiscal year does '
            f'not match the organizational unit for scopes {mismatches[:10]}.'
        )


def _deduplicate_exact_scopes(AlcanceOrganizacional):
    grouped = defaultdict(list)
    for alcance in AlcanceOrganizacional.objects.order_by('pk'):
        key = (
            alcance.usuario_id,
            alcance.rol_id,
            alcance.unidad_id,
            alcance.fiscal_year_id,
        )
        grouped[key].append(alcance)

    for key, scopes in grouped.items():
        if len(scopes) == 1:
            continue
        semantics = {
            (
                scope.scope_type,
                scope.activo,
                scope.vigente_desde,
                scope.vigente_hasta,
            )
            for scope in scopes
        }
        if len(semantics) != 1:
            raise RuntimeError(
                'POAU scope migration requires a data decision: conflicting '
                f'duplicate scopes exist for key {tuple(map(str, key))}.'
            )
        AlcanceOrganizacional.objects.filter(
            pk__in=[scope.pk for scope in scopes[1:]],
        ).delete()


def _backfill_legacy_assignments(apps, AlcanceOrganizacional):
    AsignacionUsuarioUnidad = apps.get_model(
        'organizacion', 'AsignacionUsuarioUnidad',
    )
    for assignment in AsignacionUsuarioUnidad.objects.select_related(
        'unidad',
    ).order_by('pk'):
        if assignment.gestion_id != assignment.unidad.gestion_id:
            raise RuntimeError(
                'POAU scope migration requires a data decision: legacy '
                f'assignment {assignment.pk} has an ambiguous fiscal year.'
            )
        lookup = {
            'usuario_id': assignment.usuario_id,
            'unidad_id': assignment.unidad_id,
            'fiscal_year_id': assignment.gestion_id,
        }
        if not AlcanceOrganizacional.objects.filter(**lookup).exists():
            AlcanceOrganizacional.objects.create(
                **lookup,
                rol_id=None,
                scope_type='SELF',
                activo=assignment.activo,
            )


def normalize_poau_scopes(apps, schema_editor):
    AlcanceOrganizacional = apps.get_model(
        'accounts', 'AlcanceOrganizacional',
    )
    sis_poa_role_ids = _sis_poa_role_ids(apps)
    _normalize_existing_years(AlcanceOrganizacional, sis_poa_role_ids)
    _reject_year_mismatches(AlcanceOrganizacional)
    _deduplicate_exact_scopes(AlcanceOrganizacional)
    _backfill_legacy_assignments(apps, AlcanceOrganizacional)
    if AlcanceOrganizacional.objects.filter(
        fiscal_year__isnull=True,
        rol_id__in=sis_poa_role_ids,
    ).exists():
        raise RuntimeError(
            'POAU scope migration left SIS-POA scopes without a fiscal year.',
        )
    if schema_editor is not None:
        schema_editor.connection.check_constraints()


class Migration(migrations.Migration):

    atomic = True

    dependencies = [
        ('accounts', '0012_usuario_estado'),
        ('organizacion', '0002_alter_direccionadministrativa_options_and_more'),
    ]

    operations = [
        migrations.RunPython(
            normalize_poau_scopes,
            migrations.RunPython.noop,
            atomic=True,
        ),
        migrations.AlterField(
            model_name='alcanceorganizacional',
            name='fiscal_year',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='alcances_organizacionales',
                to='gestion.gestionfiscal',
            ),
        ),
        migrations.AddConstraint(
            model_name='alcanceorganizacional',
            constraint=_unique_constraint(),
        ),
    ]
