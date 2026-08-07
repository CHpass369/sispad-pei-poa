"""
Vistas de matrices desnormalizadas (como aparecen en el Excel).
Cada endpoint devuelve una fila = cadena completa de articulación.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Prefetch
from apps.presupuesto.models import AsignacionPresupuestariaUnidad
from .models import (
    ArticulacionPADPEI, IndicadorCadena, AccionPOA,
    OperacionPOAU, ActividadPOAU,
    SeguimientoPresupuesto, AsignacionObjetoGasto
)


def _text(value, limit=None):
    text = value or ''
    return text[:limit] if limit else text


def _decimal(value):
    return str(value) if value is not None else ''


def _operational_context(row):
    action = getattr(row, 'accion_poa', None)
    operation = getattr(row, 'operacion', None)
    activity = getattr(row, 'actividad', None)
    action_name = _text(getattr(action, 'denominacion', ''))
    return {
        'codigo_accion': _text(getattr(action, 'codigo_accion', '')),
        'accion_nombre': action_name,
        'accion_poa_nombre': action_name,
        'codigo_operacion': _text(getattr(operation, 'codigo_operacion', '')),
        'operacion_nombre': _text(getattr(operation, 'denominacion', '')),
        'codigo_actividad': _text(getattr(activity, 'codigo_actividad', '')),
        'actividad_nombre': _text(getattr(activity, 'denominacion', '')),
    }


def _budget_context(row):
    return {
        'categoria_programatica': row.categoria_programatica,
        'da': row.da,
        'ue': row.ue,
        'programa': row.programa,
    }


def _serialize_m1(art, indicator):
    product_pad = art.producto_pad
    result_pad = product_pad.resultado_pad if product_pad else None
    product_pei = art.producto_pei
    result_pei = product_pei.resultado_pei if product_pei else None
    result_pad_code = _text(getattr(result_pad, 'codigo_resultado', ''))
    product_pad_code = _text(getattr(product_pad, 'codigo_producto', ''))
    result_pei_code = _text(getattr(result_pei, 'codigo_resultado', ''))
    product_pei_code = _text(getattr(product_pei, 'codigo_producto', ''))
    return {
        'id_cadena': str(art.id)[:10],
        'vigencia_desde': getattr(result_pad, 'vigencia_desde', ''),
        'vigencia_hasta': getattr(result_pad, 'vigencia_hasta', ''),
        'cod_eje_pgdesa': getattr(result_pad, 'cod_eje_pgdesa', ''),
        'objetivo_impacto': getattr(result_pad, 'objetivo_impacto', ''),
        'cod_componente_pdesa': getattr(result_pad, 'cod_componente_pdesa', ''),
        'objetivo_efecto': getattr(result_pad, 'objetivo_efecto', ''),
        'ods': ', '.join(a.codigo for a in result_pad.acuerdo_ods.all()) if result_pad else '',
        'sector': getattr(result_pad, 'sector', ''),
        'cod_resultado_pds': getattr(result_pad, 'cod_resultado_pds', ''),
        'resultado_pds': getattr(result_pad, 'resultado_pds', ''),
        'cod_geografico': getattr(result_pad, 'cod_geografico', ''),
        'eta': getattr(result_pad, 'eta', ''),
        'cod_lineamiento_pad': getattr(result_pad, 'lineamiento_pad', ''),
        'cod_resultado_pad': result_pad_code,
        'codigo_resultado_pad': result_pad_code,
        'resultado_pad': _text(getattr(result_pad, 'denominacion', ''), 100),
        'cod_producto_pad': product_pad_code,
        'codigo_producto_pad': product_pad_code,
        'producto_pad': _text(getattr(product_pad, 'denominacion', ''), 100),
        'territorializacion': getattr(product_pad, 'territorializacion', ''),
        'responsable_pad': getattr(product_pad, 'responsable', ''),
        'cod_entidad': getattr(result_pei, 'cod_entidad', ''),
        'cod_resultado_pei': result_pei_code,
        'codigo_resultado_pei': result_pei_code,
        'resultado_pei': _text(getattr(result_pei, 'denominacion', ''), 100),
        'cod_programa_presup': getattr(product_pei, 'cod_programa_presup', ''),
        'cod_producto_pei': product_pei_code,
        'codigo_producto_pei': product_pei_code,
        'producto_pei': _text(getattr(product_pei, 'denominacion', ''), 100),
        'indicador': _text(getattr(indicator, 'indicador', '')),
        'unidad_medida': _text(getattr(indicator, 'unidad_medida', '')),
        'linea_base': _decimal(getattr(indicator, 'linea_base', None)),
        'meta_2030': _decimal(getattr(indicator, 'meta_2030', None)),
        'estado': art.estado,
    }


def _serialize_m2(action):
    product = action.producto_pei
    result = product.resultado_pei if product else None
    product_name = _text(getattr(product, 'denominacion', ''), 100)
    return {
        'id_cadena': str(action.id)[:10],
        'gestion': action.gestion,
        'cod_resultado_pei': _text(getattr(result, 'codigo_resultado', '')),
        'resultado_pei': _text(getattr(result, 'denominacion', ''), 100),
        'cod_producto_pei': _text(getattr(product, 'codigo_producto', '')),
        'producto_pei': product_name,
        'producto_pei_nombre': product_name,
        'cod_accion_poa': action.codigo_accion,
        'accion_corto_plazo': _text(action.denominacion, 100),
        'codigo_accion': action.codigo_accion,
        'denominacion': _text(action.denominacion, 100),
        'resultado_esperado': action.resultado_esperado or '',
        'indicador': action.indicador or '',
        'unidad_medida': action.unidad_medida or '',
        'linea_base': _decimal(action.linea_base),
        'meta_gestion': _decimal(action.meta_gestion),
        'presupuesto_programado': _decimal(action.presupuesto_programado),
        'fuente': action.fuente_financiamiento or '',
        'fuente_financiamiento': action.fuente_financiamiento or '',
        'organismo': action.organismo_financiador or '',
        'estado': action.estado,
    }


def _serialize_task(task):
    return {
        'id': str(task.id),
        'cod_tarea': task.codigo_tarea,
        'tarea': task.denominacion,
        'codigo_tarea': task.codigo_tarea,
        'codigo_completo_articulacion': task.codigo_completo_articulacion,
        'denominacion': task.denominacion,
        'responsable': task.responsable or '',
        'fecha_inicio': task.fecha_inicio,
        'fecha_fin': task.fecha_fin,
        'metas': _decimal(task.metas) or None,
        'estado': task.estado,
    }


def _serialize_activity(activity):
    return {
        'cod_actividad': activity.codigo_actividad,
        'actividad': activity.denominacion,
        'id': str(activity.id),
        'codigo_actividad': activity.codigo_actividad,
        'codigo_completo_articulacion': activity.codigo_completo_articulacion,
        'denominacion': activity.denominacion,
        'meta_anual': _decimal(activity.meta_anual),
        'unidad_medida': activity.unidad_medida,
        'estado': activity.estado,
        'tareas': [_serialize_task(task) for task in activity.tareas.all()],
    }


def _serialize_m3(operation):
    action = operation.accion_poa
    return {
        'id': str(operation.id),
        'id_cadena': str(operation.id)[:10],
        'gestion': action.gestion if action else None,
        'cod_accion_poa': action.codigo_accion if action else '',
        'accion_corto_plazo': _text(action.denominacion, 80) if action else '',
        'cod_operacion': operation.codigo_operacion,
        'operacion': operation.denominacion,
        'codigo_operacion': operation.codigo_operacion,
        'codigo_completo_articulacion': operation.codigo_completo_articulacion,
        'denominacion': operation.denominacion,
        'tipo_operacion': operation.tipo_operacion,
        'responsable': operation.responsable,
        'meta_anual': _decimal(operation.meta_anual) or None,
        'unidad_medida': operation.unidad_medida,
        'fecha_inicio': operation.fecha_inicio,
        'fecha_fin': operation.fecha_fin,
        'estado': operation.estado,
        'actividades': [
            _serialize_activity(activity) for activity in operation.actividades.all()
        ],
    }


def _serialize_m4(row):
    return {
        'id': str(row.pk),
        'id_cadena': row.id_cadena,
        'gestion': row.gestion,
        **_operational_context(row),
        **_budget_context(row),
        'presupuesto_inicial': row.presupuesto_inicial,
        'modificaciones': row.modificaciones,
        'presupuesto_vigente': row.presupuesto_vigente,
        'ejecutado_total': row.ejecutado_total,
        'porcentaje_ejecucion_financiera': row.porcentaje_ejecucion_financiera,
        'meta_fisica': row.meta_fisica,
        'ejecucion_fisica': row.ejecucion_fisica,
        'porcentaje_ejecucion_fisica': row.porcentaje_ejecucion_fisica,
        'eficacia': row.eficacia,
        'estado': row.estado,
    }


def _serialize_m5(row, canonical):
    return {
        'id': str(row.pk),
        'codigo_asignacion': row.codigo_asignacion,
        'gestion': row.gestion,
        **_operational_context(row),
        **_budget_context(row),
        'cod_objeto_gasto': row.cod_objeto_gasto,
        'descripcion_objeto': row.descripcion_objeto,
        'grupo_gasto': row.grupo_gasto,
        'tipo_gasto': row.tipo_gasto,
        'fuente_financiamiento': row.fuente_financiamiento,
        'organismo_financiador': row.organismo_financiador,
        'monto_programado': row.monto_programado,
        'monto_vigente': row.monto_vigente,
        'monto_ejecutado': canonical.monto_ejecutado if canonical else 0,
        'justificacion': row.justificacion,
        'estado': row.estado,
    }


class MatrizViewSet(viewsets.ViewSet):
    """Endpoints que devuelven matrices desnormalizadas (formato Excel)."""

    @action(detail=False, methods=['get'])
    def m1_pad_pei(self, request):
        """Matriz 1: Articulación PAD-PEI (como en Excel, 58 columnas).
        GET /api/v1/articulacion/matrices/m1_pad_pei/?gestion=2026
        """
        gestion = request.query_params.get('gestion')
        qs = ArticulacionPADPEI.objects.select_related(
            'producto_pad__resultado_pad',
            'producto_pei__resultado_pei'
        )
        if gestion:
            qs = qs.filter(producto_pad__resultado_pad__vigencia_desde=int(gestion))
        filas = [
            _serialize_m1(
                art,
                IndicadorCadena.objects.filter(producto_pad=art.producto_pad).first(),
            )
            for art in qs
        ]
        return Response(filas)

    @action(detail=False, methods=['get'])
    def m2_pei_poa(self, request):
        """Matriz 2: Articulación PEI-POA.
        GET /api/v1/articulacion/matrices/m2_pei_poa/?gestion=2026
        """
        gestion = request.query_params.get('gestion')
        qs = AccionPOA.objects.select_related('producto_pei__resultado_pei').all()
        if gestion:
            qs = qs.filter(gestion=int(gestion))

        return Response([_serialize_m2(action) for action in qs])

    @action(detail=False, methods=['get'])
    def m3_poa_poau(self, request):
        """Matriz 3: POA-POAU jerárquico con operaciones/actividades/tareas.
        GET /api/v1/articulacion/matrices/m3_poa_poau/?gestion=2026
        """
        gestion = request.query_params.get('gestion')
        qs = OperacionPOAU.objects.select_related('accion_poa').prefetch_related(
            Prefetch('actividades', queryset=ActividadPOAU.objects.prefetch_related('tareas'))
        )
        if gestion:
            qs = qs.filter(accion_poa__gestion=int(gestion))

        return Response([_serialize_m3(operation) for operation in qs])

    @action(detail=False, methods=['get'])
    def m4_presupuesto(self, request):
        """Matriz 4: Presupuesto y seguimiento."""
        gestion = request.query_params.get('gestion')
        qs = SeguimientoPresupuesto.objects.select_related(
            'accion_poa', 'operacion', 'actividad', 'tarea',
        )
        if gestion:
            qs = qs.filter(gestion=int(gestion))
        return Response([_serialize_m4(row) for row in qs.order_by('id_cadena')])

    @action(detail=False, methods=['get'])
    def m5_objetos_gasto(self, request):
        """Matriz 5: Asignación de objetos de gasto."""
        gestion = request.query_params.get('gestion')
        qs = AsignacionObjetoGasto.objects.select_related(
            'accion_poa', 'operacion', 'actividad', 'tarea',
        )
        if gestion:
            qs = qs.filter(gestion=int(gestion))
        canonical = {
            row.objeto_gasto.codigo: row
            for row in AsignacionPresupuestariaUnidad.objects.select_related(
                'objeto_gasto'
            ).filter(gestion=int(gestion))
        } if gestion else {}
        return Response([
            _serialize_m5(row, canonical.get(row.cod_objeto_gasto))
            for row in qs.order_by('codigo_asignacion')
        ])
