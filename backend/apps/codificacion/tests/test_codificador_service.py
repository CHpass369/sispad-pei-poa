"""Strict-TDD contract tests for the institutional coding service (T3)."""
import datetime
import threading
import uuid
from queue import Queue

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    ArticulacionPADPEI,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    TareaPOAU,
)
from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    HomologacionCodigo,
    LineamientoPAD,
    ResultadoSectorial,
    SecuenciaCodigo,
    SectorEconomico,
    VersionCatalogoPlan,
)
from apps.codificacion.services.codificador import CodificadorService
from apps.planificacion.models import Plan


@pytest.fixture
def entidad_1312(db):
    return EntidadCodificadora.objects.get(codigo='1312')


@pytest.fixture
def usuario_codificador(db):
    return get_user_model().objects.create_user(
        email='servicio-codificador@test.gob.bo', password='test123',
    )


@pytest.fixture
def cadena_codificable(db, entidad_1312):
    def plan(codigo, tipo):
        return Plan.objects.create(
            codigo=codigo,
            nombre=codigo,
            tipo=tipo,
            gestion_inicio=2026,
            gestion_fin=2030,
            fecha_vigencia_desde=datetime.date(2026, 1, 1),
        )

    nacional = VersionCatalogoPlan.objects.create(
        plan=plan('PGDESA-COD', 'pgdesa'),
        gestion=2027,
        estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        norma_aprobacion='Norma institucional de prueba',
    )
    pad = VersionCatalogoPlan.objects.create(
        plan=plan('PAD-COD', 'municipal'),
        gestion=2027,
        estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        norma_aprobacion='Norma municipal de prueba',
    )
    eje = EjePGDESA.objects.create(
        codigo='04', denominacion='Eje', version_catalogo=nacional,
    )
    componente = ComponentePDESA.objects.create(
        codigo='02', denominacion='Componente', eje=eje,
        version_catalogo=nacional,
    )
    sector = SectorEconomico.objects.create(
        codigo='14', denominacion='Sector', componente=componente,
        version_catalogo=nacional,
    )
    resultado_sectorial = ResultadoSectorial.objects.create(
        codigo='01', denominacion='Resultado sectorial', sector=sector,
        version_catalogo=nacional,
    )
    cgeo = EntidadTerritorialCGEO.objects.get(codigo='031001')
    cgeo.estado = EntidadTerritorialCGEO.ESTADO_OFICIAL
    cgeo.save(update_fields=['estado', 'updated_at'])
    lineamiento = LineamientoPAD.objects.create(
        codigo='02', denominacion='Lineamiento', entidad_territorial=cgeo,
        version_catalogo=pad,
    )
    resultado_pad = ResultadoPAD.objects.create(
        id_cadena='COD-RP', codigo_resultado='COD-RP', denominacion='RP',
        lineamiento_pad='02', vigencia_desde=2027, vigencia_hasta=2030,
        cod_geografico='031001', eta='GAM Sacaba', correlativo=1,
        segmento='01', resultado_sectorial_catalogo=resultado_sectorial,
        entidad_territorial_cgeo=cgeo, lineamiento_pad_catalogo=lineamiento,
    )
    producto_pad = ProductoPAD.objects.create(
        codigo_producto='COD-PP', denominacion='PP', resultado_pad=resultado_pad,
        correlativo=1, segmento='01',
    )
    resultado_pei = ResultadoPEI.objects.create(
        codigo_resultado='COD-RI', denominacion='RI', cod_entidad='1312',
        entidad='GAM Sacaba', cod_oei='03', vigencia_desde=2027,
        vigencia_hasta=2030, correlativo=1, segmento='01',
        entidad_codificadora=entidad_1312,
    )
    producto_pei = ProductoPEI.objects.create(
        codigo_producto='COD-PI', denominacion='PI', resultado_pei=resultado_pei,
        correlativo=1, segmento='01',
    )
    ArticulacionPADPEI.objects.create(
        producto_pad=producto_pad, producto_pei=producto_pei,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='COD-ACP', denominacion='ACP', producto_pei=producto_pei,
        gestion=2027, correlativo=1, segmento='001',
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='COD-OP', denominacion='OP', tipo_operacion='Operación',
        accion_poa=accion, correlativo=1, segmento='001',
    )
    actividad = ActividadPOAU.objects.create(
        codigo_actividad='COD-ACT', denominacion='ACT', operacion=operacion,
        correlativo=1, segmento='001',
    )
    tarea = TareaPOAU.objects.create(
        codigo_tarea='COD-TAR', denominacion='TAR', actividad=actividad,
        correlativo=1, segmento='001',
    )
    return {
        'resultado_pad': resultado_pad,
        'accion': accion,
        'operacion': operacion,
        'actividad': actividad,
        'tarea': tarea,
    }


@pytest.mark.django_db
class TestSiguienteCorrelativo:
    def test_incrementa_la_misma_clave(self, entidad_1312):
        padre_id = uuid.uuid4()

        primero = CodificadorService.siguiente_correlativo(
            'operacion_poau', padre_id, 2027, entidad_1312,
        )
        segundo = CodificadorService.siguiente_correlativo(
            'operacion_poau', padre_id, 2027, entidad_1312,
        )

        assert (primero, segundo) == (1, 2)
        assert SecuenciaCodigo.objects.get(
            nivel='operacion_poau', padre_id=padre_id,
            gestion=2027, entidad=entidad_1312,
        ).ultimo_valor == 2

    def test_reinicia_por_padre(self, entidad_1312):
        valores = [
            CodificadorService.siguiente_correlativo(
                'actividad_poau', uuid.uuid4(), 2027, entidad_1312,
            )
            for _ in range(2)
        ]

        assert valores == [1, 1]

    def test_reinicia_por_gestion(self, entidad_1312):
        padre_id = uuid.uuid4()

        valores = [
            CodificadorService.siguiente_correlativo(
                'actividad_poau', padre_id, gestion, entidad_1312,
            )
            for gestion in (2027, 2027, 2028)
        ]

        assert valores == [1, 2, 1]

    def test_rechaza_nivel_y_entidad_fuera_del_dominio(self, db, entidad_1312):
        otra_entidad = EntidadCodificadora.objects.create(
            codigo='9999', denominacion='Entidad no habilitada',
        )

        with pytest.raises(ValidationError):
            CodificadorService.siguiente_correlativo(
                'nivel_inexistente', None, 2027, entidad_1312,
            )
        with pytest.raises(ValidationError):
            CodificadorService.siguiente_correlativo(
                'resultado_pad', None, 2027, otra_entidad,
            )


@pytest.mark.django_db(transaction=True)
def test_carrera_inicial_crea_una_secuencia_sin_duplicar():
    entidad_id = EntidadCodificadora.objects.get(codigo='1312').pk
    padre_id = uuid.uuid4()
    inicio = threading.Barrier(3)
    resultados = Queue()
    errores = Queue()

    def emitir():
        try:
            entidad = EntidadCodificadora.objects.get(pk=entidad_id)
            inicio.wait(timeout=5)
            resultados.put(CodificadorService.siguiente_correlativo(
                'tarea_poau', padre_id, 2027, entidad,
            ))
        except BaseException as exc:
            errores.put(exc)
        finally:
            connection.close()

    hilos = [threading.Thread(target=emitir) for _ in range(2)]
    for hilo in hilos:
        hilo.start()
    inicio.wait(timeout=5)
    for hilo in hilos:
        hilo.join(timeout=10)

    assert all(not hilo.is_alive() for hilo in hilos)
    assert errores.empty(), list(errores.queue)
    assert sorted([resultados.get_nowait(), resultados.get_nowait()]) == [1, 2]
    assert SecuenciaCodigo.objects.filter(
        nivel='tarea_poau', padre_id=padre_id,
        gestion=2027, entidad_id=entidad_id,
        ultimo_valor=2,
    ).count() == 1


class TestNormalizar:
    @pytest.mark.parametrize('nivel,valor,esperado', [
        ('EE', ' 4 ', '04'),
        ('CGEO', '031001', '031001'),
        ('ENTI', 1312, '1312'),
        ('ACP', '7', '007'),
        ('TAR', 139, '139'),
    ])
    def test_strip_y_zfill_por_ancho(self, nivel, valor, esperado):
        assert CodificadorService.normalizar(nivel, valor) == esperado

    @pytest.mark.parametrize('nivel,valor', [
        ('EE', 'ABC'),
        ('OE', '123'),
        ('CGEO', ''),
        ('DESCONOCIDO', '1'),
    ])
    def test_rechaza_valores_no_numericos_o_fuera_de_ancho(self, nivel, valor):
        with pytest.raises(ValidationError):
            CodificadorService.normalizar(nivel, valor)


class TestValidarFormato:
    @pytest.mark.parametrize('indice', range(16))
    def test_rechaza_ancho_invalido_en_cada_segmento(self, indice):
        segmentos = [
            '04', '02', '14', '01', '031001', '02', '01', '01',
            '1312', '03', '01', '01', '001', '001', '001', '001',
        ]
        segmentos[indice] += '9'

        with pytest.raises(ValidationError):
            CodificadorService.validar_codigo('.'.join(segmentos))

    @pytest.mark.parametrize('codigo', [
        '04.02',
        'AA.02.14.01.031001.02.01.01.1312.03.01.01.001.001.001.001',
    ])
    def test_rechaza_cantidad_o_contenido_no_numerico(self, codigo):
        with pytest.raises(ValidationError):
            CodificadorService.validar_codigo(codigo)

    def test_oficial_rechaza_cualquier_segmento_cero(self):
        codigo = (
            '04.02.14.01.031001.02.01.01.'
            '1312.03.01.01.001.001.000.001'
        )

        with pytest.raises(ValidationError):
            CodificadorService.validar_codigo(codigo, para_oficial=True)


@pytest.mark.django_db
class TestGeneracionCodigos:
    def test_genera_los_16_segmentos_del_ejemplo(self, cadena_codificable):
        codigo = CodificadorService.generar_codigo_completo(
            cadena_codificable['tarea'],
        )

        assert codigo == (
            '04.02.14.01.031001.02.01.01.'
            '1312.03.01.01.001.001.001.001'
        )
        assert cadena_codificable['tarea'].articulacion_incompleta is False

    def test_fk_null_omite_segmentos_y_marca_incompleta(self, cadena_codificable):
        resultado_pad = cadena_codificable['resultado_pad']
        resultado_pad.resultado_sectorial_catalogo = None
        resultado_pad.save(update_fields=['resultado_sectorial_catalogo'])

        codigo = CodificadorService.generar_codigo_completo(
            cadena_codificable['tarea'],
        )

        assert codigo == (
            '031001.02.01.01.1312.03.01.01.001.001.001.001'
        )
        assert cadena_codificable['tarea'].articulacion_incompleta is True

    def test_normaliza_todos_los_segmentos_al_generar(self, cadena_codificable):
        resultado_pei = cadena_codificable['accion'].producto_pei.resultado_pei
        resultado_pei.cod_oei = '3'
        resultado_pei.segmento = '1'
        cadena_codificable['accion'].segmento = '1'

        codigo = CodificadorService.generar_codigo_completo(
            cadena_codificable['tarea'],
        )

        assert codigo.split('.')[9:13] == ['03', '01', '01', '001']

    @pytest.mark.parametrize('nivel,esperado', [
        ('accion', '2027.1312.001'),
        ('operacion', '2027.1312.001.001'),
        ('actividad', '2027.1312.001.001.001'),
        ('tarea', '2027.1312.001.001.001.001'),
    ])
    def test_codigo_operativo_por_nivel(self, cadena_codificable, nivel, esperado):
        assert CodificadorService.generar_codigo_operativo(
            cadena_codificable[nivel],
        ) == esperado


@pytest.mark.django_db
class TestValidacionesDeDominio:
    def test_cadena_completa_vigente_es_valida(self, cadena_codificable):
        assert CodificadorService.validar(cadena_codificable['tarea']) is True

    def test_rechaza_catalogo_no_vigente(self, cadena_codificable):
        resultado = cadena_codificable['resultado_pad'].resultado_sectorial_catalogo
        version = resultado.version_catalogo
        version.estado = VersionCatalogoPlan.ESTADO_CERRADO
        version.save(update_fields=['estado', 'updated_at'])

        with pytest.raises(ValidationError):
            CodificadorService.validar(cadena_codificable['tarea'])

    def test_rechaza_jerarquia_que_mezcla_versiones(self, cadena_codificable):
        otro_plan = Plan.objects.create(
            codigo='PGDESA-OTRO', nombre='Otro PGDESA', tipo='pgdesa',
            gestion_inicio=2027, gestion_fin=2030,
            fecha_vigencia_desde=datetime.date(2027, 1, 1),
        )
        otra_version = VersionCatalogoPlan.objects.create(
            plan=otro_plan, gestion=2027,
            estado=VersionCatalogoPlan.ESTADO_VIGENTE,
            norma_aprobacion='Otra norma',
        )
        resultado = cadena_codificable['resultado_pad'].resultado_sectorial_catalogo
        resultado.sector.version_catalogo = otra_version
        resultado.sector.save(update_fields=['version_catalogo', 'updated_at'])

        with pytest.raises(ValidationError):
            CodificadorService.validar(cadena_codificable['tarea'])

    def test_rechaza_gestion_inconsistente(self, cadena_codificable):
        cadena_codificable['accion'].gestion = 2028

        with pytest.raises(ValidationError):
            CodificadorService.validar(cadena_codificable['tarea'])

    def test_rechaza_entidad_inconsistente(self, cadena_codificable):
        resultado_pei = cadena_codificable['accion'].producto_pei.resultado_pei
        resultado_pei.cod_entidad = '9999'

        with pytest.raises(ValidationError):
            CodificadorService.validar(cadena_codificable['tarea'])

    def test_rechaza_cgeo_no_oficial(self, cadena_codificable):
        cgeo = cadena_codificable['resultado_pad'].entidad_territorial_cgeo
        cgeo.estado = EntidadTerritorialCGEO.ESTADO_PROVISIONAL
        cgeo.save(update_fields=['estado', 'updated_at'])

        with pytest.raises(ValidationError):
            CodificadorService.validar(
                cadena_codificable['tarea'], para_oficial=True,
            )

    def test_rechaza_articulacion_pad_pei_ambigua(self, cadena_codificable):
        resultado_pad = cadena_codificable['resultado_pad']
        segundo_producto = ProductoPAD.objects.create(
            codigo_producto='COD-PP-02', denominacion='Segundo PP',
            resultado_pad=resultado_pad, correlativo=2, segmento='02',
        )
        ArticulacionPADPEI.objects.create(
            producto_pad=segundo_producto,
            producto_pei=cadena_codificable['accion'].producto_pei,
        )

        with pytest.raises(ValidationError):
            CodificadorService.validar(cadena_codificable['tarea'])

    def test_rechaza_codigo_completo_duplicado(self, cadena_codificable):
        tarea = cadena_codificable['tarea']
        codigo = CodificadorService.generar_codigo_completo(tarea)
        otra_tarea = TareaPOAU.objects.create(
            codigo_tarea='COD-TAR-02', denominacion='Otra tarea',
            actividad=cadena_codificable['actividad'], correlativo=2,
            segmento='002',
        )
        TareaPOAU.objects.filter(pk=otra_tarea.pk).update(
            codigo_completo_articulacion=codigo,
        )

        with pytest.raises(ValidationError):
            CodificadorService.validar(tarea)


@pytest.mark.django_db
class TestPromocionOficial:
    def test_promueve_crea_homologacion_y_persiste_codigo(
        self, cadena_codificable, usuario_codificador,
    ):
        tarea = cadena_codificable['tarea']
        tarea.codigo_fuente = 'SIM-2027-TAR-001'
        tarea.save(update_fields=['codigo_fuente', 'updated_at'])

        promovida = CodificadorService.promover_a_oficial(
            tarea,
            usuario=usuario_codificador,
            motivo='Homologación inicial de prueba',
            documento_respaldo='Resolución 001/2027',
        )

        promovida.refresh_from_db()
        assert promovida.estado_codigo == promovida.ESTADO_CODIGO_OFICIAL
        assert promovida.articulacion_incompleta is False
        assert promovida.codigo_completo_articulacion.endswith('.001.001.001.001')
        homologacion = HomologacionCodigo.objects.get(entidad_id=tarea.pk)
        assert homologacion.tipo_entidad == 'tarea_poau'
        assert homologacion.codigo_anterior == 'SIM-2027-TAR-001'
        assert homologacion.codigo_nuevo == promovida.codigo_completo_articulacion
        assert homologacion.usuario == usuario_codificador

    def test_rechaza_promocion_incompleta(self, cadena_codificable, usuario_codificador):
        resultado_pad = cadena_codificable['resultado_pad']
        resultado_pad.entidad_territorial_cgeo = None
        resultado_pad.save(update_fields=['entidad_territorial_cgeo', 'updated_at'])

        with pytest.raises(ValidationError):
            CodificadorService.promover_a_oficial(
                cadena_codificable['tarea'],
                usuario=usuario_codificador,
                motivo='No debe promoverse',
            )

        assert HomologacionCodigo.objects.count() == 0

    def test_rechaza_promocion_con_segmento_cero(
        self, cadena_codificable, usuario_codificador,
    ):
        cadena_codificable['actividad'].segmento = '000'

        with pytest.raises(ValidationError):
            CodificadorService.promover_a_oficial(
                cadena_codificable['tarea'],
                usuario=usuario_codificador,
                motivo='No debe promoverse',
            )

    def test_modelo_bloquea_promocion_directa(self, cadena_codificable):
        tarea = cadena_codificable['tarea']
        tarea.estado_codigo = tarea.ESTADO_CODIGO_OFICIAL

        with pytest.raises(ValidationError):
            tarea.save(update_fields=['estado_codigo', 'updated_at'])

    def test_oficial_es_inmutable_pero_admite_cambiar_denominacion(
        self, cadena_codificable, usuario_codificador,
    ):
        tarea = CodificadorService.promover_a_oficial(
            cadena_codificable['tarea'],
            usuario=usuario_codificador,
            motivo='Homologación inicial de prueba',
        )
        tarea.segmento = '002'
        with pytest.raises(ValidationError):
            tarea.save(update_fields=['segmento', 'updated_at'])

        tarea.refresh_from_db()
        tarea.denominacion = 'Denominación corregida sin alterar código'
        tarea.save(update_fields=['denominacion', 'updated_at'])
        tarea.refresh_from_db()
        assert tarea.denominacion == 'Denominación corregida sin alterar código'

    def test_oficial_bloquea_cambio_de_relacion_codificante(
        self, cadena_codificable, usuario_codificador,
    ):
        tarea = CodificadorService.promover_a_oficial(
            cadena_codificable['tarea'],
            usuario=usuario_codificador,
            motivo='Homologación inicial de prueba',
        )
        otra_actividad = ActividadPOAU.objects.create(
            codigo_actividad='COD-ACT-OTRA', denominacion='Otra actividad',
            operacion=cadena_codificable['operacion'], correlativo=2,
            segmento='002',
        )
        tarea.actividad = otra_actividad

        with pytest.raises(ValidationError):
            tarea.save(update_fields=['actividad', 'updated_at'])
