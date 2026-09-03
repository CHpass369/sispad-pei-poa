"""Borra asignaciones de objeto de gasto puntuales, por código exacto.

Problema que resuelve
----------------------
Probar el asistente de recursos POAU (o el importador) contra unidades
reales deja `AsignacionObjetoGasto` de prueba en la base — plata que no
corresponde a ninguna programación real. No hay forma segura de
borrarlas a mano desde la pantalla (no tiene un botón de borrado
masivo), y borrar "por parecido" (denominación, monto) es una apuesta
sobre datos reales de presupuesto.

Qué hace
--------
Recibe uno o más `--codigo` (el `codigo_asignacion` exacto, por ejemplo
`PROV-SF-DRT-38-3440024.G1`) y por defecto solo LISTA lo que encontró —
código, denominación del objeto de gasto, monto vigente, acción y
operación/actividad/tarea a la que está atada — sin tocar nada. Recién
con `--aplicar` borra, dentro de una única transacción.

Uso::

    # 1. Ver qué encontró, sin tocar nada (por defecto):
    python manage.py borrar_asignaciones_gasto \\
        --codigo PROV-SF-DRT-38-3440024.G1 \\
        --codigo PROV-SF-DRT-38-3440024.G2 \\
        --codigo PROV-SF-DRT-37-3500003.G1

    # 2. Aplicarlo:
    python manage.py borrar_asignaciones_gasto \\
        --codigo PROV-SF-DRT-38-3440024.G1 \\
        --codigo PROV-SF-DRT-38-3440024.G2 \\
        --codigo PROV-SF-DRT-37-3500003.G1 \\
        --aplicar

Un código que no matchea ninguna fila se avisa y no interrumpe el resto.
Si algún código coincide con más de una gestión, hay que desambiguar con
`--gestion`.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.articulacion.models import AsignacionObjetoGasto


class Command(BaseCommand):
    help = (
        'Lista (por defecto) o borra (--aplicar) AsignacionObjetoGasto por '
        'codigo_asignacion exacto.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--codigo', action='append', required=True, dest='codigos',
            help='codigo_asignacion exacto a borrar. Repetible.',
        )
        parser.add_argument(
            '--gestion', type=int, default=None,
            help='Gestión (año) para desambiguar si un código se repite.',
        )
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Borra de verdad. Sin esta bandera solo lista qué encontró.',
        )

    def handle(self, *args, **options):
        codigos = options['codigos']
        gestion = options['gestion']
        aplicar = options['aplicar']

        qs = AsignacionObjetoGasto.objects.filter(
            codigo_asignacion__in=codigos,
        ).select_related('accion_poa', 'operacion', 'actividad', 'tarea')
        if gestion is not None:
            qs = qs.filter(gestion=gestion)

        encontrados = list(qs)
        encontrados_codigos = {a.codigo_asignacion for a in encontrados}
        faltantes = [c for c in codigos if c not in encontrados_codigos]

        if not encontrados:
            self.stdout.write(self.style.WARNING(
                'Ningún código coincide con una fila existente.',
            ))
            return

        self.stdout.write(f'Encontradas {len(encontrados)} de {len(codigos)} código(s):')
        for a in encontrados:
            nivel = a.actividad or a.tarea or a.operacion
            self.stdout.write(
                f'  {a.codigo_asignacion} · gestión {a.gestion} · '
                f'{a.cod_objeto_gasto} {a.descripcion_objeto} · '
                f'Bs {a.monto_vigente} · acción {a.accion_poa.codigo_accion} · '
                f'{nivel}',
            )
        if faltantes:
            self.stdout.write(self.style.WARNING(
                f'No se encontró ninguna fila para: {", ".join(faltantes)}',
            ))

        if not aplicar:
            self.stdout.write(self.style.NOTICE(
                'Dry-run: no se borró nada. Repetir con --aplicar para borrar '
                'de verdad estas filas.',
            ))
            return

        with transaction.atomic():
            eliminados, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Borradas {eliminados} fila(s).'))
