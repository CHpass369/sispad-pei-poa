"""Carga los techos por unidad y categoría desde el fixture de la planilla.

Los datos no viajan en los commits: el comando va en el repositorio, su efecto
queda en la base donde se corre. Sin esta siembra el asistente de recursos no
ofrece monto para ninguna unidad y la pantalla dice «no figura en la planilla
de saldos» para todo el municipio.

Es idempotente: se puede correr las veces que haga falta. No borra nada — una
fila que administración cargó a mano y que el fixture no trae se respeta, no se
purga. Ver `apps/articulacion/data/saldos_unidad_categoria_2027.json`.
"""
import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.articulacion.models import SaldoUnidadCategoria
from apps.organizacion.models import UnidadOrganizacional

RUTA_DATOS = Path(__file__).resolve().parents[2] / 'data'


class Command(BaseCommand):
    help = 'Siembra los saldos por unidad y categoría programática desde el fixture.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2027)
        parser.add_argument(
            '--archivo', type=str, default=None,
            help='Ruta del fixture. Por defecto, el de la gestión indicada.',
        )
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Sin esta bandera solo simula y no escribe nada.',
        )

    def handle(self, *args, **opciones):
        gestion = opciones['gestion']
        ruta = Path(
            opciones['archivo']
            or RUTA_DATOS / f'saldos_unidad_categoria_{gestion}.json'
        )
        if not ruta.exists():
            raise CommandError(f'No existe el fixture {ruta}')

        datos = json.loads(ruta.read_text(encoding='utf-8'))
        if datos.get('gestion') != gestion:
            raise CommandError(
                f'El fixture declara la gestión {datos.get("gestion")} y se pidió '
                f'{gestion}. Sembrar techos de otro año en esta gestión mezclaría '
                f'dos presupuestos distintos.'
            )
        filas = datos['filas']

        unidades = {
            u.codigo: u for u in UnidadOrganizacional.objects
            .filter(gestion__anio=gestion)
        }
        if not unidades:
            raise CommandError(
                f'No hay ninguna unidad organizacional en la gestión {gestion}. '
                f'Corra primero `traspasar_vigencia_uo`.'
            )

        creadas, actualizadas, iguales, huerfanas = [], [], [], []

        with transaction.atomic():
            for fila in filas:
                unidad = unidades.get(fila['codigo_unidad'])
                if unidad is None:
                    huerfanas.append(fila)
                    continue

                saldo = Decimal(str(fila['saldo']))
                existente = SaldoUnidadCategoria.objects.filter(
                    unidad=unidad,
                    categoria_programatica=fila['categoria_programatica'],
                    fuente__isnull=True, organismo__isnull=True,
                ).first()

                if existente is None:
                    if opciones['aplicar']:
                        SaldoUnidadCategoria.objects.create(
                            unidad=unidad,
                            categoria_programatica=fila['categoria_programatica'],
                            denominacion=fila['denominacion'],
                            saldo=saldo,
                            filas_origen=fila['filas_origen'],
                        )
                    creadas.append(fila)
                elif (existente.saldo != saldo
                      or existente.denominacion != fila['denominacion']):
                    if opciones['aplicar']:
                        existente.saldo = saldo
                        existente.denominacion = fila['denominacion']
                        existente.filas_origen = fila['filas_origen']
                        existente.save(update_fields=[
                            'saldo', 'denominacion', 'filas_origen', 'updated_at',
                        ])
                    actualizadas.append((fila, existente))
                else:
                    iguales.append(fila)

            if not opciones['aplicar']:
                transaction.set_rollback(True)

        modo = 'APLICADO' if opciones['aplicar'] else 'SIMULACRO (use --aplicar)'
        self.stdout.write(f'--- {modo} · gestión {gestion} · {ruta.name} ---')
        self.stdout.write(f'  filas en el fixture : {len(filas)}')
        self.stdout.write(f'  creadas             : {len(creadas)}')
        self.stdout.write(f'  actualizadas        : {len(actualizadas)}')
        self.stdout.write(f'  sin cambio          : {len(iguales)}')

        total = sum(Decimal(str(f['saldo'])) for f in filas)
        self.stdout.write(f'  techo del fixture   : {total:,.2f} Bs.')

        if huerfanas:
            # No es un detalle: cada una es una unidad que no va a poder
            # programar y nadie se entera hasta que alguien la abre.
            self.stdout.write(self.style.WARNING(
                f'\n  {len(huerfanas)} filas sin unidad en la gestión {gestion}:'
            ))
            for f in huerfanas:
                self.stdout.write(
                    f'    {f["codigo_unidad"]:<14} {f["categoria_programatica"]} '
                    f'({f["saldo"]:,.2f} Bs.)'
                )

        if opciones['aplicar']:
            vivos = SaldoUnidadCategoria.objects.filter(
                unidad__gestion__anio=gestion,
            ).count()
            self.stdout.write(self.style.SUCCESS(
                f'\n  saldos en la base ahora: {vivos}'
            ))
