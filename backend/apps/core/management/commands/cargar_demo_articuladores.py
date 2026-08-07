import json

from django.core.management.base import BaseCommand, CommandError

from apps.core.demo_articuladores import DemoArticuladoresSeeder


class Command(BaseCommand):
    help = (
        'Previsualiza o refresca, de forma opt-in y transaccional, el conjunto '
        'provisional 2027 basado en el Excel de formulación de POAUs.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Persiste el conjunto; sin esta opción el comando solo consulta.',
        )
        parser.add_argument(
            '--refresh',
            action='store_true',
            help='Sincroniza campos demostrativos y reutiliza las filas fuente existentes.',
        )
        parser.add_argument(
            '--gestion',
            type=int,
            default=2027,
            help='Gestión respaldada por el archivo fuente (actualmente solo 2027).',
        )
        parser.add_argument(
            '--source-file',
            required=True,
            help='Ruta al Excel BASE FORMULACIÓN DE POAUS 2027.',
        )

    def handle(self, *args, **options):
        try:
            seeder = DemoArticuladoresSeeder(
                source_file=options['source_file'],
                gestion=options['gestion'],
                refresh=options['refresh'],
            )
            result = seeder.run(commit=options['commit'])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=False))
