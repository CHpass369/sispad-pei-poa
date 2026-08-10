"""Medición de cobertura WP-13.

Carga Django (GDAL) ANTES de iniciar el tracing de coverage: evita el
WinError 127 de ctypes cuando el tracer está activo durante la carga de
gdal.dll (quirk conocido de CPython).

Uso: python scripts/measure_coverage.py [--fail-under 80]
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('COVERAGE_CORE', 'sysmon')

# Nota: django.setup() ANTES de iniciar el tracing evita el WinError 127 de
# ctypes al cargar gdal.dll con un tracer activo (quirk de CPython en
# Windows). Consecuencia: el código a nivel de módulo (definiciones de
# modelos) no se mide; la lógica de servicios/vistas/adaptadores sí.

import django
django.setup()

import coverage

APP_CRITICOS = [
    'apps.accounts',
    'apps.planificacion',
    'apps.poau',
    'apps.inversion',
    'apps.workflow',
]

TEST_FILES = [
    'tests/test_iam_v2.py',
    'tests/test_sis_pe_kernel.py',
    'tests/test_marco_superior_v2.py',
    'tests/test_migracion_pad_v2.py',
    'tests/test_workflow_v2.py',
    'tests/test_sis_poa_v2.py',
    'tests/test_sis_pro_v2.py',
]

fail_under = 0
if '--fail-under' in sys.argv:
    idx = sys.argv.index('--fail-under')
    fail_under = float(sys.argv[idx + 1])

cov = coverage.Coverage(source=APP_CRITICOS)
cov.start()

import django
django.setup()

import pytest
code = pytest.main(TEST_FILES + ['-q'])

cov.stop()
cov.save()
total = cov.report(show_missing=False)

sys.exit(1 if code != 0 or total < fail_under else 0)
