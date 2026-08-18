"""
Vistas de matrices desnormalizadas (como aparecen en el Excel).
Cada endpoint devuelve una fila = cadena completa de articulación.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Prefetch
from datetime import date
from apps.presupuesto.models import AsignacionPresupuestariaUnidad
from .models import (
    ArticulacionPADPEI, IndicadorCadena, AccionPOA,
    OperacionPOAU, ActividadPOAU, ResultadoPEI, ProductoPEI,
    SeguimientoPresupuesto, AsignacionObjetoGasto
)

GESTIONES_PEI = ('2026', '2027', '2028', '2029', '2030')

NO_APLICA = 'NO APLICA'
from .services import construir_matriz_a_gestion, construir_matriz_b_gestion


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


def _pei_articulacion(result):
    """Secciones I a IV y articulación territorial: son idénticas en todas las
    filas que cuelgan de un mismo resultado institucional."""
    return {
        'cod_eje_pgdesa': _text(result.cod_eje_pgdesa),
        'objetivo_impacto': _text(result.objetivo_impacto),
        'cod_componente_pdesa': _text(result.cod_componente_pdesa),
        'objetivo_efecto': _text(result.objetivo_efecto),
        'cod_ods': _text(result.cod_ods),
        'cod_ndc': _text(result.cod_ndc),
        'cod_ndt': _text(result.cod_ndt),
        'cod_meta_3030': _text(result.cod_meta_3030),
        'cod_sector': _text(result.cod_sector),
        'sector': _text(result.sector),
        'cod_resultado_sectorial': _text(result.cod_resultado_sectorial),
        'resultado_sectorial': _text(result.resultado_sectorial),
        'cod_resultado_territorial': _text(result.cod_resultado_territorial),
        'cod_entidad': _text(result.cod_entidad),
        'entidad': _text(result.entidad),
        'cod_oei': _text(result.cod_oei),
        'cod_resultado_pei': _text(result.codigo_resultado),
        'resultado_institucional': _text(result.denominacion),
    }


def _pei_indicador(indicator):
    """Secciones VI, VII y VIII a partir del indicador de la fila."""
    fisica = getattr(indicator, 'programacion_fisica', None) or {}
    inversion = {
        year: _decimal(getattr(indicator, f'inversion_{year}', None))
        for year in GESTIONES_PEI
    } if indicator else {year: '' for year in GESTIONES_PEI}
    corriente = {
        year: _decimal(getattr(indicator, f'corriente_{year}', None))
        for year in GESTIONES_PEI
    } if indicator else {year: '' for year in GESTIONES_PEI}
    inversion_total = _decimal(getattr(indicator, 'presupuesto_inversion_total', None))
    corriente_total = _decimal(getattr(indicator, 'presupuesto_corriente_total', None))
    total = (
        (getattr(indicator, 'presupuesto_inversion_total', None) or 0)
        + (getattr(indicator, 'presupuesto_corriente_total', None) or 0)
    ) if indicator else 0
    return {
        'indicador': _text(getattr(indicator, 'indicador', '')),
        'tipo_indicador': _text(getattr(indicator, 'tipo_indicador', '')),
        'unidad_medida': _text(getattr(indicator, 'unidad_medida', '')),
        'formula': _text(getattr(indicator, 'formula', '')),
        'linea_base': _decimal(getattr(indicator, 'linea_base', None)),
        'meta_2030': _decimal(getattr(indicator, 'meta_2030', None)),
        'fisica': {year: _text(str(fisica.get(year, ''))) for year in GESTIONES_PEI},
        'presupuesto_total': _decimal(total) if total else '',
        'inversion_total': inversion_total,
        'inversion': inversion,
        'corriente_total': corriente_total,
        'corriente': corriente,
    }


def _serialize_pei_resultado(result, indicator):
    """Fila de nivel resultado: programa y producto van en NO APLICA."""
    return {
        'id': str(result.pk),
        'nivel': 'resultado',
        **_pei_articulacion(result),
        'cod_programa_presup': NO_APLICA,
        'programa_presup': NO_APLICA,
        'cod_producto': NO_APLICA,
        'nombre_producto': NO_APLICA,
        'tipo_producto': '',
        **_pei_indicador(indicator),
    }


def _serialize_pei_producto(product, indicator):
    result = product.resultado_pei
    return {
        'id': str(product.pk),
        'nivel': 'producto',
        **_pei_articulacion(result),
        'cod_programa_presup': _text(product.cod_programa_presup),
        'programa_presup': _text(product.programa_presup),
        'cod_producto': _text(product.codigo_producto),
        'nombre_producto': _text(product.denominacion),
        'tipo_producto': _text(product.tipo_producto),
        **_pei_indicador(indicator),
    }


class MatrizViewSet(viewsets.ViewSet):
    """Endpoints que devuelven matrices desnormalizadas (formato Excel)."""

    @action(detail=False, methods=['get'])
    def pei_territorial(self, request):
        """Matriz de planificación PEI territorial (46 columnas, 8 secciones).

        Cada resultado institucional aporta una fila de nivel resultado seguida
        de una fila por cada producto institucional que lo compone.
        GET /api/v1/articulacion/matrices/pei_territorial/?vigencia_desde=2026
        """
        vigencia = request.query_params.get('vigencia_desde')
        cod_entidad = request.query_params.get('cod_entidad')
        qs = ResultadoPEI.objects.prefetch_related(
            Prefetch(
                'productos',
                queryset=ProductoPEI.objects.prefetch_related('indicadores'),
            ),
            'indicadores',
        )
        if vigencia:
            qs = qs.filter(vigencia_desde=int(vigencia))
        if cod_entidad:
            qs = qs.filter(cod_entidad=cod_entidad)

        filas = []
        for result in qs.order_by('codigo_resultado'):
            filas.append(
                _serialize_pei_resultado(result, result.indicadores.first())
            )
            for product in result.productos.all():
                filas.append(
                    _serialize_pei_producto(product, product.indicadores.first())
                )
        return Response(filas)

    def _gestion_param(self, request, por_defecto=2026):
        """Lee y valida ``?gestion=`` (int); 400 si no es numérico."""
        raw = request.query_params.get('gestion') or por_defecto
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    @action(detail=False, methods=['get'])
    def matriz_a_gestion(self, request):
        """Matriz A (27 columnas) ACUMULADA de la gestión completa.

        GET /api/v1/articulacion/matrices/matriz_a_gestion/?gestion=2026

        Acumula TODOS los ResultadoPAD materializados de la gestión (todos
        los borradores COMPLETO + cualquier ResultadoPAD existente con
        ``vigencia_desde=gestion``) en una sola Matriz A: por cada resultado
        1 fila + 1 fila por producto, ordenado por cgeo, lineamiento,
        resultado y producto. Reutiliza la misma lógica de filas que la
        matriz por borrador (construir_matriz_a).

        Respuesta: ``{gestion, fecha, total_filas, filas: [...]}``.
        """
        gestion = self._gestion_param(request)
        if gestion is None:
            return Response(
                {'error': 'Parámetro "gestion" debe ser numérico.'},
                status=400,
            )
        filas = construir_matriz_a_gestion(gestion)
        return Response({
            'gestion': gestion,
            'fecha': date.today().isoformat(),
            'total_filas': len(filas),
            'filas': filas,
        })

    @action(detail=False, methods=['get'])
    def matriz_b_gestion(self, request):
        """Matriz B (34 columnas) ACUMULADA de la gestión completa.

        GET /api/v1/articulacion/matrices/matriz_b_gestion/?gestion=2026

        Idem ``matriz_a_gestion`` pero para la Matriz B (34 columnas),
        reutilizando la lógica de filas de ``construir_matriz_b``.

        Respuesta: ``{gestion, fecha, total_filas, filas: [...]}``.
        """
        gestion = self._gestion_param(request)
        if gestion is None:
            return Response(
                {'error': 'Parámetro "gestion" debe ser numérico.'},
                status=400,
            )
        filas = construir_matriz_b_gestion(gestion)
        return Response({
            'gestion': gestion,
            'fecha': date.today().isoformat(),
            'total_filas': len(filas),
            'filas': filas,
        })

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

    @action(detail=False, methods=['get'])
    def catalogos_articulacion(self, request):
        """Catálogos de soporte para los formularios de articulación.

        Devuelve ejes PGDESA, componentes PDESA, lineamientos PAD, sectores
        económicos presupuestarios y unidades de medida desde los modelos
        canónicos (codificacion + catalogos), filtrado por gestión cuando se
        provee (?gestion=2027).

        TODO-articulacion-s2: main no tiene objetivo_impacto (EjePGDESA),
        objetivo_efecto (ComponentePDESA) ni FK LineamientoPAD.componente;
        esos campos salen degradados ('').
        """
        gestion = request.query_params.get('gestion')

        def _by_gestion(qs):
            if gestion:
                return qs.filter(version_catalogo__gestion=int(gestion))
            return qs

        from apps.codificacion.models import (
            EjePGDESA, ComponentePDESA, LineamientoPAD,
            EntidadTerritorialCGEO, ResultadoSectorial, SectorEconomico,
        )
        from apps.catalogos.models import UnidadMedida

        ejes = [
            {'codigo': e.codigo, 'denominacion': e.denominacion, 'id': str(e.id),
             'objetivo_impacto': getattr(e, 'objetivo_impacto', '') or ''}
            for e in _by_gestion(EjePGDESA.objects.all()).order_by('codigo')
        ]
        componentes = [
            {'codigo': c.codigo, 'denominacion': c.denominacion, 'id': str(c.id),
             'eje_codigo': getattr(getattr(c, 'eje', None), 'codigo', ''),
             'objetivo_efecto': getattr(c, 'objetivo_efecto', '') or ''}
            for c in _by_gestion(ComponentePDESA.objects.select_related('eje').all()).order_by('codigo')
        ]
        lineamientos = [
            {'codigo': l.codigo, 'denominacion': l.denominacion, 'id': str(l.id),
             'componente_codigo': getattr(getattr(l, 'componente', None), 'codigo', '')}
            for l in _by_gestion(LineamientoPAD.objects.all()).order_by('codigo')
        ]
        # Sectores del PAD (segmento SS, 2 dígitos) desde el catálogo maestro
        # nacional: los 24 completos, incluidos los administrativos/estatales
        # (14 ADMINISTRACION GENERAL, 15 ORDEN PUBLICO Y SEGURIDAD CIUDADANA,
        # 16 DEFENSA, 17 DEUDA PUBLICA), porque el GAM también planifica en
        # ellos. Se lee codificacion.SectorEconomico —no el clasificador
        # presupuestario de 3 niveles, que es otro catálogo.
        sectores = [
            {'codigo': s.codigo, 'denominacion': s.denominacion, 'id': str(s.id)}
            for s in _by_gestion(SectorEconomico.objects.all()).order_by('codigo')
        ]
        # Si la gestión pedida no tiene ejes/componentes, fallback a 2026
        # (el catálogo maestro está poblado en 2026 baseline; 2027 pendiente
        # de homologación). Los formularios de articulación usan vigencia 2026.
        if not ejes:
            ejes = [
                {'codigo': e.codigo, 'denominacion': e.denominacion, 'id': str(e.id),
                 'objetivo_impacto': getattr(e, 'objetivo_impacto', '') or ''}
                for e in EjePGDESA.objects.filter(
                    version_catalogo__gestion=2026
                ).order_by('codigo')
            ]
        if not componentes:
            componentes = [
                {'codigo': c.codigo, 'denominacion': c.denominacion, 'id': str(c.id),
                 'eje_codigo': getattr(getattr(c, 'eje', None), 'codigo', ''),
                 'objetivo_efecto': getattr(c, 'objetivo_efecto', '') or ''}
                for c in ComponentePDESA.objects.select_related('eje').filter(
                    version_catalogo__gestion=2026
                ).order_by('codigo')
            ]
        if not lineamientos:
            lineamientos = [
                {'codigo': l.codigo, 'denominacion': l.denominacion, 'id': str(l.id),
                 'componente_codigo': getattr(getattr(l, 'componente', None), 'codigo', '')}
                for l in LineamientoPAD.objects.filter(
                    version_catalogo__gestion=2026
                ).order_by('codigo')
            ]
        if not sectores:
            sectores = [
                {'codigo': s.codigo, 'denominacion': s.denominacion, 'id': str(s.id)}
                for s in SectorEconomico.objects.filter(
                    version_catalogo__gestion=2026
                ).order_by('codigo')
            ]
        unidades = [
            {'codigo': u.codigo, 'denominacion': u.denominacion, 'id': str(u.id)}
            for u in UnidadMedida.objects.all().order_by('codigo')
        ]
        # Entidades territoriales CGEO (clasificador geográfico INE/MEPF) para
        # el paso de contexto territorial: el código CGEO se elige de catálogo,
        # no se escribe como texto libre.
        entidades_territoriales = [
            {'codigo': e.codigo, 'denominacion': e.nombre, 'nivel': e.nivel, 'id': str(e.id)}
            for e in EntidadTerritorialCGEO.objects.all().order_by('codigo')
        ]
        # Resultados sectoriales del PDS (clasificador codificacion.ResultadoSectorial).
        # ``sector_codigo`` permite la cascada sector → resultado sectorial; si el
        # sector elegido no tiene resultados, el formulario los muestra libres.
        resultados_sectoriales = [
            {'codigo': r.codigo, 'denominacion': r.denominacion, 'id': str(r.id),
             'sector_codigo': getattr(getattr(r, 'sector', None), 'codigo', '')}
            for r in ResultadoSectorial.objects.select_related('sector').all().order_by('codigo')
        ]
        return Response({
            'ejes': ejes,
            'componentes': componentes,
            'lineamientos': lineamientos,
            'sectores': sectores,
            'unidades_medida': unidades,
            'entidades_territoriales': entidades_territoriales,
            'resultados_sectoriales': resultados_sectoriales,
        })
