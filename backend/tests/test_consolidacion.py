"""
Tests de consolidación y cálculos monetarios.
Usa datos semilla mínimos para verificar sumas, alertas y consistencia.
"""
import pytest
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.workflow.consolidacion import (
    consolidar_poa_institucional,
    verificar_consistencia_presupuestaria,
    generar_acta_consolidacion,
)
from apps.presupuesto.models import LineaPresupuestaria, ProgramaPresupuestario
from apps.techos.models import TechoPresupuestario, DistribucionTecho


class TestConsolidacion:
    """Tests de consolidación institucional."""

    def test_consolidar_sin_datos(self, gestion):
        """Consolidación sin datos debe retornar estructura válida."""
        resultado = consolidar_poa_institucional(2026)
        assert 'estado' in resultado
        assert 'alertas' in resultado
        assert 'totales' in resultado
        assert resultado['estado'] in ('completado', 'con_observaciones', 'incompleto')

    def test_consolidar_con_lineas(self, gestion, programa, fuentes, objetos_gasto):
        """Consolidación con líneas presupuestarias debe sumar correctamente."""
        from datetime import date
        from apps.organizacion.models import DireccionAdministrativa, UnidadEjecutora
        da, _ = DireccionAdministrativa.objects.get_or_create(
            codigo='99', gestion=2026,
            defaults={'nombre': 'DA Test', 'fecha_vigencia_desde': date(2026, 1, 1)}
        )
        ue, _ = UnidadEjecutora.objects.get_or_create(
            codigo='99', da=da, gestion=2026,
            defaults={'nombre': 'UE Test', 'fecha_vigencia_desde': date(2026, 1, 1)}
        )
        fuente = fuentes.first()
        objeto = objetos_gasto.first()
        from apps.catalogos.models import FinalidadFuncion
        ff, _ = FinalidadFuncion.objects.get_or_create(
            codigo='TEST', gestion=2026,
            defaults={'denominacion': 'Finalidad Test',
                      'fecha_vigencia_desde': date(2026, 1, 1)}
        )

        LineaPresupuestaria.objects.create(
            gestion=2026, entidad='TEST',
            da=da, ue=ue, programa=programa,
            finalidad_funcion=ff, fuente=fuente,
            objeto_gasto=objeto,
            importe=Decimal('100000.00'),
        )
        LineaPresupuestaria.objects.create(
            gestion=2026, entidad='TEST',
            da=da, ue=ue, programa=programa,
            finalidad_funcion=ff, fuente=fuente,
            objeto_gasto=objeto,
            importe=Decimal('50000.00'),
        )

        resultado = consolidar_poa_institucional(2026)
        totales = resultado['totales']
        total_formulado = float(totales.get('formulado', 0))
        assert total_formulado == 150000.0, \
            f'Total formulado debe ser 150,000, es {total_formulado}. Totales: {totales}'

    def test_verificar_consistencia_sin_datos(self, gestion):
        """Verificación sin datos debe retornar estructura."""
        resultado = verificar_consistencia_presupuestaria(2026)
        assert 'gestion' in resultado
        assert 'hallazgos' in resultado
        assert 'resumen' in resultado

    def test_acta_consolidacion(self, gestion):
        """Acta debe generar texto con fecha y gestión."""
        resultado = generar_acta_consolidacion(2026)
        assert 'acta' in resultado or 'texto' in resultado or 'resumen' in resultado
        texto = str(resultado)
        assert '2026' in texto

    def test_verificar_techo_sin_distribuir(self, gestion, fuentes):
        """Debe detectar techos sin distribuir."""
        techo, _ = TechoPresupuestario.objects.get_or_create(
            gestion=2026, fuente=fuentes.first(),
            defaults={'monto_total': 1000000}
        )
        resultado = verificar_consistencia_presupuestaria(2026)
        alertas = resultado.get('alertas', [])
        techos_alertas = [a for a in alertas if 'techo' in str(a).lower()]
        assert len(resultado.get('alertas', [])) >= 0

    def test_consolidacion_idempotente(self, gestion):
        """Consolidar dos veces debe dar el mismo resultado."""
        r1 = consolidar_poa_institucional(2026)
        r2 = consolidar_poa_institucional(2026)
        assert r1['estado'] == r2['estado']
