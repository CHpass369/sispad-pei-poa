"""Tests de EntidadTerritorialCGEO, EntidadCodificadora y LineamientoPAD (T1.4)."""
import importlib

import pytest
from django.apps import apps as global_apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    LineamientoPAD,
    VersionCatalogoPlan,
    validador_cgeo_departamento,
    validador_cgeo_municipio,
    validador_cgeo_provincia,
    validador_codigo_4_digitos,
)


@pytest.fixture
def sacaba(db):
    """Usa el seed del data migration: Sacaba 031001."""
    return EntidadTerritorialCGEO.objects.get(codigo='031001')


class TestValidadoresAncho:
    """Validators de ancho importables: CGEO por nivel y entidad (S3)."""

    @pytest.mark.parametrize('validador,codigo', [
        (validador_cgeo_departamento, '03'),
        (validador_cgeo_provincia, '0310'),
        (validador_cgeo_municipio, '031001'),
        (validador_codigo_4_digitos, '1312'),
    ])
    def test_codigo_valido_no_levanta_error(self, validador, codigo):
        validador(codigo)

    @pytest.mark.parametrize('validador,codigo', [
        (validador_cgeo_departamento, '3'),
        (validador_cgeo_departamento, '0310'),
        (validador_cgeo_provincia, '03'),
        (validador_cgeo_provincia, '031001'),
        (validador_cgeo_municipio, '0310'),
        (validador_cgeo_municipio, '0310010'),
        (validador_cgeo_municipio, '03100A'),
        (validador_codigo_4_digitos, '131'),
        (validador_codigo_4_digitos, '13121'),
        (validador_codigo_4_digitos, '13A2'),
    ])
    def test_codigo_invalido_rechazado(self, validador, codigo):
        with pytest.raises(ValidationError):
            validador(codigo)


@pytest.mark.django_db
class TestEntidadTerritorialCGEO:
    @pytest.mark.parametrize('nivel,codigo', [
        ('departamento', '05'),
        ('provincia', '0501'),
        ('municipio', '050101'),
    ])
    def test_codigo_acorde_al_nivel_valido(self, nivel, codigo):
        """El ancho del código INE depende del nivel: 2/4/6 dígitos."""
        cgeo = EntidadTerritorialCGEO(codigo=codigo, nombre='X', nivel=nivel)
        cgeo.full_clean()

    @pytest.mark.parametrize('codigo_invalido', ['', '1', '03100', '0310010', 'ABCDEF', '03100A'])
    def test_codigo_formato_invalido_rechazado(self, codigo_invalido):
        cgeo = EntidadTerritorialCGEO(
            codigo=codigo_invalido, nombre='X', nivel='municipio',
        )
        with pytest.raises(ValidationError):
            cgeo.full_clean()

    @pytest.mark.parametrize('nivel,codigo', [
        ('departamento', '050101'),
        ('departamento', '0501'),
        ('provincia', '05'),
        ('provincia', '050101'),
        ('municipio', '05'),
        ('municipio', '0501'),
    ])
    def test_codigo_no_corresponde_al_nivel_rechazado(self, nivel, codigo):
        """Un código con ancho de otro nivel falla en el campo codigo."""
        cgeo = EntidadTerritorialCGEO(codigo=codigo, nombre='X', nivel=nivel)
        with pytest.raises(ValidationError) as excinfo:
            cgeo.full_clean()
        assert 'codigo' in excinfo.value.message_dict

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
        """Re-ejecutar la lógica real del seed no duplica ni altera registros."""
        seed_modulo = importlib.import_module(
            'apps.codificacion.migrations.0004_seed_cgeo_y_entidad',
        )
        assert EntidadTerritorialCGEO.objects.count() == 3
        assert EntidadCodificadora.objects.count() == 1

        seed_modulo.seed_catalogos(global_apps, None)
        seed_modulo.seed_catalogos(global_apps, None)

        assert EntidadTerritorialCGEO.objects.count() == 3
        assert EntidadCodificadora.objects.count() == 1
        sacaba = EntidadTerritorialCGEO.objects.get(codigo='031001')
        assert sacaba.padre.codigo == '0310'
        assert sacaba.padre.padre.codigo == '03'

    @pytest.mark.parametrize('codigo,nivel', [
        ('03', 'departamento'),
        ('0310', 'provincia'),
        ('031001', 'municipio'),
    ])
    def test_registros_seeded_pasan_full_clean(self, db, codigo, nivel):
        """Los códigos INE reales del seed (2/4/6 dígitos) pasan full_clean."""
        entidad = EntidadTerritorialCGEO.objects.get(codigo=codigo, nivel=nivel)
        entidad.full_clean()

    def test_entidad_codificadora_seeded_pasa_full_clean(self, db):
        EntidadCodificadora.objects.get(codigo='1312').full_clean()


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
        # El constraint de unicidad aplica por (entidad, componente, codigo, version):
        # sin componente las filas no chocan; con el mismo componente sí.
        LineamientoPAD.objects.create(
            codigo='02', denominacion='A',
            entidad_territorial=sacaba, version_catalogo=version_pad,
        )
        # Sin componente: permitido (componente nullable).
        LineamientoPAD.objects.create(
            codigo='02', denominacion='B',
            entidad_territorial=sacaba, version_catalogo=version_pad,
        )
        # Con el mismo componente: colisión.
        eje = EjePGDESA.objects.create(
            codigo='01', denominacion='Eje test', version_catalogo=version_pad,
        )
        componente = ComponentePDESA.objects.create(
            codigo='01', denominacion='Componente test',
            version_catalogo=version_pad, eje=eje,
        )
        LineamientoPAD.objects.create(
            codigo='02', denominacion='C',
            entidad_territorial=sacaba, version_catalogo=version_pad,
            componente=componente,
        )
        with pytest.raises(IntegrityError):
            LineamientoPAD.objects.create(
                codigo='02', denominacion='D',
                entidad_territorial=sacaba, version_catalogo=version_pad,
                componente=componente,
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

    def test_related_name_lineamientos_pad_en_version(self, version_pad, sacaba):
        """La versión expone el plural explícito lineamientos_pad (S1)."""
        lineamiento = LineamientoPAD.objects.create(
            codigo='02', denominacion='A',
            entidad_territorial=sacaba, version_catalogo=version_pad,
        )
        assert list(version_pad.lineamientos_pad.all()) == [lineamiento]
