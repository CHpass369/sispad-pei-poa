"""Migración del PAD al kernel V2 (WP-07).

Uso:
    python manage.py migrar_pad --nodos [--dry-run] [--gestion 2027] [--lote pad]
    python manage.py migrar_pad --vinculos [--dry-run] [--gestion 2027]
    python manage.py migrar_pad --comparar
"""
from django.core.management.base import BaseCommand

from apps.pad.migration_v2 import (
    comparar_duplicados_pad,
    importar_articulaciones_sipeb,
    importar_pad,
)


class Command(BaseCommand):
    help = 'Migra la jerarquía PAD legacy al kernel estratégico V2 (WP-07).'

    def add_arguments(self, parser):
        parser.add_argument('--nodos', action='store_true')
        parser.add_argument('--vinculos', action='store_true')
        parser.add_argument('--comparar', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--gestion', type=int, default=None)
        parser.add_argument('--lote', default='pad')

    def handle(self, *args, **options):
        if options['comparar']:
            self._comparar()
            return
        if options['nodos']:
            self._nodos(options)
            return
        if options['vinculos']:
            self._vinculos(options)
            return
        raise CommandError('Indique --nodos, --vinculos o --comparar.')

    def _nodos(self, options):
        resumen = importar_pad(
            lote=options['lote'],
            dry_run=options['dry_run'],
            gestion=options['gestion'],
        )
        self.stdout.write(
            f"Lote {resumen['lote']} (dry-run={resumen['dry_run']}): "
            f"{resumen['nodos_creados']} nodos, "
            f"{resumen['migraciones_registradas']} migraciones"
        )
        for instrumento in resumen['instrumentos']:
            self.stdout.write(
                f"  {instrumento['codigo']} (g {instrumento['gestion']}): "
                f"v{instrumento['version']} — {instrumento['nodos']} nodos — "
                f"{instrumento['estado']}"
            )

    def _vinculos(self, options):
        resumen = importar_articulaciones_sipeb(
            lote=options['lote'] + '-sipeb',
            dry_run=options['dry_run'],
            gestion=options['gestion'],
        )
        self.stdout.write(
            f"Vínculos PAD→marco (dry-run={resumen['dry_run']}): "
            f"{resumen['vinculos_creados']} creados, "
            f"{resumen['sin_marco']} sin nodo marco disponible"
        )

    def _comparar(self):
        reporte = comparar_duplicados_pad()
        for nivel, datos in reporte.items():
            self.stdout.write(
                f'{nivel}: pad={datos["pad"]}, articulacion={datos["articulacion"]}, '
                f'coinciden por código y nombre={datos["coinciden_codigo_y_nombre"]}'
            )
            if datos['solo_pad']:
                self.stdout.write(f'  solo en pad: {", ".join(datos["solo_pad"])}')
            if datos['solo_articulacion']:
                self.stdout.write(
                    f'  solo en articulacion: '
                    f'{", ".join(datos["solo_articulacion"])}'
                )
