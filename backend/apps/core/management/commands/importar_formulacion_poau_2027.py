"""Import the simulated 2027 POAU formulation workbook safely."""

import json

from django.core.management.base import BaseCommand, CommandError

from apps.core.services.formulacion_poau_2027 import import_formulacion_poau_2027


class Command(BaseCommand):
    help = "Importa la formulación POAU 2027 de forma simulada e idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Ruta del workbook fuente.",
        )
        parser.add_argument("--sheet", default="Base", help="Hoja fuente.")
        parser.add_argument("--max-row", type=int, default=166, help="Última fila incluida.")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--dry-run", action="store_true", help="Solo valida; no escribe (predeterminado).")
        mode.add_argument("--commit", action="store_true", help="Escribe los registros válidos.")

    def handle(self, *args, **options):
        if options["max_row"] < 1:
            raise CommandError("--max-row debe ser mayor o igual a 1.")

        try:
            report = import_formulacion_poau_2027(
                file_path=options["file"],
                sheet_name=options["sheet"],
                max_row=options["max_row"],
                commit=options["commit"],
            )
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, default=str))
