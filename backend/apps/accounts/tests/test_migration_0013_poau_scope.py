"""Migration proof for domain-aware year-safe organizational scopes."""

from datetime import date
from importlib import import_module

import pytest
from django.db import IntegrityError, connection, migrations, transaction
from django.db.migrations.executor import MigrationExecutor


MIGRATE_FROM = [
    ('accounts', '0012_usuario_estado'),
    ('organizacion', '0002_alter_direccionadministrativa_options_and_more'),
]
MIGRATE_TO = ('accounts', '0013_poau_scope_backfill')
CONSTRAINT = 'uniq_alcance_usuario_rol_unidad_gestion'


class MigrationInterrupted(RuntimeError):
    """Simulated crash at a migration operation boundary."""


def _interrupt(apps, schema_editor):
    raise MigrationInterrupted('simulated crash at operation boundary')


def _seed_pre_migration_data(apps):
    """Seed yearless SIS-PE/SIS-POA scopes plus one exact legacy assignment."""
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    TipoUnidad = apps.get_model('organizacion', 'TipoUnidad')
    UnidadOrganizacional = apps.get_model(
        'organizacion', 'UnidadOrganizacional',
    )
    AsignacionUsuarioUnidad = apps.get_model(
        'organizacion', 'AsignacionUsuarioUnidad',
    )
    Usuario = apps.get_model('accounts', 'Usuario')
    Rol = apps.get_model('accounts', 'Rol')
    Capacidad = apps.get_model('accounts', 'Capacidad')
    AlcanceOrganizacional = apps.get_model(
        'accounts', 'AlcanceOrganizacional',
    )

    # The 0012-state historical GestionFiscal still defaults `activa=True`
    # (gestion 0005 is not part of that state), so be explicit to respect
    # the partial unique constraint `unica_gestion_habilitada`.
    gestion, _ = GestionFiscal.objects.get_or_create(
        anio=2197, defaults={'activa': False},
    )
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='MIG-0013',
        defaults={'nombre': 'Migration test unit', 'nivel': 1},
    )
    unidad, _ = UnidadOrganizacional.objects.get_or_create(
        codigo='MIG-0013', gestion=gestion,
        defaults={
            'nombre': 'Migration test unit',
            'tipo': tipo,
            'fecha_vigencia_desde': date(2197, 1, 1),
        },
    )
    # Real data mixes underscore ('sis_pe') and legacy hyphen ('sis-poa')
    # capacity systems; the SIS-POA role uses the legacy hyphen variant.
    capacidad_pe, _ = Capacidad.objects.get_or_create(
        codigo='sis_pe.mig.edit',
        defaults={'nombre': 'PE migration test', 'sistema': 'sis_pe'},
    )
    capacidad_poa, _ = Capacidad.objects.get_or_create(
        codigo='sis_poa.mig.edit',
        defaults={'nombre': 'POA migration test', 'sistema': 'sis-poa'},
    )
    rol_pe, _ = Rol.objects.get_or_create(
        codigo='MIG-0013-PE', defaults={'nombre': 'PE test role'},
    )
    rol_pe.capacidades.add(capacidad_pe)
    rol_poa, _ = Rol.objects.get_or_create(
        codigo='MIG-0013-POA', defaults={'nombre': 'POA test role'},
    )
    rol_poa.capacidades.add(capacidad_poa)
    usuario_pe, _ = Usuario.objects.get_or_create(email='pe@test.example')
    usuario_poa, _ = Usuario.objects.get_or_create(email='poa@test.example')
    usuario_legacy, _ = Usuario.objects.get_or_create(
        email='legacy@test.example',
    )
    AlcanceOrganizacional.objects.filter(
        usuario_id__in=[usuario_pe.pk, usuario_poa.pk],
    ).delete()
    AsignacionUsuarioUnidad.objects.filter(usuario=usuario_legacy).delete()

    AlcanceOrganizacional.objects.create(
        usuario=usuario_pe, rol=rol_pe, unidad=unidad, fiscal_year=None,
        scope_type='SELF', activo=True,
    )
    AlcanceOrganizacional.objects.create(
        usuario=usuario_poa, rol=rol_poa, unidad=unidad, fiscal_year=None,
        scope_type='SELF', activo=True,
    )
    AsignacionUsuarioUnidad.objects.create(
        usuario=usuario_legacy, unidad=unidad, gestion=gestion, activo=True,
    )
    return {
        'gestion': gestion.pk,
        'unidad': unidad.pk,
        'rol_pe': rol_pe.pk,
        'rol_poa': rol_poa.pk,
        'pe': usuario_pe.pk,
        'poa': usuario_poa.pk,
        'legacy': usuario_legacy.pk,
    }


def _applied(executor, target):
    return executor.recorder.migration_qs.filter(
        app=target[0], name=target[1],
    ).exists()


def _constraint_present():
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(
            cursor, 'cuentas_alcance_organizacional',
        )
    return CONSTRAINT in constraints


def _assert_converged(executor, ids):
    migrated_apps = executor.loader.project_state([MIGRATE_TO]).apps
    Alcance = migrated_apps.get_model('accounts', 'AlcanceOrganizacional')
    # Yearless SIS-PE scope is valid persisted state and never gets a year.
    assert Alcance.objects.get(usuario_id=ids['pe']).fiscal_year_id is None
    # SIS-POA scope received the unit's exact fiscal year.
    assert (
        Alcance.objects.get(usuario_id=ids['poa']).fiscal_year_id
        == ids['gestion']
    )
    # Exact legacy assignment produced exactly one year-safe scope.
    legacy = Alcance.objects.filter(usuario_id=ids['legacy'])
    assert legacy.count() == 1
    assert legacy.get().fiscal_year_id == ids['gestion']
    assert legacy.get().scope_type == 'SELF'
    assert _constraint_present()


def _assert_interrupted_state(executor, ids):
    """An interrupted migration rolls data, DDL, and recording back together."""
    apps_0012 = executor.loader.project_state(MIGRATE_FROM).apps
    Alcance = apps_0012.get_model('accounts', 'AlcanceOrganizacional')
    assert Alcance.objects.get(usuario_id=ids['poa']).fiscal_year_id is None
    assert Alcance.objects.get(usuario_id=ids['pe']).fiscal_year_id is None
    assert not Alcance.objects.filter(usuario_id=ids['legacy']).exists()
    assert not _constraint_present()


def _interrupt_and_retry(after_operation):
    """Crash 0013 after `after_operation`, prove rollback, then converge."""
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    # Rebuild the graph so the loader's `applied_migrations` cache reflects
    # the reversal, then capture the LIVE migration instance it will execute.
    # Never call `build_graph()` again before the migrate calls below: it
    # re-instantiates migrations from disk and would drop the mutation.
    executor.loader.build_graph()
    old_apps = executor.loader.project_state(MIGRATE_FROM).apps
    migration = executor.loader.graph.nodes[MIGRATE_TO]
    original_operations = list(migration.operations)
    try:
        ids = _seed_pre_migration_data(old_apps)
        migration.operations = original_operations[:after_operation + 1] + [
            migrations.RunPython(_interrupt, migrations.RunPython.noop),
        ]
        with pytest.raises(MigrationInterrupted):
            executor.migrate([MIGRATE_TO])
        assert not _applied(executor, MIGRATE_TO)
        _assert_interrupted_state(executor, ids)

        migration.operations = original_operations
        executor.migrate([MIGRATE_TO])
        assert _applied(executor, MIGRATE_TO)
        _assert_converged(executor, ids)
    finally:
        migration.operations = original_operations
        # Refresh the loader cache so the leaf migration is not re-applied
        # after a successful run (new instances come from disk, unmutated).
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_migration_backfills_poa_scopes_and_preserves_yearless_pe():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    old_apps = executor.loader.project_state(MIGRATE_FROM).apps
    try:
        ids = _seed_pre_migration_data(old_apps)
        executor.loader.build_graph()
        executor.migrate([MIGRATE_TO])
        _assert_converged(executor, ids)

        migrated_apps = executor.loader.project_state([MIGRATE_TO]).apps
        Alcance = migrated_apps.get_model(
            'accounts', 'AlcanceOrganizacional',
        )
        migration = import_module(
            'apps.accounts.migrations.0013_poau_scope_backfill',
        )
        before = Alcance.objects.count()
        migration.normalize_poau_scopes(migrated_apps, None)
        assert Alcance.objects.count() == before

        with pytest.raises(IntegrityError), transaction.atomic():
            Alcance.objects.create(
                usuario_id=ids['pe'], rol_id=ids['rol_pe'],
                unidad_id=ids['unidad'], fiscal_year_id=None,
                scope_type='SELF',
            )
        with pytest.raises(IntegrityError), transaction.atomic():
            Alcance.objects.create(
                usuario_id=ids['poa'], rol_id=ids['rol_poa'],
                unidad_id=ids['unidad'], fiscal_year_id=ids['gestion'],
                scope_type='SELF',
            )
    finally:
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_migration_rejects_conflicting_data_loudly():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    old_apps = executor.loader.project_state(MIGRATE_FROM).apps
    conflicto = None
    asignacion_conflicto = None
    try:
        ids = _seed_pre_migration_data(old_apps)
        GestionFiscal = old_apps.get_model('gestion', 'GestionFiscal')
        otra_gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2198, defaults={'activa': False},
        )
        Usuario = old_apps.get_model('accounts', 'Usuario')
        AlcanceOrganizacional = old_apps.get_model(
            'accounts', 'AlcanceOrganizacional',
        )
        AsignacionUsuarioUnidad = old_apps.get_model(
            'organizacion', 'AsignacionUsuarioUnidad',
        )
        usuario_conflicto, _ = Usuario.objects.get_or_create(
            email='conflicto@test.example',
        )
        conflicto = AlcanceOrganizacional.objects.create(
            usuario=usuario_conflicto, rol_id=ids['rol_pe'],
            unidad_id=ids['unidad'], fiscal_year=otra_gestion,
            scope_type='SELF', activo=True,
        )
        asignacion_conflicto = AsignacionUsuarioUnidad.objects.create(
            usuario=usuario_conflicto, unidad_id=ids['unidad'],
            gestion=otra_gestion, activo=True,
        )
        executor.loader.build_graph()
        with pytest.raises(RuntimeError, match='requires a data decision'):
            executor.migrate([MIGRATE_TO])
        assert not _applied(executor, MIGRATE_TO)
    finally:
        if asignacion_conflicto is not None:
            asignacion_conflicto.delete()
        if conflicto is not None:
            conflicto.delete()
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_retry_after_normalization_boundary_converges():
    _interrupt_and_retry(0)


@pytest.mark.django_db(transaction=True)
def test_retry_after_field_alteration_boundary_converges():
    _interrupt_and_retry(1)


@pytest.mark.django_db(transaction=True)
def test_retry_around_uniqueness_enforcement_converges():
    _interrupt_and_retry(2)
