from django.core import management
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase
from rest_framework.test import APIClient

from apps.articulacion.models import (
    AcuerdoInternacional,
    CompatibilidadAcuerdoInternacional,
)


class CompatibilidadModelTest(TestCase):
    def setUp(self):
        self.ods = AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='6.6', denominacion='Agua y ecosistemas',
        )
        self.ndc = AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDC', codigo='NDC-AGUA', denominacion='Adaptación hídrica',
        )
        self.ndt = AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDT', codigo='d.1.2',
            denominacion='Neutralidad de degradación de tierras',
        )

    def test_rejects_same_agreement_and_same_type(self):
        same_agreement = CompatibilidadAcuerdoInternacional(
            origen=self.ods,
            destino=self.ods,
            tipo_relacion='OFICIAL_EXPLICITA',
        )
        with self.assertRaises(ValidationError):
            same_agreement.full_clean()

        same_type = CompatibilidadAcuerdoInternacional(
            origen=self.ods,
            destino=AcuerdoInternacional.objects.create(
                tipo_acuerdo='ODS', codigo='6.7', denominacion='Otra meta',
            ),
            tipo_relacion='OFICIAL_EXPLICITA',
        )
        with self.assertRaises(ValidationError):
            same_type.full_clean()

    def test_unique_constraint_includes_source(self):
        values = dict(
            origen=self.ods,
            destino=self.ndc,
            tipo_relacion='SUGERENCIA_SEMANTICA',
            fuente_url='https://example.test/source-a',
        )
        CompatibilidadAcuerdoInternacional.objects.create(**values)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CompatibilidadAcuerdoInternacional.objects.bulk_create([
                    CompatibilidadAcuerdoInternacional(**values),
                ])

        CompatibilidadAcuerdoInternacional.objects.create(
            **{**values, 'fuente_url': 'https://example.test/source-b'},
        )
        self.assertEqual(CompatibilidadAcuerdoInternacional.objects.count(), 2)

    def test_different_types_are_valid(self):
        relation = CompatibilidadAcuerdoInternacional.objects.create(
            origen=self.ods,
            destino=self.ndt,
            tipo_relacion='DERIVADA_DOCUMENTAL',
            estado='VALIDADA',
            confianza='ALTA',
        )
        self.assertEqual(relation.origen.tipo_acuerdo, 'ODS')
        self.assertEqual(relation.destino.tipo_acuerdo, 'NDT')


class CompatibilidadApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self._create_user()
        self.ods = AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='6.6', denominacion='Agua',
        )
        self.ndc = AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDC', codigo='NDC-1', denominacion='Agua y clima',
        )
        self.ndt = AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDT', codigo='NDT-1', denominacion='Tierras',
        )
        self.oficial = CompatibilidadAcuerdoInternacional.objects.create(
            origen=self.ods,
            destino=self.ndc,
            tipo_relacion='OFICIAL_EXPLICITA',
            estado='VALIDADA',
            confianza='ALTA',
            fuente_url='https://example.test/official',
            evidencia='Fuente oficial',
        )
        self.sugerencia = CompatibilidadAcuerdoInternacional.objects.create(
            origen=self.ods,
            destino=self.ndt,
            tipo_relacion='SUGERENCIA_SEMANTICA',
            estado='CANDIDATA',
            confianza='BAJA',
            evidencia='Coincidencia textual: tierra',
        )
        self.rechazada = CompatibilidadAcuerdoInternacional.objects.create(
            origen=self.ods,
            destino=AcuerdoInternacional.objects.create(
                tipo_acuerdo='NDC', codigo='NDC-RECH', denominacion='No usar',
            ),
            tipo_relacion='OFICIAL_EXPLICITA',
            estado='RECHAZADA',
            confianza='ALTA',
            fuente_url='https://example.test/rejected',
        )
        self.client.force_authenticate(user=self.user)

    def _create_user(self):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.create_user(
            email='compatibilidad@test.com', password='test123',
        )

    def _results(self, response):
        return response.data.get('results', response.data)

    def test_filters_by_origin_and_destination_type_and_excludes_rejected(self):
        response = self.client.get(
            '/api/v2/integracion/compatibilidades/',
            {'origen_id': self.ods.id, 'destino_tipo': 'NDC'},
        )
        self.assertEqual(response.status_code, 200)
        results = self._results(response)
        self.assertEqual([item['id'] for item in results], [str(self.oficial.id)])
        self.assertEqual(results[0]['origen']['codigo'], '6.6')
        self.assertEqual(results[0]['destino']['codigo'], 'NDC-1')
        self.assertEqual(results[0]['tipo_relacion'], 'OFICIAL_EXPLICITA')
        self.assertEqual(results[0]['evidencia'], 'Fuente oficial')

    def test_suggestions_are_included_by_default_and_can_be_excluded(self):
        response = self.client.get(
            '/api/v2/integracion/compatibilidades/',
            {'origen_id': self.ods.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item['tipo_relacion'] for item in self._results(response)},
            {'OFICIAL_EXPLICITA', 'SUGERENCIA_SEMANTICA'},
        )

        response = self.client.get(
            '/api/v2/integracion/compatibilidades/',
            {'origen_id': self.ods.id, 'incluir_sugerencias': 'false'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item['tipo_relacion'] for item in self._results(response)},
            {'OFICIAL_EXPLICITA'},
        )

    def test_multiple_origins_use_conservative_intersection(self):
        second_ods = AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='15.3', denominacion='Tierra',
        )
        CompatibilidadAcuerdoInternacional.objects.create(
            origen=second_ods,
            destino=self.ndc,
            tipo_relacion='OFICIAL_EXPLICITA',
            estado='VALIDADA',
            confianza='ALTA',
            fuente_url='https://example.test/second',
        )
        response = self.client.get(
            '/api/v2/integracion/compatibilidades/',
            {'origen_ids': f'{self.ods.id},{second_ods.id}', 'destino_tipo': 'NDC'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self._results(response)), 2)
        self.assertEqual(
            {item['destino']['codigo'] for item in self._results(response)},
            {'NDC-1'},
        )


class CompatibilidadSeedTest(TestCase):
    def setUp(self):
        for code in ('6.6', '14.2', '15.1', '15.3', '11.4', '14.5', '15.4', '13.1', '13.2', '14.3', '11.7', '11.b', '15.9'):
            AcuerdoInternacional.objects.create(
                tipo_acuerdo='ODS', codigo=code, denominacion=f'ODS {code}',
            )
        for code in ('2', '3', '8', '12', '14'):
            AcuerdoInternacional.objects.create(
                tipo_acuerdo='COMPROMISO_3030', codigo=code, denominacion=f'Target {code}',
            )
        AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDT', codigo='d.1.2',
            denominacion='Neutralidad de degradación de tierras',
        )
        AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDC', codigo='NDC-1', denominacion='Agua y clima',
        )

    def test_seed_is_idempotent_and_creates_official_relations(self):
        management.call_command('sembrar_compatibilidades_acuerdos')
        first_count = CompatibilidadAcuerdoInternacional.objects.count()
        official_count = CompatibilidadAcuerdoInternacional.objects.filter(
            tipo_relacion='OFICIAL_EXPLICITA',
        ).count()
        self.assertEqual(official_count, 14)
        self.assertGreater(first_count, official_count)

        management.call_command('sembrar_compatibilidades_acuerdos')
        self.assertEqual(CompatibilidadAcuerdoInternacional.objects.count(), first_count)

    def test_seed_uses_exact_meta_before_parent_goal(self):
        exact_meta = AcuerdoInternacional.objects.get(tipo_acuerdo='ODS', codigo='6.6')
        AcuerdoInternacional.objects.filter(tipo_acuerdo='ODS', codigo='14.2').delete()
        parent_goal = AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='14', denominacion='ODS 14',
        )
        management.call_command('sembrar_compatibilidades_acuerdos')

        exact_relation = CompatibilidadAcuerdoInternacional.objects.get(
            origen=exact_meta,
            destino__tipo_acuerdo='COMPROMISO_3030',
            destino__codigo='2',
        )
        self.assertEqual(exact_relation.tipo_relacion, 'OFICIAL_EXPLICITA')
        self.assertEqual(exact_relation.estado, 'VALIDADA')
        self.assertEqual(exact_relation.confianza, 'ALTA')
        self.assertNotIn('proyectada', exact_relation.evidencia)

        fallback_relation = CompatibilidadAcuerdoInternacional.objects.get(
            origen=parent_goal,
            destino__tipo_acuerdo='COMPROMISO_3030',
            destino__codigo='2',
            tipo_relacion='DERIVADA_DOCUMENTAL',
        )
        self.assertEqual(fallback_relation.estado, 'CANDIDATA')
        self.assertEqual(fallback_relation.confianza, 'MEDIA')
        self.assertIn('meta ODS 14.2', fallback_relation.localizador)
        self.assertIn('objetivo ODS 14', fallback_relation.localizador)
        self.assertIn('meta ODS 14.2', fallback_relation.evidencia)
        self.assertNotEqual(fallback_relation.tipo_relacion, 'OFICIAL_EXPLICITA')

    def test_seed_uses_target_specific_cbd_sources(self):
        management.call_command('sembrar_compatibilidades_acuerdos')

        target_12 = CompatibilidadAcuerdoInternacional.objects.get(
            origen__codigo='11.7', destino__codigo='12',
        )
        self.assertEqual(target_12.fuente_url, 'https://www.cbd.int/gbf/targets/12/')
        self.assertIn('Target 12', target_12.localizador)
        self.assertIn('Target 12', target_12.evidencia)

        target_14 = CompatibilidadAcuerdoInternacional.objects.get(
            origen__codigo='15.9', destino__codigo='14',
        )
        self.assertEqual(target_14.fuente_url, 'https://www.cbd.int/gbf/targets/14/')
        self.assertIn('Target 14', target_14.localizador)
        self.assertIn('Target 14', target_14.evidencia)

    def test_seed_does_not_fallback_ods_target_for_ldn_ndt(self):
        AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='15', denominacion='ODS 15',
        )
        AcuerdoInternacional.objects.filter(tipo_acuerdo='ODS', codigo='15.3').delete()
        management.call_command('sembrar_compatibilidades_acuerdos')

        self.assertFalse(
            CompatibilidadAcuerdoInternacional.objects.filter(
                origen__codigo='15',
                destino__tipo_acuerdo='NDT',
                tipo_relacion='DERIVADA_DOCUMENTAL',
            ).exists()
        )
