from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class TestMigracionT4PreservaCatalogosLegacy(TransactionTestCase):
    reset_sequences = False

    migrate_from = [('catalogos', '0001_initial'), ('presupuesto', '0001_initial')]
    migrate_to = [
        ('catalogos', '0002_objetogasto_nivel_objetogasto_padre_and_more'),
        ('presupuesto', '0002_categoriaprogramatica_asignacionpresupuestariaunidad_and_more'),
    ]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        vigencia = date(2025, 1, 1)
        self.legacy = {}
        for model_name, codigo in (
            ('ObjetoGasto', 'LEGACY-OBJ'),
            ('FuenteFinanciamiento', 'LEGACY-FUE'),
            ('OrganismoFinanciador', 'LEGACY-ORG'),
        ):
            model = old_apps.get_model('catalogos', model_name)
            row = model.objects.create(
                codigo=codigo,
                denominacion=f'{model_name} previo',
                gestion=2025,
                fecha_vigencia_desde=vigencia,
                fuente_normativa='Fuente legacy preservada',
            )
            self.legacy[model_name] = (row.pk, codigo)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_ids_codigos_y_linea_presupuestaria_legacy_siguen_disponibles(self):
        for model_name, (pk, codigo) in self.legacy.items():
            model = self.apps.get_model('catalogos', model_name)
            row = model.objects.get(pk=pk)
            assert row.codigo == codigo
            assert row.fuente_normativa == 'Fuente legacy preservada'
            assert row.version_clasificador_id is None

        linea = self.apps.get_model('presupuesto', 'LineaPresupuestaria')
        assert linea._meta.db_table == 'presupuesto_lineapresupuestaria'
