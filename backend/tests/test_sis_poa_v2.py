"""Contratos del SIS-POA V2 (WP-10)."""
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    OperacionPOAU,
    TareaPOAU,
)
from apps.core.models import LegacyMigrationMap
from apps.poau.migration_v2 import (
    comparar_duplicados_poa,
    importar_poa_v2,
    resumen_presupuesto,
    validar_techo,
)
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
    Tarea,
)
from apps.techos.models import TechoPresupuestario


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def producto_pei(db):
    from apps.articulacion.models import ProductoPEI, ResultadoPEI
    from apps.codificacion.models import EntidadCodificadora

    entidad = EntidadCodificadora.objects.get(codigo='1312')
    resultado = ResultadoPEI.objects.create(
        codigo_resultado='R1', denominacion='Resultado PEI',
        cod_entidad='1312', entidad='GAM Sacaba',
        entidad_codificadora=entidad, vigencia_desde=2027, vigencia_hasta=2031,
        correlativo=1, segmento='01',
    )
    return ProductoPEI.objects.create(
        codigo_producto='PP1', denominacion='Producto PEI',
        resultado_pei=resultado, cod_programa_presup='000', programa_presup='X',
    )


@pytest.fixture
def poa_legacy(producto_pei, db):
    accion = AccionPOA.objects.create(
        codigo_accion='ACP-01', denominacion='Acción corto plazo 1',
        gestion=2027, producto_pei=producto_pei, presupuesto_programado=500000,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='OP-01', denominacion='Operación 1',
        accion_poa=accion,
    )
    actividad = ActividadPOAU.objects.create(
        codigo_actividad='ACT-01', denominacion='Actividad 1',
        operacion=operacion,
    )
    TareaPOAU.objects.create(
        codigo_tarea='TAR-01', denominacion='Tarea 1',
        actividad=actividad,
    )
    return {
        'accion': accion, 'operacion': operacion,
        'actividad': actividad,
    }


@pytest.fixture
def formulador(db):
    user = Usuario.objects.create_user(email='form@sis-poa.gob.bo', password='x')
    user.roles.add(Rol.objects.get(codigo='admin_poa'))
    return user


@pytest.fixture
def lector_poa(db):
    user = Usuario.objects.create_user(email='lector-poa@test.gob.bo', password='x')
    user.roles.add(Rol.objects.get(codigo='consulta'))
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Importación
# ---------------------------------------------------------------------------
def test_importa_jerarquia_poa(poa_legacy):
    resumen = importar_poa_v2()
    assert resumen['creados'] == 4

    poa = PoAInstitucional.objects.get(codigo='P-2027')
    accion = poa.acciones.get(codigo='ACP-01')
    assert float(accion.atributos['presupuesto_programado']) == 500000
    operacion = accion.operaciones.get(codigo='OP-01')
    actividad = operacion.actividades.get(codigo='ACT-01')
    tarea = actividad.tareas.get(codigo='TAR-01')
    assert tarea.nombre == 'Tarea 1'

    # Trazabilidad en el mapa
    assert LegacyMigrationMap.objects.filter(lote='poa').count() == 4
    entrada = LegacyMigrationMap.objects.get(
        app_legacy='articulacion', modelo_legacy='tareapoau',
    )
    assert entrada.estado == LegacyMigrationMap.Estados.MIGRADO


def test_importacion_idempotente(poa_legacy):
    importar_poa_v2()
    importar_poa_v2()
    assert PoAInstitucional.objects.count() == 1
    assert AccionCortoPlazo.objects.count() == 1
    assert Tarea.objects.count() == 1


def test_dry_run_no_escribe(poa_legacy):
    resumen = importar_poa_v2(dry_run=True)
    assert resumen['creados'] == 4
    assert not PoAInstitucional.objects.exists()
    assert not LegacyMigrationMap.objects.exists()


@pytest.fixture
def fuente(db):
    from datetime import date as _date
    from apps.catalogos.models import FuenteFinanciamiento
    from apps.gestion.models import GestionFiscal
    gestion_2027, _ = GestionFiscal.objects.get_or_create(
        anio=2027, defaults={'estado': 'abierta'},
    )
    f, _ = FuenteFinanciamiento.objects.get_or_create(
        codigo='41-113', gestion=gestion_2027,
        defaults={
            'denominacion': 'CT - Coparticipación',
            'fecha_vigencia_desde': _date(2027, 1, 1),
        },
    )
    return f


# ---------------------------------------------------------------------------
# Presupuesto y techos
# ---------------------------------------------------------------------------
def test_resumen_presupuesto(poa_legacy):
    importar_poa_v2()
    poa = PoAInstitucional.objects.get(codigo='P-2027')
    actividad = Tarea.objects.get(codigo='TAR-01').actividad
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='financiera',
        programado=100000, ejecutado=40000,
    )
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='fisica',
        programado=100, ejecutado=50,
    )
    resumen = resumen_presupuesto(poa)
    assert float(resumen['financiera']['programado']) == 100000
    assert float(resumen['financiera']['ejecutado']) == 40000
    assert float(resumen['fisica']['programado']) == 100


def test_validar_techo_dentro(poa_legacy, fuente):
    importar_poa_v2()
    poa = PoAInstitucional.objects.get(codigo='P-2027')
    actividad = Tarea.objects.get(codigo='TAR-01').actividad
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='financiera', programado=80000,
    )
    TechoPresupuestario.objects.create(
        gestion=2027, monto_total=100000, fuente=fuente,
    )
    resultado = validar_techo(poa)
    assert resultado['excede'] is False


def test_validar_techo_excede(poa_legacy, fuente):
    importar_poa_v2()
    poa = PoAInstitucional.objects.get(codigo='P-2027')
    actividad = Tarea.objects.get(codigo='TAR-01').actividad
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='financiera', programado=150000,
    )
    TechoPresupuestario.objects.create(
        gestion=2027, monto_total=100000, fuente=fuente,
    )
    resultado = validar_techo(poa)
    assert resultado['excede'] is True
    assert float(resultado['techo']) == 100000


def test_comparar_duplicados_poa(poa_legacy):
    from datetime import date as _date
    from apps.indicadores.models import Operacion as OpInd, Tarea as TareaInd
    from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
    from apps.planificacion.models import (
        AccionCortoPlazo as AccionLegacy,
        AccionMedianoPlazo,
        NodoPlanificacion,
        Plan,
    )

    plan = Plan.objects.create(
        codigo='PEI-LEG', nombre='PEI', tipo='pei',
        gestion_inicio=2021, gestion_fin=2025,
        fecha_vigencia_desde=_date(2021, 1, 1),
    )
    nodo = NodoPlanificacion.objects.create(
        plan=plan, nivel='accion_mediano', codigo='AMP-1', gestion=2025,
        nombre='AMP',
    )
    amp = AccionMedianoPlazo.objects.create(
        codigo='AMP-1', nombre='AMP', nodo_planificacion=nodo,
        gestion_inicio=2021, gestion_fin=2025,
    )
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='SEC-X', defaults={'nombre': 'Secretaría', 'nivel': 1},
    )
    from apps.gestion.models import GestionFiscal
    gestion_2027, _ = GestionFiscal.objects.get_or_create(
        anio=2027, defaults={'estado': 'abierta'},
    )
    unidad, _ = UnidadOrganizacional.objects.get_or_create(
        codigo='SEC-X-2027', gestion=gestion_2027,
        defaults={
            'nombre': 'Secretaría X', 'tipo': tipo,
            'fecha_vigencia_desde': _date(2027, 1, 1),
        },
    )
    accion = AccionLegacy.objects.create(
        codigo='ACP-01', nombre='Acción 1', accion_mediano_plazo=amp,
        unidad_responsable=unidad, gestion=2027,
    )
    op_ind = OpInd.objects.create(codigo='OP-01', nombre='Operación 1', accion_corto_plazo=accion)
    TareaInd.objects.create(codigo='TAR-01', nombre='Tarea 1', operacion=op_ind)
    reporte = comparar_duplicados_poa()
    assert reporte['operaciones']['coinciden_codigo_y_nombre'] == 1
    assert reporte['tareas']['coinciden_codigo_y_nombre'] == 1


# ---------------------------------------------------------------------------
# API V2
# ---------------------------------------------------------------------------
def test_api_poa_requiere_auth():
    assert APIClient().get('/api/v2/sis-poa/poas/').status_code == 401


@pytest.mark.skip(
    reason='La FK poainstitucional.version_pei la retiro '
           'poau/0006_remove_kernel_v2_fks: la API ya no puede rechazar por '
           'ella. El test se conserva como especificacion para cuando se '
           'reconstruya SIS-PE y el vinculo vuelva.'
)
def test_api_poa_estado_revision_sin_pei_rechazado(formulador):
    client = _client(formulador)
    response = client.post(
        '/api/v2/sis-poa/poas/',
        {
            'gestion': 2027, 'codigo': 'P-2027', 'nombre': 'POA',
            'estado': 'en_revision',
        },
        format='json',
    )
    assert response.status_code == 400
    assert 'version_pei' in response.json()['error']


def test_api_resumen_presupuesto(poa_legacy, formulador):
    importar_poa_v2()
    poa = PoAInstitucional.objects.get(codigo='P-2027')
    actividad = Tarea.objects.get(codigo='TAR-01').actividad
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='financiera', programado=100000,
    )
    response = _client(formulador).get(
        f'/api/v2/sis-poa/poas/{poa.id}/resumen_presupuesto/'
    )
    assert response.status_code == 200
    assert float(response.json()['financiera']['programado']) == 100000


def test_api_validar_techo(poa_legacy, formulador, fuente):
    importar_poa_v2()
    poa = PoAInstitucional.objects.get(codigo='P-2027')
    actividad = Tarea.objects.get(codigo='TAR-01').actividad
    ProgramacionActividad.objects.create(
        actividad=actividad, anio=2027, tipo='financiera', programado=150000,
    )
    TechoPresupuestario.objects.create(gestion=2027, monto_total=100000, fuente=fuente)
    response = _client(formulador).get(
        f'/api/v2/sis-poa/poas/{poa.id}/validar_techo/'
    )
    assert response.status_code == 200
    assert response.json()['excede'] is True


# ---------------------------------------------------------------------------
# Presupuesto y Techos (modulo V2)
# ---------------------------------------------------------------------------


def test_api_techos_listar_y_crear(poa_legacy, formulador, fuente):
    client = _client(formulador)
    response = client.post(
        '/api/v2/sis-poa/techos/',
        {'gestion': 2027, 'monto_total': 200000, 'fuente': str(fuente.id)},
        format='json',
    )
    assert response.status_code == 201
    techo_id = response.json()['id']

    lista = client.get('/api/v2/sis-poa/techos/?gestion=2027')
    assert lista.status_code == 200
    assert lista.json()['count'] == 1
    assert lista.json()['results'][0]['fuente_codigo'] == '41-113'

    borrado = client.delete(f'/api/v2/sis-poa/techos/{techo_id}/')
    assert borrado.status_code == 204


def test_api_techos_lector_solo_lectura(poa_legacy, lector_poa, fuente):
    response = _client(lector_poa).post(
        '/api/v2/sis-poa/techos/',
        {'gestion': 2027, 'monto_total': 200000, 'fuente': str(fuente.id)},
        format='json',
    )
    assert response.status_code == 403


def test_api_techos_deprecacion_blanda(poa_legacy, formulador, fuente):
    """PIP-POA-001: la ruta V2 legacy `techos` responde con headers RFC 8594.

    Deprecación blanda (sin 410): la ruta sigue operativa pero avisa que la
    fuente canónica es `/api/v2/sis-poa/budget/directive-ceilings/`.
    """
    response = _client(formulador).get('/api/v2/sis-poa/techos/?gestion=2027')
    assert response.status_code == 200
    assert response.headers['Deprecation'] == 'true'
    assert response.headers['Sunset'] == 'Sun, 01 Jan 2027 00:00:00 GMT'
    assert 'rel="deprecation"' in response.headers['Link']


def test_api_programaciones_por_poa(poa_legacy, formulador):
    importar_poa_v2()
    poa = PoAInstitucional.objects.get(codigo='P-2027')
    tarea = Tarea.objects.get(codigo='TAR-01')
    ProgramacionActividad.objects.create(
        actividad=tarea.actividad, anio=2027, tipo='financiera',
        programado=100000, ejecutado=40000,
    )
    response = _client(formulador).get(
        f'/api/v2/sis-poa/poas/{poa.id}/programaciones/'
    )
    assert response.status_code == 200
    filas = response.json()['filas']
    assert len(filas) == 1
    assert filas[0]['actividad_codigo'] == 'ACT-01'
    assert float(filas[0]['programado']) == 100000

