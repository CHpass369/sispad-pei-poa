"""Lo aprobado en un acta cae en la fila de gasto que le corresponde."""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Rol
from apps.budget.models import (
    Apertura, AperturaFuente, CategoriaProgramaticaTecho, RecursoTecho,
    TechoDirectivo,
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
        self.distrito = Distrito.objects.create(codigo='D2', nombre='DISTRITO 2')
        PlantillaActa.objects.create(nombre='Acta', titulo='ACTA',
                                     encabezado='X', firmas=[])

        catalogo = dict(gestion=self.gestion, fecha_vigencia_desde=date(2027, 1, 1))
        self.ff = FuenteFinanciamiento.objects.create(
            codigo='41', denominacion='Transferencias T.G.N.', **catalogo)
        self.of = OrganismoFinanciador.objects.create(
            codigo='113', denominacion='TGN - Coparticipación', **catalogo)

        # Categoría de proyecto: programa 180, SISIN, actividad 000.
        self.categoria = CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='180 08620281200000 000',
            nivel='ACTIVIDAD', denominacion='IMPLEM. PAVIMENTO FLEXIBLE')

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

    def test_una_categoria_que_no_esta_en_el_catalogo_se_informa(self):
        acta = self.crear_acta(proyectos=[{
            'nombre': 'X', 'monto': '5000', 'sisin': '',
            'categoria_programatica': '999 12345678901234 000',
            'fuente': str(self.ff.id), 'organismo': str(self.of.id),
        }])
        omitidos = self.validar(acta['id']).json()['materializacion']['omitidos']
        self.assertIn('no está en el catálogo maestro', omitidos[0]['motivo'])
        self.assertEqual(Apertura.objects.count(), 0)

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
