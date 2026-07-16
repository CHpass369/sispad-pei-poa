from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.pad.models import (
    ProgramacionAnualPAD, ResultadoTerritorial, ProductoTerritorial,
    LineamientoEstrategico, SectorPAD, PoliticaPAD,
)


class ProgramacionAnualPADModelTest(TestCase):
    """Tests del modelo ProgramacionAnualPAD"""

    def setUp(self):
        self.politica = PoliticaPAD.objects.create(
            codigo='P1', nombre='Política 1', gestion=2026
        )
        self.sector = SectorPAD.objects.create(
            codigo='S01', nombre='Salud'
        )
        self.lineamiento = LineamientoEstrategico.objects.create(
            codigo='L1', nombre='Lineamiento 1',
            politica=self.politica, gestion=2026
        )
        self.resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado 1',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=2026
        )
        self.producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026
        )

    def test_create_con_resultado(self):
        """Crear ProgramacionAnualPAD con resultado"""
        prog = ProgramacionAnualPAD.objects.create(
            resultado=self.resultado,
            anio=2026, tipo='fisica', valor=100.5000
        )
        self.assertEqual(prog.anio, 2026)
        self.assertEqual(prog.tipo, 'fisica')
        self.assertEqual(prog.valor, 100.5000)
        self.assertEqual(prog.resultado, self.resultado)
        self.assertIsNone(prog.producto)

    def test_create_con_producto(self):
        """Crear ProgramacionAnualPAD con producto"""
        prog = ProgramacionAnualPAD.objects.create(
            producto=self.producto,
            anio=2026, tipo='financiera', valor=50000.0000
        )
        self.assertEqual(prog.anio, 2026)
        self.assertEqual(prog.tipo, 'financiera')
        self.assertEqual(prog.valor, 50000.0000)
        self.assertEqual(prog.producto, self.producto)
        self.assertIsNone(prog.resultado)

    def test_unique_together(self):
        """Validar unique_together: mismo resultado+producto+anio+tipo"""
        from django.core.exceptions import ValidationError
        # Usamos ambos FKs para que Django valide unique_together
        # (con FKs nulos, la constraint no aplica por NULL != NULL en Postgres)
        ProgramacionAnualPAD.objects.create(
            resultado=self.resultado, producto=self.producto,
            anio=2026, tipo='fisica', valor=100
        )
        # La validación se dispara en full_clean() vía validate_unique()
        with self.assertRaises(ValidationError):
            ProgramacionAnualPAD.objects.create(
                resultado=self.resultado, producto=self.producto,
                anio=2026, tipo='fisica', valor=200
            )

    def test_ambos_fk_null_rechazado(self):
        """Validar que clean() rechace si resultado y producto son ambos None"""
        prog = ProgramacionAnualPAD(
            resultado=None, producto=None,
            anio=2026, tipo='fisica', valor=100
        )
        with self.assertRaises(ValidationError) as ctx:
            prog.full_clean()
        self.assertIn('Debe especificar', str(ctx.exception))

    def test_valor_negativo_rechazado(self):
        """Validar que clean() rechace valor negativo"""
        prog = ProgramacionAnualPAD(
            resultado=self.resultado,
            anio=2026, tipo='fisica', valor=-100
        )
        with self.assertRaises(ValidationError):
            prog.full_clean()

    def test_str_representation(self):
        """Verificar __str__ de ProgramacionAnualPAD"""
        prog = ProgramacionAnualPAD.objects.create(
            resultado=self.resultado,
            anio=2026, tipo='fisica', valor=100.5000
        )
        # Decimal 100.5000 se muestra como '100.5' (Python elimina ceros)
        expected = f'Resultado {self.resultado.id} - 2026 (Física): 100.5'
        self.assertEqual(str(prog), expected)

    def test_str_con_producto(self):
        """Verificar __str__ cuando es de producto"""
        prog = ProgramacionAnualPAD.objects.create(
            producto=self.producto,
            anio=2026, tipo='financiera', valor=50000
        )
        expected = f'Producto {self.producto.id} - 2026 (Financiera): 50000'
        self.assertEqual(str(prog), expected)

    def test_related_name_resultado(self):
        """Verificar related_name 'programaciones' en ResultadoTerritorial"""
        ProgramacionAnualPAD.objects.create(
            resultado=self.resultado,
            anio=2026, tipo='fisica', valor=100
        )
        ProgramacionAnualPAD.objects.create(
            resultado=self.resultado,
            anio=2027, tipo='fisica', valor=200
        )
        self.assertEqual(self.resultado.programaciones.count(), 2)

    def test_related_name_producto(self):
        """Verificar related_name 'programaciones' en ProductoTerritorial"""
        ProgramacionAnualPAD.objects.create(
            producto=self.producto,
            anio=2026, tipo='fisica', valor=100
        )
        self.assertEqual(self.producto.programaciones.count(), 1)


class ResultadoTerritorialModelTest(TestCase):
    """Tests de campos nuevos en ResultadoTerritorial"""

    def setUp(self):
        self.politica = PoliticaPAD.objects.create(
            codigo='P1', nombre='Política 1', gestion=2026
        )
        self.lineamiento = LineamientoEstrategico.objects.create(
            codigo='L1', nombre='Lineamiento 1',
            politica=self.politica, gestion=2026
        )

    def test_cod_geografico_default_vacio(self):
        """cod_geografico debe tener default vacío"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado 1',
            lineamiento=self.lineamiento, gestion=2026
        )
        self.assertEqual(resultado.cod_geografico, '')

    def test_cod_geografico_con_valor(self):
        """cod_geografico puede almacenar un código"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado 1',
            lineamiento=self.lineamiento, gestion=2026,
            cod_geografico='1102'
        )
        self.assertEqual(resultado.cod_geografico, '1102')


class ProductoTerritorialModelTest(TestCase):
    """Tests de campos nuevos en ProductoTerritorial"""

    def setUp(self):
        self.politica = PoliticaPAD.objects.create(
            codigo='P1', nombre='Política 1', gestion=2026
        )
        self.lineamiento = LineamientoEstrategico.objects.create(
            codigo='L1', nombre='Lineamiento 1',
            politica=self.politica, gestion=2026
        )
        self.resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado 1',
            lineamiento=self.lineamiento, gestion=2026
        )

    def test_cuenta_con_financiamiento_default(self):
        """cuenta_con_financiamiento debe ser 'NO' por defecto"""
        producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026
        )
        self.assertEqual(producto.cuenta_con_financiamiento, 'NO')

    def test_cuenta_con_financiamiento_si(self):
        """cuenta_con_financiamiento puede ser 'SI'"""
        producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026,
            cuenta_con_financiamiento='SI'
        )
        self.assertEqual(producto.cuenta_con_financiamiento, 'SI')

    def test_presupuesto_total_pad_nulo(self):
        """presupuesto_total_pad puede ser nulo"""
        producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026
        )
        self.assertIsNone(producto.presupuesto_total_pad)

    def test_presupuesto_total_pad_con_valor(self):
        """presupuesto_total_pad puede almacenar un monto"""
        producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026,
            presupuesto_total_pad=150000.50
        )
        self.assertEqual(producto.presupuesto_total_pad, 150000.50)
