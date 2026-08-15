"""Carga los dominios de catalogo desde los estandares MEFP 2027.

Los catalogos de dominio (unidades de medida, tipos de operacion, tipos de
producto/proyecto/financiamiento) son estandares del clasificador MEFP 2027.
Este command los carga de forma idempotente por (codigo, gestion) como
CatalogoBase, con la fuente normativa RM N. 271/2026 (Clasificadores
Presupuestarios Gestion 2027) y metadatos de importacion.

Complementa al importador ETL (`importar_catalogo_maestro`) que lee la BD
legacy MEFP (`catalogo.dominio_item`) cuando esta disponible; este command
cubre el mismo lote L6 con valores oficiales embebidos, sin BD externa.
"""
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogos.models import (
    UnidadMedida, TipoOperacion, TipoProducto, TipoProyecto, TipoFinanciamiento,
)

GESTION_DEFAULT = 2027
NORMA = 'RM N. 271/2026 - Clasificadores Presupuestarios Gestion 2027'


class Command(BaseCommand):
    help = 'Carga dominios de catalogo (unidades de medida, tipos) desde los estandares MEFP 2027'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=GESTION_DEFAULT)

    @transaction.atomic
    def handle(self, *args, **options):
        gestion = options['gestion']
        vigencia = date(gestion, 1, 1)
        creados = 0
        actualizados = 0

        def cargar(modelo, items):
            nonlocal creados, actualizados
            for codigo, denominacion, descripcion in items:
                _, created = modelo.objects.update_or_create(
                    codigo=codigo, gestion=gestion,
                    defaults={
                        'denominacion': denominacion,
                        'descripcion': descripcion,
                        'fecha_vigencia_desde': vigencia,
                        'activo': True,
                        'fuente_normativa': NORMA,
                        'metadatos_importacion': {
                            'fuente': 'clasificadores-mefp-2027',
                            'norma': NORMA,
                        },
                    },
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1

        # Unidades de medida (13) — clasificador MEFP 2027.
        cargar(UnidadMedida, [
            ('PORC', 'Porcentaje', '%'),
            ('NUM', 'Número', 'Cantidad'),
            ('UN', 'Unidad', 'Unidad'),
            ('M2', 'Metro cuadrado', 'm2'),
            ('KM', 'Kilómetro', 'km'),
            ('HA', 'Hectárea', 'ha'),
            ('PER', 'Persona', 'Persona'),
            ('FAM', 'Familia', 'Familia'),
            ('TASA', 'Tasa', 'Tasa'),
            ('M3', 'Metro cúbico', 'm3'),
            ('ML', 'Metro lineal', 'ml'),
            ('KG', 'Kilogramo', 'kg'),
            ('LT', 'Litro', 'l'),
        ])

        # Tipos de operación (2) — operaciones del POAU.
        cargar(TipoOperacion, [
            ('CORRIENTE', 'Operación corriente', 'Gasto corriente'),
            ('INVERSION', 'Operación de inversión', 'Gasto de inversión'),
        ])

        # Tipos de producto (6) — productos institucionales del POA.
        cargar(TipoProducto, [
            ('BIEN', 'Bien', 'Producto físico (bien)'),
            ('SERVICIO', 'Servicio', 'Producto físico (servicio)'),
            ('NORMATIVA', 'Normativa', 'Norma emitida'),
            ('GESTION', 'Gestión/Planificación', 'Gestión y planificación'),
            ('CONTROL', 'Control y fiscalización', 'Control y fiscalización'),
            ('ESTUDIO', 'Estudio', 'Estudio técnico'),
        ])

        # Tipos de proyecto (5) — SIS-PRO.
        cargar(TipoProyecto, [
            ('INVERSION', 'Proyecto de inversión', 'Proyecto de inversión pública'),
            ('PREINVERSION', 'Preinversión', 'Estudio de preinversión'),
            ('INVERSION_RECURRENTE', 'Inversión recurrente', 'Inversión recurrente'),
            ('MANTENIMIENTO', 'Mantenimiento', 'Mantenimiento de activos'),
            ('OTRO', 'Otro', 'Otro tipo de proyecto'),
        ])

        # Tipos de financiamiento (4) — origen de recursos.
        cargar(TipoFinanciamiento, [
            ('TGN', 'Tesoro General de la Nación', 'Recursos del TGN'),
            ('COPARTICIPACION', 'Coparticipación tributaria', 'Recursos de coparticipación'),
            ('ESPECIFICOS', 'Recursos específicos', 'Recursos propios municipales'),
            ('EXTERNO', 'Financiamiento externo', 'Crédito o donación externa'),
        ])

        self.stdout.write(self.style.SUCCESS(
            f'Dominios gestion {gestion}: {creados} creados, {actualizados} actualizados '
            f'(UM {UnidadMedida.objects.filter(gestion=gestion).count()}, '
            f'TO {TipoOperacion.objects.filter(gestion=gestion).count()}, '
            f'TP {TipoProducto.objects.filter(gestion=gestion).count()}, '
            f'TProy {TipoProyecto.objects.filter(gestion=gestion).count()}, '
            f'TFin {TipoFinanciamiento.objects.filter(gestion=gestion).count()}).'
        ))
