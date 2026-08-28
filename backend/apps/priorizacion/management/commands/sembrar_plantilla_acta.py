"""Carga la plantilla del acta oficial, calcada de la hoja ACTAOFI."""
from django.core.management.base import BaseCommand

from apps.priorizacion.models import PlantillaActa

# El marcador {otb} se escribe sin anteponerle "OTB": el dato ya trae su tipo
# —OTB, J.V., SINDICATO AGRARIO, SUB CENTRAL— y no todas las organizaciones que
# priorizan son OTB.
PLANTILLA = {
    'titulo': 'ACTA DE PRIORIZACIÓN DE PROYECTOS Y ACTIVIDADES',
    'subtitulo': 'POA {gestion}',
    'encabezado': (
        'El Sr. {presidente} presidente de la {otb} del {distrito}, en '
        'fecha {dia} de {mes} del año {anio_letras}, realizo la priorización '
        'del proyecto para el POA {gestion}, mismo se detalla a continuación:'
    ),
    'rotulo_descripcion': 'DESCRIPCION',
    'rotulo_monto': 'MONTO BS.-',
    'rotulo_total': 'TOTAL',
    'aclaracion': (
        'Aclarar que las transferencias del TGN y la proyección de recursos '
        'propios del GAMS programados en el POA {gestion} son proyectados y su '
        'ejecución en actividades y proyectos de inversión pública está sujeto '
        'a la recaudación efectiva por tanto son proyectados, por lo que su '
        'recaudación puede ser menor o mayor durante la gestión fiscal, '
        'asimismo la asignación de presupuesto no constituyen, obligaciones o '
        'deudas por parte del GAMS debiendo los desembolsos sujetarse a la '
        'recaudación efectiva.'
    ),
    'nota': ('Nota:  Se aclara que, una vez priorizado el proyecto, no se podrá '
             'realizar ninguna modificación ni cambio de proyecto.'),
    'cierre': ('En constancia de conformidad firman al pie del presente '
               'documento los siguientes:'),
    'firmas': [
        {'rol': 'Presidente de la OTB', 'campo': 'presidente'},
    ],
}


class Command(BaseCommand):
    help = 'Siembra la plantilla del acta de priorización.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=None)
        parser.add_argument('--nombre', default='Acta de priorización POA')

    def handle(self, *args, **opciones):
        plantilla, creada = PlantillaActa.objects.update_or_create(
            nombre=opciones['nombre'], gestion=opciones['gestion'],
            defaults={**PLANTILLA, 'activa': True},
        )
        self.stdout.write(self.style.SUCCESS(
            f'Plantilla {"creada" if creada else "actualizada"}: {plantilla}'))
