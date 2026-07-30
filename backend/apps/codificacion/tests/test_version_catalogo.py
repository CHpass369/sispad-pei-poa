"""Tests del modelo VersionCatalogoPlan (T1.2)."""
import datetime

import pytest
from django.db import IntegrityError

from apps.codificacion.models import VersionCatalogoPlan
from apps.planificacion.models import Plan


def _crear_plan(codigo='PGDESA-TEST', tipo='pgdesa'):
    return Plan.objects.create(
        codigo=codigo,
        nombre='Plan de prueba',
        tipo=tipo,
        gestion_inicio=2026,
        gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )


@pytest.mark.django_db
class TestVersionCatalogoPlan:
    def test_crear_version_borrador_por_defecto(self):
        """Una versión nueva inicia en estado borrador."""
        plan = _crear_plan()
        version = VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)
        assert version.estado == VersionCatalogoPlan.ESTADO_BORRADOR
        assert version.norma_aprobacion == ''
        assert version.plan == plan
        assert version.gestion == 2026

    def test_unique_plan_gestion(self):
        """No puede haber dos versiones del mismo plan para la misma gestión."""
        plan = _crear_plan()
        VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)
        with pytest.raises(IntegrityError):
            VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)

    def test_misma_gestion_en_planes_distintos_es_valida(self):
        """La unicidad es por (plan, gestión): otro plan sí puede usar la gestión."""
        plan_a = _crear_plan(codigo='PLAN-A')
        plan_b = _crear_plan(codigo='PLAN-B', tipo='pdesa')
        VersionCatalogoPlan.objects.create(plan=plan_a, gestion=2026)
        version_b = VersionCatalogoPlan.objects.create(plan=plan_b, gestion=2026)
        assert version_b.pk is not None

    def test_solo_un_vigente_por_plan(self):
        """El partial unique impide dos versiones vigentes para el mismo plan."""
        plan = _crear_plan()
        VersionCatalogoPlan.objects.create(
            plan=plan, gestion=2026, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        )
        with pytest.raises(IntegrityError):
            VersionCatalogoPlan.objects.create(
                plan=plan, gestion=2027, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
            )

    def test_varios_borradores_por_plan_son_validos(self):
        """El partial unique no aplica a borrador: pueden coexistir varios."""
        plan = _crear_plan()
        VersionCatalogoPlan.objects.create(plan=plan, gestion=2026)
        VersionCatalogoPlan.objects.create(plan=plan, gestion=2027)
        assert VersionCatalogoPlan.objects.filter(plan=plan).count() == 2

    def test_vigente_en_planes_distintos_es_valido(self):
        """Cada plan puede tener su propia versión vigente."""
        plan_a = _crear_plan(codigo='PLAN-A')
        plan_b = _crear_plan(codigo='PLAN-B', tipo='pdesa')
        VersionCatalogoPlan.objects.create(
            plan=plan_a, gestion=2026, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        )
        version_b = VersionCatalogoPlan.objects.create(
            plan=plan_b, gestion=2026, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
        )
        assert version_b.estado == VersionCatalogoPlan.ESTADO_VIGENTE

    def test_str(self):
        plan = _crear_plan()
        version = VersionCatalogoPlan.objects.create(
            plan=plan, gestion=2026, estado=VersionCatalogoPlan.ESTADO_VIGENTE,
            norma_aprobacion='Ley 1234',
        )
        assert '2026' in str(version)
        assert 'vigente' in str(version).lower()

    def test_partial_unique_usa_constante_de_estado_vigente(self):
        """La condición del partial unique referencia el estado vigente real.

        Guardia anti-desfase: si cambia el valor de ESTADO_VIGENTE, la
        restricción debe seguirlo (no hay literal duplicado en el modelo).
        """
        constraint = next(
            c for c in VersionCatalogoPlan._meta.constraints
            if c.name == 'uniq_version_catalogo_vigente_por_plan'
        )
        assert dict(constraint.condition.children)['estado'] == (
            VersionCatalogoPlan.ESTADO_VIGENTE
        )
