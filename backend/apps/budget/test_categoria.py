"""Lectura del código de categoría programática."""
from django.test import TestCase

from apps.budget.categoria import codigo_programa, partes_categoria


class PartesCategoriaTests(TestCase):
    def test_lee_un_proyecto_de_inversion(self):
        c = partes_categoria('180 08620281200000  000')
        self.assertEqual(c.programa, '180')
        self.assertEqual(c.sisin, '08620281200000')
        self.assertEqual(c.actividad, '000')
        self.assertTrue(c.es_proyecto)
        self.assertEqual(c.subprograma, '')

    def test_lee_una_actividad_de_funcionamiento(self):
        c = partes_categoria('000 0 001')
        self.assertEqual(c.programa, '000')
        self.assertEqual(c.subprograma, '0')
        self.assertEqual(c.actividad, '001')
        self.assertFalse(c.es_proyecto)
        self.assertEqual(c.sisin, '')

    def test_el_espaciado_irregular_no_cambia_la_lectura(self):
        # El doble espacio del SIGEP es lo normal, no la excepción.
        self.assertEqual(partes_categoria('  180   08620281200000  000 '),
                         partes_categoria('180 08620281200000 000'))

    def test_un_sisin_alfanumerico_tambien_es_proyecto(self):
        # Los proyectos plurianuales llegan como TPP13120000001.
        c = partes_categoria('100 TPP13120000001 000')
        self.assertTrue(c.es_proyecto)
        self.assertEqual(c.sisin, 'TPP13120000001')

    def test_un_codigo_incompleto_se_marca_invalido_y_no_se_completa(self):
        c = partes_categoria('180 08620281200000')
        self.assertFalse(c.valida)
        self.assertEqual(c.actividad, '')
        self.assertFalse(partes_categoria('').valida)
        self.assertFalse(partes_categoria(None).valida)

    def test_el_programa_es_lo_que_agrupa_el_gasto(self):
        self.assertEqual(codigo_programa('180 08620281200000 000'), '180')
        self.assertEqual(codigo_programa('000 0 001'), '000')
        self.assertEqual(codigo_programa(''), '')
