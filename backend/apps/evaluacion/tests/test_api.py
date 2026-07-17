import uuid
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario
from apps.evaluacion.models import (
    Evaluacion, CriterioEvaluacion, ResultadoEvaluacion,
    LeccionAprendida, Recomendacion,
)
from apps.evaluacion.services import calcular_score_global


TEST数据库配置 = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'test_evaluacion',
        'USER': 'test',
        'PASSWORD': 'test',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


class EvaluacionViewSetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            email='evaluador@test.com',
            password='Test1234!',
            first_name='Evaluador',
            last_name='Test',
        )
        self.admin_user = Usuario.objects.create_superuser(
            email='admin@test.com',
            password='Admin1234!',
        )
        self.client.force_authenticate(user=self.user)

        from apps.planificacion.models import Plan
        self.plan = Plan.objects.create(
            codigo='PEI-001',
            nombre='Plan Estratégico Institucional 2025-2030',
            tipo='pei',
            gestion_inicio=2025,
            gestion_fin=2030,
            fecha_vigencia_desde=date(2025, 1, 1),
        )

        self.evaluacion_data = {
            'plan': str(self.plan.id),
            'fiscal_year': 2026,
            'evaluation_type': 'anual',
            'period': 'AN',
            'responsible_team': 'Equipo de Evaluación',
            'conclusions': 'Resultados satisfactorios',
            'recommendations': 'Fortalecer seguimiento',
        }

        self.evaluacion = Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2026,
            evaluation_type='anual',
            period='AN',
            status='borrador',
            responsible_team='Equipo Test',
        )

    def test_crear_evaluacion(self):
        response = self.client.post(
            '/api/v1/evaluaciones/',
            self.evaluacion_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Evaluacion.objects.count(), 2)
        self.assertEqual(
            Evaluacion.objects.get(id=response.data['id']).evaluation_type,
            'anual',
        )

    def test_listar_evaluaciones(self):
        response = self.client.get('/api/v1/evaluaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_obtener_evaluacion_por_id(self):
        response = self.client.get(f'/api/v1/evaluaciones/{self.evaluacion.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['evaluation_type'],
            self.evaluacion.evaluation_type,
        )
        self.assertEqual(response.data['fiscal_year'], 2026)

    def test_actualizar_evaluacion(self):
        update_data = {
            'status': 'en_curso',
            'conclusions': 'Conclusiones actualizadas',
        }
        response = self.client.patch(
            f'/api/v1/evaluaciones/{self.evaluacion.id}/',
            update_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.evaluacion.refresh_from_db()
        self.assertEqual(self.evaluacion.status, 'en_curso')
        self.assertEqual(self.evaluacion.conclusions, 'Conclusiones actualizadas')

    def test_eliminar_evaluacion(self):
        evaluacion_id = self.evaluacion.id
        response = self.client.delete(f'/api/v1/evaluaciones/{evaluacion_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Evaluacion.objects.filter(id=evaluacion_id).exists())

    def test_agregar_criterio_evaluacion(self):
        criterio_data = {
            'evaluacion': str(self.evaluacion.id),
            'criterion': 'eficacia',
            'score': '85.00',
            'weight': '0.20',
            'justification': 'Buen cumplimiento de objetivos',
        }
        response = self.client.post(
            '/api/v1/criterios-evaluacion/',
            criterio_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CriterioEvaluacion.objects.filter(
                evaluacion=self.evaluacion,
            ).count(),
            1,
        )

    def test_generar_resultados(self):
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.poau.models import POAU

        tipo_unidad = TipoUnidad.objects.create(
            codigo='DIR',
            nombre='Dirección',
            nivel=1,
        )
        unidad = UnidadOrganizacional.objects.create(
            codigo='U001',
            nombre='Unidad Test',
            tipo=tipo_unidad,
            gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        poau = POAU.objects.create(
            unidad=unidad,
            gestion=2026,
            codigo='POAU-001',
            nombre='POAU de prueba',
        )

        resultado = ResultadoEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            poau=poau,
            unidad=unidad,
            score_global=Decimal('72.50'),
            status='parcial',
        )
        response = self.client.get(
            f'/api/v1/evaluaciones/{self.evaluacion.id}/resultados/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('criterios', response.data)
        self.assertIn('resultados_poau', response.data)
        self.assertIn('resumen', response.data)

    def test_calcular_score_global(self):
        CriterioEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterion='eficacia',
            score=Decimal('80.00'),
            weight=Decimal('0.20'),
        )
        CriterioEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterion='eficiencia',
            score=Decimal('70.00'),
            weight=Decimal('0.15'),
        )
        score = calcular_score_global(self.evaluacion)
        self.assertGreater(score, Decimal('0.00'))
        self.assertLessEqual(score, Decimal('100.00'))

    def test_evaluar_por_poau(self):
        from apps.evaluacion.services import evaluar_por_poau
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.poau.models import POAU

        tipo_unidad = TipoUnidad.objects.create(
            codigo='UE',
            nombre='Unidad Ejecutora',
            nivel=2,
        )
        unidad = UnidadOrganizacional.objects.create(
            codigo='UE-01',
            nombre='Unidad Ejecutora Test',
            tipo=tipo_unidad,
            gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        POAU.objects.create(
            unidad=unidad,
            gestion=2026,
            codigo='POAU-EVAL-001',
            nombre='POAU para evaluación',
        )

        resultados = evaluar_por_poau(self.evaluacion)
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].poau.codigo, 'POAU-EVAL-001')
        self.assertIn(resultados[0].status, ['cumple', 'parcial', 'no_cumple'])

    def test_evaluar_por_unidad(self):
        from apps.evaluacion.services import evaluar_por_unidad
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.poau.models import POAU

        tipo_unidad = TipoUnidad.objects.create(
            codigo='SEC',
            nombre='Secretaría',
            nivel=1,
        )
        unidad = UnidadOrganizacional.objects.create(
            codigo='SEC-01',
            nombre='Secretaría Test',
            tipo=tipo_unidad,
            gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        POAU.objects.create(
            unidad=unidad,
            gestion=2026,
            codigo='POAU-UNI-001',
            nombre='POAU unidad test',
        )

        resultados = evaluar_por_unidad(self.evaluacion)
        self.assertGreaterEqual(len(resultados), 1)
        for r in resultados:
            self.assertIsNotNone(r.unidad)
            self.assertIn(r.status, ['cumple', 'parcial', 'no_cumple'])

    def test_evaluar_institucional(self):
        from apps.evaluacion.services import evaluar_institucional

        ResultadoEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            score_global=Decimal('80.00'),
            status='cumple',
        )
        ResultadoEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            score_global=Decimal('60.00'),
            status='parcial',
        )

        CriterioEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterion='eficacia',
            score=Decimal('70.00'),
            weight=Decimal('0.20'),
        )

        resultado = evaluar_institucional(self.evaluacion)
        self.assertIn('score_institucional', resultado)
        self.assertIn('total_resultados', resultado)
        self.assertEqual(resultado['total_resultados'], 2)
        self.assertEqual(resultado['cumple'], 1)
        self.assertEqual(resultado['parcial'], 1)

    def test_leccion_aprendida_crear(self):
        leccion_data = {
            'evaluacion': str(self.evaluacion.id),
            'title': 'Lección sobre coordinación',
            'description': 'La coordinación interinstitucional fue clave',
            'category': 'organizacional',
            'recommendations': 'Mejorar canales de comunicación',
        }
        response = self.client.post(
            '/api/v1/lecciones-aprendidas/',
            leccion_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LeccionAprendida.objects.count(), 1)
        leccion = LeccionAprendida.objects.first()
        self.assertEqual(leccion.category, 'organizacional')

    def test_recomendacion_crear(self):
        rec_data = {
            'evaluacion': str(self.evaluacion.id),
            'description': 'Aumentar la inversión en infraestructura tecnológica',
            'priority': 'alta',
            'responsible_unit': 'Dirección de Tecnología',
            'status': 'pendiente',
        }
        response = self.client.post(
            '/api/v1/recomendaciones/',
            rec_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recomendacion.objects.count(), 1)
        rec = Recomendacion.objects.first()
        self.assertEqual(rec.priority, 'alta')
        self.assertEqual(rec.status, 'pendiente')

    def test_evaluacion_sin_criterios_score_cero(self):
        score = calcular_score_global(self.evaluacion)
        self.assertEqual(score, Decimal('0.00'))

    def test_score_rango_valido(self):
        for score_val, weight_val in [
            ('0.00', '1.00'),
            ('50.00', '0.50'),
            ('100.00', '0.30'),
        ]:
            CriterioEvaluacion.objects.create(
                evaluacion=self.evaluacion,
                criterion='eficacia',
                score=Decimal(score_val),
                weight=Decimal(weight_val),
            )

        score = calcular_score_global(self.evaluacion)
        self.assertGreaterEqual(score, Decimal('0.00'))
        self.assertLessEqual(score, Decimal('100.00'))

    def test_evaluacion_duplicada_error(self):
        response = self.client.post(
            '/api/v1/evaluaciones/',
            {
                'plan': str(self.plan.id),
                'fiscal_year': 2026,
                'evaluation_type': 'anual',
                'period': 'AN',
            },
            format='json',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED],
        )
        if response.status_code == status.HTTP_201_CREATED:
            response2 = self.client.post(
                '/api/v1/evaluaciones/',
                {
                    'plan': str(self.plan.id),
                    'fiscal_year': 2026,
                    'evaluation_type': 'anual',
                    'period': 'AN',
                },
                format='json',
            )
            self.assertEqual(
                response2.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

    def test_permiso_solo_evaluador(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/evaluaciones/')
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        regular_user = Usuario.objects.create_user(
            email='regular@test.com',
            password='Test1234!',
        )
        self.client.force_authenticate(user=regular_user)
        response = self.client.get('/api/v1/evaluaciones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_sin_autenticacion_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/evaluaciones/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(
            '/api/v1/evaluaciones/',
            self.evaluacion_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filtro_por_tipo(self):
        Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2025,
            evaluation_type='medio_termino',
            period='AN',
        )
        response = self.client.get(
            '/api/v1/evaluaciones/',
            {'evaluation_type': 'anual'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['evaluation_type'], 'anual')

    def test_filtro_por_periodo(self):
        Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2026,
            evaluation_type='final',
            period='S1',
        )
        response = self.client.get(
            '/api/v1/evaluaciones/',
            {'period': 'S1'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['period'], 'S1')


class CriterioEvaluacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.planificacion.models import Plan
        self.plan = Plan.objects.create(
            codigo='PEI-TEST',
            nombre='Plan Test',
            tipo='pei',
            gestion_inicio=2025,
            gestion_fin=2030,
            fecha_vigencia_desde=date(2025, 1, 1),
        )
        self.evaluacion = Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2026,
            evaluation_type='anual',
            period='AN',
        )

    def test_criterio_str(self):
        criterio = CriterioEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterion='eficacia',
            score=Decimal('85.50'),
            weight=Decimal('0.20'),
        )
        self.assertIn('85.50', str(criterio))

    def test_weighted_score_property(self):
        criterio = CriterioEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterion='eficiencia',
            score=Decimal('80.00'),
            weight=Decimal('0.15'),
        )
        expected = Decimal('80.00') * Decimal('0.15')
        self.assertEqual(criterio.weighted_score, expected)

    def test_criterio_unique_together(self):
        CriterioEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterion='impacto',
            score=Decimal('70.00'),
            weight=Decimal('0.15'),
        )
        with self.assertRaises(Exception):
            CriterioEvaluacion.objects.create(
                evaluacion=self.evaluacion,
                criterion='impacto',
                score=Decimal('90.00'),
                weight=Decimal('0.15'),
            )


class ResultadoEvaluacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.planificacion.models import Plan
        self.plan = Plan.objects.create(
            codigo='PEI-R',
            nombre='Plan Resultado Test',
            tipo='pei',
            gestion_inicio=2025,
            gestion_fin=2030,
            fecha_vigencia_desde=date(2025, 1, 1),
        )
        self.evaluacion = Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2026,
            evaluation_type='anual',
            period='AN',
        )

    def test_resultado_str_con_poau(self):
        from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
        from apps.poau.models import POAU

        tipo = TipoUnidad.objects.create(codigo='DIR2', nombre='Dir', nivel=1)
        unidad = UnidadOrganizacional.objects.create(
            codigo='U-R', nombre='Unidad R', tipo=tipo, gestion=2026,
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        poau = POAU.objects.create(
            unidad=unidad, gestion=2026, codigo='P-R', nombre='POAU R',
        )
        resultado = ResultadoEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            poau=poau,
            score_global=Decimal('82.00'),
            status='cumple',
        )
        s = str(resultado)
        self.assertIn('cumple', s.lower())

    def test_resultado_str_sin_referencia(self):
        resultado = ResultadoEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            score_global=Decimal('45.00'),
            status='no_cumple',
        )
        s = str(resultado)
        self.assertIn('Sin referencia', s)


class LeccionAprendidaModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.planificacion.models import Plan
        self.plan = Plan.objects.create(
            codigo='PEI-L',
            nombre='Plan Lecciones',
            tipo='pei',
            gestion_inicio=2025,
            gestion_fin=2030,
            fecha_vigencia_desde=date(2025, 1, 1),
        )
        self.evaluacion = Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2026,
            evaluation_type='anual',
            period='AN',
        )

    def test_leccion_str(self):
        leccion = LeccionAprendida.objects.create(
            evaluacion=self.evaluacion,
            title='Aprendizaje clave',
            description='Descripción detallada',
            category='tecnica',
        )
        s = str(leccion)
        self.assertIn('Aprendizaje clave', s)
        self.assertIn('Técnica', s)


class RecomendacionModelTests(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            password='Test1234!',
        )
        from apps.planificacion.models import Plan
        self.plan = Plan.objects.create(
            codigo='PEI-REC',
            nombre='Plan Recomendaciones',
            tipo='pei',
            gestion_inicio=2025,
            gestion_fin=2030,
            fecha_vigencia_desde=date(2025, 1, 1),
        )
        self.evaluacion = Evaluacion.objects.create(
            plan=self.plan,
            fiscal_year=2026,
            evaluation_type='anual',
            period='AN',
        )

    def test_recomendacion_str(self):
        rec = Recomendacion.objects.create(
            evaluacion=self.evaluacion,
            description='Mejorar procesos internos de planificación institucional',
            priority='media',
        )
        s = str(rec)
        self.assertIn('Mejorar procesos', s)
        self.assertIn('Media', s)
