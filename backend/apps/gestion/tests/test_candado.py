"""El candado de gestión fiscal de SIS-POA (ADR-007).

Una sola gestión habilitada, garantizada por la base; todos los módulos de
SIS-POA la absorben; escribir o leer fuera de ella no se puede.
"""
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Usuario
from apps.budget.services import cerrar_gestion, habilitar_gestion
from apps.gestion import candado
from apps.gestion.models import GestionFiscal

BUDGET_URL = '/api/v2/sis-poa/budget/'


def crear_gestion(anio, **extra):
    """La migración 0003 siembra 2026/2027: `get_or_create` evita colisiones."""
    gestion, creada = GestionFiscal.objects.get_or_create(anio=anio, defaults=extra)
    if not creada and extra:
        for campo, valor in extra.items():
            setattr(gestion, campo, valor)
        gestion.save()
    return gestion


class CandadoUnicoTests(TestCase):
    """La base es la que garantiza el candado, no la buena voluntad del código."""

    def test_dos_gestiones_activas_no_entran_en_la_base(self):
        crear_gestion(2040, estado='HABILITADA', activa=True)
        otra = GestionFiscal(anio=2041, estado='HABILITADA', activa=True)
        with self.assertRaises((IntegrityError, ValidationError)):
            with transaction.atomic():
                otra.save()

    def test_una_gestion_nueva_nace_sin_el_candado(self):
        gestion = GestionFiscal.objects.create(anio=2042)
        self.assertFalse(
            gestion.activa,
            'Una gestión recién creada no puede tomar el candado sola: si '
            'naciera activa, crear la gestión siguiente robaría el candado '
            'a la que se está formulando.',
        )


class HabilitarYCerrarTests(TestCase):
    def setUp(self):
        GestionFiscal.objects.update(activa=False)

    def test_habilitar_pone_el_candado(self):
        gestion = crear_gestion(2043, estado='preparacion', activa=False)
        habilitar_gestion(gestion, None)
        gestion.refresh_from_db()
        self.assertEqual(gestion.estado, 'HABILITADA')
        self.assertTrue(gestion.activa)
        self.assertEqual(candado.gestion_habilitada(), gestion)

    def test_no_se_puede_habilitar_con_otra_gestion_en_curso(self):
        en_curso = crear_gestion(2044, estado='HABILITADA', activa=True)
        siguiente = crear_gestion(2045, estado='preparacion', activa=False)

        with self.assertRaises(ValidationError) as caso:
            habilitar_gestion(siguiente, None)

        # El mensaje tiene que nombrar a la culpable: si solo dice "ya hay una
        # gestión habilitada", el usuario no sabe cuál cerrar.
        self.assertIn(str(en_curso.anio), ' '.join(caso.exception.messages))
        siguiente.refresh_from_db()
        self.assertFalse(siguiente.activa)

    def test_cerrar_suelta_el_candado(self):
        gestion = crear_gestion(2046, estado='HABILITADA', activa=True)
        cerrar_gestion(gestion, None)
        gestion.refresh_from_db()
        self.assertFalse(gestion.activa)
        self.assertIsNone(candado.gestion_habilitada())

    def test_cerrar_y_habilitar_la_siguiente_es_el_circuito(self):
        actual = crear_gestion(2047, estado='HABILITADA', activa=True)
        siguiente = crear_gestion(2048, estado='preparacion', activa=False)

        cerrar_gestion(actual, None)
        habilitar_gestion(siguiente, None)

        self.assertEqual(candado.gestion_habilitada().anio, 2048)
        self.assertEqual(
            GestionFiscal.objects.filter(activa=True).count(), 1,
        )


class ResolverGestionTests(TestCase):
    """Lo que absorbe cada módulo de SIS-POA."""

    def setUp(self):
        GestionFiscal.objects.update(activa=False)
        self.habilitada = crear_gestion(2049, estado='HABILITADA', activa=True)

    def _request(self, **params):
        class _Falso:
            query_params = params
        return _Falso()

    def test_sin_parametro_absorbe_la_habilitada(self):
        self.assertEqual(candado.resolver_gestion(self._request()), self.habilitada)

    def test_con_el_anio_de_la_habilitada_pasa(self):
        resuelta = candado.resolver_gestion(self._request(gestion='2049'))
        self.assertEqual(resuelta, self.habilitada)

    def test_con_el_uuid_de_la_habilitada_pasa(self):
        resuelta = candado.resolver_gestion(
            self._request(gestion=str(self.habilitada.id)),
        )
        self.assertEqual(resuelta, self.habilitada)

    def test_otra_gestion_se_rechaza(self):
        crear_gestion(2026)
        with self.assertRaises(candado.FueraDeGestionHabilitada):
            candado.resolver_gestion(self._request(gestion='2026'))

    def test_sin_gestion_habilitada_se_rechaza_con_su_propio_codigo(self):
        GestionFiscal.objects.update(activa=False)
        with self.assertRaises(candado.FueraDeGestionHabilitada) as caso:
            candado.resolver_gestion(self._request())
        self.assertEqual(caso.exception.codigo, candado.CODIGO_SIN_GESTION)


class GestionActivaApiTests(TestCase):
    """El endpoint del que cuelga todo el frontend."""

    def setUp(self):
        self.usuario = Usuario.objects.create_superuser(
            email='candado@test.gob', password='test2026',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
        self.url = BUDGET_URL + 'fiscal-years/activa/'
        GestionFiscal.objects.update(activa=False)

    def test_devuelve_la_gestion_habilitada(self):
        gestion = crear_gestion(2050, estado='HABILITADA', activa=True)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data['habilitada'])
        self.assertEqual(resp.data['gestion']['anio'], gestion.anio)

    def test_sin_gestion_habilitada_responde_200_con_el_sobre_vacio(self):
        # Un 204 sin cuerpo obligaría a cada consumidor a distinguir
        # "no hay gestión" de "falló la llamada".
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertFalse(resp.data['habilitada'])
        self.assertIsNone(resp.data['gestion'])


class PuertaTraseraV1Tests(TestCase):
    """`/api/v1/gestiones/` dejaba mover el estado sin permiso ni auditoría."""

    def setUp(self):
        self.gestion = crear_gestion(2051, estado='preparacion', activa=False)
        self.raso = Usuario.objects.create_user(
            email='raso@test.gob', password='test2026',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.raso)
        self.url = f'/api/v1/gestiones/{self.gestion.id}/'

    def test_un_usuario_sin_capacidad_no_puede_editar_la_gestion(self):
        resp = self.client.patch(self.url, {'estado': 'abierta'}, format='json')
        self.assertEqual(resp.status_code, 403, resp.data)
        self.gestion.refresh_from_db()
        self.assertEqual(self.gestion.estado, 'preparacion')

    def test_el_estado_es_de_solo_lectura_aun_con_capacidad(self):
        admin = Usuario.objects.create_superuser(
            email='admin-v1@test.gob', password='test2026',
        )
        self.client.force_authenticate(user=admin)

        resp = self.client.patch(
            self.url, {'estado': 'abierta', 'activa': True}, format='json',
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        self.gestion.refresh_from_db()
        # Habilitar es un acto de gobierno: pasa por `habilitar_gestion`, que
        # valida la transición y deja rastro en la auditoría.
        self.assertEqual(self.gestion.estado, 'preparacion')
        self.assertFalse(self.gestion.activa)
