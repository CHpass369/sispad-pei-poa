import os
import json
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import Rol
from apps.articulacion.models import AcuerdoInternacional, LineamientoPAD, ResultadoPAD
from apps.core.services.limpieza_datos_simulados import CleanupError
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional
from apps.pad.models import SectorPAD
from apps.planificacion.models import Plan
from apps.poau.models import POAU
from scripts.seed import DEMO_PASSWORD_ENV


TEST_DEMO_PASSWORDS = {
    env_name: f'test-only-{account}-credential'
    for account, env_name in DEMO_PASSWORD_ENV.items()
}


@patch.dict(os.environ, TEST_DEMO_PASSWORDS, clear=False)
class LimpiezaDatosSimuladosTest(TestCase):
    def setUp(self):
        # patch.dict applied at class level only wraps test_* methods, not
        # setUp; seed_demo_data() in setUp needs the demo seed passwords, so
        # the environment is patched explicitly for the whole test lifecycle.
        self._seed_env = patch.dict(os.environ, TEST_DEMO_PASSWORDS, clear=False)
        self._seed_env.start()
        self.addCleanup(self._seed_env.stop)
        from scripts.seed import seed_demo_data

        seed_demo_data()
        user_model = get_user_model()
        user_model.objects.create_superuser(
            email="admin@gamsacaba.gob.bo", password="real-password"
        )
        self.ambiguous_user = user_model.objects.create_user(
            email="test@test.com", password="test-password"
        )
        self.role_count = Rol.objects.count()

    def _run(self, *args):
        output = StringIO()
        call_command("limpiar_datos_simulados", *args, stdout=output)
        return json.loads(output.getvalue())

    def test_dry_run_is_default_and_contains_primary_keys_without_writing(self):
        before = {
            "users": get_user_model().objects.count(),
            "plans": Plan.objects.count(),
            "pad_results": ResultadoPAD.objects.count(),
        }

        report = self._run()

        self.assertFalse(report["committed"])
        self.assertGreater(report["candidates"]["articulacion.ResultadoPAD"]["count"], 0)
        self.assertEqual(
            len(report["candidates"]["articulacion.ResultadoPAD"]["primary_keys"]),
            report["candidates"]["articulacion.ResultadoPAD"]["count"],
        )
        self.assertEqual(before["users"], get_user_model().objects.count())
        self.assertEqual(before["plans"], Plan.objects.count())
        self.assertEqual(before["pad_results"], ResultadoPAD.objects.count())

    def test_commit_excludes_ambiguous_rows_without_dangerous_flag(self):
        report = self._run("--commit")

        self.assertTrue(report["committed"])
        self.assertTrue(
            get_user_model().objects.filter(email="test@test.com").exists()
        )
        # Exact-key collisions on common seed identifiers survive normal commit:
        # the seeded PGDESA plan carries no explicit ownership marker, so its
        # code alone must not be treated as ownership proof.
        self.assertTrue(Plan.objects.filter(codigo="PGDESA-2026-2050").exists())
        self.assertTrue(Plan.objects.filter(codigo="PDESA-2026-2030").exists())
        self.assertFalse(UnidadOrganizacional.objects.filter(codigo="ORG-DEMO").exists())
        # Explicitly DEMO-named markers still prove ownership in normal mode.
        self.assertFalse(Plan.objects.filter(codigo="PEI-DEMO-2026").exists())
        self.assertFalse(POAU.objects.filter(codigo="POAU-DEMO-2026").exists())

    def test_commit_preserves_legitimate_rows_colliding_on_exact_seed_identifiers(self):
        unit_type = TipoUnidad.objects.get(codigo="SEC")
        colliding_plan = Plan.objects.create(
            codigo="PGDESA-2026-2050",
            nombre="Plan institucional legítimo",
            tipo="otro",
            gestion_inicio=2026,
            gestion_fin=2050,
            descripcion="Registro oficial que coincide con un identificador de semilla",
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        colliding_unit = UnidadOrganizacional.objects.create(
            codigo="GAM",
            gestion=2026,
            nombre="Gobierno Autónomo Municipal legítimo",
            sigla="GAM",
            tipo=unit_type,
            fecha_vigencia_desde=date(2026, 1, 1),
            fecha_vigencia_hasta=date(2026, 12, 31),
            activo=True,
        )
        colliding_lineamiento = LineamientoPAD.objects.create(
            codigo="01",
            denominacion="Lineamiento legítimo del sector salud",
            codigo_padre="",
            gestion_desde=2026,
            gestion_hasta=2030,
            activo=True,
        )
        colliding_type = TipoUnidad.objects.create(
            codigo="MAE", nombre="Máxima Autoridad Ejecutiva", nivel=1, activo=True
        )

        manifest = self._run()

        for label, row in (
            ("planificacion.Plan", colliding_plan),
            ("organizacion.UnidadOrganizacional", colliding_unit),
            ("articulacion.LineamientoPAD", colliding_lineamiento),
        ):
            candidate_keys = manifest["candidates"].get(label, {}).get("primary_keys", [])
            self.assertNotIn(str(row.pk), candidate_keys)

        ambiguous = manifest["ambiguous_excluded"]
        self.assertIn(
            str(colliding_plan.pk), ambiguous["planificacion.Plan"]["primary_keys"]
        )
        self.assertIn(
            str(colliding_unit.pk),
            ambiguous["organizacion.UnidadOrganizacional"]["primary_keys"],
        )
        self.assertIn(
            str(colliding_lineamiento.pk),
            ambiguous["articulacion.LineamientoPAD"]["primary_keys"],
        )
        self.assertGreater(manifest["ambiguous_excluded_total"], 0)

        self._run("--commit")

        self.assertTrue(Plan.objects.filter(pk=colliding_plan.pk).exists())
        self.assertTrue(UnidadOrganizacional.objects.filter(pk=colliding_unit.pk).exists())
        self.assertTrue(LineamientoPAD.objects.filter(pk=colliding_lineamiento.pk).exists())
        self.assertTrue(TipoUnidad.objects.filter(pk=colliding_type.pk).exists())

    def test_commit_preserves_legitimate_2026_and_demo_like_rows(self):
        legitimate_plan = Plan.objects.create(
            codigo="OFFICIAL-2026",
            nombre="Plan institucional",
            tipo="otro",
            gestion_inicio=2026,
            gestion_fin=2026,
            descripcion="Demostración institucional legítima",
            fecha_vigencia_desde=date(2026, 1, 1),
        )
        legitimate_result = ResultadoPAD.objects.create(
            id_cadena="OFFICIAL-2026-RESULT",
            codigo_resultado="OFFICIAL.2026.01",
            denominacion="Resultado legítimo de demostración pública",
            lineamiento_pad="OFFICIAL",
            vigencia_desde=2026,
            vigencia_hasta=2026,
            cod_geografico="000000",
            eta="Entidad legítima",
            cod_resultado_pds="OFFICIAL-RESULT",
        )

        manifest = self._run()
        plan_candidates = manifest["candidates"].get("planificacion.Plan", {})
        result_candidates = manifest["candidates"].get("articulacion.ResultadoPAD", {})
        self.assertNotIn(str(legitimate_plan.pk), plan_candidates.get("primary_keys", []))
        self.assertNotIn(str(legitimate_result.pk), result_candidates.get("primary_keys", []))

        self._run("--commit")

        self.assertTrue(Plan.objects.filter(pk=legitimate_plan.pk).exists())
        self.assertTrue(ResultadoPAD.objects.filter(pk=legitimate_result.pk).exists())

    def test_commit_removes_demo_and_ambiguous_data_preserving_contract(self):
        report = self._run("--commit", "--include-ambiguous-test-data")

        self.assertTrue(report["committed"])
        # With the dangerous opt-in, exact-key collisions on common seed
        # identifiers are deleted too.
        self.assertFalse(Plan.objects.filter(codigo="PGDESA-2026-2050").exists())
        self.assertFalse(Plan.objects.filter(codigo="PDESA-2026-2030").exists())
        self.assertFalse(LineamientoPAD.objects.filter(codigo__in=["01", "02"]).exists())
        self.assertFalse(TipoUnidad.objects.filter(codigo__in=["INST", "SEC", "DIR", "UE"]).exists())
        self.assertFalse(
            get_user_model().objects.filter(email__endswith="@demo.sispoa.local").exists()
        )
        self.assertFalse(
            get_user_model().objects.filter(email="test@test.com").exists()
        )
        self.assertFalse(Plan.objects.filter(codigo="SIM-2027-EM-DJR-01-PLAN-PEI").exists())
        self.assertFalse(POAU.objects.filter(codigo="POAU-DEMO-2026").exists())
        self.assertEqual(report["ambiguous_excluded_total"], 0)
        self.assertEqual(
            SectorPAD.objects.filter(
                codigo__in=[f"{index:02d}" for index in range(1, 21)]
            ).count(),
            20,
        )
        self.assertEqual(
            AcuerdoInternacional.objects.filter(
                tipo_acuerdo="ODS", codigo__in=[f"{i:02d}" for i in range(1, 18)]
            ).count(),
            17,
        )
        self.assertEqual(Rol.objects.count(), self.role_count)
        self.assertTrue(
            get_user_model().objects.filter(email="admin@gamsacaba.gob.bo").exists()
        )
        self.assertGreater(report["deleted"], 0)

    def test_commit_rolls_back_when_postcondition_fails(self):
        from apps.core.services import limpieza_datos_simulados

        before = ResultadoPAD.objects.count()
        with patch.object(
            limpieza_datos_simulados,
            "validate_preserved_state",
            side_effect=CleanupError("forced invariant failure"),
        ) as postcondition:
            with self.assertRaises(CleanupError):
                limpieza_datos_simulados.clean_simulated_data(
                    commit=True, include_ambiguous_test_data=True
                )

        postcondition.assert_called_once()
        self.assertEqual(ResultadoPAD.objects.count(), before)

    def test_implementation_does_not_contain_global_delete(self):
        for path in (
            Path(__file__).parents[1] / "services" / "limpieza_datos_simulados.py",
            Path(__file__).parents[1] / "management" / "commands" / "limpiar_datos_simulados.py",
        ):
            source = path.read_text()
            self.assertNotIn("objects.all().delete()", source)
