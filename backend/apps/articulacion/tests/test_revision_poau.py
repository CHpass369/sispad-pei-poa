"""Circuito de revisión de los registros POAU.

BORRADOR → VALIDADO → APROBADO, con vuelta por OBSERVADO. Se revisa registro
por registro —operación, actividad y tarea— porque las unidades presentan su
programación en momentos distintos.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Rol
from apps.articulacion.models import (
    AccionPOA, ActividadPOAU, OperacionPOAU, ProductoPEI, ResultadoPEI, TareaPOAU,
)

User = get_user_model()
API = '/api/v1/articulacion'


class RevisionPOAUTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tecnico = User.objects.create_user(
            email='tecnico@test.com', password='tecnico123',
        )
        rol_tecnico, _ = Rol.objects.get_or_create(
            codigo='tecnico_admin', defaults={'nombre': 'Técnico administrador'},
        )
        self.tecnico.roles.add(rol_tecnico)

        self.jefatura = User.objects.create_user(
            email='jefe@test.com', password='jefe12345',
        )
        rol_jefe, _ = Rol.objects.get_or_create(
            codigo='jefe_poa', defaults={'nombre': 'Jefatura POA'},
        )
        self.jefatura.roles.add(rol_jefe)

        resultado = ResultadoPEI.objects.create(
            codigo_resultado='1312.1', denominacion='Resultado institucional',
            cod_entidad='1312', entidad='GAM Sacaba', cod_oei='OEI1',
            vigencia_desde=2026, vigencia_hasta=2030,
        )
        producto = ProductoPEI.objects.create(
            codigo_producto='1312.1.1', denominacion='Servicio ampliado',
            resultado_pei=resultado, tipo_producto='TERMINAL',
        )
        self.accion = AccionPOA.objects.create(
            codigo_accion='ACP-0001', denominacion='Acción de corto plazo',
            producto_pei=producto, gestion=2027,
        )
        self.operacion = OperacionPOAU.objects.create(
            codigo_operacion='ACP-0001.1', denominacion='Operación',
            accion_poa=self.accion,
        )
        self.actividad = ActividadPOAU.objects.create(
            codigo_actividad='ACP-0001.1.1', denominacion='Actividad',
            operacion=self.operacion,
        )
        self.tarea = TareaPOAU.objects.create(
            codigo_tarea='ACP-0001.1.1.1', denominacion='Tarea',
            actividad=self.actividad,
        )

    def _post(self, coleccion, obj, accion, datos=None, como=None):
        self.client.force_authenticate(user=como or self.tecnico)
        return self.client.post(f'{API}/{coleccion}/{obj.id}/{accion}/', datos or {})

    # --- Estado inicial ----------------------------------------------------

    def test_lo_importado_nace_en_borrador(self):
        for obj in (self.operacion, self.actividad, self.tarea):
            self.assertEqual(obj.estado, 'BORRADOR')

    # --- Camino feliz ------------------------------------------------------

    def test_validar_y_aprobar_recorre_el_circuito(self):
        r = self._post('tareas', self.tarea, 'validar')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['estado'], 'VALIDADO')

        r = self._post('tareas', self.tarea, 'aprobar', como=self.jefatura)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'APROBADO')

    def test_los_tres_niveles_tienen_circuito_propio(self):
        for coleccion, obj in (('operaciones', self.operacion),
                               ('actividades', self.actividad),
                               ('tareas', self.tarea)):
            self.assertEqual(
                self._post(coleccion, obj, 'validar').status_code,
                status.HTTP_200_OK,
            )
        # Aprobar una tarea no arrastra a su actividad: se revisan por separado.
        self._post('tareas', self.tarea, 'aprobar', como=self.jefatura)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.estado, 'VALIDADO')

    # --- Orden del circuito ------------------------------------------------

    def test_no_se_aprueba_lo_que_no_fue_validado(self):
        r = self._post('tareas', self.tarea, 'aprobar', como=self.jefatura)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'BORRADOR')

    def test_un_registro_aprobado_ya_no_se_valida(self):
        self._post('tareas', self.tarea, 'validar')
        self._post('tareas', self.tarea, 'aprobar', como=self.jefatura)
        r = self._post('tareas', self.tarea, 'validar')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Quién puede qué ---------------------------------------------------

    def test_quien_formula_no_aprueba_su_propio_registro(self):
        self._post('tareas', self.tarea, 'validar')
        r = self._post('tareas', self.tarea, 'aprobar')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'VALIDADO')

    def test_quien_formula_tampoco_observa(self):
        r = self._post('tareas', self.tarea, 'observar', {'comentario': 'Falta'})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    # --- Observación -------------------------------------------------------

    def test_observar_exige_motivo(self):
        r = self._post('tareas', self.tarea, 'observar', {'comentario': '   '},
                       como=self.jefatura)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_observar_guarda_el_motivo_y_devuelve_el_registro(self):
        self._post('tareas', self.tarea, 'validar')
        r = self._post('tareas', self.tarea, 'observar',
                       {'comentario': 'Falta el cronograma mensual'},
                       como=self.jefatura)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'OBSERVADO')
        self.assertEqual(self.tarea.observacion, 'Falta el cronograma mensual')

    def test_lo_observado_se_puede_volver_a_validar_y_limpia_el_motivo(self):
        self._post('tareas', self.tarea, 'validar')
        self._post('tareas', self.tarea, 'observar', {'comentario': 'Corregir'},
                   como=self.jefatura)
        r = self._post('tareas', self.tarea, 'validar')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, 'VALIDADO')
        self.assertEqual(self.tarea.observacion, '')

    # --- Eliminación -------------------------------------------------------

    def test_un_registro_en_borrador_se_elimina(self):
        self.client.force_authenticate(user=self.tecnico)
        r = self.client.delete(f'{API}/tareas/{self.tarea.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TareaPOAU.objects.filter(id=self.tarea.id).exists())

    def test_un_registro_aprobado_no_se_elimina(self):
        self._post('tareas', self.tarea, 'validar')
        self._post('tareas', self.tarea, 'aprobar', como=self.jefatura)
        self.client.force_authenticate(user=self.tecnico)
        r = self.client.delete(f'{API}/tareas/{self.tarea.id}/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(TareaPOAU.objects.filter(id=self.tarea.id).exists())
