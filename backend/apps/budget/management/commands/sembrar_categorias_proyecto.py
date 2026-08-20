"""Da de alta en el catálogo maestro las categorías de los proyectos SISIN.

El catálogo traía solo categorías de funcionamiento (`000 0 001`). Las de
inversión —`180 08620281200000 000`, con el SISIN en el segmento del medio—
viven en los reportes del SIGEP y sin ellas no hay forma de enlazar lo que una
OTB prioriza con la fila de gasto que le corresponde.

Cada categoría se cuelga del subprograma `<programa>.SP`, que es de donde
cuelgan las actividades de funcionamiento: el árbol del presupuesto de gastos
va actividad → subprograma → programa, y los PROGRAMA del catálogo son rangos
(`180 - 189`), no códigos sueltos.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.budget.categoria import partes_categoria
from apps.budget.models import CategoriaProgramaticaTecho
from apps.gestion.models import GestionFiscal


class Command(BaseCommand):
    help = 'Siembra las categorías programáticas de proyectos SISIN.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, required=True)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opciones):
        from apps.priorizacion.models import ProyectoCatalogo

        gestion = GestionFiscal.objects.filter(anio=opciones['gestion']).first()
        if gestion is None:
            self.stdout.write(self.style.ERROR(
                f'La gestión {opciones["gestion"]} no está habilitada.'))
            return

        subprogramas = {
            c.codigo: c for c in CategoriaProgramaticaTecho.objects.filter(
                gestion=gestion, nivel='SUBPROGRAMA')
        }
        existentes = set(CategoriaProgramaticaTecho.objects
                         .filter(gestion=gestion)
                         .values_list('codigo', flat=True))

        nuevas, sin_programa, ilegibles = {}, set(), 0
        for proyecto in ProyectoCatalogo.objects.exclude(categoria_programatica=''):
            partes = partes_categoria(proyecto.categoria_programatica)
            if not partes.valida or not partes.es_proyecto:
                ilegibles += 1
                continue
            if partes.codigo in existentes or partes.codigo in nuevas:
                continue
            if f'{partes.programa}.SP' not in subprogramas:
                sin_programa.add(partes.programa)
            nuevas[partes.codigo] = (partes, proyecto.nombre)

        self.stdout.write(
            f'{len(nuevas)} categorías de proyecto nuevas · '
            f'{ilegibles} entradas sin categoría legible.')
        if sin_programa:
            # Se avisa, no se inventa el subprograma: colgarlas de un padre que
            # no existe las dejaría fuera del árbol del presupuesto de gastos.
            self.stdout.write(self.style.WARNING(
                f'Programas sin subprograma en el catálogo, quedan sin padre: '
                f'{sorted(sin_programa)}'))
        if opciones['dry_run']:
            self.stdout.write(self.style.WARNING('[dry-run] no se escribió nada.'))
            return
        self._guardar(nuevas, subprogramas, gestion)

    @transaction.atomic
    def _guardar(self, nuevas, subprogramas, gestion):
        creadas = 0
        for codigo, (partes, denominacion) in nuevas.items():
            CategoriaProgramaticaTecho.objects.create(
                gestion=gestion, codigo=codigo, nivel='PROYECTO',
                denominacion=denominacion[:300],
                parent=subprogramas.get(f'{partes.programa}.SP'),
                origen='SIGEP',
            )
            creadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'{creadas} categorías creadas · '
            f'{CategoriaProgramaticaTecho.objects.filter(gestion=gestion).count()} '
            'en el catálogo.'))
