from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models import Sum

from apps.pad.models import (
    SectorPAD, PoliticaPAD, LineamientoEstrategico,
    ResultadoTerritorial, ProductoTerritorial,
    ProgramacionAnualPAD, ArticulacionLog,
)


class PADHierarchyBaseTestCase(TestCase):
    """Base para tests de jerarquía PAD."""

    def setUp(self):
        self.sector_salud = SectorPAD.objects.create(
            codigo='S01', nombre='Salud',
        )
        self.sector_educacion = SectorPAD.objects.create(
            codigo='S02', nombre='Educación',
        )
        self.politica = PoliticaPAD.objects.create(
            codigo='POL-01', nombre='Política de Desarrollo Local',
            gestion=2026,
        )
        self.politica_2 = PoliticaPAD.objects.create(
            codigo='POL-02', nombre='Política Social',
            gestion=2026,
        )
        self.lineamiento = LineamientoEstrategico.objects.create(
            codigo='LIN-01', nombre='Lineamiento de Infraestructura',
            politica=self.politica, gestion=2026,
        )
        self.lineamiento_2 = LineamientoEstrategico.objects.create(
            codigo='LIN-02', nombre='Lineamiento de Servicios',
            politica=self.politica, gestion=2026,
        )
        self.resultado = ResultadoTerritorial.objects.create(
            codigo='RES-01', nombre='Resultado de Salud',
            lineamiento=self.lineamiento, sector=self.sector_salud,
            indicador='Cobertura de salud',
            formula='(beneficiarios / poblacion) * 100',
            linea_base=Decimal('65.0000'),
            meta_2030=Decimal('90.0000'),
            gestion=2026,
        )
        self.resultado_2 = ResultadoTerritorial.objects.create(
            codigo='RES-02', nombre='Resultado de Educación',
            lineamiento=self.lineamiento_2, sector=self.sector_educacion,
            gestion=2026,
        )
        self.producto = ProductoTerritorial.objects.create(
            codigo='PROD-01', nombre='Producto de Salud',
            resultado=self.resultado,
            indicador='Consultas atendidas',
            linea_base=Decimal('5000.0000'),
            meta_2030=Decimal('10000.0000'),
            cuenta_con_financiamiento='SI',
            presupuesto_total_pad=Decimal('200000.00'),
            gestion=2026,
        )
        self.producto_2 = ProductoTerritorial.objects.create(
            codigo='PROD-02', nombre='Producto de Educación',
            resultado=self.resultado_2,
            gestion=2026,
        )


class SectorPADModelTest(PADHierarchyBaseTestCase):
    """Tests del modelo SectorPAD."""

    def test_sector_creacion(self):
        self.assertEqual(self.sector_salud.codigo, 'S01')
        self.assertEqual(self.sector_salud.nombre, 'Salud')

    def test_sector_str(self):
        s = str(self.sector_salud)
        self.assertIn('S01', s)
        self.assertIn('Salud', s)

    def test_sector_unico_codigo(self):
        with self.assertRaises(Exception):
            SectorPAD.objects.create(
                codigo='S01', nombre='Duplicado',
            )


class PoliticaPADModelTest(PADHierarchyBaseTestCase):
    """Tests del modelo PoliticaPAD."""

    def test_politica_creacion(self):
        self.assertEqual(self.politica.gestion, 2026)
        self.assertEqual(self.politica.codigo, 'POL-01')

    def test_politica_str(self):
        s = str(self.politica)
        self.assertIn('POL-01', s)

    def test_politica_unique_together(self):
        with self.assertRaises(Exception):
            PoliticaPAD.objects.create(
                codigo='POL-01', nombre='Duplicada',
                gestion=2026,
            )

    def test_politica_diferentes_gestiones(self):
        PoliticaPAD.objects.create(
            codigo='POL-01', nombre='Mismo código',
            gestion=2027,
        )
        self.assertEqual(
            PoliticaPAD.objects.filter(codigo='POL-01').count(), 2
        )


class LineamientoEstrategicoModelTest(PADHierarchyBaseTestCase):
    """Tests del modelo LineamientoEstrategico."""

    def test_lineamiento_creacion(self):
        self.assertEqual(self.lineamiento.politica, self.politica)
        self.assertEqual(self.lineamiento.gestion, 2026)

    def test_lineamiento_str(self):
        s = str(self.lineamiento)
        self.assertIn('LIN-01', s)

    def test_lineamientos_por_politica(self):
        self.assertEqual(self.politica.lineamientos.count(), 2)

    def test_lineamiento_unique_together(self):
        with self.assertRaises(Exception):
            LineamientoEstrategico.objects.create(
                codigo='LIN-01', nombre='Duplicado',
                politica=self.politica, gestion=2026,
            )


class ResultadoTerritorialModelTest(PADHierarchyBaseTestCase):
    """Tests del modelo ResultadoTerritorial."""

    def test_resultado_creacion(self):
        self.assertEqual(self.resultado.lineamiento, self.lineamiento)
        self.assertEqual(self.resultado.sector, self.sector_salud)
        self.assertEqual(self.resultado.gestion, 2026)

    def test_resultado_str(self):
        s = str(self.resultado)
        self.assertIn('RES-01', s)

    def test_resultado_estados(self):
        estados = [c[0] for c in ResultadoTerritorial.ESTADO_CHOICES]
        self.assertIn('borrador', estados)
        self.assertIn('aprobado', estados)
        self.assertIn('rechazado', estados)

    def test_resultado_transicion_estados(self):
        self.resultado.estado = 'enviado'
        self.resultado.save()
        self.resultado.refresh_from_db()
        self.assertEqual(self.resultado.estado, 'enviado')

    def test_resultado_unique_together(self):
        with self.assertRaises(Exception):
            ResultadoTerritorial.objects.create(
                codigo='RES-01', nombre='Duplicado',
                lineamiento=self.lineamiento, gestion=2026,
            )

    def test_resultado_cod_geografico(self):
        self.assertEqual(self.resultado.cod_geografico, '')
        self.resultado.cod_geografico = '1102'
        self.resultado.save()
        self.resultado.refresh_from_db()
        self.assertEqual(self.resultado.cod_geografico, '1102')

    def test_resultado_indicador(self):
        self.assertEqual(self.resultado.indicador, 'Cobertura de salud')

    def test_resultado_linea_base(self):
        self.assertEqual(self.resultado.linea_base, Decimal('65.0000'))

    def test_resultado_meta_2030(self):
        self.assertEqual(self.resultado.meta_2030, Decimal('90.0000'))


class ProductoTerritorialModelTest(PADHierarchyBaseTestCase):
    """Tests del modelo ProductoTerritorial."""

    def test_producto_creacion(self):
        self.assertEqual(self.producto.resultado, self.resultado)
        self.assertEqual(self.producto.gestion, 2026)

    def test_producto_str(self):
        s = str(self.producto)
        self.assertIn('PROD-01', s)

    def test_producto_cuenta_financiamiento(self):
        self.assertEqual(self.producto.cuenta_con_financiamiento, 'SI')
        self.assertEqual(self.producto_2.cuenta_con_financiamiento, 'NO')

    def test_producto_presupuesto_pad(self):
        self.assertEqual(
            self.producto.presupuesto_total_pad, Decimal('200000.00')
        )
        self.assertIsNone(self.producto_2.presupuesto_total_pad)

    def test_producto_unique_together(self):
        with self.assertRaises(Exception):
            ProductoTerritorial.objects.create(
                codigo='PROD-01', nombre='Duplicado',
                resultado=self.resultado, gestion=2026,
            )

    def test_productos_por_resultado(self):
        self.assertEqual(self.resultado.productos.count(), 1)
        self.assertEqual(self.resultado_2.productos.count(), 1)


class ProgramacionAnualPADBudgetSumsTest(PADHierarchyBaseTestCase):
    """Tests de sumas de programación presupuestaria PAD."""

    def test_programacion_fisica_por_resultado(self):
        for anio in [2026, 2027, 2028]:
            ProgramacionAnualPAD.objects.create(
                resultado=self.resultado, anio=anio,
                tipo='fisica', valor=Decimal(f'{100 * anio}.0000'),
            )
        total = ProgramacionAnualPAD.objects.filter(
            resultado=self.resultado, tipo='fisica'
        ).aggregate(total_valor=Sum('valor'))
        self.assertEqual(total['total_valor'], Decimal('810000.0000'))

    def test_programacion_financiera_por_producto(self):
        for anio in [2026, 2027]:
            ProgramacionAnualPAD.objects.create(
                producto=self.producto, anio=anio,
                tipo='financiera', valor=Decimal(f'{50000 * (anio - 2025)}.0000'),
            )
        total = ProgramacionAnualPAD.objects.filter(
            producto=self.producto, tipo='financiera'
        ).aggregate(total_valor=Sum('valor'))
        self.assertIsNotNone(total['total_valor'])

    def test_programacion_valor_no_negativo(self):
        prog = ProgramacionAnualPAD(
            resultado=self.resultado, anio=2026,
            tipo='fisica', valor=Decimal('-100.0000'),
        )
        with self.assertRaises(ValidationError):
            prog.full_clean()

    def test_programacion_requiere_resultado_o_producto(self):
        prog = ProgramacionAnualPAD(
            resultado=None, producto=None,
            anio=2026, tipo='fisica', valor=Decimal('100.0000'),
        )
        with self.assertRaises(ValidationError):
            prog.full_clean()

    def test_programacion_duplicada_rechazada(self):
        ProgramacionAnualPAD.objects.create(
            resultado=self.resultado, producto=self.producto,
            anio=2026, tipo='fisica', valor=Decimal('100.0000'),
        )
        with self.assertRaises(Exception):
            ProgramacionAnualPAD.objects.create(
                resultado=self.resultado, producto=self.producto,
                anio=2026, tipo='fisica', valor=Decimal('200.0000'),
            )

    def test_programacion_tipos_fisica_financiera(self):
        ProgramacionAnualPAD.objects.create(
            resultado=self.resultado, anio=2026,
            tipo='fisica', valor=Decimal('100.0000'),
        )
        ProgramacionAnualPAD.objects.create(
            resultado=self.resultado, anio=2026,
            tipo='financiera', valor=Decimal('50000.0000'),
        )
        self.assertEqual(
            ProgramacionAnualPAD.objects.filter(
                resultado=self.resultado, anio=2026
            ).count(), 2
        )

    def test_programacion_varios_anios(self):
        for anio in range(2026, 2031):
            ProgramacionAnualPAD.objects.create(
                resultado=self.resultado, anio=anio,
                tipo='fisica', valor=Decimal('100.0000'),
            )
        self.assertEqual(
            ProgramacionAnualPAD.objects.filter(
                resultado=self.resultado
            ).count(), 5
        )

    def test_programacion_str(self):
        prog = ProgramacionAnualPAD.objects.create(
            resultado=self.resultado, anio=2026,
            tipo='fisica', valor=Decimal('100.0000'),
        )
        s = str(prog)
        self.assertIn('2026', s)
        self.assertIn('Física', s)

    def test_programacion_str_producto(self):
        prog = ProgramacionAnualPAD.objects.create(
            producto=self.producto, anio=2026,
            tipo='financiera', valor=Decimal('50000.0000'),
        )
        s = str(prog)
        self.assertIn('2026', s)
        self.assertIn('Financiera', s)


class IndicadorCreationPerResultadoTest(PADHierarchyBaseTestCase):
    """Tests de creación de indicadores por resultado territorial."""

    def setUp(self):
        super().setUp()
        from apps.indicadores.models import Indicador
        self.indicador = Indicador.objects.create(
            codigo='IND-SALUD-01', nombre='Cobertura de servicios de salud',
            formula='(beneficiarios_atendidos / poblacion_total) * 100',
            tipo_comportamiento='porcentaje',
            linea_base=Decimal('65.0000'),
            meta_anual=Decimal('90.0000'),
        )

    def test_indicador_vinculado_resultado(self):
        self.resultado.indicador = self.indicador.nombre
        self.resultado.save()
        self.resultado.refresh_from_db()
        self.assertEqual(self.resultado.indicador, self.indicador.nombre)

    def test_indicador_meta_programada_por_resultado(self):
        from apps.indicadores.models import MetaProgramada
        meta = MetaProgramada.objects.create(
            indicador=self.indicador, gestion=2026,
            meta_anual=Decimal('90.0000'),
            trimestre1=Decimal('20.0000'),
            trimestre2=Decimal('22.0000'),
            trimestre3=Decimal('24.0000'),
            trimestre4=Decimal('24.0000'),
        )
        suma = meta.trimestre1 + meta.trimestre2 + meta.trimestre3 + meta.trimestre4
        self.assertEqual(suma, meta.meta_anual)

    def test_articulacion_log(self):
        log = ArticulacionLog.objects.create(
            entidad='resultado', entidad_id=str(self.resultado.id),
            accion='crear', detalle={'campo': 'nombre'},
        )
        self.assertEqual(log.entidad, 'resultado')
        self.assertEqual(log.accion, 'crear')

    def test_articulacion_log_str(self):
        log = ArticulacionLog.objects.create(
            entidad='producto', entidad_id=str(self.producto.id),
            accion='aprobar',
        )
        s = str(log)
        self.assertIn('producto', s)
        self.assertIn('aprobar', s)

    def test_resultado_sector_relacion(self):
        self.assertEqual(self.resultado.sector, self.sector_salud)
        self.assertEqual(self.resultado_2.sector, self.sector_educacion)
