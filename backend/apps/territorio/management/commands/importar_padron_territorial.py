"""Carga el padrón desde el JSON que produce `exportar_padron_territorial`.

Pensado para llevar el padrón al servidor sin mover las doce planillas Excel ni
tocar la base a mano. Es idempotente: correrlo dos veces no duplica ni
renumera nada.

Resuelve el distrito por su CÓDIGO, así que funciona aunque el UUID del
distrito sea distinto en cada base —que es exactamente lo que pasa—.
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.territorio.models import (
    DirigenteTerritorial, Distrito, UnidadTerritorial, clave_organizacion,
)

VERSION_SOPORTADA = 1


class Command(BaseCommand):
    help = 'Carga el padrón de organizaciones territoriales desde un JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', required=True, help='Ruta del .json.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Informa lo que haría, sin escribir nada.')

    def handle(self, *args, **opciones):
        datos = self._leer(opciones['archivo'])
        organizaciones = datos.get('organizaciones') or []
        if not organizaciones:
            raise CommandError('El archivo no trae ninguna organización.')

        distritos, faltantes = self._resolver_distritos(organizaciones)
        if faltantes:
            # Se corta antes de escribir: una carga a medias es peor que
            # ninguna, porque nadie sabe qué distritos quedaron adentro.
            raise CommandError(
                'Estos códigos de distrito no existen en esta base: '
                f'{", ".join(sorted(faltantes))}. '
                f'Hay: {", ".join(sorted(distritos))}.')

        self.stdout.write(
            f'{len(organizaciones)} organizaciones · generado {datos.get("generado", "?")}')
        if opciones['dry_run']:
            self.stdout.write(self.style.WARNING('[dry-run] sin escribir.'))
            return

        altas, cambios, dirigentes = self._guardar(organizaciones, distritos)
        self.stdout.write(self.style.SUCCESS(
            f'{altas} organizaciones nuevas, {cambios} actualizadas, '
            f'{dirigentes} dirigentes.'))

    def _leer(self, ruta):
        try:
            with open(ruta, encoding='utf-8') as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            raise CommandError(f'No se encontró el archivo {ruta}')
        except json.JSONDecodeError as error:
            raise CommandError(f'El archivo no es JSON válido: {error}')
        if datos.get('version') != VERSION_SOPORTADA:
            raise CommandError(
                f'Versión de formato {datos.get("version")!r}; este comando '
                f'entiende la {VERSION_SOPORTADA}.')
        return datos

    def _resolver_distritos(self, organizaciones):
        distritos = {d.codigo.upper(): d for d in Distrito.objects.all()}
        pedidos = {(o.get('distrito') or '').upper() for o in organizaciones}
        return distritos, pedidos - set(distritos)

    @transaction.atomic
    def _guardar(self, organizaciones, distritos):
        altas = cambios = total_dirigentes = 0
        for fila in organizaciones:
            distrito = distritos[(fila.get('distrito') or '').upper()]
            clave = clave_organizacion(fila['nombre'])
            unidad = UnidadTerritorial.objects.filter(
                distrito=distrito, nombre_busqueda=clave).first()
            if unidad is None:
                # Se conserva el código del origen para que las dos bases
                # nombren igual a la misma organización.
                unidad = UnidadTerritorial(distrito=distrito,
                                           codigo=fila.get('codigo', ''))
                altas += 1
            else:
                cambios += 1
            unidad.nombre = fila['nombre']
            unidad.tipo = fila.get('tipo') or 'otro'
            unidad.activa = fila.get('activa', True)
            unidad.observacion = fila.get('observacion', '')
            unidad.save()

            for dirigente in fila.get('dirigentes') or []:
                DirigenteTerritorial.objects.update_or_create(
                    unidad=unidad,
                    gestion=dirigente['gestion'],
                    cargo=dirigente.get('cargo', ''),
                    defaults={
                        'nombre': dirigente['nombre'],
                        'telefono': dirigente.get('telefono', ''),
                        'vigente': dirigente.get('vigente', True),
                        'observacion': dirigente.get('observacion', ''),
                    },
                )
                total_dirigentes += 1
        return altas, cambios, total_dirigentes
