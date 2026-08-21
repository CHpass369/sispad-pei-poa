"""Lo aprobado en un acta cae en la fila de gasto que le corresponde."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Rol
from apps.budget.models import (
    Apertura, AperturaFuente, CategoriaProgramaticaTecho, RangoProgramaDirectriz,
    RecursoTecho, TechoDirectivo,
)
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.gestion.models import GestionFiscal
from apps.priorizacion.models import ActaPriorizacion, PlantillaActa
from apps.territorio.models import Distrito

User = get_user_model()
API = '/api/v1/priorizacion'


class MaterializacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tecnico = User.objects.create_user(email='t@t.com', password='x12345678')
        self.jefatura = User.objects.create_user(email='j@t.com', password='x12345678')
        rol, _ = Rol.objects.get_or_create(codigo='jefe_poa',
                                           defaults={'nombre': 'Jefatura POA'})
        self.jefatura.roles.add(rol)
        self.client.force_authenticate(user=self.tecnico)

        self.gestion = GestionFiscal.objects.create(anio=2027, estado='HABILITADA')
        # La directriz del Anexo VI: sin ella no se valida ningún código.
        for desde, hasta, den in [
            (0, 0, 'FUNCIONAMIENTO ÓRGANO EJECUTIVO'),
            (170, 179, 'INFRAESTRUCTURA URBANA Y RURAL'),
            (180, 189, 'GESTIÓN DE CAMINOS VECINALES'),
            (360, 890, 'OTROS PROGRAMAS ESPECÍFICOS'),
        ]:
            RangoProgramaDirectriz.objects.create(
                gestion=2027, desde=desde, hasta=hasta, denominacion=den,
                finalidad_funcion='1.1.1', sector_economico='14')
        self.distrito = Distrito.objects.create(codigo='D2', nombre='DISTRITO 2')
        PlantillaActa.objects.create(nombre='Acta', titulo='ACTA',
                                     encabezado='X', firmas=[])

        catalogo = dict(gestion=self.gestion, fecha_vigencia_desde=date(2027, 1, 1))
        self.ff = FuenteFinanciamiento.objects.create(
            codigo='41', denominacion='Transferencias T.G.N.', **catalogo)
        self.of = OrganismoFinanciador.objects.create(
            codigo='113', denominacion='TGN - Coparticipación', **catalogo)

        # Categoría de proyecto: programa 180, SISIN, actividad 000. El nivel
        # es PROYECTO justamente porque el segmento del medio es un SISIN.
        self.categoria = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='180 08620281200000 000',
            nivel='PROYECTO', denominacion='IMPLEM. PAVIMENTO FLEXIBLE')
        # Una de funcionamiento, para distinguir los dos niveles.
        CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='000 0 001', nivel='ACTIVIDAD',
            denominacion='FUNCIONAMIENTO ALCALDIA MUNICIPAL')

        techo = TechoDirectivo.objects.create(gestion=self.gestion,
                                              version_actual=1)
        version = techo.versiones.create(numero=1)
        RecursoTecho.objects.create(version=version, origen='SIGEP',
                                    fuente=self.ff, organismo=self.of,
                                    monto=Decimal('1000000'))

    # --- Helpers -----------------------------------------------------------

    def crear_acta(self, proyectos=None, otb='OTB SAN JOSE'):
        datos = {
            'gestion': 2027, 'distrito': str(self.distrito.id), 'otb': otb,
            'presidente': 'JUAN', 'responsable_registro': 'ANA',
            'fecha': '2026-09-03',
            'proyectos': proyectos if proyectos is not None else [{
                'nombre': 'IMPLEM. PAVIMENTO FLEXIBLE D2', 'monto': '220000',
                'sisin': '08620281200000',
                'categoria_programatica': '180 08620281200000 000',
                'fuente': str(self.ff.id), 'organismo': str(self.of.id),
            }],
        }
        return self.client.post(f'{API}/actas/', datos, format='json').json()

    def validar(self, acta_id):
        """El volcado al gasto ocurre acá, no al aprobar."""
        self.client.force_authenticate(user=self.tecnico)
        return self.client.post(f'{API}/actas/{acta_id}/validar/')

    def aprobar(self, acta_id):
        self.validar(acta_id)
        self.client.force_authenticate(user=self.jefatura)
        r = self.client.post(f'{API}/actas/{acta_id}/aprobar/')
        self.client.force_authenticate(user=self.tecnico)
        return r

    # --- Volcado -----------------------------------------------------------

    def test_validar_crea_la_fila_de_gasto_de_su_categoria(self):
        r = self.validar(self.crear_acta()['id'])
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        apertura = Apertura.objects.get()
        self.assertEqual(apertura.categoria, self.categoria)
        self.assertEqual(apertura.proyecto_codigo, '180')
        self.assertEqual(apertura.codigo_sisin, '08620281200000')
        self.assertEqual(apertura.actividad_codigo, '000')

        fila = AperturaFuente.objects.get()
        self.assertEqual(fila.fuente, self.ff)
        self.assertEqual(fila.organismo, self.of)
        self.assertEqual(fila.monto, Decimal('220000'))

    def test_informa_en_que_programa_quedo_cada_monto(self):
        r = self.validar(self.crear_acta()['id'])
        volcado = r.json()['materializacion']['materializados'][0]
        self.assertEqual(volcado['programa'], '180')
        self.assertEqual(volcado['par'], '41/113')
        self.assertEqual(volcado['monto'], 220000.0)
        self.assertTrue(volcado['apertura_creada'])

    def test_dos_proyectos_de_la_misma_categoria_y_par_suman_en_una_fila(self):
        acta = self.crear_acta(proyectos=[
            {'nombre': 'A', 'monto': '220000', 'sisin': '',
             'categoria_programatica': '180 08620281200000 000',
             'fuente': str(self.ff.id), 'organismo': str(self.of.id)},
            {'nombre': 'B', 'monto': '30000', 'sisin': '',
             'categoria_programatica': '180 08620281200000 000',
             'fuente': str(self.ff.id), 'organismo': str(self.of.id)},
        ])
        self.validar(acta['id'])
        # AperturaFuente es única por (apertura, fuente, organismo).
        self.assertEqual(AperturaFuente.objects.count(), 1)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('250000'))

    def test_dos_actas_distintas_acumulan_sobre_la_misma_fila(self):
        self.aprobar(self.crear_acta()['id'])
        self.aprobar(self.crear_acta(otb='OTB LOS PINOS')['id'])
        self.assertEqual(Apertura.objects.count(), 1)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('440000'))

    def test_volver_a_aprobar_no_duplica_el_monto(self):
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        # El acta ya está aprobada: se fuerza una segunda materialización.
        from apps.priorizacion.materializacion import materializar_acta
        materializar_acta(ActaPriorizacion.objects.get(id=acta_id))
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('220000'))

    def test_corregir_el_monto_y_reaprobar_recalcula_en_vez_de_sumar(self):
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        acta = ActaPriorizacion.objects.get(id=acta_id)
        proyecto = acta.proyectos.get()
        proyecto.monto = Decimal('100000')
        proyecto.save()
        from apps.priorizacion.materializacion import materializar_acta
        materializar_acta(acta)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('100000'))

    # --- Lo que no se puede volcar ----------------------------------------

    def test_un_proyecto_sin_par_ff_of_se_informa_y_no_se_pierde_en_silencio(self):
        acta = self.crear_acta(proyectos=[{
            'nombre': 'SIN PAR', 'monto': '5000', 'sisin': '',
            'categoria_programatica': '180 08620281200000 000',
        }])
        r = self.validar(acta['id'])
        omitidos = r.json()['materializacion']['omitidos']
        self.assertEqual(len(omitidos), 1)
        self.assertIn('fuente/organismo', omitidos[0]['motivo'])
        self.assertEqual(AperturaFuente.objects.count(), 0)

    def test_un_proyecto_sin_categoria_se_informa(self):
        acta = self.crear_acta(proyectos=[{
            'nombre': 'SIN CATEGORIA', 'monto': '5000', 'sisin': '',
            'categoria_programatica': '',
            'fuente': str(self.ff.id), 'organismo': str(self.of.id),
        }])
        omitidos = self.validar(acta['id']).json()['materializacion']['omitidos']
        self.assertIn('categoría programática', omitidos[0]['motivo'])

    def test_un_proyecto_que_no_esta_en_el_catalogo_se_da_de_alta(self):
        # Antes se descartaba. Un proyecto priorizado que todavía no tiene
        # categoría no es un error: es una categoría que hay que crear.
        acta = self.crear_acta(proyectos=[{
            'nombre': 'CONST. PUENTE NUEVO', 'monto': '5000', 'sisin': '',
            'categoria_programatica': '380 12345678901234 000',
            'fuente': str(self.ff.id), 'organismo': str(self.of.id),
        }])
        r = self.validar(acta['id'])
        self.assertEqual(r.json()['materializacion']['omitidos'], [])
        creada = CategoriaProgramaticaTecho.objects.get(
            codigo='380 12345678901234 000')
        self.assertEqual(creada.denominacion, 'CONST. PUENTE NUEVO')
        self.assertEqual(Apertura.objects.count(), 1)

    def test_el_acta_queda_aprobada_aunque_algo_no_se_pueda_volcar(self):
        acta = self.crear_acta(proyectos=[
            {'nombre': 'OK', 'monto': '1000', 'sisin': '',
             'categoria_programatica': '180 08620281200000 000',
             'fuente': str(self.ff.id), 'organismo': str(self.of.id)},
            {'nombre': 'SIN PAR', 'monto': '5000', 'sisin': '',
             'categoria_programatica': '180 08620281200000 000'},
        ])
        r = self.validar(acta['id'])
        self.assertEqual(r.json()['estado'], 'VALIDADO')
        self.assertEqual(len(r.json()['materializacion']['materializados']), 1)
        self.assertEqual(len(r.json()['materializacion']['omitidos']), 1)

    def test_la_revision_previa_no_escribe_nada(self):
        acta_id = self.crear_acta()['id']
        d = self.client.get(f'{API}/actas/{acta_id}/revision-previa/').json()
        self.assertEqual(len(d['listos']), 1)
        self.assertEqual(d['listos'][0]['par'], '41/113')
        self.assertEqual(Apertura.objects.count(), 0)
        self.assertEqual(AperturaFuente.objects.count(), 0)

    # --- Saldos ------------------------------------------------------------

    def test_lo_priorizado_sin_aprobar_compromete_el_techo(self):
        self.crear_acta()
        par = self.client.get(f'{API}/saldos/?gestion=2027').json()['pares'][0]
        self.assertEqual(par['techo'], 1000000.0)
        self.assertEqual(par['comprometido'], 220000.0)
        self.assertEqual(par['asignado'], 0.0)
        self.assertEqual(par['disponible'], 780000.0)

    def test_al_validar_el_monto_pasa_de_comprometido_a_asignado(self):
        self.validar(self.crear_acta()['id'])
        par = self.client.get(f'{API}/saldos/?gestion=2027').json()['pares'][0]
        self.assertEqual(par['comprometido'], 0.0)
        self.assertEqual(par['asignado'], 220000.0)
        # El disponible no cambia: la plata es la misma, cambió de estado.
        self.assertEqual(par['disponible'], 780000.0)

    def test_el_acta_que_se_edita_no_se_descuenta_a_si_misma(self):
        acta_id = self.crear_acta()['id']
        d = self.client.get(
            f'{API}/saldos/?gestion=2027&excluir_acta={acta_id}').json()
        self.assertEqual(d['pares'][0]['comprometido'], 0.0)
        self.assertEqual(d['pares'][0]['disponible'], 1000000.0)

    def test_el_saldo_muestra_el_sobregiro_en_vez_de_esconderlo(self):
        self.crear_acta(proyectos=[{
            'nombre': 'GRANDE', 'monto': '1500000', 'sisin': '',
            'categoria_programatica': '180 08620281200000 000',
            'fuente': str(self.ff.id), 'organismo': str(self.of.id)}])
        par = self.client.get(f'{API}/saldos/?gestion=2027').json()['pares'][0]
        self.assertEqual(par['disponible'], -500000.0)


class CircuitoActaTests(MaterializacionTests):
    """Quién puede mover el acta y qué pasa con el gasto en cada paso."""

    def test_solo_quien_registro_el_acta_puede_validarla(self):
        acta_id = self.crear_acta()['id']
        otro = User.objects.create_user(email='otro@t.com', password='x12345678')
        self.client.force_authenticate(user=otro)
        r = self.client.post(f'{API}/actas/{acta_id}/validar/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(AperturaFuente.objects.count(), 0)

    def test_desvalidar_devuelve_el_acta_a_borrador_y_libera_el_techo(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('220000'))

        r = self.client.post(f'{API}/actas/{acta_id}/desvalidar/')
        self.assertEqual(r.json()['estado'], 'BORRADOR')
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('0'))
        self.assertEqual(r.json()['revertidos'][0]['monto'], 220000.0)

    def test_desvalidar_es_del_autor_no_de_cualquiera(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        otro = User.objects.create_user(email='otro@t.com', password='x12345678')
        self.client.force_authenticate(user=otro)
        r = self.client.post(f'{API}/actas/{acta_id}/desvalidar/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_se_desvalida_lo_que_no_esta_validado(self):
        acta_id = self.crear_acta()['id']
        r = self.client.post(f'{API}/actas/{acta_id}/desvalidar/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_un_acta_aprobada_no_se_desvalida(self):
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        r = self.client.post(f'{API}/actas/{acta_id}/desvalidar/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('220000'))

    def test_solo_la_jefatura_aprueba(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        r = self.client.post(f'{API}/actas/{acta_id}/aprobar/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_observar_saca_el_monto_del_presupuesto_de_gastos(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        self.client.force_authenticate(user=self.jefatura)
        r = self.client.post(f'{API}/actas/{acta_id}/observar/',
                             {'comentario': 'Corregir el monto'})
        self.assertEqual(r.json()['estado'], 'OBSERVADO')
        # Un acta devuelta no puede seguir ocupando techo.
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('0'))

    def test_un_acta_aprobada_no_se_elimina(self):
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        r = self.client.delete(f'{API}/actas/{acta_id}/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_borrar_un_acta_validada_libera_lo_que_habia_cargado(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        r = self.client.delete(f'{API}/actas/{acta_id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('0'))

    def test_desvalidar_corregir_y_volver_a_validar_deja_el_monto_nuevo(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        self.client.post(f'{API}/actas/{acta_id}/desvalidar/')
        acta = ActaPriorizacion.objects.get(id=acta_id)
        proyecto = acta.proyectos.get()
        proyecto.monto = Decimal('75000')
        proyecto.save()
        self.validar(acta_id)
        self.assertEqual(AperturaFuente.objects.get().monto, Decimal('75000'))


class DocumentosDelActaTests(MaterializacionTests):
    """El acta emitida y la escaneada, cifradas en la base."""

    CLAVE = 'Zm9vYmFyYmF6cXV1eHF1dXhmb29iYXJiYXpxdXV4cXU='  # 32 bytes en base64

    def setUp(self):
        super().setUp()
        self.override = self.settings(DOCUMENTOS_CLAVE=self.CLAVE)
        self.override.enable()
        self.addCleanup(self.override.disable)

    def test_emitir_el_pdf_de_un_acta_aprobada_deja_copia_cifrada(self):
        from apps.documentos.models import DocumentoAdjunto
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        r = self.client.get(f'{API}/actas/{acta_id}/pdf/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        doc = DocumentoAdjunto.objects.get(tipo_documento='ACTA_GENERADA')
        self.assertTrue(doc.contenido_cifrado)
        # Lo guardado no se puede leer sin la clave.
        self.assertNotIn(b'%PDF', bytes(doc.contenido_cifrado))
        self.assertEqual(len(doc.hash_sha256), 64)

    def test_emitir_dos_veces_no_duplica_la_copia(self):
        from apps.documentos.models import DocumentoAdjunto
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        self.client.get(f'{API}/actas/{acta_id}/pdf/')
        self.client.get(f'{API}/actas/{acta_id}/pdf/')
        # Los bytes cambian en cada emisión por la hora del QR: guardar cada
        # descarga llenaría la base de copias equivalentes.
        self.assertEqual(
            DocumentoAdjunto.objects.filter(tipo_documento='ACTA_GENERADA').count(), 1)

    def test_un_acta_sin_aprobar_no_se_archiva(self):
        from apps.documentos.models import DocumentoAdjunto
        acta_id = self.crear_acta()['id']
        self.client.get(f'{API}/actas/{acta_id}/pdf/')
        # Antes de aprobarse el acta todavía se corrige.
        self.assertEqual(
            DocumentoAdjunto.objects.filter(tipo_documento='ACTA_GENERADA').count(), 0)

    def test_adjuntar_el_escaneado_lo_guarda_cifrado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.documentos.models import DocumentoAdjunto
        acta_id = self.crear_acta()['id']
        archivo = SimpleUploadedFile('acta-firmada.pdf', b'%PDF-1.4 firmada',
                                     content_type='application/pdf')
        r = self.client.post(f'{API}/actas/{acta_id}/adjuntar/',
                             {'archivo': archivo}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.json()['nombre'], 'acta-firmada.pdf')

        doc = DocumentoAdjunto.objects.get(tipo_documento='ACTA_ESCANEADA')
        self.assertNotIn(b'firmada', bytes(doc.contenido_cifrado))
        self.assertEqual(doc.tamanio_bytes, len(b'%PDF-1.4 firmada'))

    def test_adjuntar_sin_archivo_lo_dice(self):
        acta_id = self.crear_acta()['id']
        r = self.client.post(f'{API}/actas/{acta_id}/adjuntar/', {},
                             format='multipart')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_descargar_devuelve_el_documento_original(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        acta_id = self.crear_acta()['id']
        archivo = SimpleUploadedFile('firmada.pdf', b'%PDF-1.4 firmada',
                                     content_type='application/pdf')
        doc_id = self.client.post(f'{API}/actas/{acta_id}/adjuntar/',
                                  {'archivo': archivo},
                                  format='multipart').json()['id']
        r = self.client.get(f'/api/v1/documentos/{doc_id}/descargar/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.content, b'%PDF-1.4 firmada')
        self.assertEqual(len(r['X-Documento-Huella']), 64)

    def test_un_documento_alterado_no_se_entrega(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.documentos.models import DocumentoAdjunto
        acta_id = self.crear_acta()['id']
        archivo = SimpleUploadedFile('firmada.pdf', b'%PDF-1.4 firmada',
                                     content_type='application/pdf')
        doc_id = self.client.post(f'{API}/actas/{acta_id}/adjuntar/',
                                  {'archivo': archivo},
                                  format='multipart').json()['id']
        doc = DocumentoAdjunto.objects.get(id=doc_id)
        tocado = bytearray(doc.contenido_cifrado)
        tocado[0] ^= 1
        doc.contenido_cifrado = bytes(tocado)
        doc.save(update_fields=['contenido_cifrado'])

        r = self.client.get(f'/api/v1/documentos/{doc_id}/descargar/')
        # Se avisa, no se devuelve un documento dudoso.
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)

    def test_la_descarga_exige_sesion(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        acta_id = self.crear_acta()['id']
        archivo = SimpleUploadedFile('f.pdf', b'x', content_type='application/pdf')
        doc_id = self.client.post(f'{API}/actas/{acta_id}/adjuntar/',
                                  {'archivo': archivo},
                                  format='multipart').json()['id']
        self.client.force_authenticate(user=None)
        r = self.client.get(f'/api/v1/documentos/{doc_id}/descargar/')
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED,
                                      status.HTTP_403_FORBIDDEN))

    def test_el_acta_lista_sus_documentos(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        self.client.get(f'{API}/actas/{acta_id}/pdf/')
        archivo = SimpleUploadedFile('firmada.pdf', b'%PDF firmada',
                                     content_type='application/pdf')
        self.client.post(f'{API}/actas/{acta_id}/adjuntar/',
                         {'archivo': archivo}, format='multipart')
        d = self.client.get(f'{API}/actas/{acta_id}/documentos/').json()
        self.assertEqual([x['tipo_documento'] for x in d],
                         ['ACTA_GENERADA', 'ACTA_ESCANEADA'])


class SinClaveDeCifradoTests(MaterializacionTests):
    """Qué pasa cuando falta DOCUMENTOS_CLAVE en la configuración."""

    def test_adjuntar_explica_que_falta_la_clave(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        acta_id = self.crear_acta()['id']
        archivo = SimpleUploadedFile('f.pdf', b'%PDF', content_type='application/pdf')
        with self.settings(DOCUMENTOS_CLAVE=''):
            r = self.client.post(f'{API}/actas/{acta_id}/adjuntar/',
                                 {'archivo': archivo}, format='multipart')
        # Un 500 opaco manda a revisar el archivo, no la configuración.
        self.assertEqual(r.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('DOCUMENTOS_CLAVE', r.json()['error'])

    def test_el_acta_se_emite_igual_aunque_no_se_pueda_archivar(self):
        from apps.documentos.models import DocumentoAdjunto
        acta_id = self.crear_acta()['id']
        self.aprobar(acta_id)
        with self.settings(DOCUMENTOS_CLAVE=''):
            r = self.client.get(f'{API}/actas/{acta_id}/pdf/')
        # Quedarse sin copia es un problema de configuración, no motivo para
        # no poder imprimir el acta.
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertEqual(DocumentoAdjunto.objects.count(), 0)


class VisibilidadEnGastosTests(MaterializacionTests):
    """Lo adjuntado por un acta tiene que verse en el presupuesto de gastos."""

    GASTOS = '/api/v2/sis-poa/budget/presupuesto-gastos/?gestion=2027'

    def actividades(self):
        d = self.client.get(self.GASTOS).json()
        return [a for p in d['programas'] for s in p['subprogramas']
                for a in s['actividades']]

    def test_la_fila_declara_cuanto_vino_de_priorizacion(self):
        self.validar(self.crear_acta()['id'])
        con = [a for a in self.actividades() if a['priorizaciones']]
        self.assertEqual(len(con), 1)
        self.assertEqual(con[0]['categoria'], '180 08620281200000 000')
        self.assertEqual(con[0]['monto_priorizado'], 220000.0)

    def test_dice_que_acta_lo_aporto(self):
        self.validar(self.crear_acta()['id'])
        aporte = [a for a in self.actividades() if a['priorizaciones']][0]
        detalle = aporte['priorizaciones'][0]
        self.assertEqual(detalle['otb'], 'OTB SAN JOSE')
        self.assertEqual(detalle['distrito'], 'DISTRITO 2')
        self.assertEqual(detalle['par'], '41/113')
        self.assertEqual(detalle['estado_acta'], 'VALIDADO')

    def test_dos_actas_sobre_la_misma_fila_se_listan_por_separado(self):
        # El monto se funde en una sola fila; el origen no puede fundirse.
        self.validar(self.crear_acta()['id'])
        self.validar(self.crear_acta(otb='OTB LOS PINOS')['id'])
        aporte = [a for a in self.actividades() if a['priorizaciones']][0]
        self.assertEqual(len(aporte['priorizaciones']), 2)
        self.assertEqual(aporte['monto_priorizado'], 440000.0)

    def test_desvalidar_saca_la_fila_del_listado_de_aportes(self):
        acta_id = self.crear_acta()['id']
        self.validar(acta_id)
        self.client.post(f'{API}/actas/{acta_id}/desvalidar/')
        self.assertEqual([a for a in self.actividades() if a['priorizaciones']], [])

    def test_una_fila_sin_priorizacion_no_muestra_nada(self):
        self.validar(self.crear_acta()['id'])
        sin = [a for a in self.actividades() if not a['priorizaciones']]
        for a in sin:
            self.assertEqual(a['monto_priorizado'], 0)


class CategoriasOfrecidasTests(MaterializacionTests):
    def test_el_formulario_ofrece_las_categorias_de_proyecto(self):
        # Si solo se ofrecen las de ACTIVIDAD, una obra termina cargada bajo
        # `000 0 001 FUNCIONAMIENTO ALCALDIA MUNICIPAL` porque es lo único que hay.
        d = self.client.get(
            f'{API}/categorias-programaticas/?gestion=2027').json()
        niveles = {c['nivel'] for c in d}
        self.assertIn('PROYECTO', niveles)
        proyecto = next(c for c in d if c['nivel'] == 'PROYECTO')
        self.assertTrue(proyecto['es_proyecto'])
        self.assertEqual(proyecto['sisin'], '08620281200000')

    def test_se_puede_pedir_un_solo_nivel(self):
        d = self.client.get(
            f'{API}/categorias-programaticas/?gestion=2027&nivel=ACTIVIDAD').json()
        self.assertEqual({c['nivel'] for c in d}, {'ACTIVIDAD'})
        self.assertEqual(d[0]['codigo'], '000 0 001')


class AltaDeCategoriaTests(MaterializacionTests):
    """Un proyecto priorizado que no está en el catálogo se da de alta."""

    def acta_con_categoria(self, codigo, nombre='CONST. PUENTE VEHICULAR D7'):
        return self.crear_acta(proyectos=[{
            'nombre': nombre, 'monto': '90000', 'sisin': '',
            'categoria_programatica': codigo,
            'fuente': str(self.ff.id), 'organismo': str(self.of.id),
        }])

    def test_crea_la_categoria_con_el_nombre_del_proyecto(self):
        acta = self.acta_con_categoria('171 13120104700000 000')
        r = self.validar(acta['id'])

        creada = CategoriaProgramaticaTecho.objects.get(
            codigo='171 13120104700000 000')
        self.assertEqual(creada.nivel, 'PROYECTO')
        # La denominación es el nombre del proyecto priorizado.
        self.assertEqual(creada.denominacion, 'CONST. PUENTE VEHICULAR D7')
        self.assertEqual(creada.gestion, self.gestion)

        volcado = r.json()['materializacion']['materializados'][0]
        self.assertTrue(volcado['categoria_creada'])
        self.assertEqual(volcado['programa'], '171')

    def test_la_cuelga_del_subprograma_de_su_programa(self):
        # El subprograma es el código de tres dígitos: `171` para
        # `171 13120104700000 000`.
        CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='171', nivel='SUBPROGRAMA',
            denominacion='INFRAESTRUCTURA URBANA Y RURAL - VIAS URBANAS')
        self.validar(self.acta_con_categoria('171 13120104700000 000')['id'])
        creada = CategoriaProgramaticaTecho.objects.get(
            codigo='171 13120104700000 000')
        self.assertEqual(creada.parent.codigo, '171')

    def test_sin_subprograma_se_crea_igual_y_queda_sin_padre(self):
        # Mejor la categoría suelta que perder el monto priorizado.
        self.validar(self.acta_con_categoria('380 13120104700000 000')['id'])
        creada = CategoriaProgramaticaTecho.objects.get(
            codigo='380 13120104700000 000')
        self.assertIsNone(creada.parent)

    def test_dos_actas_con_el_mismo_proyecto_no_duplican_la_categoria(self):
        self.validar(self.acta_con_categoria('171 13120104700000 000')['id'])
        acta = self.crear_acta(otb='OTB LOS PINOS', proyectos=[{
            'nombre': 'CONST. PUENTE VEHICULAR D7', 'monto': '10000',
            'sisin': '', 'categoria_programatica': '171 13120104700000 000',
            'fuente': str(self.ff.id), 'organismo': str(self.of.id)}])
        r = self.validar(acta['id'])
        self.assertEqual(CategoriaProgramaticaTecho.objects.filter(
            codigo='171 13120104700000 000').count(), 1)
        self.assertFalse(
            r.json()['materializacion']['materializados'][0]['categoria_creada'])

    def test_un_sisin_mas_largo_tambien_se_reconoce(self):
        # El SISIN llega con 14 o 15 dígitos según la fuente.
        self.validar(self.acta_con_categoria('171 131201047000000 000')['id'])
        self.assertTrue(CategoriaProgramaticaTecho.objects.filter(
            codigo='171 131201047000000 000', nivel='PROYECTO').exists())

    def test_una_categoria_de_funcionamiento_que_no_existe_no_se_inventa(self):
        # Esas las fija el catálogo oficial: crearlas al vuelo lo ensuciaría.
        r = self.validar(self.acta_con_categoria('380 0 001')['id'])
        self.assertFalse(
            CategoriaProgramaticaTecho.objects.filter(codigo='380 0 001').exists())
        omitidos = r.json()['materializacion']['omitidos']
        self.assertIn('no tiene forma de proyecto', omitidos[0]['motivo'])

    def test_rechaza_el_programa_que_la_directriz_prohibe(self):
        r = self.validar(self.acta_con_categoria('050 13120104700000 000')['id'])
        omitidos = r.json()['materializacion']['omitidos']
        self.assertIn('10 al 96', omitidos[0]['motivo'])
        self.assertFalse(CategoriaProgramaticaTecho.objects.filter(
            codigo='050 13120104700000 000').exists())

    def test_rechaza_el_programa_que_no_esta_en_la_directriz(self):
        r = self.validar(self.acta_con_categoria('999 13120104700000 000')['id'])
        omitidos = r.json()['materializacion']['omitidos']
        self.assertIn('no corresponde a ningún rango', omitidos[0]['motivo'])

    def test_la_categoria_creada_queda_atada_a_su_rango(self):
        self.validar(self.acta_con_categoria('171 13120104700000 000')['id'])
        creada = CategoriaProgramaticaTecho.objects.get(
            codigo='171 13120104700000 000')
        self.assertEqual(creada.rango_directriz.codigo, '170-179')

    def test_la_categoria_creada_aparece_en_el_presupuesto_de_gastos(self):
        self.validar(self.acta_con_categoria('171 13120104700000 000')['id'])
        d = self.client.get(
            '/api/v2/sis-poa/budget/presupuesto-gastos/?gestion=2027').json()
        filas = [a for p in d['programas'] for s in p['subprogramas']
                 for a in s['actividades']
                 if a['categoria'] == '171 13120104700000 000']
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]['denominacion'], 'CONST. PUENTE VEHICULAR D7')
        self.assertEqual(filas[0]['monto_priorizado'], 90000.0)


class OrdenDelPresupuestoTests(TestCase):
    """La lista sale secuencial por categoría programática.

    No hereda de MaterializacionTests a propósito: acá se cargan aperturas en
    el setUp y los tests de aquella clase asumen una base limpia.
    """

    GASTOS = '/api/v2/sis-poa/budget/presupuesto-gastos/?gestion=2027'

    # A propósito en desorden: si el árbol respeta el orden de carga en vez de
    # ordenar, se nota.
    FILAS = [
        ('300 0', 'SUBPROGRAMA', None),
        ('300 0 002', 'ACTIVIDAD', 'ACT B'),
        ('000 0', 'SUBPROGRAMA', None),
        ('171 0', 'SUBPROGRAMA', None),
        ('171 0 004', 'ACTIVIDAD', 'VIAS'),
        ('300 0 001', 'ACTIVIDAD', 'ACT A'),
        ('000 0 009', 'ACTIVIDAD', 'ALCALDIA'),
    ]

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=User.objects.create_user(email='o@t.com', password='x12345678'))
        self.gestion = GestionFiscal.objects.create(anio=2027,
                                                    estado='HABILITADA')
        subprogramas = {}
        for codigo, nivel, denominacion in self.FILAS:
            # La actividad cuelga de `<programa> <segmento>`, que es de donde
            # el árbol deduce el subprograma.
            padre = subprogramas.get(' '.join(codigo.split(' ')[:2]))
            categoria = CategoriaProgramaticaTecho.objects.create(
                gestion=self.gestion, codigo=codigo, nivel=nivel,
                denominacion=denominacion or codigo, parent=padre)
            if nivel == 'SUBPROGRAMA':
                subprogramas[codigo] = categoria
                continue
            # Solo las categorías con fila de gasto aparecen en el árbol.
            Apertura.objects.create(gestion=self.gestion, categoria=categoria,
                                    denominacion=denominacion)

    def arbol(self):
        return self.client.get(self.GASTOS).json()['programas']

    def categorias(self):
        return [a['categoria'] for p in self.arbol()
                for s in p['subprogramas'] for a in s['actividades']]

    def test_hay_varias_filas_que_ordenar(self):
        # Si el árbol trae una sola fila, "está ordenado" no prueba nada.
        self.assertEqual(len(self.categorias()), 4)

    def test_ningun_codigo_lleva_el_sufijo_sp(self):
        for p in self.arbol():
            self.assertFalse(p['codigo'].endswith('.SP'))
            for s in p['subprogramas']:
                self.assertFalse(s['codigo'].endswith('.SP'))

    def test_las_categorias_salen_en_orden_secuencial(self):
        codigos = self.categorias()
        self.assertEqual(codigos, sorted(codigos))
        self.assertLess(codigos.index('000 0 009'), codigos.index('300 0 002'))

    def test_los_subprogramas_salen_ordenados(self):
        codigos = [s['codigo'] for p in self.arbol() for s in p['subprogramas']]
        self.assertEqual(codigos, sorted(codigos))

    def test_el_orden_no_depende_de_como_se_cargaron(self):
        # `300 0` se creó antes que `171 0` y que `000 0`.
        subs = [s['codigo'] for p in self.arbol() for s in p['subprogramas']]
        self.assertLess(subs.index('000 0'), subs.index('171 0'))
        self.assertLess(subs.index('171 0'), subs.index('300 0'))


class JerarquiaDelGastoTests(TestCase):
    """El rango es el PROGRAMA y el código de tres dígitos el SUBPROGRAMA."""

    GASTOS = '/api/v2/sis-poa/budget/presupuesto-gastos/?gestion=2027'

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=User.objects.create_user(email='r@t.com', password='x12345678'))
        self.gestion = GestionFiscal.objects.create(anio=2027,
                                                    estado='HABILITADA')
        self.rango = RangoProgramaDirectriz.objects.create(
            gestion=2027, desde=170, hasta=179,
            denominacion='INFRAESTRUCTURA URBANA Y RURAL',
            finalidad_funcion='4.4.3; 4.5.1; 6.1', sector_economico='11')
        self.programa = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='170-179', nivel='PROGRAMA',
            denominacion='INFRAESTRUCTURA URBANA Y RURAL',
            rango_directriz=self.rango)

        for numero, nombre in (('170', 'INFRAESTRUCTURAS MUNICIPALES'),
                               ('171', 'VIAS URBANAS')):
            sub = CategoriaProgramaticaTecho.objects.create(
                gestion=self.gestion, codigo=numero, nivel='SUBPROGRAMA',
                denominacion=f'INFRAESTRUCTURA URBANA Y RURAL - {nombre}',
                parent=self.programa)
            act = CategoriaProgramaticaTecho.objects.create(
                gestion=self.gestion, codigo=f'{numero} 0 001',
                nivel='ACTIVIDAD', denominacion=f'OBRA {numero}', parent=sub)
            Apertura.objects.create(gestion=self.gestion, categoria=act,
                                    denominacion=f'OBRA {numero}')

    def arbol(self):
        return self.client.get(self.GASTOS).json()['programas']

    def test_el_programa_es_el_rango(self):
        programas = self.arbol()
        self.assertEqual(len(programas), 1)
        self.assertEqual(programas[0]['codigo'], '170-179')
        self.assertEqual(programas[0]['denominacion'],
                         'INFRAESTRUCTURA URBANA Y RURAL')

    def test_el_subprograma_es_el_codigo_de_tres_digitos(self):
        subprogramas = self.arbol()[0]['subprogramas']
        self.assertEqual([s['codigo'] for s in subprogramas], ['170', '171'])
        self.assertIn('VIAS URBANAS', subprogramas[1]['denominacion'])

    def test_la_actividad_cuelga_de_su_subprograma(self):
        actividades = self.arbol()[0]['subprogramas'][0]['actividades']
        self.assertEqual([a['categoria'] for a in actividades], ['170 0 001'])

    def test_el_programa_trae_lo_que_exige_la_directriz(self):
        programa = self.arbol()[0]
        self.assertEqual(programa['sector_economico'], '11')
        self.assertEqual(programa['finalidad_funcion'], '4.4.3; 4.5.1; 6.1')

    def test_los_programas_salen_en_orden_numerico_no_alfabetico(self):
        # '170-179' y '97': por número el 97 va primero, por texto no.
        rango97 = RangoProgramaDirectriz.objects.create(
            gestion=2027, desde=97, hasta=97, denominacion='NO ASIGNABLES')
        prog = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='97', nivel='PROGRAMA',
            denominacion='NO ASIGNABLES', rango_directriz=rango97)
        sub = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='097', nivel='SUBPROGRAMA',
            denominacion='X', parent=prog)
        act = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='097 0 001', nivel='ACTIVIDAD',
            denominacion='Y', parent=sub)
        Apertura.objects.create(gestion=self.gestion, categoria=act,
                                denominacion='Y')
        codigos = [p['codigo'] for p in self.arbol()]
        self.assertEqual(codigos, ['97', '170-179'])
        self.assertNotEqual(codigos, sorted(codigos))

class AltaDesdeGastosTests(TestCase):
    """Estructurar desde la pantalla de Presupuesto General de Gastos."""

    API = '/api/v2/sis-poa/budget/programmatic-categories/'

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=User.objects.create_superuser(email='a@t.com',
                                               password='x12345678'))
        self.gestion = GestionFiscal.objects.create(anio=2027,
                                                    estado='HABILITADA')
        for desde, hasta, den in [
            (170, 179, 'INFRAESTRUCTURA URBANA Y RURAL'),
            (250, 259, 'GRUPOS VULNERABLES Y DE LA MUJER'),
            (251, 251, 'PREVENCIÓN CONTRA LA VIOLENCIA HACIA LA MUJER'),
            (360, 890, 'OTROS PROGRAMAS ESPECÍFICOS'),
        ]:
            RangoProgramaDirectriz.objects.create(
                gestion=2027, desde=desde, hasta=hasta, denominacion=den,
                finalidad_funcion='4.4.3', sector_economico='11')

    def crear(self, codigo, nivel='PROGRAMA'):
        return self.client.post(self.API, {
            'gestion': str(self.gestion.id), 'codigo': codigo,
            'denominacion': 'X', 'nivel': nivel, 'estado': 'ACTIVA',
        }, format='json')

    def test_el_programa_nuevo_queda_atado_a_su_rango(self):
        r = self.crear('175')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        creado = CategoriaProgramaticaTecho.objects.get(codigo='175')
        self.assertEqual(creado.rango_directriz.codigo, '170-179')

    def test_gana_el_rango_mas_especifico(self):
        self.crear('251')
        self.assertEqual(
            CategoriaProgramaticaTecho.objects.get(codigo='251')
            .rango_directriz.codigo, '251')

    def test_rechaza_el_programa_de_la_franja_reservada(self):
        r = self.crear('050')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('10 al 96', str(r.data))
        self.assertFalse(
            CategoriaProgramaticaTecho.objects.filter(codigo='050').exists())

    def test_rechaza_el_programa_sin_rango_en_la_directriz(self):
        r = self.crear('999')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no corresponde a ningún rango', str(r.data))

    def test_rechaza_un_programa_no_numerico(self):
        r = self.crear('ABC')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('numérico', str(r.data))

    def test_el_subprograma_valida_igual_pero_no_guarda_rango(self):
        # El rango lo define la directriz en el programa; el subprograma lo
        # hereda por su cadena.
        r = self.crear('175 0', nivel='SUBPROGRAMA')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(
            CategoriaProgramaticaTecho.objects.get(codigo='175 0').rango_directriz)

    def test_un_subprograma_de_la_franja_reservada_tambien_se_rechaza(self):
        self.assertEqual(self.crear('050 0', nivel='SUBPROGRAMA').status_code,
                         status.HTTP_400_BAD_REQUEST)


class SinDirectrizCargadaTests(TestCase):
    """Sin la norma cargada no hay contra qué contrastar."""

    API = '/api/v2/sis-poa/budget/programmatic-categories/'

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=User.objects.create_superuser(email='s@t.com',
                                               password='x12345678'))
        # A propósito sin RangoProgramaDirectriz.
        self.gestion = GestionFiscal.objects.create(anio=2030,
                                                    estado='HABILITADA')

    def crear(self, codigo):
        return self.client.post(self.API, {
            'gestion': str(self.gestion.id), 'codigo': codigo,
            'denominacion': 'X', 'nivel': 'PROGRAMA', 'estado': 'ACTIVA',
        }, format='json')

    def test_no_bloquea_el_alta(self):
        # Bloquear todo haría parecer que la herramienta está rota cuando lo
        # que falta es un catálogo.
        self.assertEqual(self.crear('175').status_code,
                         status.HTTP_201_CREATED)

    def test_tampoco_aplica_la_franja_reservada(self):
        # Las reglas de la directriz se aplican juntas o no se aplica ninguna:
        # media validación rechaza por un motivo y deja pasar por el contrario.
        self.assertEqual(self.crear('050').status_code,
                         status.HTTP_201_CREATED)

    def test_la_categoria_queda_sin_rango(self):
        self.crear('175')
        self.assertIsNone(
            CategoriaProgramaticaTecho.objects.get(codigo='175').rango_directriz)

    def test_con_la_directriz_cargada_vuelve_a_validar(self):
        RangoProgramaDirectriz.objects.create(
            gestion=2030, desde=170, hasta=179, denominacion='INFRAESTRUCTURA')
        self.assertEqual(self.crear('050').status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.crear('175').status_code,
                         status.HTTP_201_CREATED)
        self.assertEqual(
            CategoriaProgramaticaTecho.objects.get(codigo='175')
            .rango_directriz.codigo, '170-179')
