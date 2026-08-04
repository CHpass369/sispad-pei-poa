from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class TestSeedNormativoClasificadores2026(TransactionTestCase):
    migrate_from = [('catalogos', '0002_objetogasto_nivel_objetogasto_padre_and_more')]
    migrate_to = [('catalogos', '0003_seed_clasificadores_oficiales_2026')]
    hash_valido = 'a' * 64

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def _crear_preexistentes(self, apps):
        Version = apps.get_model('catalogos', 'VersionClasificador')
        comun = {
            'gestion': 2026,
            'norma': 'NORMA PREEXISTENTE INTACTA',
            'fecha_norma': date(2025, 1, 1),
            'procedencia_normativa': 'PROCEDENCIA PREEXISTENTE INTACTA',
            'hash_fuente': self.hash_valido,
            'clasificacion_fuente': 'oficial',
        }
        fuente = Version.objects.create(
            tipo='fuente_financiamiento',
            codigo_fuente='PREEXISTENTE-UNO',
            vigente=True,
            **comun,
        )
        objeto_vigente = Version.objects.create(
            tipo='objeto_gasto',
            codigo_fuente='PREEXISTENTE-MULTIPLE-VIGENTE',
            vigente=True,
            **comun,
        )
        objeto_historico = Version.objects.create(
            tipo='objeto_gasto',
            codigo_fuente='PREEXISTENTE-MULTIPLE-HISTORICO',
            vigente=False,
            **{**comun, 'hash_fuente': 'A' * 64},
        )
        return [fuente.pk, objeto_vigente.pk, objeto_historico.pk]

    def _snapshot(self, apps, ids):
        Version = apps.get_model('catalogos', 'VersionClasificador')
        fields = (
            'id', 'tipo', 'gestion', 'norma', 'fecha_norma', 'codigo_fuente',
            'procedencia_normativa', 'hash_fuente', 'clasificacion_fuente', 'vigente',
        )
        return list(
            Version.objects.filter(pk__in=ids).order_by('codigo_fuente').values(*fields)
        )

    def test_forward_reverse_reapply_es_aditivo_idempotente_y_trazable(self):
        apps_0002 = self._migrate(self.migrate_from)
        preexistentes = self._crear_preexistentes(apps_0002)
        snapshot_original = self._snapshot(apps_0002, preexistentes)

        apps_0003 = self._migrate(self.migrate_to)
        Version = apps_0003.get_model('catalogos', 'VersionClasificador')
        Geografico = apps_0003.get_model('catalogos', 'ClasificadorGeograficoPresupuestario')

        assert self._snapshot(apps_0003, preexistentes) == snapshot_original
        assert Version.objects.filter(codigo_fuente__startswith='SEED-T4-RM249-').count() == 5
        assert Version.objects.get(codigo_fuente='SEED-T4-RM249-INSTITUCIONAL').vigente is True
        assert Version.objects.get(codigo_fuente='SEED-T4-RM249-FUENTE_FINANCIAMIENTO').vigente is False
        assert Version.objects.get(codigo_fuente='SEED-T4-RM249-OBJETO_GASTO').vigente is False
        assert Version.objects.get(codigo_fuente='SEED-T4-CATEGORIA-INCIERTA').vigente is False
        assert Geografico.objects.filter(codigo_fuente='3|5|1').count() == 1
        seed_ids = set(
            Version.objects.filter(codigo_fuente__startswith='SEED-T4-').values_list('pk', flat=True)
        )

        apps_reversa = self._migrate(self.migrate_from)
        VersionReversa = apps_reversa.get_model('catalogos', 'VersionClasificador')
        assert self._snapshot(apps_reversa, preexistentes) == snapshot_original
        assert not VersionReversa.objects.filter(pk__in=seed_ids).exists()

        apps_reaplicada = self._migrate(self.migrate_to)
        VersionReaplicada = apps_reaplicada.get_model('catalogos', 'VersionClasificador')
        assert self._snapshot(apps_reaplicada, preexistentes) == snapshot_original
        assert set(
            VersionReaplicada.objects.filter(codigo_fuente__startswith='SEED-T4-')
            .values_list('pk', flat=True)
        ) == seed_ids
