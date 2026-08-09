"""Contratos de la migración del PAD al kernel V2 (WP-07)."""
from datetime import date

import pytest

from apps.core.models import LegacyMigrationMap
from apps.pad.migration_v2 import (
    comparar_duplicados_pad,
    importar_articulaciones_sipeb,
    importar_pad,
)
from apps.pad.models import (
    ArticulacionSIPEB,
    LineamientoEstrategico,
    PoliticaPAD,
    ProductoTerritorial,
    ResultadoTerritorial,
    SectorPAD,
)
from apps.planificacion.models import Plan
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    VersionInstrumento,
    VinculoEstrategico,
)
from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    VersionCatalogoPlan,
)


@pytest.fixture
def pad_legacy(db):
    politica = PoliticaPAD.objects.create(
        codigo='P1', nombre='Política 1', gestion=2027,
    )
    lineamiento = LineamientoEstrategico.objects.create(
        codigo='L1', nombre='Lineamiento 1', politica=politica, gestion=2027,
    )
    resultado = ResultadoTerritorial.objects.create(
        codigo='R1', nombre='Resultado 1', lineamiento=lineamiento,
        gestion=2027, indicador='Tasa', linea_base=10, meta_2030=50,
    )
    producto = ProductoTerritorial.objects.create(
        codigo='PR1', nombre='Producto 1', resultado=resultado,
        gestion=2027, presupuesto_total_pad=100000,
    )
    return {
        'politica': politica, 'lineamiento': lineamiento,
        'resultado': resultado, 'producto': producto,
    }


@pytest.fixture
def marco_superior(db):
    """Marco superior importado (prerequisito WP-06 para vínculos)."""
    plan = Plan.objects.create(
        codigo='PGDESA', nombre='PGDESA', tipo='pgdesa',
        gestion_inicio=2021, gestion_fin=2045,
        fecha_vigencia_desde=date(2021, 1, 1),
    )
    vc = VersionCatalogoPlan.objects.create(
        plan=plan, gestion=2027,
        estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        clasificacion_fuente=VersionCatalogoPlan.FUENTE_OFICIAL,
    )
    eje = EjePGDESA.objects.create(
        codigo='04', denominacion='Eje', version_catalogo=vc,
    )
    ComponentePDESA.objects.create(
        codigo='02', denominacion='Componente', version_catalogo=vc, eje=eje,
    )
    from apps.codificacion.migration_v2 import importar_marco_superior
    importar_marco_superior(lote='pgdesa-test')
    return InstrumentoPlanificacion.objects.get(codigo='PGDESA-2027')


def test_importa_jerarquia_pad(pad_legacy):
    resumen = importar_pad()
    assert resumen['nodos_creados'] == 4

    instrumento = InstrumentoPlanificacion.objects.get(codigo='PAD-2027')
    version = instrumento.versiones.get()
    nodos = {n.codigo: n for n in version.nodos.all()}
    assert set(nodos) == {'P1', 'P1.L1', 'P1.L1.R1', 'P1.L1.R1.PR1'}

    # Jerarquía y tipos
    assert nodos['P1.L1'].padre.codigo == 'P1'
    assert nodos['P1.L1.R1'].padre.codigo == 'P1.L1'
    assert nodos['P1.L1.R1.PR1'].padre.codigo == 'P1.L1.R1'
    assert nodos['P1.L1.R1'].tipo_nodo.codigo == 'RESULTADO'
    assert nodos['P1.L1.R1.PR1'].tipo_nodo.codigo == 'PRODUCTO'

    # Atributos legacy preservados
    atributos = nodos['P1.L1.R1'].atributos
    assert atributos['indicador'] == 'Tasa'
    assert float(atributos['linea_base']) == 10
    assert float(
        nodos['P1.L1.R1.PR1'].atributos['presupuesto_total_pad'],
    ) == 100000


def test_version_pad_aprobada_inmutable(pad_legacy):
    importar_pad()
    version = InstrumentoPlanificacion.objects.get(
        codigo='PAD-2027',
    ).versiones.get()
    assert version.inmutable is True
    assert version.estado == 'aprobado'
    assert version.checksum
    assert version.verificar_checksum() is True


def test_trazabilidad_legacy_map(pad_legacy):
    importar_pad(lote='pad-2027')
    assert LegacyMigrationMap.objects.filter(lote='pad-2027').count() == 4
    entrada = LegacyMigrationMap.objects.get(
        app_legacy='pad', modelo_legacy='resultadoterritorial',
    )
    assert entrada.estado == LegacyMigrationMap.Estados.MIGRADO
    assert entrada.tipo_destino == 'NodoEstrategico'


def test_importacion_idempotente(pad_legacy):
    importar_pad()
    importar_pad()
    assert InstrumentoPlanificacion.objects.filter(codigo='PAD-2027').count() == 1
    assert NodoEstrategico.objects.count() == 4


def test_dry_run_no_escribe(pad_legacy):
    resumen = importar_pad(dry_run=True)
    assert resumen['nodos_creados'] == 4
    assert not InstrumentoPlanificacion.objects.exists()
    assert not LegacyMigrationMap.objects.exists()


def test_vinculos_sipeb(pad_legacy, marco_superior):
    sip = ArticulacionSIPEB.objects.create(
        resultado=pad_legacy['resultado'],
        cod_eje_pgdesa='04',
        cod_componente_pdesa='02',
        cod_ods='ODS-11',
        gestion=2027,
    )
    resumen = importar_pad(lote='pad-2027', con_vinculos=True)
    assert resumen['vinculos_sipeb'] == 2
    assert resumen['vinculos_pendientes'] == 0

    version = InstrumentoPlanificacion.objects.get(codigo='PAD-2027').versiones.get()
    vinculos = version.vinculos.all()
    assert vinculos.count() == 2
    tipos = {v.tipo.codigo for v in vinculos}
    assert tipos == {'ARTICULA-EJE', 'ARTICULA-COMP'}

    # Los vínculos quedan dentro de la versión aprobada e inmutable
    assert version.inmutable is True
    assert version.verificar_checksum() is True

    # Compromisos internacionales preservados en la justificación
    vinculo = vinculos.get(tipo__codigo='ARTICULA-EJE')
    assert 'ODS: ODS-11' in vinculo.justificacion

    # Trazabilidad
    assert LegacyMigrationMap.objects.filter(lote='pad-2027-sipeb').count() == 1


def test_vinculos_sipeb_posteriores_crean_version_nueva(pad_legacy, marco_superior):
    """Si el PAD ya fue aprobado sin vínculos, los SIPEB se registran en
    una versión nueva (la aprobada permanece inmutable)."""
    importar_pad(lote='pad-2027', con_vinculos=False)
    ArticulacionSIPEB.objects.create(
        resultado=pad_legacy['resultado'],
        cod_eje_pgdesa='04',
        gestion=2027,
    )
    resumen = importar_articulaciones_sipeb()
    assert resumen['version_creada'] is True
    assert resumen['vinculos_creados'] == 1

    instrumento = InstrumentoPlanificacion.objects.get(codigo='PAD-2027')
    v1 = instrumento.versiones.get(numero=1)
    v2 = instrumento.versiones.get(numero=2)
    assert v1.inmutable is True
    assert v1.vinculos.count() == 0
    assert v2.vinculos.count() == 1
    assert v2.etiqueta == 'Articulación SIPEB'


def test_vinculos_sin_marco_no_crean_nada(pad_legacy):
    ArticulacionSIPEB.objects.create(
        resultado=pad_legacy['resultado'],
        cod_eje_pgdesa='04',
        gestion=2027,
    )
    resumen = importar_pad(lote='pad-2027', con_vinculos=True)
    assert resumen['vinculos_sipeb'] == 0
    assert resumen['vinculos_pendientes'] == 1
    assert VinculoEstrategico.objects.count() == 0


def test_comparar_duplicados_reporta(pad_legacy):
    from apps.articulacion.models import (
        LineamientoPAD as LineamientoPADArt,
        ProductoPAD as ProductoPADArt,
        ResultadoPAD as ResultadoPADArt,
    )
    LineamientoPADArt.objects.create(
        codigo='L1', denominacion='Lineamiento 1',
        gestion_desde=2027, gestion_hasta=2031,
    )
    ResultadoPADArt.objects.create(
        codigo_resultado='R1', denominacion='Resultado 1',
        lineamiento_pad='L1', vigencia_desde=2027, vigencia_hasta=2031,
    )
    ProductoPADArt.objects.create(
        codigo_producto='PR1', denominacion='Producto 1',
        resultado_pad=ResultadoPADArt.objects.get(codigo_resultado='R1'),
    )
    reporte = comparar_duplicados_pad()
    assert reporte['lineamientos']['pad'] == 1
    assert reporte['lineamientos']['articulacion'] == 1
    assert reporte['lineamientos']['coinciden_codigo_y_nombre'] == 1
    assert reporte['resultados']['coinciden_codigo_y_nombre'] == 1
    assert reporte['productos']['coinciden_codigo_y_nombre'] == 1
