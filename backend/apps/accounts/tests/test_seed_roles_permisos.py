from io import StringIO
from importlib import import_module

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.accounts.models import Capacidad, Rol


MIGRATE_0014 = (
    'accounts', '0014_repair_alcance_fiscal_year_nullability',
)
MIGRATE_0015 = ('accounts', '0015_access_authorization_baseline')
BASE_ROLE_CODES = {
    'SUPER_ADMIN', 'SECRETARIO_MUNICIPAL', 'DIRECTOR', 'JEFE_POA',
    'JEFE_PE', 'FORMULADOR_POAU',
}
BASE_CAPABILITY_CODES = {
    'sis_poa.formulate',
    'sis_poa.poau.edit',
    'sis_pe.pad.view', 'sis_pe.pei.view', 'sis_pe.articulacion.view',
    'sis_pe.articulacion.edit', 'sis_pe.indicadores.view',
    'sis_pe.indicadores.edit', 'sis_pe.evaluacion.view',
    'sis_pe.evaluacion.edit', 'sis_poa.poau.view', 'sis_poa.poau.create',
    'sis_poa.poau.submit', 'sis_poa.poau.review', 'sis_poa.poau.approve',
    'sis_poa.poa.view', 'sis_poa.poa.edit', 'sis_poa.techos.view',
    'sis_poa.techos.edit', 'sis_poa.distribuciones.view',
    'sis_poa.distribuciones.edit', 'sis_poa.programacion.view',
    'sis_poa.programacion.edit', 'sis_poa.reportes.view',
    'sis_poa.seguimiento.view', 'sis_poa.seguimiento.edit',
    'accounts.usuario.view', 'accounts.usuario.create',
    'accounts.usuario.edit', 'accounts.usuario.activate', 'accounts.rol.view',
    'accounts.rol.create', 'accounts.rol.edit', 'accounts.capacidad.view',
    'accounts.capacidad.assign', 'accounts.alcance.view',
    'accounts.alcance.assign', 'accounts.solicitud.view',
    'accounts.solicitud.approve',
}


def _migration_apps(executor, target):
    return executor.loader.project_state([target]).apps


def _restore_leaf_migrations(executor):
    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())


def _clear_baseline(apps):
    Role = apps.get_model('accounts', 'Rol')
    Capability = apps.get_model('accounts', 'Capacidad')
    Role.objects.filter(codigo__in=BASE_ROLE_CODES).delete()
    Capability.objects.filter(codigo__in=BASE_CAPABILITY_CODES).delete()


def _baseline_snapshot(apps):
    Role = apps.get_model('accounts', 'Rol')
    Capability = apps.get_model('accounts', 'Capacidad')
    return {
        'capabilities': Capability.objects.filter(
            codigo__in=BASE_CAPABILITY_CODES,
        ).count(),
        'roles': Role.objects.filter(codigo__in=BASE_ROLE_CODES).count(),
        'grants': {
            role.codigo: tuple(role.capacidades.order_by('codigo').values_list(
                'codigo', flat=True,
            ))
            for role in Role.objects.filter(codigo__in=BASE_ROLE_CODES)
        },
    }


@pytest.mark.django_db
def test_seed_asigna_activacion_a_roles_autorizados_y_es_idempotente():
    Rol.objects.get_or_create(
        codigo='superadmin',
        defaults={
            'nombre': 'Superadministrador Tecnico',
            'es_sistema': True,
        },
    )
    Rol.objects.create(
        codigo='SIN_GESTION_USUARIOS',
        nombre='Sin gestión de usuarios',
    )

    call_command('seed_roles_permisos', stdout=StringIO())

    capacidad = Capacidad.objects.get(codigo='accounts.usuario.activate')
    roles_esperados = {'superadmin', 'SUPER_ADMIN', 'JEFE_PE', 'JEFE_POA'}
    assert set(
        capacidad.roles.filter(codigo__in={
            *roles_esperados,
            'SECRETARIO_MUNICIPAL',
            'DIRECTOR',
            'FORMULADOR_POAU',
            'SIN_GESTION_USUARIOS',
        }).values_list('codigo', flat=True)
    ) == roles_esperados

    relaciones_antes = capacidad.roles.count()
    call_command('seed_roles_permisos', stdout=StringIO())

    capacidad.refresh_from_db()
    assert capacidad.roles.count() == relaciones_antes
    assert set(
        capacidad.roles.filter(codigo__in=roles_esperados)
        .values_list('codigo', flat=True)
    ) == roles_esperados


@pytest.mark.django_db(transaction=True)
def test_seed_and_0015_describe_the_same_authorization_baseline():
    migration = import_module(
        'apps.accounts.migrations.0015_access_authorization_baseline',
    )
    from apps.accounts.management.commands.seed_roles_permisos import (
        CAPACIDADES_BASE,
        CAPACIDADES_NUEVAS,
        ROLES,
    )

    operational = set(CAPACIDADES_BASE + CAPACIDADES_NUEVAS)
    assert operational == set(migration.BASE_CAPABILITIES)
    assert ROLES == migration.BASE_ROLES

    call_command('seed_roles_permisos', stdout=StringIO())
    formulator = Rol.objects.get(codigo='FORMULADOR_POAU')
    assert formulator.capacidades.filter(codigo='sis_poa.formulate').exists()
    first = _baseline_snapshot(Rol.objects.all().model._meta.apps)

    call_command('seed_roles_permisos', stdout=StringIO())
    assert _baseline_snapshot(Rol.objects.all().model._meta.apps) == first


@pytest.mark.django_db(transaction=True)
def test_0015_clean_apply_reapply_is_complete_and_idempotent():
    executor = MigrationExecutor(connection)
    executor.migrate([MIGRATE_0014])
    try:
        _clear_baseline(_migration_apps(executor, MIGRATE_0014))
        executor.loader.build_graph()
        executor.migrate([MIGRATE_0015])

        apps = _migration_apps(executor, MIGRATE_0015)
        migration = import_module(
            'apps.accounts.migrations.0015_access_authorization_baseline',
        )
        Capability = apps.get_model('accounts', 'Capacidad')
        Role = apps.get_model('accounts', 'Rol')
        assert Capability.objects.filter(
            codigo__in=BASE_CAPABILITY_CODES,
        ).count() == len(BASE_CAPABILITY_CODES)
        assert Role.objects.filter(
            codigo__in=BASE_ROLE_CODES,
        ).count() == len(BASE_ROLE_CODES)
        for code, (_, prefixes, explicit) in migration.BASE_ROLES.items():
            grants = set(
                Role.objects.get(codigo=code).capacidades.values_list(
                    'codigo', flat=True,
                ),
            )
            assert set(explicit) <= grants
            for prefix in prefixes:
                expected = set(
                    Capability.objects.filter(
                        codigo__startswith=prefix,
                    ).values_list('codigo', flat=True),
                )
                assert expected <= grants
        assert Role.objects.get(codigo='FORMULADOR_POAU').capacidades.filter(
            codigo='sis_poa.formulate',
        ).exists()
        legacy = Role.objects.filter(codigo='superadmin').first()
        if legacy:
            legacy_grants = set(
                legacy.capacidades.values_list('codigo', flat=True),
            )
            assert BASE_CAPABILITY_CODES <= legacy_grants
        before = _baseline_snapshot(apps)

        migration.seed_authorization_baseline(apps, None)
        assert _baseline_snapshot(apps) == before

        executor.loader.build_graph()
        executor.migrate([MIGRATE_0014])
        assert _baseline_snapshot(
            _migration_apps(executor, MIGRATE_0014),
        ) == before
        executor.loader.build_graph()
        executor.migrate([MIGRATE_0015])
        assert _baseline_snapshot(
            _migration_apps(executor, MIGRATE_0015),
        ) == before
    finally:
        _restore_leaf_migrations(executor)


@pytest.mark.django_db(transaction=True)
def test_0015_preserves_unrelated_grants_when_reconciling():
    executor = MigrationExecutor(connection)
    executor.migrate([MIGRATE_0014])
    try:
        apps = _migration_apps(executor, MIGRATE_0014)
        _clear_baseline(apps)
        Role = apps.get_model('accounts', 'Rol')
        Capability = apps.get_model('accounts', 'Capacidad')
        role = Role.objects.create(
            codigo='FORMULADOR_POAU', nombre='Existing formulator',
        )
        custom = Capability.objects.create(
            codigo='custom.unrelated.grant', nombre='Custom grant',
        )
        role.capacidades.add(custom)
        executor.loader.build_graph()
        executor.migrate([MIGRATE_0015])

        role = _migration_apps(executor, MIGRATE_0015).get_model(
            'accounts', 'Rol',
        ).objects.get(codigo='FORMULADOR_POAU')
        assert role.capacidades.filter(
            codigo='custom.unrelated.grant',
        ).exists()
        assert role.capacidades.filter(codigo='sis_poa.formulate').exists()
    finally:
        _restore_leaf_migrations(executor)
