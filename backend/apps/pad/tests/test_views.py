from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.pad.models import (
    ProgramacionAnualPAD, ResultadoTerritorial, ProductoTerritorial,
    LineamientoEstrategico, SectorPAD, PoliticaPAD,
)

API_PREFIX = '/api/v1/pad/'


class ProgramacionAnualPADViewSetTest(TestCase):
    """Tests del ViewSet ProgramacionAnualPAD"""

    def setUp(self):
        self.client = APIClient()
        # Forzar autenticación sin crear usuario real (los viewsets requieren auth)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.politica = PoliticaPAD.objects.create(
            codigo='P1', nombre='Política 1', gestion=2026
        )
        self.sector = SectorPAD.objects.create(
            codigo='S01', nombre='Salud'
        )
        self.lineamiento = LineamientoEstrategico.objects.create(
            codigo='L1', nombre='Lineamiento 1',
            politica=self.politica, gestion=2026
        )
        self.resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado 1',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=2026
        )
        self.producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026
        )
        self.prog_fisica = ProgramacionAnualPAD.objects.create(
            resultado=self.resultado,
            anio=2026, tipo='fisica', valor=100.5000
        )
        self.prog_financiera = ProgramacionAnualPAD.objects.create(
            resultado=self.resultado,
            anio=2026, tipo='financiera', valor=50000.0000
        )

    def _result_count(self, response):
        """Obtener cantidad de resultados de respuesta paginada"""
        if isinstance(response.data, list):
            return len(response.data)
        return response.data.get('count', 0)

    def _results(self, response):
        """Obtener resultados de respuesta paginada"""
        if isinstance(response.data, list):
            return response.data
        return response.data.get('results', [])

    def test_list_programaciones(self):
        """GET lista programaciones"""
        url = f'{API_PREFIX}programaciones-anuales/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._result_count(response), 2)

    def test_create_programacion(self):
        """POST crear programación"""
        url = f'{API_PREFIX}programaciones-anuales/'
        data = {
            'resultado': self.resultado.id,
            'anio': 2027, 'tipo': 'fisica', 'valor': 200.0000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProgramacionAnualPAD.objects.count(), 3)

    def test_create_programacion_sin_fk_rechazado(self):
        """POST sin resultado ni producto retorna 400"""
        url = f'{API_PREFIX}programaciones-anuales/'
        data = {
            'anio': 2027, 'tipo': 'fisica', 'valor': 200
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_por_anio(self):
        """GET con ?anio=2026 filtra correctamente"""
        url = f'{API_PREFIX}programaciones-anuales/?anio=2026'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._result_count(response), 2)

    def test_filter_por_tipo(self):
        """GET con ?tipo=fisica filtra correctamente"""
        url = f'{API_PREFIX}programaciones-anuales/?tipo=fisica'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._result_count(response), 1)
        results = self._results(response)
        self.assertEqual(results[0]['tipo'], 'fisica')

    def test_filter_por_resultado(self):
        """GET con ?resultado=ID filtra correctamente"""
        url = f'{API_PREFIX}programaciones-anuales/?resultado={self.resultado.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._result_count(response), 2)

    def test_destroy_programacion(self):
        """DELETE elimina programación"""
        url = f'{API_PREFIX}programaciones-anuales/{self.prog_fisica.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProgramacionAnualPAD.objects.count(), 1)

    def test_create_resultado_con_programaciones_api(self):
        """POST resultado territorial con programaciones anidadas"""
        url = f'{API_PREFIX}resultados-territoriales/'
        data = {
            'codigo': 'R02',
            'nombre': 'Resultado nuevo con prog',
            'lineamiento': self.lineamiento.id,
            'sector': self.sector.id,
            'gestion': 2026,
            'cod_geografico': '1102',
            'programaciones': [
                {'anio': 2026, 'tipo': 'fisica', 'valor': 50.0000},
                {'anio': 2027, 'tipo': 'fisica', 'valor': 75.0000},
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            msg=getattr(response, 'data', 'error')
        )
        # programaciones es write_only, verificar via DB
        resultado_id = response.data['id']
        self.assertEqual(
            ProgramacionAnualPAD.objects.filter(
                resultado_id=resultado_id
            ).count(),
            2
        )
