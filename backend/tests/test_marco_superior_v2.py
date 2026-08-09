"""Contratos de la importación del marco superior PGDESA/PDESA (WP-06)."""
from datetime import date

import pytest

from apps.codificacion.migration_v2 import importar_marco_superior
from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    ResultadoSectorial,
    SectorEconomico,
    VersionCatalogoPlan,
)
from apps.core.models import LegacyMigrationMap
from apps.planificacion.models import Plan
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    VersionInstrumento,
)


@pytest.fixture
def plan_pgdesa(db):
    return Plan.objects.create(
        codigo='PGDESA', nombre='PGDESA Cochabamba', tipo='pgdesa',
        gestion_inicio=2021, gestion_fin=2045,
        fecha_vigencia_desde=date(2021, 1, 1),
    )


@pytest.fixture
def catalogo(plan_pgdesa, db):
    vc = VersionCatalogoPlan.objects.create(
        plan=plan_pgdesa, gestion=2027,
        estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        norma_aprobacion='RM 200/2026',
        clasificacion_fuente=VersionCatalogoPlan.FUENTE_OFICIAL,
        procedencia_fuente='Gaceta departamental',
    )
    eje = EjePGDESA.objects.create(
        codigo='04', denominacion='Eje desarrollo', version_catalogo=vc,
    )
    componente = ComponentePDESA.objects.create(
        codigo='02', denominacion='Componente economico',
        version_catalogo=vc, eje=eje,
    )
    sector = SectorEconomico.objects.create(
        codigo='14', denominacion='Sector productivo',
        version_catalogo=vc, componente=componente,
    )
    resultado = ResultadoSectorial.objects.create(
        codigo='01', denominacion='Resultado sectorial',
        version_catalogo=vc, sector=sector,
    )
    return vc


def test_importa_jerarquia_completa(catalogo):
    resumen = importar_marco_superior()
    assert resumen['nodos_creados'] == 4

    instrumento = InstrumentoPlanificacion.objects.get(codigo='PGDESA-2027')
    version = instrumento.versiones.get()
    nodos = {n.codigo: n for n in version.nodos.all()}
    assert set(nodos) == {'04', '04.02', '04.02.14', '04.02.14.01'}

    # Jerarquía correcta
    assert nodos['04.02'].padre.codigo == '04'
    assert nodos['04.02.14'].padre.codigo == '04.02'
    assert nodos['04.02.14.01'].padre.codigo == '04.02.14'

    # Tipos de nodo por nivel
    assert nodos['04'].tipo_nodo.codigo == 'EJE'
    assert nodos['04.02'].tipo_nodo.codigo == 'COMP'
    assert nodos['04.02.14'].tipo_nodo.codigo == 'SECTOR'
    assert nodos['04.02.14.01'].tipo_nodo.codigo == 'RS'


def test_version_queda_aprobada_inmutable(catalogo):
    importar_marco_superior()
    version = InstrumentoPlanificacion.objects.get(
        codigo='PGDESA-2027',
    ).versiones.get()
    assert version.inmutable is True
    assert version.estado == 'aprobado'
    assert version.checksum
    assert version.norma_aprobacion == 'RM 200/2026'
    assert version.verificar_checksum() is True


def test_trazabilidad_en_legacy_map(catalogo):
    importar_marco_superior(lote='pgdesa-2027')
    entradas = LegacyMigrationMap.objects.filter(lote='pgdesa-2027')
    assert entradas.count() == 4
    for modelo in (EjePGDESA, ComponentePDESA, SectorEconomico, ResultadoSectorial):
        entrada = entradas.get(
            app_legacy='codificacion', modelo_legacy=modelo._meta.model_name,
        )
        assert entrada.estado == LegacyMigrationMap.Estados.MIGRADO
        assert entrada.tipo_destino == 'NodoEstrategico'
        assert entrada.uuid_destino is not None


def test_importacion_idempotente(catalogo):
    importar_marco_superior()
    importar_marco_superior()
    assert InstrumentoPlanificacion.objects.count() == 1
    assert VersionInstrumento.objects.count() == 1
    assert NodoEstrategico.objects.count() == 4
    assert LegacyMigrationMap.objects.filter(lote='pgdesa-pdesa').count() == 4


def test_dry_run_no_escribe(catalogo):
    resumen = importar_marco_superior(dry_run=True)
    assert resumen['nodos_creados'] == 4
    assert not InstrumentoPlanificacion.objects.exists()
    assert not NodoEstrategico.objects.exists()
    assert not LegacyMigrationMap.objects.exists()


def test_nueva_gestion_no_sobrescribe_aprobada(catalogo):
    importar_marco_superior()

    # Nueva gestión con el mismo plan: nuevo instrumento, no toca la aprobada
    vc2 = VersionCatalogoPlan.objects.create(
        plan=catalogo.plan, gestion=2028,
        estado=VersionCatalogoPlan.ESTADO_BORRADOR,
        norma_aprobacion='RM 300/2027',
        clasificacion_fuente=VersionCatalogoPlan.FUENTE_OFICIAL,
    )
    EjePGDESA.objects.create(
        codigo='05', denominacion='Eje nuevo', version_catalogo=vc2,
    )
    importar_marco_superior()

    assert InstrumentoPlanificacion.objects.count() == 2
    v1 = InstrumentoPlanificacion.objects.get(codigo='PGDESA-2027').versiones.get()
    v2 = InstrumentoPlanificacion.objects.get(codigo='PGDESA-2028').versiones.get()
    assert v1.inmutable is True
    assert v2.inmutable is True
    assert v1.checksum != v2.checksum


def test_reconciliacion_detecta_modificacion_legacy(catalogo):
    importar_marco_superior(lote='pgdesa-2027')

    eje = EjePGDESA.objects.get(codigo='04')
    eje.denominacion = 'Eje manipulado'
    eje.save(update_fields=['denominacion', 'updated_at'])

    from django.core.management import call_command
    call_command('legacy_audit', '--reconciliar', '--lote', 'pgdesa-2027')
    entrada = LegacyMigrationMap.objects.get(
        app_legacy='codificacion', modelo_legacy='ejepgdesa',
    )
    assert entrada.estado == LegacyMigrationMap.Estados.DISCREPANCIA


def test_reconciliacion_ok_sin_cambios(catalogo):
    importar_marco_superior(lote='pgdesa-2027')
    from django.core.management import call_command
    call_command('legacy_audit', '--reconciliar', '--lote', 'pgdesa-2027')
    assert not LegacyMigrationMap.objects.filter(
        estado=LegacyMigrationMap.Estados.DISCREPANCIA,
    ).exists()
    assert LegacyMigrationMap.objects.filter(
        estado=LegacyMigrationMap.Estados.RECONCILIADO,
    ).count() == 4


def test_gestion_filtrada(catalogo, plan_pgdesa):
    importar_marco_superior(gestion=2028)
    assert not InstrumentoPlanificacion.objects.exists()
