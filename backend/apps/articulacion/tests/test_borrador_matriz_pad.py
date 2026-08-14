"""Tests del borrador de Matriz PAD (wizard 11 pasos, guardado incremental).

Cubre el flujo completo verificado por el SDD con la estructura REAL de las
matrices: VARIOS resultados territoriales, cada uno con VARIOS productos,
agregándose como filas a la misma Matriz A y Matriz B.

Flujo: POST borrador → PATCH sección (p1..p5 + resultados[] completa) →
GET matriz_a (borrador) → materializar → GET matriz_a (modelos) → GET
matriz_b. También se verifica la retrocompatibilidad con el formato legacy
p6..p10 (cadena única).
"""
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.articulacion.models import (
    BorradorMatrizPAD, ResultadoPAD, ProductoPAD, IndicadorCadena,
    AcuerdoInternacional,
)
from apps.planificacion.models import Plan
from apps.codificacion.models import (
    VersionCatalogoPlan, EntidadTerritorialCGEO, LineamientoPAD,
)

User = get_user_model()


def seccion_nacional():
    return {
        'eje': {'id': '7691f6f8-2fd0-4349-a11a-cb0e24013b9b', 'codigo': 'E1', 'denominacion': 'Eje 1'},
        'objetivo_impacto': 'Impacto nacional',
        'componente': {'id': '01ba47a2-bd34-4807-8ac5-6278f6a47602', 'codigo': 'C1', 'denominacion': 'Componente 1'},
        'objetivo_efecto': 'Efecto departamental',
    }


def seccion_territorial(cgeo):
    return {
        'cgeo': {'id': str(cgeo.id), 'codigo': '031001', 'denominacion': 'Sacaba'},
        'eta': 'Sacaba',
        'politica': 'Directriz territorial',
    }


def seccion_lineamiento(lineamiento):
    return {
        'lineamiento': {
            'id': str(lineamiento.id), 'codigo': '05', 'denominacion': 'Lineamiento 5',
        },
    }


def resultado_dict(nombre, productos, financiamiento=True):
    """Resultado de la colección ``resultados`` (formato nuevo)."""
    return {
        'denominacion': nombre,
        'territorializacion': 'COMUNIDAD 1, DISTRITO 4',
        'responsable': 'GAM Sacaba',
        'cuenta_con_financiamiento': financiamiento,
        'indicador': {
            'indicador': f'Indicador {nombre[:20]}',
            'formula': 'F = x / y * 100',
            'unidad_medida': 'Porcentaje',
            'linea_base': 10,
            'meta_2030': 90,
        },
        'programacion_fisica': {
            '2026': 20, '2027': 30, '2028': 40, '2029': 50, '2030': 60,
        },
        'presupuesto_total': 34000000,
        'presupuesto_anual': {
            '2026': 5000000, '2027': 6000000, '2028': 7000000,
            '2029': 8000000, '2030': 8000000,
        },
        'productos': productos,
    }


def producto_dict(nombre):
    return {
        'denominacion': nombre,
        'territorializacion': 'COMUNIDAD 1',
        'responsable': 'ENDE',
        'cuenta_con_financiamiento': True,
        'indicador': {
            'indicador': f'Indicador {nombre[:20]}',
            'formula': 'N/A',
            'unidad_medida': 'Número',
            'linea_base': 0,
            'meta_2030': 5,
        },
        'programacion_fisica': {
            '2026': 1, '2027': 1, '2028': 1, '2029': 1, '2030': 1,
        },
        'presupuesto_total': 8000000,
        'presupuesto_anual': {
            '2026': 1600000, '2027': 1600000, '2028': 1600000,
            '2029': 1600000, '2030': 1600000,
        },
    }


class BorradorMatrizPADAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_admin = User.objects.create_superuser(
            email='admin@test.com', password='admin123'
        )
        self.client.force_authenticate(user=self.user_admin)
        # Catálogos reales para las FKs de ResultadoPAD
        self.plan = Plan.objects.create(
            codigo='TEST-PAD', nombre='Plan test', tipo='pdesa',
            gestion_inicio=2026, gestion_fin=2030,
            fecha_vigencia_desde='2026-01-01',
        )
        self.version = VersionCatalogoPlan.objects.create(
            plan=self.plan, gestion=2026,
        )
        self.cgeo, _ = EntidadTerritorialCGEO.objects.get_or_create(
            codigo='031001', defaults={'nombre': 'Sacaba', 'nivel': 'municipio'},
        )
        self.lineamiento = LineamientoPAD.objects.create(
            codigo='05', denominacion='Lineamiento 5',
            version_catalogo=self.version,
            entidad_territorial=self.cgeo,
        )
        self.ods = AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='ODS 7',
            denominacion='Energía Asequible y No Contaminante',
        )

    def _crear_borrador_con_cabecera(self):
        """POST borrador + PATCH p1..p5; devuelve el id."""
        response = self.client.post(
            '/api/v1/articulacion/borradores-matriz-pad/',
            {'gestion': 2026}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        borrador_id = response.data['id']
        for seccion, valores in {
            'p1_nacional': seccion_nacional(),
            'p3_sectorial': {'sector': {'id': 'db684b00-6952-49b3-9aa9-7670750d4775', 'codigo': '02', 'denominacion': 'Agropecuario'}},
            'p4_territorial': seccion_territorial(self.cgeo),
            'p5_lineamiento': seccion_lineamiento(self.lineamiento),
        }.items():
            response = self.client.patch(
                f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
                {'seccion': seccion, 'valores': valores}, format='json',
            )
            self.assertEqual(
                response.status_code, status.HTTP_200_OK,
                f'PATCH {seccion} falló: {response.data}',
            )
        return borrador_id

    def test_flujo_completo_coleccion_resultados(self):
        """Colección resultados: 2 resultados (2+1 productos) → 5 filas A/B."""
        # 1. Crear borrador + cabecera p1..p5
        borrador_id = self._crear_borrador_con_cabecera()

        # 2. PATCH sección "resultados" con la lista completa
        coleccion = [
            resultado_dict('Se ha incrementado la cobertura de energía', [
                producto_dict('Proyecto de electrificación rural'),
                producto_dict('Sistemas de alumbrado público'),
            ]),
            resultado_dict('Se ha incrementado la disponibilidad hídrica', [
                producto_dict('Construcción de represas'),
            ]),
        ]
        response = self.client.patch(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
            {'seccion': 'resultados', 'valores': coleccion}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['datos']['resultados'], coleccion)

        # 3. Sección inválida → 400
        response = self.client.patch(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
            {'seccion': 'p99_invalida', 'valores': {}}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Estructura inválida de resultados → 400
        response = self.client.patch(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
            {'seccion': 'resultados', 'valores': [{'sin_denominacion': True}]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.patch(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
            {'seccion': 'resultados', 'valores': {'no': 'es lista'}},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Matriz A en vivo (desde borrador, sin materializar): 5 filas
        response = self.client.get(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/matriz_a/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)  # 1+2 + 1+1
        fila_resultado = response.data[0]
        self.assertEqual(fila_resultado['tipo_fila'], 'resultado')
        self.assertEqual(
            fila_resultado['codigo_resultado_pad'], '031001.05.1',
        )
        self.assertEqual(fila_resultado['politica'], 'Directriz territorial')
        self.assertEqual(fila_resultado['presupuesto_total'], '34000000')
        self.assertEqual(response.data[1]['codigo_producto_pad'], '031001.05.1.1')
        self.assertEqual(response.data[2]['codigo_producto_pad'], '031001.05.1.2')
        # Segundo resultado: correlativo incremental + producto propio
        self.assertEqual(
            response.data[3]['codigo_resultado_pad'], '031001.05.2',
        )
        self.assertEqual(response.data[4]['codigo_producto_pad'], '031001.05.2.1')
        # Orden: resultado, sus productos, siguiente resultado...
        self.assertEqual(response.data[3]['tipo_fila'], 'resultado')
        self.assertEqual(response.data[4]['tipo_fila'], 'producto')

        # 6. Matriz B en vivo: mismas 5 filas
        response = self.client.get(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/matriz_b/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data[0]['cod_eje_pgdesa'], 'E1')
        self.assertEqual(response.data[0]['sector'], 'Agropecuario')

        # 7. Materializar (transacción atómica)
        response = self.client.post(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/materializar/',
            {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado'], 'COMPLETO')
        self.assertEqual(response.data['total_resultados'], 2)
        self.assertEqual(response.data['total_productos'], 3)
        self.assertEqual(response.data['total_indicadores'], 5)
        self.assertEqual(
            response.data['codigos']['resultados'], ['031001.05.1', '031001.05.2'],
        )

        # 8. Registros operativos creados
        self.assertEqual(ResultadoPAD.objects.count(), 2)
        self.assertEqual(ProductoPAD.objects.count(), 3)
        self.assertEqual(IndicadorCadena.objects.count(), 5)
        resultado = ResultadoPAD.objects.get(codigo_resultado='031001.05.1')
        self.assertEqual(resultado.cuenta_con_financiamiento, True)
        self.assertEqual(resultado.responsable_pad, 'GAM Sacaba')
        self.assertEqual(resultado.productos.count(), 2)

        # 9. Re-materializar → 400 (ya materializado)
        response = self.client.post(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/materializar/',
            {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 10. Matriz A desde modelos materializados: 5 filas
        response = self.client.get(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/matriz_a/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data[0]['nivel'], 'RESULTADO_PAD')
        self.assertEqual(response.data[0]['presupuesto_total'], '34000000')
        self.assertEqual(response.data[1]['nivel'], 'PRODUCTO_PAD')
        self.assertEqual(response.data[1]['presupuesto_2026'], '1600000')
        self.assertEqual(
            response.data[3]['codigo_resultado_pad'], '031001.05.2',
        )

        # 11. Matriz B desde modelos: 5 filas
        response = self.client.get(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/matriz_b/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data[0]['compromiso_3030'], '')

    def test_retrocompatibilidad_legacy_p6_p10(self):
        """Borradores legacy (p6..p10, cadena única) siguen materializando."""
        borrador_id = self._crear_borrador_con_cabecera()
        secciones_legacy = {
            'p6_resultado': {
                'denominacion': 'Se ha incrementado la cobertura',
                'territorializacion': 'COMUNIDAD 1, DISTRITO 4',
                'responsable': 'GAM Sacaba',
                'cuenta_con_financiamiento': True,
            },
            'p7_producto': {
                'denominacion': 'Proyecto de electrificación',
                'territorializacion': 'COMUNIDAD 1',
                'responsable': 'ENDE',
                'cuenta_con_financiamiento': True,
            },
            'p8_indicador_resultado': {
                'indicador': 'Indicador resultado', 'formula': 'F', 'unidad_medida': '%',
                'linea_base': 10, 'meta_2030': 90,
                'programacion_fisica': {'2026': 20, '2027': 30},
            },
            'p9_indicador_producto': {
                'indicador': 'Indicador producto', 'formula': 'N/A', 'unidad_medida': 'Número',
                'linea_base': 0, 'meta_2030': 5,
                'programacion_fisica': {'2026': 1},
            },
            'p10_financiera': {
                'presupuesto_total': 34000000,
                'presupuesto_anual': {'2026': 5000000},
            },
        }
        for seccion, valores in secciones_legacy.items():
            response = self.client.patch(
                f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
                {'seccion': seccion, 'valores': valores}, format='json',
            )
            self.assertEqual(
                response.status_code, status.HTTP_200_OK,
                f'PATCH {seccion} falló: {response.data}',
            )

        # Matriz A en vivo: 2 filas (resultado + producto) por transformación
        response = self.client.get(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/matriz_a/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Materializar: 1 resultado + 1 producto
        response = self.client.post(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/materializar/',
            {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['total_resultados'], 1)
        self.assertEqual(response.data['total_productos'], 1)
        self.assertEqual(ResultadoPAD.objects.count(), 1)
        self.assertEqual(ProductoPAD.objects.count(), 1)

    def test_borrador_requiere_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            '/api/v1/articulacion/borradores-matriz-pad/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_borradores(self):
        BorradorMatrizPAD.objects.create(gestion=2026)
        response = self.client.get(
            '/api/v1/articulacion/borradores-matriz-pad/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('datos', response.data['results'][0])

    def test_materializar_preserva_valores_falsy(self):
        """linea_base=0 / meta_2030=0 / presupuesto=0 no deben perderse."""
        borrador_id = self._crear_borrador_con_cabecera()
        coleccion = [{
            'denominacion': 'Resultado con valores cero',
            'territorializacion': '',
            'responsable': '',
            'cuenta_con_financiamiento': False,
            'indicador': {
                'indicador': 'I', 'formula': 'F', 'unidad_medida': '%',
                'linea_base': 0, 'meta_2030': 0,
            },
            'programacion_fisica': {'2026': 0, '2027': 0},
            'presupuesto_total': 0,
            'presupuesto_anual': {'2026': 0},
            'productos': [{
                'denominacion': 'Producto con valores cero',
                'territorializacion': '',
                'responsable': '',
                'cuenta_con_financiamiento': False,
                'indicador': {
                    'indicador': 'I2', 'formula': 'F2', 'unidad_medida': '%',
                    'linea_base': 0, 'meta_2030': 0,
                },
                'programacion_fisica': {'2026': 0},
                'presupuesto_total': 0,
                'presupuesto_anual': {'2026': 0},
            }],
        }]
        response = self.client.patch(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/',
            {'seccion': 'resultados', 'valores': coleccion}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        response = self.client.post(
            f'/api/v1/articulacion/borradores-matriz-pad/{borrador_id}/materializar/',
            {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        ind_resultado = IndicadorCadena.objects.get(nivel_indicador='RESULTADO_PAD')
        ind_producto = IndicadorCadena.objects.get(nivel_indicador='PRODUCTO_PAD')
        self.assertEqual(ind_resultado.linea_base, 0)
        self.assertEqual(ind_resultado.meta_2030, 0)
        self.assertEqual(ind_resultado.programacion_fisica, {'2026': 0, '2027': 0})
        self.assertEqual(ind_producto.presupuesto_total, 0)
        self.assertEqual(ind_producto.presupuesto_anual, {'2026': 0})
