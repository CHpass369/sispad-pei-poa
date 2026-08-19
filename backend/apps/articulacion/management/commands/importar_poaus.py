"""Importa los POAUs desde la planilla BASE FORMULACIÓN DE POAUS.

    python manage.py importar_poaus --archivo ruta.xlsx --gestion 2027

La hoja es un árbol por unidad organizacional:

    EM-DJR-01                          ← unidad (columna B)
      000 0 001  ·  Operación          ← categoría programática (H) + J
        └─ Actividad                   ← K
             └─ Tareas                 ← L, con su cronograma mensual

CODIFICACIÓN PROVISIONAL: la planilla no trae el código de producto PEI ni el
de acción de corto plazo (columnas C y F, vacías en toda la hoja), y el modelo
los exige. Se generan con prefijo PROV- a partir de la unidad y la categoría
programática, que sí están. Hay que reemplazarlos cuando el PEI se formule:
son reconocibles por el prefijo.
"""
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.articulacion.models import (
    AccionPOA, ActividadPOAU, OperacionPOAU, ProductoPEI, ResultadoPEI,
    TareaPOAU,
)
from apps.organizacion.models import UnidadOrganizacional

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
# Columnas PROGRAMADO del cronograma: Y, AA, AC … AU (una sí, una no).
COL_MES = {MESES[i]: 25 + i * 2 for i in range(12)}

COL_UNIDAD, COL_CATEGORIA = 2, 8
COL_OPERACION, COL_ACTIVIDAD, COL_TAREA = 10, 11, 12
COL_INDICADOR, COL_FORMULA, COL_UNIDAD_MEDIDA = 14, 15, 16
COL_META, COL_INICIO, COL_FIN = 21, 22, 23
COL_RESPONSABLE = 55


class Command(BaseCommand):
    help = 'Importa los POAUs (operaciones, actividades y tareas) con su programación física.'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', required=True)
        parser.add_argument('--gestion', type=int, default=2027)
        parser.add_argument('--hoja', default='Base PEI 2027')
        parser.add_argument('--dry-run', action='store_true')

    @transaction.atomic
    def handle(self, *args, **op):
        try:
            import openpyxl
        except ImportError:
            raise CommandError('Falta openpyxl.')

        hoja = openpyxl.load_workbook(
            op['archivo'], data_only=True, read_only=True)[op['hoja']]
        gestion = op['gestion']
        seco = op['dry_run']

        unidades = {u.codigo: u for u in UnidadOrganizacional.objects.filter(
            gestion__anio=gestion)}
        if not unidades:
            raise CommandError(
                f'No hay unidades organizacionales en la gestión {gestion}. '
                'Ejecute antes importar_estructura_gams.')

        # Un resultado y un producto PEI provisionales por unidad: el modelo
        # los exige y la planilla no los trae.
        resultado = None
        if not seco:
            resultado, _ = ResultadoPEI.objects.get_or_create(
                codigo_resultado='PROV-POAU', vigencia_desde=gestion,
                defaults={
                    'denominacion': 'Resultado provisional para POAUs importados',
                    'cod_entidad': '1312', 'entidad': 'GAM Sacaba',
                    'vigencia_hasta': gestion,
                },
            )

        def texto(fila, col):
            v = fila[col - 1] if len(fila) >= col else None
            return '' if v in (None, '') else str(v).strip()

        def numero(fila, col):
            v = fila[col - 1] if len(fila) >= col else None
            try:
                return Decimal(str(v)) if isinstance(v, (int, float)) else None
            except (InvalidOperation, TypeError):
                return None

        def cronograma(fila):
            """Solo lo PROGRAMADO: lo ejecutado se carga en seguimiento."""
            plan = {}
            for mes, col in COL_MES.items():
                v = fila[col - 1] if len(fila) >= col else None
                if isinstance(v, (int, float)) and v:
                    plan[mes] = float(v)
            return plan or None

        def fecha(fila, col):
            v = fila[col - 1] if len(fila) >= col else None
            return v.date() if hasattr(v, 'date') else None

        unidad = accion = operacion = actividad = None
        cuenta = {'acciones': 0, 'operaciones': 0, 'actividades': 0, 'tareas': 0}
        sin_unidad = set()
        correlativos: dict[int, int] = {}

        def accion_para(categoria):
            """Acción de corto plazo provisional por unidad y categoría."""
            nonlocal accion
            if unidad is None:
                return None
            producto, _ = ProductoPEI.objects.get_or_create(
                codigo_producto=f'PROV-{unidad.codigo}',
                resultado_pei=resultado,
                defaults={'denominacion': f'Producto provisional {unidad.nombre}'[:300]},
            )
            correlativo = correlativos.get(producto.id, 0) + 1
            correlativos[producto.id] = correlativo
            codigo = f'PROV-{unidad.codigo}-{categoria.replace(" ", "")}'[:50]
            accion, creada = AccionPOA.objects.get_or_create(
                codigo_accion=codigo,
                defaults={
                    'denominacion': f'Acción provisional {categoria} — {unidad.nombre}'[:300],
                    'producto_pei': producto, 'gestion': gestion,
                    'categoria_programatica': categoria,
                    'unidad_responsable': unidad,
                    'correlativo': correlativo,
                    'segmento': AccionPOA.generar_segmento(correlativo),
                },
            )
            cuenta['acciones'] += int(creada)
            return accion

        categoria_actual = ''
        for fila in hoja.iter_rows(min_row=5, values_only=True):
            cod_unidad = texto(fila, COL_UNIDAD)
            if cod_unidad and cod_unidad.count('-') >= 2:
                unidad = unidades.get(cod_unidad)
                if unidad is None:
                    sin_unidad.add(cod_unidad)
                accion = operacion = actividad = None
                continue

            categoria = texto(fila, COL_CATEGORIA)
            if categoria:
                categoria_actual = categoria

            den_op = texto(fila, COL_OPERACION)
            den_act = texto(fila, COL_ACTIVIDAD)
            den_tar = texto(fila, COL_TAREA)
            if not (den_op or den_act or den_tar) or unidad is None:
                continue

            comunes = dict(
                indicador=texto(fila, COL_INDICADOR),
                formula=texto(fila, COL_FORMULA),
                unidad_medida=texto(fila, COL_UNIDAD_MEDIDA)[:100],
                fecha_inicio=fecha(fila, COL_INICIO),
                fecha_fin=fecha(fila, COL_FIN),
                programacion_mensual=cronograma(fila),
            )

            if den_op:
                cuenta['operaciones'] += 1
                if seco:
                    operacion = actividad = 'seco'
                    continue
                accion_para(categoria_actual or '000 0 000')
                if accion is None:
                    continue
                operacion = OperacionPOAU.objects.create(
                    codigo_operacion=f'{accion.codigo_accion}.{cuenta["operaciones"]}'[:50],
                    correlativo=cuenta['operaciones'],
                    segmento=OperacionPOAU.generar_segmento(
                        min(cuenta['operaciones'], 999)),
                    denominacion=den_op[:2000], tipo_operacion='POAU',
                    accion_poa=accion, unidad_ejecutora=unidad.nombre[:200],
                    meta_anual=numero(fila, COL_META), **comunes,
                )
                actividad = None

            elif den_act:
                cuenta['actividades'] += 1
                if seco:
                    actividad = 'seco'
                    continue
                if operacion is None:
                    continue
                actividad = ActividadPOAU.objects.create(
                    codigo_actividad=f'{operacion.codigo_operacion}.{cuenta["actividades"]}'[:50],
                    correlativo=cuenta['actividades'],
                    segmento=ActividadPOAU.generar_segmento(
                        min(cuenta['actividades'], 999)),
                    denominacion=den_act[:2000], operacion=operacion,
                    meta_anual=numero(fila, COL_META), **comunes,
                )

            elif den_tar:
                cuenta['tareas'] += 1
                if seco or actividad in (None, 'seco'):
                    continue
                TareaPOAU.objects.create(
                    codigo_tarea=f'{actividad.codigo_actividad}.{cuenta["tareas"]}'[:50],
                    correlativo=cuenta['tareas'],
                    segmento=TareaPOAU.generar_segmento(min(cuenta['tareas'], 999)),
                    denominacion=den_tar[:2000], actividad=actividad,
                    responsable=texto(fila, COL_RESPONSABLE)[:200],
                    metas=numero(fila, COL_META),
                    fecha_inicio=comunes['fecha_inicio'],
                    fecha_fin=comunes['fecha_fin'],
                    programacion_mensual=comunes['programacion_mensual'],
                )

        etiqueta = '[dry-run] ' if seco else ''
        self.stdout.write(self.style.SUCCESS(
            f'{etiqueta}Gestión {gestion}: {cuenta["acciones"]} acciones provisionales, '
            f'{cuenta["operaciones"]} operaciones, {cuenta["actividades"]} actividades, '
            f'{cuenta["tareas"]} tareas.'))
        if sin_unidad:
            self.stdout.write(self.style.WARNING(
                f'  {len(sin_unidad)} códigos de unidad sin correspondencia en el '
                f'catálogo: {sorted(sin_unidad)[:6]}'))
