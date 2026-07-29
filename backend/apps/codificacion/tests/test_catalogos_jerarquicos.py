"""Tests de la cadena EjePGDESA -> ComponentePDESA -> SectorEconomico
-> ResultadoSectorial (T1.3)."""
import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    ResultadoSectorial,
    SectorEconomico,
    VersionCatalogoPlan,
)
from apps.planificacion.models import Plan


@pytest.fixture
def version_catalogo(db):
    plan = Plan.objects.create(
        codigo='PGDESA-JER', nombre='PGDESA', tipo='pgdesa',
        gestion_inicio=2026, gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )
    return VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)


@pytest.fixture
def cadena(version_catalogo):
    """Cadena completa 04 -> 02 -> 14 -> 01 (ejemplo del diseño)."""
    eje = EjePGDESA.objects.create(
        codigo='04', denominacion='Eje de prueba',
        version_catalogo=version_catalogo,
    )
    componente = ComponentePDESA.objects.create(
        codigo='02', denominacion='Componente de prueba',
        eje=eje, version_catalogo=version_catalogo,
    )
    sector = SectorEconomico.objects.create(
        codigo='14', denominacion='Sector de prueba',
        componente=componente, version_catalogo=version_catalogo,
    )
    resultado = ResultadoSectorial.objects.create(
        codigo='01', denominacion='Resultado de prueba',
        sector=sector, version_catalogo=version_catalogo,
    )
    return eje, componente, sector, resultado


@pytest.mark.django_db
class TestCodigoSegmento:
    """El código de cada nivel es de exactamente 2 dígitos."""

    @pytest.mark.parametrize('modelo,codigo_valido', [
        (EjePGDESA, '00'),
        (EjePGDESA, '04'),
        (EjePGDESA, '99'),
    ])
    def test_codigo_dos_digitos_valido(self, version_catalogo, modelo, codigo_valido):
        instancia = modelo(
            codigo=codigo_valido, denominacion='X',
            version_catalogo=version_catalogo,
        )
        instancia.full_clean()

    @pytest.mark.parametrize('codigo_invalido', ['', '1', '123', 'AB', '0A', ' 4'])
    def test_codigo_invalido_rechazado(self, version_catalogo, codigo_invalido):
        eje = EjePGDESA(
            codigo=codigo_invalido, denominacion='X',
            version_catalogo=version_catalogo,
        )
        with pytest.raises(ValidationError):
            eje.full_clean()

    def test_activo_por_defecto(self, version_catalogo):
        eje = EjePGDESA.objects.create(
            codigo='01', denominacion='Eje', version_catalogo=version_catalogo,
        )
        assert eje.activo is True

    def test_str_incluye_codigo_y_denominacion(self, version_catalogo):
        eje = EjePGDESA(
            codigo='04', denominacion='Desarrollo económico',
            version_catalogo=version_catalogo,
        )
        assert str(eje) == '[04] Desarrollo económico'


@pytest.mark.django_db
class TestJerarquia:
    def test_cadena_completa(self, cadena):
        eje, componente, sector, resultado = cadena
        assert componente.eje == eje
        assert sector.componente == componente
        assert resultado.sector == sector
        assert sector.componente.eje.codigo == '04'
        assert resultado.sector.componente.codigo == '02'

    def test_componente_requiere_eje(self, version_catalogo):
        with pytest.raises(IntegrityError):
            ComponentePDESA.objects.create(
                codigo='01', denominacion='Huérfano', eje=None,
                version_catalogo=version_catalogo,
            )

    def test_sector_requiere_componente(self, version_catalogo):
        with pytest.raises(IntegrityError):
            SectorEconomico.objects.create(
                codigo='01', denominacion='Huérfano', componente=None,
                version_catalogo=version_catalogo,
            )

    def test_resultado_requiere_sector(self, version_catalogo):
        with pytest.raises(IntegrityError):
            ResultadoSectorial.objects.create(
                codigo='01', denominacion='Huérfano', sector=None,
                version_catalogo=version_catalogo,
            )


@pytest.mark.django_db
class TestUnicidad:
    def test_eje_unique_codigo_version(self, version_catalogo):
        EjePGDESA.objects.create(
            codigo='01', denominacion='A', version_catalogo=version_catalogo,
        )
        with pytest.raises(IntegrityError):
            EjePGDESA.objects.create(
                codigo='01', denominacion='B', version_catalogo=version_catalogo,
            )

    def test_mismo_codigo_en_otra_version_es_valido(self, version_catalogo, db):
        EjePGDESA.objects.create(
            codigo='01', denominacion='A', version_catalogo=version_catalogo,
        )
        otra_version = VersionCatalogoPlan.objects.create(
            plan=version_catalogo.plan, gestion=2027,
        )
        eje = EjePGDESA.objects.create(
            codigo='01', denominacion='B', version_catalogo=otra_version,
        )
        assert eje.pk is not None

    def test_componente_unique_padre_codigo_version(self, cadena):
        eje, _, _, _ = cadena
        version = eje.version_catalogo
        with pytest.raises(IntegrityError):
            ComponentePDESA.objects.create(
                codigo='02', denominacion='Duplicado', eje=eje,
                version_catalogo=version,
            )

    def test_mismo_codigo_en_padre_distinto_es_valido(self, cadena):
        eje, _, _, _ = cadena
        version = eje.version_catalogo
        otro_eje = EjePGDESA.objects.create(
            codigo='05', denominacion='Otro eje', version_catalogo=version,
        )
        componente = ComponentePDESA.objects.create(
            codigo='02', denominacion='Mismo código, otro padre',
            eje=otro_eje, version_catalogo=version,
        )
        assert componente.pk is not None

    def test_sector_unique_padre_codigo_version(self, cadena):
        _, componente, _, _ = cadena
        with pytest.raises(IntegrityError):
            SectorEconomico.objects.create(
                codigo='14', denominacion='Duplicado', componente=componente,
                version_catalogo=componente.version_catalogo,
            )

    def test_resultado_unique_padre_codigo_version(self, cadena):
        _, _, sector, _ = cadena
        with pytest.raises(IntegrityError):
            ResultadoSectorial.objects.create(
                codigo='01', denominacion='Duplicado', sector=sector,
                version_catalogo=sector.version_catalogo,
            )
