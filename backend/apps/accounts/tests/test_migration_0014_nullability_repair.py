"""Physical-schema proof for the forward-only 0014 nullability repair."""

from copy import copy

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

MIGRATE_FROM = [
    ('accounts', '0012_usuario_estado'),
    ('organizacion', '0002_alter_direccionadministrativa_options_and_more'),
]
MIGRATE_0013 = ('accounts', '0013_poau_scope_backfill')
MIGRATE_0014 = (
    'accounts', '0014_repair_alcance_fiscal_year_nullability',
)
CONSTRAINT = 'uniq_alcance_usuario_rol_unidad_gestion'


def _apps(executor, target):
    targets = target if isinstance(target, list) else [target]
    return executor.loader.project_state(targets).apps


def _model(executor, target):
    return _apps(executor, target).get_model(
        'accounts', 'AlcanceOrganizacional',
    )


def _column(Model):
    field = Model._meta.get_field('fiscal_year')
    with connection.cursor() as cursor:
        columns = {
            column.name: column
            for column in connection.introspection.get_table_description(
                cursor, Model._meta.db_table,
            )
        }
    return columns[field.column]


def _constraints(Model):
    with connection.cursor() as cursor:
        return connection.introspection.get_constraints(
            cursor, Model._meta.db_table,
        )


def _is_applied(executor, target):
    return executor.recorder.migration_qs.filter(
        app=target[0], name=target[1],
    ).exists()


def _seed_scopes(apps):
    Gestion = apps.get_model('gestion', 'GestionFiscal')
    Tipo = apps.get_model('organizacion', 'TipoUnidad')
    Unidad = apps.get_model('organizacion', 'UnidadOrganizacional')
    Usuario = apps.get_model('accounts', 'Usuario')
    Rol = apps.get_model('accounts', 'Rol')
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Alcance = apps.get_model('accounts', 'AlcanceOrganizacional')
    gestion = Gestion.objects.create(anio=2196, activa=False)
    tipo = Tipo.objects.create(codigo='MIG-0014', nombre='Migration', nivel=1)
    unidad = Unidad.objects.create(
        codigo='MIG-0014', nombre='Migration', tipo=tipo, gestion=gestion,
        fecha_vigencia_desde='2196-01-01',
    )
    ids = {'gestion': gestion.pk, 'unidad': unidad.pk}
    for domain, system in (('pe', 'sis_pe'), ('poa', 'sis_poa')):
        capacidad = Capacidad.objects.create(
            codigo=f'sis_{domain}.mig.0014', nombre='Migration', sistema=system,
        )
        rol = Rol.objects.create(codigo=f'MIG-0014-{domain}', nombre='Migration')
        rol.capacidades.add(capacidad)
        usuario = Usuario.objects.create(email=f'{domain}-0014@test.example')
        Alcance.objects.create(
            usuario=usuario, rol=rol, unidad=unidad, fiscal_year=None,
            scope_type='SELF', activo=True,
        )
        ids[domain] = usuario.pk
        ids[f'rol_{domain}'] = rol.pk
    return ids


def _assert_nullable_schema(executor, target, *, repair_applied):
    Model = _model(executor, target)
    field = Model._meta.get_field('fiscal_year')
    constraints = _constraints(Model)

    assert field.null is True
    assert _column(Model).null_ok is True
    assert _is_applied(executor, MIGRATE_0014) is repair_applied
    assert constraints[CONSTRAINT]['unique'] is True
    assert constraints[CONSTRAINT]['columns'] == [
        'usuario_id', 'rol_id', 'unidad_id', 'fiscal_year_id',
    ]
    expected_fk = (
        field.remote_field.model._meta.db_table, field.target_field.column,
    )
    assert any(
        data['foreign_key'] == expected_fk
        and field.column in data['columns']
        for data in constraints.values()
    )
    return Model


def _scope_rows(Model):
    return list(
        Model.objects.order_by('pk').values_list(
            'pk', 'usuario_id', 'rol_id', 'unidad_id', 'fiscal_year_id',
            'scope_type', 'activo',
        )
    )


def _manufacture_not_null(Model):
    nullable_field = Model._meta.get_field('fiscal_year')
    non_null_field = copy(nullable_field)
    non_null_field.null = False
    with connection.schema_editor() as schema_editor:
        schema_editor.alter_field(
            Model, nullable_field, non_null_field, strict=True,
        )
    assert _column(Model).null_ok is False


def _restore_leaf_migrations(executor):
    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_fresh_path_preserves_yearless_pe_and_schema_integrity():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    try:
        ids = _seed_scopes(_apps(executor, MIGRATE_FROM))
        executor.loader.build_graph()
        executor.migrate([MIGRATE_0014])

        Alcance = _assert_nullable_schema(
            executor, MIGRATE_0014, repair_applied=True,
        )
        assert Alcance.objects.get(usuario_id=ids['pe']).fiscal_year_id is None
        assert (
            Alcance.objects.get(usuario_id=ids['poa']).fiscal_year_id
            == ids['gestion']
        )
    finally:
        _restore_leaf_migrations(executor)


@pytest.mark.django_db(transaction=True)
def test_recorded_0013_drift_repairs_reverse_and_reapply_converge():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    try:
        ids = _seed_scopes(_apps(executor, MIGRATE_FROM))
        executor.loader.build_graph()
        executor.migrate([MIGRATE_0013])
        Alcance0013 = _model(executor, MIGRATE_0013)
        Alcance0013.objects.filter(usuario_id=ids['pe']).delete()
        before = _scope_rows(Alcance0013)

        _manufacture_not_null(Alcance0013)
        assert _is_applied(executor, MIGRATE_0013) is True
        executor.loader.build_graph()
        executor.migrate([MIGRATE_0014])

        Alcance0014 = _assert_nullable_schema(
            executor, MIGRATE_0014, repair_applied=True,
        )
        assert _scope_rows(Alcance0014) == before
        yearless = Alcance0014.objects.create(
            usuario_id=ids['pe'], rol_id=ids['rol_pe'],
            unidad_id=ids['unidad'], fiscal_year_id=None,
            scope_type='SELF', activo=True,
        )
        assert yearless.fiscal_year_id is None

        executor.loader.build_graph()
        executor.migrate([MIGRATE_0013])
        Alcance0013 = _assert_nullable_schema(
            executor, MIGRATE_0013, repair_applied=False,
        )
        assert Alcance0013.objects.get(pk=yearless.pk).fiscal_year_id is None

        executor.loader.build_graph()
        executor.migrate([MIGRATE_0014])
        Alcance0014 = _assert_nullable_schema(
            executor, MIGRATE_0014, repair_applied=True,
        )
        assert Alcance0014.objects.get(pk=yearless.pk).fiscal_year_id is None
    finally:
        _restore_leaf_migrations(executor)
