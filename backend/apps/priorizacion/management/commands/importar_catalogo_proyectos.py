"""Arma el catálogo maestro de nombres de proyecto.

Dos fuentes, y hacen falta las dos: los reportes SIGEP traen los proyectos con
código SISIN y su categoría programática, pero en las OTB se prioriza mayormente
por tipo de obra —`ADQ. LUMINARIAS...`, `PAVIMENTO FLEXIBLE...`—, nombres que no
existen en el SIGEP. De 406 nombres de acta, solo 27 figuran ahí.
"""
import glob
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.priorizacion.models import OrigenProyecto, ProyectoCatalogo, normalizar

COL_ACTAS = [7, 9, 11, 13, 15, 17, 19]  # PROYECTO 1..7


class Command(BaseCommand):
    help = 'Importa el catálogo de proyectos desde reportes SIGEP y actas.'

    def add_arguments(self, parser):
        parser.add_argument('--sigep', help='Carpeta o glob de los .xls del SIGEP')
        parser.add_argument('--actas', help='Libro de actas (.xlsx)')
        parser.add_argument('--hoja', default='REGISTRO ACTAS')
        parser.add_argument('--dry-run', action='store_true',
                            help='Informa sin escribir nada.')

    def handle(self, *args, **opciones):
        self.seco = opciones['dry_run']
        registros = {}

        if opciones['sigep']:
            self._leer_sigep(opciones['sigep'], registros)
        if opciones['actas']:
            self._leer_actas(opciones['actas'], opciones['hoja'], registros)

        if not registros:
            self.stdout.write(self.style.WARNING(
                'Nada que importar: indique --sigep y/o --actas.'))
            return

        if self.seco:
            self.stdout.write(self.style.WARNING(
                f'[dry-run] {len(registros)} proyectos, sin escribir.'))
            return
        self._guardar(registros)

    # --- Lectura -----------------------------------------------------------

    def _leer_sigep(self, ruta, registros):
        """Los .xls del SIGEP son BIFF viejo: openpyxl no los abre."""
        import xlrd

        archivos = sorted(glob.glob(os.path.join(ruta, '*.xls'))
                          if os.path.isdir(ruta) else glob.glob(ruta))
        if not archivos:
            self.stdout.write(self.style.WARNING(f'Sin .xls en {ruta}'))
            return

        leidas = repetidas = 0
        for archivo in archivos:
            hoja = xlrd.open_workbook(archivo).sheet_by_index(0)
            cabecera = [str(hoja.cell_value(1, c)).strip()
                        for c in range(hoja.ncols)]
            try:
                i_sisin = cabecera.index('SISIN')
                i_desc = cabecera.index('Descripcion SISIN')
                i_cat = cabecera.index('Cat. Prg.')
            except ValueError:
                self.stdout.write(self.style.WARNING(
                    f'{os.path.basename(archivo)}: cabecera inesperada, se omite.'))
                continue
            # El SIGEP repite la cabecera cada 63 filas por los saltos de
            # página: sin esto se cuela como un proyecto llamado
            # "Descripcion SISIN".
            rotulos = {cabecera[i_sisin], cabecera[i_desc]}
            for f in range(2, hoja.nrows):
                sisin = str(hoja.cell_value(f, i_sisin)).strip()
                nombre = ' '.join(str(hoja.cell_value(f, i_desc)).split())
                if not sisin or not nombre or sisin in rotulos or nombre in rotulos:
                    repetidas += 1
                    continue
                leidas += 1
                clave = (normalizar(nombre), sisin)
                registros.setdefault(clave, {
                    'nombre': nombre, 'sisin': sisin,
                    'categoria': ' '.join(str(hoja.cell_value(f, i_cat)).split()),
                    'origen': OrigenProyecto.SIGEP, 'veces': 0,
                })
        self.stdout.write(
            f'SIGEP: {leidas} filas en {len(archivos)} archivo(s)'
            + (f', {repetidas} cabeceras repetidas omitidas.' if repetidas
               else '.'))

    def _leer_actas(self, archivo, hoja, registros):
        """Los nombres históricos: lo que las OTB realmente priorizan."""
        import openpyxl

        ws = openpyxl.load_workbook(archivo, data_only=True)[hoja]
        nuevos = repetidos = 0
        for fila in range(2, ws.max_row + 1):
            for columna in COL_ACTAS:
                nombre = ' '.join(str(ws.cell(fila, columna).value or '').split())
                if not nombre:
                    continue
                clave = (normalizar(nombre), '')
                if clave in registros:
                    registros[clave]['veces'] += 1
                    repetidos += 1
                    continue
                # Un nombre que ya vino del SIGEP no se duplica sin SISIN.
                con_sisin = next(
                    (v for (n, s), v in registros.items()
                     if n == clave[0] and s), None)
                if con_sisin:
                    con_sisin['veces'] += 1
                    repetidos += 1
                    continue
                registros[clave] = {
                    'nombre': nombre, 'sisin': '', 'categoria': '',
                    'origen': OrigenProyecto.HISTORICO, 'veces': 1,
                }
                nuevos += 1
        self.stdout.write(
            f'Actas: {nuevos} nombres nuevos, {repetidos} repeticiones.')

    # --- Escritura ---------------------------------------------------------

    @transaction.atomic
    def _guardar(self, registros):
        creados = actualizados = 0
        for (busqueda, sisin), datos in registros.items():
            obj, nuevo = ProyectoCatalogo.objects.update_or_create(
                nombre_busqueda=busqueda, sisin=sisin,
                defaults={
                    'nombre': datos['nombre'],
                    'categoria_programatica': datos['categoria'],
                    'origen': datos['origen'],
                    'veces_priorizado': datos['veces'],
                },
            )
            creados += nuevo
            actualizados += not nuevo
        self.stdout.write(self.style.SUCCESS(
            f'Catálogo: {creados} creados, {actualizados} actualizados, '
            f'{ProyectoCatalogo.objects.count()} en total.'))
