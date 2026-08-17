"""Tests del management command importar_catalogos_sacaba (GAM Sacaba, gestión 2027)."""
import re
from datetime import date

import pytest
from django.conf import settings
from django.core.management import call_command

from apps.catalogos.models import (
    VersionClasificador, FuenteFinanciamiento, OrganismoFinanciador,
)
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import (
    DireccionAdministrativa, UnidadEjecutora, UnidadOrganizacional,
)

# apps.territorio (PostGIS) no está instalado en settings_test_sqlite y su
# módulo no puede importarse ahí; los distritos se verifican solo cuando
# el app está disponible (config.settings con PostgreSQL/PostGIS).
TIENE_TERRITORIO = 'apps.territorio' in settings.INSTALLED_APPS
if TIENE_TERRITORIO:
    from apps.territorio.models import Distrito


def _cargar_catalogos():
    call_command('importar_catalogos_sacaba', gestion=2027)


def test_command_carga_catalogos_completos(db):
    _cargar_catalogos()
    _cargar_catalogos()  # segunda ejecución: no debe duplicar

    assert GestionFiscal.objects.filter(anio=2027).count() == 1
    assert VersionClasificador.objects.filter(
        gestion__anio=2027, vigente=True,
        clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
    ).count() == 2
    for tipo in (
        VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
        VersionClasificador.TIPO_ORGANISMO_FINANCIADOR,
    ):
        assert VersionClasificador.objects.filter(
            tipo=tipo, gestion__anio=2027, vigente=True,
        ).count() == 1
    assert FuenteFinanciamiento.objects.filter(gestion__anio=2027).count() == 21
    assert OrganismoFinanciador.objects.filter(gestion__anio=2027).count() == 11
    assert DireccionAdministrativa.objects.filter(gestion__anio=2027).count() == 5
    assert UnidadEjecutora.objects.filter(gestion__anio=2027).count() == 11
    assert UnidadOrganizacional.objects.filter(
        gestion__anio=2027, tipo__codigo='SEC',
    ).count() >= 8
    if TIENE_TERRITORIO:
        assert Distrito.objects.count() == 12


@pytest.mark.skipif(
    not TIENE_TERRITORIO,
    reason='apps.territorio no está en settings_test_sqlite (requiere PostGIS)',
)
def test_distritos_cargados(db):
    _cargar_catalogos()
    assert Distrito.objects.count() == 12
    assert Distrito.objects.filter(codigo='DLL').first().nombre == 'DISTRITO LAVA LAVA'


def test_version_clasificador_oficial_tiene_norma(db):
    _cargar_catalogos()
    version = VersionClasificador.objects.get(
        tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
        gestion__anio=2027, vigente=True,
    )
    assert version.norma == (
        'RM N° 271 de 31/07/2026 - Directrices de Formulación Presupuestaria 2027'
    )
    assert version.fecha_norma == date(2026, 7, 31)
    assert version.clasificacion_fuente == VersionClasificador.FUENTE_OFICIAL
    assert version.vigente is True
    assert re.fullmatch(r'[0-9a-f]{64}', version.hash_fuente)


def test_fuentes_y_organismos_versionados(db):
    _cargar_catalogos()
    fuente = FuenteFinanciamiento.objects.get(codigo='41', gestion__anio=2027)
    assert fuente.version_clasificador is not None
    assert fuente.version_clasificador.tipo == (
        VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO
    )
    assert fuente.version_clasificador.gestion.anio == 2027
    assert fuente.fecha_vigencia_desde == date(2027, 1, 1)

    organismo = OrganismoFinanciador.objects.get(codigo='113', gestion__anio=2027)
    assert organismo.version_clasificador is not None
    assert organismo.version_clasificador.tipo == (
        VersionClasificador.TIPO_ORGANISMO_FINANCIADOR
    )
    assert organismo.version_clasificador.gestion.anio == 2027
    assert organismo.fecha_vigencia_desde == date(2027, 1, 1)


def test_ues_apuntan_a_da_correcta(db):
    _cargar_catalogos()
    ue_6 = UnidadEjecutora.objects.get(codigo='6', gestion__anio=2027)
    assert ue_6.da.codigo == '3'
    assert ue_6.da.nombre == 'ADMINISTRACION CONCEJO MUNICIPAL'
    assert ue_6.nombre == 'CONCEJO MUNICIPAL'

    ue_2 = UnidadEjecutora.objects.get(codigo='2', gestion__anio=2027)
    assert ue_2.da.codigo == '2'
    assert ue_2.da.nombre == 'HOSPITAL DE SEGUNDO NIVEL MEXICO'
