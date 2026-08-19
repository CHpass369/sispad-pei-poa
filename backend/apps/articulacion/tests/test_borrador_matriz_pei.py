"""Tests del borrador de Matriz PEI (asistente 2026-2030, guardado incremental).

Cubre lo que faltaba cuando el instrumento se dio por terminado: las actions
``matriz`` y ``materializar`` usaban funciones que ``views.py`` nunca importaba
y respondian 500 por NameError, sin que nadie lo notara porque el frontend
consolida las matrices con ``catchError(() => of([]))`` por registro.

Tambien cubre el circuito de revision completo, incluida la aprobacion por la
jefatura: ``ArticulacionPermisos`` solo deja escribir a quien formula, asi que
sin ``RevisionMatrizMixin`` un aprobador recibia 403 antes de llegar a la action.
"""
import copy

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Rol
from apps.articulacion.models import (
    BorradorMatrizPEI, IndicadorCadena, ProductoPEI, ResultadoPEI,
)

User = get_user_model()

BASE = '/api/v1/articulacion/borradores-matriz-pei'

GESTIONES = ('2026', '2027', '2028', '2029', '2030')


def programacion(valor):
    return {anio: valor for anio in GESTIONES}


def producto_dict(nombre, programa='1', inversion=1000, corriente=500):
    return {
        'denominacion': nombre,
        'bien_servicio': nombre,
        'condicion_estado': 'con cobertura ampliada',
        'tipo_producto': 'TERMINAL',
        'cod_programa_presup': programa,
        'programa_presup': f'Programa {programa}',
        'indicador': {
            'indicador': f'Indicador de {nombre}',
            'tipo_indicador': 'Producto',
            'unidad_medida': 'Porcentaje',
            'formula': 'F = x / y * 100',
            'linea_base': 10,
            'meta_2030': 90,
        },
        'programacion_fisica': programacion(20),
        'inversion': programacion(inversion),
        'corriente': programacion(corriente),
    }


def resultado_dict(nombre, productos):
    return {
        'correlativo': 1,
        'accion_cambio': 'Se ha incrementado',
        'variable_resultado': nombre,
        'denominacion': f'Se ha incrementado {nombre}',
        'indicador': {
            'indicador': f'Indicador de {nombre}',
            'tipo_indicador': 'Resultado',
            'unidad_medida': 'Porcentaje',
            'formula': 'F = x / y * 100',
            'linea_base': 5,
            'meta_2030': 80,
        },
        'programacion_fisica': programacion(15),
        'productos': productos,
    }


class BorradorMatrizPEIAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tecnico = User.objects.create_user(
            email='tecnico.pe@test.com', password='tecnico123',
        )
        rol, _ = Rol.objects.get_or_create(
            codigo='tecnico_pe',
            defaults={'nombre': 'Tecnico de Planificacion Estrategica'},
        )
        self.tecnico.roles.add(rol)
        self.client.force_authenticate(user=self.tecnico)

    # --- Helpers -----------------------------------------------------------

    def _crear_borrador_con_cabecera(self):
        response = self.client.post(f'{BASE}/', {'gestion': 2026}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        borrador_id = response.data['id']
        secciones = {
            's1_nacional': {
                'eje': {'codigo': 'E1'},
                'componente': {'codigo': 'C1'},
                'objetivo_impacto': 'Impacto nacional',
                'objetivo_efecto': 'Efecto departamental',
            },
            's2_acuerdos': {'ods': 'ODS 6', 'ndc': 'N/A', 'ndt': 'N/A', 'kmgbf': 'N/A'},
            's3_sector': {
                'sector': {'codigo': '02', 'denominacion': 'Agropecuario'},
                'resultado_sectorial': {'codigo': '02.1', 'denominacion': 'Resultado PES'},
            },
            's4_territorial': {
                'cod_resultado_territorial': '031001.05.1', 'resultado_pad': None,
            },
            's5_institucional': {
                'cod_entidad': '1312', 'entidad': 'GAM Sacaba', 'cod_oei': 'OEI1',
                'objetivo_estrategico': 'Objetivo institucional',
                'vigencia_desde': 2026, 'vigencia_hasta': 2030,
            },
        }
        for seccion, valores in secciones.items():
            response = self.client.patch(
                f'{BASE}/{borrador_id}/',
                {'seccion': seccion, 'valores': valores}, format='json',
            )
            self.assertEqual(
                response.status_code, status.HTTP_200_OK,
                f'PATCH {seccion} fallo: {response.data}',
            )
        return borrador_id

    def _jefatura(self):
        usuario = User.objects.create_user(
            email='jefe.pe@test.com', password='jefe123',
        )
        rol, _ = Rol.objects.get_or_create(
            codigo='jefe_pe',
            defaults={'nombre': 'Jefe de Planificacion Estrategica'},
        )
        usuario.roles.add(rol)
        return usuario

    # --- Matriz y materializacion ------------------------------------------

    def test_matriz_responde_y_arma_las_filas(self):
        """Regresion: la action usaba `construir_filas_pei` sin importarla."""
        borrador_id = self._crear_borrador_con_cabecera()
        coleccion = [resultado_dict('la cobertura de agua', [
            producto_dict('Sistema de agua potable'),
            producto_dict('Red de alcantarillado', programa='2'),
        ])]
        response = self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'resultados', 'valores': coleccion}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        response = self.client.get(f'{BASE}/{borrador_id}/matriz/')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # 1 fila de resultado + 2 de productos.
        self.assertEqual(len(response.data), 3)

        fila_resultado = response.data[0]
        self.assertEqual(fila_resultado['tipo_fila'], 'resultado')
        self.assertEqual(fila_resultado['cod_resultado_pei'], '1312.1')
        self.assertEqual(fila_resultado['cod_eje_pgdesa'], 'E1')
        self.assertEqual(fila_resultado['cod_producto'], 'NO APLICA')
        # El presupuesto del resultado consolida el de sus productos.
        self.assertEqual(fila_resultado['inversion_total'], 10000)
        self.assertEqual(fila_resultado['corriente_total'], 5000)

        self.assertEqual(response.data[1]['tipo_fila'], 'producto')
        self.assertEqual(response.data[1]['cod_producto'], '1312.1.1')
        self.assertEqual(response.data[2]['cod_producto'], '1312.1.2')
        self.assertEqual(response.data[1]['presupuesto_total'], 7500)

    def test_materializar_crea_la_cadena_institucional(self):
        """Regresion: la action usaba `materializar_borrador_pei` sin importarla."""
        borrador_id = self._crear_borrador_con_cabecera()
        coleccion = [resultado_dict('la cobertura de agua', [
            producto_dict('Sistema de agua potable'),
            producto_dict('Red de alcantarillado', programa='2'),
        ])]
        self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'resultados', 'valores': coleccion}, format='json',
        )

        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['resultados'], 1)
        self.assertEqual(response.data['productos'], 2)
        # Un indicador por resultado y uno por producto.
        self.assertEqual(response.data['indicadores'], 3)

        self.assertEqual(ResultadoPEI.objects.count(), 1)
        self.assertEqual(ProductoPEI.objects.count(), 2)
        self.assertEqual(IndicadorCadena.objects.count(), 3)

        resultado = ResultadoPEI.objects.get(codigo_resultado='1312.1')
        self.assertEqual(resultado.entidad, 'GAM Sacaba')
        self.assertEqual(resultado.cod_eje_pgdesa, 'E1')
        self.assertEqual(resultado.cod_sector, '02')
        self.assertEqual(resultado.vigencia_desde, 2026)
        self.assertEqual(resultado.vigencia_hasta, 2030)
        self.assertEqual(resultado.productos.count(), 2)

        borrador = BorradorMatrizPEI.objects.get(pk=borrador_id)
        self.assertEqual(borrador.estado, BorradorMatrizPEI.ESTADO_COMPLETO)
        self.assertEqual(borrador.id_resultado_pei_id, resultado.id)

        # Re-materializar -> 400.
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_materializar_sin_resultados_es_rechazado(self):
        borrador_id = self._crear_borrador_con_cabecera()
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ResultadoPEI.objects.count(), 0)

    # --- Circuito de revision ----------------------------------------------

    def test_validar_luego_aprobar_solo_por_la_jefatura(self):
        """El aprobador no formula: sin el mixin recibia 403 antes de la action."""
        borrador_id = self._crear_borrador_con_cabecera()

        response = self.client.post(f'{BASE}/{borrador_id}/validar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado_revision'], 'VALIDADO')

        # El tecnico autor no aprueba.
        response = self.client.post(f'{BASE}/{borrador_id}/aprobar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self._jefatura())
        response = self.client.post(f'{BASE}/{borrador_id}/aprobar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado_revision'], 'APROBADO')
        self.assertFalse(response.data['permisos']['editar'])
        self.assertFalse(response.data['permisos']['borrar'])

    def test_aprobar_sin_validar_es_rechazado(self):
        borrador_id = self._crear_borrador_con_cabecera()
        self.client.force_authenticate(user=self._jefatura())
        response = self.client.post(f'{BASE}/{borrador_id}/aprobar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_observar_exige_texto_y_solo_la_jefatura(self):
        borrador_id = self._crear_borrador_con_cabecera()

        response = self.client.post(
            f'{BASE}/{borrador_id}/observar/',
            {'observacion': 'Falta el indicador'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self._jefatura())
        response = self.client.post(
            f'{BASE}/{borrador_id}/observar/', {'observacion': '  '}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            f'{BASE}/{borrador_id}/observar/',
            {'observacion': 'Corrija la linea base del producto 2'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado_revision'], 'OBSERVADO')

    def test_aprobado_es_inmutable(self):
        borrador_id = self._crear_borrador_con_cabecera()
        self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'resultados',
             'valores': [resultado_dict('la cobertura', [producto_dict('Producto')])]},
            format='json',
        )
        borrador = BorradorMatrizPEI.objects.get(pk=borrador_id)
        borrador.estado_revision = BorradorMatrizPEI.REVISION_APROBADO
        borrador.save(update_fields=['estado_revision'])
        datos_aprobados = copy.deepcopy(borrador.datos)

        intento = [resultado_dict('otra cosa', [producto_dict('Producto intruso')])]
        self.assertNotEqual(intento, datos_aprobados.get('resultados'))

        response = self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'resultados', 'valores': intento}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        response = self.client.patch(
            f'{BASE}/{borrador_id}/', {'datos': {}}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        response = self.client.delete(f'{BASE}/{borrador_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        borrador.refresh_from_db()
        self.assertEqual(borrador.datos, datos_aprobados)

    def test_permisos_del_serializer_para_el_autor(self):
        borrador_id = self._crear_borrador_con_cabecera()
        response = self.client.get(f'{BASE}/{borrador_id}/')
        permisos = response.data['permisos']
        self.assertTrue(permisos['es_autor'])
        self.assertFalse(permisos['es_aprobador'])
        self.assertTrue(permisos['editar'])
        self.assertTrue(permisos['validar'])
        self.assertFalse(permisos['aprobar'])
        self.assertTrue(permisos['borrar'])

    def test_borrador_requiere_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(f'{BASE}/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
