"""Load the official POAU 2027 programmatic-category master."""

import json

from django.core.management.base import BaseCommand, CommandError

from apps.budget.importer_programmatic_category import import_programmatic_categories


class Command(BaseCommand):
    help = "Importa el maestro de categorías programáticas POAU 2027."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Ruta del workbook fuente.")
        parser.add_argument("--sheet", default="CLASIFICADOR", help="Hoja fuente.")
        parser.add_argument("--header-row", type=int, default=8, help="Fila del encabezado.")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--dry-run", action="store_true", dest="dry_run", default=True,
            help="Valida y reporta sin escribir (predeterminado).",
        )
        mode.add_argument("--commit", action="store_true", dest="commit", help="Escribe atómicamente.")

    def handle(self, *args, **options):
        try:
            report = import_programmatic_categories(
                file_path=options["file"],
                sheet_name=options["sheet"],
                header_row=options["header_row"],
                commit=options["commit"],
            )
        except (FileNotFoundError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, default=str))
