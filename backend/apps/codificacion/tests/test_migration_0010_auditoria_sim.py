"""MigrationExecutor proof for persistent SIM migration audit structures."""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


MIGRATE_FROM = ('codificacion', '0009_fuente_normativa_e_idempotencia')
MIGRATE_TO = ('codificacion', '0010_auditoria_migracion_sim')


@pytest.mark.django_db(transaction=True)
def test_migracion_0010_forward_reverse_reapply_preserva_legacy():
    executor = MigrationExecutor(connection)
    executor.migrate([MIGRATE_FROM])
    # Build historical states that include every other app at its latest migration
    # so models referenced by codificacion (e.g. articulacion.LineamientoPAD) exist.
    other_leaf_nodes = [
        node for node in executor.loader.graph.leaf_nodes() if node[0] != 'codificacion'
    ]

    def state_at(*nodes):
        return executor.loader.project_state(other_leaf_nodes + list(nodes)).apps

    old_apps = state_at(MIGRATE_FROM)
    LineamientoLegacy = old_apps.get_model('articulacion', 'LineamientoPAD')
    legacy = LineamientoLegacy.objects.create(
        codigo='SIM-LL-01',
        denominacion='Lineamiento legacy preservado',
        gestion_desde=2026,
        gestion_hasta=2030,
    )

    try:
        executor.loader.build_graph()
        executor.migrate([MIGRATE_TO])
        apps_0010 = state_at(MIGRATE_TO)
        Ejecucion = apps_0010.get_model('codificacion', 'EjecucionMigracionSIM')
        Mapeo = apps_0010.get_model('codificacion', 'MapeoLineamientoPADLegacy')
        assert Ejecucion._meta.db_table == 'codificacion_ejecucionmigracionsim'
        assert Mapeo._meta.db_table == 'codificacion_mapeolineamientopadlegacy'
        assert apps_0010.get_model(
            'articulacion', 'LineamientoPAD',
        ).objects.filter(pk=legacy.pk).exists()

        executor.loader.build_graph()
        executor.migrate([MIGRATE_FROM])
        apps_reversed = state_at(MIGRATE_FROM)
        assert apps_reversed.get_model(
            'articulacion', 'LineamientoPAD',
        ).objects.filter(pk=legacy.pk).exists()

        executor.loader.build_graph()
        executor.migrate([MIGRATE_TO])
        apps_reapplied = state_at(MIGRATE_TO)
        assert apps_reapplied.get_model(
            'articulacion', 'LineamientoPAD',
        ).objects.filter(pk=legacy.pk).exists()
    finally:
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
