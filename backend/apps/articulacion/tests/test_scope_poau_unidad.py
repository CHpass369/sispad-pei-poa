"""Alcance organizacional de las tres pantallas POAU de una unidad.

`MatrizPOAUViewSet` (Matriz POAU) y la cadena AccionPOA → OperacionPOAU →
ActividadPOAU (POAU Físico y POAU Recursos) alimentaban las pantallas SIN
filtro territorial: cualquiera con la capacidad listaba y abría las acciones de
toda la alcaldía, y el `?unidad=` de la matriz era un parámetro libre.

Lo que estos casos fijan:

- la matriz se acota a las UO efectivas, y el catálogo `unidades` que alimenta
  el selector también (si el desplegable ofrece lo que no se puede abrir, el
  filtro es decorativo);
- pedir explícitamente una UO ajena devuelve vacío, no la matriz ajena;
- el detalle (`retrieve`) rechaza una acción fuera de alcance: adivinar un UUID
  no debe alcanzar donde el listado no llega;
- un alcance GLOBAL sigue viendo todo — el filtro solo muerde al acotado;
- sin alcances vigentes no se ve nada (fail-closed).
"""
from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import AlcanceOrganizacional, Capacidad, Rol, Usuario
from apps.articulacion.models import (
    AccionPOA, OperacionPOAU, ProductoPEI, ResultadoPEI,
)
from apps.gestion.testing import habilitar_gestion_para_tests
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

CAPS_POAU = [
    'sis_poa.poau.view', 'sis_poa.poau.create', 'sis_poa.poau.edit',
    'sis_poa.poau.submit', 'sis_poa.poau.review', 'sis_poa.poau.approve',
]
MATRIZ = '/api/v1/articulacion/matriz-poau/'


class ScopePOAUUnidadBase(TestCase):
    """Dos unidades hermanas, cada una con su propia cadena POAU."""

    @classmethod
    def setUpTestData(cls):
        cls.gestion = habilitar_gestion_para_tests(2027)
        tipo, _ = TipoUnidad.objects.get_or_create(
            codigo='SCOPE-POAU-TIPO',
            defaults={'nombre': 'Tipo scope POAU', 'nivel': 1},
        )

        def uo(codigo, nombre):
            return UnidadOrganizacional.objects.create(
                codigo=codigo, nombre=nombre, tipo=tipo, padre=None,
                gestion=cls.gestion, fecha_vigencia_desde=date(2027, 1, 1),
            )

        cls.propia = uo('SCOPE-PROPIA', 'Unidad propia')
        cls.ajena = uo('SCOPE-AJENA', 'Unidad ajena')

        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='SCP001.01', denominacion='Resultado scope POAU',
            cod_entidad='01', entidad='GAMS',
            vigencia_desde=2026, vigencia_hasta=2030,
        )
        cls.producto_pei = ProductoPEI.objects.create(
            codigo_producto='SCP001.01.01', denominacion='Producto scope POAU',
            resultado_pei=resultado_pei,
        )

        def accion(unidad, codigo):
            return AccionPOA.objects.create(
                unidad_responsable=unidad, gestion=2027,
                producto_pei=cls.producto_pei,
                codigo_accion=codigo, denominacion=f'Acción {codigo}',
            )

        cls.accion_propia = accion(cls.propia, 'ACC-PROPIA')
        cls.accion_ajena = accion(cls.ajena, 'ACC-AJENA')
        for accion_poa, codigo in (
            (cls.accion_propia, 'OP-PROPIA'), (cls.accion_ajena, 'OP-AJENA'),
        ):
            OperacionPOAU.objects.create(
                accion_poa=accion_poa, codigo_operacion=codigo,
                denominacion=f'Operación {codigo}',
            )

        def rol(codigo, capacidades):
            r, _ = Rol.objects.get_or_create(
                codigo=codigo, defaults={'nombre': codigo},
            )
            for c in capacidades:
                capacidad, _ = Capacidad.objects.get_or_create(
                    codigo=c,
                    defaults={'nombre': c, 'sistema': c.split('.')[0]},
                )
                r.capacidades.add(capacidad)
            return r

        cls.rol_poau = rol('SCOPE-ENCARGADO', CAPS_POAU)

        def usuario(email, unidad, scope_type):
            u = Usuario.objects.create_user(
                email=email, password='Clave.Scope.2027',
            )
            u.roles.add(cls.rol_poau)
            if unidad is not None:
                AlcanceOrganizacional.objects.create(
                    usuario=u, unidad=unidad, rol=cls.rol_poau,
                    scope_type=scope_type, fiscal_year=cls.gestion,
                )
            return u

        cls.acotado = usuario(
            'scope-acotado@test.gob.bo', cls.propia,
            AlcanceOrganizacional.SCOPE_SELF,
        )
        cls.global_ = usuario(
            'scope-global@test.gob.bo', cls.propia,
            AlcanceOrganizacional.SCOPE_GLOBAL,
        )
        cls.sin_alcance = usuario('scope-sin@test.gob.bo', None, None)

    def cliente(self, usuario):
        client = APIClient()
        client.force_authenticate(user=usuario)
        return client

    def matriz(self, usuario, query=''):
        response = self.cliente(usuario).get(f'{MATRIZ}{query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data


class MatrizPOAUScopeTests(ScopePOAUUnidadBase):
    """A. GET /matriz-poau/ — filas y catálogo de unidades."""

    @staticmethod
    def _codigos_de_filas(data):
        return {
            fila['unidad_codigo'] for fila in data['filas']
            if fila.get('unidad_codigo')
        }

    def test_acotado_solo_ve_su_unidad(self):
        data = self.matriz(self.acotado)
        self.assertEqual(self._codigos_de_filas(data), {'SCOPE-PROPIA'})

    def test_el_selector_solo_ofrece_lo_que_puede_abrir(self):
        data = self.matriz(self.acotado)
        self.assertEqual(
            [u['codigo'] for u in data['unidades']], ['SCOPE-PROPIA'],
        )

    def test_pedir_una_unidad_ajena_devuelve_vacio(self):
        data = self.matriz(self.acotado, '?unidad=SCOPE-AJENA')
        self.assertEqual(data['total_filas'], 0)

    def test_el_selector_no_se_vacia_al_filtrar_por_la_propia(self):
        """El catálogo sale de la gestión, no de las filas ya filtradas."""
        data = self.matriz(self.acotado, '?unidad=SCOPE-PROPIA')
        self.assertEqual(
            [u['codigo'] for u in data['unidades']], ['SCOPE-PROPIA'],
        )

    def test_alcance_global_sigue_viendo_todo(self):
        data = self.matriz(self.global_)
        self.assertEqual(
            self._codigos_de_filas(data), {'SCOPE-PROPIA', 'SCOPE-AJENA'},
        )

    def test_sin_alcances_no_ve_nada(self):
        data = self.matriz(self.sin_alcance)
        self.assertEqual(data['total_filas'], 0)
        self.assertEqual(data['unidades'], [])

    def test_exige_la_capacidad_poau(self):
        sin_rol = Usuario.objects.create_user(
            email='scope-sin-cap@test.gob.bo', password='Clave.Scope.2027',
        )
        response = self.cliente(sin_rol).get(MATRIZ)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MatrizPOAUDetalleScopeTests(ScopePOAUUnidadBase):
    """B. GET /matriz-poau/<accion>/ — el detalle también se acota."""

    def url(self, accion):
        return f'{MATRIZ}{accion.pk}/'

    def test_abre_una_accion_propia(self):
        response = self.cliente(self.acotado).get(self.url(self.accion_propia))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rechaza_una_accion_ajena(self):
        response = self.cliente(self.acotado).get(self.url(self.accion_ajena))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_alcance_global_abre_cualquiera(self):
        response = self.cliente(self.global_).get(self.url(self.accion_ajena))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CadenaPOAUScopeTests(ScopePOAUUnidadBase):
    """C. La cadena que alimenta POAU (Físico) y POAU (Recursos)."""

    ENDPOINTS = (
        '/api/v1/articulacion/acciones-poa/',
        '/api/v1/articulacion/operaciones/',
    )

    def _cantidad(self, usuario, url):
        response = self.cliente(usuario).get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cuerpo = response.data
        return cuerpo['count'] if isinstance(cuerpo, dict) else len(cuerpo)

    def test_acotado_ve_solo_lo_de_su_unidad(self):
        for url in self.ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self._cantidad(self.acotado, url), 1)

    def test_alcance_global_ve_ambas_unidades(self):
        for url in self.ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self._cantidad(self.global_, url), 2)

    def test_sin_alcances_no_ve_nada(self):
        for url in self.ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self._cantidad(self.sin_alcance, url), 0)

    def test_no_puede_crear_en_una_unidad_ajena(self):
        response = self.cliente(self.acotado).post(
            '/api/v1/articulacion/acciones-poa/',
            {
                'unidad_responsable': str(self.ajena.pk),
                'producto_pei': str(self.producto_pei.pk),
                'gestion': 2027,
                'codigo_accion': 'ACC-INTRUSA',
                'denominacion': 'Acción intrusa',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            AccionPOA.objects.filter(codigo_accion='ACC-INTRUSA').exists(),
        )
