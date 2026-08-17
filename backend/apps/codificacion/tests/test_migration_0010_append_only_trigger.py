"""Append-only contract for the SIM migration audit tables (migration 0010).

``EjecucionMigracionSIM`` and ``MapeoLineamientoPADLegacy`` are immutable
evidence of the SIM-2027 migration: INSERT is allowed, UPDATE and DELETE are
rejected both by the ORM (manager + model hooks) and by the PostgreSQL
trigger installed by migration 0010.
"""
import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.db.migrations.executor import MigrationExecutor

from apps.codificacion.models import (
    EjecucionMigracionSIM,
    EntidadTerritorialCGEO,
    LineamientoPAD,
    MapeoLineamientoPADLegacy,
    VersionCatalogoPlan,
)
from apps.gestion.models import GestionFiscal
from apps.planificacion.models import Plan

MIGRATE_FROM = ('codificacion', '0009_fuente_normativa_e_idempotencia')
MIGRATE_TO = ('codificacion', '0010_auditoria_migracion_sim')


def _state_at(executor, *nodes):
    """Historical state with every other app at its leaf node."""
    other_leaf_nodes = [
        node for node in executor.loader.graph.leaf_nodes()
        if node[0] != 'codificacion'
    ]
    return executor.loader.project_state(other_leaf_nodes + list(nodes)).apps


def _crear_ejecucion(apps, suffix):
    Ejecucion = apps.get_model('codificacion', 'EjecucionMigracionSIM')
    return Ejecucion.objects.create(
        gestion=2027,
        modo='dry_run',
        manifest_hash='a' * 64,
        manifest={'version': 1, 'gestion': 2027, 'suffix': suffix},
    )


def _crear_lineamiento_pad(apps, suffix):
    Plan = apps.get_model('planificacion', 'Plan')
    VersionCatalogo = apps.get_model('codificacion', 'VersionCatalogoPlan')
    CGEO = apps.get_model('codificacion', 'EntidadTerritorialCGEO')
    Lineamiento = apps.get_model('codificacion', 'LineamientoPAD')
    plan = Plan.objects.create(
        codigo=f'PAD-TRIGGER-{suffix}',
        nombre=f'PAD-TRIGGER-{suffix}',
        tipo='municipal',
        gestion_inicio=2026,
        gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )
    version = VersionCatalogo.objects.create(plan=plan, gestion=2027)
    # Tests with transaction=True flush the whole DB between tests (Django 6
    # TransactionTestCase teardown), so the migration-seeded CGEO row may be
    # gone; create it explicitly to stay deterministic.
    cgeo, _ = CGEO.objects.get_or_create(
        codigo='031001',
        defaults={'nombre': 'Sacaba', 'nivel': 'municipio'},
    )
    return Lineamiento.objects.create(
        codigo='01',
        denominacion='Desarrollo institucional',
        version_catalogo=version,
        entidad_territorial=cgeo,
    )


def _crear_mapeo(apps, suffix):
    Mapeo = apps.get_model('codificacion', 'MapeoLineamientoPADLegacy')
    canonico = _crear_lineamiento_pad(apps, suffix)
    return Mapeo.objects.create(
        origen='articulacion.LineamientoPAD',
        legacy_id=f'legacy-{suffix}',
        codigo_legacy='01',
        denominacion_legacy='Desarrollo institucional',
        lineamiento_pad=canonico,
    )


def _update_directo(tabla, columna, valor, pk):
    with connection.cursor() as cursor:
        cursor.execute(
            f'UPDATE {tabla} SET {columna} = %s WHERE id = %s',
            [valor, pk],
        )


def _delete_directo(tabla, pk):
    with connection.cursor() as cursor:
        cursor.execute(f'DELETE FROM {tabla} WHERE id = %s', [pk])


def _assert_trigger_bloquea_update_y_delete(tabla, columna, update_pk, delete_pk):
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            _update_directo(tabla, columna, 'Alterado con trigger', update_pk)

    with pytest.raises(DatabaseError):
        with transaction.atomic():
            _delete_directo(tabla, delete_pk)


@pytest.mark.django_db(transaction=True)
def test_0010_reverse_y_forward_controlan_trigger_append_only():
    executor = MigrationExecutor(connection)

    try:
        executor.migrate([MIGRATE_TO])
        apps_0010 = _state_at(executor, MIGRATE_TO)
        ejecucion_update = _crear_ejecucion(apps_0010, 'UPDATE')
        ejecucion_delete = _crear_ejecucion(apps_0010, 'DELETE')
        mapeo_update = _crear_mapeo(apps_0010, 'UPDATE')
        mapeo_delete = _crear_mapeo(apps_0010, 'DELETE')

        _assert_trigger_bloquea_update_y_delete(
            'codificacion_ejecucionmigracionsim',
            'modo',
            ejecucion_update.pk,
            ejecucion_delete.pk,
        )
        _assert_trigger_bloquea_update_y_delete(
            'codificacion_mapeolineamientopadlegacy',
            'denominacion_legacy',
            mapeo_update.pk,
            mapeo_delete.pk,
        )

        executor.loader.build_graph()
        executor.migrate([MIGRATE_FROM])
        tablas = set(connection.introspection.table_names())
        assert 'codificacion_ejecucionmigracionsim' not in tablas
        assert 'codificacion_mapeolineamientopadlegacy' not in tablas
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT 1 FROM pg_proc WHERE proname = %s',
                ['codificacion_rechazar_cambio_auditoria_sim'],
            )
            assert cursor.fetchone() is None

        executor.loader.build_graph()
        executor.migrate([MIGRATE_TO])
        apps_reapplied = _state_at(executor, MIGRATE_TO)
        ejecucion_otra = _crear_ejecucion(apps_reapplied, 'REAPP')
        mapeo_otro = _crear_mapeo(apps_reapplied, 'REAPP')

        _assert_trigger_bloquea_update_y_delete(
            'codificacion_ejecucionmigracionsim',
            'modo',
            ejecucion_otra.pk,
            ejecucion_otra.pk,
        )
        _assert_trigger_bloquea_update_y_delete(
            'codificacion_mapeolineamientopadlegacy',
            'denominacion_legacy',
            mapeo_otro.pk,
            mapeo_otro.pk,
        )
    finally:
        # PIP-DB-003: las filas insertadas con modelos históricos (gestion
        # int) quedan con gestion_fk NULL y bloquean el SET NOT NULL de la
        # migración 0013 al migrar a leaf; se limpian antes. TRUNCATE sortea
        # los triggers row-level append-only.
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE codificacion_ejecucionmigracionsim')
            cursor.execute('TRUNCATE codificacion_mapeolineamientopadlegacy')
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.fixture
def canonico_lineamiento(db):
    plan = Plan.objects.create(
        codigo='PAD-ORM-APPEND',
        nombre='PAD-ORM-APPEND',
        tipo='municipal',
        gestion_inicio=2026,
        gestion_fin=2030,
        fecha_vigencia_desde=datetime.date(2026, 1, 1),
    )
    version = VersionCatalogoPlan.objects.create(plan=plan, gestion=2027)
    cgeo, _ = EntidadTerritorialCGEO.objects.get_or_create(
        codigo='031001',
        defaults={'nombre': 'Sacaba', 'nivel': 'municipio'},
    )
    return LineamientoPAD.objects.create(
        codigo='01',
        denominacion='Desarrollo institucional',
        version_catalogo=version,
        entidad_territorial=cgeo,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('gestion_fiscal_2027')
class TestEjecucionMigracionSIMAppendOnlyORM:
    def _crear(self, suffix):
        return EjecucionMigracionSIM.objects.create(
            gestion=GestionFiscal.objects.get(anio=2027),
            modo='dry_run',
            manifest_hash='a' * 64,
            manifest={'version': 1, 'gestion': 2027, 'suffix': suffix},
        )

    def test_creacion_permite_varios_inserts(self):
        primera = self._crear('A')
        segunda = self._crear('B')
        assert EjecucionMigracionSIM.objects.count() == 2
        assert primera.pk != segunda.pk

    def test_append_only_bloquea_update(self):
        ejecucion = self._crear('U')
        ejecucion.modo = 'commit'
        with pytest.raises(ValidationError):
            ejecucion.save()

    def test_append_only_bloquea_delete(self):
        ejecucion = self._crear('D')
        with pytest.raises(ValidationError):
            ejecucion.delete()
        assert EjecucionMigracionSIM.objects.filter(pk=ejecucion.pk).exists()

    def test_append_only_bloquea_queryset_update(self):
        ejecucion = self._crear('QU')
        with pytest.raises(ValidationError):
            EjecucionMigracionSIM.objects.filter(pk=ejecucion.pk).update(
                modo='commit',
            )
        ejecucion.refresh_from_db()
        assert ejecucion.modo == 'dry_run'

    def test_append_only_bloquea_queryset_delete(self):
        ejecucion = self._crear('QD')
        with pytest.raises(ValidationError):
            EjecucionMigracionSIM.objects.filter(pk=ejecucion.pk).delete()
        assert EjecucionMigracionSIM.objects.filter(pk=ejecucion.pk).exists()

    def test_append_only_bloquea_bulk_update(self):
        ejecucion = self._crear('B')
        ejecucion.modo = 'commit'
        with pytest.raises(ValidationError):
            EjecucionMigracionSIM.objects.bulk_update([ejecucion], ['modo'])
        ejecucion.refresh_from_db()
        assert ejecucion.modo == 'dry_run'


@pytest.mark.django_db
class TestMapeoLineamientoPADLegacyAppendOnlyORM:
    def _crear(self, canonico_lineamiento, suffix):
        return MapeoLineamientoPADLegacy.objects.create(
            origen='articulacion.LineamientoPAD',
            legacy_id=f'legacy-{suffix}',
            codigo_legacy='01',
            denominacion_legacy='Desarrollo institucional',
            lineamiento_pad=canonico_lineamiento,
        )

    def test_creacion_permite_varios_inserts(self, canonico_lineamiento):
        primera = self._crear(canonico_lineamiento, 'A')
        segunda = self._crear(canonico_lineamiento, 'B')
        assert MapeoLineamientoPADLegacy.objects.count() == 2
        assert primera.pk != segunda.pk

    def test_append_only_bloquea_update(self, canonico_lineamiento):
        mapeo = self._crear(canonico_lineamiento, 'U')
        mapeo.denominacion_legacy = 'Alterado'
        with pytest.raises(ValidationError):
            mapeo.save()

    def test_append_only_bloquea_delete(self, canonico_lineamiento):
        mapeo = self._crear(canonico_lineamiento, 'D')
        with pytest.raises(ValidationError):
            mapeo.delete()
        assert MapeoLineamientoPADLegacy.objects.filter(pk=mapeo.pk).exists()

    def test_append_only_bloquea_queryset_update(self, canonico_lineamiento):
        mapeo = self._crear(canonico_lineamiento, 'QU')
        with pytest.raises(ValidationError):
            MapeoLineamientoPADLegacy.objects.filter(pk=mapeo.pk).update(
                denominacion_legacy='Alterado',
            )
        mapeo.refresh_from_db()
        assert mapeo.denominacion_legacy == 'Desarrollo institucional'

    def test_append_only_bloquea_queryset_delete(self, canonico_lineamiento):
        mapeo = self._crear(canonico_lineamiento, 'QD')
        with pytest.raises(ValidationError):
            MapeoLineamientoPADLegacy.objects.filter(pk=mapeo.pk).delete()
        assert MapeoLineamientoPADLegacy.objects.filter(pk=mapeo.pk).exists()

    def test_append_only_bloquea_bulk_update(self, canonico_lineamiento):
        mapeo = self._crear(canonico_lineamiento, 'B')
        mapeo.denominacion_legacy = 'Alterado'
        with pytest.raises(ValidationError):
            MapeoLineamientoPADLegacy.objects.bulk_update(
                [mapeo], ['denominacion_legacy'],
            )
        mapeo.refresh_from_db()
        assert mapeo.denominacion_legacy == 'Desarrollo institucional'
