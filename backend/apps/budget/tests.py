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
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.auditoria.models import EventoAuditoria
from apps.catalogos.models import (
    FuenteFinanciamiento,
    ObjetoGasto,
    OrganismoFinanciador,
    RubroRecurso,
)
from apps.gestion.models import CicloFormulacion, EtapaFormulacion, GestionFiscal

from .models import (
    RecursoTecho,
    TechoDirectivo,
    TechoVersion,
    GastoObligatorio,
    CategoriaProgramaticaTecho,
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
    # PIP-DB-003: gestion.0003 siembra 2026/2027; get_or_create evita
    # colisiones de unicidad con la semilla (idempotente).
    return GestionFiscal.objects.get_or_create(anio=anio, defaults=extra)[0]


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
            codigo='11', denominacion='Tesoro General', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.organismo = OrganismoFinanciador.objects.create(
            codigo='111', denominacion='Tesoro General de la Nación',
            gestion=self.gestion, fecha_vigencia_desde=timezone.now().date(),
        )
        self.rubro = RubroRecurso.objects.create(
            codigo='11', denominacion='Impuestos municipales', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(self.gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.ceiling = TechoDirectivo.objects.get(gestion=self.gestion)
        self.version = TechoVersion.objects.get(
            ceiling=self.ceiling, numero=1
        )

    def crear_recurso(self, origen='SIGEP', monto='1000.00', concepto='Recurso',
                      fuente=None, organismo=None, rubro=None):
        return RecursoTecho.objects.create(
            version=self.version, origen=origen, monto=monto,
            concepto=concepto, fuente=fuente, organismo=organismo, rubro=rubro,
            created_by=self.admin, updated_by=self.admin,
        )

    def crear_gasto(self, monto='200.00', denominacion='Gasto obligatorio',
                    fuente=None, organismo=None):
        return GastoObligatorio.objects.create(
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
            TechoDirectivo.objects.filter(gestion=gestion_cerrada).exists()
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
            entidad='TechoVersion', entidad_id=str(version.id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'aprobar')
        self.assertIn('fijado', evento.resumen.lower())
        self.assertEqual(evento.gestion.anio, 2030)

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
                entidad='TechoVersion', entidad_id=str(v.id),
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
        self.assertTrue(GastoObligatorio.objects.filter(pk=gasto.pk).exists())

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
        v1 = TechoVersion.objects.get(ceiling=self.ceiling, numero=1)

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
        # anio bajo (sin gestiones previas, incluso con la semilla 2026/2027)
        # garantiza gestion_anterior None de forma determinista.
        resp = self.client.post(self.url, {'anio': 2020}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['anio'], 2020)
        self.assertEqual(resp.data['estado'], 'preparacion')
        self.assertEqual(resp.data['fecha_inicio'], '2020-01-01')
        self.assertEqual(resp.data['fecha_cierre_programada'], '2020-12-31')
        self.assertIsNone(resp.data['gestion_anterior'])
        self.assertTrue(GestionFiscal.objects.filter(anio=2020).exists())

    def test_crear_gestion_con_documento_expone_metadatos_de_cargado(self):
        archivo = SimpleUploadedFile(
            'habilitacion-2029.pdf', b'%PDF-1.4 fiscal year',
            content_type='application/pdf',
        )
        resp = self.client.post(
            self.url,
            {'anio': 2029, 'documento_habilitacion': archivo},
            format='multipart',
        )

        self.assertEqual(resp.status_code, 201, resp.data)
        gestion = GestionFiscal.objects.get(anio=2029)
        self.assertEqual(gestion.fecha_inicio.isoformat(), '2029-01-01')
        self.assertEqual(
            gestion.fecha_cierre_programada.isoformat(), '2029-12-31'
        )
        self.assertEqual(resp.data['fecha_inicio'], '2029-01-01')
        self.assertEqual(resp.data['fecha_cierre_programada'], '2029-12-31')
        self.assertTrue(resp.data['documento_habilitacion'])
        self.assertEqual(resp.data['encargado_cargado'], self.admin.email)
        self.assertIsNotNone(resp.data['fecha_cargado'])
        self.assertIsNone(gestion.fecha_cierre)

    def test_serializar_registro_legacy_deriva_fechas_anuales(self):
        gestion = crear_gestion(2019)
        GestionFiscal.objects.filter(pk=gestion.pk).update(
            fecha_inicio=None, fecha_cierre_programada=None,
        )

        resp = self.client.get(f'{self.url}{gestion.id}/')

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['fecha_inicio'], '2019-01-01')
        self.assertEqual(resp.data['fecha_cierre_programada'], '2019-12-31')

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
        self.assertEqual(evento.first().gestion.anio, 2028)

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


    # -- Reapertura ----------------------------------------------------------

    def test_reopen_devuelve_la_gestion_cerrada_al_ciclo(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        self.client.post(f'{self.url}{gestion.id}/close/', {}, format='json')

        resp = self.client.post(
            f'{self.url}{gestion.id}/reopen/',
            {'motivo': 'se cerró por error'}, format='json',
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')
        self.assertIsNone(gestion.fecha_cierre)
        # Vuelve a tomar el candado: SIS-POA opera otra vez sobre ella.
        self.assertTrue(gestion.activa)
        self.assertTrue(validar_gestion_para_techo(gestion))
        evento = EventoAuditoria.objects.filter(
            entidad='GestionFiscal', entidad_id=str(gestion.id),
            accion='reabrir',
        ).first()
        self.assertIsNotNone(evento)
        self.assertIn('se cerró por error', evento.resumen)

    def test_reopen_sin_motivo_rechazado(self):
        # El motivo es lo que separa "se puede" de "se puede sin dejar rastro".
        gestion = crear_gestion(2028, estado='CERRADA')
        resp = self.client.post(
            f'{self.url}{gestion.id}/reopen/', {'motivo': '  '}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'CERRADA')

    def test_reopen_de_gestion_no_cerrada_rechazado(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        resp = self.client.post(
            f'{self.url}{gestion.id}/reopen/', {'motivo': 'x'}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_reopen_con_otra_gestion_habilitada_rechazado(self):
        # El candado admite una sola: reabrir no puede robárselo a la que
        # está en curso, tiene que cerrarse esa primero.
        GestionFiscal.objects.update(activa=False)
        cerrada = crear_gestion(2028, estado='CERRADA')
        en_curso = crear_gestion(2029, estado='preparacion')
        self.client.post(f'{self.url}{en_curso.id}/enable/', {}, format='json')

        resp = self.client.post(
            f'{self.url}{cerrada.id}/reopen/', {'motivo': 'x'}, format='json',
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('2029', str(resp.data))
        cerrada.refresh_from_db()
        self.assertFalse(cerrada.activa)

    # -- Gobernanza: reabrir y eliminar son de la jefatura --------------------

    def _usuario_con(self, *capacidades, email):
        from apps.accounts.models import Capacidad
        rol = Rol.objects.create(
            codigo=f'rol_{email.split("@")[0]}', nombre='Rol de prueba',
        )
        for codigo in capacidades:
            capacidad, _ = Capacidad.objects.get_or_create(
                codigo=codigo, defaults={'nombre': codigo, 'sistema': 'sis-poa'},
            )
            rol.capacidades.add(capacidad)
        usuario = Usuario.objects.create_user(email=email, password='test2026')
        usuario.roles.add(rol)
        cliente = APIClient()
        cliente.force_authenticate(user=usuario)
        return cliente

    def test_administrar_el_presupuesto_no_alcanza_para_reabrir(self):
        # `sis_poa.budget.manage` la tiene cualquiera que administre el
        # presupuesto. Reabrir revierte un acto formal: es de la jefatura.
        cliente = self._usuario_con(
            'sis_poa.budget.manage', email='tecnico@budget.test',
        )
        gestion = crear_gestion(2028, estado='CERRADA')

        resp = cliente.post(
            f'{self.url}{gestion.id}/reopen/', {'motivo': 'x'}, format='json',
        )

        self.assertEqual(resp.status_code, 403, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'CERRADA')

    def test_la_jefatura_de_poa_reabre(self):
        cliente = self._usuario_con(
            'sis_poa.budget.reopen', email='jefatura@budget.test',
        )
        GestionFiscal.objects.update(activa=False)
        gestion = crear_gestion(2028, estado='CERRADA')

        resp = cliente.post(
            f'{self.url}{gestion.id}/reopen/',
            {'motivo': 'cierre anticipado por error de carga'}, format='json',
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')

    def test_administrar_el_presupuesto_no_alcanza_para_eliminar(self):
        cliente = self._usuario_con(
            'sis_poa.budget.manage', email='tecnico2@budget.test',
        )
        gestion = crear_gestion(2028, estado='preparacion')

        resp = cliente.delete(f'{self.url}{gestion.id}/')

        self.assertEqual(resp.status_code, 403, resp.data)
        self.assertTrue(GestionFiscal.objects.filter(pk=gestion.pk).exists())

    # -- Eliminación ---------------------------------------------------------

    def test_eliminar_gestion_vacia_conserva_la_auditoria(self):
        gestion = crear_gestion(2028, estado='preparacion')
        gestion_id = gestion.id

        resp = self.client.delete(f'{self.url}{gestion_id}/')

        self.assertEqual(resp.status_code, 204, resp.data)
        self.assertFalse(GestionFiscal.objects.filter(pk=gestion_id).exists())
        eventos = EventoAuditoria.objects.filter(
            entidad='GestionFiscal', entidad_id=str(gestion_id),
        )
        # El rastro sobrevive desvinculado de la gestión eliminada.
        self.assertTrue(eventos.exists())
        self.assertTrue(all(e.gestion_id is None for e in eventos))
        self.assertTrue(eventos.filter(accion='anular').exists())

    def test_no_se_elimina_la_gestion_que_tiene_el_candado(self):
        # Apagar SIS-POA no puede ser el efecto lateral de un DELETE.
        GestionFiscal.objects.update(activa=False)
        gestion = crear_gestion(2028, estado='preparacion')
        self.client.post(f'{self.url}{gestion.id}/enable/', {}, format='json')

        resp = self.client.delete(f'{self.url}{gestion.id}/')

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('habilitada', str(resp.data))
        self.assertTrue(GestionFiscal.objects.filter(pk=gestion.pk).exists())

    def test_eliminar_gestion_con_dependencias_rechazado(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        TechoDirectivo.objects.create(gestion=gestion)

        resp = self.client.delete(f'{self.url}{gestion.id}/')

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertTrue(GestionFiscal.objects.filter(pk=gestion.pk).exists())

    def test_eliminar_gestion_ve_las_dependencias_ocultas(self):
        # Casi todas las FK hacia la gestión usan related_name='+': si el
        # conteo mirara solo `_meta.related_objects`, una gestión con
        # catálogos cargados parecería vacía y se borraría en cascada.
        gestion = crear_gestion(2028, estado='HABILITADA')
        FuenteFinanciamiento.objects.create(
            codigo='11', denominacion='Tesoro General', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )

        resp = self.client.delete(f'{self.url}{gestion.id}/')

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('Fuentes de financiamiento', str(resp.data))
        self.assertTrue(GestionFiscal.objects.filter(pk=gestion.pk).exists())

    # -- Transiciones expuestas a la UI --------------------------------------

    def test_serializer_expone_las_transiciones_validas(self):
        cerrada = crear_gestion(2028, estado='CERRADA')
        preparacion = crear_gestion(2030, estado='preparacion')

        resp = self.client.get(self.url)
        por_anio = {g['anio']: g for g in resp.data['results']}

        self.assertFalse(por_anio[cerrada.anio]['puede_habilitar'])
        self.assertTrue(por_anio[cerrada.anio]['puede_reabrir'])
        self.assertFalse(por_anio[cerrada.anio]['puede_cerrar'])

        self.assertTrue(por_anio[preparacion.anio]['puede_habilitar'])
        self.assertFalse(por_anio[preparacion.anio]['puede_reabrir'])
        self.assertTrue(por_anio[preparacion.anio]['puede_cerrar'])
        self.assertTrue(por_anio[preparacion.anio]['puede_eliminar'])

    def test_puede_eliminar_es_falso_con_dependencias(self):
        gestion = crear_gestion(2028, estado='HABILITADA')
        TechoDirectivo.objects.create(gestion=gestion)

        resp = self.client.get(self.url)
        por_anio = {g['anio']: g for g in resp.data['results']}

        self.assertFalse(por_anio[gestion.anio]['puede_eliminar'])


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
        copias = CategoriaProgramaticaTecho.objects.filter(gestion=destino)
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
    Apertura,
    AperturaFuente,
    DistribucionVersion,
    Reserva,
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

        version = DistribucionVersion.objects.get(gestion=self.gestion)
        self.assertEqual(version.numero, 1)
        evento = EventoAuditoria.objects.filter(
            entidad='Apertura', gestion__anio=2030,
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
            Apertura.objects.filter(gestion=self.gestion).count(), 0
        )

    def test_distribucion_bloqueada_sin_techo_fijado(self):
        gestion = crear_gestion(2034, estado='HABILITADA')
        self.assertEqual(disponible_por_fuente(gestion), {})
        resp = self.crear_apertura(gestion=gestion)
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertFalse(
            Apertura.objects.filter(gestion=gestion).exists()
        )

    def test_concurrencia_secuencial_dos_requests_exceden(self):
        resp1 = self.crear_apertura(monto='1000.00', denominacion='Primera')
        self.assertEqual(resp1.status_code, 201, resp1.data)
        resp2 = self.crear_apertura(monto='1000.00', denominacion='Segunda')
        self.assertEqual(resp2.status_code, 400, resp2.data)
        self.assertEqual(resp2.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(
            Apertura.objects.filter(gestion=self.gestion).count(), 1
        )

    def test_eliminar_apertura_borrador_ok(self):
        from .services import version_distribucion_activa
        allocation = Apertura.objects.create(
            gestion=self.gestion,
            version=version_distribucion_activa(self.gestion),
            denominacion='Borrador importado (Fase 5)',
            estado='BORRADOR',
            created_by=self.admin, updated_by=self.admin,
        )
        AperturaFuente.objects.create(
            allocation=allocation, fuente=self.fuente, monto=Decimal('50.00'),
            created_by=self.admin, updated_by=self.admin,
        )
        resp = self.client.delete(
            f'{BUDGET_URL}allocations/{allocation.id}/'
        )
        self.assertEqual(resp.status_code, 204, resp.data)
        self.assertFalse(Apertura.objects.filter(pk=allocation.pk).exists())

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
            Apertura.objects.get(pk=allocation_id).denominacion, 'A cerrar'
        )

        resp = self.client.delete(f'{BUDGET_URL}allocations/{allocation_id}/')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertTrue(Apertura.objects.filter(pk=allocation_id).exists())

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
        allocation = Apertura.objects.get(pk=allocation_id)
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
            Reserva.objects.filter(gestion=self.gestion).count(), 0
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
    Importacion,
    ImportacionDetalle,
    ImportacionError,
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
                codigo=codigo, denominacion=nombre, gestion=self.gestion,
                fecha_vigencia_desde=timezone.now().date(),
            )
        prog = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='097', denominacion='Programa 097',
            nivel='PROGRAMA',
        )
        CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='010',
            denominacion='Subprograma 010', nivel='SUBPROGRAMA', parent=prog,
        )
        Distrito.objects.create(codigo='D1', nombre='URBANO 1')

    def subir(self, contenido, perfil='PIP_GASTOS_HISTORICO'):
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
        importacion = Importacion.objects.get(pk=resp.data['id'])
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

        importacion = Importacion.objects.get(pk=data['id'])
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
        importacion = Importacion.objects.get(pk=resp.data['id'])
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
            {'gestion': str(self.gestion.id), 'perfil': 'PIP_GASTOS_HISTORICO',
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
            {'gestion': str(self.gestion.id), 'perfil': 'PIP_GASTOS_HISTORICO',
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
        criticos = ImportacionError.objects.filter(
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
        self.assertTrue(ImportacionError.objects.filter(
            importacion=importacion, severidad='CRITICAL',
            mensaje__contains='negativo',
        ).exists())

    def test_fuente_inexistente_es_critical(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(),
        ])
        # Quitar la fuente 41 del catálogo → CT/IDH quedan inválidas.
        FuenteFinanciamiento.objects.filter(codigo='41', gestion__anio=2030).delete()
        importacion.errores.all().delete()
        validar_importacion(importacion)
        importacion.refresh_from_db()
        self.assertEqual(importacion.estado, 'STAGING')
        criticos = ImportacionError.objects.filter(
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
        self.assertTrue(ImportacionError.objects.filter(
            importacion=importacion, severidad='CRITICAL',
            mensaje__contains='999',
        ).exists())

    def test_denominacion_vacia_es_error(self):
        importacion, _, _ = self.subir_y_validar([
            HEADER_GASTOS,
            fila_detalle(denom=''),
        ])
        self.assertEqual(importacion.estado, 'STAGING')
        self.assertTrue(ImportacionError.objects.filter(
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
        self.assertTrue(ImportacionError.objects.filter(
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
        self.assertFalse(ImportacionError.objects.filter(
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
        self.assertTrue(ImportacionError.objects.filter(
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
        from .models import Apertura
        aperturas = Apertura.objects.filter(gestion=self.gestion)
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
        from .models import Apertura
        self.assertFalse(Apertura.objects.filter(gestion=self.gestion).exists())
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

        from .models import Apertura, AperturaFuente
        aperturas = Apertura.objects.filter(gestion=self.gestion)
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
        fuentes = AperturaFuente.objects.filter(
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
            entidad='Importacion', entidad_id=str(importacion.id),
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
    AsignacionTerritorial,
    DistribucionTerritorial,
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
        distribucion = DistribucionTerritorial.objects.get(pk=pk)
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

        reservas = Reserva.objects.filter(
            gestion=self.gestion, tipo='DISTRITAL', estado='ACTIVA',
        )
        self.assertEqual(reservas.count(), 3)
        self.assertEqual(
            sum(r.monto for r in reservas), Decimal('600.00')
        )
        for asignacion in AsignacionTerritorial.objects.filter(
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
            Reserva.objects.filter(gestion=self.gestion).count(), 0
        )
        distribucion = DistribucionTerritorial.objects.get(pk=pk)
        self.assertEqual(distribucion.estado, 'CALCULADA')

    def test_liberar_devuelve_reservas_y_estado_calculada(self):
        pk = self._aplicada()
        resp = self.aplicar(pk)
        self.assertEqual(resp.status_code, 200, resp.data)

        resp = self.liberar(pk)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'CALCULADA')
        self.assertEqual(
            Reserva.objects.filter(
                gestion=self.gestion, estado='ACTIVA',
            ).count(), 0
        )
        self.assertEqual(
            Reserva.objects.filter(
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
            codigo=str(anio), denominacion=f'Fuente {anio}', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        organismo = OrganismoFinanciador.objects.create(
            codigo=str(anio) + '1', denominacion=f'Origen {anio}', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        ceiling = TechoDirectivo.objects.get(gestion=gestion)
        version = TechoVersion.objects.get(
            ceiling=ceiling, numero=1
        )
        RecursoTecho.objects.create(
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
            entidad='DistribucionVersion', entidad_id=str(version.id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'aprobar')
        self.assertIn('fijada', evento.resumen.lower())
        self.assertEqual(evento.gestion.anio, 2030)


class FijacionInmutabilidadTests(FijacionDistribucionBase):
    def test_patch_apertura_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        allocation = Apertura.objects.get(gestion=self.gestion)
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
            Apertura.objects.filter(denominacion='Post fijación').count(), 0
        )

    def test_crear_reserva_tras_fijar_rechazado(self):
        self.fijar_v1_api()
        resp = self.crear_reserva_api(monto='50.00')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(Reserva.objects.filter(motivo='Contingencia').count(), 1)

    def test_liberar_reserva_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        reserva = Reserva.objects.get(gestion=self.gestion, estado='ACTIVA')
        resp = self.client.post(
            f'{BUDGET_URL}reserves/{reserva.id}/liberar/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'ACTIVA')

    def test_patch_reserva_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        reserva = Reserva.objects.get(gestion=self.gestion, estado='ACTIVA')
        resp = self.client.patch(
            f'{BUDGET_URL}reserves/{reserva.id}/',
            {'monto': '1.00'}, format='json',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        reserva.refresh_from_db()
        self.assertEqual(reserva.monto, Decimal('500.00'))

    def test_eliminar_apertura_de_version_fijada_rechazado(self):
        self.fijar_v1_api()
        allocation = Apertura.objects.get(gestion=self.gestion)
        resp = self.client.delete(f'{BUDGET_URL}allocations/{allocation.id}/')
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertTrue(Apertura.objects.filter(pk=allocation.pk).exists())

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

        v2 = DistribucionVersion.objects.get(gestion=self.gestion, numero=2)
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
            DistribucionVersion.objects.filter(gestion=self.gestion).count(), 1
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
        a = Apertura.objects.get(gestion=self.gestion, denominacion='A')
        b = Apertura.objects.get(gestion=self.gestion, denominacion='B')
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


# ===========================================================================
# Fase 8 - Control presupuestario central (BudgetControlService + API +
# concurrencia real con locks sobre el techo fijado)
# ===========================================================================
import threading  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402

from django.db import connection, transaction  # noqa: E402
from django.test import TransactionTestCase  # noqa: E402

from .control import BudgetControlService  # noqa: E402
from .services import (  # noqa: E402
    ErrorDisponibilidad,
    aprobar,
    enviar_a_revision,
    fijar_techo,
    version_distribucion_activa,
)

CONTROL_URL = BUDGET_URL + 'control/'


class ControlSummaryTests(DistribucionBase):
    """get_summary: resumen consolidado con invariante exacta por fuente."""

    def test_summary_consistente_exacto_por_fuente(self):
        self.crear_apertura(monto='1000.00', denominacion='Apertura A')
        self.crear_reserva_api(monto='200.00')
        resumen = BudgetControlService.get_summary(self.gestion)

        self.assertEqual(resumen['techo_bruto'], Decimal('1500.00'))
        self.assertEqual(resumen['techo_distribuible'], Decimal('1500.00'))
        self.assertEqual(resumen['distribuido'], Decimal('1000.00'))
        self.assertEqual(resumen['reservado'], Decimal('200.00'))
        self.assertEqual(resumen['disponible'], Decimal('300.00'))
        self.assertEqual(resumen['porcentaje'], 66.67)
        self.assertEqual(len(resumen['por_fuente']), 1)

        fila = resumen['por_fuente'][0]
        self.assertEqual(fila['fuente'], str(self.fuente.id))
        self.assertEqual(fila['denominacion'], 'Tesoro General')
        self.assertEqual(fila['techo'], Decimal('1500.00'))
        self.assertEqual(fila['distribuido'], Decimal('1000.00'))
        self.assertEqual(fila['reservado'], Decimal('200.00'))
        self.assertEqual(fila['disponible'], Decimal('300.00'))
        # Invariante exacta por fuente: techo = distribuido + reservado +
        # disponible (sin redondeos).
        self.assertEqual(
            fila['techo'],
            fila['distribuido'] + fila['reservado'] + fila['disponible'],
        )
        # Y la invariante global también.
        self.assertEqual(
            resumen['techo_distribuible'],
            resumen['distribuido'] + resumen['reservado']
            + resumen['disponible'],
        )
        # Coherencia con los agregados del servicio.
        techo = BudgetControlService.get_distributable_ceiling(self.gestion)
        self.assertEqual(techo[self.fuente.id], fila['techo'])

    def test_summary_sin_techo_devuelve_ceros(self):
        gestion = crear_gestion(2041, estado='HABILITADA')
        resumen = BudgetControlService.get_summary(gestion)
        self.assertEqual(resumen['gestion'], 2041)
        self.assertEqual(resumen['techo_bruto'], Decimal('0.00'))
        self.assertEqual(resumen['techo_distribuible'], Decimal('0.00'))
        self.assertEqual(resumen['distribuido'], Decimal('0.00'))
        self.assertEqual(resumen['reservado'], Decimal('0.00'))
        self.assertEqual(resumen['disponible'], Decimal('0.00'))
        self.assertEqual(resumen['porcentaje'], 0.0)
        self.assertEqual(resumen['por_fuente'], [])

    def test_getters_de_saldos_coinciden_con_services(self):
        self.crear_apertura(monto='1000.00', denominacion='Apertura A')
        self.crear_reserva_api(monto='200.00')
        self.assertEqual(
            BudgetControlService.get_directive_ceiling(self.gestion)[
                'techo_bruto'
            ],
            Decimal('1500.00'),
        )
        self.assertEqual(
            BudgetControlService.get_distributable_ceiling(self.gestion),
            techo_distribuible_por_fuente(self.gestion),
        )
        self.assertEqual(
            BudgetControlService.get_distributed(self.gestion),
            distribuido_por_fuente(self.gestion),
        )
        self.assertEqual(
            BudgetControlService.get_reserved(self.gestion),
            reservado_por_fuente(self.gestion),
        )
        self.assertEqual(
            BudgetControlService.get_available_for_distribution(self.gestion),
            disponible_por_fuente(self.gestion),
        )

    def test_getters_de_apertura(self):
        resp = self.crear_apertura(monto='1000.00', denominacion='Apertura A')
        allocation = Apertura.objects.get(pk=resp.data['id'])
        self.assertEqual(
            BudgetControlService.get_allocation_ceiling(allocation),
            Decimal('1000.00'),
        )
        # Fase 8: sin programación por objetos del gasto → disponible =
        # techo de la apertura.
        self.assertEqual(
            BudgetControlService.get_allocated_to_expense_objects(allocation),
            Decimal('0.00'),
        )
        self.assertEqual(
            BudgetControlService.get_allocation_available(allocation),
            Decimal('1000.00'),
        )

    def test_validate_distribution_reutiliza_servicio(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='500.00')
        resultado = BudgetControlService.validate_distribution(self.gestion)
        self.assertTrue(resultado['valida'])
        self.assertEqual(
            resultado,
            validar_distribucion_completa(self.gestion),
        )

    def test_validate_expense_object_valida_apertura_activa(self):
        resp = self.crear_apertura(monto='100.00', denominacion='Apertura A')
        allocation = Apertura.objects.get(pk=resp.data['id'])
        # Fase 9: requiere versión de distribución FIJADA → completar y
        # congelar la distribución (apertura 100 + reserva 1400 = techo 1500).
        self.crear_reserva_api(monto='1400.00')
        version = version_distribucion_activa(self.gestion)
        enviar_distribucion_a_revision(version, self.admin)
        aprobar_distribucion(version, self.admin)
        fijar_distribucion(version, self.admin)
        objeto = ObjetoGasto.objects.create(
            codigo='25220', denominacion='Papelería', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.assertEqual(
            BudgetControlService.validate_expense_object(
                allocation, objeto, Decimal('50.00'),
            ),
            {'valido': True},
        )
        allocation.estado = 'BORRADOR'
        allocation.save()
        with self.assertRaises(ValidationError):
            BudgetControlService.validate_expense_object(
                allocation, objeto, Decimal('50.00'),
            )

    def test_validate_expense_object_con_allocation_inexistente(self):
        with self.assertRaises(ValidationError):
            BudgetControlService.validate_expense_object(
                999999, self.fuente, Decimal('50.00'),
            )


class ControlReservaTests(DistribucionBase):
    """reserve/release vía BudgetControlService (refactor de services)."""

    def test_reserve_respeta_disponibilidad(self):
        reserva = BudgetControlService.reserve(
            self.gestion, self.fuente, self.organismo,
            Decimal('200.00'), motivo='Control Fase 8', usuario=self.admin,
        )
        self.assertEqual(reserva.estado, 'ACTIVA')
        self.assertEqual(reserva.monto, Decimal('200.00'))
        disponible = BudgetControlService.get_available_for_distribution(
            self.gestion,
        )
        self.assertEqual(disponible[self.fuente.id], Decimal('1300.00'))
        evento = EventoAuditoria.objects.filter(
            entidad='Reserva', entidad_id=str(reserva.id),
        ).first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'crear')

    def test_reserve_excede_disponible_lanza_budget_exceeded(self):
        with self.assertRaises(ErrorDisponibilidad) as ctx:
            BudgetControlService.reserve(
                self.gestion, self.fuente, self.organismo,
                Decimal('1600.00'), motivo='Exceso', usuario=self.admin,
            )
        self.assertEqual(ctx.exception.code, 'BUDGET_EXCEEDED')
        self.assertEqual(ctx.exception.details['available'], '1500.00')
        self.assertEqual(
            Reserva.objects.filter(gestion=self.gestion).count(), 0,
        )

    def test_release_devuelve_el_disponible(self):
        reserva = BudgetControlService.reserve(
            self.gestion, self.fuente, self.organismo,
            Decimal('200.00'), motivo='A liberar', usuario=self.admin,
        )
        BudgetControlService.release(reserva, self.admin)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'LIBERADA')
        self.assertEqual(
            BudgetControlService.get_available_for_distribution(self.gestion)[
                self.fuente.id
            ],
            Decimal('1500.00'),
        )

    def test_release_doble_rechazado(self):
        reserva = BudgetControlService.reserve(
            self.gestion, self.fuente, self.organismo,
            Decimal('200.00'), motivo='A liberar', usuario=self.admin,
        )
        BudgetControlService.release(reserva, self.admin)
        with self.assertRaises(ValidationError):
            BudgetControlService.release(reserva, self.admin)


class ControlMovimientoTests(DistribucionBase):
    """apply_movement: movimiento atómico TRASPASO con saldos (Fase 10)."""

    def _escenario(self):
        resp = self.crear_apertura(monto='100.00', denominacion='Origen')
        origen = Apertura.objects.get(pk=resp.data['id'])
        destino = Apertura.objects.create(
            gestion=self.gestion,
            version=origen.version,
            denominacion='Destino',
            estado='ACTIVA',
            created_by=self.admin,
            updated_by=self.admin,
        )
        return origen, destino

    def test_apply_movement_mueve_saldos_con_saldos_antes_despues(self):
        origen, destino = self._escenario()
        resultado = BudgetControlService.apply_movement(
            origen, destino, self.fuente, self.organismo,
            Decimal('80.00'), motivo='Reformulación (traspaso)',
            usuario=self.admin,
        )
        self.assertTrue(resultado['valido'])
        self.assertTrue(resultado['movido'])
        # Saldos del AperturaFuente de ORIGEN antes/después.
        self.assertEqual(resultado['saldo_antes'], Decimal('100.00'))
        self.assertEqual(resultado['saldo_despues'], Decimal('20.00'))
        origen_src = AperturaFuente.objects.get(allocation=origen)
        self.assertEqual(origen_src.monto, Decimal('20.00'))
        # El destino gana la fuente (se crea la fila si no existía).
        destino_src = AperturaFuente.objects.get(allocation=destino)
        self.assertEqual(destino_src.monto, Decimal('80.00'))

    def test_apply_movement_con_exceso_lanza_budget_exceeded(self):
        origen, destino = self._escenario()
        with self.assertRaises(ErrorDisponibilidad) as ctx:
            BudgetControlService.apply_movement(
                origen, destino, self.fuente, self.organismo,
                Decimal('120.00'), motivo='Exceso', usuario=self.admin,
            )
        self.assertEqual(ctx.exception.code, 'BUDGET_EXCEEDED')
        self.assertEqual(ctx.exception.details['available'], '100.00')
        self.assertEqual(
            Apertura.objects.get(pk=origen.pk).fuentes.count(), 1,
        )
        # Nada movido: el destino sigue sin fuentes (rollback del intento).
        self.assertEqual(
            Apertura.objects.get(pk=destino.pk).fuentes.count(), 0,
        )

    def test_apply_movement_con_origen_inexistente_rechazado(self):
        origen, destino = self._escenario()
        origen.delete()
        with self.assertRaises(ValidationError):
            BudgetControlService.apply_movement(
                origen, destino, self.fuente, self.organismo,
                Decimal('10.00'), motivo='Inexistente', usuario=self.admin,
            )

    def test_apply_movement_sin_fuente_rechazado(self):
        origen, destino = self._escenario()
        with self.assertRaises(ValidationError):
            BudgetControlService.apply_movement(
                origen, destino, None, self.organismo,
                Decimal('10.00'), motivo='Sin fuente', usuario=self.admin,
            )


class ControlConcurrenciaTests(TransactionTestCase):
    """Demuestra el lock: dos consumos concurrentes NUNCA exceden el saldo.

    Corre contra PostgreSQL (el test DB usa PostGIS local); cada hilo abre
    su propia conexión real. `TransactionTestCase` deja las transacciones
    por hilo independientes (los datos del setUp quedan commiteados y los
    hilos hacen `transaction.atomic` sobre ellos).

    Hallazgo documentado (Fase 8): con barrera y arranque simultáneo el
    GANADOR del lock es no determinista (50 u 80); lo que SÍ es
    determinista es la INVARIANTE de seguridad: exactamente UNA reserva
    queda creada y el saldo final nunca refleja los dos consumos (nunca
    130). Por eso este test afirma la invariante (y el rango de disponibles
    posibles), no un ganador particular; `test_lock_serializa_el_consumo`
    fuerza el interleaving para demostrar la serialización de forma
    determinista (gana la reserva que tomó el lock primero).
    """

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@control.test', password='test2026'
        )
        self.gestion = crear_gestion(2040, estado='HABILITADA')
        self.fuente = FuenteFinanciamiento.objects.create(
            codigo='11', denominacion='Tesoro General', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.organismo = OrganismoFinanciador.objects.create(
            codigo='111', denominacion='Tesoro General de la Nación',
            gestion=self.gestion, fecha_vigencia_desde=timezone.now().date(),
        )
        ceiling = TechoDirectivo.objects.create(gestion=self.gestion)
        version = TechoVersion.objects.create(
            ceiling=ceiling, numero=1,
        )
        RecursoTecho.objects.create(
            version=version, origen='SIGEP', monto='100.00', concepto='CT',
            fuente=self.fuente, organismo=self.organismo,
            created_by=self.admin, updated_by=self.admin,
        )
        enviar_a_revision(version, self.admin)
        aprobar(version, self.admin)
        fijar_techo(version, self.admin)
        # Versión activa de distribución v1 (la crean las reservas si no).
        version_distribucion_activa(self.gestion)

    def _intentar_reservar(self, monto):
        """Reserva vía servicio; devuelve ('ok', reserva) o ('exceeded', exc)."""
        try:
            reserva = BudgetControlService.reserve(
                self.gestion, self.fuente, self.organismo,
                monto, motivo=f'Concurrente {monto}', usuario=self.admin,
            )
            return ('ok', reserva)
        except ErrorDisponibilidad as exc:
            return ('exceeded', exc)
        except ValidationError as exc:
            return ('error', exc)

    def _disponible(self):
        return BudgetControlService.get_available_for_distribution(
            self.gestion,
        )[self.fuente.id]

    def _en_hilo(self, fn):
        """Ejecuta fn en el hilo y cierra su conexión al terminar.

        Sin esto, las conexiones de los hilos quedan abiertas contra la BD
        de test e impiden dropearla al finalizar la suite (PostgreSQL lo
        rechaza mientras haya sesiones activas).
        """
        def _wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            finally:
                try:
                    connection.close()
                except Exception:
                    pass
        return _wrapper

    def test_doble_reserva_concurrente_nunca_excede_saldo(self):
        barrera = threading.Barrier(2)

        def worker(monto):
            barrera.wait()
            return self._intentar_reservar(monto)

        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_80 = pool.submit(
                self._en_hilo(worker), Decimal('80.00'),
            )
            fut_50 = pool.submit(
                self._en_hilo(worker), Decimal('50.00'),
            )
            r_80 = fut_80.result(timeout=60)
            r_50 = fut_50.result(timeout=60)

        resultados = [r_80, r_50]
        exitos = [r for r in resultados if r[0] == 'ok']
        fallas = [r for r in resultados if r[0] == 'exceeded']
        self.assertEqual(len(exitos), 1, resultados)
        self.assertEqual(len(fallas), 1, resultados)
        self.assertEqual(fallas[0][1].code, 'BUDGET_EXCEEDED')

        reservada = exitos[0][1].monto
        self.assertIn(reservada, {Decimal('80.00'), Decimal('50.00')})
        activas = Reserva.objects.filter(
            gestion=self.gestion, estado='ACTIVA',
        )
        self.assertEqual(activas.count(), 1)
        self.assertEqual(activas.first().monto, reservada)

        # NUNCA 130: el disponible final refleja UN solo consumo.
        disponible = self._disponible()
        self.assertIn(
            disponible, {Decimal('20.00'), Decimal('50.00')}, disponible,
        )
        self.assertEqual(disponible, Decimal('100.00') - reservada)
        self.assertNotEqual(disponible, Decimal('-30.00'))

    def test_lock_serializa_el_consumo_de_forma_determinista(self):
        """A toma el lock y reserva 80 sin commitear; B espera el lock y
        re-lee el saldo YA commiteado de A → B falla (available 20)."""
        lock_held = threading.Event()
        proceed = threading.Event()

        def worker_a():
            with transaction.atomic():
                BudgetControlService._bloquear_fuentes(
                    self.gestion, {self.fuente.id},
                )
                reserva = BudgetControlService.reserve(
                    self.gestion, self.fuente, self.organismo,
                    Decimal('80.00'), motivo='A (con lock)',
                    usuario=self.admin,
                )
                lock_held.set()
                if not proceed.wait(30):
                    raise TimeoutError('A esperó demasiado el avance.')
                return reserva

        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_a = pool.submit(self._en_hilo(worker_a))
            self.assertTrue(
                lock_held.wait(30), 'A no tomó el lock a tiempo.',
            )
            fut_b = pool.submit(
                self._en_hilo(self._intentar_reservar), Decimal('50.00'),
            )
            time.sleep(0.5)  # B ya está bloqueado en el lock del techo.
            proceed.set()
            resultado_b = fut_b.result(timeout=60)
            fut_a.result(timeout=60)

        self.assertEqual(resultado_b[0], 'exceeded')
        self.assertEqual(resultado_b[1].code, 'BUDGET_EXCEEDED')
        self.assertEqual(resultado_b[1].details['available'], '20.00')
        self.assertEqual(
            Reserva.objects.filter(gestion=self.gestion, estado='ACTIVA')
            .count(), 1,
        )
        self.assertEqual(self._disponible(), Decimal('20.00'))

    def test_secuencial_dos_reservas_exceden(self):
        """Equivalente secuencial (determinista): 80 ok, luego 50 excede."""
        r_1 = self._intentar_reservar(Decimal('80.00'))
        self.assertEqual(r_1[0], 'ok')
        r_2 = self._intentar_reservar(Decimal('50.00'))
        self.assertEqual(r_2[0], 'exceeded')
        self.assertEqual(r_2[1].code, 'BUDGET_EXCEEDED')
        self.assertEqual(r_2[1].details['available'], '20.00')
        self.assertEqual(
            Reserva.objects.filter(gestion=self.gestion, estado='ACTIVA')
            .count(), 1,
        )
        self.assertEqual(self._disponible(), Decimal('20.00'))


class ControlApiTests(DistribucionBase):
    """Endpoints GET /control/summary/ y POST /control/validate/."""

    def test_summary_endpoint_devuelve_resumen(self):
        self.crear_apertura(monto='1000.00', denominacion='Apertura A')
        self.crear_reserva_api(monto='200.00')
        resp = self.client.get(
            f'{CONTROL_URL}summary/', {'gestion': str(self.gestion.id)},
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['techo_bruto'], '1500.00')
        self.assertEqual(resp.data['techo_distribuible'], '1500.00')
        self.assertEqual(resp.data['distribuido'], '1000.00')
        self.assertEqual(resp.data['reservado'], '200.00')
        self.assertEqual(resp.data['disponible'], '300.00')
        self.assertEqual(resp.data['por_fuente'][0]['fuente'],
                         str(self.fuente.id))
        self.assertEqual(resp.data['por_fuente'][0]['disponible'], '300.00')

    def test_summary_requiere_gestion(self):
        resp = self.client.get(f'{CONTROL_URL}summary/')
        self.assertEqual(resp.status_code, 400, resp.data)

    def test_summary_sin_autenticacion_rechazado(self):
        client = APIClient()
        resp = client.get(
            f'{CONTROL_URL}summary/', {'gestion': str(self.gestion.id)},
        )
        self.assertEqual(resp.status_code, 401)

    def test_validate_distribution_valida(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='500.00')
        resp = self.client.post(
            f'{CONTROL_URL}validate/',
            {'tipo': 'distribution', 'gestion': str(self.gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data['valido'])
        self.assertEqual(resp.data['errores'][0]['diferencia'], '0.00')

    def test_validate_distribution_con_diferencia(self):
        self.crear_apertura(monto='1000.00')
        self.crear_reserva_api(monto='200.00')
        resp = self.client.post(
            f'{CONTROL_URL}validate/',
            {'tipo': 'distribution', 'gestion': str(self.gestion.id)},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertFalse(resp.data['valido'])
        self.assertEqual(resp.data['errores'][0]['diferencia'], '300.00')

    def test_validate_expense_object_valida_apertura_activa(self):
        resp = self.crear_apertura(monto='100.00', denominacion='Apertura A')
        # Fase 9: requiere versión de distribución FIJADA → completar y
        # congelar la distribución (apertura 100 + reserva 1400 = techo 1500).
        self.crear_reserva_api(monto='1400.00')
        version = version_distribucion_activa(self.gestion)
        enviar_distribucion_a_revision(version, self.admin)
        aprobar_distribucion(version, self.admin)
        fijar_distribucion(version, self.admin)
        objeto = ObjetoGasto.objects.create(
            codigo='25220', denominacion='Papelería', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{CONTROL_URL}validate/',
            {'tipo': 'expense-object', 'allocation': resp.data['id'],
             'objeto_gasto': str(objeto.id), 'monto': '50.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data['valido'])
        self.assertEqual(resp.data['errores'], [])

    def test_validate_expense_object_con_apertura_inexistente(self):
        resp = self.client.post(
            f'{CONTROL_URL}validate/',
            {'tipo': 'expense-object', 'allocation': 999999,
             'fuente': str(self.fuente.id), 'monto': '50.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertFalse(resp.data['valido'])
        self.assertIn('no existe', resp.data['errores'][0])

    def test_validate_allocation_devuelve_saldos(self):
        resp = self.crear_apertura(monto='100.00', denominacion='Apertura A')
        resp = self.client.post(
            f'{CONTROL_URL}validate/',
            {'tipo': 'allocation', 'allocation': resp.data['id']},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data['valido'])
        self.assertEqual(resp.data['techo'], '100.00')
        self.assertEqual(resp.data['programado'], '0.00')
        self.assertEqual(resp.data['disponible'], '100.00')

    def test_validate_sin_tipo_rechazado(self):
        resp = self.client.post(
            f'{CONTROL_URL}validate/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('tipo', str(resp.data))

    def test_validate_sin_autenticacion_rechazado(self):
        client = APIClient()
        resp = client.post(
            f'{CONTROL_URL}validate/', {'tipo': 'distribution'}, format='json',
        )
        self.assertEqual(resp.status_code, 401)


# ===========================================================================
# Fase 9 - Objetos del gasto: programación por apertura (§90-91)
# ===========================================================================
from .models import AsignacionObjetoGastoTecho  # noqa: E402
from .services import (  # noqa: E402
    ErrorObjetoGastoExcedido,
    programar_objeto_gasto,
)

EXPENSE_URL = BUDGET_URL + 'expense-objects/'


class ObjetosGastoBase(TestCase):
    """Base de Fase 9 (§90-91): techo 500.000 y distribución FIJADA.

    Gestión 2045 HABILITADA con techo fijado de 500.000 (fuente 11) y
    apertura única de 500.000 → distribución v1 completa y congelada
    (Σfuente = techo − reservas, sin reservas).
    """

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@objetos.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.gestion = crear_gestion(2045, estado='HABILITADA')
        self.fuente = FuenteFinanciamiento.objects.create(
            codigo='11', denominacion='Tesoro General', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.organismo = OrganismoFinanciador.objects.create(
            codigo='111', denominacion='Tesoro General de la Nación',
            gestion=self.gestion, fecha_vigencia_desde=timezone.now().date(),
        )
        self.objeto_25220 = ObjetoGasto.objects.create(
            codigo='25220', denominacion='Papelería y útiles', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.objeto_34200 = ObjetoGasto.objects.create(
            codigo='34200', denominacion='Pasajes al interior', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.objeto_43110 = ObjetoGasto.objects.create(
            codigo='43110', denominacion='Maquinaria y equipo', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        self.objeto_42310 = ObjetoGasto.objects.create(
            codigo='42310', denominacion='Muebles de oficina', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )

        ceiling = TechoDirectivo.objects.create(gestion=self.gestion)
        version = TechoVersion.objects.create(
            ceiling=ceiling, numero=1,
        )
        RecursoTecho.objects.create(
            version=version, origen='SIGEP', monto='500000.00', concepto='CT',
            fuente=self.fuente, organismo=self.organismo,
            created_by=self.admin, updated_by=self.admin,
        )
        enviar_a_revision(version, self.admin)
        aprobar(version, self.admin)
        fijar_techo(version, self.admin)

        resp = self.client.post(
            f'{BUDGET_URL}allocations/',
            {'gestion': str(self.gestion.id), 'denominacion': 'Apertura 500K',
             'codigo_sisin': '12345678',
             'fuentes': [{'fuente': str(self.fuente.id),
                          'organismo': str(self.organismo.id),
                          'monto': '500000.00'}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.allocation = Apertura.objects.get(pk=resp.data['id'])

        version_distribucion = version_distribucion_activa(self.gestion)
        enviar_distribucion_a_revision(version_distribucion, self.admin)
        aprobar_distribucion(version_distribucion, self.admin)
        fijar_distribucion(version_distribucion, self.admin)

    def programar_api(self, objeto, monto, allocation=None):
        return self.client.post(
            f'{EXPENSE_URL}',
            {'allocation': str((allocation or self.allocation).id),
             'objeto_gasto': str(objeto.id), 'monto': monto},
            format='json',
        )


class ProgramacionObjetosGastoTests(ObjetosGastoBase):
    """Programación por objeto del gasto: techo/programado/disponible."""

    def test_programar_objetos_suma_programado_y_disponible(self):
        for objeto, monto in (
            (self.objeto_25220, '100000.00'),
            (self.objeto_34200, '180000.00'),
            (self.objeto_43110, '120000.00'),
        ):
            resp = self.programar_api(objeto, monto)
            self.assertEqual(resp.status_code, 201, resp.data)
        # Techo 500.000 − programado 400.000 → disponible 100.000.
        self.assertEqual(
            BudgetControlService.get_allocated_to_expense_objects(
                self.allocation
            ),
            Decimal('400000.00'),
        )
        self.assertEqual(
            BudgetControlService.get_allocation_available(self.allocation),
            Decimal('100000.00'),
        )
        self.assertEqual(
            AsignacionObjetoGastoTecho.objects.filter(
                allocation=self.allocation
            ).count(),
            3,
        )
        self.assertEqual(
            EventoAuditoria.objects.filter(
                entidad='AsignacionObjetoGastoTecho', accion='crear',
            ).count(),
            3,
        )

    def test_exceso_devuelve_409_budget_exceeded(self):
        self.programar_api(self.objeto_25220, '100000.00')
        self.programar_api(self.objeto_34200, '180000.00')
        self.programar_api(self.objeto_43110, '120000.00')
        # 42310 = 150.000 sobre disponible 100.000 → 409 (§91).
        resp = self.programar_api(self.objeto_42310, '150000.00')
        self.assertEqual(resp.status_code, 409, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['requested'], '150000.00')
        self.assertEqual(resp.data['details']['available'], '100000.00')
        self.assertEqual(resp.data['details']['difference'], '50000.00')
        self.assertIn(
            'supera el disponible de la apertura',
            resp.data['error']['detail'][0],
        )
        self.assertFalse(
            AsignacionObjetoGastoTecho.objects.filter(
                objeto_gasto=self.objeto_42310,
            ).exists()
        )

    def test_actualizar_objeto_respeta_disponible_de_los_demas(self):
        self.programar_api(self.objeto_25220, '100000.00')
        self.programar_api(self.objeto_34200, '180000.00')
        self.programar_api(self.objeto_43110, '120000.00')
        fila = AsignacionObjetoGastoTecho.objects.get(
            allocation=self.allocation, objeto_gasto=self.objeto_25220,
        )
        # Subir 25220 de 100.000 a 150.000: los demás suman 300.000 →
        # disponible 200.000 → OK.
        resp = self.client.patch(
            f'{EXPENSE_URL}{fila.id}/', {'monto': '150000.00'}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['monto'], '150000.00')
        self.assertEqual(
            BudgetControlService.get_allocation_available(self.allocation),
            Decimal('50000.00'),
        )
        # Subir a 250.000 excede (300.000 + 250.000 > 500.000) → 409.
        resp = self.client.patch(
            f'{EXPENSE_URL}{fila.id}/', {'monto': '250000.00'}, format='json',
        )
        self.assertEqual(resp.status_code, 409, resp.data)
        self.assertEqual(resp.data['details']['available'], '200000.00')
        fila.refresh_from_db()
        self.assertEqual(fila.monto, Decimal('150000.00'))

    def test_programar_en_version_no_fijada_rechazado(self):
        gestion = crear_gestion(2046, estado='HABILITADA')
        fuente = FuenteFinanciamiento.objects.create(
            codigo='46', denominacion='Fuente 2046', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        organismo = OrganismoFinanciador.objects.create(
            codigo='461', denominacion='Origen 2046', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        ceiling = TechoDirectivo.objects.create(gestion=gestion)
        version = TechoVersion.objects.create(
            ceiling=ceiling, numero=1,
        )
        RecursoTecho.objects.create(
            version=version, origen='SIGEP', monto='500000.00', concepto='CT',
            fuente=fuente, organismo=organismo,
            created_by=self.admin, updated_by=self.admin,
        )
        enviar_a_revision(version, self.admin)
        aprobar(version, self.admin)
        fijar_techo(version, self.admin)
        resp = self.client.post(
            f'{BUDGET_URL}allocations/',
            {'gestion': str(gestion.id), 'denominacion': 'Apertura 2046',
             'codigo_sisin': '11111111',
             'fuentes': [{'fuente': str(fuente.id),
                          'organismo': str(organismo.id),
                          'monto': '500000.00'}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        allocation = Apertura.objects.get(pk=resp.data['id'])
        objeto = ObjetoGasto.objects.create(
            codigo='25220', denominacion='Papelería', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{EXPENSE_URL}',
            {'allocation': str(allocation.id), 'objeto_gasto': str(objeto.id),
             'monto': '100.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('fijada', resp.data['error']['detail'][0])
        self.assertFalse(
            AsignacionObjetoGastoTecho.objects.filter(allocation=allocation).exists()
        )

    def test_eliminar_objeto_libera_disponible(self):
        self.programar_api(self.objeto_25220, '100000.00')
        self.programar_api(self.objeto_34200, '180000.00')
        self.programar_api(self.objeto_43110, '120000.00')
        fila = AsignacionObjetoGastoTecho.objects.get(
            allocation=self.allocation, objeto_gasto=self.objeto_25220,
        )
        resp = self.client.delete(f'{EXPENSE_URL}{fila.id}/')
        self.assertEqual(resp.status_code, 204, resp.data)
        self.assertEqual(
            BudgetControlService.get_allocated_to_expense_objects(
                self.allocation
            ),
            Decimal('300000.00'),
        )
        self.assertEqual(
            BudgetControlService.get_allocation_available(self.allocation),
            Decimal('200000.00'),
        )
        self.assertEqual(
            EventoAuditoria.objects.filter(
                entidad='AsignacionObjetoGastoTecho', accion='anular',
            ).count(),
            1,
        )

    def test_get_allocated_to_expense_objects_suma_correcta(self):
        self.assertEqual(
            BudgetControlService.get_allocated_to_expense_objects(
                self.allocation
            ),
            Decimal('0.00'),
        )
        for objeto, monto in (
            (self.objeto_25220, '100000.00'),
            (self.objeto_34200, '180000.00'),
            (self.objeto_43110, '120000.00'),
        ):
            self.programar_api(objeto, monto)
        self.assertEqual(
            BudgetControlService.get_allocated_to_expense_objects(
                self.allocation
            ),
            Decimal('400000.00'),
        )

    def test_programar_objeto_duplicado_es_upsert(self):
        resp = self.programar_api(self.objeto_25220, '100000.00')
        self.assertEqual(resp.status_code, 201, resp.data)
        resp = self.programar_api(self.objeto_25220, '200000.00')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(
            AsignacionObjetoGastoTecho.objects.filter(
                allocation=self.allocation, objeto_gasto=self.objeto_25220,
            ).count(),
            1,
        )
        self.assertEqual(
            AsignacionObjetoGastoTecho.objects.get(
                allocation=self.allocation, objeto_gasto=self.objeto_25220,
            ).monto,
            Decimal('200000.00'),
        )

    def test_exceso_por_servicio_lanza_error_objeto_gasto(self):
        self.programar_api(self.objeto_25220, '100000.00')
        self.programar_api(self.objeto_34200, '180000.00')
        self.programar_api(self.objeto_43110, '120000.00')
        with self.assertRaises(ErrorObjetoGastoExcedido) as ctx:
            programar_objeto_gasto(
                self.allocation, self.objeto_42310,
                Decimal('150000.00'), self.admin,
            )
        self.assertEqual(ctx.exception.code, 'BUDGET_EXCEEDED')
        self.assertEqual(ctx.exception.details['requested'], '150000.00')
        self.assertEqual(ctx.exception.details['available'], '100000.00')
        self.assertEqual(ctx.exception.details['difference'], '50000.00')

# ===========================================================================
# Fase 10 - Reformulaciones (tipos + workflow + movimientos atómicos, §92-97)
# ===========================================================================
from .models import Reforma, ReformaMovimiento  # noqa: E402
from .services import (  # noqa: E402
    EstadosReform,
    aprobar_reform,
    aplicar_reform,
    crear_reform,
    enviar_reform_a_revision,
    observar_reform,
    rechazar_reform,
)

REFORM_URL = BUDGET_URL + 'reforms/'


class ReformulacionBase(FijacionDistribucionBase):
    """Base de Fase 10: techo 1500 (fuente 11) + distribución fijada.

    La distribución v1 se fija con aperturas A/B y una reserva, dejando el
    pool disponible en `pool` (techo − distribuido − reservado).
    """

    def preparar_distribucion_fijada(self, monto_a='1000.00', monto_b='300.00',
                                     reserva='200.00'):
        """Aperturas A (monto_a) y B (monto_b) + reserva → fija v1.

        Pool por fuente = techo(1500) − A − B − reserva.
        """
        self.crear_apertura(monto=monto_a, denominacion='Apertura A')
        self.crear_apertura(monto=monto_b, denominacion='Apertura B')
        self.crear_reserva_api(monto=reserva)
        version = self.version_activa()
        enviar_distribucion_a_revision(version, self.admin)
        aprobar_distribucion(version, self.admin)
        fijar_distribucion(version, self.admin)
        return version

    def apertura(self, denominacion):
        return Apertura.objects.get(gestion=self.gestion,
                                      denominacion=denominacion)

    def source(self, allocation, fuente=None):
        return AperturaFuente.objects.get(
            allocation=allocation, fuente=fuente or self.fuente,
        )

    def movimiento(self, tipo, origen=None, destino=None, fuente=None,
                   organismo=None, monto='500.00', motivo=''):
        fila = {'tipo': tipo, 'monto': monto}
        if origen is not None:
            fila['apertura_origen'] = str(origen.id)
        if destino is not None:
            fila['apertura_destino'] = str(destino.id)
        if fuente is not None:
            fila['fuente'] = str(fuente.id)
        elif self.fuente is not None:
            fila['fuente'] = str(self.fuente.id)
        if organismo is not None:
            fila['organismo'] = str(organismo.id)
        elif self.organismo is not None:
            fila['organismo'] = str(self.organismo.id)
        if motivo:
            fila['motivo'] = motivo
        return fila

    def crear_api(self, tipo='TRASPASO', movimientos=None, motivo='Prueba'):
        return self.client.post(
            f'{REFORM_URL}',
            {'gestion': str(self.gestion.id), 'tipo': tipo,
             'motivo': motivo, 'movimientos': movimientos},
            format='json',
        )

    def flujo_hasta(self, reform_id, paso):
        """Recorre submit → approve (→ observe/re-submit si `paso` lo pide)."""
        if paso in ('submit',):
            return self.client.post(
                f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
            )
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/approve/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        return resp


class ReformulacionCreacionTests(ReformulacionBase):
    def test_crear_reform_traspaso_borrador_con_dos_movimientos(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='300.00'),
            self.movimiento('TRASPASO', origen=b, destino=a, monto='100.00'),
        ])
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['estado'], 'BORRADOR')
        self.assertEqual(resp.data['tipo'], 'TRASPASO')
        self.assertEqual(len(resp.data['movimientos']), 2)
        # Solo BORRADOR: los saldos NO se movieron.
        self.assertEqual(self.source(a).monto, Decimal('1000.00'))
        self.assertEqual(self.source(b).monto, Decimal('300.00'))
        reform = Reforma.objects.get(pk=resp.data['id'])
        self.assertEqual(reform.version_origen.estado, 'FIJADO')
        self.assertIsNone(reform.version_resultante)

    def test_crear_reform_sin_distribucion_fijada_rechazado(self):
        # Gestión sin fijar la distribución → 400.
        resp = self.crear_api(movimientos=[self.movimiento('DISMINUCION')])
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(Reforma.objects.count(), 0)

    def test_crear_reform_valida_estructura_de_movimientos(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        # Traspaso sin destino → 400.
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, monto='50.00'),
        ])
        self.assertEqual(resp.status_code, 400, resp.data)
        # Monto no positivo → 400.
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='0.00'),
        ])
        self.assertEqual(resp.status_code, 400, resp.data)
        # Sin movimientos → 400.
        resp = self.crear_api(movimientos=[])
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(Reforma.objects.count(), 0)

    def test_crear_reform_permisos_requieren_capacidad_reform(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        usuario = self._usuario_sin_capacidades()
        client = APIClient()
        client.force_authenticate(user=usuario)
        resp = client.post(
            f'{REFORM_URL}',
            {'gestion': str(self.gestion.id), 'tipo': 'TRASPASO',
             'motivo': 'x', 'movimientos': [
                 self.movimiento('TRASPASO', origen=a, destino=b,
                                 monto='50.00'),
             ]},
            format='json',
        )
        self.assertEqual(resp.status_code, 403, resp.data)


class ReformulacionFlujoTests(ReformulacionBase):
    def test_flujo_completo_submit_approve_apply_mueve_saldos(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='500.00'),
        ])
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']

        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'EN_REVISION')

        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/approve/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'APROBADA')
        self.assertEqual(resp.data['aprobada_por_email'], 'admin@techo.test')

        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'APLICADA')
        self.assertIsNotNone(resp.data['fecha_aplicacion'])

        # Saldos movidos: origen baja, destino sube (500 A→B).
        self.assertEqual(self.source(a).monto, Decimal('500.00'))
        self.assertEqual(self.source(b).monto, Decimal('800.00'))
        reform = Reforma.objects.get(pk=reform_id)
        self.assertEqual(reform.fecha_aplicacion is not None, True)
        self.assertEqual(reform.aprobada_por, self.admin)

    def test_observar_requiere_motivo_y_reenviar(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='100.00'),
        ])
        reform_id = resp.data['id']
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        # Observar sin motivo → 400.
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/observe/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/observe/',
            {'observaciones': 'Falta la resolución'}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'OBSERVADA')
        # Re-envío tras observación.
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'EN_REVISION')

    def test_apply_de_reform_no_aprobada_rechazado(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='100.00'),
        ])
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        # BORRADOR → apply rechazado.
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        # EN_REVISION → apply rechazado (falta aprobar).
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        reform = Reforma.objects.get(pk=reform_id)
        self.assertEqual(reform.estado, 'EN_REVISION')
        # Nada aplicado.
        self.assertEqual(self.source(a).monto, Decimal('1000.00'))
        self.assertEqual(self.source(b).monto, Decimal('300.00'))

    def test_rechazar_reform_no_aplica(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='100.00'),
        ])
        reform_id = resp.data['id']
        self.client.post(f'{REFORM_URL}{reform_id}/submit/', {}, format='json')
        # Rechazo sin motivo → 400.
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/reject/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/reject/',
            {'motivo': 'No corresponde la reasignación'}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'RECHAZADA')
        # Una rechazada no puede aplicarse.
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(self.source(a).monto, Decimal('1000.00'))
        self.assertEqual(self.source(b).monto, Decimal('300.00'))

    def test_movimiento_registra_saldo_antes_despues(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='250.00'),
        ])
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        mov = ReformaMovimiento.objects.get(reform_id=reform_id)
        self.assertEqual(mov.saldo_antes, Decimal('1000.00'))
        self.assertEqual(mov.saldo_despues, Decimal('750.00'))
        # El detalle de la API expone los saldos.
        self.assertEqual(resp.data['movimientos'][0]['saldo_antes'],
                         '1000.00')
        self.assertEqual(resp.data['movimientos'][0]['saldo_despues'],
                         '750.00')


class ReformulacionAtomicidadTests(ReformulacionBase):
    def test_traspaso_sin_saldo_400_budget_exceeded_rollback_total(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        # Traspaso de 2000 > saldo de A (1000) → BUDGET_EXCEEDED al aplicar.
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='2000.00'),
        ])
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['available'], '1000.00')
        # ROLLBACK COMPLETO: reform sigue APROBADA y saldos intactos.
        reform = Reforma.objects.get(pk=reform_id)
        self.assertEqual(reform.estado, 'APROBADA')
        self.assertIsNone(reform.fecha_aplicacion)
        self.assertEqual(self.source(a).monto, Decimal('1000.00'))
        self.assertEqual(self.source(b).monto, Decimal('300.00'))
        # La versión activa abierta por el ajuste también se revirtió.
        self.assertEqual(
            DistribucionVersion.objects.filter(
                gestion=self.gestion, inmutable=False,
            ).count(), 0,
        )

    def test_segundo_movimiento_fallido_rollback_del_primero(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        # Primer movimiento VÁLIDO (300: A 1000→700, B 300→600); segundo
        # INVALIDO (700 de B, que tras el primero solo tiene 600) → el
        # primer movimiento también se revierte (atomicidad §97).
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='300.00'),
            self.movimiento('TRASPASO', origen=b, destino=a, monto='700.00'),
        ])
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        # NADA se movió: A sigue con 1000 y B con 300.
        self.assertEqual(self.source(a).monto, Decimal('1000.00'))
        self.assertEqual(self.source(b).monto, Decimal('300.00'))


class ReformulacionTiposTests(ReformulacionBase):
    def test_incremento_dentro_del_techo_y_exceso(self):
        self.preparar_distribucion_fijada()
        # Regla §96: el destino crece sin exceder el techo distribuible de
        # la fuente (1500): B (300) puede crecer hasta 1500; más → 400.
        b = self.apertura('Apertura B')
        resp = self.crear_api(
            tipo='INCREMENTO',
            movimientos=[
                self.movimiento('INCREMENTO', destino=b, monto='150.00'),
            ],
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(self.source(b).monto, Decimal('450.00'))
        # saldo_antes/despues del DESTINO (sin origen).
        mov = ReformaMovimiento.objects.get(reform_id=reform_id)
        self.assertEqual(mov.saldo_antes, Decimal('300.00'))
        self.assertEqual(mov.saldo_despues, Decimal('450.00'))

        # Segundo incremento de 1300: B (450) quedaría en 1750 > techo 1500
        # → BUDGET_EXCEEDED con available = techo − saldo actual.
        resp = self.crear_api(
            tipo='INCREMENTO',
            movimientos=[
                self.movimiento('INCREMENTO', destino=b, monto='1300.00'),
            ],
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        reform2_id = resp.data['id']
        self.flujo_hasta(reform2_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform2_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(resp.data['details']['available'], '1050.00')
        self.assertEqual(self.source(b).monto, Decimal('450.00'))

    def test_disminucion_devuelve_al_pool(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        resp = self.crear_api(
            tipo='DISMINUCION',
            movimientos=[
                self.movimiento('DISMINUCION', origen=a, monto='400.00'),
            ],
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(self.source(a).monto, Decimal('600.00'))
        mov = ReformaMovimiento.objects.get(reform_id=reform_id)
        self.assertEqual(mov.saldo_antes, Decimal('1000.00'))
        self.assertEqual(mov.saldo_despues, Decimal('600.00'))

    def test_cambio_fuente_en_la_misma_apertura(self):
        # Gestión 2042: techo 1000 en fuente A + 1000 en fuente B.
        gestion = crear_gestion(2042, estado='HABILITADA')
        fuente_a = FuenteFinanciamiento.objects.create(
            codigo='41', denominacion='Fuente A (cambio)', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        fuente_b = FuenteFinanciamiento.objects.create(
            codigo='42', denominacion='Fuente B (cambio)', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        organismo = OrganismoFinanciador.objects.create(
            codigo='411', denominacion='Origen A (cambio)', gestion=gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.client.post(
            f'{BUDGET_URL}directive-ceilings/',
            {'gestion': str(gestion.id)}, format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        ceiling = TechoDirectivo.objects.get(gestion=gestion)
        version = TechoVersion.objects.get(ceiling=ceiling, numero=1)
        RecursoTecho.objects.create(
            version=version, origen='SIGEP', monto='1000.00', concepto='A',
            fuente=fuente_a, organismo=organismo,
            created_by=self.admin, updated_by=self.admin,
        )
        RecursoTecho.objects.create(
            version=version, origen='SIGEP', monto='1000.00', concepto='B',
            fuente=fuente_b, organismo=organismo,
            created_by=self.admin, updated_by=self.admin,
        )
        enviar_a_revision(version, self.admin)
        aprobar(version, self.admin)
        fijar_techo(version, self.admin)

        # Aperturas: X {a: 500}, Y {a: 500, b: 300}; reserva en b: 700.
        # Σa = 1000 = techo_a; Σb = 300 (Y) + 700 (reserva) = 1000 = techo_b.
        resp = self.client.post(
            f'{BUDGET_URL}allocations/',
            {'gestion': str(gestion.id), 'denominacion': 'Apertura X',
             'fuentes': [{'fuente': str(fuente_a.id),
                          'organismo': str(organismo.id),
                          'monto': '500.00'}]},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        resp = self.client.post(
            f'{BUDGET_URL}allocations/',
            {'gestion': str(gestion.id), 'denominacion': 'Apertura Y',
             'fuentes': [
                 {'fuente': str(fuente_a.id), 'organismo': str(organismo.id),
                  'monto': '500.00'},
                 {'fuente': str(fuente_b.id), 'organismo': str(organismo.id),
                  'monto': '300.00'},
             ]},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        resp = self.client.post(
            f'{BUDGET_URL}reserves/',
            {'gestion': str(gestion.id), 'fuente': str(fuente_b.id),
             'organismo': str(organismo.id), 'tipo': 'OTRA',
             'motivo': 'Contingencia', 'monto': '700.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        version_dist = DistribucionVersion.objects.get(
            gestion=gestion, numero=1,
        )
        enviar_distribucion_a_revision(version_dist, self.admin)
        aprobar_distribucion(version_dist, self.admin)
        fijar_distribucion(version_dist, self.admin)

        # CAMBIO_FUENTE en X: 300 de la fuente a → fuente b (misma apertura).
        x = Apertura.objects.get(gestion=gestion, denominacion='Apertura X')
        resp = self.client.post(
            f'{REFORM_URL}',
            {'gestion': str(gestion.id), 'tipo': 'CAMBIO_FUENTE',
             'motivo': 'Cambiar origen de fondos',
             'movimientos': [{
                 'tipo': 'CAMBIO_FUENTE',
                 'apertura_origen': str(x.id),
                 'fuente': str(fuente_b.id),
                 'organismo': str(organismo.id),
                 'monto': '300.00',
             }]},
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)

        # X: fuente a baja 500 → 200; fuente b nace con 300.
        self.assertEqual(
            AperturaFuente.objects.get(
                allocation=x, fuente=fuente_a, organismo=organismo,
            ).monto, Decimal('200.00'),
        )
        self.assertEqual(
            AperturaFuente.objects.get(
                allocation=x, fuente=fuente_b, organismo=organismo,
            ).monto, Decimal('300.00'),
        )
        mov = ReformaMovimiento.objects.get(reform_id=reform_id)
        self.assertEqual(mov.saldo_antes, Decimal('500.00'))
        self.assertEqual(mov.saldo_despues, Decimal('200.00'))

    def test_cambio_fuente_sin_pool_en_destino_rechazado(self):
        # Sin pool en la fuente nueva: el CAMBIO_FUENTE falla (BUDGET_EXCEEDED).
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        fuente_extra = FuenteFinanciamiento.objects.create(
            codigo='51', denominacion='Fuente sin techo', gestion=self.gestion,
            fecha_vigencia_desde=timezone.now().date(),
        )
        resp = self.crear_api(
            tipo='CAMBIO_FUENTE',
            movimientos=[{
                'tipo': 'CAMBIO_FUENTE',
                'apertura_origen': str(a.id),
                'fuente': str(fuente_extra.id),
                'organismo': str(self.organismo.id),
                'monto': '100.00',
            }],
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED')
        self.assertEqual(self.source(a).monto, Decimal('1000.00'))


class ReformulacionAuditoriaTests(ReformulacionBase):
    def test_auditoria_registrada_en_aplicar(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='100.00'),
        ])
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        self.client.post(f'{REFORM_URL}{reform_id}/apply/', {}, format='json')
        evento = EventoAuditoria.objects.filter(
            entidad='Reforma', entidad_id=str(reform_id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertIn('aplicada', evento.resumen.lower())
        self.assertEqual(evento.accion, 'aprobar')
        self.assertEqual(evento.datos_posteriores['estado'], 'APLICADA')
        self.assertEqual(evento.gestion.anio, 2030)
        # El flujo completo dejó su rastro (crear → enviar → aprobar → aplicar).
        self.assertGreaterEqual(
            EventoAuditoria.objects.filter(entidad='Reforma',
                                           entidad_id=str(reform_id)).count(),
            4,
        )

    def test_estados_terminales_no_transicionan(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='50.00'),
        ])
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        self.client.post(f'{REFORM_URL}{reform_id}/apply/', {}, format='json')
        # APLICADA: no admite más transiciones.
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/submit/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/reject/', {'motivo': 'x'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400, resp.data)


# ===========================================================================
# Fase 11 - Auditoría de trazabilidad (EventoAuditoria + GET /budget/audit/)
# ===========================================================================

AUDIT_URL = BUDGET_URL + 'audit/'


class AuditoriaFase11Tests(ReformulacionBase):
    """Fase 11: todo el ciclo deja EventoAuditoria y el endpoint /audit/
    lo expone con filtros y capacidad `sis_poa.budget.audit_read`."""

    def _usuario_con_capacidad(self, codigo):
        from apps.accounts.models import Capacidad
        rol = Rol.objects.create(codigo=f'rol_{codigo}', nombre='Rol')
        capacidad, _ = Capacidad.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': codigo, 'sistema': 'sis-poa'},
        )
        rol.capacidades.add(capacidad)
        usuario = Usuario.objects.create_user(
            email=f'{codigo}@audit.test', password='test2026'
        )
        usuario.roles.add(rol)
        return usuario

    def _cliente_como(self, usuario):
        client = APIClient()
        client.force_authenticate(user=usuario)
        return client

    def test_crear_apertura_registra_evento_allocation_create(self):
        resp = self.crear_apertura(monto='1000.00', denominacion='Apertura F11')
        self.assertEqual(resp.status_code, 201, resp.data)
        allocation = Apertura.objects.get(denominacion='Apertura F11')
        evento = EventoAuditoria.objects.filter(
            entidad='Apertura', entidad_id=str(allocation.id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'crear')
        self.assertEqual(evento.gestion.anio, 2030)
        self.assertEqual(evento.usuario, self.admin)
        self.assertEqual(evento.datos_posteriores['total'], '1000.00')

    def test_fijar_techo_registra_evento_freeze(self):
        # La base fija el techo en setUp (submit → approve → freeze).
        evento = EventoAuditoria.objects.filter(
            entidad='TechoVersion',
            entidad_id=str(self.version.id),
            accion='aprobar',
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertIn('fijado', evento.resumen.lower())
        self.assertEqual(evento.gestion.anio, 2030)
        self.assertEqual(evento.datos_posteriores['estado'], 'FIJADO')
        self.assertIn('hash', evento.datos_posteriores)

    def test_aplicar_reform_registra_evento_aplicar(self):
        self.preparar_distribucion_fijada()
        a = self.apertura('Apertura A')
        b = self.apertura('Apertura B')
        resp = self.crear_api(movimientos=[
            self.movimiento('TRASPASO', origen=a, destino=b, monto='100.00'),
        ])
        reform_id = resp.data['id']
        self.flujo_hasta(reform_id, 'approve')
        resp = self.client.post(
            f'{REFORM_URL}{reform_id}/apply/', {}, format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        evento = EventoAuditoria.objects.filter(
            entidad='Reforma', entidad_id=str(reform_id),
        ).order_by('-creado_en').first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.accion, 'aprobar')
        self.assertIn('aplicada', evento.resumen.lower())
        self.assertEqual(evento.datos_posteriores['estado'], 'APLICADA')
        self.assertEqual(evento.gestion.anio, 2030)

    def test_endpoint_audit_filtra_por_gestion_y_entidad(self):
        # Eventos de la gestión 2030 (apertura + techo de la base).
        self.crear_apertura(monto='500.00', denominacion='Auditable')
        # Eventos de OTRA gestión (2031), que el filtro debe excluir.
        self.crear_gestion_con_techo(2031, '1000.00')

        auditor = self._usuario_con_capacidad('sis_poa.budget.audit_read')
        client = self._cliente_como(auditor)

        resp = client.get(f'{AUDIT_URL}', {'gestion': '2030'})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn('count', resp.data)
        self.assertGreaterEqual(resp.data['count'], 1)
        for fila in resp.data['results']:
            self.assertEqual(fila['gestion'], 2030)
        entidades = {fila['entidad'] for fila in resp.data['results']}
        self.assertIn('Apertura', entidades)

        # Filtro por slug de entidad del ciclo.
        resp = client.get(f'{AUDIT_URL}', {'gestion': '2030',
                                           'entidad': 'allocation'})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(
            all(f['entidad'] == 'Apertura' for f in resp.data['results'])
        )
        # El slug de techo directivo resuelve a TechoVersion.
        resp = client.get(f'{AUDIT_URL}', {'gestion': '2030',
                                           'entidad': 'directive-ceiling'})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(
            all(f['entidad'] == 'TechoVersion'
                for f in resp.data['results'])
        )
        # Acción semántica CREATE → código del catálogo 'crear'.
        resp = client.get(f'{AUDIT_URL}', {'gestion': '2030',
                                           'accion': 'CREATE'})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(all(f['accion'] == 'crear' for f in resp.data['results']))

    def test_endpoint_audit_exige_capacidad_audit_read(self):
        self.crear_apertura(monto='500.00', denominacion='Auditable')
        sin_permiso = self._usuario_con_capacidad('sis_poa.budget.manage')
        client = self._cliente_como(sin_permiso)
        resp = client.get(f'{AUDIT_URL}', {'gestion': '2030'})
        self.assertEqual(resp.status_code, 403, resp.data)

    def test_helper_registrar_auditoria_mapea_acciones_semanticas(self):
        from .services import ACCIONES_AUDITORIA, registrar_auditoria

        evento = registrar_auditoria(
            self.admin, 'FREEZE', 'TechoVersion', 'f11-v1',
            {'estado': 'APROBADO'}, {'estado': 'FIJADO'},
            gestion=2030, version=1, motivo='Techo fijado (F11)',
        )
        self.assertEqual(evento.accion, 'aprobar')
        self.assertIn('fijado', evento.resumen.lower())
        evento = registrar_auditoria(
            self.admin, 'RELEASE', 'Reserva', 'f11-r1',
            {'estado': 'ACTIVA'}, {'estado': 'LIBERADA'},
            gestion=2030, motivo='Reserva liberada (F11)',
        )
        self.assertEqual(evento.accion, 'modificar')
        self.assertEqual(evento.gestion.anio, 2030)
        with self.assertRaises(ValidationError):
            registrar_auditoria(
                self.admin, 'NO_EXISTE', 'Reserva', 'x',
                None, None, gestion=2030,
            )
        # El mapeo cubre todas las acciones semánticas del ciclo.
        for clave in ('CREATE', 'UPDATE', 'DELETE', 'IMPORT', 'SUBMIT',
                      'OBSERVE', 'APPROVE', 'FREEZE', 'REFORM', 'RELEASE',
                      'CLOSE', 'RESTORE', 'CONSOLIDATE'):
            self.assertIn(clave, ACCIONES_AUDITORIA)


# ===========================================================================
# Fase 12 - Testing E2E del flujo completo (§135): APIClient real, superuser
# ===========================================================================


class FlujoCompletoE2ETests(TestCase):
    """E2E del ciclo presupuestario completo vía API (Fase 12, §135).

    Recorre el flujo del administrador de punta a punta usando SOLO
    endpoints (APIClient autenticado como superuser), verificando cada paso
    con un assert explícito (mensaje descriptivo) antes de continuar:

        1. Habilitar la gestión 2040 (fiscal-years + enable).
        2. Techo SIGEP (245.290.497,50; fuente 41 / organismo 113).
        3. Recursos propios municipales (5.000.000).
        4. Gastos obligatorios (6.464.396,00; fuente 41).
        5. Composición (bruto / distribuible exactos).
        6. Revisión → aprobación → fijación del techo (inmutable + hash).
        7. Categorías programáticas (PROGRAMA 09 + SUBPROGRAMA 010).
        8. Distribución: aperturas + reserva DISTRITAL = techo por fuente.
        9. Validación de fijación (Σfuente = techo).
        10. Fijación de la distribución (inmutable; sin aperturas nuevas).
        11. Objetos del gasto (400.000 programado / 100.000 disponible;
            exceso → 409 BUDGET_EXCEEDED y sistema intacto).
        12. Reformulación TRASPASO (50.000 entre aperturas; saldos movidos
            y ReformaMovimiento con saldo_antes/saldo_despues).
        13. Auditoría: evento por cada operación clave.

    Montos Decimal exactos (sin float). Un solo `test_*` para preservar el
    estado secuencial del flujo. Corre en < 2 minutos: TestCase Django en
    una transacción, sin concurrencia real.
    """

    ANIO = 2040

    # Datos de prueba del flujo (§135) — NO hardcodeados en código
    # productivo, solo en este test.
    SIGEP = Decimal('245290497.50')
    MUNICIPAL = Decimal('5000000.00')
    OBLIGATORIOS = Decimal('6464396.00')

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@e2e.test', password='test2026'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    # -- Helpers ------------------------------------------------------------

    def _post(self, ruta, datos):
        return self.client.post(f'{BUDGET_URL}{ruta}', datos, format='json')

    def _crear_apertura(self, gestion, fuente, organismo, monto,
                        denominacion):
        resp = self._post('allocations/', {
            'gestion': str(gestion.id), 'denominacion': denominacion,
            'codigo_sisin': '12345678',
            'fuentes': [{
                'fuente': str(fuente.id), 'organismo': str(organismo.id),
                'monto': monto,
            }],
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['estado'], 'ACTIVA', resp.data)
        self.assertEqual(resp.data['total'], monto, resp.data)
        return Apertura.objects.get(pk=resp.data['id'])

    def _flujo_techo(self, ceiling_id, prefijo):
        for paso in ('submit', 'approve', 'freeze'):
            resp = self.client.post(
                f'{BUDGET_URL}{prefijo}{ceiling_id}/{paso}/', {},
                format='json',
            )
            self.assertEqual(resp.status_code, 200, f'{paso}: {resp.data}')
        return resp

    # -- E2E ----------------------------------------------------------------

    def test_flujo_completo_administrador(self):
        # --------------------------------------------------------------
        # 1. Habilitar gestión: POST fiscal-years (2040) + enable
        # --------------------------------------------------------------
        resp = self._post('fiscal-years/', {'anio': self.ANIO})
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['estado'], 'preparacion', resp.data)
        gestion = GestionFiscal.objects.get(anio=self.ANIO)

        resp = self.client.post(
            f'{BUDGET_URL}fiscal-years/{gestion.id}/enable/', {},
            format='json',
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['estado'], 'HABILITADA',
                         'el enable debe dejar la gestión HABILITADA')
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA',
                         'el estado en BD debe ser HABILITADA')
        self.assertIsNotNone(gestion.fecha_apertura)

        # --------------------------------------------------------------
        # 2-4. Catálogos + techo directivo (SIGEP, municipales, oblig.)
        # --------------------------------------------------------------
        fuente = FuenteFinanciamiento.objects.create(
            codigo='41', denominacion='Coparticipación tributaria',
            gestion=gestion, fecha_vigencia_desde=timezone.now().date(),
        )
        organismo = OrganismoFinanciador.objects.create(
            codigo='113', denominacion='Organismo financiador SIGEP',
            gestion=gestion, fecha_vigencia_desde=timezone.now().date(),
        )

        resp = self._post('directive-ceilings/', {'gestion': str(gestion.id)})
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['estado'], 'BORRADOR', resp.data)
        ceiling = TechoDirectivo.objects.get(gestion=gestion)
        version = TechoVersion.objects.get(
            ceiling=ceiling, numero=1,
        )
        self.assertEqual(version.estado, 'BORRADOR',
                         'la versión 1 del techo nace en BORRADOR')

        resp = self._post('resources/', {
            'version': str(version.id), 'origen': 'SIGEP', 'concepto': 'CT',
            'monto': str(self.SIGEP), 'fuente': str(fuente.id),
            'organismo': str(organismo.id),
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['monto'], str(self.SIGEP), resp.data)

        resp = self._post('resources/', {
            'version': str(version.id), 'origen': 'MUNICIPAL',
            'concepto': 'Ingresos propios', 'monto': str(self.MUNICIPAL),
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['monto'], str(self.MUNICIPAL), resp.data)

        resp = self._post('mandatory-expenses/', {
            'version': str(version.id), 'denominacion': 'Gastos obligatorios',
            'monto': str(self.OBLIGATORIOS), 'fuente': str(fuente.id),
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['monto'], str(self.OBLIGATORIOS), resp.data)

        # --------------------------------------------------------------
        # 5. Composición: bruto = SIGEP + municipales; distribuible = − oblig.
        # --------------------------------------------------------------
        bruto = self.SIGEP + self.MUNICIPAL
        distribuible = bruto - self.OBLIGATORIOS
        resp = self.client.get(
            f'{BUDGET_URL}directive-ceilings/{ceiling.id}/composition/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(Decimal(resp.data['techo_bruto']), bruto,
                         f'techo bruto debe ser SIGEP + municipales = {bruto}')
        self.assertEqual(
            Decimal(resp.data['techo_distribuible']), distribuible,
            f'distribuible = bruto − obligatorios = {distribuible}',
        )
        self.assertEqual(Decimal(resp.data['sigep']), self.SIGEP)
        self.assertEqual(Decimal(resp.data['municipales']), self.MUNICIPAL)
        self.assertEqual(Decimal(resp.data['gastos_obligatorios']),
                         self.OBLIGATORIOS)
        self.assertEqual(len(resp.data['por_fuente']), 2,
                         'fuente 41 + recursos sin fuente agrupados aparte')
        por_fuente = {f['fuente']: f for f in resp.data['por_fuente']}
        self.assertEqual(Decimal(por_fuente['41']['monto']), self.SIGEP)
        self.assertEqual(
            Decimal(por_fuente['SIN_FUENTE']['monto']), self.MUNICIPAL,
            'el recurso MUNICIPAL sin fuente se agrupa como SIN_FUENTE',
        )

        # --------------------------------------------------------------
        # 6. Revisión → aprobación → fijación del techo
        # --------------------------------------------------------------
        self._flujo_techo(ceiling.id, 'directive-ceilings/')
        version.refresh_from_db()
        self.assertEqual(version.estado, 'FIJADO',
                         'el techo debe quedar FIJADO tras el freeze')
        self.assertTrue(version.inmutable,
                        'la versión fijada es inmutable (solo lectura)')
        self.assertTrue(version.hash,
                        'la versión fijada lleva checksum SHA-256')
        self.assertEqual(len(version.hash), 64)
        self.assertTrue(version.verificar_hash(),
                        'el checksum se verifica contra los datos')
        ceiling.refresh_from_db()
        self.assertEqual(ceiling.estado, 'FIJADO')

        # --------------------------------------------------------------
        # 7. Categorías programáticas (PROGRAMA 09 + SUBPROGRAMA 010)
        # --------------------------------------------------------------
        resp = self._post('programmatic-categories/', {
            'gestion': gestion.id, 'codigo': '09',
            'denominacion': 'Servicios generales', 'nivel': 'PROGRAMA',
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['codigo'], '09',
                         'el código preserva los ceros')
        resp = self._post('programmatic-categories/', {
            'gestion': gestion.id, 'codigo': '010',
            'denominacion': 'Servicios administrativos',
            'nivel': 'SUBPROGRAMA', 'parent': resp.data['id'],
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['codigo_compuesto'], '09.010')

        # --------------------------------------------------------------
        # 8. Distribución: aperturas + reserva DISTRITAL = techo por fuente
        # --------------------------------------------------------------
        techo_fuente41 = self.SIGEP - self.OBLIGATORIOS  # 238.826.101,50
        apertura_a = self._crear_apertura(
            gestion, fuente, organismo, '200000000.00', 'Apertura principal',
        )
        apertura_b = self._crear_apertura(
            gestion, fuente, organismo, '500000.00', 'Apertura ejemplo 500K',
        )
        distribuido_total = Decimal('200500000.00')
        reserva_monto = techo_fuente41 - distribuido_total  # 38.326.101,50
        self.assertGreater(reserva_monto, Decimal('0.00'))
        resp = self._post('reserves/', {
            'gestion': str(gestion.id), 'fuente': str(fuente.id),
            'organismo': str(organismo.id), 'tipo': 'DISTRITAL',
            'motivo': 'Reserva por el resto del techo distribuible',
            'monto': str(reserva_monto),
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['tipo'], 'DISTRITAL', resp.data)
        self.assertEqual(resp.data['estado'], 'ACTIVA', resp.data)

        # Σ por fuente: distribuido + reservado = techo → disponible 0.
        self.assertEqual(
            distribuido_por_fuente(gestion)[fuente.id], distribuido_total,
            'el distribuido debe ser la suma de las aperturas',
        )
        self.assertEqual(
            reservado_por_fuente(gestion)[fuente.id], reserva_monto,
            'la reserva DISTRITAL cubre exactamente el resto del techo',
        )
        self.assertEqual(
            disponible_por_fuente(gestion)[fuente.id], Decimal('0.00'),
            'sin disponible: distribuido + reserva = techo por fuente',
        )

        # --------------------------------------------------------------
        # 9. Validación de la fijación (GET validate → Σfuente = techo)
        # --------------------------------------------------------------
        version_dist = version_distribucion_activa(gestion)
        self.assertEqual(version_dist.numero, 1, version_dist.numero)
        resp = self.client.get(
            f'{BUDGET_URL}distributions/{version_dist.id}/validate/'
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data['valida'],
                        'la distribución está completa por fuente')
        fila = resp.data['diferencias'][0]
        self.assertEqual(Decimal(fila['techo']), techo_fuente41)
        self.assertEqual(Decimal(fila['distribuido']), distribuido_total)
        self.assertEqual(Decimal(fila['reservado']), reserva_monto)
        self.assertEqual(Decimal(fila['diferencia']), Decimal('0.00'))

        # --------------------------------------------------------------
        # 10. Fijar la distribución (submit → approve → freeze)
        # --------------------------------------------------------------
        self._flujo_techo(version_dist.id, 'distributions/')
        version_dist.refresh_from_db()
        self.assertEqual(version_dist.estado, 'FIJADO',
                         'la distribución debe quedar FIJADA')
        self.assertTrue(version_dist.inmutable)
        self.assertTrue(version_dist.hash)
        self.assertEqual(len(version_dist.hash), 64)
        self.assertTrue(version_dist.verificar_hash())

        # Inmutabilidad E2E: una apertura nueva tras la fijación se rechaza.
        resp = self._post('allocations/', {
            'gestion': str(gestion.id), 'denominacion': 'Post fijación',
            'fuentes': [{
                'fuente': str(fuente.id), 'organismo': str(organismo.id),
                'monto': '100.00',
            }],
        })
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn('fijada', json.dumps(resp.data))

        # --------------------------------------------------------------
        # 11. Objetos del gasto sobre la apertura de 500.000
        # --------------------------------------------------------------
        objetos = {}
        for codigo, denominacion in (
            ('25220', 'Papelería y útiles'),
            ('34200', 'Pasajes al interior'),
            ('43110', 'Maquinaria y equipo'),
            ('42310', 'Muebles de oficina'),
        ):
            objetos[codigo] = ObjetoGasto.objects.create(
                codigo=codigo, denominacion=denominacion, gestion=gestion,
                fecha_vigencia_desde=timezone.now().date(),
            )
        for codigo, monto in (('25220', '100000.00'),
                              ('34200', '180000.00'),
                              ('43110', '120000.00')):
            resp = self._post('expense-objects/', {
                'allocation': str(apertura_b.id),
                'objeto_gasto': str(objetos[codigo].id), 'monto': monto,
            })
            self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(
            BudgetControlService.get_allocated_to_expense_objects(apertura_b),
            Decimal('400000.00'),
            'programado = 100.000 + 180.000 + 120.000 = 400.000',
        )
        self.assertEqual(
            BudgetControlService.get_allocation_available(apertura_b),
            Decimal('100000.00'),
            'disponible = techo 500.000 − programado 400.000',
        )
        resp = self._post('expense-objects/', {
            'allocation': str(apertura_b.id),
            'objeto_gasto': str(objetos['42310'].id), 'monto': '150000.00',
        })
        self.assertEqual(resp.status_code, 409,
                         'programar 150.000 sobre disponible 100.000 → 409')
        self.assertEqual(resp.data['code'], 'BUDGET_EXCEEDED', resp.data)
        self.assertEqual(resp.data['details']['requested'], '150000.00')
        self.assertEqual(resp.data['details']['available'], '100000.00')
        self.assertEqual(resp.data['details']['difference'], '50000.00')
        self.assertFalse(
            AsignacionObjetoGastoTecho.objects.filter(
                allocation=apertura_b, objeto_gasto=objetos['42310'],
            ).exists(),
            'la programación con exceso no se persiste',
        )
        self.assertEqual(
            AsignacionObjetoGastoTecho.objects.filter(allocation=apertura_b)
            .count(), 3,
            'el sistema queda intacto tras el rechazo (siguen 3 objetos)',
        )

        # --------------------------------------------------------------
        # 12. Reformulación: TRASPASO de 50.000 entre aperturas (fuente 41)
        # --------------------------------------------------------------
        resp = self._post('reforms/', {
            'gestion': str(gestion.id), 'tipo': 'TRASPASO',
            'motivo': 'Reasignación entre aperturas (E2E)',
            'movimientos': [{
                'tipo': 'TRASPASO',
                'apertura_origen': str(apertura_a.id),
                'apertura_destino': str(apertura_b.id),
                'fuente': str(fuente.id), 'organismo': str(organismo.id),
                'monto': '50000.00', 'motivo': 'Traspaso E2E',
            }],
        })
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['estado'], 'BORRADOR', resp.data)
        reform_id = resp.data['id']
        for paso in ('submit', 'approve', 'apply'):
            resp = self.client.post(
                f'{BUDGET_URL}reforms/{reform_id}/{paso}/', {}, format='json',
            )
            self.assertEqual(resp.status_code, 200, f'{paso}: {resp.data}')
        self.assertEqual(resp.data['estado'], 'APLICADA', resp.data)
        self.assertIsNotNone(resp.data['fecha_aplicacion'])

        # Saldos movidos: origen −50.000, destino +50.000.
        self.assertEqual(
            AperturaFuente.objects.get(
                allocation=apertura_a, fuente=fuente,
            ).monto,
            Decimal('199950000.00'),
            'origen: 200.000.000 − 50.000 = 199.950.000',
        )
        self.assertEqual(
            AperturaFuente.objects.get(
                allocation=apertura_b, fuente=fuente,
            ).monto,
            Decimal('550000.00'),
            'destino: 500.000 + 50.000 = 550.000',
        )
        mov = ReformaMovimiento.objects.get(reform_id=reform_id)
        self.assertEqual(mov.saldo_antes, Decimal('200000000.00'),
                         'saldo_antes del origen antes del movimiento')
        self.assertEqual(mov.saldo_despues, Decimal('199950000.00'),
                         'saldo_despues del origen tras el movimiento')

        # --------------------------------------------------------------
        # 13. Auditoría: al menos un evento por operación clave (§135)
        # --------------------------------------------------------------
        resp = self.client.get(
            f'{BUDGET_URL}audit/', {'gestion': str(self.ANIO)},
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertGreaterEqual(resp.data['count'], 1)
        entidades = {fila['entidad'] for fila in resp.data['results']}
        for entidad, operacion in (
            ('GestionFiscal', 'enable de la gestión'),
            ('TechoVersion', 'freeze del techo directivo'),
            ('DistribucionVersion', 'freeze de la distribución'),
            ('Reforma', 'reformulación aplicada'),
        ):
            self.assertIn(
                entidad, entidades,
                f'la auditoría debe incluir la operación: {operacion}',
            )
