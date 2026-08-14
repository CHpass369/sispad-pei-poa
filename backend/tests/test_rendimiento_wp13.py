"""WP-13: control de N+1 y E2E del camino crítico."""
from datetime import date

import pytest
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.codificacion.models import VersionCatalogoPlan
from apps.planificacion.models import Plan
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
    VinculoEstrategico,
)
from apps.sis_poa.models import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
)
from apps.workflow.models_v2 import WorkflowDefinition
from apps.workflow.services_v2 import (
    aprobar_workflow,
    avanzar_workflow,
    iniciar_workflow,
)


@pytest.fixture
def usuario_super(db):
    return Usuario.objects.create_superuser(
        email='super-wp13@test.gob.bo', password='x',
    )


@pytest.fixture
def client_super(usuario_super):
    client = APIClient()
    client.force_authenticate(user=usuario_super)
    return client


def _cadena_v2(usuario):
    """Crea instrumento → versión → nodos → vínculo y la devuelve."""
    tipo = TipoInstrumento.objects.create(
        codigo='PEI', nombre='PEI', nivel='institucional',
    )
    instrumento = InstrumentoPlanificacion.objects.create(
        tipo=tipo, codigo='PEI-CRIT', nombre='PEI crítico',
        periodo_inicio=2027, periodo_fin=2031,
    )
    met = VersionMetodologia.objects.create(
        codigo='MET-CRIT', nombre='Met', tipo_instrumento=tipo,
    )
    version = VersionInstrumento.objects.create(
        instrumento=instrumento, numero=1, metodologia=met,
    )
    tipo_nodo = TipoNodoEstrategico.objects.create(
        codigo='OE', denominacion='Objetivo', metodologia=met,
    )
    n1 = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipo_nodo, codigo='OE-1', nombre='OE 1',
    )
    n2 = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipo_nodo, codigo='OE-2', nombre='OE 2',
    )
    return {'version': version, 'n1': n1, 'n2': n2, 'tipo_nodo': tipo_nodo}


class TestNoNMasUno(TestCase):
    """Lecturas críticas sin N+1 (assertNumQueries)."""

    fixtures = []

    def setUp(self):
        self.user = Usuario.objects.create_superuser(
            email='n1@test.gob.bo', password='x',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.cadena = _cadena_v2(self.user)

        # POA con jerarquía completa + programación
        poa = PoAInstitucional.objects.create(
            gestion=2027, codigo='P-N1', nombre='POA',
            version_pei=self.cadena['version'],
        )
        accion = AccionCortoPlazo.objects.create(poa=poa, codigo='A1', nombre='A1')
        operacion = Operacion.objects.create(accion=accion, codigo='O1', nombre='O1')
        self.actividad = Actividad.objects.create(
            operacion=operacion, codigo='AC1', nombre='AC1',
        )

    def test_listado_instrumentos_sin_n_plus_1(self):
        with self.assertNumQueries(2):
            self.client.get('/api/v2/sis-pe/instrumentos/')

    def test_nodos_de_version_sin_n_plus_1(self):
        version_id = self.cadena['version'].id
        with self.assertNumQueries(2):
            self.client.get(f'/api/v2/sis-pe/versiones/{version_id}/nodos/')

    def test_resumen_presupuesto_poa_sin_n_plus_1(self):
        poa = PoAInstitucional.objects.get(codigo='P-N1')
        with self.assertNumQueries(3):
            self.client.get(f'/api/v2/sis-poa/poas/{poa.id}/resumen_presupuesto/')


@pytest.mark.django_db
def test_e2e_camino_critico(client_super, usuario_super):
    """E2E: identidad → instrumento → versión → nodos → workflow → aprobación."""
    # 1. Identidad y capacidades
    me = client_super.get('/api/v2/me/capabilities/')
    assert me.status_code == 200
    assert 'sis_pe.pad.edit' in me.json()['capabilities']

    # 2. Instrumento
    tipo = TipoInstrumento.objects.create(
        codigo='PAD', nombre='PAD', nivel='territorial',
    )
    response = client_super.post(
        '/api/v2/sis-pe/instrumentos/',
        {
            'tipo': str(tipo.id), 'codigo': 'PAD-E2E', 'nombre': 'PAD E2E',
            'periodo_inicio': 2027, 'periodo_fin': 2031,
        },
        format='json',
    )
    assert response.status_code == 201
    instrumento_id = response.json()['id']

    # 3. Versión con metodología
    met = VersionMetodologia.objects.create(
        codigo='MET-E2E', nombre='Met', tipo_instrumento=tipo,
    )
    response = client_super.post(
        f'/api/v2/sis-pe/instrumentos/{instrumento_id}/crear_version/',
        {'metodologia': str(met.id)},
        format='json',
    )
    assert response.status_code == 201
    version_id = response.json()['id']

    # 4. Nodos
    tipo_nodo = TipoNodoEstrategico.objects.create(
        codigo='LINEA', denominacion='Lineamiento', metodologia=met,
    )
    nodo = client_super.post(
        '/api/v2/sis-pe/nodos/',
        {
            'version': version_id, 'tipo_nodo': str(tipo_nodo.id),
            'codigo': 'L1', 'nombre': 'Lineamiento 1',
        },
        format='json',
    )
    assert nodo.status_code == 201

    # 5. Workflow de validación → aprobación (sincroniza versión)
    version = VersionInstrumento.objects.get(pk=version_id)
    instancia, error = iniciar_workflow(
        'validacion_instrumento', 'VersionInstrumento', version.id, usuario_super,
    )
    assert error is None
    for _ in range(3):  # → formulación → revisión → validado
        ok, err = avanzar_workflow(instancia, usuario_super)
        assert ok, err
    ok, error = aprobar_workflow(
        instancia, usuario_super, 'RM E2E/2027', entidad_destino=version,
    )
    assert ok
    version.refresh_from_db()
    assert version.inmutable is True
    assert version.verificar_checksum() is True

    # 6. POA vinculado a la versión aprobada
    response = client_super.post(
        '/api/v2/sis-poa/poas/',
        {
            'gestion': 2027, 'codigo': 'P-E2E', 'nombre': 'POA E2E',
            'version_pei': str(version_id),
        },
        format='json',
    )
    assert response.status_code == 201
