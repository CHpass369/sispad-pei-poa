"""Strict-TDD contracts for the controlled SIM-2027 migration."""
import datetime
import json
import os

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    ArticulacionPADPEI,
    LineamientoPAD as LineamientoPADLegacy,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    TareaPOAU,
)
from apps.codificacion.models import (
    EjecucionMigracionSIM,
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    HomologacionCodigo,
    LineamientoPAD,
    MapeoLineamientoPADLegacy,
    VersionCatalogoPlan,
)
from apps.codificacion.services.migracion_sim import MigracionSIMService
from apps.codificacion.services.postgres_backup import PostgresBackupService
from apps.pad.models import LineamientoEstrategico, PoliticaPAD
from apps.planificacion.models import Plan


@pytest.fixture
def usuario_migracion(db):
    return get_user_model().objects.create_user(
        email='migracion-sim@test.gob.bo', password='test123',
    )


@pytest.fixture
def cadena_sim(db):
    resultado_pad = ResultadoPAD.objects.create(
        id_cadena='SIM-CADENA-01',
        codigo_resultado='SIM-2027-PAD-RT-01',
        denominacion='Resultado PAD preservado',
        lineamiento_pad='SIM-2027-LL-01',
        vigencia_desde=2027,
        vigencia_hasta=2030,
        cod_geografico='SIM-2027-CGEO',
        eta='GAM Sacaba',
    )
    producto_pad = ProductoPAD.objects.create(
        codigo_producto='SIM-2027-PAD-PT-01',
        denominacion='Producto PAD preservado',
        resultado_pad=resultado_pad,
    )
    resultado_pei = ResultadoPEI.objects.create(
        codigo_resultado='SIM-2027-PEI-RI-01',
        denominacion='Resultado PEI preservado',
        cod_entidad='SIM-2027',
        entidad='GAM Sacaba',
        cod_oei='SIM-2027',
        vigencia_desde=2027,
        vigencia_hasta=2030,
    )
    producto_pei = ProductoPEI.objects.create(
        codigo_producto='SIM-2027-PEI-PI-01',
        denominacion='Producto PEI preservado',
        resultado_pei=resultado_pei,
    )
    enlace = ArticulacionPADPEI.objects.create(
        producto_pad=producto_pad,
        producto_pei=producto_pei,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='SIM-2027-POA-01',
        denominacion='Acción preservada',
        producto_pei=producto_pei,
        gestion=2027,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='SIM-2027-OPE-01',
        denominacion='Operación preservada',
        tipo_operacion='Operación',
        accion_poa=accion,
    )
    actividad_1 = ActividadPOAU.objects.create(
        codigo_actividad='SIM-2027-ACT-01',
        denominacion='Actividad uno preservada',
        operacion=operacion,
    )
    actividad_2 = ActividadPOAU.objects.create(
        codigo_actividad='SIM-2027-ACT-02',
        denominacion='Actividad dos preservada',
        operacion=operacion,
    )
    tareas = [
        TareaPOAU.objects.create(
            codigo_tarea='SIM-2027-TAR-01-01',
            denominacion='Tarea uno preservada',
            actividad=actividad_1,
        ),
        TareaPOAU.objects.create(
            codigo_tarea='SIM-2027-TAR-01-02',
            denominacion='Tarea dos preservada',
            actividad=actividad_1,
        ),
        TareaPOAU.objects.create(
            codigo_tarea='SIM-2027-TAR-02-01',
            denominacion='Tarea tres preservada',
            actividad=actividad_2,
        ),
    ]
    return {
        'resultado_pad': resultado_pad,
        'producto_pad': producto_pad,
        'resultado_pei': resultado_pei,
        'producto_pei': producto_pei,
        'enlace': enlace,
        'accion': accion,
        'operacion': operacion,
        'actividades': [actividad_1, actividad_2],
        'tareas': tareas,
    }


@pytest.mark.django_db
def test_dry_run_es_persistente_determinista_y_no_modifica_objetivos(cadena_sim):
    service = MigracionSIMService(gestion=2027)

    primero = service.auditar()
    segundo = service.auditar()

    assert primero['manifest_hash'] == segundo['manifest_hash']
    assert primero['resumen']['cambios_planificados'] == 11
    assert primero['resumen']['por_nivel'] == {
        'resultado_pad': 1,
        'producto_pad': 1,
        'resultado_pei': 1,
        'producto_pei': 1,
        'accion_poa': 1,
        'operacion_poau': 1,
        'actividad_poau': 2,
        'tarea_poau': 3,
    }
    assert EjecucionMigracionSIM.objects.filter(modo='dry_run').count() == 2
    assert HomologacionCodigo.objects.count() == 0
    cadena_sim['accion'].refresh_from_db()
    assert cadena_sim['accion'].codigo_accion == 'SIM-2027-POA-01'
    assert cadena_sim['accion'].correlativo is None


@pytest.mark.django_db
def test_snapshot_y_validacion_restore_incluyen_tablas_pad_canonicas(cadena_sim):
    counts = MigracionSIMService.snapshot_counts()

    assert counts['articulacion_resultadopad'] == 1
    assert counts['articulacion_productopad'] == 1
    assert set(counts).issubset(PostgresBackupService.SAFE_TABLES)


@pytest.mark.django_db
def test_commit_migra_ocho_niveles_y_segunda_ejecucion_es_noop(
    cadena_sim, usuario_migracion,
):
    ids = {
        nombre: objeto.pk
        for nombre, objeto in cadena_sim.items()
        if nombre not in {'actividades', 'tareas'}
    }
    manifest = MigracionSIMService(gestion=2027).construir_manifiesto()
    service = MigracionSIMService(gestion=2027, usuario=usuario_migracion)

    primera = service.ejecutar(
        expected_hash=manifest['manifest_hash'],
        backup={
            'path': '/backups/t5/pre-commit.dump',
            'sha256': 'a' * 64,
            'restore_validated': True,
        },
    )
    segunda = service.ejecutar(
        expected_hash=manifest['manifest_hash'],
        backup={
            'path': '/backups/t5/pre-second-run.dump',
            'sha256': 'b' * 64,
            'restore_validated': True,
        },
    )

    assert primera['cambios_aplicados'] == 11
    assert primera['homologaciones_creadas'] == 11
    assert segunda['cambios_aplicados'] == 0
    assert segunda['homologaciones_creadas'] == 0
    assert HomologacionCodigo.objects.count() == 11

    resultado_pei = ResultadoPEI.objects.get(pk=ids['resultado_pei'])
    producto_pei = ProductoPEI.objects.get(pk=ids['producto_pei'])
    accion = AccionPOA.objects.get(pk=ids['accion'])
    operacion = OperacionPOAU.objects.get(pk=ids['operacion'])
    actividades = list(ActividadPOAU.objects.order_by('codigo_actividad'))
    tareas = list(TareaPOAU.objects.order_by('codigo_tarea'))

    assert resultado_pei.codigo_resultado == '1312.01'
    assert producto_pei.codigo_producto == '1312.01.01'
    assert accion.codigo_accion == '2027.1312.001'
    assert operacion.codigo_operacion == '2027.1312.001.001'
    assert [item.codigo_actividad for item in actividades] == [
        '2027.1312.001.001.001',
        '2027.1312.001.001.002',
    ]
    assert [item.codigo_tarea for item in tareas] == [
        '2027.1312.001.001.001.001',
        '2027.1312.001.001.001.002',
        '2027.1312.001.001.002.001',
    ]
    assert resultado_pei.codigo_fuente == 'SIM-2027-PEI-RI-01'
    assert resultado_pei.cod_entidad == '1312'
    assert resultado_pei.cod_oei == ''
    assert resultado_pei.entidad_codificadora.codigo == '1312'

    for model in (
        ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
        AccionPOA, OperacionPOAU, ActividadPOAU, TareaPOAU,
    ):
        for row in model.objects.all():
            assert row.estado_codigo == 'provisional'
            assert row.articulacion_incompleta is True
            assert row.correlativo > 0
            assert row.segmento == row.codigo_normalizado
            assert int(row.segmento) > 0

    assert ArticulacionPADPEI.objects.get(pk=ids['enlace']).producto_pei_id == ids[
        'producto_pei'
    ]
    assert accion.denominacion == 'Acción preservada'
    assert operacion.accion_poa_id == ids['accion']


@pytest.mark.django_db
def test_commit_rechaza_hash_obsoleto_o_backup_no_restaurado(
    cadena_sim, usuario_migracion,
):
    service = MigracionSIMService(gestion=2027, usuario=usuario_migracion)

    with pytest.raises(ValidationError, match='hash'):
        service.ejecutar(
            expected_hash='0' * 64,
            backup={
                'path': '/backups/t5/pre-commit.dump',
                'sha256': 'a' * 64,
                'restore_validated': True,
            },
        )
    with pytest.raises(ValidationError, match='restaur'):
        service.ejecutar(
            expected_hash=service.construir_manifiesto()['manifest_hash'],
            backup={
                'path': '/backups/t5/pre-commit.dump',
                'sha256': 'a' * 64,
                'restore_validated': False,
            },
        )

    assert HomologacionCodigo.objects.count() == 0
    assert AccionPOA.objects.get().codigo_accion == 'SIM-2027-POA-01'


@pytest.mark.django_db
def test_lineamientos_solo_se_mapean_con_correspondencia_inequivoca():
    cgeo = EntidadTerritorialCGEO.objects.get(codigo='031001')

    def version(codigo_plan):
        plan = Plan.objects.create(
            codigo=codigo_plan,
            nombre=codigo_plan,
            tipo='municipal',
            gestion_inicio=2026,
            gestion_fin=2030,
            fecha_vigencia_desde=datetime.date(2026, 1, 1),
        )
        return VersionCatalogoPlan.objects.create(
            plan=plan,
            gestion=2027,
            estado=VersionCatalogoPlan.ESTADO_BORRADOR,
            clasificacion_fuente=VersionCatalogoPlan.FUENTE_INCIERTA,
        )

    version_unica = version('PAD-SIM-UNICO')
    canonico = LineamientoPAD.objects.create(
        codigo='01',
        denominacion='Desarrollo institucional',
        version_catalogo=version_unica,
        entidad_territorial=cgeo,
    )
    legacy_unico = LineamientoPADLegacy.objects.create(
        codigo='01',
        denominacion=' Desarrollo institucional ',
        gestion_desde=2026,
        gestion_hasta=2030,
    )

    version_ambigua_1 = version('PAD-SIM-AMB-1')
    version_ambigua_2 = version('PAD-SIM-AMB-2')
    for catalogo in (version_ambigua_1, version_ambigua_2):
        LineamientoPAD.objects.create(
            codigo='02',
            denominacion='Gestión territorial',
            version_catalogo=catalogo,
            entidad_territorial=cgeo,
        )
    politica = PoliticaPAD.objects.create(
        codigo='P-01', nombre='Política', gestion=2027,
    )
    legacy_ambiguo = LineamientoEstrategico.objects.create(
        codigo='02',
        nombre='Gestión territorial',
        politica=politica,
        gestion=2027,
    )

    manifest = MigracionSIMService(gestion=2027).construir_manifiesto()

    assert manifest['lineamientos']['mapeables'] == 1
    assert manifest['lineamientos']['ambiguos'] == 1
    assert manifest['lineamientos']['sin_correspondencia'] == 0
    assert manifest['lineamientos']['entradas'][0]['legacy_id'] == str(
        legacy_unico.pk
    )
    assert manifest['lineamientos']['entradas'][0]['canonico_id'] == str(
        canonico.pk
    )
    assert manifest['lineamientos']['entradas'][1]['legacy_id'] == str(
        legacy_ambiguo.pk
    )
    assert manifest['lineamientos']['entradas'][1]['canonico_id'] is None

    resultado = MigracionSIMService(gestion=2027).consolidar_lineamientos()

    assert resultado == {'mapeos_creados': 1, 'mapeos_existentes': 0}
    mapeo = MapeoLineamientoPADLegacy.objects.get()
    assert mapeo.origen == 'articulacion.LineamientoPAD'
    assert mapeo.legacy_id == str(legacy_unico.pk)
    assert mapeo.lineamiento_pad_id == canonico.pk
    assert LineamientoPADLegacy.objects.filter(pk=legacy_unico.pk).exists()
    assert LineamientoEstrategico.objects.filter(pk=legacy_ambiguo.pk).exists()


@pytest.mark.django_db
def test_lineamiento_pad_origen_pk_entero_se_mapea_y_consolida():
    """pad.LineamientoEstrategico (pk entero) se mapea sin ValidationError."""
    cgeo = EntidadTerritorialCGEO.objects.get(codigo='031001')
    plan = Plan.objects.create(
        codigo='PAD-SIM-PK-ENTERO',
        nombre='PAD-SIM-PK-ENTERO',
        tipo='municipal',
        gestion_inicio=2026,
        gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )
    version_catalogo = VersionCatalogoPlan.objects.create(
        plan=plan,
        gestion=2027,
        estado=VersionCatalogoPlan.ESTADO_BORRADOR,
        clasificacion_fuente=VersionCatalogoPlan.FUENTE_INCIERTA,
    )
    canonico = LineamientoPAD.objects.create(
        codigo='01',
        denominacion='Desarrollo institucional',
        version_catalogo=version_catalogo,
        entidad_territorial=cgeo,
    )
    politica = PoliticaPAD.objects.create(
        codigo='P-01', nombre='Política', gestion=2027,
    )
    legacy = LineamientoEstrategico.objects.create(
        codigo='01',
        nombre='Desarrollo institucional',
        politica=politica,
        gestion=2027,
    )
    assert isinstance(legacy.pk, int)

    manifest = MigracionSIMService(gestion=2027).construir_manifiesto()

    assert manifest['lineamientos']['mapeables'] == 1
    assert manifest['lineamientos']['ambiguos'] == 0
    assert manifest['lineamientos']['sin_correspondencia'] == 0
    entrada = manifest['lineamientos']['entradas'][0]
    assert entrada['origen'] == MapeoLineamientoPADLegacy.ORIGEN_PAD
    assert entrada['legacy_id'] == str(legacy.pk)
    assert entrada['canonico_id'] == str(canonico.pk)

    resultado = MigracionSIMService(gestion=2027).consolidar_lineamientos()

    assert resultado == {'mapeos_creados': 1, 'mapeos_existentes': 0}
    mapeo = MapeoLineamientoPADLegacy.objects.get()
    assert mapeo.origen == MapeoLineamientoPADLegacy.ORIGEN_PAD
    assert mapeo.legacy_id == str(legacy.pk)
    assert mapeo.lineamiento_pad_id == canonico.pk
    assert LineamientoEstrategico.objects.filter(pk=legacy.pk).exists()


def test_manifiesto_json_es_canonico_y_verificable(tmp_path, cadena_sim):
    service = MigracionSIMService(gestion=2027)
    manifest = service.construir_manifiesto()
    path = tmp_path / 'manifest.json'

    service.persistir_manifiesto(manifest, path)

    persisted = json.loads(path.read_text(encoding='utf-8'))
    assert persisted == manifest
    # El permiso 0600 es un invariante POSIX del manifiesto (auditoría);
    # en Windows el bitmask POSIX no aplica (siempre 0666), se omite.
    if os.name != 'nt':
        assert path.stat().st_mode & 0o777 == 0o600
    assert service.verificar_hash(persisted) is True
