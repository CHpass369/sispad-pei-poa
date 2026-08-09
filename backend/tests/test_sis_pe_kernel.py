"""Contratos del kernel estratégico V2 (WP-04 / SIS-PE)."""
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import Rol, Usuario
from apps.planificacion.models_v2 import (
    EstadosInstrumento,
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    TipoVinculoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
    VinculoEstrategico,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def tipo_pad(db):
    return TipoInstrumento.objects.create(
        codigo='PAD', nombre='Plan Anual de Desarrollo',
        nivel='territorial', horizonte_anios=5,
    )


@pytest.fixture
def metodologia(tipo_pad, db):
    return VersionMetodologia.objects.create(
        codigo='MET-PAD-2027', nombre='Metodología PAD 2027',
        tipo_instrumento=tipo_pad, version='1.0.0',
        estado='publicada',
    )


@pytest.fixture
def tipos_nodo(metodologia, db):
    nivel = TipoNodoEstrategico.objects.create(
        codigo='NIVEL', denominacion='Nivel', metodologia=metodologia,
        nivel_orden=1, permite_hijos=True,
    )
    resultado = TipoNodoEstrategico.objects.create(
        codigo='RESULTADO', denominacion='Resultado', metodologia=metodologia,
        nivel_orden=2, permite_hijos=False,
    )
    return {'nivel': nivel, 'resultado': resultado}


@pytest.fixture
def instrumento(tipo_pad, db):
    return InstrumentoPlanificacion.objects.create(
        tipo=tipo_pad, codigo='PAD-2027', nombre='PAD Municipal 2027',
        periodo_inicio=2027, periodo_fin=2031,
    )


@pytest.fixture
def version(metodologia, instrumento, db):
    return VersionInstrumento.objects.create(
        instrumento=instrumento, numero=1, metodologia=metodologia,
        etiqueta='Borrador inicial',
    )


@pytest.fixture
def usuario_editor(db):
    user = Usuario.objects.create_user(
        email='editor@test.gob.bo', password='test123',
    )
    rol = Rol.objects.get(codigo='admin_poa')
    user.roles.add(rol)
    return user


@pytest.fixture
def usuario_lector(db):
    user = Usuario.objects.create_user(
        email='lector@test.gob.bo', password='test123',
    )
    rol = Rol.objects.get(codigo='consulta')
    user.roles.add(rol)
    return user


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
def test_version_aprobada_es_inmutable(version, tipos_nodo, db, usuario_editor):
    nodo = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='Nivel 1',
    )
    version.aprobar(usuario=usuario_editor, norma='RM 001/2027')
    assert version.inmutable is True
    assert version.checksum

    with pytest.raises(ValidationError):
        nodo.nombre = 'Cambiado tras aprobar'
        nodo.save()

    with pytest.raises(ValidationError):
        version.etiqueta = 'Cambiar etiqueta'
        version.save()


def test_checksum_verifica_datos(version, tipos_nodo, db, usuario_editor):
    NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='Nivel 1',
    )
    version.aprobar(usuario=usuario_editor)
    assert version.verificar_checksum() is True

    # Manipulación directa en DB (bypass de las guards del modelo):
    # el checksum debe detectarla.
    NodoEstrategico.objects.filter(codigo='N1').update(nombre='Alterado')
    assert version.verificar_checksum() is False


def test_nodo_sin_ciclos(version, tipos_nodo, db):
    padre = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='Nivel 1',
    )
    hijo = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['resultado'],
        codigo='R1', nombre='Resultado 1', padre=padre,
    )
    with pytest.raises(ValidationError):
        padre.padre = hijo
        padre.save()


def test_nodo_codigo_unico_por_version(version, tipos_nodo, db):
    NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='Nivel 1',
    )
    with pytest.raises(Exception):
        NodoEstrategico.objects.create(
            version=version, tipo_nodo=tipos_nodo['nivel'],
            codigo='N1', nombre='Duplicado',
        )


def test_tipo_nodo_debe_pertenecer_a_la_metodologia(version, tipos_nodo, db):
    met2 = VersionMetodologia.objects.create(
        codigo='MET-OTRA', nombre='Otra',
        tipo_instrumento=version.metodologia.tipo_instrumento,
    )
    tipo_ajeno = TipoNodoEstrategico.objects.create(
        codigo='AJENA', denominacion='Ajena', metodologia=met2,
    )
    nodo = NodoEstrategico(
        version=version, tipo_nodo=tipo_ajeno,
        codigo='X1', nombre='X',
    )
    with pytest.raises(ValidationError):
        nodo.full_clean()


def test_vinculo_no_autoarticulacion(version, tipos_nodo, db, usuario_editor):
    nodo = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='N1',
    )
    tipo_vinculo = TipoVinculoEstrategico.objects.create(
        codigo='V-NN', denominacion='Nivel-Nivel',
        metodologia=version.metodologia,
        origen_permitido=tipos_nodo['nivel'],
        destino_permitido=tipos_nodo['nivel'],
    )
    vinculo = VinculoEstrategico(
        version=version, origen=nodo, destino=nodo, tipo=tipo_vinculo,
    )
    with pytest.raises(ValidationError):
        vinculo.full_clean()


def test_vinculo_requiere_ponderacion_si_tipo_la_exige(
    version, tipos_nodo, db,
):
    n1 = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'], codigo='N1', nombre='N1',
    )
    n2 = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'], codigo='N2', nombre='N2',
    )
    tipo_vinculo = TipoVinculoEstrategico.objects.create(
        codigo='V-POND', denominacion='Con ponderación',
        metodologia=version.metodologia,
        origen_permitido=tipos_nodo['nivel'],
        destino_permitido=tipos_nodo['nivel'],
        requiere_ponderacion=True,
    )
    vinculo = VinculoEstrategico(
        version=version, origen=n1, destino=n2, tipo=tipo_vinculo,
    )
    with pytest.raises(ValidationError):
        vinculo.full_clean()
    vinculo.ponderacion = 45
    vinculo.full_clean()  # no levanta


# ---------------------------------------------------------------------------
# API V2
# ---------------------------------------------------------------------------
def test_instrumento_requiere_autenticacion():
    assert APIClient().get('/api/v2/sis-pe/instrumentos/').status_code == 401


def test_listar_instrumentos_como_lector(usuario_lector, instrumento):
    response = _client(usuario_lector).get('/api/v2/sis-pe/instrumentos/')
    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 1
    items = data['results']
    assert items[0]['codigo'] == 'PAD-2027'
    assert items[0]['tipo_nombre'] == 'Plan Anual de Desarrollo'


def test_lector_no_puede_crear_instrumento(usuario_lector, tipo_pad):
    response = _client(usuario_lector).post(
        '/api/v2/sis-pe/instrumentos/',
        {
            'tipo': str(tipo_pad.id), 'codigo': 'X', 'nombre': 'X',
            'periodo_inicio': 2027, 'periodo_fin': 2031,
        },
        format='json',
    )
    assert response.status_code == 403


def test_editor_crea_instrumento(usuario_editor, tipo_pad):
    response = _client(usuario_editor).post(
        '/api/v2/sis-pe/instrumentos/',
        {
            'tipo': str(tipo_pad.id), 'codigo': 'PAD-2028', 'nombre': 'PAD 2028',
            'periodo_inicio': 2028, 'periodo_fin': 2032,
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.json()['codigo'] == 'PAD-2028'


def test_crear_version_desde_instrumento(usuario_editor, instrumento, metodologia):
    response = _client(usuario_editor).post(
        f'/api/v2/sis-pe/instrumentos/{instrumento.id}/crear_version/',
        {'metodologia': str(metodologia.id), 'etiqueta': 'V2 borrador'},
        format='json',
    )
    assert response.status_code == 201
    data = response.json()
    assert data['numero'] == 1
    assert data['metodologia'] == str(metodologia.id)


def test_nodos_de_una_version(usuario_editor, version, tipos_nodo):
    NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='Nivel 1',
    )
    response = _client(usuario_editor).get(
        f'/api/v2/sis-pe/versiones/{version.id}/nodos/'
    )
    assert response.status_code == 200
    assert response.json()[0]['codigo'] == 'N1'


def test_aprobar_version_via_api(usuario_editor, version, tipos_nodo):
    NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='Nivel 1',
    )
    response = _client(usuario_editor).post(
        f'/api/v2/sis-pe/versiones/{version.id}/aprobar/',
        {'norma_aprobacion': 'RM 001/2027'},
        format='json',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['inmutable'] is True
    assert data['estado'] == EstadosInstrumento.APROBADO
    assert data['checksum']

    response2 = _client(usuario_editor).post(
        f'/api/v2/sis-pe/versiones/{version.id}/aprobar/',
        format='json',
    )
    assert response2.status_code == 400


def test_verificar_checksum_via_api(usuario_editor, version, tipos_nodo):
    NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'],
        codigo='N1', nombre='N1',
    )
    version.aprobar(usuario=usuario_editor)
    response = _client(usuario_editor).get(
        f'/api/v2/sis-pe/versiones/{version.id}/verificar/'
    )
    assert response.status_code == 200
    assert response.json()['consistente'] is True


def test_vinculo_via_api(usuario_editor, version, tipos_nodo):
    n1 = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'], codigo='N1', nombre='N1',
    )
    n2 = NodoEstrategico.objects.create(
        version=version, tipo_nodo=tipos_nodo['nivel'], codigo='N2', nombre='N2',
    )
    tipo_vinculo = TipoVinculoEstrategico.objects.create(
        codigo='V-NN', denominacion='Nivel-Nivel',
        metodologia=version.metodologia,
        origen_permitido=tipos_nodo['nivel'],
        destino_permitido=tipos_nodo['nivel'],
    )
    response = _client(usuario_editor).post(
        '/api/v2/sis-pe/vinculos/',
        {
            'version': str(version.id),
            'origen': str(n1.id),
            'destino': str(n2.id),
            'tipo': str(tipo_vinculo.id),
            'es_principal': True,
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.json()['origen_codigo'] == 'N1'


@pytest.fixture
def usuario_v2_super(db):
    user = Usuario.objects.create_superuser(
        email='kernel-super@test.gob.bo', password='test123',
    )
    return user


def test_schema_v2_incluye_sis_pe(usuario_v2_super):
    import json
    client = _client(usuario_v2_super)
    response = client.get('/api/v2/schema/', HTTP_ACCEPT='application/json')
    data = json.loads(response.content)
    assert '/api/v2/sis-pe/instrumentos/' in data['paths']
    assert '/api/v2/sis-pe/versiones/' in data['paths']
    assert '/api/v2/sis-pe/vinculos/' in data['paths']
