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

DISEÑOS DE PLANILLA: la fuente cambió de estructura entre versiones. La original
traía la hoja «Base PEI 2027» con la categoría en la columna H; la actualizada
trae «BASE POA 2027», con las mismas columnas corridas y campos nuevos
(responsable, medio de verificación, unidad ejecutora). Ambas describen el mismo
árbol, así que se soportan las dos con un mapa de columnas por diseño, elegido
automáticamente por el nombre de la hoja.

ACTUALIZAR EN LUGAR DE AGREGAR: operaciones, actividades y tareas se crean con
un correlativo corrido, no con `get_or_create`, así que volver a correr el
importador sobre la misma planilla **duplica todo**. Para cargar una versión
corregida de la fuente está `--reemplazar`, que borra primero el árbol
provisional (las acciones `PROV-` de esa gestión y todo lo que les cuelga) y
vuelve a construirlo. Las acciones que no son provisionales no se tocan: son
carga manual, no de esta planilla.
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

# Cada diseño mapea el mismo árbol a las columnas de su versión de la planilla.
# `primer_mes` es la columna PROGRAMADO de enero; los meses van una sí, una no,
# porque cada uno trae su par PROGRAMADO/EJECUTADO.
DISENOS = {
    'base-pei-2027': {
        'hoja': 'Base PEI 2027', 'primera_fila': 5,
        'unidad': 2, 'categoria': 8,
        'operacion': 10, 'actividad': 11, 'tarea': 12,
        'indicador': 14, 'formula': 15, 'unidad_medida': 16,
        'meta': 21, 'inicio': 22, 'fin': 23,
        'responsable': 55, 'medio_verificacion': None, 'unidad_ejecutora': None,
        'primer_mes': 25,
    },
    'base-poa-2027': {
        'hoja': 'BASE POA 2027', 'primera_fila': 4,
        'unidad': 6, 'categoria': 21,
        'operacion': 23, 'actividad': 24, 'tarea': 25,
        'indicador': 27, 'formula': 28, 'unidad_medida': 29,
        # 32 es la meta original y 33 su modificación: 34 ya trae la vigente.
        'meta': 34, 'inicio': 35, 'fin': 36,
        'responsable': 68, 'medio_verificacion': 66, 'unidad_ejecutora': 67,
        'primer_mes': 38,
    },
}


def diseno_de(nombre_hoja, elegido=None):
    if elegido:
        return DISENOS[elegido]
    for diseno in DISENOS.values():
        if diseno['hoja'].lower() == (nombre_hoja or '').lower():
            return diseno
    raise CommandError(
        f'No hay diseño de columnas para la hoja «{nombre_hoja}». '
        f'Indique --diseno entre: {", ".join(DISENOS)}.'
    )


class Command(BaseCommand):
    help = 'Importa los POAUs (operaciones, actividades y tareas) con su programación física.'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', required=True)
        parser.add_argument('--gestion', type=int, default=2027)
        parser.add_argument('--hoja', default='Base PEI 2027')
        parser.add_argument(
            '--diseno', choices=sorted(DISENOS),
            help='Mapa de columnas. Si se omite se deduce del nombre de la hoja.')
        parser.add_argument(
            '--reemplazar', action='store_true',
            help='Borra el árbol provisional de la gestión antes de importar. '
                 'Es lo que corresponde al cargar una versión corregida de la '
                 'planilla: sin esto, los registros se duplican.')
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

        d = diseno_de(op['hoja'], op.get('diseno'))
        col_mes = {MESES[i]: d['primer_mes'] + i * 2 for i in range(12)}

        unidades = {u.codigo: u for u in UnidadOrganizacional.objects.filter(
            gestion__anio=gestion)}
        if not unidades:
            raise CommandError(
                f'No hay unidades organizacionales en la gestión {gestion}. '
                'Ejecute antes importar_estructura_gams.')

        if op['reemplazar']:
            # El árbol provisional se reconstruye entero: las operaciones,
            # actividades y tareas se crean con correlativo corrido, así que
            # importar encima duplicaría en vez de corregir. Sólo se borra lo
            # que generó este mismo importador (prefijo PROV-); lo cargado a
            # mano no se toca.
            provisionales = AccionPOA.objects.filter(
                gestion=gestion, codigo_accion__startswith='PROV-')
            operaciones = OperacionPOAU.objects.filter(accion_poa__in=provisionales)
            actividades = ActividadPOAU.objects.filter(operacion__in=operaciones)
            tareas = TareaPOAU.objects.filter(actividad__in=actividades)
            borrado = {
                'tareas': tareas.count(), 'actividades': actividades.count(),
                'operaciones': operaciones.count(), 'acciones': provisionales.count(),
            }
            if not seco:
                tareas.delete()
                actividades.delete()
                operaciones.delete()
                provisionales.delete()
            self.stdout.write(self.style.WARNING(
                f'{"[dry-run] " if seco else ""}Árbol provisional reemplazado: '
                f'{borrado["acciones"]} acciones, {borrado["operaciones"]} operaciones, '
                f'{borrado["actividades"]} actividades, {borrado["tareas"]} tareas.'))

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
            if col is None:          # el diseño no tiene esa columna
                return ''
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
            for mes, col in col_mes.items():
                v = fila[col - 1] if len(fila) >= col else None
                if isinstance(v, (int, float)) and v:
                    plan[mes] = float(v)
            return plan or None

        def fecha(fila, col):
            v = fila[col - 1] if len(fila) >= col else None
            return v.date() if hasattr(v, 'date') else None

        unidad = accion = operacion = actividad = None
        cuenta = {'acciones': 0, 'operaciones': 0, 'actividades': 0, 'tareas': 0}
        sin_unidad = {}          # código -> filas de la planilla descartadas
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
        descartando = None
        rotulos_no_categoria = set()
        for fila in hoja.iter_rows(min_row=d['primera_fila'], values_only=True):
            cod_unidad = texto(fila, d['unidad'])
            if cod_unidad and cod_unidad.count('-') >= 2:
                unidad = unidades.get(cod_unidad)
                if unidad is None:
                    sin_unidad.setdefault(cod_unidad, 0)
                    descartando = cod_unidad
                else:
                    descartando = None
                accion = operacion = actividad = None
                continue

            categoria = texto(fila, d['categoria'])
            # La columna de categoría a veces trae rótulos de la planilla en vez
            # de un código: «SISIN», «SISIN WEB», «S/N». Todo código programático
            # empieza con dígito, así que lo que no lo hace no es una categoría y
            # no debe guardarse como si lo fuera: guardarlo rompe la clave
            # foránea contra el catálogo y finge un dato que no existe.
            if categoria and not categoria[:1].isdigit():
                rotulos_no_categoria.add(categoria)
                categoria = ''
            if categoria:
                categoria_actual = categoria

            den_op = texto(fila, d['operacion'])
            den_act = texto(fila, d['actividad'])
            den_tar = texto(fila, d['tarea'])
            if not (den_op or den_act or den_tar):
                continue
            if unidad is None:
                if descartando:
                    sin_unidad[descartando] += 1
                continue

            comunes = dict(
                indicador=texto(fila, d['indicador']),
                formula=texto(fila, d['formula']),
                unidad_medida=texto(fila, d['unidad_medida'])[:100],
                fecha_inicio=fecha(fila, d['inicio']),
                fecha_fin=fecha(fila, d['fin']),
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
                    meta_anual=numero(fila, d['meta']), **comunes,
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
                    meta_anual=numero(fila, d['meta']), **comunes,
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
                    responsable=texto(fila, d['responsable'])[:200],
                    metas=numero(fila, d['meta']),
                    fecha_inicio=comunes['fecha_inicio'],
                    fecha_fin=comunes['fecha_fin'],
                    programacion_mensual=comunes['programacion_mensual'],
                )

        etiqueta = '[dry-run] ' if seco else ''
        self.stdout.write(self.style.SUCCESS(
            f'{etiqueta}Gestión {gestion}: {cuenta["acciones"]} acciones provisionales, '
            f'{cuenta["operaciones"]} operaciones, {cuenta["actividades"]} actividades, '
            f'{cuenta["tareas"]} tareas.'))
        if rotulos_no_categoria:
            self.stdout.write(self.style.WARNING(
                f'  {len(rotulos_no_categoria)} valores de la columna categoría no '
                f'son códigos y se dejaron vacíos: '
                f'{sorted(rotulos_no_categoria)}'))
        if sin_unidad:
            perdidas = sum(sin_unidad.values())
            self.stdout.write(self.style.ERROR(
                f'  ATENCIÓN: {len(sin_unidad)} códigos de unidad de la planilla no '
                f'existen en el catálogo organizacional, y por eso se DESCARTARON '
                f'{perdidas} filas:'))
            for codigo, filas in sorted(sin_unidad.items()):
                self.stdout.write(self.style.ERROR(
                    f'    {codigo}: {filas} filas de la planilla sin importar'))
            self.stdout.write(self.style.WARNING(
                '  Cargue esas unidades y vuelva a correr con --reemplazar.'))
