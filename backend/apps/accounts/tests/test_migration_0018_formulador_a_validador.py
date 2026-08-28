"""Traspaso de FORMULADOR_POAU a VALIDADOR_POAU (migracion 0018).

En una base de desarrollo la migracion no mueve nada porque no hay usuarios con
ese rol; el traspaso solo se ejerce en produccion. Estos casos llaman a la
funcion de la migracion sobre datos armados a mano para que el comportamiento
quede fijado igual, y en particular la trampa que la hace fallar en silencio:
el alcance duplicado que choca contra
`uniq_alcance_usuario_rol_unidad_gestion`.
"""
from datetime import date
from importlib import import_module

import pytest
from django.apps import apps as registro_apps

from apps.accounts.models import AlcanceOrganizacional, Rol, Usuario
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

migracion = import_module(
    'apps.accounts.migrations.0018_formulador_poau_pasa_a_validador',
)


def _traspasar():
    migracion.pasar_a_validador(registro_apps, None)


@pytest.fixture
def escenario(db):
    gestion, _ = GestionFiscal.objects.get_or_create(
        anio=2031, defaults={'estado': 'preparacion'},
    )
    tipo, _ = TipoUnidad.objects.get_or_create(
        codigo='M18-TIPO', defaults={'nombre': 'Tipo 0018', 'nivel': 1},
    )
    unidad = UnidadOrganizacional.objects.create(
        codigo='M18-UO', nombre='Unidad 0018', tipo=tipo, gestion=gestion,
        fecha_vigencia_desde=date(2031, 1, 1),
    )
    formulador, _ = Rol.objects.get_or_create(
        codigo='FORMULADOR_POAU', defaults={'nombre': 'Formulador POAU'},
    )
    validador, _ = Rol.objects.get_or_create(
        codigo='VALIDADOR_POAU', defaults={'nombre': 'Validador POAU'},
    )
    usuario = Usuario.objects.create_user(
        email='m18@test.gob.bo', password='Clave.M18.2031',
    )
    usuario.roles.add(formulador)
    return {
        'gestion': gestion, 'unidad': unidad, 'usuario': usuario,
        'formulador': formulador, 'validador': validador,
    }


def _codigos(usuario):
    return set(usuario.roles.values_list('codigo', flat=True))


def test_el_usuario_queda_como_validador(escenario):
    _traspasar()

    assert _codigos(escenario['usuario']) == {'VALIDADOR_POAU'}


def test_el_alcance_se_reapunta_conservando_unidad_y_gestion(escenario):
    alcance = AlcanceOrganizacional.objects.create(
        usuario=escenario['usuario'], unidad=escenario['unidad'],
        rol=escenario['formulador'],
        scope_type=AlcanceOrganizacional.SCOPE_SELF,
        fiscal_year=escenario['gestion'],
    )

    _traspasar()

    alcance.refresh_from_db()
    assert alcance.rol.codigo == 'VALIDADOR_POAU'
    assert alcance.unidad_id == escenario['unidad'].pk
    assert alcance.fiscal_year_id == escenario['gestion'].pk


def test_no_pisa_un_scope_type_no_normativo(escenario):
    """Un alcance guardado como DESCENDANTS conserva su alcance territorial."""
    alcance = AlcanceOrganizacional.objects.create(
        usuario=escenario['usuario'], unidad=escenario['unidad'],
        rol=escenario['formulador'],
        scope_type=AlcanceOrganizacional.SCOPE_DESCENDANTS,
        fiscal_year=escenario['gestion'],
    )

    _traspasar()

    alcance.refresh_from_db()
    assert alcance.scope_type == AlcanceOrganizacional.SCOPE_DESCENDANTS


def test_el_alcance_duplicado_se_retira_en_vez_de_chocar(escenario):
    """Reapuntar sobre un equivalente violaria la unicidad del alcance."""
    AlcanceOrganizacional.objects.create(
        usuario=escenario['usuario'], unidad=escenario['unidad'],
        rol=escenario['formulador'],
        scope_type=AlcanceOrganizacional.SCOPE_SELF,
        fiscal_year=escenario['gestion'],
    )
    AlcanceOrganizacional.objects.create(
        usuario=escenario['usuario'], unidad=escenario['unidad'],
        rol=escenario['validador'],
        scope_type=AlcanceOrganizacional.SCOPE_SELF,
        fiscal_year=escenario['gestion'],
    )

    _traspasar()

    restantes = AlcanceOrganizacional.objects.filter(
        usuario=escenario['usuario'], unidad=escenario['unidad'],
    )
    assert restantes.count() == 1
    assert restantes.first().rol.codigo == 'VALIDADOR_POAU'


def test_no_toca_a_quien_nunca_fue_formulador(escenario):
    ajeno = Usuario.objects.create_user(
        email='m18-ajeno@test.gob.bo', password='Clave.M18.2031',
    )
    ajeno.roles.add(escenario['validador'])

    _traspasar()

    assert _codigos(ajeno) == {'VALIDADOR_POAU'}


def test_es_idempotente(escenario):
    AlcanceOrganizacional.objects.create(
        usuario=escenario['usuario'], unidad=escenario['unidad'],
        rol=escenario['formulador'],
        scope_type=AlcanceOrganizacional.SCOPE_SELF,
        fiscal_year=escenario['gestion'],
    )

    _traspasar()
    _traspasar()

    assert _codigos(escenario['usuario']) == {'VALIDADOR_POAU'}
    assert AlcanceOrganizacional.objects.filter(
        usuario=escenario['usuario'], rol__codigo='FORMULADOR_POAU',
    ).count() == 0


def test_el_rol_formulador_sigue_existiendo(escenario):
    """La migracion mueve usuarios; no retira el perfil."""
    _traspasar()

    assert Rol.objects.filter(codigo='FORMULADOR_POAU').exists()
