from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class TestSeedNormativoClasificadores2026(TransactionTestCase):
    migrate_from = [('catalogos', '0002_objetogasto_nivel_objetogasto_padre_and_more')]
    migrate_to = [('catalogos', '0003_seed_clasificadores_oficiales_2026')]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(self.migrate_to)
        super().tearDown()

    def test_solo_maestros_confirmados_quedan_vigentes_y_categoria_es_incierta(self):
        VersionClasificador = self.apps.get_model('catalogos', 'VersionClasificador')
        Geografico = self.apps.get_model('catalogos', 'ClasificadorGeograficoPresupuestario')

        vigentes = VersionClasificador.objects.filter(gestion=2026, vigente=True)
        assert set(vigentes.values_list('tipo', flat=True)) == {
            'institucional',
            'objeto_gasto',
            'fuente_financiamiento',
            'organismo_financiador',
            'geografico_presupuestario',
        }
        assert set(vigentes.values_list('clasificacion_fuente', flat=True)) == {'oficial'}
        assert set(vigentes.values_list('norma', flat=True)) == {'RM MEFP N.º 249/2025'}

        categoria = VersionClasificador.objects.get(
            tipo='categoria_programatica', gestion=2026
        )
        assert categoria.vigente is False
        assert categoria.clasificacion_fuente == 'incierta'
        assert categoria.codigo_fuente == 'PENDIENTE-DIRECTRICES-SIGEP-2026'

        geografia = Geografico.objects.get(codigo_fuente='3|5|1')
        assert (geografia.departamento, geografia.provincia, geografia.municipio) == ('3', '5', '1')
        assert geografia.procedencia_normativa == 'Clasificadores 2026, PDF pp. 155, 159'
