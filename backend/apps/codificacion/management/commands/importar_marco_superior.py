"""Importa el marco superior PGDESA/PDESA al kernel V2 (WP-06).

Uso:
    python manage.py importar_marco_superior [--dry-run] [--gestion 2027]
        [--lote pgdesa-pdesa]
"""
from django.core.management.base import BaseCommand

from apps.codificacion.migration_v2 import importar_marco_superior


class Command(BaseCommand):
    help = (
        'Importa los catálogos oficiales PGDESA/PDESA de codificacion '
        'al kernel estratégico V2 (NodoEstrategico) con trazabilidad '
        'en LegacyMigrationMap.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--gestion', type=int, default=None)
        parser.add_argument('--lote', default='pgdesa-pdesa')

    def handle(self, *args, **options):
        resumen = importar_marco_superior(
            lote=options['lote'],
            dry_run=options['dry_run'],
            gestion=options['gestion'],
        )
        self.stdout.write(f"Lote: {resumen['lote']} (dry-run={resumen['dry_run']})")
        self.stdout.write(
            f"Nodos: {resumen['nodos_creados']} — "
            f"migraciones en el mapa: {resumen['migraciones_registradas']}"
        )
        for instrumento in resumen['instrumentos']:
            self.stdout.write(
                f"  {instrumento['codigo']} (gestión {instrumento['gestion']}): "
                f"v{instrumento['version']} — {instrumento['nodos']} nodos — "
                f"{instrumento['estado']}"
            )
