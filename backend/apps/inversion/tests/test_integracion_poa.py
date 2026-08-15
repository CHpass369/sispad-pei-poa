"""Contrato de integración SIS-PRO -> SIS-POA (IntegracionPoaContract)."""
import uuid

import pytest
from django.core.exceptions import ValidationError

from apps.inversion.models_v2 import Proyecto, VinculoProyectoActividad
from apps.inversion.services.integracion_poa import IntegracionPoaContract
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
)

contrato = IntegracionPoaContract()


@pytest.fixture
def poa_2027(db):
    poa = PoAInstitucional.objects.create(
        gestion=2027, codigo='P-2027', nombre='POA Institucional 2027',
    )
    accion = AccionCortoPlazo.objects.create(
        poa=poa, codigo='ACP-01', nombre='Educación y primera infancia',
    )
    operacion = Operacion.objects.create(
        accion=accion, codigo='OP-01', nombre='Infraestructura educativa',
    )
    Actividad.objects.create(
        operacion=operacion, codigo='ACT-01', nombre='Construcción de aulas',
    )
    Actividad.objects.create(
        operacion=operacion, codigo='ACT-02', nombre='Equipamiento',
    )
    return poa


@pytest.fixture
def proyecto(db):
    return Proyecto.objects.create(
        codigo_interno='P-PRO-1', nombre='CONST. PUENTE VEHICULAR',
        gestion=2027,
    )


def test_actividades_disponibles_filtra_gestion(poa_2027, db):
    otro_poa = PoAInstitucional.objects.create(
        gestion=2028, codigo='P-2028', nombre='POA Institucional 2028',
    )
    accion_28 = AccionCortoPlazo.objects.create(
        poa=otro_poa, codigo='ACP-02', nombre='Deportes',
    )
    operacion_28 = Operacion.objects.create(
        accion=accion_28, codigo='OP-02', nombre='Polideportivo',
    )
    Actividad.objects.create(
        operacion=operacion_28, codigo='ACT-99', nombre='Cancha sintética',
    )

    disponibles = contrato.actividades_poa_disponibles(2027)

    assert len(disponibles) == 2
    assert {a['codigo'] for a in disponibles} == {'ACT-01', 'ACT-02'}
    assert all(a['denominacion'] for a in disponibles)
    assert set(disponibles[0]) == {'id', 'codigo', 'denominacion', 'unidad'}


def test_vincular_proyecto_crea_vinculo(poa_2027, proyecto):
    actividad = Actividad.objects.get(codigo='ACT-01')

    vinculo = contrato.vincular_proyecto_a_actividad(
        proyecto, actividad.id, usuario=None,
    )

    assert vinculo.proyecto_id == proyecto.id
    assert vinculo.actividad_id == actividad.id
    assert vinculo.es_principal is True
    assert VinculoProyectoActividad.objects.count() == 1

    vinculo_2 = contrato.vincular_proyecto_a_actividad(
        proyecto, actividad.id, usuario=None,
    )
    assert vinculo_2.pk == vinculo.pk
    assert VinculoProyectoActividad.objects.count() == 1


def test_vincular_actividad_inexistente_rechaza(proyecto):
    with pytest.raises(ValidationError):
        contrato.vincular_proyecto_a_actividad(proyecto, uuid.uuid4())
    assert VinculoProyectoActividad.objects.count() == 0


def test_contrato_no_escribe_en_poau(poa_2027, proyecto):
    conteos = {
        'poa': PoAInstitucional.objects.count(),
        'accion': AccionCortoPlazo.objects.count(),
        'operacion': Operacion.objects.count(),
        'actividad': Actividad.objects.count(),
    }

    actividad = Actividad.objects.get(codigo='ACT-01')
    contrato.vincular_proyecto_a_actividad(proyecto, actividad.id)

    assert PoAInstitucional.objects.count() == conteos['poa']
    assert AccionCortoPlazo.objects.count() == conteos['accion']
    assert Operacion.objects.count() == conteos['operacion']
    assert Actividad.objects.count() == conteos['actividad']


def test_proyectos_de_actividad_lectura(poa_2027, proyecto):
    actividad = Actividad.objects.get(codigo='ACT-01')

    assert list(contrato.proyectos_de_actividad(actividad.id)) == []

    contrato.vincular_proyecto_a_actividad(proyecto, actividad.id)
    vinculos = list(contrato.proyectos_de_actividad(actividad.id))

    assert len(vinculos) == 1
    assert vinculos[0].proyecto_id == proyecto.id


def test_paquete_transferencia_poa_delega(poa_2027, proyecto):
    paquete = contrato.paquete_transferencia_poa(proyecto)

    assert paquete['project_code'] == 'P-PRO-1'
    assert paquete['management_year'] == 2027
    assert paquete['schema_version'] == '1.0'
