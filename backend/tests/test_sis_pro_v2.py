"""Contratos del SIS-PRO V2 (WP-11)."""
from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.core.models import LegacyMigrationMap
from apps.inversion.migration_v2 import cadena_ascendente, importar_proyectos_v2
from apps.inversion.models import ProyectoInversion
from apps.inversion.models_v2 import (
    CondicionPrevia,
    CostoProyecto,
    DocumentoTecnico,
    FasesProyecto,
    Proyecto,
    VinculoProyectoActividad,
)
from apps.organizacion.models import (
    TipoUnidad,
    UnidadEjecutora,
    UnidadOrganizacional,
)
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    TipoInstrumento,
    VersionInstrumento,
    VersionMetodologia,
)
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def ue(db):
    from apps.organizacion.models import DireccionAdministrativa
    from apps.gestion.models import GestionFiscal
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='UE-T', defaults={'nombre': 'UE', 'nivel': 2},
    )
    gestion_2027, _ = GestionFiscal.objects.get_or_create(
        anio=2027, defaults={'estado': 'abierta'},
    )
    unidad, _ = UnidadOrganizacional.objects.get_or_create(
        codigo='UE-2027', gestion=gestion_2027,
        defaults={
            'nombre': 'Unidad Ejecutora', 'sigla': 'UE',
            'tipo': tipo, 'fecha_vigencia_desde': date(2027, 1, 1),
        },
    )
    da, _ = DireccionAdministrativa.objects.get_or_create(
        codigo='DA-2027', defaults={
            'nombre': 'Dirección', 'gestion': gestion_2027,
            'fecha_vigencia_desde': date(2027, 1, 1),
        },
    )
    ejecutora, _ = UnidadEjecutora.objects.get_or_create(
        codigo='UE-2027', defaults={
            'nombre': 'UE', 'da': da, 'unidad_organizacional': unidad,
            'fecha_vigencia_desde': date(2027, 1, 1), 'gestion': gestion_2027,
        },
    )
    return ejecutora


@pytest.fixture
def fuente_proyecto(db):
    from apps.gestion.models import GestionFiscal
    gestion_2027, _ = GestionFiscal.objects.get_or_create(
        anio=2027, defaults={'estado': 'abierta'},
    )
    f, _ = FuenteFinanciamiento.objects.get_or_create(
        codigo='20-210', gestion=gestion_2027,
        defaults={
            'denominacion': 'Recursos Específicos',
            'fecha_vigencia_desde': date(2027, 1, 1),
        },
    )
    return f


@pytest.fixture
def programa(db):
    from apps.presupuesto.models import ProgramaPresupuestario
    p, _ = ProgramaPresupuestario.objects.get_or_create(
        codigo='000', gestion=2027,
        defaults={'nombre': 'PROGRAMA TEST'},
    )
    return p


@pytest.fixture
def proyecto_legacy(ue, fuente_proyecto, programa, db):
    return ProyectoInversion.objects.create(
        codigo_interno='PROY-001', codigo_sisin='SISIN-2027-01',
        nombre='Proyecto test', ue=ue, programa=programa,
        fuente=fuente_proyecto, costo_total=1000000,
        gestion_inicio=2027, gestion_fin=2028,
    )


@pytest.fixture
def version_pei(db):
    tipo = TipoInstrumento.objects.create(
        codigo='PEI', nombre='PEI', nivel='institucional',
    )
    instrumento = InstrumentoPlanificacion.objects.create(
        tipo=tipo, codigo='PEI-2027', nombre='PEI 2027',
        periodo_inicio=2027, periodo_fin=2031,
    )
    met = VersionMetodologia.objects.create(
        codigo='MET-PEI-P', nombre='Met', tipo_instrumento=tipo,
    )
    return VersionInstrumento.objects.create(
        instrumento=instrumento, numero=1, metodologia=met,
    )


@pytest.fixture
def cadena_poa(version_pei, db):
    poa = PoAInstitucional.objects.create(
        gestion=2027, codigo='P-2027', nombre='POA 2027',
        version_pei=version_pei,
    )
    accion = AccionCortoPlazo.objects.create(poa=poa, codigo='A1', nombre='A1')
    operacion = Operacion.objects.create(accion=accion, codigo='O1', nombre='O1')
    actividad = Actividad.objects.create(operacion=operacion, codigo='AC1', nombre='AC1')
    return {'poa': poa, 'accion': accion, 'operacion': operacion, 'actividad': actividad}


@pytest.fixture
def gestor_proyectos(db):
    user = Usuario.objects.create_user(email='gestor@sis-pro.gob.bo', password='x')
    user.roles.add(Rol.objects.get(codigo='revisor_inversion'))
    return user


@pytest.fixture
def lector_pro(db):
    user = Usuario.objects.create_user(email='lector-pro@test.gob.bo', password='x')
    user.roles.add(Rol.objects.get(codigo='consulta'))
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
def test_proyecto_avanza_fases_secuencialmente(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
    )
    assert proyecto.fase == FasesProyecto.IDEA
    ok, fase = proyecto.avanzar_fase()
    assert ok and fase == FasesProyecto.CONDICIONES_PREVIAS
    ok, fase = proyecto.avanzar_fase()
    assert fase == FasesProyecto.PREINVERSION
    proyecto.fase = FasesProyecto.EVALUACION
    proyecto.save()
    ok, _ = proyecto.avanzar_fase()
    assert ok is False  # fase final


def test_condiciones_costos_documentos(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
    )
    condicion = CondicionPrevia.objects.create(
        proyecto=proyecto, descripcion='Saneamiento',
    )
    assert condicion.cumplida is False
    CostoProyecto.objects.create(
        proyecto=proyecto, concepto='Construcción', monto=500000, anio=2027,
    )
    doc = DocumentoTecnico.objects.create(
        proyecto=proyecto, tipo='edtp', nombre='EDTP',
    )
    assert doc.estado == 'borrador'


# ---------------------------------------------------------------------------
# Cadena ascendente
# ---------------------------------------------------------------------------
def test_cadena_ascendente_completa(cadena_poa, gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='Proyecto', gestion=2027,
    )
    VinculoProyectoActividad.objects.create(
        proyecto=proyecto, actividad=cadena_poa['actividad'],
    )
    pasos = cadena_ascendente(proyecto)
    tipos = [p['tipo'] for p in pasos]
    assert tipos == [
        'proyecto', 'actividad', 'operacion', 'accion_corto_plazo',
        'poa', 'version_pei',
    ]
    assert pasos[-1]['codigo'].startswith('PEI-2027')


# ---------------------------------------------------------------------------
# Importación
# ---------------------------------------------------------------------------
def test_importa_proyectos_legacy(proyecto_legacy):
    resumen = importar_proyectos_v2()
    assert resumen['creados'] == 1
    proyecto = Proyecto.objects.get(codigo_interno='PROY-001')
    assert proyecto.codigo_sisin == 'SISIN-2027-01'
    assert proyecto.costo_total == 1000000
    assert proyecto.fase == FasesProyecto.PREINVERSION
    assert LegacyMigrationMap.objects.filter(lote='sis-pro').count() == 1


def test_importacion_idempotente(proyecto_legacy):
    importar_proyectos_v2()
    importar_proyectos_v2()
    assert Proyecto.objects.count() == 1
    assert LegacyMigrationMap.objects.filter(lote='sis-pro').count() == 1


def test_importacion_dry_run(proyecto_legacy):
    resumen = importar_proyectos_v2(dry_run=True)
    assert resumen['creados'] == 1
    assert not Proyecto.objects.exists()


# ---------------------------------------------------------------------------
# API V2
# ---------------------------------------------------------------------------
def test_api_proyectos_requiere_auth():
    assert APIClient().get('/api/v2/sis-pro/proyectos/').status_code == 401


def test_api_lector_no_puede_crear(lector_pro):
    response = _client(lector_pro).post(
        '/api/v2/sis-pro/proyectos/',
        {'codigo_interno': 'P-X', 'nombre': 'X', 'gestion': 2027},
        format='json',
    )
    assert response.status_code == 403


def test_api_gestor_crea_proyecto(gestor_proyectos):
    response = _client(gestor_proyectos).post(
        '/api/v2/sis-pro/proyectos/',
        {
            'codigo_interno': 'P-2027-1', 'nombre': 'Proyecto salud',
            'gestion': 2027, 'costo_total': 800000,
        },
        format='json',
    )
    assert response.status_code == 201
    data = response.json()
    assert data['fase'] == FasesProyecto.IDEA


def test_api_cadena(cadena_poa, gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
    )
    VinculoProyectoActividad.objects.create(
        proyecto=proyecto, actividad=cadena_poa['actividad'],
    )
    response = _client(gestor_proyectos).get(
        f'/api/v2/sis-pro/proyectos/{proyecto.id}/cadena/'
    )
    assert response.status_code == 200
    assert response.json()[-1]['tipo'] == 'version_pei'


def test_api_avanzar_fase(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
    )
    response = _client(gestor_proyectos).post(
        f'/api/v2/sis-pro/proyectos/{proyecto.id}/avanzar_fase/',
        format='json',
    )
    assert response.status_code == 200
    assert response.json()['fase'] == FasesProyecto.CONDICIONES_PREVIAS


def test_api_avanzar_fase_sin_capacidad(cadena_poa, lector_pro):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
    )
    response = _client(lector_pro).post(
        f'/api/v2/sis-pro/proyectos/{proyecto.id}/avanzar_fase/',
        format='json',
    )
    assert response.status_code == 403


def test_api_presupuesto(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
        costo_total=1000000, ejecucion_acumulada=300000,
    )
    response = _client(gestor_proyectos).get(
        f'/api/v2/sis-pro/proyectos/{proyecto.id}/presupuesto/'
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data['saldo']) == 700000


def test_api_condiciones_y_documentos(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='P1', gestion=2027,
    )
    CondicionPrevia.objects.create(
        proyecto=proyecto, descripcion='Licencia ambiental',
    )
    DocumentoTecnico.objects.create(
        proyecto=proyecto, tipo='itcp', nombre='ITCP',
    )
    client = _client(gestor_proyectos)
    assert len(client.get(
        f'/api/v2/sis-pro/proyectos/{proyecto.id}/condiciones/',
    ).json()) == 1
    assert len(client.get(
        f'/api/v2/sis-pro/proyectos/{proyecto.id}/documentos/',
    ).json()) == 1
