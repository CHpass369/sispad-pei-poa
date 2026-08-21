"""Reglas del Anexo VI de las Directrices de Formulación Presupuestaria."""
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.budget.directriz import (
    PROHIBIDO_DESDE, PROHIBIDO_HASTA, programa_prohibido, rango_de,
    validar_categoria,
)
from apps.budget.models import RangoProgramaDirectriz


class DirectrizTests(TestCase):
    def setUp(self):
        for desde, hasta, den, fin, sector in [
            (0, 0, 'FUNCIONAMIENTO ÓRGANO EJECUTIVO', '1.1.1', '14'),
            (170, 179, 'INFRAESTRUCTURA URBANA Y RURAL', '4.4.3', '11'),
            (250, 259, 'GRUPOS VULNERABLES Y DE LA MUJER', '10.9.1', '21; 23'),
            (251, 251, 'PREVENCIÓN CONTRA LA VIOLENCIA HACIA LA MUJER',
             '10.9.1', '23.1.5'),
            (99, 99, 'PARTIDAS NO ASIGNABLES - DEUDAS', '1.7', '17'),
        ]:
            RangoProgramaDirectriz.objects.create(
                gestion=2027, desde=desde, hasta=hasta, denominacion=den,
                finalidad_funcion=fin, sector_economico=sector)

    # --- Resolución del rango ----------------------------------------------

    def test_ubica_el_programa_en_su_rango(self):
        self.assertEqual(rango_de('171', 2027).codigo, '170-179')
        self.assertEqual(rango_de(171, 2027).sector_economico, '11')

    def test_el_programa_singularizado_le_gana_al_rango_que_lo_contiene(self):
        # La directriz saca al 251 del 250-259 para darle su propio sector.
        self.assertEqual(rango_de('251', 2027).codigo, '251')
        self.assertEqual(rango_de('251', 2027).sector_economico, '23.1.5')
        self.assertEqual(rango_de('250', 2027).codigo, '250-259')

    def test_el_programa_con_ceros_adelante_resuelve_igual(self):
        # El catálogo escribe 099 y la directriz 99.
        self.assertEqual(rango_de('099', 2027).codigo, '99')

    def test_una_gestion_sin_directriz_cargada_no_resuelve(self):
        self.assertIsNone(rango_de('171', 2028))

    def test_un_programa_no_numerico_no_resuelve(self):
        self.assertIsNone(rango_de('ABC', 2027))
        self.assertIsNone(rango_de('', 2027))

    # --- Franja prohibida ---------------------------------------------------

    def test_la_franja_reservada_es_del_10_al_96(self):
        self.assertEqual((PROHIBIDO_DESDE, PROHIBIDO_HASTA), (10, 96))
        self.assertTrue(programa_prohibido('050'))
        self.assertTrue(programa_prohibido(10))
        self.assertTrue(programa_prohibido(96))
        self.assertFalse(programa_prohibido('009'))
        self.assertFalse(programa_prohibido('097'))

    # --- Validación del código ---------------------------------------------

    def test_acepta_un_codigo_bien_formado(self):
        self.assertEqual(
            validar_categoria('171 13120104700000 000', 2027).codigo, '170-179')
        self.assertEqual(validar_categoria('000 0 001', 2027).codigo, '0')

    def test_rechaza_el_programa_de_la_franja_reservada(self):
        with self.assertRaises(ValidationError) as e:
            validar_categoria('050 0 001', 2027)
        self.assertIn('no se puede usar', e.exception.messages[0])
        self.assertIn('10 al 96', e.exception.messages[0])

    def test_rechaza_un_codigo_incompleto_y_dice_que_falta(self):
        with self.assertRaises(ValidationError) as e:
            validar_categoria('171 13120104700000', 2027)
        self.assertIn('tres segmentos', e.exception.messages[0])

    def test_rechaza_un_programa_sin_rango_en_la_directriz(self):
        with self.assertRaises(ValidationError) as e:
            validar_categoria('999 0 001', 2027)
        self.assertIn('no corresponde a ningún rango', e.exception.messages[0])

    def test_el_mensaje_dice_como_cargar_la_directriz_que_falta(self):
        with self.assertRaises(ValidationError) as e:
            validar_categoria('171 13120104700000 000', 2029)
        self.assertIn('sembrar_directriz_programas', e.exception.messages[0])


class RangoTests(TestCase):
    def test_el_codigo_se_arma_del_rango(self):
        rango = RangoProgramaDirectriz(gestion=2027, desde=170, hasta=179,
                                       denominacion='X')
        self.assertEqual(rango.codigo, '170-179')

    def test_un_rango_de_un_solo_programa_no_lleva_guion(self):
        rango = RangoProgramaDirectriz(gestion=2027, desde=99, hasta=99,
                                       denominacion='X')
        self.assertEqual(rango.codigo, '99')

    def test_contiene_es_inclusivo_en_los_dos_extremos(self):
        rango = RangoProgramaDirectriz(gestion=2027, desde=170, hasta=179,
                                       denominacion='X')
        self.assertTrue(rango.contiene(170))
        self.assertTrue(rango.contiene(179))
        self.assertFalse(rango.contiene(180))
