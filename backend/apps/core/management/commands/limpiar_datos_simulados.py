import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.services.limpieza_datos_simulados import CleanupError, clean_simulated_data


class Command(BaseCommand):
    help = "Generate a manifest or atomically remove allowlisted simulated data."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="Only generate the manifest (the default).",
        )
        mode.add_argument(
            "--commit",
            action="store_true",
            help=(
                "Delete the manifest candidates in one transaction. Only rows "
                "with an explicit deterministic demo marker (SIM-2027/DEMO- "
                "prefixes, @demo.sispoa.local emails, "
                "metadatos_importacion__demo=True) are deleted; exact-key "
                "collisions are reported as ambiguous_excluded and require "
                "--include-ambiguous-test-data."
            ),
        )
        parser.add_argument(
            "--include-ambiguous-test-data",
            action="store_true",
            help=(
                "DANGEROUS: include reviewed heuristic matches and common "
                "exact-key collisions (e.g. PGDESA-2026-2050, GAM, "
                "LineamientoPAD 01-20) in deletion candidates in addition to "
                "deterministic simulated-data markers."
            ),
        )
        parser.add_argument(
            "--manifest",
            help="Optional path for the JSON manifest; stdout always receives the same report.",
        )

    def handle(self, *args, **options):
        commit = bool(options.get("commit"))
        include_ambiguous = bool(options.get("include_ambiguous_test_data"))
        try:
            report = clean_simulated_data(
                commit=commit,
                include_ambiguous_test_data=include_ambiguous,
            )
        except CleanupError as exc:
            raise CommandError(str(exc)) from exc

        serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False, default=str)
        if options.get("manifest"):
            manifest_path = Path(options["manifest"])
            if not manifest_path.parent.exists():
                raise CommandError(f"Manifest parent directory does not exist: {manifest_path.parent}")
            manifest_path.write_text(serialized + "\n", encoding="utf-8")
        self.stdout.write(serialized)
