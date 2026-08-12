"""
Tests del mapeo operativo de estados de gestión (Q3, slice S2).

estado_operativo() es el mapeo centralizado 8→4 (BORRADOR / VIGENTE /
CERRADA / ANULADA) usado por wizard, API y validación. Los estados
VIGENTE y ANULADA son aditivos sobre los 8 existentes.
"""
import pytest

from apps.gestion.models import GestionFiscal
from apps.gestion.services import estado_operativo


def test_mapeo_borrador():
    """preparacion/abierta/formulacion/revision/consolidacion → BORRADOR."""
    for estado in (
        GestionFiscal.Estado.PREPARACION,
        GestionFiscal.Estado.ABIERTA,
        GestionFiscal.Estado.FORMULACION,
        GestionFiscal.Estado.REVISION,
        GestionFiscal.Estado.CONSOLIDACION,
    ):
        assert estado_operativo(estado) == 'BORRADOR'


def test_mapeo_vigente():
    """aprobacion y el nuevo vigente → VIGENTE."""
    assert estado_operativo(GestionFiscal.Estado.APROBACION) == 'VIGENTE'
    assert estado_operativo(GestionFiscal.Estado.VIGENTE) == 'VIGENTE'


def test_mapeo_cerrada():
    """cerrada/archivada → CERRADA."""
    assert estado_operativo(GestionFiscal.Estado.CERRADA) == 'CERRADA'
    assert estado_operativo(GestionFiscal.Estado.ARCHIVADA) == 'CERRADA'


def test_mapeo_anulada():
    """El nuevo estado anulada → ANULADA (terminal)."""
    assert estado_operativo(GestionFiscal.Estado.ANULADA) == 'ANULADA'


def test_estados_nuevos_aditivos_en_choices():
    """Los estados VIGENTE/ANULADA existen y los 8 previos siguen intactos."""
    valores = set(GestionFiscal.Estado.values)
    assert 'vigente' in valores
    assert 'anulada' in valores
    for estado in (
        'preparacion', 'abierta', 'formulacion', 'revision',
        'consolidacion', 'aprobacion', 'cerrada', 'archivada',
    ):
        assert estado in valores
