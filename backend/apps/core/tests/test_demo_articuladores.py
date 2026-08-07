import io
import json
import re
from copy import deepcopy
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    AsignacionObjetoGasto,
    OperacionPOAU,
    SeguimientoPresupuesto,
    TareaPOAU,
)
from apps.core.models import DemoDatasetManifest
from apps.core.tests.demo_source_fixture import DemoSourceWorkbookMixin
from apps.poau.models import EjecucionFinanciera, EjecucionFisica, POAU, POAUActividad
from apps.presupuesto.models import AsignacionPresupuestariaUnidad, LineaPresupuestaria
from apps.seguimiento.models import EntradaSeguimiento, ReporteSeguimiento


GESTION = 2027
NAMESPACE = 'demo-articuladores-numericos-v2'
NUMERIC_CODE = re.compile(r'^\d+(?:\.\d+)*$')


def run_command(source_file, *args):
    output = io.StringIO()
    call_command(
        'cargar_demo_articuladores',
        '--source-file',
        str(source_file),
        *args,
        stdout=output,
    )
    return json.loads(output.getvalue())


class DemoArticuladoresDryRunTests(DemoSourceWorkbookMixin, TestCase):
    def test_default_dry_run_reports_excel_contract_without_writes(self):
        before = {
            'actions': AccionPOA.objects.count(),
            'activities': ActividadPOAU.objects.count(),
            'manifests': DemoDatasetManifest.objects.count(),
        }

        result = run_command(self.source_file)

        self.assertEqual(result['mode'], 'dry-run')
        self.assertEqual(result['gestion'], GESTION)
        self.assertEqual(result['source_counts'], {
            'acciones': 1,
            'operaciones': 1,
            'actividades': 19,
            'tareas': 139,
            'programaciones_fisicas': 228,
        })
        self.assertEqual(AccionPOA.objects.count(), before['actions'])
        self.assertEqual(ActividadPOAU.objects.count(), before['activities'])
        self.assertEqual(DemoDatasetManifest.objects.count(), before['manifests'])


class DemoArticuladoresCommitTests(DemoSourceWorkbookMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_result = run_command(cls.source_file, '--commit', '--refresh')
        cls.admin = get_user_model().objects.create_superuser(
            email='admin-demo-2027@example.invalid',
            password='test-only-password',
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_reuses_exact_operational_shape_and_preserves_legacy_source_codes(self):
        self.assertEqual(AccionPOA.objects.filter(gestion=GESTION).count(), 1)
        self.assertEqual(
            OperacionPOAU.objects.filter(accion_poa__gestion=GESTION).count(), 1,
        )
        self.assertEqual(
            ActividadPOAU.objects.filter(operacion__accion_poa__gestion=GESTION).count(),
            19,
        )
        self.assertEqual(
            TareaPOAU.objects.filter(
                actividad__operacion__accion_poa__gestion=GESTION,
            ).count(),
            139,
        )
        self.assertEqual(POAUActividad.objects.filter(poau__gestion=GESTION).count(), 19)
        self.assertEqual(
            EjecucionFisica.objects.filter(actividad__poau__gestion=GESTION).count(),
            228,
        )

        operation = OperacionPOAU.objects.get(accion_poa__gestion=GESTION)
        first_activity = operation.actividades.order_by('correlativo').first()
        first_task = first_activity.tareas.order_by('correlativo').first()
        self.assertEqual(operation.estado, 'PROVISIONAL')
        self.assertTrue(operation.codigo_fuente.startswith('SIM-2027-'))
        self.assertTrue(first_activity.codigo_fuente.startswith('SIM-2027-'))
        self.assertTrue(first_task.codigo_fuente.startswith('SIM-2027-'))
        self.assertRegex(operation.codigo_operacion, NUMERIC_CODE)
        self.assertRegex(first_activity.codigo_actividad, NUMERIC_CODE)
        self.assertRegex(first_task.codigo_tarea, NUMERIC_CODE)
        self.assertIn('servicios de asesoramiento jurídico', operation.denominacion.lower())
        self.assertNotIn('demostración', operation.denominacion.lower())

    def test_budget_uses_multiple_classifier_objects_and_coherent_amounts(self):
        canonical = AsignacionPresupuestariaUnidad.objects.filter(gestion=GESTION)
        legacy = AsignacionObjetoGasto.objects.filter(gestion=GESTION)

        self.assertEqual(canonical.count(), 6)
        self.assertEqual(legacy.count(), 6)
        self.assertEqual(LineaPresupuestaria.objects.filter(gestion=GESTION).count(), 6)
        self.assertEqual(canonical.values('objeto_gasto__codigo').distinct().count(), 6)
        self.assertEqual(
            {assignment.nivel_operativo for assignment in canonical},
            {'operacion', 'actividad', 'tarea'},
        )
        for assignment in canonical:
            with self.subTest(assignment=assignment.pk):
                self.assertLessEqual(assignment.monto_ejecutado, assignment.monto_vigente)
                self.assertEqual(assignment.objeto_gasto.version_clasificador.codigo_fuente, '2026')
        self.assertTrue(all(row.estado == 'PROVISIONAL' for row in legacy))

    def test_tracking_reuses_physical_rows_and_adds_monthly_financial_series(self):
        self.assertEqual(
            EjecucionFisica.objects.filter(actividad__poau__gestion=GESTION).count(),
            228,
        )
        self.assertEqual(
            EjecucionFinanciera.objects.filter(actividad__poau__gestion=GESTION).count(),
            228,
        )
        self.assertEqual(ReporteSeguimiento.objects.filter(gestion=GESTION).count(), 12)
        self.assertEqual(
            EntradaSeguimiento.objects.filter(reporte__gestion=GESTION).count(),
            228,
        )
        for execution in EjecucionFinanciera.objects.filter(actividad__poau__gestion=GESTION):
            with self.subTest(execution=execution.pk):
                self.assertLessEqual(execution.ejecutado, execution.programado)

    def test_screen_api_contracts_return_2027_visible_fields(self):
        contracts = {
            '/api/v1/articulacion/matrices/m1_pad_pei/?gestion=2027': (
                1, {
                    'codigo_resultado_pad', 'resultado_pad', 'codigo_producto_pad',
                    'producto_pad', 'codigo_resultado_pei', 'resultado_pei',
                    'codigo_producto_pei', 'producto_pei', 'estado',
                }
            ),
            '/api/v1/articulacion/matrices/m2_pei_poa/?gestion=2027': (
                1, {'codigo_accion', 'denominacion', 'producto_pei_nombre', 'gestion'}
            ),
            '/api/v1/articulacion/matrices/m3_poa_poau/?gestion=2027': (
                1, {'codigo_operacion', 'denominacion', 'actividades', 'estado'}
            ),
            '/api/v1/articulacion/matrices/m4_presupuesto/?gestion=2027': (
                6, {
                    'id_cadena', 'accion_poa_nombre', 'operacion_nombre',
                    'actividad_nombre', 'categoria_programatica', 'da', 'ue',
                    'programa', 'modificaciones', 'ejecutado_total',
                    'porcentaje_ejecucion_fisica', 'eficacia', 'gestion',
                }
            ),
            '/api/v1/articulacion/matrices/m5_objetos_gasto/?gestion=2027': (
                6, {
                    'cod_objeto_gasto', 'actividad_nombre', 'grupo_gasto',
                    'tipo_gasto', 'fuente_financiamiento', 'organismo_financiador',
                    'categoria_programatica', 'da', 'ue', 'justificacion',
                    'monto_ejecutado', 'gestion',
                }
            ),
        }
        for url, (expected_count, expected_fields) in contracts.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                rows = response.json()
                self.assertEqual(len(rows), expected_count)
                self.assertTrue(expected_fields.issubset(rows[0]))

        m3 = self.client.get(
            '/api/v1/articulacion/matrices/m3_poa_poau/?gestion=2027',
        ).json()[0]
        self.assertEqual(len(m3['actividades']), 19)
        self.assertEqual(sum(len(a['tareas']) for a in m3['actividades']), 139)

        m1 = self.client.get(
            '/api/v1/articulacion/matrices/m1_pad_pei/?gestion=2027',
        ).json()[0]
        self.assertEqual(m1['codigo_resultado_pad'], m1['cod_resultado_pad'])
        self.assertEqual(m1['codigo_producto_pad'], m1['cod_producto_pad'])
        self.assertEqual(m1['codigo_resultado_pei'], m1['cod_resultado_pei'])
        self.assertEqual(m1['codigo_producto_pei'], m1['cod_producto_pei'])

        m4 = self.client.get(
            '/api/v1/articulacion/matrices/m4_presupuesto/?gestion=2027',
        ).json()
        self.assertEqual({row['gestion'] for row in m4}, {GESTION})
        self.assertEqual(
            sum(Decimal(row['presupuesto_inicial']) for row in m4),
            Decimal('285000.00'),
        )
        self.assertEqual(
            sum(Decimal(row['presupuesto_vigente']) for row in m4),
            Decimal('278000.00'),
        )
        self.assertEqual(
            sum(Decimal(row['ejecutado_total']) for row in m4),
            Decimal('162000.00'),
        )

        m5 = self.client.get(
            '/api/v1/articulacion/matrices/m5_objetos_gasto/?gestion=2027',
        ).json()
        self.assertEqual({row['gestion'] for row in m5}, {GESTION})
        self.assertEqual(
            sum(Decimal(row['monto_programado']) for row in m5),
            Decimal('285000.00'),
        )
        self.assertEqual(
            sum(Decimal(row['monto_vigente']) for row in m5),
            Decimal('278000.00'),
        )
        self.assertEqual(
            sum(Decimal(row['monto_ejecutado']) for row in m5),
            Decimal('162000.00'),
        )

    def test_dashboard_and_follow_up_contracts_use_2027(self):
        budget = self.client.get('/api/v1/dashboard/presupuesto/', {'gestion': 2027})
        self.assertEqual(budget.status_code, 200)
        self.assertGreater(budget.json()['formulado'], 0)
        self.assertEqual(len(budget.json()['programas']), 1)

        tracking = self.client.get('/api/v1/entradas/dashboard/', {'gestion': 2027})
        self.assertEqual(tracking.status_code, 200)
        self.assertEqual(tracking.json()['gestion'], 2027)
        self.assertEqual(tracking.json()['total_actividades'], 228)

        semaphore = self.client.get('/api/v1/entradas/semaforo/', {'gestion': 2027})
        self.assertEqual(semaphore.status_code, 200)
        self.assertEqual(semaphore.json()['resumen']['total'], 228)

    def test_budget_follow_up_export_resolves_for_2027(self):
        response = self.client.get(
            '/api/v1/reportes/articulacion_presupuesto_seguimiento/',
            {'gestion': GESTION},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('2027', response['Content-Disposition'])

    def test_manifest_records_owned_and_reused_rows_and_second_refresh_is_idempotent(self):
        manifest = DemoDatasetManifest.objects.get(namespace=NAMESPACE)
        self.assertEqual(manifest.gestion, GESTION)
        self.assertIn('owned', manifest.payload['ownership'])
        self.assertIn('reused', manifest.payload['ownership'])
        self.assertIn('source_counts', manifest.payload)

        counts_before = {
            'activities': ActividadPOAU.objects.filter(
                operacion__accion_poa__gestion=GESTION,
            ).count(),
            'tasks': TareaPOAU.objects.filter(
                actividad__operacion__accion_poa__gestion=GESTION,
            ).count(),
            'physical': EjecucionFisica.objects.filter(
                actividad__poau__gestion=GESTION,
            ).count(),
            'financial': EjecucionFinanciera.objects.filter(
                actividad__poau__gestion=GESTION,
            ).count(),
        }

        second = run_command(self.source_file, '--commit', '--refresh')

        self.assertEqual(second['created_total'], 0)
        self.assertEqual(counts_before['activities'], 19)
        self.assertEqual(counts_before['tasks'], 139)
        self.assertEqual(counts_before['physical'], 228)
        self.assertEqual(counts_before['financial'], 228)
        self.assertEqual(
            EjecucionFinanciera.objects.filter(actividad__poau__gestion=GESTION).count(),
            counts_before['financial'],
        )

    def _remove_owned_id(self, obj):
        manifest = DemoDatasetManifest.objects.get(namespace=NAMESPACE)
        payload = deepcopy(manifest.payload)
        model_ids = payload['ownership']['owned'][obj._meta.label]
        model_ids.remove(str(obj.pk))
        manifest.payload = payload
        manifest.save(update_fields=['payload', 'updated_at'])

    def test_refresh_rejects_foreign_segmented_row_with_demo_numeric_code(self):
        action = AccionPOA.objects.get(gestion=GESTION)
        self._remove_owned_id(action)
        action.codigo_fuente = 'FOREIGN-POA-2027'
        action.denominacion = 'Acción ajena que debe conservarse'
        action.save(update_fields=['codigo_fuente', 'denominacion', 'updated_at'])

        with self.assertRaisesMessage(CommandError, 'no pertenece al demo'):
            run_command(self.source_file, '--commit', '--refresh')

        action.refresh_from_db()
        self.assertEqual(action.codigo_fuente, 'FOREIGN-POA-2027')
        self.assertEqual(action.denominacion, 'Acción ajena que debe conservarse')

    def test_refresh_rejects_foreign_poau_with_demo_numeric_code(self):
        poau = POAU.objects.get(gestion=GESTION)
        self._remove_owned_id(poau)
        poau.nombre = 'POAU ajeno que debe conservarse'
        poau.descripcion = 'Datos institucionales ajenos al demo'
        poau.save(update_fields=['nombre', 'descripcion', 'updated_at'])

        with self.assertRaisesMessage(CommandError, 'no pertenece al demo'):
            run_command(self.source_file, '--commit', '--refresh')

        poau.refresh_from_db()
        self.assertEqual(poau.nombre, 'POAU ajeno que debe conservarse')
        self.assertEqual(poau.descripcion, 'Datos institucionales ajenos al demo')

    def test_refresh_migrates_unambiguous_legacy_poau_rows_to_owned(self):
        poau = POAU.objects.get(gestion=GESTION)
        activity_ids = list(
            POAUActividad.objects.filter(poau=poau).values_list('pk', flat=True)
        )
        self._remove_owned_id(poau)
        manifest = DemoDatasetManifest.objects.get(namespace=NAMESPACE)
        payload = deepcopy(manifest.payload)
        payload['ownership']['owned']['poau.POAUActividad'] = []
        manifest.payload = payload
        manifest.save(update_fields=['payload', 'updated_at'])

        result = run_command(self.source_file, '--commit', '--refresh')

        self.assertEqual(result['created_total'], 0)
        manifest.refresh_from_db()
        self.assertIn(
            str(poau.pk), manifest.payload['ownership']['owned']['poau.POAU'],
        )
        self.assertEqual(
            set(manifest.payload['ownership']['owned']['poau.POAUActividad']),
            {str(activity_id) for activity_id in activity_ids},
        )
