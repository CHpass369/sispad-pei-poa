"""Guardado atómico de varios requerimientos de una sola tanda.

El wizard de recursos mandaba un POST por requerimiento; si el N-ésimo
fallaba, los anteriores ya habían quedado guardados y un reintento los
duplicaba (más aún con el código autogenerado, que ya no choca contra
sí mismo). `POST .../asignaciones-gasto/bulk/` valida y guarda todo
dentro de una única transacción: todo o nada.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import Usuario
from apps.articulacion.models import (
    AccionPOA, AsignacionObjetoGasto, OperacionPOAU, ProductoPEI, ResultadoPEI,
)
from apps.gestion.testing import habilitar_gestion_para_tests

BULK_URL = '/api/v1/articulacion/asignaciones-gasto/bulk/'


def requerimiento(accion, operacion, gestion=2027, **overrides):
    datos = {
        'gestion': gestion,
        'accion_poa': accion.pk,
        'operacion': operacion.pk,
        'actividad': None,
        'categoria_programatica': '170 0 001', 'da': '1', 'ue': '001',
        'programa': '170', 'cod_objeto_gasto': '25200',
        'descripcion_objeto': 'Estudios e Investigaciones',
        'grupo_gasto': '20000', 'tipo_gasto': 'Funcionamiento',
        'fuente_financiamiento': '20', 'organismo_financiador': '230',
        'monto_programado': '1000', 'monto_vigente': '1000',
    }
    datos.update(overrides)
    return datos


class AsignacionesGastoBulkTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestion = habilitar_gestion_para_tests(2027)
        resultado = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030,
        )
        producto = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado,
        )
        cls.accion = AccionPOA.objects.create(
            codigo_accion='ACP-BULK', denominacion='Acción bulk',
            producto_pei=producto, gestion=2027,
        )
        cls.operacion = OperacionPOAU.objects.create(
            codigo_operacion='OP-BULK', denominacion='Operación',
            tipo_operacion='SUSTANTIVA', accion_poa=cls.accion,
        )
        cls.user = Usuario.objects.create_superuser(
            email='bulk@test.gob.bo', password='Clave.Bulk.2027',
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_guarda_toda_la_tanda_con_codigos_consecutivos(self):
        payload = [
            requerimiento(self.accion, self.operacion) for _ in range(3)
        ]
        response = self.client.post(BULK_URL, payload, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data), 3)
        codigos = sorted(row['codigo_asignacion'] for row in response.data)
        self.assertEqual(codigos, ['ACP-BULK.G1', 'ACP-BULK.G2', 'ACP-BULK.G3'])
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 3)

    def test_un_item_invalido_revierte_toda_la_tanda(self):
        payload = [
            requerimiento(self.accion, self.operacion),
            requerimiento(self.accion, self.operacion, monto_programado=None),
            requerimiento(self.accion, self.operacion),
        ]
        response = self.client.post(BULK_URL, payload, format='json')

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            AsignacionObjetoGasto.objects.count(), 0,
            'un error a mitad de la tanda no debe dejar nada guardado',
        )

    def test_rechaza_lista_vacia(self):
        response = self.client.post(BULK_URL, [], format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 0)

    def test_rechaza_gestiones_mezcladas(self):
        payload = [
            requerimiento(self.accion, self.operacion, gestion=2027),
            requerimiento(self.accion, self.operacion, gestion=2026),
        ]
        response = self.client.post(BULK_URL, payload, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 0)

    def test_candado_rechaza_gestion_no_habilitada(self):
        payload = [requerimiento(self.accion, self.operacion, gestion=2026)]
        response = self.client.post(BULK_URL, payload, format='json')
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 0)

    def test_un_codigo_explicito_se_respeta_en_la_tanda(self):
        payload = [
            requerimiento(self.accion, self.operacion, codigo_asignacion='IMPORT-7'),
            requerimiento(self.accion, self.operacion),
        ]
        response = self.client.post(BULK_URL, payload, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        codigos = sorted(row['codigo_asignacion'] for row in response.data)
        self.assertEqual(codigos, ['ACP-BULK.G1', 'IMPORT-7'])
