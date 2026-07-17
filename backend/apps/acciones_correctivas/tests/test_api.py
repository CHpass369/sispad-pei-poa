import uuid
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario
from apps.acciones_correctivas.models import (
    AccionCorrectiva, CompromisoAccionCorrectiva,
)
from apps.acciones_correctivas.services import (
    crear_accion_correctiva, verificar_cumplimiento,
    verificar_vencimiento, obtener_acciones_por_cumplir,
    actualizar_estado_automatico,
)


class AccionCorrectivaViewSetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            email='responsable@test.com',
            password='Test1234!',
            first_name='Responsable',
            last_name='Acciones',
        )
        self.admin_user = Usuario.objects.create_superuser(
            email='admin@test.com',
            password='Admin1234!',
        )
        self.client.force_authenticate(user=self.user)

        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        self.tipo_unidad = TipoUnidad.objects.create(
            codigo='AC-T',
            nombre='Unidad Acciones Correctivas',
            nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='U-AC',
            nombre='Unidad de Acciones Correctivas',
            tipo=self.tipo_unidad,
            gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )

        from apps.seguimiento.models import (
            ReporteSeguimiento, EntradaSeguimiento,
        )
        from apps.poau.models import POAU, POAUActividad

        self.poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-AC',
            nombre='POAU Acciones Correctivas',
        )
        self.actividad = POAUActividad.objects.create(
            poau=self.poau,
            codigo='ACT-AC-001',
            nombre='Actividad acciones correctivas',
        )
        self.reporte = ReporteSeguimiento.objects.create(
            gestion=2026,
            periodo='2026-Q1',
            unidad_organizacional=self.unidad,
        )
        self.entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=self.actividad,
            porcentaje_avance_fisico=Decimal('30.00'),
        )

        from apps.seguimiento.models import Alerta
        self.alerta = Alerta.objects.create(
            entrada=self.entrada,
            tipo='ejecucion_fisica_baja',
            severidad='moderada',
            mensaje='Avance físico por debajo del umbral',
        )

        self.accion = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Corregir el avance físico de la actividad',
            cause='Retraso en la adquisición de materiales',
            responsible=self.user,
            responsible_unit=self.unidad,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            expected_result='Alcanzar 80% de avance físico',
            status='pendiente',
            gestion=2026,
        )

        self.accion_data = {
            'alerta': str(self.alerta.id),
            'entry': str(self.entrada.id),
            'description': 'Implementar medidas correctivas adicionales',
            'cause': 'Incumplimiento parcial del plan',
            'responsible': str(self.user.id),
            'responsible_unit': str(self.unidad.id),
            'start_date': date.today().isoformat(),
            'due_date': (date.today() + timedelta(days=15)).isoformat(),
            'expected_result': 'Mejora del 50% en avance',
            'gestion': 2026,
        }

    def test_crear_accion_correctiva(self):
        response = self.client.post(
            '/api/v1/acciones-correctivas/',
            self.accion_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AccionCorrectiva.objects.count(), 2)
        nueva = AccionCorrectiva.objects.get(id=response.data['id'])
        self.assertEqual(nueva.status, 'pendiente')

    def test_listar_acciones_correctivas(self):
        response = self.client.get('/api/v1/acciones-correctivas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_agregar_compromiso(self):
        compromiso_data = {
            'accion_correctiva': str(self.accion.id),
            'description': 'Adquirir materiales necesarios',
            'due_date': (date.today() + timedelta(days=10)).isoformat(),
            'status': 'pendiente',
        }
        response = self.client.post(
            '/api/v1/compromisos-accion-correctiva/',
            compromiso_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CompromisoAccionCorrectiva.objects.filter(
                accion_correctiva=self.accion,
            ).count(),
            1,
        )

    def test_verificar_cumplimiento(self):
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Compromiso 1',
            due_date=date.today() + timedelta(days=5),
            status='cumplido',
        )
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Compromiso 2',
            due_date=date.today() + timedelta(days=10),
            status='pendiente',
        )

        resultado = verificar_cumplimiento(self.accion.id)
        self.assertEqual(resultado['total_compromisos'], 2)
        self.assertEqual(resultado['cumplidos'], 1)
        self.assertEqual(resultado['pendientes'], 1)
        self.assertFalse(resultado['todos_cumplidos'])

    def test_verificar_vencimiento_accion(self):
        self.accion.due_date = date.today() - timedelta(days=5)
        self.accion.save(update_fields=['due_date'])

        self.assertTrue(self.accion.esta_vencida)

        accion_futura = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Acción que no vence',
            cause='Sin causa',
            responsible=self.user,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            expected_result='Resultado',
            status='pendiente',
            gestion=2026,
        )
        self.assertFalse(accion_futura.esta_vencida)

    def test_obtener_acciones_por_cumplir(self):
        accion_por_cumplir = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Acción por cumplir pronto',
            cause='Causa',
            responsible=self.user,
            responsible_unit=self.unidad,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            expected_result='Resultado esperado',
            status='en_ejecucion',
            gestion=2026,
        )

        resultados = obtener_acciones_por_cumplir(dias=7)
        ids = [r['accion_id'] for r in resultados]
        self.assertIn(str(accion_por_cumplir.id), ids)

    def test_actualizar_estado_automatico(self):
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Compromiso cumplido',
            due_date=date.today() + timedelta(days=5),
            status='cumplido',
        )
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Otro compromiso cumplido',
            due_date=date.today() + timedelta(days=10),
            status='cumplido',
        )

        self.accion.status = 'en_ejecucion'
        self.accion.save(update_fields=['status'])

        actualizadas = actualizar_estado_automatico()
        self.accion.refresh_from_db()
        self.assertEqual(self.accion.status, 'cumplida')

    def test_accion_correctiva_completada(self):
        self.accion.status = 'cumplida'
        self.accion.save(update_fields=['status'])

        response = self.client.get(
            f'/api/v1/acciones-correctivas/{self.accion.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cumplida')

    def test_compromiso_cumplido(self):
        compromiso = CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Compromiso test',
            due_date=date.today() + timedelta(days=5),
            status='pendiente',
        )
        self.assertFalse(compromiso.esta_vencido)
        self.assertIsNone(compromiso.completed_at)

        compromiso.status = 'cumplido'
        compromiso.completed_at = timezone.now()
        compromiso.save(update_fields=['status', 'completed_at'])
        self.assertFalse(compromiso.esta_vencido)

    def test_accion_vencida_error(self):
        self.accion.due_date = date.today() - timedelta(days=10)
        self.accion.save(update_fields=['due_date'])
        self.assertTrue(self.accion.esta_vencida)

        self.accion.status = 'cumplida'
        self.accion.save(update_fields=['status'])
        self.assertFalse(self.accion.esta_vencida)

    def test_permiso_solo_admin(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/acciones-correctivas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/acciones-correctivas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_sin_autenticacion_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/acciones-correctivas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(
            '/api/v1/acciones-correctivas/',
            self.accion_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AccionCorrectivaModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.seguimiento.models import (
            ReporteSeguimiento, EntradaSeguimiento, Alerta,
        )
        from apps.poau.models import POAU, POAUActividad

        tipo = TipoUnidad.objects.create(
            codigo='AC-M', nombre='AC Modelo', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='U-AC-M', nombre='Unidad AC Modelo', tipo=tipo, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        poau = POAU.objects.create(
            unidad=self.unidad, gestion=2026, codigo='POAU-AC-M',
            nombre='POAU AC Modelo',
        )
        actividad = POAUActividad.objects.create(
            poau=poau, codigo='ACT-AC-M-001', nombre='Actividad AC modelo',
        )
        reporte = ReporteSeguimiento.objects.create(
            gestion=2026, periodo='2026-Q1',
            unidad_organizacional=self.unidad,
        )
        self.entrada = EntradaSeguimiento.objects.create(
            reporte=reporte, actividad=actividad,
            porcentaje_avance_fisico=Decimal('25.00'),
        )
        self.alerta = Alerta.objects.create(
            entrada=self.entrada,
            tipo='ejecucion_fisica_baja',
            severidad='grave',
            mensaje='Avance muy bajo',
        )

    def test_accion_correctiva_str(self):
        accion = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Corregir desviación en la ejecución del plan operativo',
            cause='Falta de recursos',
            responsible=self.user,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=20),
            expected_result='Plan ejecutado al 100%',
            status='pendiente',
            gestion=2026,
        )
        s = str(accion)
        self.assertIn('Corregir desviación', s)

    def test_esta_vencida_propiedad(self):
        accion = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Acción vencida',
            cause='Causa',
            responsible=self.user,
            start_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=3),
            expected_result='Resultado',
            status='pendiente',
            gestion=2026,
        )
        self.assertTrue(accion.esta_vencida)

    def test_porcentaje_cumplimiento(self):
        accion = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Acción con compromisos',
            cause='Causa',
            responsible=self.user,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            expected_result='Resultado',
            gestion=2026,
        )
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=accion,
            description='C1',
            due_date=date.today() + timedelta(days=5),
            status='cumplido',
        )
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=accion,
            description='C2',
            due_date=date.today() + timedelta(days=10),
            status='pendiente',
        )
        CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=accion,
            description='C3',
            due_date=date.today() + timedelta(days=15),
            status='cumplido',
        )
        self.assertEqual(accion.porcentaje_cumplimiento, round((2 / 3) * 100, 2))

    def test_porcentaje_cumplimiento_sin_compromisos(self):
        accion = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=self.entrada,
            description='Sin compromisos',
            cause='Causa',
            responsible=self.user,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=10),
            expected_result='Resultado',
            gestion=2026,
        )
        self.assertEqual(accion.porcentaje_cumplimiento, 0)


class CompromisoAccionCorrectivaModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.seguimiento.models import (
            ReporteSeguimiento, EntradaSeguimiento, Alerta,
        )
        from apps.poau.models import POAU, POAUActividad

        tipo = TipoUnidad.objects.create(
            codigo='COMP-M', nombre='Compromiso Modelo', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='U-COMP-M', nombre='Unidad Compromiso', tipo=tipo,
            gestion=2026, fecha_vigencia_desde=date(2026, 1, 1),
        )
        poau = POAU.objects.create(
            unidad=self.unidad, gestion=2026, codigo='POAU-COMP-M',
            nombre='POAU Compromiso',
        )
        actividad = POAUActividad.objects.create(
            poau=poau, codigo='ACT-COMP-M-001',
            nombre='Actividad compromiso',
        )
        reporte = ReporteSeguimiento.objects.create(
            gestion=2026, periodo='2026-Q1',
            unidad_organizacional=self.unidad,
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=reporte, actividad=actividad,
            porcentaje_avance_fisico=Decimal('20.00'),
        )
        self.alerta = Alerta.objects.create(
            entrada=entrada, tipo='sin_evidencia', severidad='leve',
            mensaje='Sin evidencia',
        )
        self.accion = AccionCorrectiva.objects.create(
            alerta=self.alerta,
            entry=entrada,
            description='Acción para compromisos',
            cause='Causa',
            responsible=self.user,
            start_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            expected_result='Resultado',
            gestion=2026,
        )

    def test_compromiso_str(self):
        compromiso = CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Entregar informe de avance mensual',
            due_date=date.today() + timedelta(days=7),
        )
        s = str(compromiso)
        self.assertIn('Entregar informe', s)

    def test_compromiso_esta_vencido(self):
        compromiso = CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Compromiso vencido',
            due_date=date.today() - timedelta(days=5),
            status='pendiente',
        )
        self.assertTrue(compromiso.esta_vencido)

    def test_compromiso_no_vencido_cumplido(self):
        compromiso = CompromisoAccionCorrectiva.objects.create(
            accion_correctiva=self.accion,
            description='Compromiso cumplido',
            due_date=date.today() - timedelta(days=5),
            status='cumplido',
        )
        self.assertFalse(compromiso.esta_vencido)

    def test_compromiso_estado_choices(self):
        estados = dict(CompromisoAccionCorrectiva.Estado.choices)
        self.assertIn('pendiente', estados)
        self.assertIn('cumplido', estados)
        self.assertIn('incumplido', estados)
