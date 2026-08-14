"""Tests de la Fase 1 (Gestión Fiscal) del ciclo presupuestario SIS-POA.

TestCase de Django puro: corre con pytest o el runner de Django.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.auditoria.models import EventoAuditoria
from apps.gestion.models import CicloFormulacion, EtapaFormulacion, GestionFiscal

from .services import (
    gestion_habilitada,
    habilitar_gestion,
    validar_gestion_para_techo,
)


def crear_gestion(anio, **extra):
    return GestionFiscal.objects.create(anio=anio, **extra)


class FiscalYearApiTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@budget.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.url = '/api/v2/sis-poa/budget/fiscal-years/'

    # -- Creación ------------------------------------------------------------

    def test_crear_gestion_nueva(self):
        resp = self.client.post(self.url, {'anio': 2028}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['anio'], 2028)
        self.assertEqual(resp.data['estado'], 'preparacion')
        self.assertIsNone(resp.data['gestion_anterior'])
        self.assertTrue(GestionFiscal.objects.filter(anio=2028).exists())

    def test_crear_gestion_duplicada_rechazada(self):
        crear_gestion(2028)
        resp = self.client.post(self.url, {'anio': 2028}, format='json')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('anio', resp.data['error'])
        self.assertEqual(GestionFiscal.objects.filter(anio=2028).count(), 1)

    def test_gestion_anterior_serialeza_la_anterior(self):
        crear_gestion(2026)
        crear_gestion(2027)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        gestion_2027 = next(
            g for g in resp.data['results'] if g['anio'] == 2027
        )
        self.assertEqual(gestion_2027['gestion_anterior'], 2026)

    def test_heredar_de_copia_ciclos_de_formulacion(self):
        from django.utils import timezone
        origen = crear_gestion(2026)
        ciclo = CicloFormulacion.objects.create(
            gestion=origen, nombre='Ciclo 2026',
            fecha_inicio=timezone.now(), fecha_cierre=timezone.now(),
            orden=1,
        )
        EtapaFormulacion.objects.create(
            ciclo=ciclo, codigo='PREP', nombre='Preparación',
            fecha_inicio=timezone.now(), fecha_cierre=timezone.now(), orden=1,
        )
        resp = self.client.post(
            self.url, {'anio': 2028, 'heredar_de': 2026}, format='json'
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        nueva = GestionFiscal.objects.get(anio=2028)
        self.assertEqual(nueva.ciclos_formulacion.count(), 1)
        self.assertEqual(nueva.ciclos_formulacion.first().nombre, 'Ciclo 2026')
        self.assertEqual(nueva.ciclos_formulacion.first().etapas.count(), 1)
        self.assertEqual(origen.ciclos_formulacion.count(), 1)

    def test_heredar_de_gestion_inexistente_rechazado(self):
        resp = self.client.post(
            self.url, {'anio': 2028, 'heredar_de': 1999}, format='json'
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertFalse(GestionFiscal.objects.filter(anio=2028).exists())

    # -- Bloqueos por gestión (§10) -----------------------------------------

    def test_validar_gestion_para_techo_lanza_si_no_habilitada(self):
        gestion = crear_gestion(2028, estado='preparacion')
        with self.assertRaises(ValidationError):
            validar_gestion_para_techo(gestion)

    def test_gestion_habilitada_pasa_validacion_techo(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        self.assertTrue(gestion_habilitada(gestion))
        self.assertTrue(validar_gestion_para_techo(gestion))

    # -- Enable --------------------------------------------------------------

    def test_enable_cambia_estado_y_registra_auditoria(self):
        gestion = crear_gestion(2028, estado='preparacion')
        resp = self.client.post(
            f'{self.url}{gestion.id}/enable/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')
        self.assertIsNotNone(gestion.fecha_apertura)
        evento = EventoAuditoria.objects.filter(
            entidad='GestionFiscal', entidad_id=str(gestion.id)
        )
        self.assertTrue(evento.exists())
        self.assertEqual(evento.first().accion, 'modificar')
        self.assertEqual(evento.first().gestion, 2028)

    def test_enable_de_gestion_ya_habilitada_rechazado(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        resp = self.client.post(
            f'{self.url}{gestion.id}/enable/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')

    def test_enable_de_gestion_cerrada_rechazado(self):
        gestion = crear_gestion(2028, estado='CERRADA')
        resp = self.client.post(
            f'{self.url}{gestion.id}/enable/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'CERRADA')

    # -- Close ---------------------------------------------------------------

    def test_close_cambia_estado_y_registra_auditoria(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        resp = self.client.post(
            f'{self.url}{gestion.id}/close/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'CERRADA')
        self.assertIsNotNone(gestion.fecha_cierre)
        evento = EventoAuditoria.objects.filter(
            entidad='GestionFiscal', entidad_id=str(gestion.id)
        ).first()
        self.assertEqual(evento.accion, 'cerrar')

    def test_close_de_gestion_ya_cerrada_rechazado(self):
        gestion = crear_gestion(2028, estado='CERRADA')
        resp = self.client.post(
            f'{self.url}{gestion.id}/close/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 400, resp.data)

    # -- Permisos ------------------------------------------------------------

    def test_usuario_sin_capacidad_no_puede_habilitar(self):
        rol = Rol.objects.create(codigo='test_basico', nombre='Test básico')
        usuario = Usuario.objects.create_user(
            email='basico@budget.test', password='test2026'
        )
        usuario.roles.add(rol)
        gestion = crear_gestion(2028, estado='preparacion')

        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{self.url}{gestion.id}/enable/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 403, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'preparacion')

    def test_usuario_con_capacidad_puede_habilitar(self):
        rol = Rol.objects.create(codigo='test_budget', nombre='Test budget')
        from apps.accounts.models import Capacidad
        capacidad, _ = Capacidad.objects.get_or_create(
            codigo='sis_poa.budget.manage',
            defaults={'nombre': 'Gestionar presupuesto', 'sistema': 'sis-poa'},
        )
        rol.capacidades.add(capacidad)
        usuario = Usuario.objects.create_user(
            email='budget@budget.test', password='test2026'
        )
        usuario.roles.add(rol)
        gestion = crear_gestion(2028, estado='preparacion')

        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{self.url}{gestion.id}/enable/', {}, format='json'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')


class FiscalYearServiceTests(TestCase):
    def test_habilitar_gestion_sin_usuario(self):
        gestion = crear_gestion(2028, estado='preparacion')
        habilitar_gestion(gestion, None)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')
