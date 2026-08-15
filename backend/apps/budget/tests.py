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
    ProgrammaticCategory,
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


# ===========================================================================
# Fase 3 - CategorAas programAticas + catAAlogos
# ===========================================================================
class ProgrammaticCategoryTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@cat.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.gestion = crear_gestion(2031, estado='HABILITADA')
        self.url = BUDGET_URL + 'programmatic-categories/'

    def _crear_categoria(self, codigo='097', nivel='PROGRAMA', parent=None, **extra):
        data = {
            'gestion': self.gestion.id,
            'codigo': codigo,
            'denominacion': 'CategorAa ' + codigo,
            'nivel': nivel,
            'parent': getattr(parent, 'id', parent) if parent else None,
            **extra,
        }
        return self.client.post(self.url, data, format='json')

    def test_crear_programa_preserva_ceros(self):
        resp = self._crear_categoria('097')
        self.assertEqual(resp.status_code, 201, resp.content[:300])
        self.assertEqual(resp.data['codigo'], '097')

    def test_crear_jerarquia_programa_subprograma(self):
        prog = self._crear_categoria('09', nivel='PROGRAMA')
        self.assertEqual(prog.status_code, 201)
        sub = self._crear_categoria('010', nivel='SUBPROGRAMA', parent=prog.data['id'])
        self.assertEqual(sub.status_code, 201)
        self.assertEqual(sub.data['codigo_compuesto'], '09.010')

    def test_nivel_no_puede_ser_menor_al_padre(self):
        sub = self._crear_categoria('010', nivel='SUBPROGRAMA')
        self.assertEqual(sub.status_code, 201)
        prog_hijo = self._crear_categoria('09', nivel='PROGRAMA', parent=sub.data['id'])
        self.assertEqual(prog_hijo.status_code, 400)

    def test_duplicado_codigo_misma_gestion_rechazado(self):
        self._crear_categoria('097')
        resp = self._crear_categoria('097')
        self.assertEqual(resp.status_code, 400)

    def test_no_crea_en_gestion_no_habilitada(self):
        gestion_cerrada = crear_gestion(2032, estado='CERRADA')
        resp = self.client.post(self.url, {
            'gestion': gestion_cerrada.id,
            'codigo': '01',
            'denominacion': 'Sin habilitar',
            'nivel': 'PROGRAMA',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_tree_por_gestion(self):
        prog = self._crear_categoria('09', nivel='PROGRAMA').data['id']
        self._crear_categoria('010', nivel='SUBPROGRAMA', parent=prog)
        resp = self.client.get(self.url + 'tree/', {'gestion': self.gestion.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(len(resp.data[0]['hijos']), 1)

    def test_duplicar_a_otra_gestion(self):
        prog = self._crear_categoria('09', nivel='PROGRAMA').data['id']
        sub = self._crear_categoria('010', nivel='SUBPROGRAMA', parent=prog).data['id']
        destino = crear_gestion(2033, estado='HABILITADA')
        resp = self.client.post(
            f'{self.url}{prog}/duplicar_a_gestion/',
            {'gestion_destino': destino.id}, format='json')
        self.assertEqual(resp.status_code, 201)
        copias = ProgrammaticCategory.objects.filter(gestion=destino)
        self.assertEqual(copias.count(), 2)
        self.assertEqual(copias.get(nivel='SUBPROGRAMA').codigo, '010')


class CatalogOptionsTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@catopts.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_catalogs_devuelve_todos_los_catalogos(self):
        resp = self.client.get(BUDGET_URL + 'catalogs/')
        self.assertEqual(resp.status_code, 200)
        for key in ['fuentes', 'organismos', 'rubros', 'objetos_gasto',
                    'distritos', 'direcciones', 'unidades_ejecutoras',
                    'unidades_organizacionales']:
            self.assertIn(key, resp.data)


# ===========================================================================
# Fase 4 - Distribución presupuestaria
# ===========================================================================
from .models import (  # noqa: E402
    Allocation,
    AllocationSource,
    DistributionVersion,
    Reserve,
)
from .services import (  # noqa: E402
    disponible_por_fuente,
    distribuido_por_fuente,
    reservado_por_fuente,
    techo_distribuible_por_fuente,
)


class DistribucionBase(TechoDirectivoBase):
    """Base de distribución: techo fijado de 1500.00 sobre la fuente 11."""

    def setUp(self):
        super().setUp()
        self.crear_recurso(origen='SIGEP', monto='1500.00', concepto='CT',
                           fuente=self.fuente, organismo=self.organismo)
        self.fijar_version()
        self.techo_fijado = self.version

    def crear_apertura(self, monto='1000.00', denominacion='Apertura demo',
                       codigo_sisin='12345678', gestion=None, **extra):
        data = {
            'gestion': str((gestion or self.gestion).id),
            'denominacion': denominacion,
            'codigo_sisin': codigo_sisin,
            'fuentes': [{
                'fuente': str(self.fuente.id),
                'organismo': str(self.organismo.id),
                'monto': monto,
            }],
            **extra,
        }
        return self.client.post(
            f'{BUDGET_URL}allocations/', data, format='json',
        )

    def crear_reserva_api(self, monto='200.00', motivo='Contingencia'):
        return self.client.post(
            f'{BUDGET_URL}reserves/',
            {'gestion': str(self.gestion.id), 'fuente': str(self.fuente.id),
             'organismo': str(self.organismo.id), 'tipo': 'OTRA',
             'motivo': motivo, 'monto': monto},
            format='json',
        )


class DistribucionAperturaTests(DistribucionBase):
    def test_crear_apertura_con_fuente_decrece_saldo(self):
        resp = self.crear_apertura(monto='1000.00')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['total'], '1000.00')
        self.assertEqual(resp.data['estado'], 'ACTIVA')
        self.assertEqual(len(resp.data['fuentes']), 1)
        self.assertEqual(resp.data['fuentes'][0]['monto'], '1000.00')

        distribuido = distribuido_por_fuente(self.gestion)
        self.assertEqual(distribuido[self.fuente.id], Decimal('1000.00'))
        disponible = disponible_por_fuente(self.gestion)
        self.assertEqual(disponible[self.fuente.id], Decimal('500.00'))

        version = DistributionVersion.objects.get(gestion=self.gestion)
        self.assertEqual(version.numero, 1)
        evento = EventoAuditoria.objects.filter(
            entidad='Allocation', gestion=2030,
        )
        self.assertTrue(evento.exists())

    def test_exceso_de_fuente_devuelve_budget_exceeded(self):
        resp = self.crear_apertura(monto='1600.00')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['requested'], '1600.00')
        self.assertEqual(resp.data['details']['available'], '1500.00')
        self.assertEqual(resp.data['details']['difference'], '100.00')
        self.assertEqual(
            Allocation.objects.filter(gestion=self.gestion).count(), 0
        )

    def test_distribucion_bloqueada_sin_techo_fijado(self):
        gestion = crear_gestion(2034, estado='HABILITADA')
        self.assertEqual(disponible_por_fuente(gestion), {})
        resp = self.crear_apertura(gestion=gestion)
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertFalse(
            Allocation.objects.filter(gestion=gestion).exists()
        )

    def test_concurrencia_secuencial_dos_requests_exceden(self):
        resp1 = self.crear_apertura(monto='1000.00', denominacion='Primera')
        self.assertEqual(resp1.status_code, 201, resp1.data)
        resp2 = self.crear_apertura(monto='1000.00', denominacion='Segunda')
        self.assertEqual(resp2.status_code, 400, resp2.data)
        self.assertEqual(resp2.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(
            Allocation.objects.filter(gestion=self.gestion).count(), 1
        )

    def test_eliminar_apertura_borrador_ok(self):
        from .services import version_distribucion_activa
        allocation = Allocation.objects.create(
            gestion=self.gestion,
            version=version_distribucion_activa(self.gestion),
            denominacion='Borrador importado (Fase 5)',
            estado='BORRADOR',
            created_by=self.admin, updated_by=self.admin,
        )
        AllocationSource.objects.create(
            allocation=allocation, fuente=self.fuente, monto=Decimal('50.00'),
            created_by=self.admin, updated_by=self.admin,
        )
        resp = self.client.delete(
            f'{BUDGET_URL}allocations/{allocation.id}/'
        )
        self.assertEqual(resp.status_code, 204, resp.data)
        self.assertFalse(Allocation.objects.filter(pk=allocation.pk).exists())

    def test_cerrar_apertura_y_no_puede_editarse(self):
        resp = self.crear_apertura(monto='500.00', denominacion='A cerrar')
        self.assertEqual(resp.status_code, 201, resp.data)
        allocation_id = resp.data['id']

        resp = self.client.post(
            f'{BUDGET_URL}allocations/{allocation_id}/cerrar/', {},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'CERRADA')

        resp = self.client.patch(
            f'{BUDGET_URL}allocations/{allocation_id}/',
            {'denominacion': 'Intento de cambio'}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(
            Allocation.objects.get(pk=allocation_id).denominacion, 'A cerrar'
        )

        resp = self.client.delete(f'{BUDGET_URL}allocations/{allocation_id}/')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertTrue(Allocation.objects.filter(pk=allocation_id).exists())

    def test_actualizar_apertura_reemplaza_fuentes(self):
        resp = self.crear_apertura(monto='500.00', denominacion='Original')
        self.assertEqual(resp.status_code, 201, resp.data)
        allocation_id = resp.data['id']
        resp = self.client.patch(
            f'{BUDGET_URL}allocations/{allocation_id}/',
            {'denominacion': 'Modificada',
             'fuentes': [{'fuente': str(self.fuente.id),
                          'organismo': str(self.organismo.id),
                          'monto': '700.00'}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['total'], '700.00')
        self.assertEqual(resp.data['denominacion'], 'Modificada')
        allocation = Allocation.objects.get(pk=allocation_id)
        self.assertEqual(allocation.fuentes.count(), 1)
        self.assertEqual(allocation.fuentes.first().monto, Decimal('700.00'))

    def test_actualizar_apertura_que_excede_rechazada(self):
        self.crear_apertura(monto='1200.00', denominacion='Ocupa saldo')
        resp = self.crear_apertura(monto='200.00', denominacion='Segunda')
        self.assertEqual(resp.status_code, 201, resp.data)
        allocation_id = resp.data['id']
        resp = self.client.patch(
            f'{BUDGET_URL}allocations/{allocation_id}/',
            {'fuentes': [{'fuente': str(self.fuente.id),
                          'organismo': str(self.organismo.id),
                          'monto': '400.00'}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['available'], '300.00')


class DistribucionReservaTests(DistribucionBase):
    def test_reserva_decrece_disponible_y_liberar_lo_devuelve(self):
        resp = self.crear_reserva_api(monto='200.00')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['estado'], 'ACTIVA')
        self.assertEqual(
            reservado_por_fuente(self.gestion)[self.fuente.id],
            Decimal('200.00'),
        )
        self.assertEqual(
            disponible_por_fuente(self.gestion)[self.fuente.id],
            Decimal('1300.00'),
        )

        reserva_id = resp.data['id']
        resp = self.client.post(
            f'{BUDGET_URL}reserves/{reserva_id}/liberar/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'LIBERADA')
        self.assertEqual(reservado_por_fuente(self.gestion), {})
        self.assertEqual(
            disponible_por_fuente(self.gestion)[self.fuente.id],
            Decimal('1500.00'),
        )

    def test_reserva_excede_disponible_rechazada(self):
        self.crear_apertura(monto='1200.00', denominacion='Ocupa saldo')
        resp = self.crear_reserva_api(monto='400.00')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['available'], '300.00')
        self.assertEqual(
            Reserve.objects.filter(gestion=self.gestion).count(), 0
        )


class DistribucionDashboardTests(DistribucionBase):
    def test_dashboard_consistente(self):
        self.crear_apertura(monto='1000.00', denominacion='Apertura A')
        self.crear_reserva_api(monto='200.00')
        resp = self.client.get(
            f'{BUDGET_URL}distributions/dashboard/',
            {'gestion': str(self.gestion.id)},
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        data = resp.data

        techo = Decimal(data['techo_distribuible'])
        distribuido = Decimal(data['distribuido'])
        reservado = Decimal(data['reservado'])
        disponible = Decimal(data['disponible'])
        self.assertEqual(techo, Decimal('1500.00'))
        self.assertEqual(distribuido, Decimal('1000.00'))
        self.assertEqual(reservado, Decimal('200.00'))
        self.assertEqual(disponible, Decimal('300.00'))
        self.assertEqual(techo, distribuido + reservado + disponible)
        self.assertEqual(data['porcentaje'], 66.67)
        self.assertEqual(data['aperturas_count'], 1)

        por_fuente = data['por_fuente'][0]
        self.assertEqual(por_fuente['fuente_id'], str(self.fuente.id))
        self.assertEqual(por_fuente['techo'], '1500.00')
        self.assertEqual(por_fuente['distribuido'], '1000.00')
        self.assertEqual(por_fuente['reservado'], '200.00')
        self.assertEqual(por_fuente['disponible'], '300.00')
        self.assertEqual(por_fuente['porcentaje'], 66.67)

    def test_dashboard_sin_datos_devuelve_ceros(self):
        resp = self.client.get(
            f'{BUDGET_URL}distributions/dashboard/',
            {'gestion': str(self.gestion.id)},
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['techo_distribuible'], '1500.00')
        self.assertEqual(resp.data['distribuido'], '0.00')
        self.assertEqual(resp.data['reservado'], '0.00')
        self.assertEqual(resp.data['disponible'], '1500.00')
        self.assertEqual(resp.data['porcentaje'], 0.0)
        self.assertEqual(resp.data['aperturas_count'], 0)

    def test_versions_endpoint_lista_por_gestion(self):
        self.crear_apertura(monto='100.00', denominacion='Genera versión 1')
        resp = self.client.get(
            f'{BUDGET_URL}distributions/versions/',
            {'gestion': str(self.gestion.id)},
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['numero'], 1)
        self.assertEqual(resp.data[0]['estado'], 'BORRADOR')

    def test_techo_distribuible_por_fuente_desde_techo_fijado(self):
        techo = techo_distribuible_por_fuente(self.gestion)
        self.assertEqual(techo[self.fuente.id], Decimal('1500.00'))


# ===========================================================================
# Fase 5 - Importador Excel (staging + normalización + validación + aplicar)
# ===========================================================================
import openpyxl  # noqa: E402
from io import BytesIO  # noqa: E402

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from apps.territorio.models import Distrito  # noqa: E402

from .importer import (  # noqa: E402
    clasificar_fila,
    detectar_header,
    normalizar_codigo,
    normalizar_monto,
    validar_importacion,
)
from .models import (  # noqa: E402
    BudgetImport,
    ImportDetalle,
    ImportError,
)

HEADER_GASTOS = [
    'N°', 'UNIDAD EJECUTIVA', 'DISTRITO URBANO Y RURAL',
    'DIRECCIÓN ADMINISTRATIVA', 'UNIDAD EJECUTORA', 'V', 'PROG.',
    'CODIGO SISIN WEB', 'ACT.', 'DENOMINACIÓN DEL PROYECTO',
    'Saldo gestión anterior', 'CT', 'RE', 'ORE', 'IDH', 'TGN',
    'Total Presupuesto',
]

XLSX_MIME = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


def construir_xlsx(filas, hoja='gastos'):
    """XLSX en memoria (bytes) con openpyxl."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = hoja
    for fila in filas:
        ws.append(fila)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def fila_detalle(v='', prog='097', sisin='12345678', act='01',
                denom='Apertura demo', distrito='URBANO 1', ct='500.00',
                re='300.00', ore='', idh='200.00', tgn='100.00',
                total='1100.00'):
    return [
        '1', 'SMFA', distrito, 'DA01', 'UE01', v, prog, sisin, act,
        denom, '', ct, re, ore, idh, tgn, total,
    ]


class ImportadorBase(TestCase):
    """Base del importador: gestión habilitada + fuentes + categorías."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@import.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.gestion = crear_gestion(2030, estado='HABILITADA')
        for codigo, nombre in (('41', 'Coparticipación tributaria'),
                               ('20', 'Recursos específicos'),
                               ('11', 'Tesoro general')):
            FuenteFinanciamiento.objects.create(
                codigo=codigo, denominacion=nombre, gestion=2030,
                fecha_vigencia_desde=timezone.now().date(),
            )
        prog = ProgrammaticCategory.objects.create(
            gestion=self.gestion, codigo='097', denominacion='Programa 097',
            nivel='PROGRAMA',
        )
        ProgrammaticCategory.objects.create(
            gestion=self.gestion, codigo='010',
            denominacion='Subprograma 010', nivel='SUBPROGRAMA', parent=prog,
        )
        Distrito.objects.create(codigo='D1', nombre='URBANO 1')

    def subir(self, contenido, perfil='SISPOA_GASTOS_HISTORICO'):
        archivo = SimpleUploadedFile(
            'gastos.xlsx', contenido, content_type=XLSX_MIME,
        )
        return self.client.post(
            f'{BUDGET_URL}imports/',
            {'gestion': str(self.gestion.id), 'perfil': perfil,
             'archivo': archivo},
            format='multipart',
        )

    def subir_y_validar(self, filas):
        resp = self.subir(construir_xlsx(filas))
        self.assertEqual(resp.status_code, 201, resp.content[:500])
        importacion = BudgetImport.objects.get(pk=resp.data['id'])
        resp_val = self.client.post(
            f"{BUDGET_URL}imports/{importacion.id}/validate/", {}, format='json',
        )
        self.assertEqual(resp_val.status_code, 200, resp_val.data)
        importacion.refresh_from_db()
        return importacion, resp, resp_val


class ImportadorNormalizacionTests(TestCase):
    def test_monto_con_coma_decimal(self):
        self.assertEqual(normalizar_monto('1.234.567,89'), Decimal('1234567.89'))

    def test_monto_con_punto_decimal(self):
        self.assertEqual(normalizar_monto('1,234,567.89'), Decimal('1234567.89'))

    def test_monto_con_prefijo_bs(self):
        self.assertEqual(normalizar_monto('Bs 1.234'), Decimal('1234.00'))

    def test_monto_parentesis_es_negativo(self):
        self.assertEqual(normalizar_monto('(123)'), Decimal('-123.00'))

    def test_monto_vacio_es_cero(self):
        self.assertEqual(normalizar_monto(''), Decimal('0.00'))
        self.assertEqual(normalizar_monto(None), Decimal('0.00'))

    def test_monto_error_excel_lanza(self):
        for token in ('#REF!', '#VALUE!', '#DIV/0!', '#N/A'):
            with self.assertRaises(ValueError):
                normalizar_monto(token)

    def test_codigo_preserva_ceros(self):
        self.assertEqual(normalizar_codigo('097'), '097')
        self.assertEqual(normalizar_codigo('010'), '010')
        self.assertEqual(normalizar_codigo(97), '97')

    def test_detectar_header_desplazado(self):
        filas = [
            ['GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA'],
            [],
            [],
            HEADER_GASTOS,
            fila_detalle(),
            fila_detalle(denom='Otra apertura'),
        ]
        indice = detectar_header(filas, HEADER_GASTOS)
        self.assertEqual(indice, 3)

    def test_clasificar_filas(self):
        from .models import ClasificacionFila
        self.assertEqual(
            clasificar_fila({'tipo': 'P'}), ClasificacionFila.PROGRAM_HEADER
        )
        self.assertEqual(
            clasificar_fila({'tipo': 'PROGRAMA'}),
            ClasificacionFila.PROGRAM_HEADER,
        )
        self.assertEqual(
            clasificar_fila({'tipo': 'SP'}), ClasificacionFila.SUBPROGRAM_HEADER
        )
        self.assertEqual(
            clasificar_fila({'tipo': 'TS'}), ClasificacionFila.SUBTOTAL
        )
        self.assertEqual(
            clasificar_fila({'tipo': 'T'}), ClasificacionFila.TOTAL
        )
        self.assertEqual(
            clasificar_fila({'tipo': ''}), ClasificacionFila.EMPTY
        )
        self.assertEqual(
            clasificar_fila({'tipo': '', 'denominacion': 'X'}),
            ClasificacionFila.DETAIL,
        )
        self.assertEqual(
            clasificar_fila({'tipo': 'X'}), ClasificacionFila.DETAIL
        )


class ImportadorUploadTests(ImportadorBase):
    def test_upload_parsea_con_header_desplazado(self):
        filas = [
            ['GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA'],
            ['PRESUPUESTO 2023'],
            [],
            HEADER_GASTOS,
            fila_detalle(),
        ]
        resp = self.subir(construir_xlsx(filas))
        self.assertEqual(resp.status_code, 201, resp.content[:500])
        data = resp.data
        self.assertEqual(data['estado'], 'STAGING')
        self.assertEqual(data['hoja_seleccionada'], 'gastos')
        self.assertEqual(data['gestion_anio'], 2030)
        self.assertEqual(len(data['sha256']), 64)

        importacion = BudgetImport.objects.get(pk=data['id'])
        detalles = importacion.detalles.all()
        self.assertEqual(detalles.count(), 1)
        detalle = detalles.first()
        self.assertEqual(detalle.clasificacion, 'DETAIL')
        self.assertEqual(detalle.fila, 5)
        self.assertEqual(detalle.datos_json['denominacion'], 'Apertura demo')
        self.assertEqual(detalle.datos_json['programa'], '097')
        self.assertEqual(detalle.datos_json['ct'], '500.00')
        self.assertEqual(detalle.datos_json['re'], '300.00')
        self.assertEqual(detalle.datos_json['total'], '1100.00')
        self.assertIn('columnas', importacion.mapeo_json)
        self.assertIn('fuentes', importacion.mapeo_json)

    def test_listar_importaciones_por_gestion(self):
        self.subir(construir_xlsx([HEADER_GASTOS, fila_detalle()]))
        resp = self.client.get(
            f'{BUDGET_URL}imports/', {'gestion': str(self.gestion.id)}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_hojas_endpoint(self):
        resp = self.subir(construir_xlsx([HEADER_GASTOS, fila_detalle()]))
        importacion_id = resp.data['id']
        resp = self.client.get(f'{BUDGET_URL}imports/{importacion_id}/hojas/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['hojas'], ['gastos'])

    def test_map_hoja_y_mapeo_personalizado(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'gastos'
        ws.append(['UNIDAD EJECUTIVA', 'V', 'PROG.', 'DENOMINACIÓN DEL PROYECTO',
                   'CT', 'Total Presupuesto'])
        ws.append(['SMFA', '', '097', 'Apertura mapeada', '250.00', '250.00'])
        buf = BytesIO()
        wb.save(buf)
        resp = self.subir(buf.getvalue())
        self.assertEqual(resp.status_code, 201, resp.content[:500])
        importacion = BudgetImport.objects.get(pk=resp.data['id'])
        # Re-mapeo: CT ahora se interpreta como IDH (otra fuente).
        resp_map = self.client.post(
            f"{BUDGET_URL}imports/{importacion.id}/map/",
            {'hoja': 'gastos', 'mapeo': {'fuentes': {'ct': '11'}}},
            format='json',
        )
        self.assertEqual(resp_map.status_code, 200, resp_map.data)
        importacion.refresh_from_db()
        self.assertEqual(importacion.mapeo_json['fuentes']['ct'], '11')
        detalle = importacion.detalles.first()
        self.assertEqual(detalle.datos_json['ct'], '250.00')

    def test_upload_mime_no_permitido_rechazado(self):
        archivo = SimpleUploadedFile(
            'datos.txt', b'no es excel', content_type='text/plain',
        )
        resp = self.client.post(
            f'{BUDGET_URL}imports/',
            {'gestion': str(self.gestion.id), 'perfil': 'SISPOA_GASTOS_HISTORICO',
             'archivo': archivo},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_usuario_sin_capacidad_import_no_puede_subir(self):
        rol = Rol.objects.create(codigo='rol_sin_import', nombre='Sin importar')
        usuario = Usuario.objects.create_user(
            email='sin@import.test', password='test2026'
        )
        usuario.roles.add(rol)
        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{BUDGET_URL}imports/',
            {'gestion': str(self.gestion.id), 'perfil': 'SISPOA_GASTOS_HISTORICO',
             'archivo': SimpleUploadedFile(
                 'g.xlsx', construir_xlsx([HEADER_GASTOS, fila_detalle()]),
                 content_type=XLSX_MIME,
             )},
            format='multipart',
        )
        self.assertEqual(resp.status_code, 403, resp.data)


class ImportadorValidacionTests(ImportadorBase):
    def test_ref_en_monto_genera_critical(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(ct='#REF!'),
        ])
        self.assertEqual(importacion.estado, 'STAGING')
        criticos = ImportError.objects.filter(
            importacion=importacion, severidad='CRITICAL',
        )
        self.assertTrue(criticos.exists())
        self.assertIn('#REF!', criticos.first().mensaje)
        self.assertEqual(criticos.first().campo, 'ct')
        detalle = importacion.detalles.first()
        self.assertEqual(detalle.estado, 'ERROR')

    def test_monto_negativo_es_critical(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(ct='-100.00'),
        ])
        self.assertEqual(importacion.estado, 'STAGING')
        self.assertTrue(ImportError.objects.filter(
            importacion=importacion, severidad='CRITICAL',
            mensaje__contains='negativo',
        ).exists())

    def test_fuente_inexistente_es_critical(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(),
        ])
        # Quitar la fuente 41 del catálogo → CT/IDH quedan inválidas.
        FuenteFinanciamiento.objects.filter(codigo='41', gestion=2030).delete()
        importacion.errores.all().delete()
        validar_importacion(importacion)
        importacion.refresh_from_db()
        self.assertEqual(importacion.estado, 'STAGING')
        criticos = ImportError.objects.filter(
            importacion=importacion, severidad='CRITICAL',
        )
        self.assertTrue(criticos.exists())
        self.assertIn('no existe', criticos.first().mensaje)

    def test_programa_inexistente_es_critical(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(prog='999'),
        ])
        self.assertEqual(importacion.estado, 'STAGING')
        self.assertTrue(ImportError.objects.filter(
            importacion=importacion, severidad='CRITICAL',
            mensaje__contains='999',
        ).exists())

    def test_denominacion_vacia_es_error(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(denom=''),
        ])
        self.assertEqual(importacion.estado, 'STAGING')
        self.assertTrue(ImportError.objects.filter(
            importacion=importacion, severidad='ERROR',
            campo='denominacion',
        ).exists())

    def test_duplicado_es_error(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(),
            fila_detalle(),
        ])
        self.assertEqual(importacion.estado, 'STAGING')
        self.assertTrue(ImportError.objects.filter(
            importacion=importacion, severidad='ERROR',
            mensaje__contains='duplicada',
        ).exists())

    def test_todo_valido_pasa_a_validado(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(),
            fila_detalle(sisin='87654321', denom='Segunda apertura',
                         ct='100.00', re='', idh='', tgn='',
                         total='100.00'),
        ])
        self.assertEqual(importacion.estado, 'VALIDADO')
        self.assertFalse(ImportError.objects.filter(
            importacion=importacion, severidad__in=('ERROR', 'CRITICAL'),
        ).exists())
        for detalle in importacion.detalles.all():
            self.assertEqual(detalle.estado, 'VALIDO')

    def test_distrito_no_encontrado_es_warning(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(distrito='ZONA INEXISTENTE'),
        ])
        self.assertEqual(importacion.estado, 'VALIDADO')
        self.assertTrue(ImportError.objects.filter(
            importacion=importacion, severidad='WARNING',
            campo='distrito',
        ).exists())

    def test_errores_endpoint_devuelve_hallazgos(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(ct='#REF!'),
        ])
        resp = self.client.get(f'{BUDGET_URL}imports/{importacion.id}/errors/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['severidad'], 'CRITICAL')
        self.assertEqual(resp.data[0]['fila'], 2)


class ImportadorAplicacionTests(ImportadorBase):
    def _libro_completo(self):
        return [
            HEADER_GASTOS,
            ['', 'SECRETARÍA', 'URBANO 1', 'DA01', 'UE01', 'P', '097', '', '',
             'Programa 097', '', '', '', '', '', '', ''],
            ['', 'SECRETARÍA', 'URBANO 1', 'DA01', 'UE01', 'SP', '010', '', '',
             'Subprograma 010', '', '', '', '', '', '', ''],
            ['', 'SECRETARÍA', 'URBANO 1', 'DA01', 'UE01', 'TS', '097', '', '',
             'Subtotal programa', '', '500.00', '300.00', '', '200.00',
             '100.00', '1100.00'],
            ['', 'SECRETARÍA', 'URBANO 1', 'DA01', 'UE01', 'T', '097', '', '',
             'Total general', '', '500.00', '300.00', '', '200.00',
             '100.00', '1100.00'],
            fila_detalle(),
            fila_detalle(sisin='87654321', denom='Segunda apertura'),
        ]

    def test_filas_p_sp_ts_t_no_generan_aperturas(self):
        importacion, _, _ = self.subir_y_validar(self._libro_completo())
        self.assertEqual(importacion.detalles.count(), 4)  # TS + T + 2 DETAIL
        self.assertEqual(
            importacion.detalles.filter(clasificacion='DETAIL').count(), 2
        )
        resp = self.client.post(
            f'{BUDGET_URL}imports/{importacion.id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['resultado']['aperturas_creadas'], 2)
        from .models import Allocation
        aperturas = Allocation.objects.filter(gestion=self.gestion)
        self.assertEqual(aperturas.count(), 2)

    def test_apply_con_critical_devuelve_400(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(ct='#REF!'),
        ])
        resp = self.client.post(
            f'{BUDGET_URL}imports/{importacion.id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('crítico', str(resp.data))
        from .models import Allocation
        self.assertFalse(Allocation.objects.filter(gestion=self.gestion).exists())
        importacion.refresh_from_db()
        self.assertEqual(importacion.estado, 'STAGING')

    def test_apply_todo_valido_crea_borradores_y_aplica(self):
        importacion, _, _ = self.subir_y_validar(self._libro_completo())
        resp = self.client.post(
            f'{BUDGET_URL}imports/{importacion.id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        importacion.refresh_from_db()
        self.assertEqual(importacion.estado, 'APLICADO')

        from .models import Allocation, AllocationSource
        aperturas = Allocation.objects.filter(gestion=self.gestion)
        self.assertEqual(aperturas.count(), 2)
        self.assertEqual(
            set(aperturas.values_list('codigo_sisin', flat=True)),
            {'12345678', '87654321'},
        )
        for apertura in aperturas:
            self.assertEqual(apertura.estado, 'BORRADOR')
            self.assertEqual(apertura.tipo_apertura, 'DETAIL')
            self.assertEqual(apertura.categoria.codigo, '097')
            self.assertIsNotNone(apertura.distrito)
        fuentes = AllocationSource.objects.filter(
            allocation__in=aperturas,
        ).select_related('fuente')
        por_codigo = {}
        for fuente in fuentes:
            por_codigo[fuente.fuente.codigo] = (
                por_codigo.get(fuente.fuente.codigo, 0) + fuente.monto
            )
        self.assertEqual(por_codigo['41'], Decimal('1400.00'))  # (CT 500 + IDH 200) x2
        self.assertEqual(por_codigo['20'], Decimal('600.00'))   # RE x2
        self.assertEqual(por_codigo['11'], Decimal('200.00'))   # TGN x2

        evento = EventoAuditoria.objects.filter(
            entidad='BudgetImport', entidad_id=str(importacion.id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'crear')
        self.assertIn('aplicada', evento.resumen.lower())

    def test_apply_doble_rechazado(self):
        importacion, _, _ = self.subir_y_validar(self._libro_completo())
        self.client.post(
            f'{BUDGET_URL}imports/{importacion.id}/apply/', {}, format='json',
        )
        resp = self.client.post(
            f'{BUDGET_URL}imports/{importacion.id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)

# ===========================================================================
# Fase 6 - Distribución territorial (reparto por distrito + reservas)
# ===========================================================================
from apps.territorio.models import Distrito  # noqa: E402

from .models import (  # noqa: E402
    TerritorialAllocation,
    TerritorialDistribution,
)

TERRITORIAL_URL = BUDGET_URL + 'territorial-distributions/'


def crear_distrito(codigo, nombre):
    return Distrito.objects.create(codigo=codigo, nombre=nombre)


class TerritorialBase(DistribucionBase):
    """Base territorial: techo fijado de 1500.00 sobre la fuente 11."""

    def setUp(self):
        super().setUp()
        self.d1 = crear_distrito('D1', 'Centro')
        self.d2 = crear_distrito('D2', 'Norte')
        self.d3 = crear_distrito('D3', 'Sur')

    def crear_distribucion(self, metodo='POBLACION', bolsa='600.00',
                           distritos=None):
        distritos = distritos or [
            {'distrito': str(self.d1.id), 'poblacion': 100},
            {'distrito': str(self.d2.id), 'poblacion': 200},
            {'distrito': str(self.d3.id), 'poblacion': 300},
        ]
        return self.client.post(TERRITORIAL_URL, {
            'gestion': str(self.gestion.id),
            'fuente': str(self.fuente.id),
            'organismo': str(self.organismo.id),
            'metodo': metodo,
            'bolsa_total': bolsa,
            'distritos': distritos,
        }, format='json')

    def calcular(self, pk):
        return self.client.post(
            f'{TERRITORIAL_URL}{pk}/calcular/', {}, format='json',
        )

    def aplicar(self, pk):
        return self.client.post(
            f'{TERRITORIAL_URL}{pk}/aplicar/', {}, format='json',
        )

    def liberar(self, pk):
        return self.client.post(
            f'{TERRITORIAL_URL}{pk}/liberar/', {}, format='json',
        )


class TerritorialRepartoTests(TerritorialBase):
    def test_poblacion_reparte_proporcional_exacto(self):
        resp = self.crear_distribucion()
        self.assertEqual(resp.status_code, 201, resp.data)
        pk = resp.data['id']
        self.assertEqual(resp.data['estado'], 'BORRADOR')
        self.assertEqual(len(resp.data['asignaciones']), 3)

        resp = self.calcular(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'CALCULADA')
        montos = {
            a['distrito_detalle']['codigo']: Decimal(a['monto_final'])
            for a in resp.data['asignaciones']
        }
        self.assertEqual(montos['D1'], Decimal('100.00'))
        self.assertEqual(montos['D2'], Decimal('200.00'))
        self.assertEqual(montos['D3'], Decimal('300.00'))
        self.assertEqual(sum(montos.values()), Decimal('600.00'))
        self.assertEqual(resp.data['total_asignado'], '600.00')

    def test_redondeo_distribuye_centavo_con_sum_exacta(self):
        resp = self.crear_distribucion(
            bolsa='100.00',
            distritos=[
                {'distrito': str(self.d1.id), 'poblacion': 1},
                {'distrito': str(self.d2.id), 'poblacion': 1},
                {'distrito': str(self.d3.id), 'poblacion': 1},
            ],
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        pk = resp.data['id']

        resp = self.calcular(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        montos = sorted(
            Decimal(a['monto_final'])
            for a in resp.data['asignaciones']
        )
        self.assertEqual(
            montos, [Decimal('33.33'), Decimal('33.33'), Decimal('33.34')]
        )
        self.assertEqual(sum(montos), Decimal('100.00'))
        ajustes = [Decimal(a['ajuste']) for a in resp.data['asignaciones']]
        self.assertEqual(sum(ajustes), Decimal('0.01'))

    def test_porcentaje_reparte_50_30_20(self):
        resp = self.crear_distribucion(
            metodo='PORCENTAJE', bolsa='1000.00',
            distritos=[
                {'distrito': str(self.d1.id), 'porcentaje': '50'},
                {'distrito': str(self.d2.id), 'porcentaje': '30'},
                {'distrito': str(self.d3.id), 'porcentaje': '20'},
            ],
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        pk = resp.data['id']

        resp = self.calcular(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        montos = {
            a['distrito_detalle']['codigo']: Decimal(a['monto_final'])
            for a in resp.data['asignaciones']
        }
        self.assertEqual(montos['D1'], Decimal('500.00'))
        self.assertEqual(montos['D2'], Decimal('300.00'))
        self.assertEqual(montos['D3'], Decimal('200.00'))
        self.assertEqual(sum(montos.values()), Decimal('1000.00'))

    def test_porcentaje_debe_sumar_100(self):
        resp = self.crear_distribucion(
            metodo='PORCENTAJE', bolsa='1000.00',
            distritos=[
                {'distrito': str(self.d1.id), 'porcentaje': '40'},
                {'distrito': str(self.d2.id), 'porcentaje': '30'},
                {'distrito': str(self.d3.id), 'porcentaje': '20'},
            ],
        )
        pk = resp.data['id']
        resp = self.calcular(pk)
        self.assertEqual(resp.status_code, 400, resp.data)
        distribucion = TerritorialDistribution.objects.get(pk=pk)
        self.assertEqual(distribucion.estado, 'BORRADOR')

    def test_manual_requiere_suma_exacta(self):
        resp = self.crear_distribucion(
            metodo='MANUAL', bolsa='600.00',
            distritos=[
                {'distrito': str(self.d1.id), 'monto': '100.00'},
                {'distrito': str(self.d2.id), 'monto': '200.00'},
                {'distrito': str(self.d3.id), 'monto': '300.00'},
            ],
        )
        pk = resp.data['id']
        resp = self.calcular(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        montos = {
            a['distrito_detalle']['codigo']: Decimal(a['monto_final'])
            for a in resp.data['asignaciones']
        }
        self.assertEqual(montos['D1'], Decimal('100.00'))
        self.assertEqual(montos['D2'], Decimal('200.00'))
        self.assertEqual(montos['D3'], Decimal('300.00'))

    def test_recalcular_con_distritos_actualiza_montos(self):
        resp = self.crear_distribucion()
        pk = resp.data['id']
        self.assertEqual(self.calcular(pk).status_code, 200)

        resp = self.client.post(
            f'{TERRITORIAL_URL}{pk}/calcular/',
            {'distritos': [
                {'distrito': str(self.d1.id), 'poblacion': 300},
                {'distrito': str(self.d2.id), 'poblacion': 200},
                {'distrito': str(self.d3.id), 'poblacion': 100},
            ]},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        montos = {
            a['distrito_detalle']['codigo']: Decimal(a['monto_final'])
            for a in resp.data['asignaciones']
        }
        self.assertEqual(montos['D1'], Decimal('300.00'))
        self.assertEqual(montos['D2'], Decimal('200.00'))
        self.assertEqual(montos['D3'], Decimal('100.00'))


class TerritorialAplicarLiberarTests(TerritorialBase):
    def _aplicada(self):
        pk = self.crear_distribucion().data['id']
        self.assertEqual(self.calcular(pk).status_code, 200)
        return pk

    def test_aplicar_crea_reservas_distritales_y_suma_bolsa(self):
        pk = self._aplicada()
        resp = self.aplicar(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'APLICADA')

        reservas = Reserve.objects.filter(
            gestion=self.gestion, tipo='DISTRITAL', estado='ACTIVA',
        )
        self.assertEqual(reservas.count(), 3)
        self.assertEqual(
            sum(r.monto for r in reservas), Decimal('600.00')
        )
        for asignacion in TerritorialAllocation.objects.filter(
            distribucion_id=pk,
        ):
            self.assertTrue(reservas.filter(
                motivo=f'Distribución territorial: {asignacion.distrito}',
            ).exists())
        self.assertEqual(
            disponible_por_fuente(self.gestion)[self.fuente.id],
            Decimal('900.00'),
        )

    def test_aplicar_con_bolsa_mayor_al_disponible_rollback_total(self):
        resp = self.crear_distribucion(bolsa='1600.00')
        pk = resp.data['id']
        self.assertEqual(self.calcular(pk).status_code, 200)

        resp = self.aplicar(pk)
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['requested'], '1600.00')
        self.assertEqual(resp.data['details']['available'], '1500.00')
        self.assertEqual(resp.data['details']['difference'], '100.00')
        self.assertEqual(
            Reserve.objects.filter(gestion=self.gestion).count(), 0
        )
        distribucion = TerritorialDistribution.objects.get(pk=pk)
        self.assertEqual(distribucion.estado, 'CALCULADA')

    def test_liberar_devuelve_reservas_y_estado_calculada(self):
        pk = self._aplicada()
        resp = self.aplicar(pk)
        self.assertEqual(resp.status_code, 200, resp.data)

        resp = self.liberar(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'CALCULADA')
        self.assertEqual(
            Reserve.objects.filter(
                gestion=self.gestion, estado='ACTIVA',
            ).count(), 0
        )
        self.assertEqual(
            Reserve.objects.filter(
                gestion=self.gestion, estado='LIBERADA',
            ).count(), 3
        )
        self.assertEqual(
            disponible_por_fuente(self.gestion)[self.fuente.id],
            Decimal('1500.00'),
        )

    def test_liberar_no_aplicada_rechazado(self):
        pk = self._aplicada()
        resp = self.liberar(pk)
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_calcular_sobre_aplicada_rechazado(self):
        pk = self._aplicada()
        self.assertEqual(self.aplicar(pk).status_code, 200)
        resp = self.calcular(pk)
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_update_sobre_aplicada_rechazado(self):
        pk = self._aplicada()
        self.assertEqual(self.aplicar(pk).status_code, 200)
        resp = self.client.patch(
            f'{TERRITORIAL_URL}{pk}/',
            {'bolsa_total': '500.00'}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_listar_por_gestion(self):
        self.crear_distribucion()
        resp = self.client.get(
            TERRITORIAL_URL, {'gestion': str(self.gestion.id)},
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['metodo'], 'POBLACION')


# ===========================================================================
# Fase 7 - Fijación de la distribución (validación Σfuente + checksum +
# inmutabilidad + versión de ajuste)
# ===========================================================================
from .services import (  # noqa: E402
    actualizar_allocation,
    ajuste_distribucion,
    aprobar_distribucion,
    checksum_distribucion,
    enviar_distribucion_a_revision,
    fijar_distribucion,
    validar_distribucion_completa,
)


class FijacionDistribucionBase(DistribucionBase):
    """Base: gestión 2030 con techo fijado de 1500.00 (fuente 11)."""

    def crear_gestion_con_techo(self, anio, monto):
        """Gestión nueva HABILITADA con techo fijado de `monto` (1 fuente)."""
        gestion = crear_gestion(anio, estado='HABILITADA')
        fuente = FuenteFinanciamiento.objects.create(
            codigo=str(anio), denominacion=f'Fuente {anio}', gestion=anio,
            fecha_vigencia_desde=timezone.now().date(),
        )
        organismo = OrganismoFinanciador.objects.create(
            codigo=str(anio) + '1', denominacion=f'Origen {anio}', gestion=anio,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        ceiling = DirectiveCeiling.objects.get(gestion=gestion)
        version = DirectiveCeilingVersion.objects.get(
            ceiling=ceiling, numero=1
        )
        CeilingResource.objects.create(
            version=version, origen='SIGEP', monto=monto, concepto='CT',
            fuente=fuente, organismo=organismo,
            created_by=self.admin, updated_by=self.admin,
        )
        enviar_a_revision(version, self.admin)
        aprobar(version, self.admin)
        fijar_techo(version, self.admin)
        return gestion, fuente, organismo

    def crear_apertura_en(self, gestion, fuente, organismo, monto,
                          denominacion='Apertura demo'):
        data = {
            'gestion': str(gestion.id),
            'denominacion': denominacion,
            'codigo_sisin': '12345678',
            'fuentes': [{
                'fuente': str(fuente.id),
                'organismo': str(organismo.id),
                'monto': monto,
            }],
        }
        return self.client.post(
            f'{BUDGET_URL}allocations/', data, format='json',
        )

    def crear_reserva_en(self, gestion, fuente, organismo, monto):
        return self.client.post(
            f'{BUDGET_URL}reserves/',
            {'gestion': str(gestion.id), 'fuente': str(fuente.id),
             'organismo': str(organismo.id), 'tipo': 'OTRA',
             'motivo': 'Contingencia', 'monto': monto},
            format='json',
        )

    def version_activa(self):
        from .services import version_distribucion_activa
        return version_distribucion_activa(self.gestion)

    def fijar_v1_api(self):
        """Distribución completa (1000 + 500) y freeze vía API."""
        self.crear_apertura(monto='1000.00', denominacion='A fijar')
        self.crear_reserva_api(monto='500.00')
        version = self.version_activa()
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/approve/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/freeze/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        version.refresh_from_db()
        return version

    def _usuario_sin_capacidades(self):
        rol = Rol.objects.create(codigo='rol_basico_f7', nombre='Rol básico')
        usuario = Usuario.objects.create_user(
            email='basico@f7.test', password='test2026'
        )
        usuario.roles.add(rol)
        return usuario


class FijacionValidacionTests(FijacionDistribucionBase):
    def test_validacion_completa_true_con_diferencia_cero(self):
        # techo 1000; distribuido 600 + reservado 400 = 1000 → valida.
        gestion, fuente, organismo = self.crear_gestion_con_techo(2035, '1000.00')
        resp = self.crear_apertura_en(
            gestion, fuente, organismo, '600.00', 'Apertura A',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        resp = self.crear_reserva_en(gestion, fuente, organismo, '400.00')
        self.assertEqual(resp.status_code, 201, resp.data)

        resultado = validar_distribucion_completa(gestion)
        self.assertTrue(resultado['valida'])
        self.assertEqual(len(resultado['diferencias']), 1)
        fila = resultado['diferencias'][0]
        self.assertEqual(fila['techo'], Decimal('1000.00'))
        self.assertEqual(fila['distribuido'], Decimal('600.00'))
        self.assertEqual(fila['reservado'], Decimal('400.00'))
        self.assertEqual(fila['diferencia'], Decimal('0.00'))

    def test_validacion_detecta_diferencia_no_cero(self):
        # techo 1000; distribuido 600 + reservado 300 = 900 → diferencia 100.
        gestion, fuente, organismo = self.crear_gestion_con_techo(2036, '1000.00')
        resp = self.crear_apertura_en(
            gestion, fuente, organismo, '600.00', 'Apertura A',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        resp = self.crear_reserva_en(gestion, fuente, organismo, '300.00')
        self.assertEqual(resp.status_code, 201, resp.data)

        resultado = validar_distribucion_completa(gestion)
        self.assertFalse(resultado['valida'])
        self.assertEqual(resultado['diferencias'][0]['diferencia'],
                         Decimal('100.00'))

    def test_validacion_tolera_centavo_de_redondeo(self):
        gestion, fuente, organismo = self.crear_gestion_con_techo(2037, '1000.00')
        self.crear_apertura_en(gestion, fuente, organismo, '599.99',
                               'Apertura A')
        self.crear_reserva_en(gestion, fuente, organismo, '400.00')
        resultado = validar_distribucion_completa(gestion)
        self.assertTrue(resultado['valida'])
        self.assertEqual(resultado['diferencias'][0]['diferencia'],
                         Decimal('0.00'))

    def test_validate_endpoint_devuelve_diferencias(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='500.00')
        version = self.version_activa()
        resp = self.client.get(
            f'{BUDGET_URL}distributions/{version.id}/validate/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data['valida'])
        self.assertEqual(resp.data['diferencias'][0]['diferencia'], '0.00')
        self.assertEqual(resp.data['diferencias'][0]['techo'], '1500.00')

    def test_validate_endpoint_con_diferencia(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='200.00')
        version = self.version_activa()
        resp = self.client.get(
            f'{BUDGET_URL}distributions/{version.id}/validate/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertFalse(resp.data['valida'])
        self.assertEqual(resp.data['diferencias'][0]['diferencia'], '300.00')


class FijacionFlujoTests(FijacionDistribucionBase):
    def test_flujo_submit_approve_freeze_secuencial_ok(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='500.00')
        version = self.version_activa()

        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'EN_REVISION')

        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/approve/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'APROBADO')

        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/freeze/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'FIJADO')
        self.assertTrue(resp.data['inmutable'])

    def test_freeze_sin_approve_rechazado(self):
        version = self.version_activa()
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/freeze/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        version.refresh_from_db()
        self.assertEqual(version.estado, 'BORRADOR')
        self.assertFalse(version.inmutable)

    def test_observar_requiere_motivo_y_reenviar(self):
        version = self.version_activa()
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/observe/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)

        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/observe/',
            {'observaciones': 'Falta desglose por fuente'}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'OBSERVADO')
        self.assertEqual(resp.data['observaciones'],
                         'Falta desglose por fuente')
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'EN_REVISION')

    def test_fijar_con_diferencia_no_cero_rechazado(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='200.00')  # 1200 de 1500 → diferencia 300
        version = self.version_activa()
        enviar_distribucion_a_revision(version, self.admin)
        aprobar_distribucion(version, self.admin)

        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/freeze/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('diferencia', json.dumps(resp.data))
        version.refresh_from_db()
        self.assertEqual(version.estado, 'APROBADO')
        self.assertFalse(version.inmutable)
        self.assertEqual(version.hash, '')

    def test_fijar_con_distribucion_completa_queda_fijada(self):
        version = self.fijar_v1_api()
        self.assertEqual(version.estado, 'FIJADO')
        self.assertTrue(version.inmutable)
        self.assertTrue(version.hash)
        self.assertEqual(len(version.hash), 64)
        self.assertTrue(version.verificar_hash())
        self.assertIsNotNone(version.fecha_fijacion)
        self.assertEqual(version.fijado_por, self.admin)
        self.assertEqual(version.observaciones, '')
        evento = EventoAuditoria.objects.filter(
            entidad='DistributionVersion', entidad_id=str(version.id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'aprobar')
        self.assertIn('fijada', evento.resumen.lower())
        self.assertEqual(evento.gestion, 2030)


class FijacionInmutabilidadTests(FijacionDistribucionBase):
    def test_patch_apertura_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        allocation = Allocation.objects.get(gestion=self.gestion)
        resp = self.client.patch(
            f'{BUDGET_URL}allocations/{allocation.id}/',
            {'denominacion': 'Intento'}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        allocation.refresh_from_db()
        self.assertEqual(allocation.denominacion, 'A fijar')

    def test_crear_apertura_tras_fijar_rechazado(self):
        self.fijar_v1_api()
        resp = self.crear_apertura(monto='100.00', denominacion='Post fijación')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('fijada', json.dumps(resp.data))
        self.assertEqual(
            Allocation.objects.filter(denominacion='Post fijación').count(), 0
        )

    def test_crear_reserva_tras_fijar_rechazado(self):
        self.fijar_v1_api()
        resp = self.crear_reserva_api(monto='50.00')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(Reserve.objects.filter(motivo='Contingencia').count(), 1)

    def test_liberar_reserva_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        reserva = Reserve.objects.get(gestion=self.gestion, estado='ACTIVA')
        resp = self.client.post(
            f'{BUDGET_URL}reserves/{reserva.id}/liberar/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'ACTIVA')

    def test_patch_reserva_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        reserva = Reserve.objects.get(gestion=self.gestion, estado='ACTIVA')
        resp = self.client.patch(
            f'{BUDGET_URL}reserves/{reserva.id}/',
            {'monto': '1.00'}, format='json',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        reserva.refresh_from_db()
        self.assertEqual(reserva.monto, Decimal('500.00'))

    def test_eliminar_apertura_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        allocation = Allocation.objects.get(gestion=self.gestion)
        resp = self.client.delete(f'{BUDGET_URL}allocations/{allocation.id}/')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertTrue(Allocation.objects.filter(pk=allocation.pk).exists())

    def test_patch_sobre_version_fijada_rechazado(self):
        version = self.fijar_v1_api()
        resp = self.client.patch(
            f'{BUDGET_URL}distributions/{version.id}/',
            {'observaciones': 'cambio'}, format='json',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        version.refresh_from_db()
        self.assertEqual(version.observaciones, '')


class FijacionAjusteTests(FijacionDistribucionBase):
    def test_ajuste_crea_version_nueva_y_la_fijada_sigue_intacta(self):
        v1 = self.fijar_v1_api()
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{v1.id}/ajuste/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['numero'], 2)
        self.assertEqual(resp.data['estado'], 'BORRADOR')
        self.assertFalse(resp.data['inmutable'])

        v2 = DistributionVersion.objects.get(gestion=self.gestion, numero=2)
        self.assertEqual(v2.observaciones, 'Ajuste de la versión 1 (fijada).')
        v1.refresh_from_db()
        self.assertEqual(v1.estado, 'FIJADO')
        self.assertTrue(v1.inmutable)
        self.assertTrue(v1.hash)
        self.assertEqual(v1.verificar_hash(), True)
        self.assertFalse(v2.reservas.exists())
        self.assertFalse(v2.aperturas.exists())

    def test_ajuste_requiere_version_fijada(self):
        version = self.version_activa()
        resp = self.client.post(
            f'{BUDGET_URL}distributions/{version.id}/ajuste/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(
            DistributionVersion.objects.filter(gestion=self.gestion).count(), 1
        )

    def test_version_distribucion_activa_devuelve_la_ajustada(self):
        v1 = self.fijar_v1_api()
        self.client.post(
            f'{BUDGET_URL}distributions/{v1.id}/ajuste/', {}, format='json',
        )
        from .services import version_distribucion_activa
        activa = version_distribucion_activa(self.gestion)
        self.assertEqual(activa.numero, 2)
        self.assertEqual(activa.estado, 'BORRADOR')


class FijacionChecksumTests(FijacionDistribucionBase):
    def test_checksum_cambia_con_monto_y_es_estable_ante_reorden(self):
        version = self.version_activa()
        self.crear_apertura(monto='100.00', denominacion='A')
        self.crear_apertura(monto='200.00', denominacion='B')

        h1 = checksum_distribucion(version)
        self.assertEqual(len(h1), 64)

        # Reorden: intercambiar montos entre aperturas (mismo set de tuplas
        # (fuente, organismo, monto)) → hash idéntico.
        a = Allocation.objects.get(gestion=self.gestion, denominacion='A')
        b = Allocation.objects.get(gestion=self.gestion, denominacion='B')
        actualizar_allocation(a, self.admin, {'fuentes': [{
            'fuente': self.fuente.id, 'organismo': self.organismo.id,
            'monto': Decimal('200.00'),
        }]})
        actualizar_allocation(b, self.admin, {'fuentes': [{
            'fuente': self.fuente.id, 'organismo': self.organismo.id,
            'monto': Decimal('100.00'),
        }]})
        h2 = checksum_distribucion(version)
        self.assertEqual(h1, h2)

        # Cambio de monto → hash distinto.
        actualizar_allocation(a, self.admin, {'fuentes': [{
            'fuente': self.fuente.id, 'organismo': self.organismo.id,
            'monto': Decimal('150.00'),
        }]})
        h3 = checksum_distribucion(version)
        self.assertNotEqual(h1, h3)

    def test_checksum_incluye_reservas(self):
        version = self.version_activa()
        self.crear_apertura(monto='1000.00', denominacion='A')
        sin_reservas = checksum_distribucion(version)
        self.crear_reserva_api(monto='200.00')
        con_reservas = checksum_distribucion(version)
        self.assertNotEqual(sin_reservas, con_reservas)

    def test_checksum_estable_en_verificacion_de_fijada(self):
        version = self.fijar_v1_api()
        self.assertEqual(version.hash, checksum_distribucion(version))


class FijacionPermisosTests(FijacionDistribucionBase):
    def test_submit_require_capacidad_aprobacion(self):
        version = self.version_activa()
        usuario = self._usuario_sin_capacidades()
        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{BUDGET_URL}distributions/{version.id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 403, resp.data)
        version.refresh_from_db()
        self.assertEqual(version.estado, 'BORRADOR')

    def test_validate_disponible_con_autenticacion(self):
        version = self.version_activa()
        usuario = self._usuario_sin_capacidades()
        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.get(
            f'{BUDGET_URL}distributions/{version.id}/validate/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn('valida', resp.data)
