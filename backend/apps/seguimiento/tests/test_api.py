import uuid
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario
from apps.seguimiento.models import (
    ReporteSeguimiento, EntradaSeguimiento, Alerta, UmbralConfiguracion,
)
from apps.seguimiento.services import (
    determinar_semaforo, dashboard_seguimiento, calcular_eficacia_fisica,
    calcular_ejecucion_financiera, calcular_desviacion, calcular_proyeccion_cierre,
)


class ReporteSeguimientoViewSetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            email='tecnico@test.com',
            password='Test1234!',
            first_name='Técnico',
            last_name='Seguimiento',
        )
        self.client.force_authenticate(user=self.user)

        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        self.tipo_unidad = TipoUnidad.objects.create(
            codigo='SEC-S',
            nombre='Secretaría Seguimiento',
            nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='U-SEG',
            nombre='Unidad de Seguimiento',
            tipo=self.tipo_unidad,
            gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )

        self.reporte = ReporteSeguimiento.objects.create(
            gestion=2026,
            periodo='2026-Q1',
            unidad_organizacional=self.unidad,
            estado='borrador',
        )

        self.reporte_data = {
            'gestion': 2026,
            'periodo': '2026-S1',
            'unidad_organizacional': str(self.unidad.id),
            'estado': 'borrador',
        }

    def test_crear_reporte_seguimiento(self):
        response = self.client.post(
            '/api/v1/reportes/',
            self.reporte_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReporteSeguimiento.objects.count(), 2)

    def test_crear_entrada_seguimiento(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-SEG-001',
            nombre='POAU Seguimiento',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-SEG-001',
            nombre='Actividad de seguimiento',
        )

        entrada_data = {
            'reporte': str(self.reporte.id),
            'actividad': str(actividad.id),
            'programado_fisico': '100.0000',
            'ejecutado_fisico': '75.0000',
            'porcentaje_avance_fisico': '75.00',
            'presupuesto_inicial': '50000.00',
            'presupuesto_actual': '50000.00',
            'programado_financiero': '25000.00',
            'ejecutado_financiero': '20000.00',
            'porcentaje_avance_financiero': '80.00',
        }
        response = self.client.post(
            '/api/v1/entradas/',
            entrada_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_obtener_entradas_por_reporte(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-ENT',
            nombre='POAU Entradas',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-ENT-001',
            nombre='Actividad entrada',
        )
        EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            porcentaje_avance_fisico=Decimal('60.00'),
            porcentaje_avance_financiero=Decimal('55.00'),
        )

        response = self.client.get(
            f'/api/v1/entradas/',
            {'reporte': str(self.reporte.id)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_semaforo_verde(self):
        semaforo = determinar_semaforo(Decimal('85.00'))
        self.assertEqual(semaforo, 'verde')

        semaforo_exacto = determinar_semaforo(Decimal('80.00'))
        self.assertEqual(semaforo_exacto, 'verde')

    def test_semaforo_amarillo(self):
        semaforo = determinar_semaforo(Decimal('65.00'))
        self.assertEqual(semaforo, 'amarillo')

        semaforo_min = determinar_semaforo(Decimal('50.00'))
        self.assertEqual(semaforo_min, 'amarillo')

    def test_semaforo_rojo(self):
        semaforo = determinar_semaforo(Decimal('30.00'))
        self.assertEqual(semaforo, 'rojo')

        semaforo_zero = determinar_semaforo(Decimal('0.00'))
        self.assertEqual(semaforo_zero, 'rojo')

    def test_dashboard_datos(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-DASH',
            nombre='POAU Dashboard',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-DASH-001',
            nombre='Actividad dashboard',
        )
        EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            porcentaje_avance_fisico=Decimal('85.00'),
            porcentaje_avance_financiero=Decimal('70.00'),
        )

        response = self.client.get(
            '/api/v1/entradas/dashboard/',
            {'gestion': 2026},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('gestion', response.data)
        self.assertIn('semaforo', response.data)
        self.assertIn('total_actividades', response.data)

    def test_alertas_activas(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-AL',
            nombre='POAU Alertas',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-AL-001',
            nombre='Actividad alertas',
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            porcentaje_avance_fisico=Decimal('20.00'),
        )
        Alerta.objects.create(
            entrada=entrada,
            tipo='ejecucion_fisica_baja',
            severidad='grave',
            mensaje='Avance muy bajo',
            activa=True,
        )

        response = self.client.get('/api/v1/alertas/activas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_resolver_alerta(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-RES',
            nombre='POAU Resolver',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-RES-001',
            nombre='Actividad resolver',
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            porcentaje_avance_fisico=Decimal('30.00'),
        )
        alerta = Alerta.objects.create(
            entrada=entrada,
            tipo='ejecucion_fisica_baja',
            severidad='moderada',
            mensaje='Alerta por resolver',
            activa=True,
        )

        response = self.client.post(
            f'/api/v1/alertas/{alerta.id}/resolver/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerta.refresh_from_db()
        self.assertFalse(alerta.activa)
        self.assertIsNotNone(alerta.resuelta_en)

    def test_umbral_configuracion(self):
        umbral_data = {
            'tipo_umbral': 'ejecucion_fisica_baja',
            'porcentaje_minimo': '30.00',
            'porcentaje_maximo': '100.00',
            'activo': True,
            'descripcion': 'Umbral de ejecución física baja',
        }
        response = self.client.post(
            '/api/v1/umbrales/',
            umbral_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_calcular_eficacia_fisica(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-EF',
            nombre='POAU Eficacia',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-EF-001',
            nombre='Actividad eficacia',
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            programado_fisico=Decimal('200.0000'),
            ejecutado_fisico=Decimal('150.0000'),
        )
        eficacia = calcular_eficacia_fisica(entrada)
        self.assertEqual(eficacia, Decimal('75'))

    def test_calcular_ejecucion_financiera(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-EF2',
            nombre='POAU Ejecución Financiera',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-EF2-001',
            nombre='Actividad ejecución financiera',
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            programado_financiero=Decimal('100000.00'),
            ejecutado_financiero=Decimal('80000.00'),
        )
        ejecucion = calcular_ejecucion_financiera(entrada)
        self.assertEqual(ejecucion, Decimal('80'))

    def test_desviacion_calculo(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-DES',
            nombre='POAU Desviación',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-DES-001',
            nombre='Actividad desviación',
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            programado_fisico=Decimal('100.0000'),
            ejecutado_fisico=Decimal('120.0000'),
        )
        desviacion = calcular_desviacion(entrada)
        self.assertEqual(desviacion, Decimal('20'))

    def test_proyeccion_cierre(self):
        from apps.poau.models import POAU, POAUActividad

        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-PROY',
            nombre='POAU Proyección',
        )
        actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-PROY-001',
            nombre='Actividad proyección',
        )
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=actividad,
            porcentaje_avance_fisico=Decimal('40.00'),
            porcentaje_avance_financiero=Decimal('35.00'),
        )
        proyeccion = calcular_proyeccion_cierre(entrada)
        self.assertIn('proyeccion_fisica', proyeccion)
        self.assertIn('proyeccion_financiera', proyeccion)
        self.assertIn('dias_transcurridos', proyeccion)
        self.assertIn('dias_totales', proyeccion)
        self.assertGreaterEqual(proyeccion['dias_totales'], 365)

    def test_listar_sin_autenticacion_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/reportes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(
            '/api/v1/reportes/',
            self.reporte_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AlertaModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.poau.models import POAU, POAUActividad

        tipo = TipoUnidad.objects.create(
            codigo='AL-T', nombre='Alerta Tipo', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='U-AL', nombre='Unidad Alerta', tipo=tipo, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        self.reporte = ReporteSeguimiento.objects.create(
            gestion=2026,
            periodo='2026-Q1',
            unidad_organizacional=self.unidad,
        )
        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-ALM',
            nombre='POAU Modelo',
        )
        self.actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-ALM-001',
            nombre='Actividad modelo alerta',
        )
        self.entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=self.actividad,
            porcentaje_avance_fisico=Decimal('10.00'),
        )

    def test_alerta_str(self):
        alerta = Alerta.objects.create(
            entrada=self.entrada,
            tipo='ejecucion_fisica_baja',
            severidad='grave',
            mensaje='Ejecución física muy baja',
        )
        s = str(alerta)
        self.assertIn('Grave', s)

    def test_alerta_resuelta(self):
        alerta = Alerta.objects.create(
            entrada=self.entrada,
            tipo='sin_evidencia',
            severidad='leve',
            mensaje='Sin evidencia',
        )
        self.assertTrue(alerta.activa)
        self.assertIsNone(alerta.resuelta_en)


class UmbralConfiguracionModelTests(TestCase):

    def test_umbral_str(self):
        umbral = UmbralConfiguracion.objects.create(
            tipo_umbral='ejecucion_fisica_baja',
            porcentaje_minimo=Decimal('30.00'),
            porcentaje_maximo=Decimal('100.00'),
            descripcion='Umbral de prueba',
        )
        s = str(umbral)
        self.assertIn('30.00', s)

    def test_umbral_unique(self):
        UmbralConfiguracion.objects.create(
            tipo_umbral='sobreejecucion',
            porcentaje_minimo=Decimal('100.00'),
        )
        with self.assertRaises(Exception):
            UmbralConfiguracion.objects.create(
                tipo_umbral='sobreejecucion',
                porcentaje_minimo=Decimal('90.00'),
            )


class EntradaSeguimientoModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.poau.models import POAU, POAUActividad

        tipo = TipoUnidad.objects.create(
            codigo='ENT-T', nombre='Entrada Tipo', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='U-ENT', nombre='Unidad Entrada', tipo=tipo, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        self.reporte = ReporteSeguimiento.objects.create(
            gestion=2026,
            periodo='2026-Q1',
            unidad_organizacional=self.unidad,
        )
        poau = POAU.objects.create(
            unidad=self.unidad,
            gestion=2026,
            codigo='POAU-ENT-M',
            nombre='POAU Entrada Modelo',
        )
        self.actividad = POAUActividad.objects.create(
            poau=poau,
            codigo='ACT-ENT-M-001',
            nombre='Actividad entrada modelo',
        )

    def test_entrada_str(self):
        entrada = EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=self.actividad,
            porcentaje_avance_fisico=Decimal('50.00'),
        )
        s = str(entrada)
        self.assertIn('ACT-ENT-M-001', s)

    def test_entrada_unique_together(self):
        EntradaSeguimiento.objects.create(
            reporte=self.reporte,
            actividad=self.actividad,
        )
        with self.assertRaises(Exception):
            EntradaSeguimiento.objects.create(
                reporte=self.reporte,
                actividad=self.actividad,
            )
