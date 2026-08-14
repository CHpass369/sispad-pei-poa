"""Carga los objetivos de impacto/efecto del PDESA 2026-2030.

Fuente: PDF oficial "Ejes, Componentes y Lineamientos PDESA 06Jul2026.pdf",
extraído y mapeado a JSON con la estructura::

    {
      "ejes": {"1": {"codigo": "1", "nombre": "...", "objetivo_impacto": "..."}, ...},
      "componentes": {"1.1": {"codigo": "1.1", "nombre": "...", "objetivo_efecto": "..."}, ...}
    }

MAPEO DE CÓDIGOS (PDF -> catálogo):
-------------------------------------
El PDF usa códigos cortos ("1".."7" para ejes; "1.1".."7.7" para
componentes). El catálogo usa códigos de 2 dígitos con ceros a la
izquierda, donde el componente se numera DENTRO de su eje:

- Eje del PDF "1"     -> eje de catálogo con codigo "01"
- Componente PDF "1.1" -> componente de catálogo con codigo "01"
                         dentro del eje "01" (primer segmento -> eje,
                         segundo segmento -> código del componente).

Equivalencia: PDF "X.Y" -> eje "0X", componente "0Y" bajo ese eje.

El comando es idempotente: busca primero las filas EXISTENTES del
catálogo (gestión 2026) por código y las actualiza; solo si no existen
crea la fila (get_or_create). Esto evita duplicar el catálogo cuando ya
está cargado. Reporta creados/actualizados/omitidos.

Uso:
    python manage.py cargar_objetivos_pdesa [archivo.json]
        [--archivo ruta.json] [--gestion 2026] [--dry-run]
"""
import json

from django.core.management.base import BaseCommand, CommandError

from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    VersionCatalogoPlan,
)


class Command(BaseCommand):
    help = (
        'Carga objetivo_impacto (ejes) y objetivo_efecto (componentes) '
        'desde el JSON del PDF PDESA 2026-2030.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'archivo',
            nargs='?',
            default='/tmp/opencode/pdesa_2026_map.json',
            help='Ruta del JSON con los objetivos del PDESA (o use --archivo).',
        )
        parser.add_argument(
            '--archivo',
            dest='archivo_flag',
            help='Ruta alternativa del JSON (alias del argumento posicional).',
        )
        parser.add_argument(
            '--gestion',
            type=int,
            default=2026,
            help='Gestión de la versión de catálogo a actualizar (2026).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que haría sin escribir en la base de datos.',
        )

    @staticmethod
    def _codigo_catalogo(codigo_pdf: str) -> str:
        """Convierte un código del PDF ("1") a código de catálogo ("01")."""
        return str(int(codigo_pdf)).zfill(2)

    def handle(self, *args, **options):
        archivo = options['archivo_flag'] or options['archivo']
        gestion = options['gestion']
        dry_run = options['dry_run']

        try:
            with open(archivo, encoding='utf-8') as fh:
                datos = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'No se pudo leer {archivo}: {exc}') from exc

        version = (
            VersionCatalogoPlan.objects.filter(gestion=gestion).first()
        )
        if not version:
            raise CommandError(f'No existe versión de catálogo para gestión {gestion}.')

        # ---- Ejes PGDESA: objetivo de impacto ----
        # Busca la fila existente por (codigo, gestión) para NO duplicar el
        # catálogo: hay varias versiones 2026 (PGDESA y PDESA) y la canónica
        # es la que ya tiene los ejes cargados.
        ejes = datos.get('ejes', {})
        ejes_creados = ejes_actualizados = ejes_omitidos = 0
        for codigo_pdf, info in sorted(ejes.items()):
            objetivo = (info.get('objetivo_impacto') or '').strip()
            codigo = self._codigo_catalogo(codigo_pdf)
            eje = EjePGDESA.objects.filter(
                codigo=codigo, version_catalogo__gestion=gestion,
            ).first()
            if eje is None:
                eje, creado = EjePGDESA.objects.get_or_create(
                    codigo=codigo,
                    version_catalogo=version,
                    defaults={'denominacion': info.get('nombre', '')},
                )
                if not dry_run:
                    eje.objetivo_impacto = objetivo
                    eje.save(update_fields=['objetivo_impacto'])
                ejes_creados += 1
                self._log(
                    f'EJE {codigo_pdf}->{codigo}: creado (objetivo asignado)', dry_run,
                )
            elif eje.objetivo_impacto != objetivo:
                if not dry_run:
                    eje.objetivo_impacto = objetivo
                    eje.save(update_fields=['objetivo_impacto'])
                ejes_actualizados += 1
                self._log(
                    f'EJE {codigo_pdf}->{codigo}: objetivo_impacto actualizado', dry_run,
                )
            else:
                ejes_omitidos += 1

        # ---- Componentes PDESA: objetivo de efecto ----
        # Igual que ejes: matchea la fila existente por (eje.codigo, codigo,
        # gestión) antes de crear, para no duplicar el catálogo.
        componentes = datos.get('componentes', {})
        comps_creados = comps_actualizados = comps_omitidos = 0
        for codigo_pdf, info in sorted(
                componentes.items(), key=lambda kv: kv[0],
        ):
            objetivo = (info.get('objetivo_efecto') or '').strip()
            # "1.1" -> eje "01", componente "01"
            try:
                eje_pdf, comp_pdf = codigo_pdf.split('.')
            except ValueError as exc:
                raise CommandError(
                    f'Código de componente inválido en el JSON: {codigo_pdf!r}',
                ) from exc
            eje_codigo = self._codigo_catalogo(eje_pdf)
            comp_codigo = self._codigo_catalogo(comp_pdf)

            componente = ComponentePDESA.objects.filter(
                codigo=comp_codigo,
                eje__codigo=eje_codigo,
                version_catalogo__gestion=gestion,
            ).first()
            if componente is None:
                eje = EjePGDESA.objects.filter(
                    codigo=eje_codigo, version_catalogo__gestion=gestion,
                ).first()
                componente, creado = ComponentePDESA.objects.get_or_create(
                    codigo=comp_codigo,
                    eje=eje,
                    version_catalogo=version,
                    defaults={'denominacion': info.get('nombre', '')},
                )
                if not dry_run:
                    componente.objetivo_efecto = objetivo
                    componente.save(update_fields=['objetivo_efecto'])
                comps_creados += 1
                self._log(
                    f'COMPONENTE {codigo_pdf}->{eje_codigo}/{comp_codigo}: '
                    f'creado (objetivo asignado)', dry_run,
                )
            elif componente.objetivo_efecto != objetivo:
                if not dry_run:
                    componente.objetivo_efecto = objetivo
                    componente.save(update_fields=['objetivo_efecto'])
                comps_actualizados += 1
                self._log(
                    f'COMPONENTE {codigo_pdf}->{eje_codigo}/{comp_codigo}: '
                    f'objetivo_efecto actualizado', dry_run,
                )
            else:
                comps_omitidos += 1

        self.stdout.write(self.style.SUCCESS(
            'Carga de objetivos PDESA completada (dry-run=%s):' % dry_run,
        ))
        self.stdout.write(
            f'  Ejes: {ejes_creados} creados, {ejes_actualizados} actualizados, '
            f'{ejes_omitidos} omitidos (total {ejes_creados + ejes_actualizados + ejes_omitidos})',
        )
        self.stdout.write(
            f'  Componentes: {comps_creados} creados, {comps_actualizados} actualizados, '
            f'{comps_omitidos} omitidos '
            f'(total {comps_creados + comps_actualizados + comps_omitidos})',
        )

    def _log(self, mensaje: str, dry_run: bool):
        if dry_run:
            self.stdout.write(f'  [dry-run] {mensaje}')
