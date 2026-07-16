from django.test import TestCase
from rest_framework import serializers
from apps.pad.models import (
    ProgramacionAnualPAD, ResultadoTerritorial, ProductoTerritorial,
    LineamientoEstrategico, SectorPAD, PoliticaPAD,
)
from apps.pad.serializers import (
    ProgramacionAnualPADSerializer, ResultadoTerritorialSerializer,
    ProductoTerritorialSerializer,
)


class ProgramacionAnualPADSerializerTest(TestCase):
    """Tests del serializer ProgramacionAnualPADSerializer"""

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

    def test_serializer_valida_valor_negativo(self):
        """Rechazar valor negativo"""
        data = {
            'resultado': self.resultado.id,
            'anio': 2026, 'tipo': 'fisica', 'valor': -100
        }
        serializer = ProgramacionAnualPADSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('valor', serializer.errors)

    def test_serializer_valida_fk_nulos(self):
        """Rechazar si no se envía resultado ni producto"""
        data = {
            'anio': 2026, 'tipo': 'fisica', 'valor': 100
        }
        serializer = ProgramacionAnualPADSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_serializer_valida_solo_producto(self):
        """Aceptar si solo se envía producto"""
        producto = ProductoTerritorial.objects.create(
            codigo='P01', nombre='Producto 1',
            resultado=self.resultado, gestion=2026
        )
        data = {
            'producto': producto.id,
            'anio': 2026, 'tipo': 'financiera', 'valor': 50000
        }
        serializer = ProgramacionAnualPADSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class ResultadoTerritorialSerializerTest(TestCase):
    """Tests del serializer ResultadoTerritorialSerializer con programaciones anidadas"""

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

    def test_create_con_programaciones_anidadas(self):
        """Crear resultado con programaciones anidadas en un solo POST"""
        data = {
            'codigo': 'R01',
            'nombre': 'Resultado con programaciones',
            'lineamiento': self.lineamiento.id,
            'sector': self.sector.id,
            'gestion': 2026,
            'cod_geografico': '1102',
            'programaciones': [
                {'anio': 2026, 'tipo': 'fisica', 'valor': 100.5000},
                {'anio': 2027, 'tipo': 'fisica', 'valor': 200.0000},
                {'anio': 2026, 'tipo': 'financiera', 'valor': 50000.0000},
            ]
        }
        serializer = ResultadoTerritorialSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        resultado = serializer.save()
        # programaciones es write_only, verificar via DB
        self.assertEqual(
            ProgramacionAnualPAD.objects.filter(resultado=resultado).count(), 3
        )
        self.assertEqual(resultado.cod_geografico, '1102')

    def test_create_sin_programaciones(self):
        """Crear resultado sin programaciones"""
        data = {
            'codigo': 'R02',
            'nombre': 'Resultado sin programaciones',
            'lineamiento': self.lineamiento.id,
            'sector': self.sector.id,
            'gestion': 2026,
        }
        serializer = ResultadoTerritorialSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        resultado = serializer.save()
        self.assertEqual(resultado.programaciones.count(), 0)

    def test_update_reemplaza_programaciones(self):
        """Update reemplaza todas las programaciones existentes"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado original',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=2026
        )
        ProgramacionAnualPAD.objects.create(
            resultado=resultado, anio=2026, tipo='fisica', valor=100
        )
        data = {
            'codigo': 'R01',
            'nombre': 'Resultado actualizado',
            'lineamiento': self.lineamiento.id,
            'sector': self.sector.id,
            'gestion': 2026,
            'programaciones': [
                {'anio': 2027, 'tipo': 'fisica', 'valor': 300.0000},
            ]
        }
        serializer = ResultadoTerritorialSerializer(
            resultado, data=data, partial=False
        )
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        resultado_actualizado = serializer.save()
        # Debe tener solo 1 programación (la anterior eliminada)
        progs = ProgramacionAnualPAD.objects.filter(resultado=resultado_actualizado)
        self.assertEqual(progs.count(), 1)
        self.assertEqual(progs.first().anio, 2027)

    def test_jsonfields_read_only(self):
        """programacion_fisica y programacion_financiera deben ser read_only"""
        resultado = ResultadoTerritorial.objects.create(
            codigo='R01', nombre='Resultado',
            lineamiento=self.lineamiento, sector=self.sector,
            gestion=2026
        )
        data = {
            'codigo': 'R01',
            'nombre': 'Resultado actualizado',
            'lineamiento': self.lineamiento.id,
            'sector': self.sector.id,
            'gestion': 2026,
            'programacion_fisica': {'2026': 999},
        }
        serializer = ResultadoTerritorialSerializer(
            resultado, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        # El valor de programacion_fisica debe ignorarse (read_only)
        resultado.refresh_from_db()
        self.assertIsNone(resultado.programacion_fisica)


class ProductoTerritorialSerializerTest(TestCase):
    """Tests del serializer ProductoTerritorialSerializer con nuevos campos"""

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

    def test_create_con_cuenta_con_financiamiento(self):
        """Crear producto con cuenta_con_financiamiento"""
        data = {
            'codigo': 'P01',
            'nombre': 'Producto con financiamiento',
            'resultado': self.resultado.id,
            'gestion': 2026,
            'cuenta_con_financiamiento': 'SI',
            'presupuesto_total_pad': 250000.00,
        }
        serializer = ProductoTerritorialSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        producto = serializer.save()
        self.assertEqual(producto.cuenta_con_financiamiento, 'SI')
        self.assertEqual(producto.presupuesto_total_pad, 250000.00)

    def test_create_con_programaciones_anidadas(self):
        """Crear producto con programaciones anidadas"""
        data = {
            'codigo': 'P01',
            'nombre': 'Producto con programaciones',
            'resultado': self.resultado.id,
            'gestion': 2026,
            'programaciones': [
                {'anio': 2026, 'tipo': 'fisica', 'valor': 50.0000},
                {'anio': 2026, 'tipo': 'financiera', 'valor': 10000.0000},
            ]
        }
        serializer = ProductoTerritorialSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        producto = serializer.save()
        self.assertEqual(
            ProgramacionAnualPAD.objects.filter(producto=producto).count(), 2
        )

    def test_jsonfields_read_only(self):
        """programacion_fisica/financiera deben ser read_only en producto"""
        data = {
            'codigo': 'P01',
            'nombre': 'Producto',
            'resultado': self.resultado.id,
            'gestion': 2026,
            'programacion_fisica': {'2026': 999},
        }
        serializer = ProductoTerritorialSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        producto = serializer.save()
        self.assertIsNone(producto.programacion_fisica)
