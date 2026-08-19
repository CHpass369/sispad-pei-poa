"""Tests de la importación de la estructura organizacional del GAMS.

Cubre la carga del catálogo maestro (codificación oficial 2026), su
idempotencia, la jerarquía resultante y las cuatro decisiones de modelado que
el catálogo fuente dejaba ambiguas.
"""
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

TOTAL = 190


class ImportarEstructuraGAMSTest(TestCase):
    #: Los siembra organizacion.0003, pero un test transaccional previo puede
    #: haber vaciado la tabla: el caso no debe depender de eso.
    TIPOS = [('SEC', 'Secretaría', 1), ('DIR', 'Dirección', 2),
             ('UNI', 'Unidad', 3), ('ARE', 'Área', 4)]

    @classmethod
    def setUpTestData(cls):
        # Las gestiones vienen sembradas por data migration en el esquema de
        # test: get_or_create para no chocar con la existente.
        cls.gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2026,
            defaults={'anio_inicio_plurianual': 2026, 'anio_fin_plurianual': 2030},
        )
        for codigo, nombre, nivel in cls.TIPOS:
            TipoUnidad.objects.get_or_create(
                codigo=codigo, defaults={'nombre': nombre, 'nivel': nivel},
            )

    def importar(self, **kwargs):
        salida = StringIO()
        call_command('importar_estructura_gams', gestion=2026, stdout=salida, **kwargs)
        return salida.getvalue()

    def unidades(self):
        return UnidadOrganizacional.objects.filter(gestion=self.gestion)

    # --- Carga ---------------------------------------------------------------

    def test_carga_el_catalogo_completo(self):
        salida = self.importar()
        self.assertIn(f'{TOTAL} creadas', salida)
        self.assertEqual(self.unidades().count(), TOTAL)

        por_tipo = {
            t: self.unidades().filter(tipo__codigo=t).count()
            for t in ('SEC', 'DIR', 'UNI', 'ARE')
        }
        self.assertEqual(por_tipo, {'SEC': 7, 'DIR': 23, 'UNI': 63, 'ARE': 97})

    def test_el_cuarto_nivel_area_existe_en_el_catalogo_de_tipos(self):
        area = TipoUnidad.objects.get(codigo='ARE')
        self.assertEqual(area.nivel, 4)

    def test_es_idempotente(self):
        self.importar()
        salida = self.importar()
        self.assertIn('0 creadas', salida)
        self.assertIn(f'{TOTAL} actualizadas', salida)
        self.assertEqual(self.unidades().count(), TOTAL)

    def test_la_jerarquia_cierra(self):
        self.importar()
        raices = self.unidades().filter(padre__isnull=True)
        self.assertEqual(
            sorted(raices.values_list('codigo', flat=True)),
            ['EM', 'SD', 'SF', 'SI', 'SM', 'SP', 'SS'],
        )
        # Ninguna unidad cuelga de un padre de nivel igual o inferior.
        for u in self.unidades().select_related('tipo', 'padre__tipo'):
            if u.padre:
                self.assertLess(
                    u.padre.tipo.nivel, u.tipo.nivel,
                    f'{u.codigo} cuelga de {u.padre.codigo}, de nivel no superior',
                )

    def test_no_toca_otras_gestiones(self):
        otra, _ = GestionFiscal.objects.get_or_create(
            anio=2027,
            defaults={'anio_inicio_plurianual': 2026, 'anio_fin_plurianual': 2030},
        )
        UnidadOrganizacional.objects.create(
            codigo='SMFA', nombre='Secretaría preexistente',
            tipo=TipoUnidad.objects.get(codigo='SEC'), gestion=otra,
            fecha_vigencia_desde='2027-01-01',
        )
        antes = UnidadOrganizacional.objects.filter(gestion=otra).count()
        self.importar()
        self.assertEqual(
            UnidadOrganizacional.objects.filter(gestion=otra).count(), antes,
        )
        # El mismo código puede repetirse en otra gestión: la unicidad es
        # (codigo, gestion), por eso ambas codificaciones conviven.
        self.assertFalse(self.unidades().filter(codigo='SMFA').exists())

    # --- Decisiones de modelado del catálogo fuente --------------------------

    def test_la_direccion_000_cuelga_de_la_secretaria(self):
        """El código 000 no es una dirección real: no hay nivel intermedio."""
        self.importar()
        for codigo, secretaria in (
            ('EM-000-05', 'EM'), ('SF-000-39', 'SF'),
            ('SM-000-47', 'SM'), ('SD-000-55', 'SD'),
        ):
            u = self.unidades().get(codigo=codigo)
            self.assertEqual(u.padre.codigo, secretaria)
            self.assertEqual(u.tipo.codigo, 'UNI')

    def test_las_subalcaldias_rurales_quedan_a_nivel_unidad(self):
        """Intencional en el catálogo: no son hermanas de las distritales."""
        for codigo in ('EM-DAG-12', 'EM-DCH-13', 'EM-DPA-14', 'EM-DUC-15'):
            with self.subTest(codigo=codigo):
                self.importar()
                self.assertEqual(self.unidades().get(codigo=codigo).tipo.codigo, 'UNI')

    def test_saneamiento_de_bienes_respeta_el_cod_de_columna(self):
        """La planilla traía COD 2 y código -3; manda el COD."""
        self.importar()
        self.assertTrue(self.unidades().filter(codigo='SP-DGU-21-2').exists())
        self.assertFalse(self.unidades().filter(codigo='SP-DGU-21-3').exists())

    def test_caja_recaudadora_es_area_pese_a_su_codigo_corto(self):
        """SF-DRT-1 tiene un solo guion porque su unidad es la 00."""
        self.importar()
        u = self.unidades().get(codigo='SF-DRT-1')
        self.assertEqual(u.nombre, 'CAJA RECAUDADORA')
        self.assertEqual(u.tipo.codigo, 'ARE')
        self.assertEqual(u.padre.codigo, 'SF-DRT')

    def test_mantenimiento_de_establecimientos_cuelga_de_das(self):
        self.importar()
        u = self.unidades().get(codigo='SS-DAS-63-1')
        self.assertEqual(u.padre.codigo, 'SS-DAS-63')

    # --- Clase funcional y robustez -----------------------------------------

    def test_normaliza_la_clase_funcional(self):
        """El origen escribía ADMINISTRATIVO y ADMINISTRATIVA indistintamente."""
        self.importar()
        clases = set(self.unidades().values_list('clase', flat=True))
        self.assertEqual(clases, {'', 'SUSTANTIVA', 'ADMINISTRATIVA', 'ASESORAMIENTO'})
        self.assertEqual(
            self.unidades().get(codigo='EM-DJR-01').clase, 'ASESORAMIENTO',
        )

    def test_dry_run_no_escribe(self):
        salida = self.importar(dry_run=True)
        self.assertIn('[dry-run]', salida)
        self.assertEqual(self.unidades().count(), 0)

    def test_gestion_inexistente_falla_sin_escribir(self):
        with self.assertRaises(CommandError):
            call_command('importar_estructura_gams', gestion=2099, stdout=StringIO())
        self.assertEqual(UnidadOrganizacional.objects.count(), 0)
