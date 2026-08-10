"""Contratos del dominio de preinversión SIS-PRO (SISPRE / RM 115)."""
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.inversion.models import ProyectoInversion
from apps.inversion.models_preinversion import (
    AprobacionPreinversion,
    ComponenteProyecto,
    CondicionITCP,
    EDTP,
    EstadoCondicion,
    EstadosDocumentoPreinversion,
    GrupoBeneficiario,
    ITCP,
    ItemCostoEDTP,
    FuenteFinanciamientoEDTP,
    PlanOperacionMantenimiento,
    SeccionEDTP,
    TDR,
)
from apps.inversion.models_v2 import (
    EstadosExpedientePreinversion,
    Proyecto,
    TipologiaRM115,
)
from apps.inversion.section_catalog import (
    SECCIONES_COMUNES,
    SECCIONES_TIPO_IV,
    SECCIONES_TIPO_V,
    secciones_para,
)
from apps.inversion.services_preinversion import (
    calcular_madurez,
    clasificar_tipologia,
    construir_paquete_transferencia,
    inicializar_edtp,
    inicializar_itcp,
    validar_edtp_para_aprobacion,
    validar_itcp_para_aprobacion,
)


@pytest.fixture
def formulador(db):
    user = Usuario.objects.create_user(email='formulador@sis-pro.gob.bo', password='x')
    user.roles.add(Rol.objects.get(codigo='revisor_inversion'))
    return user


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


@pytest.fixture
def proyecto(formulador):
    return Proyecto.objects.create(
        codigo_interno='P-PRE-1', nombre='CONST. PUENTE VEHICULAR',
        gestion=2027, responsable=formulador,
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Clasificación RM 115
# ---------------------------------------------------------------------------
def test_clasifica_puente_tipo_ii(proyecto):
    assert clasificar_tipologia(proyecto) == TipologiaRM115.TIPO_II


def test_clasifica_unidad_educativa_tipo_iii(formulador):
    p = Proyecto.objects.create(
        codigo_interno='P-PRE-2', nombre='CONSTRUCCIÓN UNIDAD EDUCATIVA',
        gestion=2027, responsable=formulador,
    )
    assert clasificar_tipologia(p) == TipologiaRM115.TIPO_III


def test_clasifica_software_tipo_iv(formulador):
    p = Proyecto.objects.create(
        codigo_interno='P-PRE-3', nombre='DESARROLLO SOFTWARE GAM',
        gestion=2027, responsable=formulador,
    )
    assert clasificar_tipologia(p) == TipologiaRM115.TIPO_IV


# ---------------------------------------------------------------------------
# Catálogo de secciones por tipología
# ---------------------------------------------------------------------------
def test_secciones_por_tipologia():
    assert secciones_para('IV') == SECCIONES_TIPO_IV
    assert secciones_para('V') == SECCIONES_TIPO_V
    assert secciones_para('III') == SECCIONES_COMUNES
    assert secciones_para('') == SECCIONES_COMUNES


# ---------------------------------------------------------------------------
# ITCP
# ---------------------------------------------------------------------------
def test_inicializa_itcp_con_condiciones_y_tdr(proyecto):
    itcp = inicializar_itcp(proyecto)
    assert itcp.condiciones.count() == 9
    assert itcp.condiciones.filter(critica=True).count() == 8
    assert hasattr(proyecto, 'tdr')
    assert proyecto.estado_preinversion == (
        EstadosExpedientePreinversion.ITCP_ELABORACION
    )


def test_inicializacion_itcp_idempotente(proyecto):
    inicializar_itcp(proyecto)
    inicializar_itcp(proyecto)
    assert ITCP.objects.count() == 1
    assert CondicionITCP.objects.count() == 9


def test_validar_itcp_bloquea_condiciones_criticas(proyecto):
    itcp = inicializar_itcp(proyecto)
    errores = validar_itcp_para_aprobacion(itcp)
    assert any('condiciones críticas' in e for e in errores)


def test_validar_itcp_aprueba(proyecto):
    itcp = inicializar_itcp(proyecto)
    itcp.conclusiones = 'Conclusión'
    itcp.recomendaciones = 'Recomendación'
    itcp.save()
    itcp.condiciones.update(estado=EstadoCondicion.CUMPLE)
    proyecto.tdr.presupuesto_referencial = 50000
    proyecto.tdr.save()
    assert validar_itcp_para_aprobacion(itcp) == []


def test_aprobacion_itcp_exige_tdr_sin_presupuesto(proyecto):
    itcp = inicializar_itcp(proyecto)
    itcp.conclusiones = 'Conclusión'
    itcp.recomendaciones = 'Recomendación'
    itcp.save()
    itcp.condiciones.update(estado=EstadoCondicion.CUMPLE)
    errores = validar_itcp_para_aprobacion(itcp)
    assert any('presupuesto referencial' in e for e in errores)


# ---------------------------------------------------------------------------
# EDTP
# ---------------------------------------------------------------------------
def _proyecto_con_itcp_aprobado(proyecto, tipologia='III'):
    proyecto.tipologia_rm115 = tipologia
    proyecto.save()
    itcp = inicializar_itcp(proyecto)
    itcp.conclusiones = 'C'
    itcp.recomendaciones = 'R'
    itcp.save()
    itcp.condiciones.update(estado=EstadoCondicion.CUMPLE)
    proyecto.tdr.presupuesto_referencial = 800000
    proyecto.tdr.save()
    itcp.estado = EstadosDocumentoPreinversion.APROBADO
    itcp.save()
    return itcp


def test_inicializar_edtp_requiere_itcp_aprobado(proyecto):
    inicializar_itcp(proyecto)
    with pytest.raises(Exception):
        inicializar_edtp(proyecto)


def test_inicializa_edtp_con_secciones_comunes(proyecto):
    _proyecto_con_itcp_aprobado(proyecto, 'III')
    edtp = inicializar_edtp(proyecto)
    assert edtp.secciones.count() == len(SECCIONES_COMUNES)
    assert edtp.secciones.filter(requerida=True).count() == sum(
        1 for _, _, req in SECCIONES_COMUNES if req
    )


def test_inicializa_edtp_tipo_iv_con_secciones_especificas(proyecto):
    _proyecto_con_itcp_aprobado(proyecto, 'IV')
    edtp = inicializar_edtp(proyecto)
    assert edtp.secciones.count() == len(SECCIONES_TIPO_IV)


def test_validar_edtp_bloquea_secciones_faltantes(proyecto):
    _proyecto_con_itcp_aprobado(proyecto)
    edtp = inicializar_edtp(proyecto)
    errores = validar_edtp_para_aprobacion(edtp)
    assert any('secciones obligatorias' in e for e in errores)


def test_validar_edtp_om_cero_sin_justificacion(proyecto):
    _proyecto_con_itcp_aprobado(proyecto)
    edtp = inicializar_edtp(proyecto)
    PlanOperacionMantenimiento.objects.create(edtp=edtp)
    errores = validar_edtp_para_aprobacion(edtp)
    assert any('operación y mantenimiento' in e for e in errores)


def test_validar_edtp_costo_financiamiento_inconsistente(proyecto):
    _proyecto_con_itcp_aprobado(proyecto)
    edtp = inicializar_edtp(proyecto)
    componente = ComponenteProyecto.objects.create(
        proyecto=proyecto, codigo='C1', nombre='Obra civil', presupuesto=100000,
    )
    ItemCostoEDTP.objects.create(
        edtp=edtp, componente=componente, categoria='infraestructura',
        codigo='1.1', descripcion='Item', unidad='m2',
        cantidad=Decimal('2'), precio_unitario=Decimal('50000'),
    )
    FuenteFinanciamientoEDTP.objects.create(
        edtp=edtp, codigo_fuente='41-113', nombre_fuente='CT',
        monto=Decimal('50000'),
    )
    errores = validar_edtp_para_aprobacion(edtp)
    assert any('no coincide' in e for e in errores)


# ---------------------------------------------------------------------------
# Madurez y habilitación POA
# ---------------------------------------------------------------------------
def test_madurez_proyecto_basico(formulador):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-BASIC', nombre='Proyecto básico', gestion=2027,
    )
    puntaje = calcular_madurez(proyecto)
    assert puntaje == Decimal('0')
    assert proyecto.habilitado_poa is False


def test_madurez_completa_habilitada(proyecto):
    proyecto.responsable = proyecto.responsable
    proyecto.problema = 'Problema'
    proyecto.objetivo_general = 'Objetivo'
    proyecto.tipologia_rm115 = 'III'
    proyecto.geom = Point(795000.0, 8075000.0, srid=32719)
    proyecto.distrito = 'D1'
    proyecto.save()
    _proyecto_con_itcp_aprobado(proyecto)
    edtp = inicializar_edtp(proyecto)
    edtp.secciones.update(estado=EstadosDocumentoPreinversion.APROBADO)
    GrupoBeneficiario.objects.create(
        proyecto=proyecto, descripcion='Familias', cantidad=100,
    )
    from apps.inversion.models_preinversion import DocumentoPreinversion
    DocumentoPreinversion.objects.create(
        proyecto=proyecto, tipo_documento='expediente', titulo='Expediente',
    )
    AprobacionPreinversion.objects.create(
        proyecto=proyecto, etapa='EDTP', estado='aprobado',
    )
    proyecto.estado_preinversion = EstadosExpedientePreinversion.EDTP_APROBADO
    proyecto.save()
    puntaje = calcular_madurez(proyecto)
    assert puntaje == Decimal('100')
    assert proyecto.habilitado_poa is True
    assert proyecto.estado_preinversion == (
        EstadosExpedientePreinversion.HABILITADO_POA
    )


def test_madurez_observacion_critica_bloquea(proyecto):
    proyecto.responsable = proyecto.responsable
    proyecto.problema = 'P'
    proyecto.objetivo_general = 'O'
    proyecto.tipologia_rm115 = 'III'
    proyecto.geom = Point(795000.0, 8075000.0, srid=32719)
    proyecto.distrito = 'D1'
    proyecto.save()
    _proyecto_con_itcp_aprobado(proyecto)
    edtp = inicializar_edtp(proyecto)
    edtp.secciones.update(estado=EstadosDocumentoPreinversion.APROBADO)
    from apps.inversion.models_preinversion import ObservacionPreinversion
    ObservacionPreinversion.objects.create(
        proyecto=proyecto, codigo='OBS-1', severidad='critica',
        descripcion='Crítica pendiente',
    )
    proyecto.estado_preinversion = EstadosExpedientePreinversion.EDTP_APROBADO
    proyecto.save()
    calcular_madurez(proyecto)
    assert proyecto.habilitado_poa is False


# ---------------------------------------------------------------------------
# Paquete de transferencia
# ---------------------------------------------------------------------------
def test_paquete_transferencia(proyecto):
    proyecto.problema = 'Problema'
    proyecto.objetivo_general = 'Objetivo'
    proyecto.presupuesto_aprobado = Decimal('850000')
    proyecto.save()
    ComponenteProyecto.objects.create(
        proyecto=proyecto, codigo='C1', nombre='Obra', presupuesto=850000,
    )
    paquete = construir_paquete_transferencia(proyecto)
    assert paquete['project_code'] == 'P-PRE-1'
    assert Decimal(paquete['approved_budget']) == Decimal('850000')
    assert len(paquete['components']) == 1
    assert paquete['schema_version'] == '1.0'


# ---------------------------------------------------------------------------
# API V2
# ---------------------------------------------------------------------------
def test_api_itcp_requiere_auth():
    assert APIClient().get('/api/v2/sis-pro/itcps/').status_code == 401


def test_api_lector_no_puede_inicializar_itcp(lector_pro):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-X', nombre='X', gestion=2027,
    )
    response = _client(lector_pro).post(
        f'/api/v2/sis-pro/proyectos-preinversion/{proyecto.id}/inicializar_itcp/',
        format='json',
    )
    assert response.status_code == 403


def test_api_gestor_inicializa_itcp(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-1', nombre='PUENTE TEST', gestion=2027,
    )
    response = _client(gestor_proyectos).post(
        f'/api/v2/sis-pro/proyectos-preinversion/{proyecto.id}/inicializar_itcp/',
        format='json',
    )
    assert response.status_code == 201
    data = response.json()
    assert data['condiciones'] == 9


def test_api_clasificar(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-2', nombre='CONST. PUENTE VEHICULAR', gestion=2027,
    )
    response = _client(gestor_proyectos).post(
        f'/api/v2/sis-pro/proyectos-preinversion/{proyecto.id}/clasificar/',
        format='json',
    )
    assert response.status_code == 200
    assert response.json()['tipologia_sugerida'] == 'II'
    proyecto.refresh_from_db()
    assert proyecto.tipologia_rm115 == 'II'


def test_api_condiciones_criticas(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-3', nombre='P3', gestion=2027,
    )
    itcp = inicializar_itcp(proyecto)
    response = _client(gestor_proyectos).get(
        '/api/v2/sis-pro/itcp-condiciones/', {'itcp': itcp.id},
    )
    assert response.status_code == 200
    data = response.json()
    resultados = data.get('results', data)
    assert len(resultados) == 9


def test_api_elegibles_poa(gestor_proyectos):
    p1 = Proyecto.objects.create(
        codigo_interno='P-4', nombre='P4', gestion=2027, habilitado_poa=True,
    )
    Proyecto.objects.create(
        codigo_interno='P-5', nombre='P5', gestion=2027, habilitado_poa=False,
    )
    response = _client(gestor_proyectos).get(
        '/api/v2/sis-pro/proyectos-preinversion/elegibles_poa/',
    )
    assert response.status_code == 200
    ids = [item['id'] for item in response.json()]
    assert str(p1.id) in ids
    assert len(ids) == 1


def test_api_paquete_transferencia(gestor_proyectos):
    proyecto = Proyecto.objects.create(
        codigo_interno='P-6', nombre='P6', gestion=2027,
        presupuesto_aprobado=Decimal('100000'),
    )
    response = _client(gestor_proyectos).get(
        f'/api/v2/sis-pro/proyectos-preinversion/{proyecto.id}/paquete_transferencia/',
    )
    assert response.status_code == 200
    assert response.json()['project_code'] == 'P-6'
