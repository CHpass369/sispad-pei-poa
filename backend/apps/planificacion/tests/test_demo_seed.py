import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from scripts.seed import DEMO_PASSWORD_ENV, _load_demo_passwords

from apps.articulacion.models import (
    AcuerdoInternacional,
    ArticulacionPADPEI,
    CodigoNivel,
    LineamientoPAD,
    ProductoPAD,
    ResultadoPAD,
    ResultadoPEI,
    ProductoPEI,
    AccionPOA,
)
from apps.catalogos.models import FuenteFinanciamiento
from apps.gestion.models import GestionFiscal
from apps.pad.models import SectorPAD
from apps.planificacion.models import NodoPlanificacion, Plan
from apps.poau.models import POAU, POAUActividad
from apps.seguimiento.models import EntradaSeguimiento, ReporteSeguimiento


def _walk_matrix(nodes):
    for node in nodes:
        yield node
        yield from _walk_matrix(node.get('hijos', []))
        for articulation in node.get('articulaciones', []):
            yield articulation
            yield from _walk_matrix(articulation.get('hijos', []))


TEST_DEMO_PASSWORDS = {
    env_name: f'test-only-{account}-credential'
    for account, env_name in DEMO_PASSWORD_ENV.items()
}


class DemoSeedCredentialConfigTest(SimpleTestCase):
    def test_loads_every_explicit_demo_credential(self):
        with patch.dict(os.environ, TEST_DEMO_PASSWORDS, clear=True):
            credentials = _load_demo_passwords()

        self.assertEqual(set(credentials), set(DEMO_PASSWORD_ENV))
        self.assertEqual(credentials['admin'], TEST_DEMO_PASSWORDS[DEMO_PASSWORD_ENV['admin']])

    def test_rejects_missing_demo_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'SISPOA_DEMO_ADMIN_PASSWORD'):
                _load_demo_passwords()


@patch.dict(os.environ, TEST_DEMO_PASSWORDS, clear=False)
class DemoSeedTest(TestCase):
    def test_seed_builds_complete_chain_and_is_idempotent(self):
        from scripts.seed import seed_demo_data

        seed_demo_data()
        counts_after_first_run = self._counts()
        codes_after_first_run = self._codes()

        seed_demo_data()

        self.assertEqual(self._counts(), counts_after_first_run)
        self.assertEqual(self._codes(), codes_after_first_run)
        self.assertEqual(GestionFiscal.objects.get(anio=2026).estado, 'abierta')
        self.assertEqual(
            SectorPAD.objects.filter(
                codigo__in=[f'{index:02d}' for index in range(1, 21)]
            ).count(),
            20,
        )
        self.assertEqual(
            AcuerdoInternacional.objects.filter(
                tipo_acuerdo='ODS', codigo__in=[f'{index:02d}' for index in range(1, 18)]
            ).count(),
            17,
        )
        self.assertEqual(
            CodigoNivel.objects.get(nivel='Resultado PAD').segmentos,
            'CGEO.LL.RR',
        )
        self.assertEqual(
            ResultadoPAD.objects.filter(codigo_resultado__startswith='031001.').count(),
            60,
        )
        self.assertEqual(
            ResultadoPAD.objects.filter(
                codigo_resultado__regex=r'^031001\.[0-9]{2}\.[0-9]{2}$'
            ).count(),
            60,
        )
        self.assertEqual(ProductoPAD.objects.count(), 120)
        self.assertEqual(ResultadoPAD.objects.filter(nodo_pdesa__isnull=True).count(), 0)
        self.assertEqual(ArticulacionPADPEI.objects.count(), 120)
        self.assertEqual(POAUActividad.objects.count(), POAU.objects.count())
        self.assertGreater(EntradaSeguimiento.objects.count(), 0)
        self.assertGreater(ReporteSeguimiento.objects.count(), 0)
        self.assertEqual(Plan.objects.filter(tipo='pgdesa').count(), 1)
        self.assertEqual(Plan.objects.filter(tipo='pdesa').count(), 1)
        self.assertGreaterEqual(NodoPlanificacion.objects.filter(nivel='eje').count(), 7)
        self.assertGreaterEqual(NodoPlanificacion.objects.filter(nivel='componente').count(), 24)
        self.assertGreater(FuenteFinanciamiento.objects.count(), 0)

        self.assertEqual(counts_after_first_run['pgdesa_nodes'], 70)
        self.assertEqual(counts_after_first_run['pdesa_nodes'], 84)
        self.assertEqual(counts_after_first_run['resultados_pad'], 60)
        self.assertEqual(counts_after_first_run['productos_pad'], 120)
        self.assertEqual(counts_after_first_run['resultados_pei'], 20)
        self.assertEqual(counts_after_first_run['productos_pei'], 60)
        self.assertEqual(counts_after_first_run['acciones_poa'], 60)
        self.assertIn('01', codes_after_first_run['pgdesa'])
        self.assertIn('01.01', codes_after_first_run['pgdesa'])
        self.assertIn('01.01.01', codes_after_first_run['pgdesa'])
        self.assertEqual(len(codes_after_first_run['pgdesa']), 70)
        self.assertEqual(len(codes_after_first_run['pdesa']), 84)
        self.assertEqual(len(codes_after_first_run['resultado_pad']), 60)

    def test_seed_preserves_non_demo_users_and_sets_demo_passwords(self):
        from scripts.seed import seed_demo_data

        user_model = get_user_model()
        external = user_model.objects.create_user(
            email='existing@municipio.test', password='unchanged-password'
        )

        seed_demo_data()

        external.refresh_from_db()
        self.assertTrue(external.check_password('unchanged-password'))
        self.assertEqual(
            user_model.objects.filter(email__endswith='@demo.sispoa.local').count(),
            7,
        )
        self.assertTrue(
            user_model.objects.get(email='admin@demo.sispoa.local').check_password(
                TEST_DEMO_PASSWORDS[DEMO_PASSWORD_ENV['admin']]
            )
        )

    def test_frontend_matrix_route_returns_seeded_tree(self):
        from scripts.seed import seed_demo_data

        seed_demo_data()
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )

        response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2026},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 7)
        self.assertEqual(response.data['data'][0]['tipo_plan'], 'pgdesa')
        self.assertEqual(response.data['data'][0]['codigo_completo'], '01')
        self.assertEqual(
            response.data['data'][0]['hijos'][0]['codigo_completo'],
            '01.01',
        )
        self.assertEqual(
            response.data['data'][0]['hijos'][0]['hijos'][0]['codigo_completo'],
            '01.01.01',
        )

        matrix_nodes = list(_walk_matrix(response.data['data']))
        self.assertTrue(any(node.get('codigo_resultado') for node in matrix_nodes))
        self.assertTrue(any(node.get('tipo') == 'producto_pad' for node in matrix_nodes))
        self.assertTrue(any(node.get('tipo') == 'producto_pei' for node in matrix_nodes))
        self.assertTrue(any(node.get('tipo') == 'accion_poa' for node in matrix_nodes))

        resultado_pad = next(
            node for node in matrix_nodes if node.get('resultado_pad_id')
        )
        self.assertTrue(resultado_pad.get('codigo_resultado'))
        self.assertTrue(resultado_pad.get('resultado_pad_id'))
        self.assertTrue(resultado_pad.get('lineamiento_pad'))
        self.assertTrue(resultado_pad.get('sector'))
        self.assertTrue(resultado_pad.get('ods'))

        producto_pad = next(
            node for node in resultado_pad['hijos']
            if node.get('tipo') == 'producto_pad'
        )
        producto_pei = next(
            node for node in _walk_matrix(resultado_pad['hijos'])
            if node.get('tipo') == 'producto_pei'
        )
        accion_poa = next(
            node for node in _walk_matrix(resultado_pad['hijos'])
            if node.get('tipo') == 'accion_poa'
        )
        self.assertTrue(resultado_pad['codigo_resultado'])
        self.assertTrue(resultado_pad['denominacion'])
        self.assertTrue(producto_pad['codigo_producto'])
        self.assertTrue(producto_pad['denominacion'])
        self.assertTrue(producto_pei['codigo_producto'])
        self.assertTrue(producto_pei['denominacion'])
        self.assertTrue(accion_poa['codigo_accion'])
        self.assertTrue(accion_poa['denominacion'])

        lazy_response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2026, 'nivel': 'eje'},
            HTTP_HOST='localhost',
        )
        self.assertEqual(lazy_response.status_code, 200)
        self.assertEqual(len(lazy_response.data['data']), 7)
        self.assertTrue(
            all(
                node.get('children_url') and node.get('hijos') == []
                for node in lazy_response.data['data']
            )
        )

        children_response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {
                'gestion': 2026,
                'padre_id': lazy_response.data['data'][0]['id'],
                'nivel': 'meta',
            },
            HTTP_HOST='localhost',
        )
        self.assertEqual(children_response.status_code, 200)
        self.assertEqual(
            {node['nivel'] for node in children_response.data['data']},
            {'meta'},
        )

        client.force_authenticate(
            user=get_user_model().objects.get(email='auditor@demo.sispoa.local')
        )
        denied_response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2026},
            HTTP_HOST='localhost',
        )
        self.assertEqual(denied_response.status_code, 403)

    def test_matrix_serializer_omits_null_bridge_without_breaking_tree(self):
        from scripts.seed import seed_demo_data

        seed_demo_data()
        result = ResultadoPAD.objects.filter(nodo_pdesa__isnull=False).first()
        self.assertIsNotNone(result)
        pdesa_action = result.nodo_pdesa
        result.nodo_pdesa = None
        result.save(update_fields=['nodo_pdesa'])

        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )
        response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2026},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        matrix_nodes = list(_walk_matrix(response.data['data']))
        action_node = next(
            node for node in matrix_nodes if node.get('id') == str(pdesa_action.id)
        )
        self.assertEqual(action_node['articulaciones'], [])
        self.assertNotIn(
            str(result.id),
            {node.get('resultado_pad_id') for node in matrix_nodes},
        )

    def test_matrix_route_returns_empty_for_unknown_management(self):
        from scripts.seed import seed_demo_data

        seed_demo_data()
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )

        response = client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2099},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'data': [], 'stats': {'total': 0}})

    def _counts(self):
        return {
            'users': get_user_model().objects.count(),
            'plans': Plan.objects.count(),
            'pgdesa_nodes': NodoPlanificacion.objects.filter(plan__tipo='pgdesa').count(),
            'pdesa_nodes': NodoPlanificacion.objects.filter(plan__tipo='pdesa').count(),
            'lineamientos': LineamientoPAD.objects.count(),
            'resultados_pad': ResultadoPAD.objects.count(),
            'productos_pad': ProductoPAD.objects.count(),
            'resultados_pei': ResultadoPEI.objects.count(),
            'productos_pei': ProductoPEI.objects.count(),
            'acciones_poa': AccionPOA.objects.count(),
            'poaus': POAU.objects.count(),
            'reportes': ReporteSeguimiento.objects.count(),
            'entradas': EntradaSeguimiento.objects.count(),
        }

    def _codes(self):
        return {
            'pgdesa': list(
                NodoPlanificacion.objects.filter(plan__tipo='pgdesa')
                .order_by('nivel', 'codigo')
                .values_list('codigo', flat=True)
            ),
            'pdesa': list(
                NodoPlanificacion.objects.filter(plan__tipo='pdesa')
                .order_by('nivel', 'codigo')
                .values_list('codigo', flat=True)
            ),
            'resultado_pad': list(
                ResultadoPAD.objects.order_by('codigo_resultado')
                .values_list('codigo_resultado', flat=True)
            ),
        }
