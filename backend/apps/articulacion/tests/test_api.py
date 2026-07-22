from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.articulacion.models import (
    ResultadoPAD, AccionPOA, ProductoPEI, ResultadoPEI,
)

User = get_user_model()


class ArticulacionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Usuario sin roles
        self.user_normal = User.objects.create_user(
            username='normal', password='test123'
        )
        # Superuser
        self.user_admin = User.objects.create_superuser(
            username='admin', password='admin123'
        )
        # ResultadoPAD base
        self.resultado = ResultadoPAD.objects.create(
            id_cadena='API0000001', codigo_resultado='API999.99.01',
            denominacion='Resultado API Test',
            lineamiento_pad='03', vigencia_desde=2026, vigencia_hasta=2030,
            cod_geografico='00', eta='ETA001'
        )
        # ResultadoPEI + ProductoPEI + AccionPOA base
        self.resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='API001.01', denominacion='Resultado PEI Test',
            cod_entidad='01', entidad='Entidad Test',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        self.producto_pei = ProductoPEI.objects.create(
            codigo_producto='API001.01.01', denominacion='Producto PEI Test',
            resultado_pei=self.resultado_pei
        )

    def test_get_resultados_pad_devuelve_200(self):
        """Test de GET lista resultados-pad (devuelve 200)"""
        self.client.force_authenticate(user=self.user_normal)
        response = self.client.get('/api/v1/articulacion/resultados-pad/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_crear_sin_auth_devuelve_401(self):
        """Test de POST crear resultado (sin auth devuelve 401)"""
        response = self.client.post('/api/v1/articulacion/resultados-pad/', {
            'id_cadena': 'API0000002', 'codigo_resultado': 'API999.99.02',
            'denominacion': 'Sin auth', 'lineamiento_pad': '03',
            'vigencia_desde': 2026, 'vigencia_hasta': 2030,
            'cod_geografico': '00', 'eta': 'ETA002',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sin_rol_no_puede_crear(self):
        """Test de permisos (usuario sin rol no puede crear)"""
        self.client.force_authenticate(user=self.user_normal)
        response = self.client.post('/api/v1/articulacion/resultados-pad/', {
            'id_cadena': 'API0000003', 'codigo_resultado': 'API999.99.03',
            'denominacion': 'Sin rol', 'lineamiento_pad': '03',
            'vigencia_desde': 2026, 'vigencia_hasta': 2030,
            'cod_geografico': '00', 'eta': 'ETA003',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_puede_crear_resultado(self):
        """Test que admin puede crear correctamente"""
        self.client.force_authenticate(user=self.user_admin)
        # Primero ver cuántos hay
        before = ResultadoPAD.objects.count()
        response = self.client.post('/api/v1/articulacion/resultados-pad/', {
            'id_cadena': 'API0000004', 'codigo_resultado': 'API999.99.04',
            'denominacion': 'Admin crea', 'lineamiento_pad': '03',
            'vigencia_desde': 2026, 'vigencia_hasta': 2030,
            'cod_geografico': '00', 'eta': 'ETA004',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ResultadoPAD.objects.count(), before + 1)

    def test_filtros_por_codigo_y_estado(self):
        """Test de filtros por código y estado"""
        self.client.force_authenticate(user=self.user_admin)
        # Crear un segundo con estado diferente
        ResultadoPAD.objects.create(
            id_cadena='API0000005', codigo_resultado='API999.99.05',
            denominacion='Resultado ENVIADO',
            lineamiento_pad='03', vigencia_desde=2026, vigencia_hasta=2030,
            cod_geografico='00', eta='ETA005', estado='ENVIADO'
        )
        # Filtrar por estado
        response = self.client.get(
            '/api/v1/articulacion/resultados-pad/?estado=ENVIADO'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results') or []
        self.assertTrue(all(r['estado'] == 'ENVIADO' for r in results))

        # Filtrar por código resultado
        response = self.client.get(
            '/api/v1/articulacion/resultados-pad/?search=API999.99.01'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_aprobar_cambia_estado(self):
        """Test de POST aprobar (cambia estado)"""
        self.client.force_authenticate(user=self.user_admin)
        accion = AccionPOA.objects.create(
            codigo_accion='API-ACT-001', denominacion='Accion Aprobar Test',
            producto_pei=self.producto_pei, gestion=2026, estado='ENVIADO'
        )
        response = self.client.post(
            f'/api/v1/articulacion/acciones-poa/{accion.pk}/aprobar/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accion.refresh_from_db()
        self.assertEqual(accion.estado, 'APROBADO')

    def test_aprobar_solo_enviado(self):
        """Test que solo se puede aprobar si está ENVIADO"""
        self.client.force_authenticate(user=self.user_admin)
        accion = AccionPOA.objects.create(
            codigo_accion='API-ACT-002', denominacion='Accion No Enviada',
            producto_pei=self.producto_pei, gestion=2026, estado='REFERENCIAL'
        )
        response = self.client.post(
            f'/api/v1/articulacion/acciones-poa/{accion.pk}/aprobar/'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_observar_requiere_comentario(self):
        """Test que observar requiere comentario"""
        self.client.force_authenticate(user=self.user_admin)
        accion = AccionPOA.objects.create(
            codigo_accion='API-ACT-003', denominacion='Accion Observar',
            producto_pei=self.producto_pei, gestion=2026, estado='ENVIADO'
        )
        # Sin comentario
        response = self.client.post(
            f'/api/v1/articulacion/acciones-poa/{accion.pk}/observar/',
            {}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Con comentario
        response = self.client.post(
            f'/api/v1/articulacion/acciones-poa/{accion.pk}/observar/',
            {'comentario': 'Falta justificación'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        accion.refresh_from_db()
        self.assertEqual(accion.estado, 'OBSERVADO')
