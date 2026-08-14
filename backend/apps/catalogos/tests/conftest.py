"""Conftest de los tests de integración del importador del catálogo maestro.

Los esquemas del catálogo (``core|catalogo|sispe|sispoa|metadata``) solo
existen en la BD dev ``gams_sis_poa_dev``; el test DB que crea pytest-django
no los tiene. Por eso estos tests corren DIRECTAMENTE contra la BD dev y se
revierten al final de cada test (fixture ``db`` transaccional).

Gating:
- Sin ``SISPOA_INTEGRATION=1`` los tests quedan marcados como skip (la suite
  por defecto corre verde sin tocar la BD).
- Con ``SISPOA_INTEGRATION=1`` se exige ``DB_NAME=gams_sis_poa_dev``: se
  aborta si alguien apunta a ``gams_sis_poa`` (BD real) por error.

Ejecución:
    SISPOA_INTEGRATION=1 DB_NAME=gams_sis_poa_dev \\
        .venv/bin/python -m pytest apps/catalogos/tests/ -m integration -q
"""
import os

import pytest
from django.conf import settings

INTEGRATION_ENABLED = os.environ.get('SISPOA_INTEGRATION', '0') == '1'


@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    """Modo integración: usa la BD dev sin crear test DB.

    Los tests usan la fixture ``db`` (transaccional): cada test envuelve sus
    escrituras en una transacción que se revierte al final, así la BD dev
    queda intacta tras la corrida.
    """
    if not INTEGRATION_ENABLED:
        # Tests marcados como skip en colección; no se pide esta fixture.
        return
    nombre = settings.DATABASES['default']['NAME']
    if nombre != 'gams_sis_poa_dev':
        raise RuntimeError(
            'Los tests de integración del importador exigen la BD dev: '
            f'DB_NAME=gams_sis_poa_dev (actual: {nombre!r}). '
            'Nunca se ejecutan contra gams_sis_poa.'
        )
    django_db_blocker.unblock()
