"""Carga el Presupuesto General de Recursos de una gestión.

    python manage.py sembrar_presupuesto_recursos --gestion 2027

Los montos son los del reporte oficial "MUNICIPIO DE SACABA - PLAN OPERATIVO
ANUAL 2027 / PRESUPUESTO GENERAL DE RECURSOS". Idempotente: reejecutarlo
reemplaza los rubros de la versión en borrador sin duplicar.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.budget.models import (
    EstadosTecho, OrigenRecurso, RecursoTecho, TechoDirectivo, TechoVersion,
)
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.gestion.models import GestionFiscal

D = Decimal

# (concepto, fuente, organismo, monto, corriente, inversion, [componentes])
# El corte corriente/inversión va solo en el rubro agrupador; los componentes
# aportan su monto. Los porcentajes no se cargan: se calculan.
RUBROS = [
    ('Coparticipación Tributaria', '41', '113',
     D('217742150.00'), D('35681491.00'), D('182060659.00'), [
         ('Coparticipación Tributaria', '41', '113', D('183992116.75')),
         ('Prestación de Servicios de Salud Integral', '41', '113', D('33750033.25')),
     ]),
    ('Recursos Específicos', '20', '210',
     D('90000000.00'), D('23518119.00'), D('66481881.00'), []),
    ('Recursos Específicos Salud', '20', '230',
     D('830000.00'), D('0.00'), D('830000.00'), []),
    ('Impuestos Directos a Hidrocarburos - IDH', '41', '119',
     D('27320808.00'), D('0.00'), D('27320808.00'), [
         ('Coparticipación Impuesto Directo Hidrocarburos', '41', '119', D('1114291.00')),
         ('Nivelación Impuesto Directo Hidrocarburos', '41', '119', D('19537553.00')),
         ('Compensación Impuesto Directo Hidrocarburos', '41', '119', D('6668964.00')),
     ]),
    ('Saldo Gestión anterior', None, None,
     D('0.00'), D('0.00'), D('0.00'), [
         ('Saldos Caja Bancos en Salud', '20', '230', D('0.00')),
         ('Saldos Caja Bancos Impuestos Directos a los Hidrocarburos', '41', '119', D('0.00')),
         ('Saldos Caja Bancos Coparticipación Tributaria', '41', '113', D('0.00')),
     ]),
    ('Del Tesoro General de la Nación (Bono discapacidad)', '41', '111',
     D('227539.00'), D('0.00'), D('227539.00'), []),
]


class Command(BaseCommand):
    help = 'Carga el Presupuesto General de Recursos de una gestión.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2027)

    @transaction.atomic
    def handle(self, *args, **opciones):
        anio = opciones['gestion']
        try:
            gestion = GestionFiscal.objects.get(anio=anio)
        except GestionFiscal.DoesNotExist:
            raise CommandError(f'No existe la gestión fiscal {anio}.')

        techo, creado = TechoDirectivo.objects.get_or_create(
            gestion=gestion,
            defaults={'estado': EstadosTecho.BORRADOR, 'version_actual': 1},
        )
        version, _ = TechoVersion.objects.get_or_create(
            ceiling=techo, numero=techo.version_actual,
            defaults={'estado': EstadosTecho.BORRADOR},
        )
        if version.inmutable:
            raise CommandError(
                f'La versión {version.numero} está fijada: no admite cambios.'
            )

        version.recursos.all().delete()

        fuentes = {f.codigo: f for f in FuenteFinanciamiento.objects.all()}
        organismos = {o.codigo: o for o in OrganismoFinanciador.objects.all()}

        def crear(concepto, ff, of, monto, corriente=None, inversion=None,
                  padre=None, orden=0):
            return RecursoTecho.objects.create(
                version=version, origen=OrigenRecurso.SIGEP, concepto=concepto,
                fuente=fuentes.get(ff), organismo=organismos.get(of),
                monto=monto, monto_corriente=corriente, monto_inversion=inversion,
                padre=padre, orden=orden,
            )

        total = Decimal('0')
        for i, (concepto, ff, of, monto, corr, inv, hijos) in enumerate(RUBROS):
            rubro = crear(concepto, ff, of, monto, corr, inv, orden=i)
            total += monto
            for j, (c_hijo, ff_h, of_h, monto_h) in enumerate(hijos):
                crear(c_hijo, ff_h, of_h, monto_h, padre=rubro, orden=j)

        self.stdout.write(self.style.SUCCESS(
            f'Gestión {anio}: {len(RUBROS)} rubros, '
            f'{RecursoTecho.objects.filter(version=version).count()} filas. '
            f'Total Bs {total:,.2f}'
        ))
