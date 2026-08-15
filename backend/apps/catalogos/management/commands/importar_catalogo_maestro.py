"""Comando único de importación del catálogo maestro (SISPAD-PEI-POA).

Uso:
    python manage.py importar_catalogo_maestro [--lote LOTE] [--gestion 2026]
        [--dry-run|--no-dry-run] [--commit] [--reporte-json RUTA]

Lotes (orden crítico): L0 GestionFiscal 2026 → (L1 clasificadores + L5
reglas) → (L2 marco superior + L3 acuerdos) → L4 sispoa → L6 dominios →
L7 geográfico/sector. Por defecto ejecuta TODO en modo dry-run: lee,
transforma y cuenta sin persistir (transaction.atomic + rollback).

FUENTE DE DATOS: el comando lee los esquemas ``core|catalogo|sispe|sispoa``
(``catalogo.clasificador_item``, ``catalogo.regla_gam``, ``sispe.elemento``,
``sispoa.catalogo_programa``, ...) de la BD LEGACY del MEFP, NO de la BD de
SISPOA. La conexión Django activa debe apuntar a un servidor que exponga
esos esquemas (p. ej. el dump de producción con GRANT de lectura), o bien
replicarlos previamente en la BD local. Sin esa BD el comando falla con
ProgrammingError en el primer SELECT.
"""
import argparse
import json
from datetime import datetime

from django.db import transaction
from django.core.management.base import BaseCommand

from apps.catalogos.importer import (
    acuerdos,
    clasificadores,
    dominios,
    geografico,
    marco_superior,
    reglas,
    sector,
    sispoa,
)
from apps.catalogos.importer.base import ReporteLote, upsert
from apps.gestion.models import GestionFiscal

LOTE_CLASIFICADORES = 'clasificadores'
LOTE_MARCO_SUPERIOR = 'marco_superior'
LOTE_ACUERDOS = 'acuerdos'
LOTE_SISPOA = 'sispoa'
LOTE_REGLAS = 'reglas'
LOTE_DOMINIOS = 'dominios'
LOTE_GEOGRAFICO = 'geografico'
LOTE_SECTOR = 'sector'
LOTE_TODOS = 'todos'

LOTES = [
    LOTE_CLASIFICADORES,
    LOTE_MARCO_SUPERIOR,
    LOTE_ACUERDOS,
    LOTE_SISPOA,
    LOTE_REGLAS,
    LOTE_DOMINIOS,
    LOTE_GEOGRAFICO,
    LOTE_SECTOR,
]

# Orden crítico (spec §6): L1+L5 → L2+L3 → L4 → L6 → L7.
ORDEN_CRITICO = [
    LOTE_CLASIFICADORES,
    LOTE_REGLAS,
    LOTE_MARCO_SUPERIOR,
    LOTE_ACUERDOS,
    LOTE_SISPOA,
    LOTE_DOMINIOS,
    LOTE_GEOGRAFICO,
    LOTE_SECTOR,
]


def importar_gestion_fiscal(reporte, gestion):
    """L0 — réplica de GestionFiscal 2026 abierta (upsert por anio).

    Sin ella ningún formulario 2026 opera en dev (H10/R7). La gestión de
    trabajo 2027 (preparación) se conserva tal cual.
    """
    if gestion == 2026:
        gestion_2026, creado = GestionFiscal.objects.get_or_create(
            anio=2026,
            defaults={
                'estado': GestionFiscal.Estado.ABIERTA,
                'descripcion': (
                    'Réplica 2026 creada por el importador del catálogo '
                    'maestro (clasificadores 2026 vigentes).'
                ),
                'activa': True,
            },
        )
        if creado:
            reporte.creados += 1
        elif gestion_2026.estado != GestionFiscal.Estado.ABIERTA:
            gestion_2026.estado = GestionFiscal.Estado.ABIERTA
            gestion_2026.save(update_fields=['estado', 'actualizado_en'])
            reporte.actualizados += 1
        else:
            reporte.omitidos += 1
    else:
        GestionFiscal.objects.get_or_create(
            anio=gestion,
            defaults={
                'estado': GestionFiscal.Estado.PREPARACION,
                'descripcion': 'Gestión de trabajo (importador catálogo).',
                'activa': True,
            },
        )
    reporte.conteos_modelo['GestionFiscal'] = (
        GestionFiscal.objects.filter(anio__in=[2026, gestion]).count()
    )


FUNCIONES_LOTE = {
    LOTE_CLASIFICADORES: clasificadores.importar,
    LOTE_MARCO_SUPERIOR: marco_superior.importar,
    LOTE_ACUERDOS: acuerdos.importar,
    LOTE_SISPOA: sispoa.importar,
    LOTE_REGLAS: reglas.importar,
    LOTE_DOMINIOS: dominios.importar,
    LOTE_GEOGRAFICO: geografico.importar,
    LOTE_SECTOR: sector.importar,
}


class Command(BaseCommand):
    help = (
        'Importa el catálogo maestro (esquemas core|catalogo|sispe|sispoa) '
        'a los modelos Django de SISPOA. Por defecto es dry-run (no '
        'persiste); use --commit o --no-dry-run para persistir.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--lote',
            choices=[*LOTES, LOTE_TODOS],
            default=LOTE_TODOS,
            help='Lote a importar (default: todos en orden crítico).',
        )
        parser.add_argument(
            '--dry-run',
            action=argparse.BooleanOptionalAction,
            default=True,
            help='Solo planifica (default: True). Use --no-dry-run o --commit.',
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Persiste los cambios (desactiva --dry-run).',
        )
        parser.add_argument(
            '--gestion',
            type=int,
            choices=[2026, 2027],
            default=2026,
            help='Gestión de importación de los clasificadores (default 2026).',
        )
        parser.add_argument(
            '--reporte-json',
            dest='reporte_json',
            default=None,
            help='Ruta del archivo JSON con el reporte final.',
        )

    def _registrar_error(self, nombre_lote, reporte, exc):
        reporte.errores += 1
        reporte.warnings.append(
            f'Error en lote {nombre_lote}: {type(exc).__name__}: {exc}'
        )
        self.stderr.write(
            self.style.ERROR(
                f'Lote {nombre_lote} falló: {type(exc).__name__}: {exc}'
            )
        )

    def _volcar_reporte(self, nombre_lote, reporte, reporte_global):
        reporte_global['lotes'].append(reporte.to_dict())
        resumen = reporte_global['resumen']
        resumen['creados'] += reporte.creados
        resumen['actualizados'] += reporte.actualizados
        resumen['omitidos'] += reporte.omitidos
        resumen['errores'] += reporte.errores
        resumen['warnings'] += len(reporte.warnings)

        estado = 'OK' if reporte.errores == 0 else 'ERROR'
        self.stdout.write(
            self.style.SUCCESS(f'[{estado}] Lote {nombre_lote}')
            if reporte.errores == 0
            else self.style.ERROR(f'[ERROR] Lote {nombre_lote}')
        )
        self.stdout.write(
            f'  fuente: {reporte.fuente or "—"} | creados: '
            f'{reporte.creados} | actualizados: {reporte.actualizados} | '
            f'omitidos: {reporte.omitidos} | errores: {reporte.errores}'
        )
        for warning in reporte.warnings:
            self.stdout.write(self.style.WARNING(f'  [!] {warning}'))
        for modelo, conteo in sorted(reporte.conteos_modelo.items()):
            self.stdout.write(f'  {modelo}: {conteo}')

    def handle(self, *args, **options):
        dry_run = not options['commit'] and options['dry_run'] is not False
        gestion = options['gestion']
        lote = options['lote']
        lotes = ORDEN_CRITICO if lote == LOTE_TODOS else [lote]

        reporte_global = {
            'comando': 'importar_catalogo_maestro',
            'dry_run': dry_run,
            'gestion': gestion,
            'lotes': [],
            'ejecutado_en': datetime.now().isoformat(timespec='seconds'),
            'resumen': {
                'creados': 0,
                'actualizados': 0,
                'omitidos': 0,
                'errores': 0,
                'warnings': 0,
            },
        }

        if dry_run:
            # Un único bloque atómico simula el commit secuencial: cada
            # lote usa un savepoint (si falla, revierte solo su savepoint y
            # el proceso continúa) y al final se revierte TODO (nada
            # persiste). Así los lotes posteriores ven los datos de los
            # anteriores, igual que en un commit real.
            try:
                with transaction.atomic():
                    self._ejecutar_lotes(lotes, gestion, reporte_global)
                    transaction.set_rollback(True)
            except transaction.TransactionManagementError:
                pass
        else:
            self._ejecutar_lotes(lotes, gestion, reporte_global)

        if options['reporte_json']:
            with open(options['reporte_json'], 'w', encoding='utf-8') as archivo:
                json.dump(reporte_global, archivo, ensure_ascii=False, indent=2)
            self.stdout.write(
                f'Reporte JSON escrito en {options["reporte_json"]}'
            )

        modo = 'DRY-RUN (nada persistido)' if dry_run else 'COMMIT (persistido)'
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f'\nResumen ({modo}): {reporte_global["resumen"]}'
            )
        )

    def _ejecutar_lotes(self, lotes, gestion, reporte_global):
        for nombre_lote in lotes:
            reporte = ReporteLote(lote=nombre_lote)
            if nombre_lote == 'sispoa':
                # L0 (GestionFiscal) se resuelve siempre antes del lote 4.
                importar_gestion_fiscal(reporte, gestion)
            try:
                with transaction.atomic():
                    gestion_lote = (
                        sispoa.GESTION_SISPOA
                        if nombre_lote == LOTE_SISPOA else gestion
                    )
                    FUNCIONES_LOTE[nombre_lote](reporte, gestion_lote)
            except Exception as exc:  # noqa: BLE001 — reporte y continúa
                self._registrar_error(nombre_lote, reporte, exc)
            self._volcar_reporte(nombre_lote, reporte, reporte_global)
