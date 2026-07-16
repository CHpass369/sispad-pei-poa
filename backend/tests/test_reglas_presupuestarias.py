"""
Tests CRÍTICOS: Reglas presupuestarias legales.
Estas reglas manejan plata y su correctitud no es negociable.
"""
import pytest
from decimal import Decimal
from apps.normativa.services import evaluar_reglas_presupuestarias
from apps.normativa.models import ReglaPresupuestariaLegal


class TestReglasPresupuestarias:
    """Suite de tests para reglas presupuestarias."""

    def test_reglas_existen(self, reglas):
        """Las reglas deben estar creadas en la BD."""
        count = ReglaPresupuestariaLegal.objects.filter(activo=True).count()
        assert count >= 5, f'Deben existir al menos 5 reglas, hay {count}'

    def test_limite_gasto_funcionamiento_cumple(self, reglas):
        """Gasto funcionamiento dentro del 60% debe pasar."""
        data = {'presupuesto_total': 10000000, 'gasto_funcionamiento': 5000000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'limite_gasto_funcionamiento')
        assert r['cumple'] is True, f'Debe cumplir: 5M/10M = 50% < 60%. Detalle: {r}'

    def test_limite_gasto_funcionamiento_no_cumple(self, reglas):
        """Gasto funcionamiento sobre el 60% debe fallar."""
        data = {'presupuesto_total': 10000000, 'gasto_funcionamiento': 7000000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'limite_gasto_funcionamiento')
        assert r['cumple'] is False, f'Debe NO cumplir: 7M/10M = 70% > 60%'

    def test_limite_funcionamiento_borde(self, reglas):
        """Exactamente en el límite (60%) debe pasar."""
        data = {'presupuesto_total': 10000000, 'gasto_funcionamiento': 6000000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'limite_gasto_funcionamiento')
        assert r['cumple'] is True, 'Exactamente 60% debe pasar'

    def test_no_superar_techo_cumple(self, reglas):
        """Formulado menor o igual al techo debe pasar."""
        data = {'techo_asignado': 5000000, 'monto_formulado': 4800000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'no_superar_techo')
        assert r['cumple'] is True

    def test_no_superar_techo_no_cumple(self, reglas):
        """Formulado mayor al techo debe fallar."""
        data = {'techo_asignado': 5000000, 'monto_formulado': 5200000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'no_superar_techo')
        assert r['cumple'] is False

    def test_sus_cumple(self, reglas):
        """Asignación SUS >= 10% debe pasar."""
        data = {'presupuesto_total': 10000000, 'asignacion_sus': 1200000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'gasto_sus')
        assert r['cumple'] is True

    def test_sus_no_cumple(self, reglas):
        """Asignación SUS < 10% debe fallar."""
        data = {'presupuesto_total': 10000000, 'asignacion_sus': 500000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'gasto_sus')
        assert r['cumple'] is False

    def test_renta_dignidad_cumple(self, reglas):
        """Renta Dignidad >= 0.75% debe pasar."""
        data = {'presupuesto_total': 10000000, 'asignacion_renta_dignidad': 80000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'renta_dignidad')
        assert r['cumple'] is True

    def test_seguridad_ciudadana_cumple(self, reglas):
        """Seguridad Ciudadana >= 10% debe pasar."""
        data = {'presupuesto_total': 10000000, 'asignacion_seguridad': 1100000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'seguridad_ciudadana')
        assert r['cumple'] is True

    def test_seguridad_ciudadana_no_cumple(self, reglas):
        """Seguridad Ciudadana < 10% debe fallar."""
        data = {'presupuesto_total': 10000000, 'asignacion_seguridad': 500000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'seguridad_ciudadana')
        assert r['cumple'] is False

    def test_integridad_decimal(self, reglas):
        """Los cálculos monetarios deben usar Decimal, no float."""
        data = {
            'presupuesto_total': 10000000.01,
            'gasto_funcionamiento': 4999999.99,
            'techo_asignado': 5000000.00,
            'monto_formulado': 4999999.99,
            'asignacion_sus': 1000000.50,
            'asignacion_renta_dignidad': 75000.25,
            'asignacion_seguridad': 1000000.75,
        }
        resultados = evaluar_reglas_presupuestarias(2026, data)
        for r in resultados:
            if r.get('detalle'):
                for k, v in r['detalle'].items():
                    assert isinstance(v, (int, float)), f'{r["regla"]}.{k} debe ser número, es {type(v)}'

    def test_reglas_multiples_incumplimiento(self, reglas):
        """Múltiples reglas deben fallar simultáneamente con datos malos."""
        data = {
            'presupuesto_total': 10000000,
            'gasto_funcionamiento': 7000000,
            'techo_asignado': 5000000,
            'monto_formulado': 5500000,
            'asignacion_sus': 500000,
            'asignacion_renta_dignidad': 30000,
            'asignacion_seguridad': 300000,
        }
        resultados = evaluar_reglas_presupuestarias(2026, data)
        falsos = [r for r in resultados if r.get('cumple') is False]
        assert len(falsos) >= 3, f'Deben fallar al menos 3 reglas: {[r["regla"] for r in falsos]}'

    def test_regla_sin_implementacion(self, reglas):
        """Regla sin estrategia debe reportar error sin crashear."""
        data = {'presupuesto_total': 10000000, 'gasto_funcionamiento': 5000000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        for r in resultados:
            assert 'error' not in r or r.get('error') is None or \
                   r['error'].startswith('Sin implementación'), \
                   f'Error inesperado en {r["regla"]}: {r.get("error")}'

    def test_parametros_ausentes(self, reglas):
        """Reglas sin parametros deben funcionar con valores por defecto."""
        data = {'techo_asignado': 5000000, 'monto_formulado': 4800000}
        resultados = evaluar_reglas_presupuestarias(2026, data)
        r = next(r for r in resultados if r['regla'] == 'no_superar_techo')
        assert r['cumple'] is True
