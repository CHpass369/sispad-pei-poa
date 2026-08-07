"""Migration regression proof for the HomologacionCodigo append-only trigger."""

import uuid

import pytest
from django.db import DatabaseError, connection, transaction
from django.db.migrations.executor import MigrationExecutor


MIGRATE_WITHOUT_TRIGGER = ('codificacion', '0007_secuencia_y_homologacion')
MIGRATE_WITH_TRIGGER = (
    'codificacion',
    '0008_homologacion_append_only_trigger',
)


def _insert_homologacion(apps, suffix):
    Usuario = apps.get_model('accounts', 'Usuario')
    HomologacionCodigo = apps.get_model('codificacion', 'HomologacionCodigo')
    usuario = Usuario.objects.create(
        email=f'migration-trigger-{suffix}@test.gob.bo',
        password='not-used',
    )
    return HomologacionCodigo.objects.create(
        tipo_entidad='operacion_poau',
        entidad_id=uuid.uuid4(),
        codigo_anterior=f'SIM-2027-{suffix}',
        codigo_nuevo=f'CODIGO-NUEVO-{suffix}',
        motivo=f'Motivo original {suffix}',
        gestion=2027,
        usuario=usuario,
    )


def _update_directo(pk, motivo):
    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE codificacion_homologacioncodigo '
            'SET motivo = %s WHERE id = %s',
            [motivo, pk],
        )


def _delete_directo(pk):
    with connection.cursor() as cursor:
        cursor.execute(
            'DELETE FROM codificacion_homologacioncodigo WHERE id = %s',
            [pk],
        )


def _assert_trigger_bloquea_update_y_delete(update_pk, delete_pk):
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            _update_directo(update_pk, 'Alterado con trigger')

    with pytest.raises(DatabaseError):
        with transaction.atomic():
            _delete_directo(delete_pk)


@pytest.mark.django_db(transaction=True)
def test_reverse_y_forward_sql_controlan_trigger_append_only():
    executor = MigrationExecutor(connection)

    try:
        executor.migrate([MIGRATE_WITH_TRIGGER])
        apps_0008 = executor.loader.project_state([MIGRATE_WITH_TRIGGER]).apps
        fila_update = _insert_homologacion(apps_0008, 'UPDATE')
        fila_delete = _insert_homologacion(apps_0008, 'DELETE')

        _assert_trigger_bloquea_update_y_delete(
            fila_update.pk,
            fila_delete.pk,
        )

        executor.loader.build_graph()
        executor.migrate([MIGRATE_WITHOUT_TRIGGER])
        apps_0007 = executor.loader.project_state(
            [MIGRATE_WITHOUT_TRIGGER]
        ).apps
        HomologacionSinTrigger = apps_0007.get_model(
            'codificacion',
            'HomologacionCodigo',
        )

        _update_directo(fila_update.pk, 'Alterado sin trigger')
        _delete_directo(fila_delete.pk)
        assert HomologacionSinTrigger.objects.get(
            pk=fila_update.pk,
        ).motivo == 'Alterado sin trigger'
        assert not HomologacionSinTrigger.objects.filter(
            pk=fila_delete.pk,
        ).exists()

        executor.loader.build_graph()
        executor.migrate([MIGRATE_WITH_TRIGGER])
        _assert_trigger_bloquea_update_y_delete(
            fila_update.pk,
            fila_update.pk,
        )
    finally:
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
