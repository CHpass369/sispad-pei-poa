"""Reproducible migration proof for legacy articulacion rows."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


MIGRATE_FROM = ('articulacion', '0003_resultadopad_nodo_pdesa')
MIGRATE_TO = ('articulacion', '0004_mixin_codigo_segmentado')
MIGRATE_TO_0005 = (
    'articulacion',
    '0005_accionpoa_articulacion_incompleta_and_more',
)
MODEL_LEGACY_FIELDS = {
    'ResultadoPAD': ('codigo_resultado', 'LEGACY-RP-01'),
    'ProductoPAD': ('codigo_producto', 'LEGACY-PP-01'),
    'ResultadoPEI': ('codigo_resultado', 'LEGACY-RI-01'),
    'ProductoPEI': ('codigo_producto', 'LEGACY-PI-01'),
    'AccionPOA': ('codigo_accion', 'LEGACY-ACP-01'),
    'OperacionPOAU': ('codigo_operacion', 'LEGACY-OP-01'),
    'ActividadPOAU': ('codigo_actividad', 'LEGACY-ACT-01'),
    'TareaPOAU': ('codigo_tarea', 'LEGACY-TAR-01'),
}


def _create_legacy_chain(apps):
    ResultadoPAD = apps.get_model('articulacion', 'ResultadoPAD')
    ProductoPAD = apps.get_model('articulacion', 'ProductoPAD')
    ResultadoPEI = apps.get_model('articulacion', 'ResultadoPEI')
    ProductoPEI = apps.get_model('articulacion', 'ProductoPEI')
    ArticulacionPADPEI = apps.get_model('articulacion', 'ArticulacionPADPEI')
    AccionPOA = apps.get_model('articulacion', 'AccionPOA')
    OperacionPOAU = apps.get_model('articulacion', 'OperacionPOAU')
    ActividadPOAU = apps.get_model('articulacion', 'ActividadPOAU')
    TareaPOAU = apps.get_model('articulacion', 'TareaPOAU')

    resultado_pad = ResultadoPAD.objects.create(
        id_cadena='LEGACY-CADENA-01',
        codigo_resultado='LEGACY-RP-01',
        denominacion='Resultado PAD legacy',
        lineamiento_pad='01',
        vigencia_desde=2027,
        vigencia_hasta=2030,
        cod_geografico='031001',
        eta='GAM Sacaba',
    )
    producto_pad = ProductoPAD.objects.create(
        codigo_producto='LEGACY-PP-01',
        denominacion='Producto PAD legacy',
        resultado_pad=resultado_pad,
    )
    resultado_pei = ResultadoPEI.objects.create(
        codigo_resultado='LEGACY-RI-01',
        denominacion='Resultado PEI legacy',
        cod_entidad='1312',
        entidad='GAM Sacaba',
        vigencia_desde=2027,
        vigencia_hasta=2030,
    )
    producto_pei = ProductoPEI.objects.create(
        codigo_producto='LEGACY-PI-01',
        denominacion='Producto PEI legacy',
        resultado_pei=resultado_pei,
    )
    articulacion = ArticulacionPADPEI.objects.create(
        producto_pad=producto_pad,
        producto_pei=producto_pei,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='LEGACY-ACP-01',
        denominacion='Acción POA legacy',
        producto_pei=producto_pei,
        gestion=2027,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='LEGACY-OP-01',
        denominacion='Operación legacy',
        tipo_operacion='Operación',
        accion_poa=accion,
    )
    actividad = ActividadPOAU.objects.create(
        codigo_actividad='LEGACY-ACT-01',
        denominacion='Actividad legacy',
        operacion=operacion,
    )
    tarea = TareaPOAU.objects.create(
        codigo_tarea='LEGACY-TAR-01',
        denominacion='Tarea legacy',
        actividad=actividad,
    )

    return {
        'ResultadoPAD': resultado_pad.pk,
        'ProductoPAD': producto_pad.pk,
        'ResultadoPEI': resultado_pei.pk,
        'ProductoPEI': producto_pei.pk,
        'ArticulacionPADPEI': articulacion.pk,
        'AccionPOA': accion.pk,
        'OperacionPOAU': operacion.pk,
        'ActividadPOAU': actividad.pk,
        'TareaPOAU': tarea.pk,
    }


@pytest.mark.django_db(transaction=True)
def test_migracion_0004_preserva_datos_legacy_y_relaciones():
    executor = MigrationExecutor(connection)
    executor.migrate([MIGRATE_FROM])
    old_apps = executor.loader.project_state([MIGRATE_FROM]).apps

    try:
        ids = _create_legacy_chain(old_apps)

        executor.loader.build_graph()
        executor.migrate([MIGRATE_TO])
        migrated_apps = executor.loader.project_state([MIGRATE_TO]).apps

        for model_name, (legacy_field, legacy_value) in MODEL_LEGACY_FIELDS.items():
            model = migrated_apps.get_model('articulacion', model_name)
            assert model.objects.count() == 1
            row = model.objects.get(pk=ids[model_name])
            assert getattr(row, legacy_field) == legacy_value
            assert row.correlativo is None
            assert row.segmento == ''
            assert row.codigo_fuente == ''
            assert row.codigo_normalizado == ''
            assert row.codigo_completo_articulacion == ''
            assert row.estado_codigo == 'provisional'

        ProductoPAD = migrated_apps.get_model('articulacion', 'ProductoPAD')
        ProductoPEI = migrated_apps.get_model('articulacion', 'ProductoPEI')
        ArticulacionPADPEI = migrated_apps.get_model(
            'articulacion', 'ArticulacionPADPEI',
        )
        AccionPOA = migrated_apps.get_model('articulacion', 'AccionPOA')
        OperacionPOAU = migrated_apps.get_model('articulacion', 'OperacionPOAU')
        ActividadPOAU = migrated_apps.get_model('articulacion', 'ActividadPOAU')
        TareaPOAU = migrated_apps.get_model('articulacion', 'TareaPOAU')

        assert ProductoPAD.objects.get().resultado_pad_id == ids['ResultadoPAD']
        assert ProductoPEI.objects.get().resultado_pei_id == ids['ResultadoPEI']
        assert ArticulacionPADPEI.objects.count() == 1
        link = ArticulacionPADPEI.objects.get(pk=ids['ArticulacionPADPEI'])
        assert link.producto_pad_id == ids['ProductoPAD']
        assert link.producto_pei_id == ids['ProductoPEI']
        assert AccionPOA.objects.get().producto_pei_id == ids['ProductoPEI']
        assert OperacionPOAU.objects.get().accion_poa_id == ids['AccionPOA']
        assert ActividadPOAU.objects.get().operacion_id == ids['OperacionPOAU']
        assert TareaPOAU.objects.get().actividad_id == ids['ActividadPOAU']
    finally:
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_migracion_0005_preserva_filas_sim_y_agrega_relaciones_nullable():
    executor = MigrationExecutor(connection)
    executor.migrate([MIGRATE_TO])
    apps_0004 = executor.loader.project_state([MIGRATE_TO]).apps

    try:
        ids = _create_legacy_chain(apps_0004)
        for model_name, (legacy_field, _) in MODEL_LEGACY_FIELDS.items():
            model = apps_0004.get_model('articulacion', model_name)
            model.objects.filter(pk=ids[model_name]).update(
                **{legacy_field: f'SIM-2027-{model_name.upper()}'},
            )

        executor.loader.build_graph()
        executor.migrate([MIGRATE_TO_0005])
        apps_0005 = executor.loader.project_state([MIGRATE_TO_0005]).apps

        for model_name, (legacy_field, _) in MODEL_LEGACY_FIELDS.items():
            model = apps_0005.get_model('articulacion', model_name)
            row = model.objects.get(pk=ids[model_name])
            assert row.pk == ids[model_name]
            assert getattr(row, legacy_field) == f'SIM-2027-{model_name.upper()}'
            assert row.articulacion_incompleta is True

        ResultadoPAD = apps_0005.get_model('articulacion', 'ResultadoPAD')
        ResultadoPEI = apps_0005.get_model('articulacion', 'ResultadoPEI')
        resultado_pad = ResultadoPAD.objects.get(pk=ids['ResultadoPAD'])
        resultado_pei = ResultadoPEI.objects.get(pk=ids['ResultadoPEI'])
        assert resultado_pad.resultado_sectorial_catalogo_id is None
        assert resultado_pad.entidad_territorial_cgeo_id is None
        assert resultado_pad.lineamiento_pad_catalogo_id is None
        assert resultado_pei.entidad_codificadora_id is None

        ProductoPAD = apps_0005.get_model('articulacion', 'ProductoPAD')
        ProductoPEI = apps_0005.get_model('articulacion', 'ProductoPEI')
        AccionPOA = apps_0005.get_model('articulacion', 'AccionPOA')
        OperacionPOAU = apps_0005.get_model('articulacion', 'OperacionPOAU')
        ActividadPOAU = apps_0005.get_model('articulacion', 'ActividadPOAU')
        TareaPOAU = apps_0005.get_model('articulacion', 'TareaPOAU')
        assert ProductoPAD.objects.get().resultado_pad_id == ids['ResultadoPAD']
        assert ProductoPEI.objects.get().resultado_pei_id == ids['ResultadoPEI']
        assert AccionPOA.objects.get().producto_pei_id == ids['ProductoPEI']
        assert OperacionPOAU.objects.get().accion_poa_id == ids['AccionPOA']
        assert ActividadPOAU.objects.get().operacion_id == ids['OperacionPOAU']
        assert TareaPOAU.objects.get().actividad_id == ids['ActividadPOAU']
    finally:
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
