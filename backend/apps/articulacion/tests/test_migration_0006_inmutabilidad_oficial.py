"""Behavioral proof for PostgreSQL immutability of official coding rows."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.db.migrations.executor import MigrationExecutor

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    OperacionPOAU,
    ProductoPEI,
    ResultadoPEI,
    TareaPOAU,
)


MIGRATE_WITHOUT_TRIGGER = (
    'articulacion',
    '0005_accionpoa_articulacion_incompleta_and_more',
)
MIGRATE_WITH_TRIGGER = (
    'articulacion',
    '0006_inmutabilidad_codigo_oficial',
)


def _crear_cadena():
    resultado = ResultadoPEI.objects.create(
        codigo_resultado='TRIGGER-RI', denominacion='RI trigger',
        cod_entidad='1312', entidad='GAM Sacaba',
        vigencia_desde=2027, vigencia_hasta=2030,
    )
    producto = ProductoPEI.objects.create(
        codigo_producto='TRIGGER-PI', denominacion='PI trigger',
        resultado_pei=resultado,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='TRIGGER-ACP', denominacion='ACP trigger',
        producto_pei=producto, gestion=2027,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='TRIGGER-OP', denominacion='OP trigger',
        tipo_operacion='Operación', accion_poa=accion,
    )
    actividad = ActividadPOAU.objects.create(
        codigo_actividad='TRIGGER-ACT', denominacion='ACT trigger',
        operacion=operacion,
    )
    tareas = [
        TareaPOAU.objects.create(
            codigo_tarea=f'TRIGGER-TAR-{indice}',
            denominacion=f'Tarea trigger {indice}', actividad=actividad,
        )
        for indice in (1, 2)
    ]
    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE articulacion_tareapoau SET estado_codigo = %s '
            'WHERE id IN (%s, %s)',
            ['oficial', tareas[0].pk, tareas[1].pk],
        )
    return tareas


def _upsert_directo(pk, denominacion):
    with connection.cursor() as cursor:
        cursor.execute(
            'INSERT INTO articulacion_tareapoau '
            'SELECT * FROM articulacion_tareapoau WHERE id = %s '
            'ON CONFLICT (id) DO UPDATE SET denominacion = %s',
            [pk, denominacion],
        )


def _delete_directo(pk):
    with connection.cursor() as cursor:
        cursor.execute(
            'DELETE FROM articulacion_tareapoau WHERE id = %s',
            [pk],
        )


@pytest.mark.django_db(transaction=True)
def test_trigger_forward_reverse_y_reapply_bloquea_update_delete_y_upsert():
    executor = MigrationExecutor(connection)

    try:
        executor.migrate([MIGRATE_WITHOUT_TRIGGER])
        tarea_update, tarea_delete = _crear_cadena()

        executor.loader.build_graph()
        executor.migrate([MIGRATE_WITH_TRIGGER])

        with pytest.raises(DatabaseError):
            with transaction.atomic():
                _upsert_directo(tarea_update.pk, 'Upsert bloqueado')
        with pytest.raises(DatabaseError):
            with transaction.atomic():
                _delete_directo(tarea_delete.pk)

        executor.loader.build_graph()
        executor.migrate([MIGRATE_WITHOUT_TRIGGER])
        _upsert_directo(tarea_update.pk, 'Upsert permitido sin trigger')
        _delete_directo(tarea_delete.pk)
        tarea_update.refresh_from_db()
        assert tarea_update.denominacion == 'Upsert permitido sin trigger'
        assert not TareaPOAU._base_manager.filter(pk=tarea_delete.pk).exists()

        executor.loader.build_graph()
        executor.migrate([MIGRATE_WITH_TRIGGER])
        with pytest.raises(DatabaseError):
            with transaction.atomic():
                _upsert_directo(tarea_update.pk, 'Bloqueado tras reaplicar')
    finally:
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
