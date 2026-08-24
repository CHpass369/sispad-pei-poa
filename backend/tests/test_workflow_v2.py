"""Contratos del workflow configurable V2 y evaluación SIS-PE (WP-08)."""
from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.gestion.models import GestionFiscal
from apps.accounts.models import Rol, Usuario
from apps.workflow.models_v2 import (
    EstadosTarea,
    WorkflowAprobacion,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowObservacion,
    WorkflowTask,
)
from apps.workflow.services_v2 import (
    aprobar_workflow,
    avanzar_workflow,
    delegar_tarea,
    iniciar_workflow,
    observar_workflow,
    tarea_actual,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def definicion(db):
    return WorkflowDefinition.objects.get(codigo='validacion_instrumento')


@pytest.fixture
def editor(db):
    user = Usuario.objects.create_user(email='editor@wf.gob.bo', password='x')
    rol = Rol.objects.get(codigo='admin_poa')
    user.roles.add(rol)
    return user


@pytest.fixture
def revisor(db):
    user = Usuario.objects.create_user(email='revisor@wf.gob.bo', password='x')
    rol = Rol.objects.get(codigo='revisor_planificacion')
    user.roles.add(rol)
    return user


@pytest.fixture
def lector(db):
    user = Usuario.objects.create_user(email='lector@wf.gob.bo', password='x')
    rol = Rol.objects.get(codigo='consulta')
    user.roles.add(rol)
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# API V2
# ---------------------------------------------------------------------------
def test_definiciones_api(definicion, editor):
    response = _client(editor).get('/api/v2/platform/workflow-definiciones/')
    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 1
    items = data['results']
    assert items[0]['codigo'] == 'validacion_instrumento'
    assert len(items[0]['pasos']) == 5
    assert len(items[0]['transiciones']) == 4


# ---------------------------------------------------------------------------
# Evaluación SIS-PE V2
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason='La API /api/v2/sis-pe/ se retiro junto con el nucleo estrategico (planificacion.Instrumento, VersionInstrumento y TipoInstrumento ya no existen; las rutas devuelven 404). Los tests se conservan como especificacion para cuando se reconstruya SIS-PE.'
)
def test_evaluacion_v2_requiere_auth():
    assert APIClient().get('/api/v2/sis-pe/evaluaciones/').status_code == 401


