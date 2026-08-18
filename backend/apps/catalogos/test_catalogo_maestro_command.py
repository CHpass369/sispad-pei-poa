import pytest
from django.core.management import call_command
from django.db import ProgrammingError


pytestmark = pytest.mark.django_db


def test_dry_run_reporta_lote_marco_superior_no_disponible(capsys):
    call_command(
        'importar_catalogo_maestro',
        lote='marco_superior',
        gestion=2027,
        dry_run=True,
    )

    capturado = capsys.readouterr()
    salida = capturado.out + capturado.err
    assert 'marco_superior retirado' in salida
    assert 'Resumen (DRY-RUN' in salida


def test_dry_run_reporta_esquema_legacy_ausente_sin_exigirlo(
    capsys, monkeypatch,
):
    from apps.catalogos.management.commands import importar_catalogo_maestro

    def lote_sin_esquema(reporte, gestion):
        raise ProgrammingError('relation "catalogo.clasificador_item" does not exist')

    monkeypatch.setitem(
        importar_catalogo_maestro.FUNCIONES_LOTE,
        importar_catalogo_maestro.LOTE_CLASIFICADORES,
        lote_sin_esquema,
    )
    call_command(
        'importar_catalogo_maestro',
        lote='clasificadores',
        gestion=2027,
        dry_run=True,
    )

    capturado = capsys.readouterr()
    salida = capturado.out + capturado.err
    assert 'catalogo.clasificador_item' in salida
    assert 'Lote clasificadores' in salida
