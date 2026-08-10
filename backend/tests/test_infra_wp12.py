"""Contratos de infraestructura (WP-12): health, logging y beat."""
import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_ok_con_base_de_datos(db):
    response = APIClient().get('/health/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['base_datos'] == 'ok'
    assert data['sistema'] == 'PIP-GAMS'


@pytest.mark.django_db
def test_health_es_publico(db):
    """El health check no requiere autenticación (monitoreo)."""
    response = APIClient().get('/health/')
    assert response.status_code == 200


def test_beat_schedule_exporta_poa_diario():
    schedule = settings.CELERY_BEAT_SCHEDULE
    assert 'exportar-poa-completo-diario' in schedule
    tarea = schedule['exportar-poa-completo-diario']
    assert tarea['task'] == 'apps.reportes.tasks.exportar_poa_completo_async'
    assert 1 in tarea['schedule'].hour  # 01:00 diario


def test_logging_configurado():
    assert 'console' in settings.LOGGING['handlers']
    assert 'file' in settings.LOGGING['handlers']
    assert settings.LOGGING['handlers']['file']['maxBytes'] > 0
