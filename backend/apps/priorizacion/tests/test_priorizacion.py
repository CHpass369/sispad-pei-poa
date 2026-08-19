"""Módulo Priorización POA: buscador, acta oficial y circuito de revisión."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Rol
from apps.priorizacion.models import (
    ActaPriorizacion, PlantillaActa, ProyectoCatalogo, ProyectoPriorizado,
    normalizar,
)
from apps.priorizacion.views import anio_en_letras
from apps.territorio.models import Distrito

User = get_user_model()
API = '/api/v1/priorizacion'

PLANTILLA = {
    'titulo': 'ACTA DE PRIORIZACIÓN DE PROYECTOS Y ACTIVIDADES',
    'subtitulo': 'POA {gestion}',
    'encabezado': ('El Sr. {presidente} presidente de la {otb} del {distrito}, '
                   'en fecha {dia} de {mes} del año {anio_letras}, realizo la '
                   'priorización del proyecto para el POA {gestion}, mismo se '
                   'detalla a continuación:'),
    'nota': 'Nota:  Se aclara que, una vez priorizado el proyecto, no se podrá '
            'realizar ninguna modificación ni cambio de proyecto.',
    'cierre': 'En constancia de conformidad firman al pie del presente '
              'documento los siguientes:',
    'firmas': [{'rol': 'Presidente de la OTB', 'campo': 'presidente'},
               {'rol': 'Responsable del registro', 'campo': 'responsable'}],
}


class NormalizacionTests(TestCase):
    def test_ignora_tildes_y_puntuacion(self):
        # "ADQ." y "ADQ" tienen que encontrar lo mismo.
        self.assertEqual(normalizar('ADQ. LUMINARIAS, BRAZOS'),
                         'ADQ LUMINARIAS BRAZOS')
        self.assertEqual(normalizar('Construcción'), 'CONSTRUCCION')
        self.assertEqual(normalizar('  doble   espacio '), 'DOBLE ESPACIO')
        self.assertEqual(normalizar(None), '')


class AnioEnLetrasTests(TestCase):
    def test_escribe_el_anio_como_el_acta(self):
        self.assertEqual(anio_en_letras(2025), 'dos mil veinticinco')
        self.assertEqual(anio_en_letras(2026), 'dos mil veintiséis')
        self.assertEqual(anio_en_letras(2031), 'dos mil treinta y uno')
        self.assertEqual(anio_en_letras(2040), 'dos mil cuarenta')
        self.assertEqual(anio_en_letras(2042), 'dos mil cuarenta y dos')
        self.assertEqual(anio_en_letras(2000), 'dos mil')


class BuscadorProyectosTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=User.objects.create_user(email='t@test.com', password='x12345678'))
        for nombre, sisin, cat, veces in [
            ('ADQ. LUMINARIAS, BRAZOS Y ACCESORIOS DISTRITO 4', '', '', 6),
            ('ADQ. LUMINARIAS, BRAZOS Y ACCESORIOS DISTRITO 1', '', '', 8),
            ('PAVIMENTO FLEXIBLE DISTRITO 4', '', '', 2),
            ('CONST. SISTEMA DE MICRORIEGO', '02874735200000',
             '100 02874735200000 000', 0),
        ]:
            ProyectoCatalogo.objects.create(
                nombre=nombre, sisin=sisin, categoria_programatica=cat,
                veces_priorizado=veces)

    def buscar(self, q, extra=''):
        return self.client.get(f'{API}/catalogo-proyectos/?q={q}{extra}').json()

    def test_cada_palabra_acota_mas(self):
        self.assertEqual(self.buscar('lumin')['total'], 2)
        self.assertEqual(self.buscar('lumin distrito 4')['total'], 1)
        self.assertEqual(self.buscar('distrito 4')['total'], 2)

    def test_no_importan_tildes_ni_puntuacion_ni_mayusculas(self):
        self.assertEqual(self.buscar('adq.')['total'], 2)
        self.assertEqual(self.buscar('ADQ')['total'], 2)

    def test_ordena_por_lo_mas_priorizado(self):
        primero = self.buscar('lumin')['resultados'][0]
        self.assertEqual(primero['veces_priorizado'], 8)

    def test_filtra_los_que_tienen_sisin(self):
        d = self.buscar('const', '&con_sisin=1')
        self.assertEqual(d['total'], 1)
        self.assertEqual(d['resultados'][0]['categoria_programatica'],
                         '100 02874735200000 000')

    def test_una_palabra_que_no_esta_no_devuelve_nada(self):
        self.assertEqual(self.buscar('helipuerto')['total'], 0)


class ActaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tecnico = User.objects.create_user(email='t@test.com', password='x12345678')
        self.jefatura = User.objects.create_user(email='j@test.com', password='x12345678')
        rol, _ = Rol.objects.get_or_create(codigo='jefe_poa',
                                           defaults={'nombre': 'Jefatura POA'})
        self.jefatura.roles.add(rol)
        self.client.force_authenticate(user=self.tecnico)

        self.distrito = Distrito.objects.create(codigo='D2', nombre='DISTRITO 2')
        PlantillaActa.objects.create(nombre='Acta', **PLANTILLA)

    def crear_acta(self, **extra):
        datos = {
            'gestion': 2027, 'distrito': str(self.distrito.id),
            'otb': 'OTB SAN JOSE DE KORIPILA',
            'presidente': 'LIZETTE SHIRLEY CUBA ALDUNATE',
            'responsable_registro': 'LILIANA AYALA',
            'fecha': '2026-09-03',
            'proyectos': [
                {'nombre': 'CONST. PAVIMENTO ZONA SUDOESTE', 'monto': '220000',
                 'sisin': '', 'categoria_programatica': '170 0 001'},
                {'nombre': 'ADQ. LUMINARIAS', 'monto': '10000',
                 'sisin': '', 'categoria_programatica': ''},
            ],
        }
        datos.update(extra)
        return self.client.post(f'{API}/actas/', datos, format='json')

    # --- Registro ----------------------------------------------------------

    def test_la_gestion_arranca_sin_actas(self):
        self.assertEqual(
            self.client.get(f'{API}/actas/?gestion=2027').json()['count'], 0)

    def test_registra_el_acta_con_sus_proyectos_numerados(self):
        r = self.crear_acta()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        acta = ActaPriorizacion.objects.get()
        self.assertEqual([p.orden for p in acta.proyectos.all()], [1, 2])
        self.assertEqual(float(acta.monto_total), 230000.0)

    def test_una_otb_no_prioriza_dos_veces_en_la_misma_gestion(self):
        self.crear_acta()
        self.assertEqual(self.crear_acta().status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_la_misma_otb_puede_priorizar_en_otra_gestion(self):
        self.crear_acta()
        self.assertEqual(self.crear_acta(gestion=2028).status_code,
                         status.HTTP_201_CREATED)

    def test_editar_reemplaza_la_lista_completa_de_proyectos(self):
        acta_id = self.crear_acta().json()['id']
        r = self.client.put(f'{API}/actas/{acta_id}/', {
            'gestion': 2027, 'distrito': str(self.distrito.id),
            'otb': 'OTB SAN JOSE DE KORIPILA', 'presidente': 'OTRO',
            'responsable_registro': '', 'fecha': '2026-09-03',
            'proyectos': [{'nombre': 'UNICO', 'monto': '500', 'sisin': '',
                           'categoria_programatica': ''}],
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(ProyectoPriorizado.objects.count(), 1)

    # --- Acta oficial ------------------------------------------------------

    def test_el_acta_reproduce_el_formato_oficial(self):
        acta_id = self.crear_acta().json()['id']
        d = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/').json()
        self.assertEqual(d['titulo'],
                         'ACTA DE PRIORIZACIÓN DE PROYECTOS Y ACTIVIDADES')
        self.assertEqual(d['subtitulo'], 'POA 2027')
        self.assertEqual(d['distrito'], 'DISTRITO 2')
        self.assertIn('El Sr. LIZETTE SHIRLEY CUBA ALDUNATE presidente de la '
                      'OTB SAN JOSE DE KORIPILA del DISTRITO 2', d['encabezado'])
        self.assertIn('en fecha 03 de septiembre del año dos mil veintiséis',
                      d['encabezado'])
        self.assertEqual(d['total'], 230000.0)
        self.assertEqual([f['nombre'] for f in d['firmas']],
                         ['LIZETTE SHIRLEY CUBA ALDUNATE', 'LILIANA AYALA'])

    def test_no_antepone_otb_al_nombre_de_la_organizacion(self):
        # Hay juntas vecinales y sindicatos que no son OTB.
        acta_id = self.crear_acta(otb='J.V. DIN LA PAZ').json()['id']
        d = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/').json()
        self.assertIn('presidente de la J.V. DIN LA PAZ', d['encabezado'])
        self.assertNotIn('de la OTB J.V.', d['encabezado'])

    def test_sin_fecha_no_se_emite(self):
        acta_id = self.crear_acta(fecha=None).json()['id']
        r = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_proyectos_no_se_emite(self):
        acta_id = self.crear_acta(proyectos=[]).json()['id']
        r = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_plantilla_lo_dice_en_vez_de_reventar(self):
        acta_id = self.crear_acta().json()['id']
        PlantillaActa.objects.all().delete()
        r = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('plantilla', r.json()['error'])

    def test_una_plantilla_de_la_gestion_le_gana_a_la_general(self):
        PlantillaActa.objects.create(nombre='2027', gestion=2027,
                                     **{**PLANTILLA, 'titulo': 'ACTA 2027'})
        acta_id = self.crear_acta().json()['id']
        d = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/').json()
        self.assertEqual(d['titulo'], 'ACTA 2027')

    def test_una_llave_suelta_en_la_plantilla_no_rompe_la_emision(self):
        # El texto lo escribe un usuario: format() explotaría con un KeyError.
        PlantillaActa.objects.all().update(nota='Presupuesto {no_existe} y {')
        acta_id = self.crear_acta().json()['id']
        r = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    # --- Circuito ----------------------------------------------------------

    def test_validar_exige_que_el_acta_este_completa(self):
        acta_id = self.crear_acta(fecha=None).json()['id']
        r = self.client.post(f'{API}/actas/{acta_id}/validar/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aprobar_es_de_la_jefatura_y_solo_sobre_lo_validado(self):
        acta_id = self.crear_acta().json()['id']
        self.client.force_authenticate(user=self.jefatura)
        self.assertEqual(
            self.client.post(f'{API}/actas/{acta_id}/aprobar/').status_code,
            status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.tecnico)
        self.client.post(f'{API}/actas/{acta_id}/validar/')
        self.assertEqual(
            self.client.post(f'{API}/actas/{acta_id}/aprobar/').status_code,
            status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.jefatura)
        r = self.client.post(f'{API}/actas/{acta_id}/aprobar/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()['estado'], 'APROBADO')

    def test_observar_exige_motivo_y_lo_guarda(self):
        acta_id = self.crear_acta().json()['id']
        self.client.force_authenticate(user=self.jefatura)
        self.assertEqual(
            self.client.post(f'{API}/actas/{acta_id}/observar/',
                             {'comentario': '  '}).status_code,
            status.HTTP_400_BAD_REQUEST)
        r = self.client.post(f'{API}/actas/{acta_id}/observar/',
                             {'comentario': 'Falta el monto del proyecto 2'})
        self.assertEqual(r.json()['observacion'], 'Falta el monto del proyecto 2')

    def test_un_acta_aprobada_no_se_elimina(self):
        acta_id = self.crear_acta().json()['id']
        self.client.post(f'{API}/actas/{acta_id}/validar/')
        self.client.force_authenticate(user=self.jefatura)
        self.client.post(f'{API}/actas/{acta_id}/aprobar/')
        self.client.force_authenticate(user=self.tecnico)
        r = self.client.delete(f'{API}/actas/{acta_id}/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ActaPriorizacion.objects.filter(id=acta_id).exists())

    # --- Matrices ----------------------------------------------------------

    def test_la_matriz_consolida_por_distrito(self):
        self.crear_acta()
        d = self.client.get(f'{API}/matrices/?gestion=2027').json()
        self.assertEqual(d['total_filas'], 2)
        self.assertEqual(d['total_monto'], 230000.0)
        self.assertEqual(len(d['resumen']), 1)
        self.assertEqual(d['resumen'][0]['actas'], 1)
        # El conteo no puede inflarse por el join con proyectos.
        self.assertEqual(d['resumen'][0]['proyectos'], 2)

    def test_la_matriz_de_una_gestion_sin_actas_viene_vacia(self):
        d = self.client.get(f'{API}/matrices/?gestion=2029').json()
        self.assertEqual(d['total_filas'], 0)
        self.assertEqual(d['resumen'], [])


class ActaPDFTests(ActaTests):
    """El PDF lo arma el servidor: la medida no puede quedar a criterio del
    diálogo de impresión del navegador."""

    def test_sale_en_oficio_exacto(self):
        import re
        acta_id = self.crear_acta().json()['id']
        r = self.client.get(f'{API}/actas/{acta_id}/pdf/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        caja = re.search(rb'/MediaBox \[([^\]]+)\]', r.content)
        ancho, alto = [float(v) for v in caja.group(1).split()[2:]]
        # 216 x 330 mm en puntos, con tolerancia de redondeo.
        self.assertAlmostEqual(ancho, 216 * 72 / 25.4, places=1)
        self.assertAlmostEqual(alto, 330 * 72 / 25.4, places=1)
        # El Legal norteamericano mediría 1008 puntos de alto.
        self.assertLess(alto, 1000)

    def test_se_descarga_con_nombre_propio(self):
        acta_id = self.crear_acta().json()['id']
        r = self.client.get(f'{API}/actas/{acta_id}/pdf/')
        self.assertIn('attachment', r['Content-Disposition'])
        self.assertIn('.pdf', r['Content-Disposition'])

    def test_la_huella_del_contenido_es_estable_y_viaja_en_la_cabecera(self):
        acta_id = self.crear_acta().json()['id']
        primera = self.client.get(f'{API}/actas/{acta_id}/pdf/')['X-Acta-Huella']
        segunda = self.client.get(f'{API}/actas/{acta_id}/pdf/')['X-Acta-Huella']
        self.assertEqual(primera, segunda)
        self.assertEqual(len(primera), 64)
        # El JSON del acta declara la misma huella que el PDF.
        d = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/').json()
        self.assertEqual(d['huella'], primera)

    def test_cambiar_un_monto_cambia_la_huella(self):
        acta_id = self.crear_acta().json()['id']
        antes = self.client.get(f'{API}/actas/{acta_id}/pdf/')['X-Acta-Huella']
        p = ProyectoPriorizado.objects.filter(acta_id=acta_id).first()
        p.monto = 999
        p.save()
        despues = self.client.get(f'{API}/actas/{acta_id}/pdf/')['X-Acta-Huella']
        self.assertNotEqual(antes, despues)

    def test_la_huella_no_depende_de_la_redaccion_de_la_plantilla(self):
        # Lo que se verifica es qué se priorizó y por cuánto, no cómo se
        # redactó el acta: cambiar la plantilla no invalida lo firmado.
        acta_id = self.crear_acta().json()['id']
        antes = self.client.get(f'{API}/actas/{acta_id}/pdf/')['X-Acta-Huella']
        PlantillaActa.objects.all().update(nota='Otra nota distinta')
        despues = self.client.get(f'{API}/actas/{acta_id}/pdf/')['X-Acta-Huella']
        self.assertEqual(antes, despues)

    def test_el_pdf_incluye_la_aclaracion_de_recursos(self):
        PlantillaActa.objects.all().update(
            aclaracion='Aclarar que las transferencias del TGN del POA {gestion}')
        acta_id = self.crear_acta().json()['id']
        d = self.client.get(f'{API}/actas/{acta_id}/acta-oficial/').json()
        self.assertIn('POA 2027', d['aclaracion'])
        self.assertEqual(
            self.client.get(f'{API}/actas/{acta_id}/pdf/').status_code,
            status.HTTP_200_OK)

    def test_sin_fecha_no_hay_pdf(self):
        acta_id = self.crear_acta(fecha=None).json()['id']
        r = self.client.get(f'{API}/actas/{acta_id}/pdf/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
