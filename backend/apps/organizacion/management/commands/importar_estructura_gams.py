"""Importa la estructura organizacional oficial del GAMS a una gestión.

    python manage.py importar_estructura_gams --gestion 2026
    python manage.py importar_estructura_gams --gestion 2027 --dry-run

Idempotente: reejecutarlo actualiza nombres, clase y jerarquía sin duplicar,
porque UnidadOrganizacional es única por (codigo, gestion). Eso permite
reimportar cuando el catálogo se corrige, y clonar la estructura a la gestión
siguiente sin tocar la anterior.
"""
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.gestion.models import GestionFiscal
from apps.organizacion.models import TipoUnidad, UnidadOrganizacional

DATOS = Path(__file__).resolve().parents[2] / 'data' / 'estructura_gams_2026.json'


class Command(BaseCommand):
    help = 'Importa la estructura organizacional del GAMS para una gestión.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2026)
        parser.add_argument(
            '--archivo', type=str, default=str(DATOS),
            help='JSON de la estructura (por defecto, la codificación 2026).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Valida y reporta sin escribir nada.',
        )

    def handle(self, *args, **opciones):
        ruta = Path(opciones['archivo'])
        if not ruta.exists():
            raise CommandError(f'No existe el archivo {ruta}')

        contenido = json.loads(ruta.read_text(encoding='utf-8'))
        unidades = contenido['unidades']

        try:
            gestion = GestionFiscal.objects.get(anio=opciones['gestion'])
        except GestionFiscal.DoesNotExist:
            raise CommandError(
                f'No existe la gestión fiscal {opciones["gestion"]}. '
                'Créela antes de importar la estructura.'
            )

        tipos = {t.codigo: t for t in TipoUnidad.objects.all()}
        faltantes = {u['tipo'] for u in unidades} - set(tipos)
        if faltantes:
            raise CommandError(
                f'Faltan tipos de unidad en el catálogo: {sorted(faltantes)}. '
                'Aplique la migración organizacion.0003.'
            )

        # El padre debe existir antes que la hija: se procesa por nivel.
        orden_nivel = {t.codigo: t.nivel for t in tipos.values()}
        unidades = sorted(unidades, key=lambda u: (orden_nivel[u['tipo']], u['orden']))

        if opciones['dry_run']:
            self.stdout.write(
                f'[dry-run] {len(unidades)} unidades para la gestión {gestion.anio}'
            )
            for tipo in sorted(tipos, key=lambda c: orden_nivel[c]):
                n = sum(1 for u in unidades if u['tipo'] == tipo)
                if n:
                    self.stdout.write(f'  {tipo}: {n}')
            return

        # UnidadOrganizacional hereda VigenciaModel: la vigencia arranca con
        # la gestión. Se fija solo al CREAR, para que una reimportación no
        # pise una fecha ajustada a mano.
        desde = gestion.fecha_inicio or date(gestion.anio, 1, 1)

        creadas = actualizadas = 0
        with transaction.atomic():
            registradas = {}
            for u in unidades:
                padre = registradas.get(u['padre']) if u['padre'] else None
                if u['padre'] and padre is None:
                    # Puede existir de una corrida previa.
                    padre = UnidadOrganizacional.objects.filter(
                        codigo=u['padre'], gestion=gestion,
                    ).first()
                    if padre is None:
                        raise CommandError(
                            f'{u["codigo"]}: no se encontró el padre {u["padre"]}'
                        )
                unidad, creada = UnidadOrganizacional.objects.update_or_create(
                    codigo=u['codigo'], gestion=gestion,
                    create_defaults={
                        'nombre': u['nombre'],
                        'sigla': u['sigla'] or '',
                        'clase': u['clase'] or '',
                        'tipo': tipos[u['tipo']],
                        'padre': padre,
                        'orden': u['orden'],
                        'fecha_vigencia_desde': desde,
                    },
                    defaults={
                        'nombre': u['nombre'],
                        'sigla': u['sigla'] or '',
                        'clase': u['clase'] or '',
                        'tipo': tipos[u['tipo']],
                        'padre': padre,
                        'orden': u['orden'],
                    },
                )
                registradas[u['codigo']] = unidad
                creadas += creada
                actualizadas += not creada

        self.stdout.write(self.style.SUCCESS(
            f'Gestión {gestion.anio}: {creadas} creadas, {actualizadas} actualizadas '
            f'({len(unidades)} en el catálogo).'
        ))
