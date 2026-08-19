"""Tests del borrador de Matriz POA (asistente RE-SPO, guardado incremental).

Cubre el flujo completo espejo del PEI: POST borrador → PATCH por sección
(s1_articulacion, s2_responsable, acciones[]) → GET matriz → materializar
(AccionPOA → OperacionPOAU → ActividadPOAU → TareaPOAU) → circuito de
revisión validar → aprobar / observar, con la inmutabilidad del registro
aprobado y la continuidad del correlativo frente al unique de
``AccionPOA.codigo_accion``.
"""
import copy

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Rol
from apps.articulacion.models import (
    AccionPOA, ActividadPOAU, BorradorMatrizPOA, OperacionPOAU, ProductoPEI,
    ResultadoPEI, TareaPOAU,
)

User = get_user_model()

BASE = '/api/v1/articulacion/borradores-matriz-poa'


def tarea_dict(nombre):
    return {
        'denominacion': nombre,
        'responsable': 'Técnico de obras',
        'metas': 4,
        'fecha_inicio': '2026-02-01',
        'fecha_fin': '2026-11-30',
    }


def actividad_dict(nombre, tareas):
    return {
        'denominacion': nombre,
        'producto_entregable': 'Informe de avance',
        'meta_anual': 12,
        'fecha_inicio': '2026-01-15',
        'fecha_fin': '2026-12-15',
        'tareas': tareas,
    }


def operacion_dict(nombre, actividades):
    return {
        'denominacion': nombre,
        'tipo_operacion': 'Operación',
        'producto_entregable': 'Red construida',
        'unidad_ejecutora': 'Unidad de Obras Públicas',
        'responsable': 'Jefe de Obras',
        'meta_anual': 100,
        'fecha_inicio': '2026-01-05',
        'fecha_fin': '2026-12-20',
        'actividades': actividades,
    }


def accion_dict(nombre, operaciones=None, actividad='023'):
    return {
        'denominacion': nombre,
        'resultado_esperado': f'Se ha logrado {nombre.lower()}',
        'programa': '101',
        'proyecto': '0',
        'actividad': actividad,
        'presupuesto_programado': 1500000,
        'cargo_reacp': 'Jefe de la Unidad de Obras Públicas',
        'fecha_inicio': '2026-01-02',
        'fecha_fin': '2026-12-31',
        'operaciones': operaciones or [],
    }


class BorradorMatrizPOAAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tecnico = User.objects.create_user(
            email='tecnico@test.com', password='tecnico123',
        )
        rol_tecnico, _ = Rol.objects.get_or_create(
            codigo='tecnico_admin', defaults={'nombre': 'Técnico administrador'},
        )
        self.tecnico.roles.add(rol_tecnico)
        self.client.force_authenticate(user=self.tecnico)

        self.resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='1312.1', denominacion='Resultado institucional',
            cod_entidad='1312', entidad='GAM Sacaba', cod_oei='OEI1',
            vigencia_desde=2026, vigencia_hasta=2030,
        )
        self.producto_pei = ProductoPEI.objects.create(
            codigo_producto='1312.1.1',
            denominacion='Servicio de alcantarillado ampliado',
            resultado_pei=self.resultado_pei, tipo_producto='TERMINAL',
        )

    # --- Helpers -----------------------------------------------------------

    def _seccion_articulacion(self):
        return {
            'producto_pei': str(self.producto_pei.id),
            'cod_producto_pei': self.producto_pei.codigo_producto,
            'accion_institucional_especifica': self.producto_pei.denominacion,
            'indicador_proceso': 'Porcentaje de avance de la red',
            'cod_resultado_pei': self.resultado_pei.codigo_resultado,
            'resultado_pei': self.resultado_pei.denominacion,
        }

    def _crear_borrador_con_cabecera(self, gestion=2026):
        response = self.client.post(f'{BASE}/', {'gestion': gestion}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        borrador_id = response.data['id']
        for seccion, valores in (
            ('s1_articulacion', self._seccion_articulacion()),
            ('s2_responsable', {
                'unidad_responsable': None,
                'area_responsable': 'Dirección de Infraestructura',
            }),
        ):
            response = self.client.patch(
                f'{BASE}/{borrador_id}/',
                {'seccion': seccion, 'valores': valores}, format='json',
            )
            self.assertEqual(
                response.status_code, status.HTTP_200_OK,
                f'PATCH {seccion} falló: {response.data}',
            )
        return borrador_id

    def _aprobador(self):
        """Jefatura de SIS-POA: aprueba y observa.

        Necesita DOS roles y no uno: ``revisor_planificacion`` la habilita en
        ``ROLES_APROBADORES``, pero ``ArticulacionPermisos`` solo deja escribir
        a ``superadmin``/``planificador``/``tecnico_admin``. Sin el segundo rol
        el POST muere en 403 antes de llegar al circuito de revisión.
        """
        jefatura = User.objects.create_user(
            email='jefatura@test.com', password='jefatura123',
        )
        for codigo, nombre in (
            ('revisor_planificacion', 'Revisor de planificación'),
            ('planificador', 'Planificador'),
        ):
            rol, _ = Rol.objects.get_or_create(
                codigo=codigo, defaults={'nombre': nombre},
            )
            jefatura.roles.add(rol)
        return jefatura

    # --- Flujo completo ----------------------------------------------------

    def test_flujo_completo_matriz_y_materializacion(self):
        """Secciones → matriz de 15 columnas → cadena operativa completa."""
        borrador_id = self._crear_borrador_con_cabecera()

        acciones = [
            accion_dict('Construcción de la red del Distrito 4', [
                operacion_dict('Ejecución de obra civil', [
                    actividad_dict('Excavación y tendido', [
                        tarea_dict('Replanteo topográfico'),
                        tarea_dict('Excavación de zanjas'),
                    ]),
                    actividad_dict('Pruebas hidráulicas', [
                        tarea_dict('Prueba de estanqueidad'),
                    ]),
                ]),
                operacion_dict('Supervisión técnica', [
                    actividad_dict('Informes de supervisión', []),
                ]),
            ]),
            accion_dict('Ampliación de la red del Distrito 5', actividad='024'),
        ]
        response = self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'acciones', 'valores': acciones}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['datos']['acciones'], acciones)

        # Matriz en vivo desde el borrador: una fila por acción.
        response = self.client.get(f'{BASE}/{borrador_id}/matriz/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        primera = response.data[0]
        self.assertEqual(primera['cod_producto_pei'], '1312.1.1')
        self.assertEqual(primera['cod_accion_poa'], '1312.1.1.1')
        self.assertEqual(primera['categoria_programatica'], '101 0 023')
        self.assertEqual(primera['area_responsable'], 'Dirección de Infraestructura')
        self.assertEqual(primera['total_operaciones'], 2)
        self.assertEqual(primera['total_actividades'], 3)
        self.assertEqual(primera['total_tareas'], 3)
        # Claves de m2_pei_poa sobre la misma fila: la vista "Articulación
        # PEI → POA" es otra proyección, no otra consulta.
        self.assertEqual(primera['cod_resultado_pei'], '1312.1')
        self.assertEqual(primera['producto_pei'], self.producto_pei.denominacion)
        self.assertEqual(primera['indicador'], 'Porcentaje de avance de la red')
        self.assertEqual(response.data[1]['categoria_programatica'], '101 0 024')

        # Materialización: la cadena operativa entera.
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['acciones'], 2)
        self.assertEqual(response.data['operaciones'], 2)
        self.assertEqual(response.data['actividades'], 3)
        self.assertEqual(response.data['tareas'], 3)
        self.assertEqual(
            response.data['codigos']['acciones'], ['1312.1.1.1', '1312.1.1.2'],
        )

        self.assertEqual(AccionPOA.objects.count(), 2)
        self.assertEqual(OperacionPOAU.objects.count(), 2)
        self.assertEqual(ActividadPOAU.objects.count(), 3)
        self.assertEqual(TareaPOAU.objects.count(), 3)

        accion = AccionPOA.objects.get(codigo_accion='1312.1.1.1')
        self.assertEqual(accion.correlativo, 1)
        self.assertEqual(accion.segmento, '001')
        self.assertEqual(accion.gestion, 2026)
        self.assertEqual(accion.categoria_programatica, '101 0 023')
        self.assertEqual(accion.programa, '101')
        self.assertEqual(accion.proyecto_sisin, '0')
        self.assertEqual(accion.actividad_presupuestaria, '023')
        self.assertEqual(accion.indicador, 'Porcentaje de avance de la red')
        self.assertEqual(str(accion.presupuesto_programado), '1500000.00')
        self.assertEqual(accion.operaciones.count(), 2)

        operacion = accion.operaciones.get(codigo_operacion='1312.1.1.1.1')
        self.assertEqual(operacion.correlativo, 1)
        self.assertEqual(operacion.actividades.count(), 2)
        actividad = operacion.actividades.get(codigo_actividad='1312.1.1.1.1.1')
        self.assertEqual(actividad.tareas.count(), 2)
        self.assertTrue(
            TareaPOAU.objects.filter(codigo_tarea='1312.1.1.1.1.1.1').exists()
        )

        borrador = BorradorMatrizPOA.objects.get(pk=borrador_id)
        self.assertEqual(borrador.estado, BorradorMatrizPOA.ESTADO_COMPLETO)
        self.assertEqual(borrador.id_accion_poa_id, accion.id)

        # Re-materializar → 400.
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_materializar_continua_el_correlativo_ya_registrado(self):
        """``codigo_accion`` es único: reiniciar en 1 chocaría contra la BD."""
        AccionPOA.objects.create(
            codigo_accion='1312.1.1.1', correlativo=1, segmento='001',
            denominacion='Acción previa', producto_pei=self.producto_pei,
            gestion=2026,
        )
        borrador_id = self._crear_borrador_con_cabecera()
        self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'acciones', 'valores': [accion_dict('Acción nueva')]},
            format='json',
        )
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['codigos']['acciones'], ['1312.1.1.2'])
        self.assertEqual(
            AccionPOA.objects.get(codigo_accion='1312.1.1.2').correlativo, 2,
        )

        # El borrador guarda el código realmente asignado, no el previsto.
        borrador = BorradorMatrizPOA.objects.get(pk=borrador_id)
        self.assertEqual(borrador.datos['acciones'][0]['codigo'], '1312.1.1.2')
        response = self.client.get(f'{BASE}/{borrador_id}/matriz/')
        self.assertEqual(response.data[0]['cod_accion_poa'], '1312.1.1.2')

    def test_materializar_sin_articulacion_pei_es_rechazado(self):
        response = self.client.post(f'{BASE}/', {'gestion': 2026}, format='json')
        borrador_id = response.data['id']
        self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'acciones', 'valores': [accion_dict('Acción huérfana')]},
            format='json',
        )
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('PEI', response.data['error'])
        self.assertEqual(AccionPOA.objects.count(), 0)

    def test_materializar_sin_acciones_es_rechazado(self):
        borrador_id = self._crear_borrador_con_cabecera()
        response = self.client.post(
            f'{BASE}/{borrador_id}/materializar/', {}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AccionPOA.objects.count(), 0)

    def test_seccion_invalida_es_rechazada(self):
        borrador_id = self._crear_borrador_con_cabecera()
        response = self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 's99_invalida', 'valores': {}}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Circuito de revisión ----------------------------------------------

    def test_permisos_del_serializer_para_el_autor(self):
        borrador_id = self._crear_borrador_con_cabecera()
        response = self.client.get(f'{BASE}/{borrador_id}/')
        permisos = response.data['permisos']
        self.assertTrue(permisos['es_autor'])
        self.assertFalse(permisos['es_aprobador'])
        self.assertTrue(permisos['editar'])
        self.assertTrue(permisos['validar'])
        self.assertFalse(permisos['aprobar'])
        self.assertFalse(permisos['observar'])
        self.assertTrue(permisos['borrar'])

    def test_validar_luego_aprobar_solo_por_la_jefatura(self):
        borrador_id = self._crear_borrador_con_cabecera()

        # El técnico autor valida.
        response = self.client.post(f'{BASE}/{borrador_id}/validar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado_revision'], 'VALIDADO')

        # El técnico NO puede aprobar.
        response = self.client.post(f'{BASE}/{borrador_id}/aprobar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # La jefatura sí.
        self.client.force_authenticate(user=self._aprobador())
        response = self.client.post(f'{BASE}/{borrador_id}/aprobar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado_revision'], 'APROBADO')
        self.assertEqual(response.data['permisos']['editar'], False)
        self.assertEqual(response.data['permisos']['borrar'], False)

    def test_aprobar_sin_validar_es_rechazado(self):
        borrador_id = self._crear_borrador_con_cabecera()
        self.client.force_authenticate(user=self._aprobador())
        response = self.client.post(f'{BASE}/{borrador_id}/aprobar/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_observar_exige_texto_y_solo_la_jefatura(self):
        borrador_id = self._crear_borrador_con_cabecera()

        response = self.client.post(
            f'{BASE}/{borrador_id}/observar/',
            {'observacion': 'Falta el REACP'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self._aprobador())
        response = self.client.post(
            f'{BASE}/{borrador_id}/observar/', {'observacion': '   '}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            f'{BASE}/{borrador_id}/observar/',
            {'observacion': 'Corrija las fechas del REACP'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['estado_revision'], 'OBSERVADO')
        self.assertEqual(response.data['observacion'], 'Corrija las fechas del REACP')

    def test_aprobado_es_inmutable(self):
        """APROBADO bloquea PATCH por sección, PATCH completo, PUT y DELETE."""
        borrador_id = self._crear_borrador_con_cabecera()
        self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'acciones', 'valores': [accion_dict('Acción aprobada')]},
            format='json',
        )
        borrador = BorradorMatrizPOA.objects.get(pk=borrador_id)
        borrador.estado_revision = BorradorMatrizPOA.REVISION_APROBADO
        borrador.save(update_fields=['estado_revision'])
        datos_aprobados = copy.deepcopy(borrador.datos)

        intento = [accion_dict('Acción intrusa')]
        self.assertNotEqual(intento, datos_aprobados.get('acciones'))

        response = self.client.patch(
            f'{BASE}/{borrador_id}/',
            {'seccion': 'acciones', 'valores': intento}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        response = self.client.patch(
            f'{BASE}/{borrador_id}/', {'datos': {}}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        response = self.client.put(
            f'{BASE}/{borrador_id}/', {'gestion': 2027, 'datos': {}}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        response = self.client.delete(f'{BASE}/{borrador_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        borrador.refresh_from_db()
        self.assertEqual(borrador.datos, datos_aprobados)
        self.assertEqual(borrador.gestion, 2026)

    def test_borrar_por_el_autor_mientras_no_este_aprobado(self):
        borrador_id = self._crear_borrador_con_cabecera()
        response = self.client.delete(f'{BASE}/{borrador_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BorradorMatrizPOA.objects.filter(pk=borrador_id).exists())

    def test_borrador_requiere_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(f'{BASE}/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_borradores_expone_datos_y_permisos(self):
        self._crear_borrador_con_cabecera()
        response = self.client.get(f'{BASE}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('datos', response.data['results'][0])
        self.assertIn('permisos', response.data['results'][0])
