import uuid
from datetime import date

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario
from apps.notificaciones.models import (
    TipoNotificacion, Notificacion, PreferenciaNotificacion,
)


class NotificacionViewSetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            email='usuario@test.com',
            password='Test1234!',
            first_name='Usuario',
            last_name='Notificaciones',
        )
        self.other_user = Usuario.objects.create_user(
            email='otro@test.com',
            password='Test1234!',
        )
        self.staff_user = Usuario.objects.create_superuser(
            email='staff@test.com',
            password='Staff1234!',
        )
        self.client.force_authenticate(user=self.user)

        self.tipo = TipoNotificacion.objects.create(
            codigo='cambio_estado',
            nombre='Cambio de Estado',
            descripcion='Notificación cuando cambia el estado de un proceso',
            template_subject='Estado actualizado: {proceso}',
            template_body='El estado del proceso {proceso} ha cambiado.',
        )

        self.notificacion = Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Cambio de estado en POAU',
            mensaje='El POAU POAU-001 pasó a estado aprobado',
            priority='alta',
            gestion=2026,
            entity_type='poau.POAU',
            entity_id=uuid.uuid4(),
        )

    def test_crear_notificacion(self):
        notif_data = {
            'user': str(self.user.id),
            'tipo': str(self.tipo.id),
            'titulo': 'Nueva notificación',
            'mensaje': 'Se ha creado un nuevo reporte',
            'priority': 'media',
            'gestion': 2026,
        }
        response = self.client.post(
            '/api/v1/notificaciones/',
            notif_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notificacion.objects.count(), 2)

    def test_listar_notificaciones(self):
        response = self.client.get('/api/v1/notificaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_marcar_leida(self):
        self.assertFalse(self.notificacion.is_read)
        response = self.client.post(
            f'/api/v1/notificaciones/{self.notificacion.id}/marcar_leida/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.is_read)
        self.assertIsNotNone(self.notificacion.read_at)

    def test_marcar_todas_leidas(self):
        Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Segunda notificación',
            mensaje='Otro mensaje',
            is_read=False,
            gestion=2026,
        )
        response = self.client.post(
            '/api/v1/notificaciones/marcar_todas_leidas/',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('marcadas', response.data)
        self.assertGreaterEqual(response.data['marcadas'], 1)
        no_leidas = Notificacion.objects.filter(
            user=self.user, is_read=False,
        ).count()
        self.assertEqual(no_leidas, 0)

    def test_resumen_no_leidas(self):
        Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Segunda',
            mensaje='Segundo mensaje',
            priority='baja',
            gestion=2026,
        )
        Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Tercera',
            mensaje='Tercer mensaje',
            priority='media',
            is_read=True,
            gestion=2026,
        )
        response = self.client.get('/api/v1/notificaciones/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_no_leidas', response.data)
        self.assertIn('alta', response.data)
        self.assertIn('media', response.data)
        self.assertIn('baja', response.data)
        self.assertEqual(response.data['total_no_leidas'], 2)

    def test_preferencias_obtener(self):
        preferencia = PreferenciaNotificacion.objects.create(
            user=self.user,
            receive_internal=True,
            receive_email=False,
            frequency='inmediata',
        )
        response = self.client.get('/api/v1/preferencias/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_preferencias_actualizar(self):
        preferencia = PreferenciaNotificacion.objects.create(
            user=self.user,
            receive_internal=True,
            receive_email=False,
            frequency='inmediata',
        )
        response = self.client.patch(
            f'/api/v1/preferencias/{preferencia.id}/',
            {'receive_email': True, 'frequency': 'diaria'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        preferencia.refresh_from_db()
        self.assertTrue(preferencia.receive_email)
        self.assertEqual(preferencia.frequency, 'diaria')

    def test_notificar_cambio_estado(self):
        notif = Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Estado cambiado',
            mensaje='El proceso cambió de estado',
            priority='alta',
            gestion=2026,
        )
        self.assertFalse(notif.is_read)
        notif.marcar_leida()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_notificar_vencimiento(self):
        tipo_venc = TipoNotificacion.objects.create(
            codigo='vencimiento',
            nombre='Vencimiento',
            descripcion='Notificación de vencimiento de plazo',
        )
        notif = Notificacion.objects.create(
            user=self.user,
            tipo=tipo_venc,
            titulo='Plazo próximo a vencer',
            mensaje='La actividad ACT-001 vence en 3 días',
            priority='alta',
            gestion=2026,
        )
        response = self.client.get(
            f'/api/v1/notificaciones/{notif.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'alta')

    def test_tipo_notificacion_crear(self):
        tipo_data = {
            'codigo': 'nuevo_indicador',
            'nombre': 'Nuevo Indicador',
            'descripcion': 'Se ha creado un nuevo indicador',
            'template_subject': 'Indicador creado',
            'template_body': 'Se creó el indicador {nombre}',
        }
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            '/api/v1/tipos/',
            tipo_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TipoNotificacion.objects.count(), 2)

    def test_notificacion_por_usuario(self):
        Notificacion.objects.create(
            user=self.other_user,
            tipo=self.tipo,
            titulo='Notificación del otro usuario',
            mensaje='Este es del otro usuario',
            gestion=2026,
        )
        response = self.client.get('/api/v1/notificaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['user'], str(self.user.id))

    def test_notificar_sin_preferencias(self):
        user_sin_pref = Usuario.objects.create_user(
            email='sinpref@test.com',
            password='Test1234!',
        )
        notif = Notificacion.objects.create(
            user=user_sin_pref,
            tipo=self.tipo,
            titulo='Sin preferencias',
            mensaje='Usuario sin preferencias configuradas',
            gestion=2026,
        )
        self.assertFalse(
            PreferenciaNotificacion.objects.filter(
                user=user_sin_pref,
            ).exists(),
        )
        self.assertIsNotNone(notif)


class NotificacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        self.tipo = TipoNotificacion.objects.create(
            codigo='test_tipo',
            nombre='Tipo Test',
        )

    def test_notificacion_str(self):
        notif = Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Notificación de prueba',
            mensaje='Mensaje de prueba',
            gestion=2026,
        )
        s = str(notif)
        self.assertIn('Notificación de prueba', s)

    def test_marcar_leida_method(self):
        notif = Notificacion.objects.create(
            user=self.user,
            tipo=self.tipo,
            titulo='Test marcar',
            mensaje='Mensaje test',
            is_read=False,
            gestion=2026,
        )
        self.assertFalse(notif.is_read)
        notif.marcar_leida()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_prioridad_choices(self):
        prioridades = dict(Notificacion.Prioridad.choices)
        self.assertIn('alta', prioridades)
        self.assertIn('media', prioridades)
        self.assertIn('baja', prioridades)


class TipoNotificacionModelTests(TestCase):

    def test_tipo_str(self):
        tipo = TipoNotificacion.objects.create(
            codigo='alerta_sistema',
            nombre='Alerta del Sistema',
            descripcion='Alerta generada automáticamente',
        )
        s = str(tipo)
        self.assertIn('alerta_sistema', s)
        self.assertIn('Alerta del Sistema', s)

    def test_tipo_codigo_unico(self):
        TipoNotificacion.objects.create(
            codigo='unico',
            nombre='Único',
        )
        with self.assertRaises(Exception):
            TipoNotificacion.objects.create(
                codigo='unico',
                nombre='Duplicado',
            )


class PreferenciaNotificacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='pref@test.com',
            password='Test1234!',
        )

    def test_preferencia_str(self):
        pref = PreferenciaNotificacion.objects.create(
            user=self.user,
            receive_internal=True,
            receive_email=False,
            frequency='inmediata',
        )
        s = str(pref)
        self.assertIn('pref@test.com', s)

    def test_preferencia_default(self):
        pref = PreferenciaNotificacion.objects.create(user=self.user)
        self.assertTrue(pref.receive_internal)
        self.assertFalse(pref.receive_email)
        self.assertEqual(pref.frequency, 'inmediata')

    def test_frecuencia_choices(self):
        freqs = dict(PreferenciaNotificacion.Frecuencia.choices)
        self.assertIn('inmediata', freqs)
        self.assertIn('diaria', freqs)
        self.assertIn('semanal', freqs)
