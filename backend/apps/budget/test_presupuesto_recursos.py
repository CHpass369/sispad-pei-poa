"""Tests del Presupuesto General de Recursos.

Escritos despues de que el endpoint fallara en produccion con
`NameError: EstadosTecho`. Ni el build del frontend ni `manage.py check`
detectan un nombre faltante dentro de una vista: solo ejecutarla lo revela.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Usuario
from apps.budget.models import (
    EstadosTecho, OrigenRecurso, RecursoTecho, TechoDirectivo, TechoVersion,
)
from apps.gestion.models import GestionFiscal

RUTA = '/api/v2/sis-poa/budget/directive-ceilings'


@pytest.fixture
def techo(db):
    gestion, _ = GestionFiscal.objects.get_or_create(
        anio=2031,
        defaults={'anio_inicio_plurianual': 2031, 'anio_fin_plurianual': 2035},
    )
    techo = TechoDirectivo.objects.create(
        gestion=gestion, estado=EstadosTecho.BORRADOR, version_actual=1)
    version = TechoVersion.objects.create(
        ceiling=techo, numero=1, estado=EstadosTecho.BORRADOR)
    rubro = RecursoTecho.objects.create(
        version=version, origen=OrigenRecurso.SIGEP, concepto='Coparticipación',
        monto=Decimal('1000.00'), monto_corriente=Decimal('250.00'),
        monto_inversion=Decimal('750.00'), orden=0,
    )
    RecursoTecho.objects.create(
        version=version, origen=OrigenRecurso.SIGEP, concepto='Componente A',
        monto=Decimal('600.00'), padre=rubro, orden=0)
    RecursoTecho.objects.create(
        version=version, origen=OrigenRecurso.SIGEP, concepto='Componente B',
        monto=Decimal('400.00'), padre=rubro, orden=1)
    return techo


@pytest.fixture
def cliente(db):
    usuario = Usuario.objects.create_superuser(
        email='presupuesto@test.gob.bo', password='clave12345')
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


def test_endpoint_responde_y_arma_la_tabla(cliente, techo):
    """Regresion: la vista usaba EstadosTecho sin importarlo y daba 500."""
    r = cliente.get(f'{RUTA}/{techo.id}/presupuesto-recursos/')
    assert r.status_code == 200, r.content
    d = r.json()

    assert len(d['rubros']) == 1
    assert d['editable'] is True

    rubro = d['rubros'][0]
    assert rubro['concepto'] == 'Coparticipación'
    assert len(rubro['componentes']) == 2
    # 250 de 1000 y 750 de 1000.
    assert Decimal(str(rubro['porcentaje_corriente'])) == Decimal('25.00')
    assert Decimal(str(rubro['porcentaje_inversion'])) == Decimal('75.00')
    # El componente se mide contra su grupo, no contra el total general.
    assert Decimal(str(rubro['componentes'][0]['porcentaje'])) == Decimal('60.00')
    assert Decimal(str(d['total']['monto'])) == Decimal('1000.00')


def test_sin_monto_el_porcentaje_viaja_nulo(cliente, techo):
    """La planilla de origen mostraba #DIV/0!; aqui es null y se pinta '—'."""
    version = TechoVersion.objects.get(ceiling=techo, numero=1)
    RecursoTecho.objects.create(
        version=version, origen=OrigenRecurso.SALDO, concepto='Saldo en cero',
        monto=Decimal('0.00'), monto_corriente=Decimal('0.00'),
        monto_inversion=Decimal('0.00'), orden=9)

    r = cliente.get(f'{RUTA}/{techo.id}/presupuesto-recursos/')
    saldo = [x for x in r.json()['rubros'] if x['concepto'] == 'Saldo en cero'][0]
    assert saldo['porcentaje_corriente'] is None
    assert saldo['porcentaje_inversion'] is None


def test_un_techo_fijado_no_es_editable(cliente, techo):
    techo.estado = EstadosTecho.FIJADO
    techo.save(update_fields=['estado'])
    r = cliente.get(f'{RUTA}/{techo.id}/presupuesto-recursos/')
    assert r.json()['editable'] is False


def test_el_corte_debe_cuadrar_con_el_total(db, techo):
    version = TechoVersion.objects.get(ceiling=techo, numero=1)
    recurso = RecursoTecho(
        version=version, origen=OrigenRecurso.SIGEP, concepto='Descuadrado',
        monto=Decimal('100.00'), monto_corriente=Decimal('10.00'),
        monto_inversion=Decimal('20.00'))
    with pytest.raises(Exception, match='no cuadra'):
        recurso.save()


def test_un_componente_no_lleva_corte_propio(db, techo):
    version = TechoVersion.objects.get(ceiling=techo, numero=1)
    padre = version.recursos.get(concepto='Coparticipación')
    hijo = RecursoTecho(
        version=version, origen=OrigenRecurso.SIGEP, concepto='Hijo con corte',
        monto=Decimal('50.00'), padre=padre, monto_corriente=Decimal('50.00'))
    with pytest.raises(Exception, match='rubro agrupador'):
        hijo.save()
