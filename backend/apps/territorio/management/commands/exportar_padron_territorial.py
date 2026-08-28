"""Vuelca el padrón de organizaciones territoriales a un JSON portable.

Existe porque `dumpdata` NO sirve para mover esta tabla entre bases. Los
`Distrito` se crean con `update_or_create(codigo=...)` y su UUID se genera por
base: el D1 local y el D1 del servidor son ids distintos, así que la clave
foránea de un volcado normal no engancha. Y `Distrito.codigo` no tiene
unicidad declarada, con lo cual mandar también los distritos deja dos D1 en
silencio.

Este volcado referencia el distrito por su CÓDIGO —`D1`, `DLL`, `DU`—, que sí
es el mismo en todas las bases. Lo carga `importar_padron_territorial`.
"""
import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.territorio.models import UnidadTerritorial

VERSION = 1


class Command(BaseCommand):
    help = ('Exporta el padrón de organizaciones territoriales y sus dirigentes '
            'a un JSON que se puede cargar en otra base.')

    def add_arguments(self, parser):
        parser.add_argument('--salida', required=True,
                            help='Ruta del .json a escribir.')
        parser.add_argument('--distrito',
                            help='Código de un distrito. Por defecto, todos.')
        parser.add_argument('--gestion', type=int,
                            help='Solo los dirigentes de esta gestión.')
        parser.add_argument('--sin-telefonos', action='store_true',
                            help='Omite los teléfonos, que son dato personal.')

    def handle(self, *args, **opciones):
        consulta = (UnidadTerritorial.objects
                    .select_related('distrito')
                    .prefetch_related('dirigentes')
                    .order_by('distrito__codigo', 'codigo'))
        if opciones['distrito']:
            consulta = consulta.filter(distrito__codigo__iexact=opciones['distrito'])

        organizaciones, total_dirigentes = [], 0
        for unidad in consulta:
            dirigentes = unidad.dirigentes.all()
            if opciones['gestion']:
                dirigentes = [d for d in dirigentes if d.gestion == opciones['gestion']]
            total_dirigentes += len(dirigentes)
            organizaciones.append({
                # El distrito viaja por código, nunca por id.
                'distrito': unidad.distrito.codigo if unidad.distrito else '',
                'codigo': unidad.codigo,
                'nombre': unidad.nombre,
                'tipo': unidad.tipo,
                'activa': unidad.activa,
                'observacion': unidad.observacion,
                'dirigentes': [{
                    'gestion': d.gestion,
                    'nombre': d.nombre,
                    'cargo': d.cargo,
                    'telefono': '' if opciones['sin_telefonos'] else d.telefono,
                    'vigente': d.vigente,
                    'observacion': d.observacion,
                } for d in sorted(dirigentes, key=lambda x: (-x.gestion, x.cargo))],
            })

        contenido = {
            'version': VERSION,
            'generado': timezone.now().isoformat(),
            'organizaciones': organizaciones,
        }
        with open(opciones['salida'], 'w', encoding='utf-8') as archivo:
            json.dump(contenido, archivo, ensure_ascii=False, indent=1)

        self.stdout.write(self.style.SUCCESS(
            f'{len(organizaciones)} organizaciones y {total_dirigentes} dirigentes '
            f'en {opciones["salida"]}'))
