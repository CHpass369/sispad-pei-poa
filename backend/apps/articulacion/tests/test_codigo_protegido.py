"""Regression tests for the T2/T3 coding boundary.

Until CodificadorService is implemented in T3, API and admin users may read
coding fields but cannot assign correlatives, normalize segments, or promote a
record to OFICIAL.
"""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

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
from apps.articulacion.serializers import (
    AccionPOASerializer,
    ActividadPOAUSerializer,
    OperacionPOAUSerializer,
    ProductoPADSerializer,
    ProductoPEISerializer,
    ResultadoPADSerializer,
    ResultadoPEISerializer,
    TareaPOAUSerializer,
)


CODING_FIELDS = {
    'correlativo',
    'segmento',
    'codigo_fuente',
    'codigo_normalizado',
    'codigo_completo_articulacion',
    'articulacion_incompleta',
    'estado_codigo',
}

MODEL_SERIALIZERS = [
    (ResultadoPAD, ResultadoPADSerializer),
    (ProductoPAD, ProductoPADSerializer),
    (ResultadoPEI, ResultadoPEISerializer),
    (ProductoPEI, ProductoPEISerializer),
    (AccionPOA, AccionPOASerializer),
    (OperacionPOAU, OperacionPOAUSerializer),
    (ActividadPOAU, ActividadPOAUSerializer),
    (TareaPOAU, TareaPOAUSerializer),
]

INJECTED_CODING = {
    'correlativo': 88,
    'segmento': 'XX',
    'codigo_fuente': 'UNTRUSTED-SOURCE',
    'codigo_normalizado': 'BAD',
    'codigo_completo_articulacion': 'UNTRUSTED.COMPLETE.CODE',
    'articulacion_incompleta': False,
    'estado_codigo': 'oficial',
}


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(
        email='coding-admin@test.gob.bo', password='test123',
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def coding_cases(db):
    resultado_pad = ResultadoPAD.objects.create(
        id_cadena='PROTECT-RP-BASE',
        codigo_resultado='PROTECT-RP-BASE',
        denominacion='Resultado PAD base',
        lineamiento_pad='01',
        vigencia_desde=2027,
        vigencia_hasta=2030,
        cod_geografico='031001',
        eta='GAM Sacaba',
    )
    producto_pad = ProductoPAD.objects.create(
        codigo_producto='PROTECT-PP-BASE',
        denominacion='Producto PAD base',
        resultado_pad=resultado_pad,
    )
    resultado_pei = ResultadoPEI.objects.create(
        codigo_resultado='PROTECT-RI-BASE',
        denominacion='Resultado PEI base',
        cod_entidad='1312',
        entidad='GAM Sacaba',
        vigencia_desde=2027,
        vigencia_hasta=2030,
    )
    producto_pei = ProductoPEI.objects.create(
        codigo_producto='PROTECT-PI-BASE',
        denominacion='Producto PEI base',
        resultado_pei=resultado_pei,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='PROTECT-ACP-BASE',
        denominacion='Acción POA base',
        producto_pei=producto_pei,
        gestion=2027,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='PROTECT-OP-BASE',
        denominacion='Operación base',
        tipo_operacion='Operación',
        accion_poa=accion,
    )
    actividad = ActividadPOAU.objects.create(
        codigo_actividad='PROTECT-ACT-BASE',
        denominacion='Actividad base',
        operacion=operacion,
    )
    tarea = TareaPOAU.objects.create(
        codigo_tarea='PROTECT-TAR-BASE',
        denominacion='Tarea base',
        actividad=actividad,
    )

    return {
        'resultado_pad': {
            'model': ResultadoPAD,
            'endpoint': 'resultados-pad',
            'instance': resultado_pad,
            'payload': {
                'id_cadena': 'PROTECT-RP-NEW',
                'codigo_resultado': 'PROTECT-RP-NEW',
                'denominacion': 'Resultado PAD nuevo',
                'lineamiento_pad': '01',
                'vigencia_desde': 2028,
                'vigencia_hasta': 2030,
                'cod_geografico': '031001',
                'eta': 'GAM Sacaba',
            },
        },
        'producto_pad': {
            'model': ProductoPAD,
            'endpoint': 'productos-pad',
            'instance': producto_pad,
            'payload': {
                'codigo_producto': 'PROTECT-PP-NEW',
                'denominacion': 'Producto PAD nuevo',
                'resultado_pad': str(resultado_pad.pk),
            },
        },
        'resultado_pei': {
            'model': ResultadoPEI,
            'endpoint': 'resultados-pei',
            'instance': resultado_pei,
            'payload': {
                'codigo_resultado': 'PROTECT-RI-NEW',
                'denominacion': 'Resultado PEI nuevo',
                'cod_entidad': '1312',
                'entidad': 'GAM Sacaba',
                'vigencia_desde': 2028,
                'vigencia_hasta': 2030,
            },
        },
        'producto_pei': {
            'model': ProductoPEI,
            'endpoint': 'productos-pei',
            'instance': producto_pei,
            'payload': {
                'codigo_producto': 'PROTECT-PI-NEW',
                'denominacion': 'Producto PEI nuevo',
                'resultado_pei': str(resultado_pei.pk),
            },
        },
        'accion_poa': {
            'model': AccionPOA,
            'endpoint': 'acciones-poa',
            'instance': accion,
            'payload': {
                'codigo_accion': 'PROTECT-ACP-NEW',
                'denominacion': 'Acción POA nueva',
                'producto_pei': str(producto_pei.pk),
                'gestion': 2028,
            },
        },
        'operacion_poau': {
            'model': OperacionPOAU,
            'endpoint': 'operaciones',
            'instance': operacion,
            'payload': {
                'codigo_operacion': 'PROTECT-OP-NEW',
                'denominacion': 'Operación nueva',
                'tipo_operacion': 'Operación',
                'accion_poa': str(accion.pk),
            },
        },
        'actividad_poau': {
            'model': ActividadPOAU,
            'endpoint': 'actividades',
            'instance': actividad,
            'payload': {
                'codigo_actividad': 'PROTECT-ACT-NEW',
                'denominacion': 'Actividad nueva',
                'operacion': str(operacion.pk),
            },
        },
        'tarea_poau': {
            'model': TareaPOAU,
            'endpoint': 'tareas',
            'instance': tarea,
            'payload': {
                'codigo_tarea': 'PROTECT-TAR-NEW',
                'denominacion': 'Tarea nueva',
                'actividad': str(actividad.pk),
            },
        },
    }


@pytest.mark.parametrize('model,serializer_class', MODEL_SERIALIZERS)
def test_los_seis_campos_de_codificacion_son_read_only_en_serializer(
    model, serializer_class,
):
    serializer = serializer_class()

    assert CODING_FIELDS <= {
        name for name, field in serializer.fields.items() if field.read_only
    }


@pytest.mark.django_db
@pytest.mark.parametrize('case_name', [
    'resultado_pad',
    'producto_pad',
    'resultado_pei',
    'producto_pei',
    'accion_poa',
    'operacion_poau',
    'actividad_poau',
    'tarea_poau',
])
def test_post_no_puede_asignar_campos_de_codificacion(
    admin_client, coding_cases, case_name,
):
    case = coding_cases[case_name]
    response = admin_client.post(
        f"/api/v1/articulacion/{case['endpoint']}/",
        case['payload'] | INJECTED_CODING,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    created = case['model'].objects.get(pk=response.data['id'])
    assert created.correlativo is None
    assert created.segmento == ''
    assert created.codigo_fuente == ''
    assert created.codigo_normalizado == ''
    assert created.codigo_completo_articulacion == ''
    assert created.estado_codigo == 'provisional'


@pytest.mark.django_db
@pytest.mark.parametrize('case_name', [
    'resultado_pad',
    'producto_pad',
    'resultado_pei',
    'producto_pei',
    'accion_poa',
    'operacion_poau',
    'actividad_poau',
    'tarea_poau',
])
def test_patch_no_puede_alterar_campos_de_codificacion(
    admin_client, coding_cases, case_name,
):
    case = coding_cases[case_name]
    instance = case['instance']
    response = admin_client.patch(
        f"/api/v1/articulacion/{case['endpoint']}/{instance.pk}/",
        {'denominacion': f'Editado {case_name}'} | INJECTED_CODING,
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK, response.data
    instance.refresh_from_db()
    assert instance.denominacion == f'Editado {case_name}'
    assert instance.correlativo is None
    assert instance.segmento == ''
    assert instance.codigo_fuente == ''
    assert instance.codigo_normalizado == ''
    assert instance.codigo_completo_articulacion == ''
    assert instance.estado_codigo == 'provisional'


@pytest.mark.parametrize('model,serializer_class', MODEL_SERIALIZERS)
def test_admin_no_permite_editar_campos_de_codificacion(model, serializer_class):
    model_admin = admin.site._registry[model]

    assert CODING_FIELDS <= set(model_admin.get_readonly_fields(request=None))
