"""Contratos del workflow configurable V2 y evaluación SIS-PE (WP-08)."""
from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
)
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


@pytest.fixture
def version_instrumento(db):
    tipo = TipoInstrumento.objects.create(
        codigo='PAD', nombre='PAD', nivel='territorial',
    )
    instrumento = InstrumentoPlanificacion.objects.create(
        tipo=tipo, codigo='PAD-TEST', nombre='PAD test',
        periodo_inicio=2027, periodo_fin=2031,
    )
    met = VersionMetodologia.objects.create(
        codigo='MET-TEST', nombre='Met', tipo_instrumento=tipo,
    )
    version = VersionInstrumento.objects.create(
        instrumento=instrumento, numero=1, metodologia=met,
    )
    return version


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------
def test_iniciar_workflow_crea_instancia_y_tarea(definicion, editor, version_instrumento):
    instancia, error = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    assert error is None
    assert instancia.estado_actual == 'borrador'
    assert not instancia.cerrado
    tarea = tarea_actual(instancia)
    assert tarea.estado == EstadosTarea.EN_CURSO


def test_iniciar_workflow_definicion_inexistente(editor, version_instrumento):
    instancia, error = iniciar_workflow(
        'no-existe', 'VersionInstrumento', version_instrumento.id, editor,
    )
    assert instancia is None
    assert 'no encontrada' in error


def test_avanzar_workflow_requiere_capacidad(definicion, lector, editor, version_instrumento):
    instancia, _ = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    ok, error = avanzar_workflow(instancia, lector)
    assert not ok
    assert 'capacidades' in error
    assert instancia.estado_actual == 'borrador'


def test_avanzar_workflow_avanza_estados(definicion, editor, version_instrumento):
    instancia, _ = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    ok, _ = avanzar_workflow(instancia, editor)  # borrador → en_formulacion
    assert ok
    assert instancia.estado_actual == 'en_formulacion'
    ok, _ = avanzar_workflow(instancia, editor)  # → en_revision
    assert instancia.estado_actual == 'en_revision'
    assert WorkflowTask.objects.filter(instancia=instancia).count() == 3


def test_observar_workflow_rechaza_tarea(definicion, revisor, editor, version_instrumento):
    instancia, _ = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    avanzar_workflow(instancia, editor)
    avanzar_workflow(instancia, editor)  # en_revision

    ok, error = observar_workflow(
        instancia, revisor, 'Falta desagregación territorial', 'alta',
    )
    assert ok
    assert error is None
    assert WorkflowObservacion.objects.filter(instancia=instancia).count() == 1
    obs = WorkflowObservacion.objects.get(instancia=instancia)
    assert obs.severidad == 'alta'
    assert instancia.estado_actual == 'en_revision'  # sigue en el mismo paso
    assert tarea_actual(instancia) is not None  # nueva tarea de subsanación


def test_aprobar_workflow_cierra_y_sincroniza_version(
    definicion, revisor, editor, version_instrumento,
):
    instancia, _ = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    # editor avanza formulación y revisión; revisor valida y aprueba
    for _ in range(2):
        avanzar_workflow(instancia, editor)
    assert instancia.estado_actual == 'en_revision'
    avanzar_workflow(instancia, revisor)  # → validado (pad.validate)
    assert instancia.estado_actual == 'validado'

    ok, error = aprobar_workflow(
        instancia, revisor, 'RM 1/2027', entidad_destino=version_instrumento,
    )
    assert ok
    assert error is None
    assert instancia.cerrado is True
    assert instancia.estado_actual == 'aprobado'

    # Sincronización con el kernel: versión inmutable con checksum
    version_instrumento.refresh_from_db()
    assert version_instrumento.inmutable is True
    assert version_instrumento.estado == 'aprobado'
    assert version_instrumento.checksum
    assert WorkflowAprobacion.objects.filter(
        instancia=instancia, resultado='aprobado',
    ).count() == 1


def test_una_sola_instancia_abierta_por_entidad(definicion, editor, version_instrumento):
    iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    instancia2, error = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    assert instancia2 is None
    assert error


def test_delegar_tarea(definicion, editor, lector, version_instrumento):
    instancia, _ = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    tarea = tarea_actual(instancia)
    delegacion = delegar_tarea(tarea, editor, lector, motivo='Suplencia')
    assert delegacion.delegado_a == lector
    tarea.refresh_from_db()
    assert tarea.asignado_a == lector


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


def test_iniciar_instancia_api(definicion, editor, version_instrumento):
    response = _client(editor).post(
        '/api/v2/platform/workflow-instancias/',
        {
            'definicion': 'validacion_instrumento',
            'entidad_tipo': 'VersionInstrumento',
            'entidad_id': str(version_instrumento.id),
        },
        format='json',
    )
    assert response.status_code == 201
    data = response.json()
    assert data['estado_actual'] == 'borrador'
    assert data['tarea_actual']['estado'] == 'en_curso'


def test_avanzar_api_sin_capacidad(definicion, lector, editor, version_instrumento):
    iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    instancia = WorkflowInstance.objects.get(entidad_id=version_instrumento.id)
    response = _client(lector).post(
        f'/api/v2/platform/workflow-instancias/{instancia.id}/avanzar/',
        format='json',
    )
    assert response.status_code == 403


def test_observar_api(definicion, revisor, editor, version_instrumento):
    iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    instancia = WorkflowInstance.objects.get(entidad_id=version_instrumento.id)
    response = _client(revisor).post(
        f'/api/v2/platform/workflow-instancias/{instancia.id}/observar/',
        {'texto': 'Observación API', 'severidad': 'bloqueante'},
        format='json',
    )
    assert response.status_code == 200
    assert WorkflowObservacion.objects.filter(texto='Observación API').exists()


def test_tareas_mias_api(definicion, editor, version_instrumento):
    iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento',
        version_instrumento.id, editor,
    )
    response = _client(editor).get(
        '/api/v2/platform/workflow-tareas/?mias=true'
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1


# ---------------------------------------------------------------------------
# Evaluación SIS-PE V2
# ---------------------------------------------------------------------------
def test_evaluacion_v2_vinculada_a_version(editor, version_instrumento):
    response = _client(editor).post(
        '/api/v2/sis-pe/evaluaciones/',
        {
            'version_instrumento': str(version_instrumento.id),
            'fiscal_year': 2027,
            'evaluation_type': 'medio_termino',
            'period': 'AN',
            'status': 'borrador',
            'conclusions': 'En curso',
        },
        format='json',
    )
    assert response.status_code == 201
    data = response.json()
    assert data['version_instrumento'] == str(version_instrumento.id)


def test_evaluacion_v2_requiere_auth(version_instrumento):
    assert APIClient().get('/api/v2/sis-pe/evaluaciones/').status_code == 401


def test_evaluacion_v2_lector_solo_lectura(lector, editor, version_instrumento):
    _client(editor).post(
        '/api/v2/sis-pe/evaluaciones/',
        {
            'version_instrumento': str(version_instrumento.id),
            'fiscal_year': 2027,
            'evaluation_type': 'anual',
            'period': 'AN',
            'status': 'borrador',
        },
        format='json',
    )
    response = _client(lector).post(
        '/api/v2/sis-pe/evaluaciones/',
        {
            'fiscal_year': 2028,
            'evaluation_type': 'anual',
            'period': 'AN',
        },
        format='json',
    )
    assert response.status_code == 403
