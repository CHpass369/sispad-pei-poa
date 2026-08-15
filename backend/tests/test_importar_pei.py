"""Tests del management command importar_pei (kernel estratégico SIS-PE)."""
import pytest
from django.core.management import call_command

from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    TipoNodoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
)


def _importar_pei(gestion=2027):
    call_command('importar_pei', gestion=gestion)


def test_importar_pei_crea_metodologia_y_tipos(db):
    _importar_pei()

    metodologia = VersionMetodologia.objects.get(codigo='MET-PEI-OFICIAL')
    assert metodologia.nombre == 'Metodología PEI Oficial'
    assert metodologia.version == '1.0.0'
    assert metodologia.estado == 'vigente'
    assert metodologia.tipo_instrumento.codigo == 'PEI'

    codigos = set(
        TipoNodoEstrategico.objects.filter(metodologia=metodologia)
        .values_list('codigo', flat=True)
    )
    assert {'OE', 'RI', 'PI'} <= codigos

    instrumento = InstrumentoPlanificacion.objects.get(codigo='PEI-2027')
    assert instrumento.tipo.codigo == 'PEI'
    assert instrumento.periodo_inicio == 2027
    assert instrumento.versiones.count() == 1


def test_importar_pei_crea_version_borrador(db):
    _importar_pei()

    version = VersionInstrumento.objects.get(
        instrumento__codigo='PEI-2027', numero=1,
    )
    assert version.estado == 'borrador'
    assert version.inmutable is False


def test_importar_pei_idempotente(db):
    _importar_pei()
    totales_antes = (
        VersionMetodologia.objects.count(),
        TipoNodoEstrategico.objects.count(),
        InstrumentoPlanificacion.objects.count(),
        VersionInstrumento.objects.count(),
    )

    _importar_pei()

    totales_despues = (
        VersionMetodologia.objects.count(),
        TipoNodoEstrategico.objects.count(),
        InstrumentoPlanificacion.objects.count(),
        VersionInstrumento.objects.count(),
    )
    assert totales_antes == totales_despues
    assert VersionMetodologia.objects.filter(
        codigo='MET-PEI-OFICIAL',
    ).count() == 1
    assert InstrumentoPlanificacion.objects.filter(
        codigo='PEI-2027',
    ).count() == 1


def test_importar_pei_respeta_instrumento_preexistente(db):
    """Si PEI-2027 ya existe (aprobado p. ej.), no se toca ni se crea v2."""
    _importar_pei()
    instrumento = InstrumentoPlanificacion.objects.get(codigo='PEI-2027')
    version = instrumento.versiones.get(numero=1)

    _importar_pei()

    instrumento.refresh_from_db()
    assert instrumento.versiones.count() == 1
    assert instrumento.versiones.get(numero=1).pk == version.pk
