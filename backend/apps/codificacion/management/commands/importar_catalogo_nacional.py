"""Importa el CATÁLOGO NACIONAL MAESTRO PGDES/PDES desde el XLSX oficial.

Uso:
    python manage.py importar_catalogo_nacional [--archivo RUTA]
        [--gestion 2025] [--dry-run]

Fuente: ``catalogo_nacional_maestro_ptdi_sis_pe_pgdes_pdes_2021_2025.xlsx``
(catálogo oficial SIS-PE, control de calidad verificado). PGDES / Agenda
Patriótica 2025 (Ley N° 650 de 15/01/2015) y PDES 2021-2025 (Ley N° 1407 de
09/11/2021).

Mapeo de hojas → modelos:
- ``00_INSTRUMENTOS`` → ``planificacion.Plan`` + ``VersionCatalogoPlan``
  vigente por plan.
- ``01_PGDES_PILARES`` (13) → ``EjePGDESA`` (código oficial 01..13).
- ``02_PDES_EJES`` (10) → ``ComponentePDESA`` (padre: pilar articulado de la
  hoja ``06_PILAR_EJE``).
- ``03_PDES_METAS`` (44) / ``04_PDES_RESULTADOS`` (156) /
  ``05_PDES_ACCIONES`` (227) → ``NodoPlanificacion`` (niveles meta,
  resultado y accion_nacional, con la jerarquía padre del código oficial).
- ``06_PILAR_EJE`` (19 ARTICULA) → ``ArticulacionPlanificacion`` pilar→eje.
- ``08_FUENTES`` (5) → ``normativa.VersionNormativa``.
- ``07_RELACIONES`` (446): CONTIENE/DESAGREGA/OPERATIVIZA quedan implícitas
  en la FK padre de los nodos; solo se materializan las ARTICULA.

Idempotente: ``update_or_create`` por clave natural (codigo+versión).
No borra registros demo: los datos oficiales viven en versiones nuevas y el
demo queda intacto en sus propias versiones.
"""
import os
import re
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    VersionCatalogoPlan,
)
from apps.normativa.models import VersionNormativa
from apps.planificacion.models import (
    ArticulacionPlanificacion,
    NodoPlanificacion,
    Plan,
)

RUTA_XLSX_DEFECTO = os.environ.get(
    'CATALOGO_NACIONAL_XLSX',
    'C:\\Users\\Metatron\\Desktop\\Documentos\\SIS POA\\BASE DE DATOS\\'
    'catalogo_nacional_maestro_ptdi_sis_pe_pgdes_pdes_2021_2025.xlsx',
)

HOJAS = {
    'instrumentos': '00_INSTRUMENTOS',
    'pilares': '01_PGDES_PILARES',
    'ejes': '02_PDES_EJES',
    'metas': '03_PDES_METAS',
    'resultados': '04_PDES_RESULTADOS',
    'acciones': '05_PDES_ACCIONES',
    'pilar_eje': '06_PILAR_EJE',
    'relaciones': '07_RELACIONES',
    'fuentes': '08_FUENTES',
}

TIPO_NORMATIVA = {
    'LEY': VersionNormativa.tipo.field.choices[0][0],  # 'ley'
    'PLAN': 'otro',
}

GESTION_PGDES_DEFECTO = 2025
GESTION_PDES_DEFECTO = 2021


def _filas(ws):
    """Convierte una hoja en listas de dicts (cabecera → valor)."""
    filas = list(ws.iter_rows(values_only=True))
    if not filas:
        return []
    cabeceras = [str(c).strip() if c is not None else '' for c in filas[0]]
    return [
        dict(zip(cabeceras, fila))
        for fila in filas[1:]
        if any(v is not None for v in fila)
    ]


def _texto(valor):
    if valor is None:
        return ''
    return str(valor).strip()


def _entero(valor):
    texto = _texto(valor)
    if not texto:
        return None
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None


def _codigo_2_digitos(valor):
    numero = _entero(valor)
    return str(numero).zfill(2) if numero is not None else ''


def _fecha(valor):
    texto = _texto(valor)
    if not texto:
        return None
    coincidencia = re.match(r'^(\d{4})-(\d{2})-(\d{2})', texto)
    if coincidencia:
        return date(*(int(g) for g in coincidencia.groups()))
    return None


class Command(BaseCommand):
    help = (
        'Importa el catálogo nacional maestro PGDES/PDES desde el XLSX '
        'oficial (pilares, ejes, metas, resultados, acciones, relaciones '
        'y fuentes) a los catálogos de codificacion y al árbol de '
        'planificación. Idempotente por codigo+version.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            default=RUTA_XLSX_DEFECTO,
            help='Ruta del XLSX del catálogo nacional maestro.',
        )
        parser.add_argument(
            '--gestion',
            type=int,
            default=None,
            help=(
                'Gestión de las versiones de catálogo. Por defecto: 2025 '
                'para PGDES (fin de horizonte) y 2021 para PDES (inicio).'
            ),
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Planifica y cuenta sin persistir (rollback al final).',
        )

    def handle(self, *args, **options):
        ruta = Path(options['archivo']).expanduser().resolve()
        if not ruta.exists():
            raise CommandError(f'No existe el XLSX: {ruta}')

        if options['dry_run']:
            with transaction.atomic():
                resumen = self._importar(ruta, options['gestion'])
                transaction.set_rollback(True)
        else:
            resumen = self._importar(ruta, options['gestion'])

        self._volcar_resumen(resumen, dry_run=options['dry_run'])

    # ------------------------------------------------------------------
    # Importación
    # ------------------------------------------------------------------
    def _importar(self, ruta, gestion_override):
        resumen = {'modelos': {}, 'omitidos': [], 'plan': {}, 'gestion': {}}

        libro = load_workbook(ruta, read_only=True, data_only=True)
        try:
            hojas = {
                nombre: _filas(libro[hoja])
                for nombre, hoja in HOJAS.items()
            }
        finally:
            libro.close()

        instrumentos = {
            fila['instrumento_id']: fila for fila in hojas['instrumentos']
        }
        inst_pgdes = next(
            f for f in instrumentos.values() if f['tipo'] == 'PGDES'
        )
        inst_pdes = next(
            f for f in instrumentos.values() if f['tipo'] == 'PDES'
        )

        gestion_pgdes = gestion_override or GESTION_PGDES_DEFECTO
        gestion_pdes = gestion_override or GESTION_PDES_DEFECTO
        resumen['gestion'] = {
            'pgdes': gestion_pgdes,
            'pdes': gestion_pdes,
        }

        plan_pgdes = self._plan_para(inst_pgdes, 'pgdesa')
        plan_pdes = self._plan_para(inst_pdes, 'pdesa')
        version_pgdes = self._version_vigente(plan_pgdes, gestion_pgdes, inst_pgdes)
        version_pdes = self._version_vigente(plan_pdes, gestion_pdes, inst_pdes)
        resumen['plan'] = {
            'pgdes': plan_pgdes.codigo,
            'pdes': plan_pdes.codigo,
        }

        pilares = self._importar_ejes_pgdesa(hojas['pilares'], version_pgdes)
        componentes = self._importar_componentes_pdesa(
            hojas['ejes'], hojas['pilar_eje'], version_pdes, pilares,
        )

        nodos = self._importar_nodos_planificacion(
            hojas, plan_pgdes, plan_pdes,
            gestion_pgdes, gestion_pdes,
        )

        self._importar_articulaciones(
            hojas['pilar_eje'], nodos, gestion_pdes,
        )

        self._importar_fuentes(hojas['fuentes'])

        self._conteos(resumen)
        resumen['omitidos'] = (
            self._decisiones_omision(hojas, componentes)
        )
        return resumen

    def _plan_para(self, instrumento, tipo_plan):
        """Reutiliza el Plan por (codigo, tipo) o lo crea para el instrumento."""
        codigo = instrumento['codigo']
        gestion_inicio = _entero(instrumento['gestion_inicio'])
        gestion_fin = _entero(instrumento['gestion_fin']) or gestion_inicio
        plan, _ = Plan.objects.get_or_create(
            codigo=codigo,
            tipo=tipo_plan,
            defaults={
                'nombre': instrumento['nombre'][:500],
                'gestion_inicio': gestion_inicio,
                'gestion_fin': gestion_fin,
                'fecha_vigencia_desde': date(gestion_inicio, 1, 1),
                'fecha_vigencia_hasta': date(gestion_fin, 12, 31),
                'descripcion': (
                    'Importado del catálogo nacional maestro SIS-PE '
                    f'({instrumento["codigo"]}).'
                ),
                'activo': True,
            },
        )
        return plan

    def _version_vigente(self, plan, gestion, instrumento):
        version, creada = VersionCatalogoPlan.objects.get_or_create(
            plan=plan,
            gestion=gestion,
            defaults={
                'estado': VersionCatalogoPlan.ESTADO_VIGENTE,
                'norma_aprobacion': _texto(
                    instrumento.get('norma_aprobacion')
                ),
                'clasificacion_fuente': VersionCatalogoPlan.FUENTE_OFICIAL,
                'procedencia_fuente': (
                    'Importado del catálogo nacional maestro SIS-PE '
                    '(XLSX oficial 2021-2025).'
                ),
            },
        )
        if not creada and version.estado != VersionCatalogoPlan.ESTADO_VIGENTE:
            hay_otra_vigente = VersionCatalogoPlan.objects.filter(
                plan=plan,
                estado=VersionCatalogoPlan.ESTADO_VIGENTE,
            ).exclude(pk=version.pk).exists()
            if not hay_otra_vigente:
                version.estado = VersionCatalogoPlan.ESTADO_VIGENTE
                version.save(update_fields=['estado', 'updated_at'])
        return version

    def _importar_ejes_pgdesa(self, filas, version):
        """01_PGDES_PILARES → EjePGDESA (código oficial 01..13)."""
        por_sistema = {}
        for fila in filas:
            codigo = _codigo_2_digitos(fila['codigo_oficial'])
            if not codigo:
                continue
            obj, _ = EjePGDESA.objects.update_or_create(
                codigo=codigo,
                version_catalogo=version,
                defaults={
                    'denominacion': _texto(fila['denominacion'])[:500],
                    'activo': True,
                },
            )
            por_sistema[fila['codigo_sistema']] = obj
        return por_sistema

    def _importar_componentes_pdesa(
        self, filas, pilar_eje, version, pilares_por_sistema,
    ):
        """02_PDES_EJES → ComponentePDESA, padre = pilar articulado.

        La FK ``eje`` es obligatoria; el pilar padre se resuelve con la
        primera relación ARTICULA de la hoja 06_PILAR_EJE (pilar→eje).
        """
        primer_pilar = {}
        for fila in sorted(
            pilar_eje, key=lambda f: _entero(f['relacion_id']) or 0,
        ):
            primer_pilar.setdefault(fila['eje_codigo'], fila['pilar_codigo'])

        componentes = {}
        for fila in filas:
            codigo = _codigo_2_digitos(fila['codigo_oficial'])
            if not codigo:
                continue
            eje = pilares_por_sistema.get(
                primer_pilar.get(fila['codigo_sistema'])
            )
            if eje is None:
                continue
            obj, _ = ComponentePDESA.objects.update_or_create(
                eje=eje,
                codigo=codigo,
                version_catalogo=version,
                defaults={
                    'denominacion': _texto(fila['denominacion'])[:500],
                    'activo': True,
                },
            )
            componentes[fila['codigo_sistema']] = obj
        return componentes

    def _importar_nodos_planificacion(
        self, hojas, plan_pgdes, plan_pdes,
        gestion_pgdes, gestion_pdes,
    ):
        """Pilares, ejes, metas, resultados y acciones → NodoPlanificacion.

        Jerarquía padre por código oficial: eje (E01) → meta (1.1) →
        resultado (1.1.1) → acción (1.1.1.1). Las acciones del marco
        nacional usan el nivel ``accion_nacional``.
        """
        nodos = {'pilar': {}, 'eje': {}, 'meta': {}, 'resultado': {}, 'accion': {}}

        def _nodo(plan, nivel, codigo, nombre, gestion, orden=0, padre=None):
            nodo, _ = NodoPlanificacion.objects.update_or_create(
                plan=plan,
                codigo=codigo,
                nivel=nivel,
                defaults={
                    'nombre': nombre,
                    'gestion': gestion,
                    'orden': orden,
                    'padre': padre,
                    'activo': True,
                },
            )
            return nodo

        for fila in hojas['pilares']:
            nodos['pilar'][fila['codigo_sistema']] = _nodo(
                plan_pgdes, 'pilar', _texto(fila['codigo_oficial']),
                _texto(fila['denominacion']), gestion_pgdes,
                orden=_entero(fila['numero']) or 0,
            )
        for fila in hojas['ejes']:
            nodos['eje'][fila['codigo_sistema']] = _nodo(
                plan_pdes, 'eje', _texto(fila['codigo_oficial']),
                _texto(fila['denominacion']), gestion_pdes,
                orden=_entero(fila['numero']) or 0,
            )
        for fila in hojas['metas']:
            eje = nodos['eje'].get(_codigo_sistema_eje(fila['eje_id'], hojas))
            nodos['meta'][fila['codigo_sistema']] = _nodo(
                plan_pdes, 'meta', _texto(fila['codigo_oficial']),
                _texto(fila['denominacion']), gestion_pdes,
                orden=_entero(fila['orden']) or 0,
                padre=eje,
            )
        for fila in hojas['resultados']:
            meta = nodos['meta'].get(_codigo_sistema_meta(fila['meta_id'], hojas))
            nodos['resultado'][fila['codigo_sistema']] = _nodo(
                plan_pdes, 'resultado', _texto(fila['codigo_oficial']),
                _texto(fila['denominacion']), gestion_pdes,
                orden=_entero(fila['orden']) or 0,
                padre=meta,
            )
        for fila in hojas['acciones']:
            resultado = nodos['resultado'].get(
                _codigo_sistema_resultado(fila['resultado_id'], hojas)
            )
            nodos['accion'][fila['codigo_sistema']] = _nodo(
                plan_pdes, 'accion_nacional', _texto(fila['codigo_oficial']),
                _texto(fila['denominacion']), gestion_pdes,
                orden=_entero(fila['orden']) or 0,
                padre=resultado,
            )
        return nodos

    def _importar_articulaciones(self, pilar_eje, nodos, gestion):
        """06_PILAR_EJE (ARTICULA) → ArticulacionPlanificacion pilar→eje."""
        for fila in pilar_eje:
            origen = nodos['pilar'].get(fila['pilar_codigo'])
            destino = nodos['eje'].get(fila['eje_codigo'])
            if origen is None or destino is None:
                continue
            ArticulacionPlanificacion.objects.update_or_create(
                nodo_origen=origen,
                nodo_destino=destino,
                gestion=gestion,
                defaults={'es_principal': True},
            )

    def _importar_fuentes(self, filas):
        """08_FUENTES → normativa.VersionNormativa."""
        for fila in filas:
            titulo = _texto(fila['titulo'])
            if not titulo:
                continue
            coincidencia = re.search(
                r'Ley\s*N[º°]?\s*(\d+)', titulo, re.IGNORECASE,
            )
            numero = coincidencia.group(1) if coincidencia else ''
            fecha = _fecha(fila['fecha'])
            gestion = _entero(_texto(fila['fecha'])[:4]) or (
                fecha.year if fecha else GESTION_PDES_DEFECTO
            )
            VersionNormativa.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'tipo': TIPO_NORMATIVA.get(_texto(fila['tipo']), 'otro'),
                    'numero': numero,
                    'fecha_emision': fecha,
                    'gestion': gestion,
                    'resumen': _texto(fila['uso']),
                    'activo': True,
                },
            )

    # ------------------------------------------------------------------
    # Reporte
    # ------------------------------------------------------------------
    def _conteos(self, resumen):
        for etiqueta, queryset in (
            ('EjePGDESA (pilares PGDES)', EjePGDESA.objects.all()),
            ('ComponentePDESA (ejes PDES)', ComponentePDESA.objects.all()),
            ('NodoPlanificacion', NodoPlanificacion.objects.all()),
            ('ArticulacionPlanificacion', ArticulacionPlanificacion.objects.all()),
            ('VersionNormativa (fuentes)', VersionNormativa.objects.all()),
        ):
            resumen['modelos'][etiqueta] = queryset.count()

    def _decisiones_omision(self, hojas, componentes):
        omisiones = [
            (
                'SectorEconomico y ResultadoSectorial: el XLSX oficial no '
                'trae sectores del clasificador ni resultados sectoriales; '
                'no se inventan datos y las tablas quedan como están.'
            ),
            (
                'LineamientoPAD: el XLSX no trae lineamientos PAD '
                '(catálogo municipal, no nacional); no se cargan.'
            ),
            (
                '07_RELACIONES CONTIENE/DESAGREGA/OPERATIVIZA: quedan '
                'implícitas en la FK padre de NodoPlanificacion; solo se '
                'materializan las 19 ARTICULA pilar->eje.'
            ),
        ]
        if len(componentes) < len(hojas['ejes']):
            omisiones.append(
                'ComponentePDESA: algunos ejes PDES no tienen pilar '
                'articulado en 06_PILAR_EJE y se omitieron.'
            )
        return omisiones

    def _volcar_resumen(self, resumen, dry_run):
        modo = 'DRY-RUN (nada persistido)' if dry_run else 'COMMIT (persistido)'
        self.stdout.write(
            self.style.MIGRATE_HEADING(f'\nCatálogo nacional maestro ({modo})')
        )
        self.stdout.write(
            f"Planes: PGDES={resumen['plan']['pgdes']} "
            f"(versión vigente {resumen['gestion']['pgdes']}) | "
            f"PDES={resumen['plan']['pdes']} "
            f"(versión vigente {resumen['gestion']['pdes']})"
        )
        for etiqueta, conteo in sorted(resumen['modelos'].items()):
            self.stdout.write(f'  {etiqueta}: {conteo}')
        if resumen['omitidos']:
            self.stdout.write(self.style.WARNING('  Decisiones (no cargado):'))
            for omision in resumen['omitidos']:
                self.stdout.write(self.style.WARNING(f'    - {omision}'))


def _codigo_sistema_eje(eje_id, hojas):
    for fila in hojas['ejes']:
        if fila['elemento_id'] == eje_id:
            return fila['codigo_sistema']
    return None


def _codigo_sistema_meta(meta_id, hojas):
    for fila in hojas['metas']:
        if fila['elemento_id'] == meta_id:
            return fila['codigo_sistema']
    return None


def _codigo_sistema_resultado(resultado_id, hojas):
    for fila in hojas['resultados']:
        if fila['elemento_id'] == resultado_id:
            return fila['codigo_sistema']
    return None
