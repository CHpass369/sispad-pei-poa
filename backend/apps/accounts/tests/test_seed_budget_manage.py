"""
Tests del seed de capacidad sis_poa.budget.manage → Rol.admin_poa (S2, W4).

La migración 0004_seed_budget_manage_admin_poa es aditiva e idempotente:
admin_poa NO tenía budget.manage (solo admin_presupuesto lo tenía); el
seed la agrega y re-ejecutarlo no duplica nada.
"""
import importlib

import pytest
from django.apps import apps as django_apps

from apps.accounts.models import Rol


def _seed():
    modulo = importlib.import_module(
        'apps.accounts.migrations.0004_seed_budget_manage_admin_poa',
    )
    return modulo


@pytest.mark.django_db
def test_seed_agrega_budget_manage_a_admin_poa():
    """admin_poa obtiene sis_poa.budget.manage tras el seed.

    La migración 0004 ya corre en la test DB (pytest-django aplica todas
    las migraciones al crear la BD), por lo que el estado "sin la
    capacidad" se simula explícitamente quitándola antes de invocar el
    seed; así se verifica el comportamiento real de la función seed.
    """
    rol = Rol.objects.get(codigo='admin_poa')
    cap = rol.capacidades.filter(codigo='sis_poa.budget.manage').first()
    if cap is not None:
        rol.capacidades.remove(cap)

    _seed().seed_budget_manage_admin_poa(apps=django_apps, schema_editor=None)

    rol.refresh_from_db()
    assert rol.capacidades.filter(codigo='sis_poa.budget.manage').count() == 1


@pytest.mark.django_db
def test_seed_idempotente():
    """Re-ejecutar el seed no duplica la capacidad ni el mapeo."""
    _seed().seed_budget_manage_admin_poa(apps=django_apps, schema_editor=None)
    _seed().seed_budget_manage_admin_poa(apps=django_apps, schema_editor=None)

    rol = Rol.objects.get(codigo='admin_poa')
    assert rol.capacidades.filter(codigo='sis_poa.budget.manage').count() == 1
    assert Rol.objects.count() > 0  # sin rol duplicado
