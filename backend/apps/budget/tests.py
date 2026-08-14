"""Tests del ciclo presupuestario SIS-POA (apps.budget).

Fase 1: gestión fiscal (FiscalYear*).
Fase 2: techo directivo (TechoDirectivo*).

TestCase de Django puro: corre con pytest o el runner de Django.
"""
import hashlib
import json
import tempfile
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.auditoria.models import EventoAuditoria
from apps.catalogos.models import (
    FuenteFinanciamiento,
    OrganismoFinanciador,
    RubroRecurso,
)
from apps.gestion.models import CicloFormulacion, EtapaFormulacion, GestionFiscal

from .models import (
    CeilingResource,
    DirectiveCeiling,
    DirectiveCeilingVersion,
    MandatoryExpense,
)
from .services import (
    ajuste_de_techo,
    aprobar,
    composicion_techo,
    crear_version_inicial,
    enviar_a_revision,
    fijar_techo,
    gestion_habilitada,
    habilitar_gestion,
    observar,
    validar_gestion_para_techo,
)


def crear_gestion(anio, **extra):
    return GestionFiscal.objects.create(anio=anio, **extra)


# ===========================================================================
# Fase 2 — Techo directivo
# ===========================================================================

BUDGET_URL = '/api/v2/sis-poa/budget/'


class TechoDirectivoBase(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@techo.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.gestion = crear_gestion(2030, estado='HABILITADA')
        self.fuente = FuenteFinanciamiento.objects.create(
            codigo='11', denominacion='Tesoro General', gestion=2030,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.organismo = OrganismoFinanciador.objects.create(
            codigo='111', denominacion='Tesoro General de la Nación',
            gestion=2030, fecha_vigencia_desde=timezone.now().date(),
        )
        self.rubro = RubroRecurso.objects.create(
            codigo='11', denominacion='Impuestos municipales', gestion=2030,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(self.gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.ceiling = DirectiveCeiling.objects.get(gestion=self.gestion)
        self.version = DirectiveCeilingVersion.objects.get(
            ceiling=self.ceiling, numero=1
        )

    def crear_recurso(self, origen='SIGEP', monto='1000.00', concepto='Recurso',
                      fuente=None, organismo=None, rubro=None):
        return CeilingResource.objects.create(
            version=self.version, origen=origen, monto=monto,
            concepto=concepto, fuente=fuente, organismo=organismo, rubro=rubro,
            created_by=self.admin, updated_by=self.admin,
        )

    def crear_gasto(self, monto='200.00', denominacion='Gasto obligatorio',
                    fuente=None, organismo=None):
        return MandatoryExpense.objects.create(
            version=self.version, monto=monto, denominacion=denominacion,
            fuente=fuente, organismo=organismo,
            created_by=self.admin, updated_by=self.admin,
        )

    def fijar_version(self):
        """Recorre submit → approve → freeze y devuelve la versión."""
        enviar_a_revision(self.version, self.admin)
        aprobar(self.version, self.admin)
        fijar_techo(self.version, self.admin)
        self.version.refresh_from_db()
        return self.version


class TechoDirectivoComposicionTests(TechoDirectivoBase):
    def test_techo_sigep_refleja_montos_en_composicion(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        comp = composicion_techo(self.ceiling)
        self.assertEqual(comp['sigep'], Decimal('1000.00'))
        self.assertEqual(comp['municipales'], Decimal('0.00'))
        self.assertEqual(comp['techo_bruto'], Decimal('1000.00'))
        self.assertEqual(comp['techo_distribuible'], Decimal('1000.00'))

    def test_recursos_propios_municipales_suman_al_bruto(self):
        self.crear_recurso(origen='SIGEP', monto='100.00', concepto='CT')
        self.crear_recurso(origen='MUNICIPAL', monto='50.00', concepto='IP')
        comp = composicion_techo(self.ceiling)
        self.assertEqual(comp['sigep'], Decimal('100.00'))
        self.assertEqual(comp['municipales'], Decimal('50.00'))
        self.assertEqual(comp['techo_bruto'], Decimal('150.00'))

    def test_gasto_obligatorio_resta_del_distribuible(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        self.crear_gasto(monto='200.00', denominacion='Servicio deuda')
        comp = composicion_techo(self.ceiling)
        self.assertEqual(comp['gastos_obligatorios'], Decimal('200.00'))
        self.assertEqual(comp['techo_bruto'], Decimal('1000.00'))
        self.assertEqual(comp['techo_distribuible'], Decimal('800.00'))

    def test_distribuible_es_bruto_menos_obligatorios(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        self.crear_recurso(origen='MUNICIPAL', monto='250.00', concepto='IP')
        self.crear_recurso(origen='SALDO', monto='150.00', concepto='Saldo')
        self.crear_recurso(origen='OTRO', monto='100.00', concepto='Otro')
        self.crear_gasto(monto='300.00', denominacion='Deuda 1')
        self.crear_gasto(monto='100.00', denominacion='Deuda 2')
        comp = composicion_techo(self.ceiling)
        bruto = Decimal('1500.00')
        obligatorios = Decimal('400.00')
        self.assertEqual(comp['techo_bruto'], bruto)
        self.assertEqual(comp['gastos_obligatorios'], obligatorios)
        self.assertEqual(comp['techo_distribuible'], bruto - obligatorios)
        self.assertEqual(comp['reservas'], Decimal('0.00'))

    def test_por_fuente_agrupa_por_fuente(self):
        self.crear_recurso(origen='SIGEP', monto='100.00', concepto='A',
                           fuente=self.fuente)
        self.crear_recurso(origen='SIGEP', monto='50.00', concepto='B',
                           fuente=self.fuente)
        self.crear_recurso(origen='OTRO', monto='30.00', concepto='C')
        comp = composicion_techo(self.ceiling)
        por_fuente = {f['fuente']: f['monto'] for f in comp['por_fuente']}
        self.assertEqual(por_fuente['11'], Decimal('150.00'))
        self.assertEqual(por_fuente['SIN_FUENTE'], Decimal('30.00'))


class TechoDirectivoFlujoTests(TechoDirectivoBase):
    def test_no_se_puede_crear_ceiling_sin_gestion_habilitada(self):
        gestion_cerrada = crear_gestion(2031, estado='preparacion')
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(gestion_cerrada.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertFalse(
            DirectiveCeiling.objects.filter(gestion=gestion_cerrada).exists()
        )

    def test_no_se_puede_crear_segundo_ceiling_para_misma_gestion(self):
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(self.gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('gestion', resp.data['error'])

    def test_fijar_techo_con_sumatorias_correctas(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT',
                           fuente=self.fuente, organismo=self.organismo)
        self.crear_gasto(monto='200.00', denominacion='Deuda',
                         fuente=self.fuente)
        version = self.fijar_version()
        self.assertEqual(version.estado, 'FIJADO')
        self.assertTrue(version.inmutable)
        self.assertTrue(version.hash)
        self.assertEqual(len(version.hash), 64)
        self.assertTrue(version.verificar_hash())
        self.assertIsNotNone(version.fecha_fijacion)
        self.assertEqual(version.fijado_por, self.admin)
        self.ceiling.refresh_from_db()
        self.assertEqual(self.ceiling.estado, 'FIJADO')
        self.assertEqual(self.ceiling.version_actual, 1)
        evento = EventoAuditoria.objects.filter(
            entidad='DirectiveCeilingVersion', entidad_id=str(version.id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'aprobar')
        self.assertIn('fijado', evento.resumen.lower())
        self.assertEqual(evento.gestion, 2030)

    def test_no_se_puede_fijar_sin_aprobacion_previa(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        with self.assertRaises(ValidationError):
            fijar_techo(self.version, self.admin)
        self.version.refresh_from_db()
        self.assertFalse(self.version.inmutable)

    def test_no_se_puede_fijar_con_obligatorios_mayores_al_bruto(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        self.crear_gasto(monto='1500.00', denominacion='Deuda')
        enviar_a_revision(self.version, self.admin)
        aprobar(self.version, self.admin)
        with self.assertRaises(ValidationError):
            fijar_techo(self.version, self.admin)
        self.version.refresh_from_db()
        self.assertEqual(self.version.estado, 'APROBADO')
        self.assertFalse(self.version.inmutable)

    def test_transiciones_y_auditoria_del_ciclo(self):
        v = enviar_a_revision(self.version, self.admin)
        self.assertEqual(v.estado, 'EN_REVISION')
        v = observar(v, self.admin, 'Falta desglose por fuente')
        self.assertEqual(v.estado, 'OBSERVADO')
        self.assertEqual(v.observaciones, 'Falta desglose por fuente')
        v = enviar_a_revision(v, self.admin)
        self.assertEqual(v.estado, 'EN_REVISION')
        v = aprobar(v, self.admin)
        self.assertEqual(v.estado, 'APROBADO')
        acciones = list(
            EventoAuditoria.objects.filter(
                entidad='DirectiveCeilingVersion', entidad_id=str(v.id),
            ).values_list('accion', flat=True)
        )
        self.assertIn('enviar', acciones)
        self.assertIn('devolver', acciones)
        self.assertIn('aprobar', acciones)

    def test_transicion_invalida_rechazada(self):
        with self.assertRaises(ValidationError):
            aprobar(self.version, self.admin)  # BORRADOR → APROBADO no es válida
        self.version.refresh_from_db()
        self.assertEqual(self.version.estado, 'BORRADOR')

    def test_observar_requiere_motivo(self):
        with self.assertRaises(ValidationError):
            observar(self.version, self.admin, '')


class TechoDirectivoInmutabilidadTests(TechoDirectivoBase):
    def test_update_de_recurso_en_version_fijada_devuelve_409(self):
        recurso = self.crear_recurso(origen='SIGEP', monto='1000.00',
                                     concepto='CT')
        self.fijar_version()
        resp = self.client.patch(
            f'{BUDGET_URL}resources/{recurso.id}/',
            {'monto': '999.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        recurso.refresh_from_db()
        self.assertEqual(recurso.monto, Decimal('1000.00'))

    def test_create_recurso_en_version_fijada_devuelve_409(self):
        self.fijar_version()
        resp = self.client.post(
            f'{BUDGET_URL}resources/',
            {'version': str(self.version.id), 'origen': 'SIGEP',
             'concepto': 'Nuevo', 'monto': '10.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        self.assertEqual(self.version.recursos.count(), 0)

    def test_delete_gasto_en_version_fijada_devuelve_409(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        gasto = self.crear_gasto(monto='200.00', denominacion='Deuda')
        self.fijar_version()
        resp = self.client.delete(
            f'{BUDGET_URL}mandatory-expenses/{gasto.id}/',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        self.assertTrue(MandatoryExpense.objects.filter(pk=gasto.pk).exists())

    def test_modelo_bloquea_modificacion_de_version_fijada(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        self.fijar_version()
        with self.assertRaises(ValidationError):
            self.version.observaciones = 'cambio'
            self.version.save()
        self.version.refresh_from_db()
        self.assertEqual(self.version.observaciones, '')

    def test_ajuste_crea_version_nueva_y_deja_v1_intacta(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT',
                           fuente=self.fuente)
        self.crear_gasto(monto='200.00', denominacion='Deuda')
        self.fijar_version()
        v1 = DirectiveCeilingVersion.objects.get(ceiling=self.ceiling, numero=1)

        nueva = ajuste_de_techo(self.ceiling, self.admin)

        self.assertEqual(nueva.numero, 2)
        self.assertEqual(nueva.estado, 'BORRADOR')
        self.assertFalse(nueva.inmutable)
        v1.refresh_from_db()
        self.assertEqual(v1.estado, 'FIJADO')
        self.assertTrue(v1.inmutable)
        self.assertEqual(v1.recursos.count(), 1)
        self.assertEqual(nueva.recursos.count(), 1)
        self.assertEqual(nueva.gastos_obligatorios.count(), 1)
        self.assertEqual(
            nueva.recursos.first().monto, v1.recursos.first().monto
        )
        self.ceiling.refresh_from_db()
        self.assertEqual(self.ceiling.version_actual, 2)
        self.assertEqual(self.ceiling.estado, 'BORRADOR')

    def test_ajuste_requiere_techo_fijado(self):
        with self.assertRaises(ValidationError):
            ajuste_de_techo(self.ceiling, self.admin)


class TechoDirectivoPermisosTests(TechoDirectivoBase):
    def _usuario_con_capacidades(self, *codigos):
        rol = Rol.objects.create(codigo=f'rol_{len(codigos)}', nombre='Rol')
        for codigo in codigos:
            from apps.accounts.models import Capacidad
            capacidad, _ = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': codigo, 'sistema': 'sis-poa'},
            )
            rol.capacidades.add(capacidad)
        usuario = Usuario.objects.create_user(
            email='usuario@techo.test', password='test2026'
        )
        usuario.roles.add(rol)
        return usuario

    def test_usuario_sin_capacidad_no_puede_enviar_a_revision(self):
        usuario = self._usuario_con_capacidades()
        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{BUDGET_URL}directive-ceilings/{self.ceiling.id}/submit/',
            {}, format='json',
        )
        self.assertEqual(resp.status_code, 403, resp.data)
        self.version.refresh_from_db()
        self.assertEqual(self.version.estado, 'BORRADOR')

    def test_usuario_sin_manage_no_puede_crear_recursos(self):
        usuario = self._usuario_con_capacidades()
        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{BUDGET_URL}resources/',
            {'version': str(self.version.id), 'origen': 'SIGEP',
             'concepto': 'CT', 'monto': '10.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 403, resp.data)

    def test_usuario_con_approve_puede_subir_aprobar_y_fijar(self):
        usuario = self._usuario_con_capacidades('sis_poa.budget.approve')
        client = APIClient()
        client.force_authenticate(user=usuario)
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        resp = client.post(
            f'{BUDGET_URL}directive-ceilings/{self.ceiling.id}/submit/',
            {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = client.post(
            f'{BUDGET_URL}directive-ceilings/{self.ceiling.id}/approve/',
            {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = client.post(
            f'{BUDGET_URL}directive-ceilings/{self.ceiling.id}/freeze/',
            {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.version.refresh_from_db()
        self.assertEqual(self.version.estado, 'FIJADO')
        self.assertTrue(self.version.inmutable)

    def test_composition_endpoint_devuelve_composicion(self):
        self.crear_recurso(origen='SIGEP', monto='1000.00', concepto='CT')
        resp = self.client.get(
            f'{BUDGET_URL}directive-ceilings/{self.ceiling.id}/composition/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['sigep'], '1000.00')
        self.assertEqual(resp.data['techo_distribuible'], '1000.00')

    def test_retrieve_incluye_version_y_composicion(self):
        self.crear_recurso(origen='SIGEP', monto='500.00', concepto='CT')
        resp = self.client.get(
            f'{BUDGET_URL}directive-ceilings/{self.ceiling.id}/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['version']['numero'], 1)
        self.assertEqual(
            resp.data['version']['recursos'][0]['monto'], '500.00'
        )
        self.assertEqual(resp.data['composicion']['sigep'], '500.00')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='budget-tests-'))
class TechoDirectivoDocumentoTests(TechoDirectivoBase):
    def test_upload_documento_calcula_sha256(self):
        contenido = b'%PDF-1.4\nreporte SIGEP demo'
        archivo = __import__(
            'django.core.files.uploadedfile', fromlist=['SimpleUploadedFile']
        ).SimpleUploadedFile(
            'reporte_sigep.pdf', contenido, content_type='application/pdf'
        )
        resp = self.client.post(
            f'{BUDGET_URL}documents/',
            {'gestion': str(self.gestion.id), 'tipo': 'REPORTE_SIGEP',
             'archivo': archivo},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['sha256'], hashlib.sha256(contenido).hexdigest())
        self.assertEqual(resp.data['size'], len(contenido))
        self.assertEqual(resp.data['mime_type'], 'application/pdf')
        self.assertTrue(resp.data['storage_path'].startswith('budget/'))
        self.assertEqual(resp.data['gestion_anio'], 2030)

    def test_upload_documento_mime_no_permitido_rechazado(self):
        archivo = __import__(
            'django.core.files.uploadedfile', fromlist=['SimpleUploadedFile']
        ).SimpleUploadedFile(
            'malware.exe', b'MZ....', content_type='application/x-msdownload'
        )
        resp = self.client.post(
            f'{BUDGET_URL}documents/',
            {'gestion': str(self.gestion.id), 'tipo': 'OTRO',
             'archivo': archivo},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('archivo', resp.data['error'])

    def test_upload_documento_mas_de_20mb_rechazado(self):
        archivo = __import__(
            'django.core.files.uploadedfile', fromlist=['SimpleUploadedFile']
        ).SimpleUploadedFile(
            'grande.pdf', b'x' * (20 * 1024 * 1024 + 1),
            content_type='application/pdf',
        )
        resp = self.client.post(
            f'{BUDGET_URL}documents/',
            {'gestion': str(self.gestion.id), 'tipo': 'INFORME',
             'archivo': archivo},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_listar_documentos_por_gestion(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        archivo = SimpleUploadedFile(
            'nota.pdf', b'nota MEF', content_type='application/pdf'
        )
        resp = self.client.post(
            f'{BUDGET_URL}documents/',
            {'gestion': str(self.gestion.id), 'tipo': 'NOTA_MEF',
             'archivo': archivo},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        resp = self.client.get(
            f'{BUDGET_URL}documents/?gestion={self.gestion.id}'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['tipo'], 'NOTA_MEF')


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
