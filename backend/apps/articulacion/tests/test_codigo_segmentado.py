"""Tests del refactor de los 8 modelos de articulación al mixin (T2.3/T2.4).

Cada modelo operativo hereda CodigoSegmentadoModel: correlativo, segmento
(zfill según ancho del nivel), codigo_fuente, codigo_normalizado,
codigo_completo_articulacion (editable=False) y estado_codigo
(default provisional). La unicidad del correlativo se garantiza por
(padre, gestión) según el nivel. Los campos codigo_* históricos NO se
borran: conviven una gestión hasta la data migration de T5.
"""
import pytest
from django.db import IntegrityError, transaction

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    TareaPOAU,
)
from apps.codificacion.models import CodigoSegmentadoModel

# ---------------------------------------------------------------------------
# Factories mínimas (solo campos obligatorios)
# ---------------------------------------------------------------------------


def crear_resultado_pad(codigo='RP-01', vigencia=2026):
    return ResultadoPAD.objects.create(
        id_cadena=f'CAD-{codigo}',
        codigo_resultado=codigo,
        denominacion='Resultado PAD de prueba',
        lineamiento_pad='01',
        vigencia_desde=vigencia,
        vigencia_hasta=2030,
        cod_geografico='031001',
        eta='ETA de prueba',
    )


def crear_producto_pad(resultado, codigo='PP-01'):
    return ProductoPAD.objects.create(
        codigo_producto=codigo,
        denominacion='Producto PAD de prueba',
        resultado_pad=resultado,
    )


def crear_resultado_pei(codigo='RI-01', vigencia=2026):
    return ResultadoPEI.objects.create(
        codigo_resultado=codigo,
        denominacion='Resultado PEI de prueba',
        cod_entidad='1312',
        entidad='GAM Sacaba',
        vigencia_desde=vigencia,
        vigencia_hasta=2030,
    )


def crear_producto_pei(resultado, codigo='PI-01'):
    return ProductoPEI.objects.create(
        codigo_producto=codigo,
        denominacion='Producto PEI de prueba',
        resultado_pei=resultado,
    )


def crear_accion_poa(producto, codigo='ACP-01', gestion=2027):
    return AccionPOA.objects.create(
        codigo_accion=codigo,
        denominacion='Acción POA de prueba',
        producto_pei=producto,
        gestion=gestion,
    )


def crear_operacion(accion, codigo='OP-01'):
    return OperacionPOAU.objects.create(
        codigo_operacion=codigo,
        denominacion='Operación de prueba',
        tipo_operacion='Operación',
        accion_poa=accion,
    )


def crear_actividad(operacion, codigo='ACT-01'):
    return ActividadPOAU.objects.create(
        codigo_actividad=codigo,
        denominacion='Actividad de prueba',
        operacion=operacion,
    )


def crear_tarea(actividad, codigo='TAR-01'):
    return TareaPOAU.objects.create(
        codigo_tarea=codigo,
        denominacion='Tarea de prueba',
        actividad=actividad,
    )


@pytest.fixture
def cadena_completa(db):
    """Cadena ResultadoPEI → ProductoPEI → AccionPOA → Operación → Actividad."""
    resultado_pei = crear_resultado_pei()
    producto_pei = crear_producto_pei(resultado_pei)
    accion = crear_accion_poa(producto_pei)
    operacion = crear_operacion(accion)
    actividad = crear_actividad(operacion)
    return {
        'resultado_pei': resultado_pei,
        'producto_pei': producto_pei,
        'accion': accion,
        'operacion': operacion,
        'actividad': actividad,
    }


# ---------------------------------------------------------------------------
# Estructura del mixin aplicado
# ---------------------------------------------------------------------------

MODELOS_Y_ANCHO = [
    (ResultadoPAD, 2),
    (ProductoPAD, 2),
    (ResultadoPEI, 2),
    (ProductoPEI, 2),
    (AccionPOA, 3),
    (OperacionPOAU, 3),
    (ActividadPOAU, 3),
    (TareaPOAU, 3),
]


class TestMixinAplicado:
    @pytest.mark.parametrize('modelo,ancho', MODELOS_Y_ANCHO)
    def test_hereda_del_mixin(self, modelo, ancho):
        assert issubclass(modelo, CodigoSegmentadoModel)

    @pytest.mark.parametrize('modelo,ancho', MODELOS_Y_ANCHO)
    def test_ancho_segmento_del_nivel(self, modelo, ancho):
        """RT/PT/RI/PI = 2 dígitos; ACP/OP/ACT/TAR = 3 dígitos."""
        assert modelo.ANCHO_SEGMENTO == ancho

    @pytest.mark.parametrize('modelo,ancho', MODELOS_Y_ANCHO)
    def test_campos_del_mixin_presentes(self, modelo, ancho):
        nombres = {campo.name for campo in modelo._meta.fields}
        assert {
            'correlativo',
            'segmento',
            'codigo_fuente',
            'codigo_normalizado',
            'codigo_completo_articulacion',
            'estado_codigo',
        } <= nombres

    @pytest.mark.parametrize('modelo,ancho', MODELOS_Y_ANCHO)
    def test_campos_codigo_historicos_se_conservan(self, modelo, ancho):
        """Los codigo_* viejos conviven una gestión; T5 los mapea a codigo_fuente."""
        historico_por_modelo = {
            ResultadoPAD: 'codigo_resultado',
            ProductoPAD: 'codigo_producto',
            ResultadoPEI: 'codigo_resultado',
            ProductoPEI: 'codigo_producto',
            AccionPOA: 'codigo_accion',
            OperacionPOAU: 'codigo_operacion',
            ActividadPOAU: 'codigo_actividad',
            TareaPOAU: 'codigo_tarea',
        }
        assert historico_por_modelo[modelo] in {
            campo.name for campo in modelo._meta.fields
        }


class TestGenerarSegmentoPorNivel:
    def test_niveles_3_digitos_zfill(self):
        for modelo in (AccionPOA, OperacionPOAU, ActividadPOAU, TareaPOAU):
            assert modelo.generar_segmento(1) == '001'
            assert modelo.generar_segmento(19) == '019'
            assert modelo.generar_segmento(139) == '139'

    def test_niveles_2_digitos_zfill(self):
        for modelo in (ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI):
            assert modelo.generar_segmento(1) == '01'
            assert modelo.generar_segmento(12) == '12'


# ---------------------------------------------------------------------------
# Defaults en instancias reales
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDefaultsEnInstancias:
    def test_estado_codigo_default_provisional(self, cadena_completa):
        for instancia in cadena_completa.values():
            assert instancia.estado_codigo == 'provisional'

    def test_correlativo_nulo_hasta_codificar(self, cadena_completa):
        """Los registros vivos SIM-2027 sobreviven sin correlativo."""
        assert cadena_completa['operacion'].correlativo is None
        assert cadena_completa['actividad'].correlativo is None

    def test_codigo_completo_vacio_y_no_editable(self, cadena_completa):
        campo = AccionPOA._meta.get_field('codigo_completo_articulacion')
        assert campo.editable is False
        assert cadena_completa['accion'].codigo_completo_articulacion == ''


# ---------------------------------------------------------------------------
# Unicidad del correlativo por (padre, gestión)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUnicidadCorrelativo:
    def test_resultado_pad_unico_por_vigencia_y_correlativo(self):
        crear_resultado_pad(codigo='RP-01', vigencia=2026)
        ResultadoPAD.objects.filter(codigo_resultado='RP-01').update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                duplicado = crear_resultado_pad(codigo='RP-02', vigencia=2026)
                duplicado.correlativo = 1
                duplicado.save()

    def test_resultado_pad_correlativos_nulos_no_colisionan(self):
        """Datos vivos sin correlativo: NULL jamás viola la unicidad."""
        crear_resultado_pad(codigo='RP-01', vigencia=2026)
        crear_resultado_pad(codigo='RP-02', vigencia=2026)
        assert ResultadoPAD.objects.filter(vigencia_desde=2026).count() == 2

    def test_producto_pad_unico_por_padre_y_correlativo(self):
        resultado = crear_resultado_pad()
        crear_producto_pad(resultado, codigo='PP-01')
        ProductoPAD.objects.filter(codigo_producto='PP-01').update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductoPAD.objects.create(
                    codigo_producto='PP-02',
                    denominacion='Duplicado',
                    resultado_pad=resultado,
                    correlativo=1,
                )

    def test_producto_pad_mismo_correlativo_en_otro_padre_es_valido(self):
        otro_resultado = crear_resultado_pad(codigo='RP-02')
        crear_producto_pad(crear_resultado_pad(), codigo='PP-01')
        ProductoPAD.objects.filter(codigo_producto='PP-01').update(correlativo=1)
        producto = ProductoPAD.objects.create(
            codigo_producto='PP-02',
            denominacion='Válido en otro padre',
            resultado_pad=otro_resultado,
            correlativo=1,
        )
        assert producto.pk is not None

    def test_resultado_pei_unico_por_vigencia_y_correlativo(self):
        crear_resultado_pei(codigo='RI-01', vigencia=2026)
        ResultadoPEI.objects.filter(codigo_resultado='RI-01').update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                crear_resultado_pei(codigo='RI-02', vigencia=2026)
                ResultadoPEI.objects.filter(codigo_resultado='RI-02').update(
                    correlativo=1,
                )

    def test_producto_pei_unico_por_padre_y_correlativo(self):
        resultado = crear_resultado_pei()
        crear_producto_pei(resultado, codigo='PI-01')
        ProductoPEI.objects.filter(codigo_producto='PI-01').update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProductoPEI.objects.create(
                    codigo_producto='PI-02',
                    denominacion='Duplicado',
                    resultado_pei=resultado,
                    correlativo=1,
                )

    def test_accion_poa_unico_por_padre_gestion_y_correlativo(self):
        producto = crear_producto_pei(crear_resultado_pei())
        crear_accion_poa(producto, codigo='ACP-01', gestion=2027)
        AccionPOA.objects.filter(codigo_accion='ACP-01').update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                AccionPOA.objects.create(
                    codigo_accion='ACP-02',
                    denominacion='Duplicada',
                    producto_pei=producto,
                    gestion=2027,
                    correlativo=1,
                )

    def test_accion_poa_mismo_correlativo_en_otra_gestion_es_valido(self):
        producto = crear_producto_pei(crear_resultado_pei())
        crear_accion_poa(producto, codigo='ACP-01', gestion=2027)
        AccionPOA.objects.filter(codigo_accion='ACP-01').update(correlativo=1)
        accion = AccionPOA.objects.create(
            codigo_accion='ACP-02',
            denominacion='Válida en otra gestión',
            producto_pei=producto,
            gestion=2028,
            correlativo=1,
        )
        assert accion.pk is not None

    def test_operacion_unico_por_accion_y_correlativo(self, cadena_completa):
        OperacionPOAU.objects.filter(
            pk=cadena_completa['operacion'].pk,
        ).update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                OperacionPOAU.objects.create(
                    codigo_operacion='OP-02',
                    denominacion='Duplicada',
                    tipo_operacion='Operación',
                    accion_poa=cadena_completa['accion'],
                    correlativo=1,
                )

    def test_actividad_unico_por_operacion_y_correlativo(self, cadena_completa):
        ActividadPOAU.objects.filter(
            pk=cadena_completa['actividad'].pk,
        ).update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ActividadPOAU.objects.create(
                    codigo_actividad='ACT-02',
                    denominacion='Duplicada',
                    operacion=cadena_completa['operacion'],
                    correlativo=1,
                )

    def test_tarea_unico_por_actividad_y_correlativo(self, cadena_completa):
        tarea = crear_tarea(cadena_completa['actividad'])
        TareaPOAU.objects.filter(pk=tarea.pk).update(correlativo=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                TareaPOAU.objects.create(
                    codigo_tarea='TAR-02',
                    denominacion='Duplicada',
                    actividad=cadena_completa['actividad'],
                    correlativo=1,
                )

    def test_tarea_mismo_correlativo_en_otra_actividad_es_valido(self, cadena_completa):
        otra_actividad = crear_actividad(
            cadena_completa['operacion'], codigo='ACT-02',
        )
        tarea = crear_tarea(cadena_completa['actividad'])
        TareaPOAU.objects.filter(pk=tarea.pk).update(correlativo=1)
        otra = TareaPOAU.objects.create(
            codigo_tarea='TAR-02',
            denominacion='Válida en otra actividad',
            actividad=otra_actividad,
            correlativo=1,
        )
        assert otra.pk is not None
