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
    AccionPOA, ActividadPOAU, AsignacionObjetoGasto, OperacionPOAU,
    ProductoPEI, ResultadoPEI,
)
from apps.budget.models import CategoriaProgramaticaTecho
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


class MatrizPOAUCatalogoUnidadesTests(ScopePOAUUnidadBase):
    """A-bis. GET /matriz-poau/unidades/ — el catálogo del selector, solo.

    El selector de la importación existe para elegir la unidad cuyo árbol se va
    a crear, así que tiene que ofrecer también las que todavía no tienen POAU.
    Antes el catálogo solo llegaba dentro de la matriz —miles de filas y
    megabytes—: una lectura pesada que fallara dejaba el desplegable vacío.
    """

    URL = f'{MATRIZ}unidades/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Una unidad del catálogo sin una sola AccionPOA colgando.
        cls.sin_poau = UnidadOrganizacional.objects.create(
            codigo='SCOPE-SIN-POAU', nombre='Unidad sin POAU',
            tipo=cls.propia.tipo, padre=None, gestion=cls.gestion,
            fecha_vigencia_desde=date(2027, 1, 1),
        )

    def catalogo(self, usuario):
        response = self.cliente(usuario).get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [u['codigo'] for u in response.data['unidades']]

    def test_ofrece_una_unidad_sin_arbol_todavia(self):
        self.assertIn('SCOPE-SIN-POAU', self.catalogo(self.global_))

    def test_devuelve_la_gestion_habilitada(self):
        response = self.cliente(self.global_).get(self.URL)
        self.assertEqual(response.data['gestion'], 2027)

    def test_respeta_el_alcance_organizacional(self):
        self.assertEqual(self.catalogo(self.acotado), ['SCOPE-PROPIA'])

    def test_sin_alcances_no_ofrece_nada(self):
        self.assertEqual(self.catalogo(self.sin_alcance), [])

    def test_exige_la_capacidad_poau(self):
        sin_rol = Usuario.objects.create_user(
            email='scope-cat-sin-cap@test.gob.bo', password='Clave.Scope.2027',
        )
        response = self.cliente(sin_rol).get(self.URL)
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


class MatrizPOAUPresupuestoTests(ScopePOAUUnidadBase):
    """La programación presupuestaria que va debajo de la matriz POAU.

    Es la contraparte financiera de la matriz física y comparte pantalla con
    ella, así que tiene que compartir también candado, alcance y `?unidad=`:
    dos totales en la misma pantalla que hablen de universos distintos son dos
    totales que nadie puede conciliar.
    """

    URL = f'{MATRIZ}presupuesto/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        CategoriaProgramaticaTecho.objects.create(
            gestion=cls.gestion, codigo='170 0 001', nivel='ACTIVIDAD',
            denominacion='CONSTRUCCION DE VIAS URBANAS',
        )

        # Los requerimientos cuelgan de una actividad: `actividad_id` es NOT
        # NULL, igual que exige el asistente de recursos.
        actividades = {}
        for operacion in OperacionPOAU.objects.all():
            actividades[operacion.accion_poa_id] = ActividadPOAU.objects.create(
                operacion=operacion,
                codigo_actividad=f'{operacion.codigo_operacion}-AC1',
                denominacion=f'Actividad de {operacion.codigo_operacion}',
            )

        def asignacion(accion, codigo, categoria, meses, partida='25200',
                       declarado=None):
            # `declarado` a propósito distinto de la suma mensual: si fueran
            # siempre iguales, el test del total no distinguiría cuál de los
            # dos usa el endpoint.
            return AsignacionObjetoGasto.objects.create(
                codigo_asignacion=codigo, gestion=2027, accion_poa=accion,
                operacion=actividades[accion.pk].operacion,
                actividad=actividades[accion.pk],
                categoria_programatica=categoria, da='1', ue='001',
                programa=categoria.split()[0], cod_objeto_gasto=partida,
                descripcion_objeto='Estudios e Investigaciones',
                grupo_gasto='20000', tipo_gasto='Funcionamiento',
                fuente_financiamiento='20', organismo_financiador='230',
                monto_programado=(sum(meses.values()) if declarado is None
                                  else declarado),
                monto_vigente=sum(meses.values()),
                programacion_mensual=meses,
            )

        # Declara 9 000 pero solo distribuyó 1 500: vale lo distribuido.
        asignacion(cls.accion_propia, 'ACC-PROPIA.G1', '170 0 001',
                   {'enero': 1000, 'marzo': 500}, declarado=9000)
        asignacion(cls.accion_propia, 'ACC-PROPIA.G2', '170 0 001',
                   {'julio': 2500}, partida='25800')
        # Otra categoría de la misma unidad: tiene que salir en su propio grupo.
        asignacion(cls.accion_propia, 'ACC-PROPIA.G3', '000 0 001',
                   {'diciembre': 700})
        # Y una de la unidad ajena, para que el alcance tenga qué filtrar.
        asignacion(cls.accion_ajena, 'ACC-AJENA.G1', '170 0 001',
                   {'enero': 9999})

    def presupuesto(self, usuario, query=''):
        respuesta = self.cliente(usuario).get(f'{self.URL}{query}')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return respuesta.data

    def test_agrupa_los_requerimientos_por_categoria_programatica(self):
        datos = self.presupuesto(self.global_, '?unidad=SCOPE-PROPIA')
        codigos = [c['categoria'] for c in datos['categorias']]
        self.assertEqual(codigos, ['000 0 001', '170 0 001'])
        porcategoria = {c['categoria']: c for c in datos['categorias']}
        self.assertEqual(len(porcategoria['170 0 001']['filas']), 2)
        self.assertEqual(len(porcategoria['000 0 001']['filas']), 1)

    def test_la_denominacion_la_pone_el_catalogo(self):
        # La fila guarda el código; el nombre es del maestro de categorías.
        datos = self.presupuesto(self.global_, '?unidad=SCOPE-PROPIA')
        porcategoria = {c['categoria']: c for c in datos['categorias']}
        self.assertEqual(porcategoria['170 0 001']['denominacion'],
                         'CONSTRUCCION DE VIAS URBANAS')

    def test_el_total_es_la_suma_mensual_y_no_el_monto_declarado(self):
        # `ACC-PROPIA.G1` declara 9 000 y distribuyó 1 500. Vale lo
        # distribuido: si el endpoint sumara `monto_programado`, la categoría
        # daría 11 500 en vez de 4 000.
        datos = self.presupuesto(self.global_, '?unidad=SCOPE-PROPIA')
        porcategoria = {c['categoria']: c for c in datos['categorias']}
        fila = porcategoria['170 0 001']['filas'][0]
        self.assertEqual(fila['monto_programado'], 9000.0)
        self.assertEqual(fila['total_anual'], 1500.0)
        self.assertEqual(porcategoria['170 0 001']['total'], 4000.0)
        self.assertEqual(porcategoria['000 0 001']['total'], 700.0)
        self.assertEqual(datos['total'], 4700.0)

    def test_cada_fila_trae_sus_doce_meses(self):
        datos = self.presupuesto(self.global_, '?unidad=SCOPE-PROPIA')
        fila = next(f for c in datos['categorias'] for f in c['filas']
                    if f['codigo_asignacion'] == 'ACC-PROPIA.G1')
        self.assertEqual(fila['mes_enero'], 1000.0)
        self.assertEqual(fila['mes_marzo'], 500.0)
        self.assertIsNone(fila['mes_febrero'])
        self.assertEqual(fila['total_anual'], 1500.0)
        self.assertEqual(fila['cod_objeto_gasto'], '25200')

    def test_filtrar_por_unidad_deja_afuera_a_las_demas(self):
        datos = self.presupuesto(self.global_, '?unidad=SCOPE-AJENA')
        self.assertEqual(datos['total'], 9999.0)

    def test_el_alcance_acota_igual_que_la_matriz_de_arriba(self):
        # Sin filtro explícito, el acotado ve solo lo suyo: 4700, no 14699.
        self.assertEqual(self.presupuesto(self.acotado)['total'], 4700.0)
        self.assertEqual(self.presupuesto(self.global_)['total'], 14699.0)

    def test_pedir_una_unidad_ajena_no_devuelve_su_presupuesto(self):
        datos = self.presupuesto(self.acotado, '?unidad=SCOPE-AJENA')
        self.assertEqual(datos['categorias'], [])
        self.assertEqual(datos['total'], 0)

    def test_sin_alcance_no_se_ve_nada(self):
        self.assertEqual(self.presupuesto(self.sin_alcance)['total'], 0)
