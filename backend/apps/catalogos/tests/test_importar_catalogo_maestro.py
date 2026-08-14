"""Tests de integración del importador del catálogo maestro (spec §8).

Matriz: idempotencia, jerarquías OG, componente→eje (H5), CONTIENE,
conteos vs catálogo, dry-run no muta, commit pobló modelos, reglas
mapeadas, diferencia 2758/2764, versiones no duplicadas y GestionFiscal
2026. Requieren la BD dev con el catálogo cargado; ver conftest.py.
"""
import os
from io import StringIO

import pytest
from django.core.management import call_command

from apps.catalogos.models import (
    ClasificadorGeograficoPresupuestario,
    ClasificadorInstitucional,
    FinalidadFuncion,
    FuenteFinanciamiento,
    ObjetoGasto,
    OrganismoFinanciador,
    RubroRecurso,
    SectorEconomicoPresupuestario,
    UnidadMedida,
    ValidacionPlataforma,
    VersionClasificador,
)
from apps.codificacion.models import ComponentePDESA, EjePGDESA, LineamientoPAD
from apps.gestion.models import GestionFiscal
from apps.normativa.models import ReglaPresupuestariaLegal
from apps.presupuesto.models import (
    ActividadPresupuestaria,
    ProgramaPresupuestario,
    ProyectoPresupuestario,
)
from apps.techos.models import RecursoTecho, TechoPresupuestario

pytestmark = [
    pytest.mark.integration,
    pytest.mark.django_db,
    pytest.mark.skipif(
        os.environ.get('SISPOA_INTEGRATION', '0') != '1',
        reason='Requiere SISPOA_INTEGRATION=1 y BD dev gams_sis_poa_dev '
               'con el catálogo maestro cargado (ver conftest.py).',
    ),
]


def ejecutar(lote='todos', commit=True, gestion=2026):
    """Ejecuta el comando y devuelve su salida."""
    salida = StringIO()
    call_command(
        'importar_catalogo_maestro',
        lote=lote,
        commit=commit,
        gestion=gestion,
        stdout=salida,
        stderr=StringIO(),
    )
    return salida.getvalue()


def version_pgdesa():
    from apps.planificacion.models import Plan
    plan = Plan.objects.get(codigo='PGDESA-2026-2035', tipo='pgdesa')
    return plan.versiones_catalogo.get(gestion=2026)


def version_pdesa():
    from apps.planificacion.models import Plan
    plan = Plan.objects.get(codigo='PDESA-2026-2030', tipo='pdesa')
    return plan.versiones_catalogo.get(gestion=2026)


# ---------------------------------------------------------------------------
# 1. Idempotencia
# ---------------------------------------------------------------------------

class TestIdempotencia:
    def test_doble_commit_no_duplica(self):
        ejecutar(commit=True)
        conteos_primera = {
            'FuenteFinanciamiento': FuenteFinanciamiento.objects.count(),
            'ObjetoGasto': ObjetoGasto.objects.count(),
            'ProgramaPresupuestario': (
                ProgramaPresupuestario.objects.count()
            ),
            'ReglaPresupuestariaLegal': (
                ReglaPresupuestariaLegal.objects.count()
            ),
        }
        ejecutar(commit=True)
        for modelo, conteo in conteos_primera.items():
            assert conteo > 0
        assert FuenteFinanciamiento.objects.count() == conteos_primera['FuenteFinanciamiento']
        assert ObjetoGasto.objects.count() == conteos_primera['ObjetoGasto']
        assert (
            ProgramaPresupuestario.objects.count()
            == conteos_primera['ProgramaPresupuestario']
        )
        assert (
            ReglaPresupuestariaLegal.objects.count()
            == conteos_primera['ReglaPresupuestariaLegal']
        )


# ---------------------------------------------------------------------------
# 2/3/4. Jerarquías
# ---------------------------------------------------------------------------

class TestJerarquias:
    def test_objeto_gasto_5_niveles_padre_y_codigos(self):
        ejecutar(lote='clasificadores', commit=True)
        assert ObjetoGasto.objects.filter(gestion=2026).count() == 505
        assert ObjetoGasto.objects.filter(
            gestion=2026, padre__isnull=True,
        ).count() == 9
        assert not ObjetoGasto.objects.filter(
            gestion=2026,
        ).exclude(codigo__regex=r'^\d{5}$').exists()
        for nivel in ('grupo', 'subgrupo', 'partida', 'detalle'):
            assert ObjetoGasto.objects.filter(
                gestion=2026, nivel=nivel,
            ).count() > 0

    def test_componente_bajo_eje_por_segmento(self):
        ejecutar(lote='marco_superior', commit=True)
        version = version_pgdesa()
        assert EjePGDESA.objects.filter(
            version_catalogo=version,
        ).count() == 7
        componentes = ComponentePDESA.objects.filter(
            version_catalogo=version_pdesa(),
        )
        assert componentes.count() == 38
        # H5: el eje se resuelve por el 1.er segmento del código.
        distribucion = {}
        for componente in componentes:
            distribucion[componente.eje_id] = (
                distribucion.get(componente.eje_id, 0) + 1
            )
        assert len(distribucion) == 7
        assert all(conteo > 0 for conteo in distribucion.values())
        # Spot check: eje 01 (catálogo '1') contiene los componentes 1.1..1.6.
        eje_01 = EjePGDESA.objects.get(version_catalogo=version, codigo='01')
        assert eje_01.componentes.filter(
            version_catalogo=version_pdesa(),
        ).count() == 6

    def test_con_tiene_170_lineamientos_con_componente(self):
        ejecutar(lote='marco_superior', commit=True)
        version = version_pdesa()
        lineamientos = LineamientoPAD.objects.filter(
            version_catalogo=version,
        )
        assert lineamientos.count() == 170
        assert lineamientos.filter(componente__isnull=False).count() == 170
        assert lineamientos.filter(codigo__regex=r'^\d{3}$').count() == 170


# ---------------------------------------------------------------------------
# 5. Conteos vs catálogo
# ---------------------------------------------------------------------------

class TestConteos:
    def test_conteos_por_modelo(self):
        ejecutar(commit=True)
        assert FuenteFinanciamiento.objects.filter(gestion=2026).count() == 21
        assert OrganismoFinanciador.objects.filter(gestion=2026).count() == 160
        assert ObjetoGasto.objects.filter(gestion=2026).count() == 505
        assert ClasificadorInstitucional.objects.filter(gestion=2026).count() == 568
        assert RubroRecurso.objects.filter(gestion=2026).count() == 350
        assert FinalidadFuncion.objects.filter(gestion=2026).count() == 145
        assert SectorEconomicoPresupuestario.objects.filter(gestion=2026).count() == 406
        assert (
            ClasificadorGeograficoPresupuestario.objects.filter(
                version_clasificador__gestion=2026,
            ).count() == 603
        )
        assert EjePGDESA.objects.filter(
            version_catalogo=version_pgdesa(),
        ).count() == 7
        assert ComponentePDESA.objects.filter(
            version_catalogo=version_pdesa(),
        ).count() == 38
        assert LineamientoPAD.objects.filter(
            version_catalogo=version_pdesa(),
        ).count() == 170
        # 34 programas del catálogo + 1 sintético '319' (H9: actividad
        # 'Atención de Desastres' referenciada dentro del rango 310-319).
        assert (
            ProgramaPresupuestario.objects.filter(gestion=2027).count() == 35
        )
        assert ProgramaPresupuestario.objects.filter(
            gestion=2027, codigo='319',
        ).exists()
        assert (
            ActividadPresupuestaria.objects.filter(gestion=2027).count() == 15
        )
        assert RecursoTecho.objects.count() == 15
        assert ReglaPresupuestariaLegal.objects.count() == 21
        assert ValidacionPlataforma.objects.count() == 9
        assert UnidadMedida.objects.filter(gestion=2026).count() == 13


# ---------------------------------------------------------------------------
# 6. Dry-run no muta
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_no_persiste(self):
        antes = {
            'FuenteFinanciamiento': FuenteFinanciamiento.objects.count(),
            'ObjetoGasto': ObjetoGasto.objects.count(),
            'ProgramaPresupuestario': ProgramaPresupuestario.objects.count(),
            'ReglaPresupuestariaLegal': ReglaPresupuestariaLegal.objects.count(),
        }
        salida = ejecutar(commit=False)
        assert 'DRY-RUN' in salida
        assert FuenteFinanciamiento.objects.count() == antes['FuenteFinanciamiento']
        assert ObjetoGasto.objects.count() == antes['ObjetoGasto']
        assert (
            ProgramaPresupuestario.objects.count()
            == antes['ProgramaPresupuestario']
        )
        assert (
            ReglaPresupuestariaLegal.objects.count()
            == antes['ReglaPresupuestariaLegal']
        )


# ---------------------------------------------------------------------------
# 7. Commit pobló modelos
# ---------------------------------------------------------------------------

class TestCommitPobla:
    def test_modelos_poblados(self):
        ejecutar(commit=True)
        for queryset in (
            FuenteFinanciamiento.objects.all(),
            OrganismoFinanciador.objects.all(),
            ObjetoGasto.objects.all(),
            ClasificadorInstitucional.objects.all(),
            RubroRecurso.objects.all(),
            FinalidadFuncion.objects.all(),
            SectorEconomicoPresupuestario.objects.all(),
            ClasificadorGeograficoPresupuestario.objects.all(),
            EjePGDESA.objects.all(),
            ComponentePDESA.objects.all(),
            LineamientoPAD.objects.all(),
            ProgramaPresupuestario.objects.all(),
            ProyectoPresupuestario.objects.all(),
            ActividadPresupuestaria.objects.all(),
            TechoPresupuestario.objects.all(),
            RecursoTecho.objects.all(),
            ReglaPresupuestariaLegal.objects.all(),
            ValidacionPlataforma.objects.all(),
        ):
            assert queryset.count() > 0


# ---------------------------------------------------------------------------
# 8. Reglas mapeadas
# ---------------------------------------------------------------------------

class TestReglasMapeadas:
    def test_tipo_severidad_y_parametros(self):
        ejecutar(lote='reglas', commit=True)
        sus = ReglaPresupuestariaLegal.objects.get(codigo='GAM-SUS-001')
        assert sus.tipo == 'porcentaje'
        assert sus.severidad == 'bloqueante'
        assert sus.gestion_desde == 2027
        assert sus.parametros['programa'] == '200'
        assert sus.parametros['fuente'] == '41'

        pcd = ReglaPresupuestariaLegal.objects.get(codigo='GAM-PCD-002')
        assert pcd.tipo == 'personal'
        assert pcd.severidad == 'advertencia'

        codigo = ReglaPresupuestariaLegal.objects.get(codigo='GAM-COD-001')
        assert codigo.tipo == 'codigo'
        assert codigo.parametros['programa'] == '010-096'


# ---------------------------------------------------------------------------
# 9. Diferencia 2758/2764
# ---------------------------------------------------------------------------

class TestReconciliacionOrigen:
    def test_reporte_diferencia_objeto_gasto(self):
        salida = ejecutar(lote='clasificadores', commit=False)
        assert 'OBJETO_GASTO' in salida
        assert '511' in salida
        assert '505' in salida
        # La diferencia se reporta pero no se importa.
        assert ObjetoGasto.objects.count() == 0 or ObjetoGasto.objects.filter(
            gestion=2026,
        ).count() == 505


# ---------------------------------------------------------------------------
# 10. Versiones no duplicadas
# ---------------------------------------------------------------------------

class TestVersiones:
    def test_versiones_2026_reutilizadas(self):
        ejecutar(lote='clasificadores', commit=True)
        for tipo in (
            VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
            VersionClasificador.TIPO_OBJETO_GASTO,
            VersionClasificador.TIPO_ORGANISMO_FINANCIADOR,
        ):
            assert VersionClasificador.objects.filter(
                tipo=tipo, gestion=2026,
            ).count() == 1
            assert VersionClasificador.objects.filter(
                tipo=tipo, gestion=2026, vigente=True,
            ).count() == 1


# ---------------------------------------------------------------------------
# 11. GestionFiscal 2026
# ---------------------------------------------------------------------------

class TestGestionFiscal:
    def test_gestion_2026_abierta_idempotente(self):
        ejecutar(lote='sispoa', commit=True)
        gestion = GestionFiscal.objects.filter(anio=2026)
        assert gestion.count() == 1
        assert gestion.first().estado == 'abierta'
        ejecutar(lote='sispoa', commit=True)
        assert GestionFiscal.objects.filter(anio=2026).count() == 1
