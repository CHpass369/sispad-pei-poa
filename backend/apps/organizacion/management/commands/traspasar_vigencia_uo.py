"""Traspasa la vigencia de las unidades organizacionales de una gestion a otra.

Problema que resuelve
---------------------
`unidades_organizacionales_disponibles_registro()` (apps/accounts/services.py)
ofrece en el registro publico solo las UO ya vigentes por fecha. Cuando la
gestion habilitada avanza antes que la vigencia del organigrama, el registro
sigue ofreciendo las UO del anio anterior y la aprobacion administrativa las
rechaza con «La unidad organizacional no pertenece a la gestion fiscal»:
`validar_gestion_fiscal_asignacion` exige que la UO pertenezca a la gestion
fiscal de la asignacion.

Que hace
--------
1. Abre la vigencia de las UO de la gestion destino (`fecha_vigencia_desde`).
2. Cierra la vigencia de las UO de la gestion origen (`fecha_vigencia_hasta`).

Los dos pasos son necesarios juntos. Abrir el destino sin cerrar el origen deja
las dos gestiones vigentes a la vez, y como los nombres se repiten casi uno a
uno entre anios, el desplegable del registro muestra cada unidad duplicada y sin
forma de distinguirlas: la mitad de los registros vuelve a elegir la gestion
equivocada.

Alcance del cambio
------------------
`fecha_vigencia_desde` / `fecha_vigencia_hasta` de UnidadOrganizacional solo se
LEEN en `unidades_organizacionales_disponibles_registro()`. El resto del codigo
unicamente las escribe al importar. El efecto observable se limita, entonces, a
que unidades ofrece el registro publico.

Uso::

    # 1. Ver que haria, sin tocar nada (por defecto):
    python manage.py traspasar_vigencia_uo --desde 2026 --hasta 2027

    # 2. Aplicarlo:
    python manage.py traspasar_vigencia_uo --desde 2026 --hasta 2027 --aplicar

    # 3. Volver atras (reabre origen, devuelve destino al 1 de enero):
    python manage.py traspasar_vigencia_uo --desde 2026 --hasta 2027 --revertir --aplicar

Idempotente: correrlo N veces deja el mismo estado.
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.organizacion.models import UnidadOrganizacional


class Command(BaseCommand):
    help = (
        'Abre la vigencia de las UO de la gestion destino y cierra la de la '
        'gestion origen, para que el registro publico ofrezca las correctas.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--desde', type=int, required=True,
            help='Anio de la gestion cuya vigencia se cierra.',
        )
        parser.add_argument(
            '--hasta', type=int, required=True,
            help='Anio de la gestion cuya vigencia se abre.',
        )
        parser.add_argument(
            '--fecha', type=str, default=None,
            help='Fecha de corte (YYYY-MM-DD). Por defecto, hoy.',
        )
        parser.add_argument(
            '--revertir', action='store_true',
            help='Deshace el traspaso: reabre el origen y devuelve el destino '
                 'al 1 de enero de su anio.',
        )
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Escribe los cambios. Sin esta bandera solo informa.',
        )

    def handle(self, *args, **options):
        origen, destino = options['desde'], options['hasta']
        if origen == destino:
            raise CommandError('--desde y --hasta deben ser gestiones distintas.')

        corte = self._fecha_de_corte(options['fecha'])
        revertir = options['revertir']
        aplicar = options['aplicar']

        qs_origen = UnidadOrganizacional.objects.filter(gestion__anio=origen)
        qs_destino = UnidadOrganizacional.objects.filter(gestion__anio=destino)
        if not qs_origen.exists():
            raise CommandError(f'No hay unidades organizacionales de {origen}.')
        if not qs_destino.exists():
            raise CommandError(f'No hay unidades organizacionales de {destino}.')

        if revertir:
            cambios = [
                (qs_destino, {'fecha_vigencia_desde': date(destino, 1, 1)},
                 f'{destino}: fecha_vigencia_desde = {date(destino, 1, 1)}'),
                (qs_origen, {'fecha_vigencia_hasta': None},
                 f'{origen}: fecha_vigencia_hasta = NULL (reabre)'),
            ]
        else:
            cierre = corte - timedelta(days=1)
            cambios = [
                (qs_destino, {'fecha_vigencia_desde': corte},
                 f'{destino}: fecha_vigencia_desde = {corte} (abre)'),
                (qs_origen, {'fecha_vigencia_hasta': cierre},
                 f'{origen}: fecha_vigencia_hasta = {cierre} (cierra)'),
            ]

        self.stdout.write(f'Fecha de corte: {corte}')
        for queryset, _, descripcion in cambios:
            self.stdout.write(f'  {descripcion}  [{queryset.count()} unidades]')

        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\nSimulacion: no se escribio nada. Agregue --aplicar.',
            ))
            self._informar_disponibles(corte)
            return

        with transaction.atomic():
            for queryset, valores, _ in cambios:
                queryset.update(**valores)

        self.stdout.write(self.style.SUCCESS('\nCambios aplicados.'))
        self._informar_disponibles(corte)

    @staticmethod
    def _fecha_de_corte(crudo):
        if crudo is None:
            return timezone.localdate()
        try:
            return date.fromisoformat(crudo)
        except ValueError as exc:
            raise CommandError(f'--fecha invalida: {exc}') from exc

    def _informar_disponibles(self, corte):
        """Cuenta lo que el registro publico ofreceria, por gestion."""
        from apps.accounts.services import (
            unidades_organizacionales_disponibles_registro,
        )
        from django.db.models import Count

        filas = (
            unidades_organizacionales_disponibles_registro()
            .values('gestion__anio')
            .annotate(n=Count('id'))
            .order_by('gestion__anio')
        )
        self.stdout.write('\nUO que ofreceria el registro publico hoy:')
        if not filas:
            self.stdout.write(self.style.ERROR('  NINGUNA — nadie podria registrarse.'))
            return
        for fila in filas:
            self.stdout.write(f"  gestion {fila['gestion__anio']}: {fila['n']}")
