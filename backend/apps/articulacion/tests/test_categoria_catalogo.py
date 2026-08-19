"""La denominación de la categoría programática sale del catálogo maestro.

El POAU trae el código (`000 0 001`) y la denominación se resuelve contra
`CategoriaProgramaticaTecho`, replicándose desde la acción de corto plazo hacia
operaciones, actividades y tareas.
"""
from django.test import TestCase

from apps.articulacion.views_poau import (
    _codigo_categoria, catalogo_categorias,
)
from apps.budget.models import CategoriaProgramaticaTecho
from apps.gestion.models import GestionFiscal


class CatalogoCategoriasTests(TestCase):
    def setUp(self):
        self.gestion = GestionFiscal.objects.create(anio=2027, estado='HABILITADA')
        CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='000 0 001', nivel='ACTIVIDAD',
            denominacion='FUNCIONAMIENTO ALCALDIA MUNICIPAL',
        )
        CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo='160', nivel='PROGRAMA',
            denominacion='SERVICIOS DE ALUMBRADO PUBLICO',
        )

    def test_el_espaciado_irregular_no_impide_la_coincidencia(self):
        # Según de dónde se cargó, el código llega con espacios de más.
        self.assertEqual(_codigo_categoria('  000   0  001 '), '000 0 001')
        self.assertEqual(_codigo_categoria(None), '')

    def test_separa_actividad_de_programa(self):
        exacto, programa = catalogo_categorias(2027)
        self.assertEqual(exacto['000 0 001'], 'FUNCIONAMIENTO ALCALDIA MUNICIPAL')
        self.assertEqual(programa['160'], 'SERVICIOS DE ALUMBRADO PUBLICO')
        self.assertNotIn('160', exacto)

    def test_una_gestion_sin_catalogo_propio_usa_el_vigente(self):
        # El catálogo lo publica el Ministerio; una gestión nueva puede no
        # tenerlo todavía y la matriz igual tiene que mostrar algo.
        exacto, _ = catalogo_categorias(2029)
        self.assertIn('000 0 001', exacto)


class DenominacionCategoriaTests(TestCase):
    def setUp(self):
        from apps.articulacion.views_poau import MatrizPOAUViewSet
        self.vista = MatrizPOAUViewSet()
        self.exacto = {'000 0 001': 'FUNCIONAMIENTO ALCALDIA MUNICIPAL'}
        self.programa = {'160': 'SERVICIOS DE ALUMBRADO PUBLICO'}

    def resolver(self, codigo):
        return self.vista._denominacion_categoria(codigo, self.exacto, self.programa)

    def test_coincidencia_exacta(self):
        self.assertEqual(self.resolver('000 0 001'),
                         ('FUNCIONAMIENTO ALCALDIA MUNICIPAL', 'catalogo'))

    def test_sin_la_actividad_cae_al_programa_y_lo_declara(self):
        denominacion, origen = self.resolver('160 0 008')
        self.assertEqual(denominacion, 'SERVICIOS DE ALUMBRADO PUBLICO')
        # `origen` es lo que permite marcarlo como aproximación en pantalla.
        self.assertEqual(origen, 'programa')

    def test_lo_que_no_esta_en_el_catalogo_vuelve_vacio_y_no_inventado(self):
        self.assertEqual(self.resolver('131 0 010'), ('', ''))

    def test_sin_categoria_no_hay_denominacion(self):
        self.assertEqual(self.resolver(''), ('', ''))
        self.assertEqual(self.resolver(None), ('', ''))
