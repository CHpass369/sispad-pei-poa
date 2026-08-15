"""Flujo maestro SIS-PRO → SIS-POA: POA/POAU ↔ Proyecto (§76).

Test de integración del contrato ``IntegracionPoaContract``: el SIS-PRO
lee la jerarquía operativa del SIS-POA (POA institucional → Acción de
corto plazo → Operación → Actividad) y vincula proyectos a actividades,
sin cruzar la frontera de dominio: SIS-PRO NUNCA escribe en tablas del
SIS-POA (ADR-002 / ADR-010).

Verifica:
  - ``actividades_poa_disponibles(gestion)`` expone las actividades de la
    gestión (y solo de esa gestión);
  - ``vincular_proyecto_a_actividad`` crea el vínculo idempotente;
  - ``proyectos_de_actividad`` devuelve los proyectos vinculados;
  - LÍMITE DE DOMINIO: tras vincular, los modelos de poau no ganan
    registros (conteos de PoAInstitucional/AccionCortoPlazo/Operacion/
    Actividad idénticos antes y después).

Estilo: pytest con fixtures (como test_integracion_poa.py).
"""
import pytest

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
    """Jerarquía operativa SIS-POA de la gestión 2027."""
    poa = PoAInstitucional.objects.create(
        gestion=2027, codigo='P-FLUX-2027', nombre='POA Institucional 2027',
    )
    accion = AccionCortoPlazo.objects.create(
        poa=poa, codigo='ACP-FLUX-01', nombre='Educación y primera infancia',
    )
    operacion = Operacion.objects.create(
        accion=accion, codigo='OP-FLUX-01', nombre='Infraestructura educativa',
    )
    Actividad.objects.create(
        operacion=operacion, codigo='ACT-FLUX-01', nombre='Construcción de aulas',
    )
    Actividad.objects.create(
        operacion=operacion, codigo='ACT-FLUX-02', nombre='Equipamiento',
    )
    return poa


@pytest.fixture
def proyecto(db):
    """Proyecto del SIS-PRO (ciclo de proyectos, apps.inversion)."""
    return Proyecto.objects.create(
        codigo_interno='P-FLUX-1', nombre='CONST. UNIDAD EDUCATIVA FLUJO',
        gestion=2027,
    )


def test_flujo_sispro_poa_completo(poa_2027, proyecto):
    """§76: disponibles → vincular → proyectos_de_actividad, de punta a punta."""
    disponibles = contrato.actividades_poa_disponibles(2027)
    assert len(disponibles) == 2
    assert {a['codigo'] for a in disponibles} == {'ACT-FLUX-01', 'ACT-FLUX-02'}
    assert all(a['denominacion'] for a in disponibles)

    actividad = Actividad.objects.get(codigo='ACT-FLUX-01')
    vinculo = contrato.vincular_proyecto_a_actividad(
        proyecto, actividad.id, usuario=None,
    )
    assert vinculo.proyecto_id == proyecto.id
    assert vinculo.actividad_id == actividad.id
    assert vinculo.es_principal is True

    proyectos = list(contrato.proyectos_de_actividad(actividad.id))
    assert len(proyectos) == 1
    assert proyectos[0].proyecto_id == proyecto.id
    assert proyectos[0].proyecto.codigo_interno == 'P-FLUX-1'


def test_vinculo_no_crea_registros_en_sis_poa(poa_2027, proyecto):
    """§76: SIS-PRO no escribe en SIS-POA — los conteos de poau no cambian."""
    conteos = {
        'poa': PoAInstitucional.objects.count(),
        'accion': AccionCortoPlazo.objects.count(),
        'operacion': Operacion.objects.count(),
        'actividad': Actividad.objects.count(),
    }

    actividad = Actividad.objects.get(codigo='ACT-FLUX-01')
    contrato.vincular_proyecto_a_actividad(proyecto, actividad.id)

    assert PoAInstitucional.objects.count() == conteos['poa']
    assert AccionCortoPlazo.objects.count() == conteos['accion']
    assert Operacion.objects.count() == conteos['operacion']
    assert Actividad.objects.count() == conteos['actividad']
    assert VinculoProyectoActividad.objects.count() == 1

    contrato.vincular_proyecto_a_actividad(proyecto, actividad.id)
    assert VinculoProyectoActividad.objects.count() == 1
    assert PoAInstitucional.objects.count() == conteos['poa']
    assert Actividad.objects.count() == conteos['actividad']


def test_actividades_disponibles_filtran_por_gestion(poa_2027):
    """§76: solo se exponen actividades de la gestión solicitada."""
    poa_2028 = PoAInstitucional.objects.create(
        gestion=2028, codigo='P-FLUX-2028', nombre='POA Institucional 2028',
    )
    accion_28 = AccionCortoPlazo.objects.create(
        poa=poa_2028, codigo='ACP-FLUX-02', nombre='Deportes',
    )
    operacion_28 = Operacion.objects.create(
        accion=accion_28, codigo='OP-FLUX-02', nombre='Polideportivo',
    )
    Actividad.objects.create(
        operacion=operacion_28, codigo='ACT-FLUX-99', nombre='Cancha sintética',
    )

    disponibles_2027 = contrato.actividades_poa_disponibles(2027)
    disponibles_2028 = contrato.actividades_poa_disponibles(2028)

    assert {a['codigo'] for a in disponibles_2027} == {
        'ACT-FLUX-01', 'ACT-FLUX-02',
    }
    assert {a['codigo'] for a in disponibles_2028} == {'ACT-FLUX-99'}
