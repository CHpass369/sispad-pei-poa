"""
Vistas de matrices desnormalizadas (como aparecen en el Excel).
Cada endpoint devuelve una fila = cadena completa de articulación.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.db.models import Prefetch
from .models import (
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA,
    OperacionPOAU, ActividadPOAU, TareaPOAU,
    SeguimientoPresupuesto, AsignacionObjetoGasto
)


class MatrizViewSet(viewsets.ViewSet):
    """Endpoints que devuelven matrices desnormalizadas (formato Excel)."""

    @action(detail=False, methods=['get'])
    def m1_pad_pei(self, request):
        """Matriz 1: Articulación PAD-PEI (como en Excel, 58 columnas).
        GET /api/v1/articulacion/matrices/m1_pad_pei/?gestion=2026
        """
        filas = []
        for art in ArticulacionPADPEI.objects.select_related(
            'producto_pad__resultado_pad',
            'producto_pei__resultado_pei'
        ).all():
            ppad = art.producto_pad
            rpad = ppad.resultado_pad if ppad else None
            ppei = art.producto_pei
            rpei = ppei.resultado_pei if ppei else None
            ind = IndicadorCadena.objects.filter(producto_pad=ppad).first()

            filas.append({
                'id_cadena': str(art.id)[:10],
                'vigencia_desde': getattr(rpad, 'vigencia_desde', ''),
                'vigencia_hasta': getattr(rpad, 'vigencia_hasta', ''),
                'cod_eje_pgdesa': getattr(rpad, 'cod_eje_pgdesa', ''),
                'objetivo_impacto': getattr(rpad, 'objetivo_impacto', ''),
                'cod_componente_pdesa': getattr(rpad, 'cod_componente_pdesa', ''),
                'objetivo_efecto': getattr(rpad, 'objetivo_efecto', ''),
                'ods': ', '.join(a.codigo for a in rpad.acuerdo_ods.all()) if rpad else '',
                'sector': getattr(rpad, 'sector', ''),
                'cod_resultado_pds': getattr(rpad, 'cod_resultado_pds', ''),
                'resultado_pds': getattr(rpad, 'resultado_pds', ''),
                'cod_geografico': getattr(rpad, 'cod_geografico', ''),
                'eta': getattr(rpad, 'eta', ''),
                'cod_lineamiento_pad': getattr(rpad, 'lineamiento_pad', ''),
                'cod_resultado_pad': rpad.codigo_resultado if rpad else '',
                'resultado_pad': rpad.denominacion[:100] if rpad else '',
                'cod_producto_pad': ppad.codigo_producto if ppad else '',
                'producto_pad': ppad.denominacion[:100] if ppad else '',
                'territorializacion': getattr(rpad, 'territorializacion', ''),
                'responsable_pad': getattr(rpad, 'responsable_pad', ''),
                'cod_entidad': getattr(rpei, 'cod_entidad', ''),
                'cod_resultado_pei': rpei.codigo_resultado if rpei else '',
                'resultado_pei': rpei.denominacion[:100] if rpei else '',
                'cod_programa_presup': getattr(ppei, 'cod_programa_presup', ''),
                'cod_producto_pei': ppei.codigo_producto if ppei else '',
                'producto_pei': ppei.denominacion[:100] if ppei else '',
                'indicador': ind.indicador if ind else '',
                'unidad_medida': ind.unidad_medida if ind else '',
                'linea_base': str(ind.linea_base) if ind and ind.linea_base else '',
                'meta_2030': str(ind.meta_2030) if ind and ind.meta_2030 else '',
            })
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

        filas = []
        for ac in qs:
            ppei = ac.producto_pei
            rpei = ppei.resultado_pei if ppei else None
            filas.append({
                'id_cadena': str(ac.id)[:10],
                'gestion': ac.gestion,
                'cod_resultado_pei': rpei.codigo_resultado if rpei else '',
                'resultado_pei': rpei.denominacion[:100] if rpei else '',
                'cod_producto_pei': ppei.codigo_producto if ppei else '',
                'producto_pei': ppei.denominacion[:100] if ppei else '',
                'cod_accion_poa': ac.codigo_accion,
                'accion_corto_plazo': ac.denominacion[:100],
                'resultado_esperado': ac.resultado_esperado or '',
                'indicador': ac.indicador or '',
                'unidad_medida': ac.unidad_medida or '',
                'linea_base': str(ac.linea_base) if ac.linea_base else '',
                'meta_gestion': str(ac.meta_gestion) if ac.meta_gestion else '',
                'presupuesto_programado': str(ac.presupuesto_programado) if ac.presupuesto_programado else '',
                'fuente': ac.fuente_financiamiento or '',
                'organismo': ac.organismo_financiador or '',
                'estado': ac.estado,
            })
        return Response(filas)

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

        resultado = []
        for op in qs:
            ops_data = {
                'id_cadena': str(op.id)[:10],
                'cod_accion_poa': op.accion_poa.codigo_accion if op.accion_poa else '',
                'accion_corto_plazo': op.accion_poa.denominacion[:80] if op.accion_poa else '',
                'cod_operacion': op.codigo_operacion,
                'operacion': op.denominacion,
                'tipo_operacion': op.tipo_operacion,
                'actividades': []
            }
            for act in op.actividades.all():
                act_data = {
                    'cod_actividad': act.codigo_actividad,
                    'actividad': act.denominacion,
                    'meta_anual': str(act.meta_anual) if act.meta_anual else '',
                    'tareas': [{
                        'cod_tarea': t.codigo_tarea,
                        'tarea': t.denominacion,
                        'responsable': t.responsable or '',
                    } for t in act.tareas.all()]
                }
                ops_data['actividades'].append(act_data)
            resultado.append(ops_data)
        return Response(resultado)

    @action(detail=False, methods=['get'])
    def m4_presupuesto(self, request):
        """Matriz 4: Presupuesto y seguimiento."""
        gestion = request.query_params.get('gestion')
        qs = SeguimientoPresupuesto.objects.all()
        if gestion:
            qs = qs.filter(gestion=int(gestion))
        return Response(list(qs.values()))

    @action(detail=False, methods=['get'])
    def m5_objetos_gasto(self, request):
        """Matriz 5: Asignación de objetos de gasto."""
        gestion = request.query_params.get('gestion')
        qs = AsignacionObjetoGasto.objects.all()
        if gestion:
            qs = qs.filter(gestion=int(gestion))
        return Response(list(qs.values()))
