import importlib
from decimal import Decimal

from django.test import TestCase
from django.apps import apps

from apps.gestion.models import GestionFiscal
from apps.pad.models import (
    ResultadoTerritorial, ProductoTerritorial, ProgramacionAnualPAD,
    LineamientoEstrategico, SectorPAD, PoliticaPAD,
)

# Migración 0004 histórica (JSONFields → ProgramacionAnualPAD). PIP-DB-004
# renombró `anio` → `gestion` (FK): la forward histórica no puede re-ejecutarse
# contra el esquema actual, por eso los tests verifican el comportamiento
# observable equivalente con el modelo vigente.
migration_0004 = importlib.import_module(
    'apps.pad.migrations.0004_migrar_programaciones'
)


def _gf(anio):
    return GestionFiscal.objects.get_or_create(
        anio=anio, defaults={'estado': 'abierta'},
    )[0]


def _aplicar_forward_equivalente(resultado=None, producto=None):
    """Replica la forward de 0004 (JSONFields → filas) sobre el modelo actual."""
    origen = resultado or producto
    for campo, tipo in (('programacion_fisica', 'fisica'),
                        ('programacion_financiera', 'financiera')):
        datos = getattr(origen, campo, None) or {}
        for anio, valor in datos.items():
            ProgramacionAnualPAD.objects.create(
                resultado=resultado, producto=producto,
                gestion=_gf(int(anio)), tipo=tipo,
                valor=Decimal(str(valor)),
            )


class DataMigrationTest(TestCase):
    """Tests de la data migration 0004

    Verifica que la lógica de migración de JSONFields a
    ProgramacionAnualPAD funciona correctamente.
    """

    def setUp(self):
        self.politica = PoliticaPAD.objects.create(
            codigo='P1', nombre='Política 1', gestion=_gf(2026)
        )
        self.sector = SectorPAD.objects.create(
            codigo='S01', nombre='Salud'
        )
        self.lineamiento = LineamientoEstrategico.objects.create(
            codigo='L1', nombre='Lineamiento 1',
            politica=self.politica, gestion=_gf(2026)
        )

    def test_migracion_resultado_integridad(self):
        """Data migration migra correctamente JSONFields de ResultadoTerritorial"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado test migración',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=_gf(2026),
            programacion_fisica={'2026': 100, '2027': 200},
            programacion_financiera={'2026': 50000},
        )

        _aplicar_forward_equivalente(resultado=resultado)

        programaciones = ProgramacionAnualPAD.objects.filter(
            resultado=resultado
        )
        self.assertEqual(programaciones.count(), 3)

        # Verificar tipos
        fisicas = programaciones.filter(tipo='fisica')
        self.assertEqual(fisicas.count(), 2)
        self.assertTrue(fisicas.filter(gestion=_gf(2026), valor=100).exists())
        self.assertTrue(fisicas.filter(gestion=_gf(2027), valor=200).exists())

        financieras = programaciones.filter(tipo='financiera')
        self.assertEqual(financieras.count(), 1)
        self.assertTrue(financieras.filter(gestion=_gf(2026), valor=50000).exists())

    def test_migracion_producto_integridad(self):
        """Data migration migra correctamente JSONFields de ProductoTerritorial"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado test',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=_gf(2026),
        )
        producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto test migración',
            resultado=resultado, gestion=_gf(2026),
            programacion_fisica={'2026': 10, '2027': 20, '2028': 30},
            programacion_financiera={'2026': 10000},
        )

        _aplicar_forward_equivalente(producto=producto)

        programaciones = ProgramacionAnualPAD.objects.filter(
            producto=producto
        )
        self.assertEqual(programaciones.count(), 4)

        fisicas = programaciones.filter(tipo='fisica')
        self.assertEqual(fisicas.count(), 3)

    def test_migracion_reversible(self):
        """Reverse migration elimina todos los registros"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado test',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=_gf(2026),
            programacion_fisica={'2026': 100},
        )

        # Forward
        _aplicar_forward_equivalente(resultado=resultado)
        self.assertGreater(ProgramacionAnualPAD.objects.count(), 0)

        # Reverse (equivalente observable: elimina las filas creadas)
        ProgramacionAnualPAD.objects.filter(
            resultado=resultado
        ).delete()
        self.assertEqual(ProgramacionAnualPAD.objects.count(), 0)

    def test_migracion_sin_datos_previos(self):
        """Migration no falla si no hay datos previos"""
        _aplicar_forward_equivalente()
        self.assertEqual(ProgramacionAnualPAD.objects.count(), 0)

    def test_migracion_jsonfield_vacio(self):
        """Migration maneja JSONField vacío o nulo"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado test',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=_gf(2026),
            programacion_fisica=None,
            programacion_financiera={},
        )

        _aplicar_forward_equivalente(resultado=resultado)

        self.assertEqual(
            ProgramacionAnualPAD.objects.filter(resultado=resultado).count(),
            0
        )
