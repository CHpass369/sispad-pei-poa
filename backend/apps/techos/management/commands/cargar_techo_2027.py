"""Carga el techo presupuestario 2027 de referencia (reporte RFprTechoPresup).

Uso:
    python manage.py cargar_techo_2027 [--gestion 2027] [--dry-run]

Los montos y conceptos provienen del PDF "TECHO PRESUPUESTARIO POA 2027
SACABA" (SIGEP): recursos por rubro/fuente/organismo/concepto y reservas de
gastos obligatorios. Crea en catálogos las fuentes y organismos con la
codificación SIGEP cuando no existan.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.techos.models import GastoObligatorio, RecursoTecho, TechoPresupuestario

RECURSOS_2027 = [
    {
        'rubro': '19.2.1.1',
        'rubro_descripcion': 'Por Subsidios o Subvenciones',
        'fuente_codigo': '41',
        'organismo_codigo': '119',
        'entidad_otorgante': 'Tesoro General de la Nación',
        'concepto': 'Impuesto Directo a los Hidrocarburos',
        'monto': '6,668,964.00',
    },
    {
        'rubro': '19.2.1.1',
        'rubro_descripcion': 'Por Subsidios o Subvenciones',
        'fuente_codigo': '41',
        'organismo_codigo': '119',
        'entidad_otorgante': 'Tesoro General de la Nación',
        'concepto': 'Nivelación IDH',
        'monto': '19,537,553.00',
    },
    {
        'rubro': '19.2.1.1',
        'rubro_descripcion': 'Por Subsidios o Subvenciones',
        'fuente_codigo': '41',
        'organismo_codigo': '111',
        'entidad_otorgante': 'Tesoro General de la Nación',
        'concepto': 'Transferencias T.G.N.',
        'monto': '227,539.00',
    },
    {
        'rubro': '19.2.1.2',
        'rubro_descripcion': 'Por Coparticipación Tributaria',
        'fuente_codigo': '41',
        'organismo_codigo': '113',
        'entidad_otorgante': 'Tesoro General de la Nación',
        'concepto': 'Coparticipación Tributaria',
        'monto': '217,742,150.00',
    },
    {
        'rubro': '19.2.1.2',
        'rubro_descripcion': 'Por Coparticipación Tributaria',
        'fuente_codigo': '41',
        'organismo_codigo': '119',
        'entidad_otorgante': 'Tesoro General de la Nación',
        'concepto': 'Impuesto Directo a los Hidrocarburos',
        'monto': '1,114,291.00',
    },
]

GASTOS_OBLIGATORIOS_2027 = [
    {
        'denominacion': 'Fondo de Fomento a la Educación Cívico Patriótica',
        'base_legal': 'Decreto Supremo N° 859 de 29 de abril de 2011',
        'fuente_codigo': '41',
        'organismo_codigo': '119',
        'monto': '41,304.00',
    },
    {
        'denominacion': 'Ayuda Económica para Personas con Discapacidad',
        'base_legal': 'Bono Mensual para Personas con Discapacidad',
        'fuente_codigo': '41',
        'organismo_codigo': '111',
        'monto': '227,539.00',
    },
    {
        'denominacion': 'Renta Dignidad',
        'base_legal': 'Ley N° 3791 de 28 de noviembre de 2007',
        'fuente_codigo': '41',
        'organismo_codigo': '119',
        'monto': '6,195,553.00',
    },
]

FUENTES_SIGEP = {
    '41': 'Transferencias del T.G.N.',
}

ORGANISMOS_SIGEP = {
    '111': 'Tesoro General de la Nación',
    '113': 'Tesoro General de la Nación - Coparticipación Tributaria',
    '119': 'T.G.N. - Impuesto Directo a los Hidrocarburos',
}


def _monto(texto):
    return Decimal(texto.replace(',', '').replace(' ', ''))


class Command(BaseCommand):
    help = 'Carga el techo presupuestario 2027 de referencia (SIGEP).'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2027)
        parser.add_argument('--dry-run', action='store_true')

    def _crear_fuente(self, gestion, codigo):
        from datetime import date
        fuente, _ = FuenteFinanciamiento.objects.get_or_create(
            codigo=codigo,
            gestion=gestion,
            defaults={
                'denominacion': FUENTES_SIGEP.get(codigo, f'Fuente {codigo}'),
                'fecha_vigencia_desde': date(gestion, 1, 1),
            },
        )
        return fuente

    def _crear_organismo(self, gestion, codigo):
        from datetime import date
        organismo, _ = OrganismoFinanciador.objects.get_or_create(
            codigo=codigo,
            gestion=gestion,
            defaults={
                'denominacion': ORGANISMOS_SIGEP.get(
                    codigo, f'Organismo {codigo}'
                ),
                'fecha_vigencia_desde': date(gestion, 1, 1),
            },
        )
        return organismo

    def handle(self, *args, **options):
        gestion = options['gestion']
        dry = options['dry_run']

        if dry:
            total = sum(_monto(r['monto']) for r in RECURSOS_2027)
            self.stdout.write(f'DRY-RUN: monto total techo {gestion}: Bs {total}')
            self.stdout.write(
                f'  recursos: {len(RECURSOS_2027)} · '
                f'gastos obligatorios: {len(GASTOS_OBLIGATORIOS_2027)}'
            )
            return

        @transaction.atomic
        def _ejecutar():
            fuente_41 = self._crear_fuente(gestion, '41')

            recursos = []
            for rec in RECURSOS_2027:
                organismo = self._crear_organismo(
                    gestion, rec['organismo_codigo']
                )
                recursos.append((rec, fuente_41, organismo))

            monto_total = sum(_monto(r['monto']) for r, _, _ in recursos)

            techo, creado = TechoPresupuestario.objects.get_or_create(
                gestion=gestion,
                fuente=fuente_41,
                defaults={
                    'monto_total': monto_total,
                    'concepto': 'Techo POA 2027 — SIGEP',
                    'descripcion': (
                        'Techo presupuestario de referencia cargado desde el '
                        'reporte RFprTechoPresup (SIGEP) para la gestión 2027.'
                    ),
                },
            )
            techo.monto_total = monto_total
            techo.save(update_fields=['monto_total', 'updated_at'])

            if not techo.recursos.exists():
                for orden, (rec, fuente, organismo) in enumerate(recursos, start=1):
                    RecursoTecho.objects.create(
                        techo=techo,
                        rubro=rec['rubro'],
                        rubro_descripcion=rec['rubro_descripcion'],
                        fuente=fuente,
                        organismo=organismo,
                        entidad_otorgante=rec['entidad_otorgante'],
                        concepto=rec['concepto'],
                        monto=_monto(rec['monto']),
                        orden=orden,
                    )

            if not techo.gastos_obligatorios.exists():
                for orden, gasto in enumerate(GASTOS_OBLIGATORIOS_2027, start=1):
                    organismo = self._crear_organismo(
                        gestion, gasto['organismo_codigo']
                    )
                    GastoObligatorio.objects.create(
                        techo=techo,
                        fuente=fuente_41,
                        organismo=organismo,
                        denominacion=gasto['denominacion'],
                        base_legal=gasto['base_legal'],
                        monto=_monto(gasto['monto']),
                        orden=orden,
                    )
            return techo

        techo = _ejecutar()
        self.stdout.write(
            self.style.SUCCESS(
                f'Techo {gestion} cargado: Bs {techo.monto_total} '
                f'({techo.recursos.count()} recursos, '
                f'{techo.gastos_obligatorios.count()} gastos obligatorios)'
            )
        )
