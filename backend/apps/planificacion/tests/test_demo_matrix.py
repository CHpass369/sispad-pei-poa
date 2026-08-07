import io

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.tests.demo_source_fixture import DemoSourceWorkbookMixin


def flatten_matrix(nodes):
    flattened = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(flatten_matrix(node.get('hijos', [])))
        flattened.extend(flatten_matrix(node.get('articulaciones', [])))
    return flattened


class DemoMatrizCompletaTests(DemoSourceWorkbookMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command(
            'cargar_demo_articuladores',
            '--commit',
            '--refresh',
            '--source-file',
            str(cls.source_file),
            stdout=io.StringIO(),
        )
        cls.admin = get_user_model().objects.create_superuser(
            email='matrix-2027-admin@example.invalid',
            password='test-only-password',
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_matrix_2027_returns_same_operational_chain_as_m3(self):
        response = self.client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2027},
        )
        m3 = self.client.get(
            '/api/v1/articulacion/matrices/m3_poa_poau/',
            {'gestion': 2027},
        ).json()[0]

        self.assertEqual(response.status_code, 200)
        nodes = flatten_matrix(response.json()['data'])
        activity_nodes = [n for n in nodes if n.get('nivel') == 'actividad_poau']
        task_nodes = [n for n in nodes if n.get('nivel') == 'tarea_poau']
        self.assertEqual(len(activity_nodes), 19)
        self.assertEqual(len(task_nodes), 139)
        self.assertEqual(
            {n['codigo_completo'] for n in activity_nodes},
            {a['codigo_completo_articulacion'] for a in m3['actividades']},
        )
        self.assertEqual(
            {n['nombre'] for n in task_nodes},
            {t['denominacion'] for a in m3['actividades'] for t in a['tareas']},
        )

    def test_matrix_2026_no_longer_exposes_previous_manifest_demo(self):
        response = self.client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2026},
        )

        self.assertEqual(response.status_code, 200)
        nodes = flatten_matrix(response.json()['data'])
        self.assertFalse(any(
            'Demostración provisional articuladores' in node.get('nombre', '')
            for node in nodes
        ))

    def test_unknown_management_returns_the_exact_empty_contract(self):
        response = self.client.get(
            '/api/v1/planificacion/matriz-completa/',
            {'gestion': 2099},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': [], 'stats': {'total': 0}})
