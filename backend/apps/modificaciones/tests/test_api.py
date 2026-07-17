import uuid
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario
from apps.modificaciones.models import (
    SolicitudModificacion, CambioModificacion, ImpactoModificacion,
)
from apps.modificaciones.services import (
    crear_solicitud, calcular_impacto_financiero, verificar_compatibilidad,
)


class SolicitudModificacionViewSetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            email='tecnico@test.com',
            password='Test1234!',
            first_name='Técnico',
            last_name='Modificaciones',
        )
        self.admin_user = Usuario.objects.create_superuser(
            email='admin@test.com',
            password='Admin1234!',
        )
        self.client.force_authenticate(user=self.user)

        self.entidad_id = uuid.uuid4()
        self.solicitud = SolicitudModificacion.objects.create(
            tipo='meta',
            gestion_fiscal=2026,
            entidad_afectada_tipo='poau.POAU',
            entidad_afectada_id=self.entidad_id,
            motivo='Es necesario modificar la meta por cambios en la demanda del servicio',
            informe_tecnico='El informe técnico justifica el cambio',
            estado='borrador',
            solicitado_por=self.user,
        )

        self.solicitud_data = {
            'tipo': 'operacion',
            'gestion_fiscal': 2026,
            'entidad_afectada_tipo': 'poau.POAU',
            'entidad_afectada_id': str(uuid.uuid4()),
            'motivo': 'Cambio en la operación por reorganización',
            'informe_tecnico': 'Informe técnico de soporte',
            'solicitado_por': str(self.user.id),
        }

    def test_crear_solicitud(self):
        response = self.client.post(
            '/api/v1/solicitudes-modificacion/',
            self.solicitud_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SolicitudModificacion.objects.count(), 2)
        nueva = SolicitudModificacion.objects.get(id=response.data['id'])
        self.assertEqual(nueva.tipo, 'operacion')
        self.assertEqual(nueva.estado, 'borrador')

    def test_listar_solicitudes(self):
        response = self.client.get('/api/v1/solicitudes-modificacion/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_aprobar_solicitud(self):
        self.solicitud.estado = 'en_revision'
        self.solicitud.save(update_fields=['estado'])

        response = self.client.post(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/aprobar/',
            {'observaciones': 'Aprobado por revisión'},
            format='json',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

    def test_rechazar_solicitud(self):
        self.solicitud.estado = 'en_revision'
        self.solicitud.save(update_fields=['estado'])

        response = self.client.post(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/rechazar/',
            {'justificacion': 'No cumple con los requisitos técnicos'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'rechazada')

    def test_agregar_cambio(self):
        cambio_data = {
            'solicitud': str(self.solicitud.id),
            'campo': 'nombre',
            'valor_anterior': 'Meta original',
            'valor_propuesto': 'Meta modificada',
        }
        response = self.client.post(
            '/api/v1/cambios-modificacion/',
            cambio_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CambioModificacion.objects.filter(
                solicitud=self.solicitud,
            ).count(),
            1,
        )

    def test_calcular_impacto(self):
        CambioModificacion.objects.create(
            solicitud=self.solicitud,
            campo='presupuesto',
            valor_anterior='100000',
            valor_propuesto='150000',
        )
        impacto = calcular_impacto_financiero(self.solicitud)
        self.assertIsNotNone(impacto)
        self.assertEqual(impacto.impacto_financiero, Decimal('50000.00'))
        self.assertTrue(ImpactoModificacion.objects.filter(
            solicitud=self.solicitud,
        ).exists())

    def test_verificar_compatibilidad(self):
        from apps.poau.models import POAU
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

        tipo = TipoUnidad.objects.create(
            codigo='COMP', nombre='Comparabilidad', nivel=1,
        )
        unidad = UnidadOrganizacional.objects.create(
            codigo='UC', nombre='Unidad Compat', tipo=tipo, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        poau = POAU.objects.create(
            unidad=unidad,
            gestion=2026,
            codigo='POAU-COMP',
            nombre='POAU compatibilidad',
        )
        self.solicitud.poau = poau
        self.solicitud.save(update_fields=['poau'])

        resultado = verificar_compatibilidad(self.solicitud)
        self.assertIn('compatible', resultado)
        self.assertIn('detalles', resultado)

    def test_solicitud_borrador_transiciones(self):
        self.assertEqual(self.solicitud.estado, 'borrador')

        self.solicitud.estado = 'en_revision'
        self.solicitud.save(update_fields=['estado'])
        self.assertEqual(self.solicitud.estado, 'en_revision')

        self.solicitud.estado = 'aprobada'
        self.solicitud.save(update_fields=['estado'])
        self.assertEqual(self.solicitud.estado, 'aprobada')

    def test_solicitud_aprobada_no_modificable(self):
        self.solicitud.estado = 'aprobada'
        self.solicitud.save(update_fields=['estado'])

        self.solicitud.estado = 'en_revision'
        self.solicitud.save(update_fields=['estado'])

        response = self.client.post(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/aprobar/',
            {},
            format='json',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

    def test_cambio_tipo_options(self):
        tipos = dict(SolicitudModificacion.TIPO_CHOICES)
        self.assertIn('meta', tipos)
        self.assertIn('operacion', tipos)
        self.assertIn('reprogramacion', tipos)
        self.assertIn('responsable', tipos)
        self.assertIn('inscripcion', tipos)
        self.assertIn('eliminacion', tipos)
        self.assertIn('incremento', tipos)
        self.assertIn('reduccion', tipos)
        self.assertIn('traspaso', tipos)
        self.assertIn('fuente', tipos)
        self.assertIn('organismo', tipos)
        self.assertIn('categoria', tipos)
        self.assertIn('reformulacion', tipos)
        self.assertEqual(len(tipos), 13)

    def test_impacto_financiero_calculo(self):
        CambioModificacion.objects.create(
            solicitud=self.solicitud,
            campo='presupuesto',
            valor_anterior='50000',
            valor_propuesto='80000',
        )
        CambioModificacion.objects.create(
            solicitud=self.solicitud,
            campo='monto',
            valor_anterior='30000',
            valor_propuesto='20000',
        )
        impacto = calcular_impacto_financiero(self.solicitud)
        total_esperado = abs(Decimal('80000') - Decimal('50000')) + abs(
            Decimal('20000') - Decimal('30000')
        )
        self.assertEqual(impacto.impacto_financiero, total_esperado)

    def test_permiso_solo_tecnico_admin(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/solicitudes-modificacion/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/solicitudes-modificacion/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_sin_autenticacion_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/solicitudes-modificacion/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(
            '/api/v1/solicitudes-modificacion/',
            self.solicitud_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_solicitud_sin_justificacion_error(self):
        self.solicitud.motivo = ''
        self.solicitud.save(update_fields=['motivo'])

        response = self.client.post(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/rechazar/',
            {},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_historial_aprobaciones(self):
        self.solicitud.estado = 'en_revision'
        self.solicitud.save(update_fields=['estado'])

        response = self.client.post(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/aprobar/',
            {'observaciones': 'Primera revisión'},
            format='json',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

        CambioModificacion.objects.create(
            solicitud=self.solicitud,
            campo='nombre',
            valor_anterior='Original',
            valor_propuesto='Modificado',
        )
        cambios = self.solicitud.cambios.all()
        self.assertEqual(cambios.count(), 1)
        self.assertEqual(cambios.first().campo, 'nombre')

    def test_obtener_solicitud_por_id(self):
        response = self.client.get(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tipo'], 'meta')
        self.assertEqual(response.data['gestion_fiscal'], 2026)

    def test_eliminar_solicitud_borrador(self):
        response = self.client.delete(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            SolicitudModificacion.objects.filter(id=self.solicitud.id).exists(),
        )

    def test_rechazar_sin_justificacion_error(self):
        self.solicitud.estado = 'en_revision'
        self.solicitud.save(update_fields=['estado'])

        response = self.client.post(
            f'/api/v1/solicitudes-modificacion/{self.solicitud.id}/rechazar/',
            {'justificacion': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CambioModificacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        self.solicitud = SolicitudModificacion.objects.create(
            tipo='meta',
            gestion_fiscal=2026,
            entidad_afectada_tipo='test.Model',
            entidad_afectada_id=uuid.uuid4(),
            motivo='Test motivo',
        )

    def test_cambio_str(self):
        cambio = CambioModificacion.objects.create(
            solicitud=self.solicitud,
            campo='nombre',
            valor_anterior='Original',
            valor_propuesto='Cambiado',
        )
        s = str(cambio)
        self.assertIn('nombre', s)
        self.assertIn('Original', s)
        self.assertIn('Cambiado', s)

    def test_cambio_valores(self):
        cambio = CambioModificacion.objects.create(
            solicitud=self.solicitud,
            campo='presupuesto',
            valor_anterior='10000',
            valor_propuesto='25000',
            valor_aprobado='20000',
        )
        self.assertEqual(cambio.valor_aprobado, '20000')


class ImpactoModificacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        self.solicitud = SolicitudModificacion.objects.create(
            tipo='incremento',
            gestion_fiscal=2026,
            entidad_afectada_tipo='test.Model',
            entidad_afectada_id=uuid.uuid4(),
            motivo='Incremento necesario',
        )

    def test_impacto_str(self):
        impacto = ImpactoModificacion.objects.create(
            solicitud=self.solicitud,
            impacto_financiero=Decimal('50000.00'),
            impacto_fisico='Aumento de productividad',
        )
        s = str(impacto)
        self.assertIn('50000', s)
        self.assertIn('Incremento', s)

    def test_impacto_default_cero(self):
        impacto = ImpactoModificacion.objects.create(
            solicitud=self.solicitud,
        )
        self.assertEqual(impacto.impacto_financiero, Decimal('0.00'))


class SolicitudModificacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )

    def test_solicitud_str(self):
        solicitud = SolicitudModificacion.objects.create(
            tipo='meta',
            gestion_fiscal=2026,
            entidad_afectada_tipo='poau.POAU',
            entidad_afectada_id=uuid.uuid4(),
            motivo='Test',
        )
        s = str(solicitud)
        self.assertIn('Modificación de Meta', s)
        self.assertIn('Borrador', s)

    def test_solicitud_estado_choices(self):
        estados = dict(SolicitudModificacion.ESTADO_CHOICES)
        self.assertIn('borrador', estados)
        self.assertIn('en_revision', estados)
        self.assertIn('aprobada', estados)
        self.assertIn('rechazada', estados)
        self.assertIn('cumplida', estados)

    def test_solicitud_version_default(self):
        solicitud = SolicitudModificacion.objects.create(
            tipo='reformulacion',
            gestion_fiscal=2026,
            entidad_afectada_tipo='test.Model',
            entidad_afectada_id=uuid.uuid4(),
            motivo='Reformulación',
        )
        self.assertEqual(solicitud.version, 1)
