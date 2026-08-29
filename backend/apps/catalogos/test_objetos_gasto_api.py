"""El desplegable de partidas de gasto del POAU se apoya en este endpoint.

El clasificador tiene ~505 objetos del gasto por gestión y la API pagina de a
25: sin `?search=` el combo box de `/poau_recursos` solo podría ofrecer las
primeras 25 filas. `?imputable=true` deja partidas y detalles —los niveles
contra los que se imputa— y la búsqueda baja por el árbol, para que un grupo o
un subgrupo sirvan de punto de partida sin ser elegibles.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalogos.models import ObjetoGasto
from apps.gestion.models import GestionFiscal

User = get_user_model()
API = '/api/v1/objetos-gasto/'


class ObjetoGastoFiltrosTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=User.objects.create_user(email='t@test.com', password='x12345678'))
        self.gestion = GestionFiscal.objects.update_or_create(
            anio=2027, defaults={'estado': 'HABILITADA', 'activa': True},
        )[0]
        self.otra = GestionFiscal.objects.update_or_create(
            anio=2026, defaults={'estado': 'CERRADA', 'activa': False},
        )[0]

        # El árbol real: 25200 tiene detalles colgados y 25800 no. Ese es el
        # caso que rompía el desplegable.
        grupo = self.crear('20000', 'SERVICIOS NO PERSONALES', 'grupo',
                           self.gestion)
        subgrupo = self.crear('25000', 'Servicios Profesionales', 'subgrupo',
                              self.gestion, padre=grupo)
        partida = self.crear('25200', 'Estudios e Investigaciones', 'partida',
                             self.gestion, padre=subgrupo)
        self.crear('25220', 'Consultores Individuales de Línea', 'detalle',
                   self.gestion, padre=partida)
        self.crear('25230', 'Auditorías Externas', 'detalle', self.gestion,
                   padre=partida)
        # Partida sin detalles: es hoja y también se imputa.
        self.crear('25800', 'Consultoría por Producto', 'partida',
                   self.gestion, padre=subgrupo)
        self.crear('31100', 'Alimentos para Personas', 'partida',
                   self.gestion)
        # La misma partida de otra gestión: el clasificador se versiona por año
        # y el catálogo guarda las dos.
        self.crear('25200', 'Estudios e Investigaciones', 'partida', self.otra)

    def crear(self, codigo, denominacion, nivel, gestion, padre=None):
        # `save()` corre `full_clean`: sin la fecha de vigencia el catálogo no
        # deja dar de alta la fila.
        return ObjetoGasto.objects.create(
            codigo=codigo, denominacion=denominacion, nivel=nivel,
            gestion=gestion, padre=padre,
            fecha_vigencia_desde=date(gestion.anio, 1, 1))

    def codigos(self, consulta=''):
        r = self.client.get(f'{API}{consulta}')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        return [o['codigo'] for o in r.json()['results']]

    def test_filtra_por_nivel_para_no_ofrecer_encabezados(self):
        # Contra un grupo o un subgrupo no se imputa gasto: no pueden aparecer
        # en el desplegable de «Cod. partida de gastos».
        codigos = self.codigos('?gestion=2027&nivel=partida')
        self.assertEqual(sorted(codigos), ['25200', '25800', '31100'])
        self.assertNotIn('20000', codigos)
        self.assertNotIn('25000', codigos)

    # --- Qué se puede elegir -----------------------------------------------

    def test_imputable_ofrece_partidas_y_detalles(self):
        # Los dos niveles contra los que imputa el GAM Sacaba.
        codigos = sorted(self.codigos('?gestion=2027&imputable=true'))
        self.assertEqual(codigos, ['25200', '25220', '25230', '25800', '31100'])

    def test_una_partida_con_detalles_igual_se_elige(self):
        # Se probó dejando solo las hojas del árbol y eso sacaba a `25200`,
        # que sí se usa. Tener detalles colgados no la vuelve inelegible.
        self.assertIn('25200', self.codigos('?gestion=2027&imputable=true'))

    def test_el_detalle_tambien_se_elige(self):
        codigos = self.codigos('?gestion=2027&imputable=true')
        self.assertIn('25220', codigos)
        self.assertIn('25230', codigos)

    def test_imputable_deja_afuera_los_encabezados(self):
        # `grupo` y `subgrupo` son rótulos del clasificador: contra ellos no
        # se imputa, aunque sí se pueden teclear para llegar a lo que cuelga.
        codigos = self.codigos('?gestion=2027&imputable=true')
        self.assertNotIn('20000', codigos)
        self.assertNotIn('25000', codigos)

    def test_imputable_se_combina_con_la_busqueda(self):
        self.assertEqual(sorted(self.codigos('?gestion=2027&imputable=true&search=252')),
                         ['25200', '25220', '25230'])

    def test_sin_el_filtro_el_catalogo_sigue_completo(self):
        # Es opcional: quien administra el catálogo ve todo.
        self.assertEqual(len(self.codigos('?gestion=2027')), 7)

    # --- Buscar desde un nivel alto ----------------------------------------

    def test_buscar_el_subgrupo_trae_lo_que_cuelga_de_el(self):
        # Antes tecleando `25000` aparecía una sola fila —el subgrupo— y con
        # `hoja=true` ninguna, porque tiene hijos. No había forma de llegar a
        # sus partidas partiendo del subgrupo.
        codigos = sorted(self.codigos('?gestion=2027&search=25000'))
        self.assertEqual(codigos, ['25000', '25200', '25220', '25230', '25800'])

    def test_buscar_el_subgrupo_por_su_nombre_tambien_baja(self):
        codigos = sorted(self.codigos('?gestion=2027&search=Servicios Profesionales'))
        self.assertIn('25220', codigos)
        self.assertIn('25800', codigos)

    def test_desde_el_subgrupo_hasta_lo_imputable(self):
        # El caso de la pantalla: se teclea el subgrupo y se elige entre lo que
        # cuelga. El subgrupo mismo queda afuera de lo elegible.
        codigos = sorted(self.codigos('?gestion=2027&search=25000&imputable=true'))
        self.assertEqual(codigos, ['25200', '25220', '25230', '25800'])

    def test_buscar_el_grupo_baja_hasta_el_fondo(self):
        # Tres niveles de distancia: grupo → subgrupo → partida → detalle.
        codigos = self.codigos('?gestion=2027&search=20000&imputable=true')
        self.assertIn('25220', codigos)
        self.assertIn('25200', codigos)

    def test_la_busqueda_no_sube_a_los_padres(self):
        # Baja, no sube: buscar el detalle no arrastra a su partida.
        codigos = self.codigos('?gestion=2027&search=25220')
        self.assertEqual(codigos, ['25220'])

    def test_busca_por_codigo_y_por_denominacion(self):
        # Son las dos caras del mismo combo: se teclea el código o el texto.
        # Buscar `25200` trae también sus detalles: la búsqueda baja por el
        # árbol, que es lo que permite partir de un nivel alto.
        self.assertEqual(sorted(self.codigos('?gestion=2027&search=25200')),
                         ['25200', '25220', '25230'])
        self.assertEqual(self.codigos('?gestion=2027&search=Consultoría'), ['25800'])

    def test_la_gestion_separa_las_versiones_del_clasificador(self):
        # Sin el filtro por año la misma partida sale dos veces y el usuario
        # elige a ciegas entre dos filas idénticas. Se cuenta cuántas veces
        # aparece `25200`, no el largo: la búsqueda arrastra sus detalles.
        de_2027 = self.codigos('?gestion=2027&search=25200')
        self.assertEqual(de_2027.count('25200'), 1)
        self.assertEqual(self.codigos('?search=25200').count('25200'), 2)

    def test_los_tres_filtros_se_combinan(self):
        codigos = self.codigos('?gestion=2027&nivel=partida&activo=true&search=252')
        self.assertEqual(codigos, ['25200'])

    def test_buscar_250_encuentra_al_subgrupo_y_baja_por_su_familia(self):
        # `250` no está dentro de `25200`: la coincidencia es con el subgrupo
        # `25000`. Antes eso devolvía una fila sola y ahora arrastra su rama.
        codigos = sorted(self.codigos('?gestion=2027&search=250'))
        self.assertEqual(codigos, ['25000', '25200', '25220', '25230', '25800'])
