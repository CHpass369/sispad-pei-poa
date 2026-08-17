from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction

from apps.codificacion.models import EntidadTerritorialCGEO
from apps.gestion.models import GestionFiscal


def _gf(anio):
    return GestionFiscal.objects.get_or_create(
        anio=anio, defaults={'estado': 'abierta'},
    )[0]


pytestmark = pytest.mark.django_db


def crear_version(**overrides):
    from apps.catalogos.models import VersionClasificador

    reemplazar_vigente = overrides.pop('_reemplazar_vigente', True)
    data = {
        'tipo': VersionClasificador.TIPO_OBJETO_GASTO,
        'gestion': _gf(2026),
        'norma': 'RM MEFP 249/2025',
        'fecha_norma': date(2025, 6, 24),
        'codigo_fuente': 'RM-249-2025',
        'procedencia_normativa': 'Clasificadores Presupuestarios 2026, PDF pp. 3-4',
        'hash_fuente': '9719fd35d33a4ce0278aef96a5599cb93aa4d9f148d45f57adf81730d5a90ccf',
        'clasificacion_fuente': VersionClasificador.FUENTE_OFICIAL,
        'vigente': True,
    }
    data.update(overrides)
    if data['vigente'] and reemplazar_vigente:
        for version in VersionClasificador.objects.filter(
            tipo=data['tipo'], gestion=data['gestion'] if isinstance(data['gestion'], GestionFiscal) else _gf(data['gestion']), vigente=True
        ):
            version.vigente = False
            version.save(update_fields=['vigente'])
    return VersionClasificador.objects.create(**data)


class TestVersionClasificador:
    def test_resuelve_solo_version_vigente_explicita_por_tipo_y_gestion(self):
        from apps.catalogos.models import VersionClasificador

        vigente = crear_version()
        crear_version(vigente=False, norma='RM anterior', codigo_fuente='RM-ANTERIOR')

        assert (
            VersionClasificador.objects.vigente_para(
                VersionClasificador.TIPO_OBJETO_GASTO,
                2026,
            )
            == vigente
        )
        with pytest.raises(VersionClasificador.DoesNotExist):
            VersionClasificador.objects.vigente_para(
                VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
                2099,
            )

    def test_rechaza_vigente_sin_fuente_oficial_completa(self):
        from apps.catalogos.models import VersionClasificador

        version = VersionClasificador(
            tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
            gestion=_gf(2026),
            vigente=True,
            clasificacion_fuente=VersionClasificador.FUENTE_INCIERTA,
        )

        with pytest.raises(ValidationError) as error:
            version.full_clean()

        assert {'norma', 'codigo_fuente', 'procedencia_normativa', 'hash_fuente', 'clasificacion_fuente'} <= set(
            error.value.message_dict
        )

    def test_impide_dos_versiones_vigentes_del_mismo_tipo_y_gestion(self):
        from apps.catalogos.models import VersionClasificador

        crear_version()

        with pytest.raises(IntegrityError), transaction.atomic():
            crear_version(
                norma='Otra norma',
                codigo_fuente='OTRA-NORMA',
                _reemplazar_vigente=False,
            )

        assert VersionClasificador.objects.filter(
            tipo=VersionClasificador.TIPO_OBJETO_GASTO,
            gestion=_gf(2026),
            vigente=True,
        ).count() == 1

    def test_create_rechaza_fuente_oficial_no_vigente_con_hash_invalido(self):
        from apps.catalogos.models import VersionClasificador

        with pytest.raises(ValidationError) as error:
            VersionClasificador.objects.create(
                tipo=VersionClasificador.TIPO_OBJETO_GASTO,
                gestion=_gf(2030),
                norma='RM válida',
                fecha_norma=date(2029, 1, 1),
                codigo_fuente='RM-VALIDA',
                procedencia_normativa='Documento oficial',
                hash_fuente='A' * 64,
                clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
                vigente=False,
            )

        assert 'hash_fuente' in error.value.message_dict

    @pytest.mark.parametrize('campo', ['norma', 'codigo_fuente', 'procedencia_normativa'])
    def test_create_rechaza_trazabilidad_oficial_vacia_o_en_blanco(self, campo):
        from apps.catalogos.models import VersionClasificador

        data = {
            'tipo': VersionClasificador.TIPO_OBJETO_GASTO,
            'gestion': _gf(2030),
            'norma': 'RM válida',
            'fecha_norma': date(2029, 1, 1),
            'codigo_fuente': 'RM-VALIDA',
            'procedencia_normativa': 'Documento oficial',
            'hash_fuente': 'a' * 64,
            'clasificacion_fuente': VersionClasificador.FUENTE_OFICIAL,
            'vigente': False,
        }
        data[campo] = '   '

        with pytest.raises(ValidationError) as error:
            VersionClasificador.objects.create(**data)

        assert campo in error.value.message_dict

    def test_bulk_create_rechaza_version_oficial_semanticamente_invalida(self):
        from apps.catalogos.models import VersionClasificador

        invalida = VersionClasificador(
            tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
            gestion=_gf(2030),
            norma='RM válida',
            fecha_norma=date(2029, 1, 1),
            codigo_fuente='RM-VALIDA',
            procedencia_normativa='Documento oficial',
            hash_fuente='A' * 64,
            clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
            vigente=False,
        )

        with pytest.raises(ValidationError):
            VersionClasificador.objects.bulk_create([invalida])

    def test_queryset_update_bloquea_campos_semanticos(self):
        from apps.catalogos.models import VersionClasificador

        version = crear_version(gestion=_gf(2030), _reemplazar_vigente=False)

        with pytest.raises(ValidationError):
            VersionClasificador.objects.filter(pk=version.pk).update(hash_fuente='A' * 64)

        version.refresh_from_db()
        assert version.hash_fuente.startswith('9719')

    def test_constraint_sql_rechaza_hash_que_no_es_sha256_minusculo_exacto(self):
        version = crear_version(gestion=_gf(2030), _reemplazar_vigente=False)

        with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                'UPDATE catalogo_version_clasificador SET hash_fuente = %s WHERE id = %s',
                ['A' * 64, str(version.pk)],
            )


class TestCatalogosVersionados:
    def test_vincula_catalogos_legacy_sin_perder_codigo_fuente_ni_procedencia(self):
        from apps.catalogos.models import FuenteFinanciamiento, ObjetoGasto, OrganismoFinanciador

        objeto_version = crear_version()
        fuente_version = crear_version(
            tipo=objeto_version.TIPO_FUENTE_FINANCIAMIENTO,
            codigo_fuente='RM-249-FUENTES',
        )
        organismo_version = crear_version(
            tipo=objeto_version.TIPO_ORGANISMO_FINANCIADOR,
            codigo_fuente='RM-249-ORGANISMOS',
        )
        vigencia = {'fecha_vigencia_desde': date(2026, 1, 1), 'gestion': _gf(2026)}
        objeto = ObjetoGasto.objects.create(
            codigo='11210',
            denominacion='Gastos especializados',
            fuente_normativa='Clasificadores 2026, PDF p. 51',
            version_clasificador=objeto_version,
            nivel=ObjetoGasto.NIVEL_DETALLE,
            **vigencia,
        )
        fuente = FuenteFinanciamiento.objects.create(
            codigo='20',
            denominacion='Recursos específicos',
            fuente_normativa='Clasificadores 2026, PDF pp. 135-136',
            version_clasificador=fuente_version,
            **vigencia,
        )
        organismo = OrganismoFinanciador.objects.create(
            codigo='210',
            denominacion='Recursos específicos GAM/GAIOC',
            fuente_normativa='Clasificadores 2026, PDF pp. 143-144',
            version_clasificador=organismo_version,
            **vigencia,
        )

        assert (objeto.codigo, fuente.codigo, organismo.codigo) == ('11210', '20', '210')
        assert objeto.fuente_normativa.endswith('p. 51')
        assert fuente.version_clasificador.codigo_fuente == 'RM-249-FUENTES'
        assert organismo.version_clasificador.codigo_fuente == 'RM-249-ORGANISMOS'

    def test_conserva_filas_legacy_sin_version_y_soporta_jerarquia_de_objetos(self):
        from apps.catalogos.models import ObjetoGasto

        vigencia = {'fecha_vigencia_desde': date(2025, 1, 1), 'gestion': _gf(2025)}
        legacy = ObjetoGasto.objects.create(codigo='LEGACY', denominacion='Dato previo', **vigencia)
        version = crear_version()
        grupo = ObjetoGasto.objects.create(
            codigo='10000',
            denominacion='Servicios no personales',
            version_clasificador=version,
            nivel=ObjetoGasto.NIVEL_GRUPO,
            fecha_vigencia_desde=date(2026, 1, 1),
            gestion=_gf(2026),
        )
        detalle = ObjetoGasto.objects.create(
            codigo='11210',
            denominacion='Detalle',
            version_clasificador=version,
            nivel=ObjetoGasto.NIVEL_DETALLE,
            padre=grupo,
            fecha_vigencia_desde=date(2026, 1, 1),
            gestion=_gf(2026),
        )

        assert legacy.version_clasificador is None
        assert detalle.padre == grupo

    def test_rechaza_tipo_de_version_incorrecto_y_anchos_no_oficiales(self):
        from apps.catalogos.models import FuenteFinanciamiento, VersionClasificador

        version_objeto = crear_version()
        fuente_tipo_incorrecto = FuenteFinanciamiento(
            codigo='20',
            denominacion='Fuente con versión incorrecta',
            gestion=_gf(2026),
            fecha_vigencia_desde=date(2026, 1, 1),
            version_clasificador=version_objeto,
        )
        version_fuente = crear_version(
            tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
            codigo_fuente='RM-249-FUENTES',
        )
        fuente_ancho_incorrecto = FuenteFinanciamiento(
            codigo='200',
            denominacion='Fuente con ancho incorrecto',
            gestion=_gf(2026),
            fecha_vigencia_desde=date(2026, 1, 1),
            version_clasificador=version_fuente,
        )

        with pytest.raises(ValidationError) as tipo_error:
            fuente_tipo_incorrecto.save()
        with pytest.raises(ValidationError) as codigo_error:
            fuente_ancho_incorrecto.save()

        assert 'version_clasificador' in tipo_error.value.message_dict
        assert 'codigo' in codigo_error.value.message_dict

    @pytest.mark.parametrize(
        'modelo,codigo',
        [
            ('ObjetoGasto', '11210'),
            ('FuenteFinanciamiento', '20'),
            ('OrganismoFinanciador', '210'),
        ],
    )
    def test_bulk_create_rechaza_version_de_tipo_incorrecto(self, modelo, codigo):
        from apps import catalogos
        from apps.catalogos.models import VersionClasificador

        model = getattr(catalogos.models, modelo)
        version_incorrecta = VersionClasificador.objects.get(
            tipo=VersionClasificador.TIPO_CATEGORIA_PROGRAMATICA,
            gestion=_gf(2026),
        )
        invalido = model(
            codigo=codigo,
            denominacion='Clasificador inválido',
            gestion=_gf(2026),
            fecha_vigencia_desde=date(2026, 1, 1),
            version_clasificador=version_incorrecta,
        )

        with pytest.raises(ValidationError):
            model.objects.bulk_create([invalido])

    @pytest.mark.parametrize(
        'modelo,codigo,tipo',
        [
            ('ObjetoGasto', '11210', 'objeto_gasto'),
            ('FuenteFinanciamiento', '20', 'fuente_financiamiento'),
            ('OrganismoFinanciador', '210', 'organismo_financiador'),
        ],
    )
    def test_queryset_update_rechaza_cambiar_asociacion_versionada(self, modelo, codigo, tipo):
        from apps import catalogos
        from apps.catalogos.models import VersionClasificador

        model = getattr(catalogos.models, modelo)
        version = crear_version(tipo=tipo, gestion=_gf(2030), _reemplazar_vigente=False)
        row = model.objects.create(
            codigo=codigo,
            denominacion='Clasificador válido',
            gestion=_gf(2030),
            fecha_vigencia_desde=date(2030, 1, 1),
            version_clasificador=version,
        )
        version_incorrecta = VersionClasificador.objects.get(
            tipo=VersionClasificador.TIPO_CATEGORIA_PROGRAMATICA,
            gestion=_gf(2026),
        )

        with pytest.raises(ValidationError):
            model.objects.filter(pk=row.pk).update(
                version_clasificador=version_incorrecta,
            )

    def test_objeto_padre_debe_compartir_version_y_gestion_en_save_y_bulk(self):
        from apps.catalogos.models import ObjetoGasto

        version_2026 = crear_version(gestion=_gf(2030), _reemplazar_vigente=False)
        version_2027 = crear_version(gestion=_gf(2031), _reemplazar_vigente=False)
        padre = ObjetoGasto.objects.create(
            codigo='10000',
            denominacion='Grupo 2030',
            gestion=_gf(2030),
            fecha_vigencia_desde=date(2030, 1, 1),
            version_clasificador=version_2026,
            nivel=ObjetoGasto.NIVEL_GRUPO,
        )
        hijo = ObjetoGasto(
            codigo='11210',
            denominacion='Detalle 2031',
            gestion=_gf(2031),
            fecha_vigencia_desde=date(2031, 1, 1),
            version_clasificador=version_2027,
            nivel=ObjetoGasto.NIVEL_DETALLE,
            padre=padre,
        )

        with pytest.raises(ValidationError) as save_error:
            hijo.save()
        with pytest.raises(ValidationError):
            ObjetoGasto.objects.bulk_create([hijo])

        assert 'padre' in save_error.value.message_dict


class TestGeografiaPresupuestaria:
    def test_mefp_geo_es_un_catalogo_distinto_de_cgeo_ine(self):
        from apps.catalogos.models import ClasificadorGeograficoPresupuestario, VersionClasificador

        version = crear_version(
            tipo=VersionClasificador.TIPO_GEOGRAFICO_PRESUPUESTARIO,
            codigo_fuente='RM-249-GEO',
        )
        cgeo_ine = EntidadTerritorialCGEO.objects.get(codigo='031001')
        mefp_geo = ClasificadorGeograficoPresupuestario.objects.create(
            version_clasificador=version,
            departamento='3',
            provincia='5',
            municipio='1',
            codigo_fuente='3|5|1',
            denominacion='Sacaba',
            procedencia_normativa='Clasificadores 2026, PDF pp. 155, 159',
        )

        assert cgeo_ine.codigo == '031001'
        assert mefp_geo.codigo_compuesto == '3.5.1'
        assert not hasattr(mefp_geo, 'entidad_territorial_cgeo')
