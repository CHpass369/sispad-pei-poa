"""Tests del management command importar_catalogos_sacaba (GAM Sacaba, gestión 2027)."""
from datetime import date

import pytest
from django.conf import settings
from django.core.management import CommandError
from django.core.management import call_command

from apps.catalogos.models import (
    ClasificadorGeograficoPresupuestario,
    ClasificadorInstitucional,
    FuenteFinanciamiento,
    OrganismoFinanciador,
    VersionClasificador,
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
    tipos_2027 = {
        VersionClasificador.TIPO_INSTITUCIONAL,
        VersionClasificador.TIPO_RUBRO_RECURSO,
        VersionClasificador.TIPO_OBJETO_GASTO,
        VersionClasificador.TIPO_FINALIDAD_FUNCION,
        VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
        VersionClasificador.TIPO_ORGANISMO_FINANCIADOR,
        VersionClasificador.TIPO_SECTOR_ECONOMICO,
        VersionClasificador.TIPO_GEOGRAFICO_PRESUPUESTARIO,
    }
    assert set(VersionClasificador.objects.filter(
        gestion__anio=2027,
    ).values_list('tipo', flat=True)) == tipos_2027
    assert not VersionClasificador.objects.filter(
        gestion__anio=2027, vigente=True,
    ).exists()
    assert FuenteFinanciamiento.objects.filter(gestion__anio=2027).count() == 21
    assert OrganismoFinanciador.objects.filter(gestion__anio=2027).count() == 11
    assert ClasificadorInstitucional.objects.get(
        codigo='1312', gestion__anio=2027,
    ).metadatos_importacion['sigla'] == 'SCB'
    assert ClasificadorGeograficoPresupuestario.objects.get(
        version_clasificador__gestion__anio=2027,
        departamento='3', provincia='5', municipio='1',
    ).codigo_fuente == '3|5|1'
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


def test_version_clasificador_sin_pdf_queda_no_oficial(db):
    _cargar_catalogos()
    version = VersionClasificador.objects.get(
        tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
        gestion__anio=2027,
    )
    assert version.norma == (
        'RM N° 271 de 31/07/2026 - Directrices de Formulación Presupuestaria 2027'
    )
    assert version.fecha_norma == date(2026, 7, 31)
    assert version.clasificacion_fuente == VersionClasificador.FUENTE_INCIERTA
    assert version.vigente is False
    assert version.hash_fuente == ''


def test_ruta_pdf_inexistente_falla_cerrado(db, tmp_path):
    ruta_inexistente = tmp_path / 'ausente' / 'clasificadores-2027.pdf'

    with pytest.raises(CommandError):
        call_command(
            'importar_catalogos_sacaba',
            gestion=2027,
            clasificadores_pdf=str(ruta_inexistente),
        )

    assert not GestionFiscal.objects.filter(anio=2027).exists()


def test_version_clasificador_con_pdf_conserva_proveniencia_oficial(db, tmp_path):
    pdf = tmp_path / 'clasificadores-2027.pdf'
    pdf.write_bytes(b'%PDF-1.7 source-backed test artifact')

    from hashlib import sha256

    call_command(
        'importar_catalogos_sacaba',
        gestion=2027,
        clasificadores_pdf=str(pdf),
    )
    version = VersionClasificador.objects.get(
        tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
        gestion__anio=2027,
    )
    assert VersionClasificador.objects.filter(
        gestion__anio=2027,
        vigente=True,
        clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
    ).count() == 8
    assert version.clasificacion_fuente == VersionClasificador.FUENTE_OFICIAL
    assert version.vigente is True
    assert version.hash_fuente == sha256(pdf.read_bytes()).hexdigest()
    assert version.codigo_fuente == 'CLASIFICADORES-PRESUPUESTARIOS-2027-MEFP'


def test_familias_sin_fuente_completa_quedan_bloqueadas(db, capsys):
    _cargar_catalogos()
    salida = capsys.readouterr().out
    for tipo in (
        VersionClasificador.TIPO_RUBRO_RECURSO,
        VersionClasificador.TIPO_OBJETO_GASTO,
        VersionClasificador.TIPO_FINALIDAD_FUNCION,
        VersionClasificador.TIPO_SECTOR_ECONOMICO,
    ):
        assert f'[BLOQUEADO] {tipo}' in salida


def test_importar_2027_no_modifica_version_2026(db):
    version_2026 = VersionClasificador.objects.create(
        tipo=VersionClasificador.TIPO_INSTITUCIONAL,
        gestion=GestionFiscal.objects.create(anio=2026),
        norma='RM MEFP N.º 249/2025',
        fecha_norma=date(2025, 6, 24),
        codigo_fuente='RM-249-2025',
        procedencia_normativa='Clasificadores Presupuestarios Gestión 2026',
        hash_fuente='a' * 64,
        clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
        vigente=True,
    )

    _cargar_catalogos()
    version_2026.refresh_from_db()

    assert version_2026.vigente is True
    assert version_2026.codigo_fuente == 'RM-249-2025'
    assert VersionClasificador.objects.filter(
        gestion__anio=2026, codigo_fuente='RM-249-2025',
    ).count() == 1


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
