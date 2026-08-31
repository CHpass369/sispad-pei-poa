"""El catálogo maestro: qué entra, qué no, y qué no se pisa al importar."""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.priorizacion.catalogo_sigep import (Categoria, distrito_de, es_obra,
                                              leer_ejecucion, parsear_categoria)
from apps.priorizacion.models import OrigenProyecto, ProyectoCatalogo


class HojaFalsa:
    """Lo mínimo de la interfaz de xlrd que usan los lectores."""

    def __init__(self, filas, ancho=21):
        self.nrows = len(filas)
        self.ncols = ancho
        self._filas = filas

    def cell_value(self, fila, columna):
        return self._filas[fila].get(columna, '')


def bloque(etiqueta, codigo, nombre):
    return {2: etiqueta, 5: codigo, 10: nombre}


def gasto(objeto, descripcion):
    return {1: objeto, 3: descripcion}


class ParseoDeCategoria(TestCase):

    def test_parte_el_codigo_en_sus_tres_segmentos(self):
        cat = parsear_categoria('171 13120123400000 000', 'CONST. EMPEDRADO')
        self.assertEqual(cat.programa, '171')
        self.assertEqual(cat.sisin, '13120123400000')
        self.assertEqual(cat.actividad, '000')
        self.assertTrue(cat.es_proyecto)

    def test_el_medio_en_cero_no_es_un_sisin(self):
        cat = parsear_categoria('160 0 008', 'ADQ. LUMINARIAS DISTRITO 1')
        self.assertEqual(cat.sisin, '')
        self.assertEqual(cat.codigo, '160 0 008')

    def test_normaliza_los_espacios_del_codigo(self):
        # El SIGEP alinea con espacios de relleno: `000 0  001`.
        self.assertEqual(parsear_categoria('000 0  001', 'X').codigo, '000 0 001')

    def test_devuelve_none_si_el_codigo_no_tiene_la_forma(self):
        for basura in ('Total', '1312', '', '  ', '1.1.7'):
            self.assertIsNone(parsear_categoria(basura, 'X'), basura)

    def test_funcionamiento_y_no_asignables_no_son_proyecto(self):
        self.assertFalse(parsear_categoria('000 0 001', 'FUNCIONAMIENTO').es_proyecto)
        self.assertFalse(parsear_categoria('099 0 002', 'PARTIDAS').es_proyecto)
        self.assertTrue(parsear_categoria('110 0 004', 'CONST.').es_proyecto)


class ClasificacionDeNombre(TestCase):

    def test_reconoce_los_verbos_de_obra(self):
        for nombre in ('CONST. SISTEMA DE AGUA', 'ADQ. LUMINARIAS',
                       'MEJ. PLAZA', 'MANTENIMIENTO Y MEJORAMIENTO DE VIAS'):
            self.assertTrue(es_obra(nombre), nombre)

    def test_gestion_y_transferencias_no_son_obra(self):
        for nombre in ('Renta Dignidad', 'UNIDAD CEMENTERIO MUNICIPAL',
                       'FORTALECIMIENTO SUB ALCALDIA DISTRITO 6',
                       'TRANSFERENCIA DE RECURSOS F.D.I.'):
            self.assertFalse(es_obra(nombre), nombre)

    def test_el_distrito_sale_del_nombre_no_del_parentesis(self):
        self.assertEqual(
            distrito_de('ADQ. LUMINARIAS DISTRITO 4 (OTB ESMERALDA NORTE)'), '4')
        self.assertEqual(
            distrito_de('CONST. AGUA DISTRITO LAVA LAVA (PUEBLITO)'), 'LAVA LAVA')
        self.assertEqual(distrito_de('REPOSICION POSTES Y BRAZOS'), '')


class LecturaJerarquica(TestCase):

    def hoja(self):
        return HojaFalsa([
            {},
            {1: 'Objeto', 3: 'Descripcion Objeto Del Gasto'},
            bloque('Entidad', '1312', 'Gobierno Autónomo Municipal de Sacaba'),
            bloque('DA', '1', 'SECRETARIA GENERAL'),
            bloque('UE', '4', 'SECRETARIA DE INFRAESTRUCTURA Y SERVICIOS'),
            bloque('Cat. Prg.', '160 0 008', 'ADQ. LUMINARIAS DISTRITO 1'),
            bloque('FTE', '20', 'Recursos Específicos'),
            bloque('Org.', '210', 'Recursos Específicos de los GAM'),
            gasto('1.1.7', 'Sueldos'),
            bloque('Cat. Prg.', '111 13120135300000 000',
                   'CONST. SISTEMA DE AGUA POTABLE UCUCHI'),
            gasto('Total', 'Gobierno Autónomo'),
        ])

    def test_toma_solo_los_bloques_de_categoria(self):
        cats = leer_ejecucion(self.hoja())
        self.assertEqual([c.codigo for c in cats],
                         ['160 0 008', '111 13120135300000 000'])

    def test_atribuye_la_unidad_ejecutora_vigente(self):
        cats = leer_ejecucion(self.hoja())
        self.assertEqual(cats[0].unidad_ejecutora,
                         'SECRETARIA DE INFRAESTRUCTURA Y SERVICIOS')

    def test_las_filas_de_gasto_no_se_confunden_con_categorias(self):
        # Usan las columnas 1 y 3; la etiqueta de bloque vive en la 2.
        hoja = HojaFalsa([gasto('1.1.7', 'Sueldos'), gasto('Total', 'X')])
        self.assertEqual(leer_ejecucion(hoja), [])


class ImportacionAlCatalogo(TestCase):
    """La categoría programática como condición de entrada."""

    def importar(self, **opciones):
        salida = StringIO()
        call_command('importar_catalogo_proyectos', stdout=salida, **opciones)
        return salida.getvalue()

    def test_sin_fuentes_falla_en_vez_de_no_hacer_nada(self):
        with self.assertRaises(CommandError):
            self.importar()

    def test_no_crea_filas_sin_categoria_programatica(self):
        cmd = self._comando()
        cmd._guardar({
            ('CON CAT', ''): {'nombre': 'CONST. AGUA', 'sisin': '',
                              'categoria': '110 0 004',
                              'denominacion': 'CONST. AGUA',
                              'origen': OrigenProyecto.SIGEP, 'veces': 0},
            ('SIN CAT', ''): {'nombre': 'ADQ. LUMINARIAS (OTB X)', 'sisin': '',
                              'categoria': '', 'denominacion': '',
                              'origen': OrigenProyecto.HISTORICO, 'veces': 3},
        })
        self.assertEqual(ProyectoCatalogo.objects.count(), 1)
        self.assertEqual(ProyectoCatalogo.objects.get().categoria_programatica,
                         '110 0 004')

    def test_no_pisa_las_veces_priorizadas_con_cero(self):
        """Un reporte del SIGEP no conoce las actas: si escribiera su cero,
        el buscador perdería el orden que le da valor."""
        previo = ProyectoCatalogo.objects.create(
            nombre='ADQ. LUMINARIAS DISTRITO 1', veces_priorizado=8,
            origen=OrigenProyecto.HISTORICO)
        cmd = self._comando()
        cmd._guardar({
            (previo.nombre_busqueda, ''): {
                'nombre': previo.nombre, 'sisin': '',
                'categoria': '160 0 008', 'denominacion': previo.nombre,
                'origen': OrigenProyecto.SIGEP, 'veces': 0},
        })
        previo.refresh_from_db()
        self.assertEqual(previo.veces_priorizado, 8)
        self.assertEqual(previo.categoria_programatica, '160 0 008')

    def test_solo_altas_no_toca_lo_que_ya_estaba(self):
        """El append puro: la fila incompleta se queda incompleta."""
        previo = ProyectoCatalogo.objects.create(
            nombre='CONST. SANEAMIENTO BASICO DISTRITO 4', veces_priorizado=6,
            origen=OrigenProyecto.HISTORICO)
        cmd = self._comando()
        cmd._guardar({
            (previo.nombre_busqueda, ''): {
                'nombre': previo.nombre, 'sisin': '',
                'categoria': '110 0 006', 'denominacion': previo.nombre,
                'origen': OrigenProyecto.SIGEP, 'veces': 0},
            ('CONST AGUA DISTRITO 9', ''): {
                'nombre': 'CONST. AGUA DISTRITO 9', 'sisin': '',
                'categoria': '111 0 003', 'denominacion': 'CONST. AGUA',
                'origen': OrigenProyecto.SIGEP, 'veces': 0},
        }, solo_altas=True)
        previo.refresh_from_db()
        self.assertEqual(previo.categoria_programatica, '')
        self.assertEqual(previo.origen, OrigenProyecto.HISTORICO)
        self.assertEqual(ProyectoCatalogo.objects.count(), 2)

    def test_sin_solo_altas_completa_la_fila_existente(self):
        previo = ProyectoCatalogo.objects.create(
            nombre='CONST. SANEAMIENTO BASICO DISTRITO 4', veces_priorizado=6,
            origen=OrigenProyecto.HISTORICO)
        cmd = self._comando()
        cmd._guardar({
            (previo.nombre_busqueda, ''): {
                'nombre': previo.nombre, 'sisin': '',
                'categoria': '110 0 006', 'denominacion': previo.nombre,
                'origen': OrigenProyecto.SIGEP, 'veces': 0},
        })
        previo.refresh_from_db()
        self.assertEqual(previo.categoria_programatica, '110 0 006')
        self.assertEqual(previo.veces_priorizado, 6)
        self.assertEqual(ProyectoCatalogo.objects.count(), 1)

    def test_guarda_la_denominacion_de_la_categoria(self):
        cmd = self._comando()
        cmd._guardar({
            ('CONST AGUA', ''): {'nombre': 'CONST. AGUA', 'sisin': '',
                                 'categoria': '110 0 004',
                                 'denominacion': 'CONST. AGUA POTABLE',
                                 'origen': OrigenProyecto.SIGEP, 'veces': 0},
        })
        self.assertEqual(ProyectoCatalogo.objects.get().denominacion_categoria,
                         'CONST. AGUA POTABLE')

    def _comando(self, seco=False):
        from apps.priorizacion.management.commands import (
            importar_catalogo_proyectos)
        cmd = importar_catalogo_proyectos.Command()
        cmd.seco = seco
        cmd.stdout = StringIO()
        return cmd


class EmparejadoPorDistrito(TestCase):
    """El distrito es la llave dura; la similitud solo desempata dentro de él."""

    def setUp(self):
        ProyectoCatalogo.objects.create(
            nombre='ADQ. LUMINARIAS, BRAZOS Y ACCESORIOS DISTRITO 1',
            categoria_programatica='160 0 008', origen=OrigenProyecto.SIGEP)
        ProyectoCatalogo.objects.create(
            nombre='ADQ. LUMINARIAS, BRAZOS Y ACCESORIOS DISTRITO 6',
            categoria_programatica='160 0 011', origen=OrigenProyecto.SIGEP)

    def emparejar(self, umbral=0.85):
        salida = StringIO()
        call_command('importar_catalogo_proyectos',
                     emparejar_distrito=umbral, stdout=salida)
        return salida.getvalue()

    def test_completa_dentro_del_mismo_distrito(self):
        huerfano = ProyectoCatalogo.objects.create(
            nombre='ADQ. LUMINARIAS, BRAZOS Y ACCESORIOS DISTRITO 1 (OTB VIDA NUEVA)',
            origen=OrigenProyecto.HISTORICO)
        self.emparejar()
        huerfano.refresh_from_db()
        self.assertEqual(huerfano.categoria_programatica, '160 0 008')

    def test_no_cruza_de_distrito_aunque_el_nombre_se_parezca(self):
        """Es el defecto que la similitud sola introduce: el 4 no existe como
        categoría, y el 6 se le parece lo bastante para colarse."""
        huerfano = ProyectoCatalogo.objects.create(
            nombre='ADQ. LUMINARIAS, BRAZOS Y ACCESORIOS DISTRITO 4 (OTB ESMERALDA)',
            origen=OrigenProyecto.HISTORICO)
        self.emparejar(umbral=0.70)
        huerfano.refresh_from_db()
        self.assertEqual(huerfano.categoria_programatica, '')

    def test_deja_en_paz_lo_que_no_declara_distrito(self):
        huerfano = ProyectoCatalogo.objects.create(
            nombre='REPOSICION POSTES Y BRAZOS', origen=OrigenProyecto.HISTORICO)
        salida = self.emparejar(umbral=0.50)
        huerfano.refresh_from_db()
        self.assertEqual(huerfano.categoria_programatica, '')
        self.assertIn('1 sin distrito', salida)


class PurgaDeSobrantes(TestCase):

    def test_borra_solo_lo_que_no_tiene_categoria(self):
        ProyectoCatalogo.objects.create(
            nombre='CONST. AGUA DISTRITO 1', categoria_programatica='110 0 004')
        ProyectoCatalogo.objects.create(
            nombre='ADQ. LUMINARIAS DISTRITO 1 (OTB X)', veces_priorizado=3)
        call_command('importar_catalogo_proyectos',
                     purgar_sin_categoria=True, stdout=StringIO())
        self.assertEqual([p.nombre for p in ProyectoCatalogo.objects.all()],
                         ['CONST. AGUA DISTRITO 1'])

    def test_en_seco_no_borra_nada(self):
        ProyectoCatalogo.objects.create(nombre='ADQ. LUMINARIAS (OTB X)')
        salida = StringIO()
        call_command('importar_catalogo_proyectos', purgar_sin_categoria=True,
                     dry_run=True, stdout=salida)
        self.assertEqual(ProyectoCatalogo.objects.count(), 1)
        self.assertIn('Se borrarían 1', salida.getvalue())
