"""Tests de EntidadTerritorialCGEO, EntidadCodificadora y LineamientoPAD (T1.4)."""
import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.codificacion.models import (
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    LineamientoPAD,
    VersionCatalogoPlan,
)
from apps.planificacion.models import Plan


@pytest.fixture
def version_pad(db):
    plan = Plan.objects.create(
        codigo='PAD-TEST', nombre='PAD', tipo='municipal',
        gestion_inicio=2026, gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )
    return VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)


@pytest.fixture
def sacaba(db):
    """Usa el seed del data migration: Sacaba 031001."""
    return EntidadTerritorialCGEO.objects.get(codigo='031001')


@pytest.mark.django_db
class TestEntidadTerritorialCGEO:
    def test_codigo_seis_digitos_valido(self):
        cgeo = EntidadTerritorialCGEO(
            codigo='030101', nombre='Municipio de prueba', nivel='municipio',
        )
        cgeo.full_clean()

    @pytest.mark.parametrize('codigo_invalido', ['', '1', '03100', '0310010', 'ABCDEF', '03100A'])
    def test_codigo_invalido_rechazado(self, codigo_invalido):
        cgeo = EntidadTerritorialCGEO(
            codigo=codigo_invalido, nombre='X', nivel='municipio',
        )
        with pytest.raises(ValidationError):
            cgeo.full_clean()

    def test_codigo_unico(self, sacaba):
        with pytest.raises(IntegrityError):
            EntidadTerritorialCGEO.objects.create(
                codigo='031001', nombre='Duplicado', nivel='municipio',
            )

    def test_jerarquia_padre_nullable(self, sacaba):
        """La jerarquía interna es para filtrar: padre puede ser NULL
        (raíz) y debe enlazar municipio -> provincia -> departamento."""
        assert sacaba.padre is not None
        assert sacaba.padre.codigo == '0310'
        assert sacaba.padre.padre.codigo == '03'
        assert sacaba.padre.padre.padre is None

    def test_nivel_choices(self, sacaba):
        assert sacaba.nivel == 'municipio'
        assert sacaba.padre.nivel == 'provincia'
        assert sacaba.padre.padre.nivel == 'departamento'

    def test_str(self, sacaba):
        assert '031001' in str(sacaba)
        assert 'Sacaba' in str(sacaba)


@pytest.mark.django_db
class TestSeedCGEO:
    """El data migration carga Cochabamba / Chapare / Sacaba como PROVISIONAL."""

    def test_seed_cochabamba(self, db):
        cbba = EntidadTerritorialCGEO.objects.get(codigo='03')
        assert cbba.nivel == 'departamento'
        assert cbba.estado == EntidadTerritorialCGEO.ESTADO_PROVISIONAL

    def test_seed_chapare(self, db):
        chapare = EntidadTerritorialCGEO.objects.get(codigo='0310')
        assert chapare.nivel == 'provincia'
        assert chapare.padre.codigo == '03'

    def test_seed_sacaba_provisional(self, db):
        sacaba = EntidadTerritorialCGEO.objects.get(codigo='031001')
        assert sacaba.nombre == 'Sacaba'
        assert sacaba.estado == EntidadTerritorialCGEO.ESTADO_PROVISIONAL

    def test_seed_es_idempotente(self, db):
        """Solo existen los 3 registros del seed (no duplicados)."""
        assert EntidadTerritorialCGEO.objects.count() == 3


@pytest.mark.django_db
class TestEntidadCodificadora:
    def test_seed_1312_gam_sacaba(self, db):
        """La única entidad codificadora inicial es 1312 GAM Sacaba."""
        entidad = EntidadCodificadora.objects.get(codigo='1312')
        assert 'Sacaba' in entidad.denominacion
        assert entidad.activo is True
        assert EntidadCodificadora.objects.count() == 1

    def test_codigo_cuatro_digitos_valido(self):
        entidad = EntidadCodificadora(codigo='2301', denominacion='Otra')
        entidad.full_clean()

    @pytest.mark.parametrize('codigo_invalido', ['', '131', '13121', 'ABCD', '13A2'])
    def test_codigo_invalido_rechazado(self, codigo_invalido):
        entidad = EntidadCodificadora(codigo=codigo_invalido, denominacion='X')
        with pytest.raises(ValidationError):
            entidad.full_clean()

    def test_codigo_unico(self, db):
        with pytest.raises(IntegrityError):
            EntidadCodificadora.objects.create(
                codigo='1312', denominacion='Duplicado',
            )

    def test_str(self, db):
        entidad = EntidadCodificadora.objects.get(codigo='1312')
        assert str(entidad).startswith('[1312]')


@pytest.mark.django_db
class TestLineamientoPAD:
    def test_crear_lineamiento(self, version_pad, sacaba):
        lineamiento = LineamientoPAD.objects.create(
            codigo='02',
            denominacion='Lineamiento de prueba',
            entidad_territorial=sacaba,
            version_catalogo=version_pad,
        )
        assert lineamiento.activo is True
        assert lineamiento.entidad_territorial.codigo == '031001'

    def test_codigo_dos_digitos(self, version_pad, sacaba):
        lineamiento = LineamientoPAD(
            codigo='2', denominacion='X',
            entidad_territorial=sacaba, version_catalogo=version_pad,
        )
        with pytest.raises(ValidationError):
            lineamiento.full_clean()

    def test_unique_territorio_codigo_version(self, version_pad, sacaba):
        LineamientoPAD.objects.create(
            codigo='02', denominacion='A',
            entidad_territorial=sacaba, version_catalogo=version_pad,
        )
        with pytest.raises(IntegrityError):
            LineamientoPAD.objects.create(
                codigo='02', denominacion='B',
                entidad_territorial=sacaba, version_catalogo=version_pad,
            )

    def test_mismo_codigo_en_otra_version_es_valido(self, version_pad, sacaba):
        LineamientoPAD.objects.create(
            codigo='02', denominacion='A',
            entidad_territorial=sacaba, version_catalogo=version_pad,
        )
        otra_version = VersionCatalogoPlan.objects.create(
            plan=version_pad.plan, gestion=2027,
        )
        lineamiento = LineamientoPAD.objects.create(
            codigo='02', denominacion='B',
            entidad_territorial=sacaba, version_catalogo=otra_version,
        )
        assert lineamiento.pk is not None

    def test_requiere_entidad_territorial(self, version_pad):
        with pytest.raises(IntegrityError):
            LineamientoPAD.objects.create(
                codigo='02', denominacion='Huérfano',
                entidad_territorial=None, version_catalogo=version_pad,
            )
