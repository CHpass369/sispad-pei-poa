import os
from io import BytesIO
from unittest.mock import patch

import openpyxl
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from scripts.seed import DEMO_PASSWORD_ENV


TEST_DEMO_PASSWORDS = {
    env_name: f'test-only-{account}-credential'
    for account, env_name in DEMO_PASSWORD_ENV.items()
}


@patch.dict(os.environ, TEST_DEMO_PASSWORDS, clear=False)
class MatrizCompletaXlsxIntegrationTest(TestCase):
    def test_authenticated_endpoint_returns_readable_workbook(self):
        from scripts.seed import seed_demo_data

        seed_demo_data()
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.get(email='admin@demo.sispoa.local')
        )

        response = client.get(
            '/api/v1/reportes/matriz_completa_xlsx/',
            {'gestion': 2026},
            HTTP_HOST='localhost',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        workbook = openpyxl.load_workbook(BytesIO(response.content), read_only=True)
        worksheet = workbook['Matriz Articulación Completa']
        headers = [cell.value for cell in next(worksheet.iter_rows(min_row=4, max_row=4))]
        self.assertEqual(
            headers,
            [
                'Código Completo',
                'Nivel',
                'Nombre',
                'Plan',
                'Código Padre',
                'Nodos Vinculados',
            ],
        )
        self.assertGreater(worksheet.max_row, 4)
        workbook.close()

        client.force_authenticate(
            user=get_user_model().objects.get(email='auditor@demo.sispoa.local')
        )
        denied_response = client.get(
            '/api/v1/reportes/matriz_completa_xlsx/',
            {'gestion': 2026},
            HTTP_HOST='localhost',
        )
        self.assertEqual(denied_response.status_code, 403)
