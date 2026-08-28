"""Carga una cadena POAU de DEMOSTRACION para una unidad organizacional.

Existe porque el importador que sembro las 175 acciones provisionales de 2027
dejo fuera a varias unidades (entre ellas PLANIFICACION ESTRATEGICA), y sin
datos no se puede ver en pantalla que el filtro por alcance funciona: la matriz
sale vacia tanto si el filtro anda bien como si escondiera de mas.

NO es un seed de produccion. Todo lo que crea lleva el prefijo `DEMO-` en su
codigo, de modo que `--revertir` borra exactamente esto y nada mas. Los
registros nacen `provisional`, asi que el trigger de inmutabilidad de codigos
oficiales (migracion 0006) no los protege y se pueden retirar.

Uso:

    python manage.py poau_demo_unidad --unidad SP-DPD-18            # simula
    python manage.py poau_demo_unidad --unidad SP-DPD-18 --aplicar
    python manage.py poau_demo_unidad --unidad SP-DPD-18 --revertir --aplicar
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.articulacion.models import (
    AccionPOA, ActividadPOAU, OperacionPOAU, ProductoPEI, ResultadoPEI,
    TareaPOAU,
)
from apps.gestion.models import GestionFiscal
from apps.organizacion.models import UnidadOrganizacional

PREFIJO = 'DEMO'

# (codigo_operacion, denominacion, [(codigo_actividad, denominacion, [tareas])])
ESQUELETO = [
    (
        '01', 'Formular y consolidar la programacion operativa anual',
        [
            (
                '01', 'Elaborar el POA institucional de la gestion',
                ['Recopilar insumos de las unidades',
                 'Consolidar la matriz institucional'],
            ),
            (
                '02', 'Acompaniar la formulacion POAU de las unidades',
                ['Capacitar a los formuladores'],
            ),
        ],
    ),
    (
        '02', 'Realizar el seguimiento a la ejecucion del POA',
        [
            (
                '01', 'Evaluar el avance trimestral',
                ['Emitir el reporte de avance'],
            ),
        ],
    ),
]


class Command(BaseCommand):
    help = 'Carga (o retira) una cadena POAU de demostracion para una unidad.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--unidad', required=True,
            help='Codigo de la unidad organizacional (p. ej. SP-DPD-18).',
        )
        parser.add_argument(
            '--gestion', type=int, default=None,
            help='Anio. Por defecto, la gestion habilitada.',
        )
        parser.add_argument(
            '--revertir', action='store_true',
            help='Retira lo que este comando creo para esa unidad.',
        )
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Sin esta bandera solo informa lo que haria.',
        )

    def handle(self, *args, **opciones):
        codigo_uo = opciones['unidad']
        anio = opciones['gestion']
        if anio is None:
            habilitada = GestionFiscal.objects.filter(activa=True).first()
            if habilitada is None:
                raise CommandError(
                    'No hay gestion habilitada; pase --gestion explicitamente.',
                )
            anio = habilitada.anio

        gestion = GestionFiscal.objects.filter(anio=anio).first()
        if gestion is None:
            raise CommandError(f'No existe la gestion fiscal {anio}.')

        unidad = UnidadOrganizacional.objects.filter(
            codigo=codigo_uo, gestion=gestion,
        ).first()
        if unidad is None:
            raise CommandError(
                f'No existe la unidad {codigo_uo} en la gestion {anio}.',
            )

        raiz = f'{PREFIJO}-{codigo_uo}'
        if opciones['revertir']:
            self._revertir(raiz, unidad, anio, opciones['aplicar'])
            return
        self._cargar(raiz, unidad, gestion, anio, opciones['aplicar'])

    # --- carga --------------------------------------------------------------

    def _cargar(self, raiz, unidad, gestion, anio, aplicar):
        existentes = AccionPOA.objects.filter(
            codigo_accion__startswith=raiz, gestion=anio,
        ).count()
        tareas = sum(len(t) for _, _, acts in ESQUELETO for _, _, t in acts)
        actividades = sum(len(acts) for _, _, acts in ESQUELETO)

        self.stdout.write(f'Unidad  : {unidad.codigo} — {unidad.nombre}')
        self.stdout.write(f'Gestion : {anio}')
        self.stdout.write(
            f'A crear : 1 accion, {len(ESQUELETO)} operaciones, '
            f'{actividades} actividades, {tareas} tareas',
        )
        if existentes:
            self.stdout.write(self.style.WARNING(
                f'Ya existen {existentes} acciones DEMO para esta unidad; '
                'el comando es idempotente y no las duplica.',
            ))
        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\nSimulacion. Repita con --aplicar para escribir.',
            ))
            return

        with transaction.atomic():
            resultado, _ = ResultadoPEI.objects.get_or_create(
                codigo_resultado=f'{raiz}.R',
                defaults={
                    'denominacion': f'Resultado demo — {unidad.nombre}',
                    'cod_entidad': '1312', 'entidad': 'GAM Sacaba',
                    'vigencia_desde': anio, 'vigencia_hasta': anio + 3,
                },
            )
            producto, _ = ProductoPEI.objects.get_or_create(
                codigo_producto=f'{raiz}.P',
                defaults={
                    'denominacion': f'Producto demo — {unidad.nombre}',
                    'resultado_pei': resultado,
                    'tipo_producto': 'TERMINAL',
                },
            )
            accion, _ = AccionPOA.objects.get_or_create(
                codigo_accion=f'{raiz}-0001',
                gestion=anio,
                defaults={
                    'denominacion': (
                        f'Accion de corto plazo demo — {unidad.nombre}'
                    ),
                    'producto_pei': producto,
                    'unidad_responsable': unidad,
                },
            )
            for cod_op, den_op, actividades_esqueleto in ESQUELETO:
                operacion, _ = OperacionPOAU.objects.get_or_create(
                    codigo_operacion=f'{accion.codigo_accion}.{cod_op}',
                    defaults={
                        'denominacion': den_op, 'accion_poa': accion,
                    },
                )
                for cod_act, den_act, tareas_esqueleto in actividades_esqueleto:
                    actividad, _ = ActividadPOAU.objects.get_or_create(
                        codigo_actividad=(
                            f'{operacion.codigo_operacion}.{cod_act}'
                        ),
                        defaults={
                            'denominacion': den_act, 'operacion': operacion,
                        },
                    )
                    for indice, den_tarea in enumerate(tareas_esqueleto, 1):
                        TareaPOAU.objects.get_or_create(
                            codigo_tarea=(
                                f'{actividad.codigo_actividad}.{indice}'
                            ),
                            defaults={
                                'denominacion': den_tarea,
                                'actividad': actividad,
                            },
                        )

        self.stdout.write(self.style.SUCCESS('\nCadena POAU demo cargada.'))

    # --- reversion ----------------------------------------------------------

    def _revertir(self, raiz, unidad, anio, aplicar):
        acciones = AccionPOA.objects.filter(
            codigo_accion__startswith=raiz, gestion=anio,
        )
        self.stdout.write(f'Unidad  : {unidad.codigo} — {unidad.nombre}')
        self.stdout.write(f'A retirar: {acciones.count()} acciones DEMO')
        if not aplicar:
            self.stdout.write(self.style.WARNING(
                '\nSimulacion. Repita con --aplicar para borrar.',
            ))
            return

        with transaction.atomic():
            # El cascade de la cadena arrastra operaciones, actividades y
            # tareas; los nodos PEI demo se retiran despues, ya sin referencias.
            acciones.delete()
            ProductoPEI.objects.filter(
                codigo_producto=f'{raiz}.P', acciones_poa__isnull=True,
            ).delete()
            ResultadoPEI.objects.filter(
                codigo_resultado=f'{raiz}.R', productos__isnull=True,
            ).delete()

        self.stdout.write(self.style.SUCCESS('\nCadena POAU demo retirada.'))
