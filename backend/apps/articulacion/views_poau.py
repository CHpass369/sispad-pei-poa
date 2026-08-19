"""Matriz POAU: el árbol del formato oficial, con filtro por unidad.

La planilla no repite la cadena en cada fila: cada nivel ocupa su propia fila y
su propio color, escalonándose hacia la derecha. Acá se devuelve esa misma
jerarquía como lista plana con `nivel` y `padre`, que es lo que necesita una
tabla —las columnas tienen que seguir alineadas— sin perder el árbol.

    unidad → acción institucional específica (PEI) → acción de corto plazo
           → operación (producto intermedio) → actividad → tarea

El cronograma mensual viaja como doce columnas más el total anual.
"""
from rest_framework import viewsets
from rest_framework.response import Response

import re

from django.shortcuts import get_object_or_404

from .models import AccionPOA, OperacionPOAU

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

# Orden de la planilla; el frontend lo usa para el escalonado y los colores.
NIVELES = ['unidad', 'aie', 'accion', 'operacion', 'actividad', 'tarea']


def _plan(origen):
    """El cronograma se guarda con clave libre: se normaliza a minúsculas."""
    plan = {str(k).lower(): v for k, v in (origen or {}).items()}
    return {m: plan.get(m) for m in MESES}


def _num(v):
    return None if v is None else float(v)


def _codigo_categoria(valor):
    """La categoría viaja con espaciado irregular según de dónde se cargó."""
    return re.sub(r'\s+', ' ', str(valor or '')).strip().upper()


def catalogo_categorias(gestion):
    """Denominaciones oficiales de la categoría programática, por gestión.

    Devuelve dos diccionarios: el de coincidencia exacta (nivel ACTIVIDAD, que
    es lo que usa el POAU) y el de PROGRAMA, que sirve de respaldo cuando la
    actividad todavía no está dada de alta en el catálogo.
    """
    from apps.budget.models import CategoriaProgramaticaTecho

    qs = CategoriaProgramaticaTecho.objects.all()
    if gestion:
        por_gestion = qs.filter(gestion__anio=int(gestion))
        # Si la gestión aún no tiene catálogo propio se usa el vigente.
        qs = por_gestion if por_gestion.exists() else qs
    exacto, programa = {}, {}
    for c in qs:
        codigo = _codigo_categoria(c.codigo)
        if c.nivel == 'PROGRAMA':
            programa[codigo] = c.denominacion
        else:
            exacto[codigo] = c.denominacion
    return exacto, programa


class MatrizPOAUViewSet(viewsets.ViewSet):
    """GET /matriz-poau/?gestion=2027&unidad=EM-DJR-01"""

    def _fila(self, nivel, clave, padre, **campos):
        fila = {
            'id': clave, 'padre': padre, 'nivel': nivel,
            'orden_nivel': NIVELES.index(nivel), 'hijos': 0,
        }
        # Toda fila declara las 34 columnas: la tabla no puede desalinearse
        # porque un nivel no tenga indicador.
        for c in ('objeto_id', 'tipo', 'accion_id', 'observacion',
                  'origen_categoria',
                  'codigo', 'unidad', 'unidad_codigo', 'cod_producto_pei',
                  'accion_institucional', 'cod_accion_corto_plazo',
                  'accion_corto_plazo', 'categoria_programatica',
                  'denominacion_categoria', 'operacion', 'actividad', 'tarea',
                  'indicador', 'formula', 'unidad_medida', 'linea_base',
                  'meta', 'meta_actual', 'fecha_inicio', 'fecha_fin',
                  'ponderacion', 'total_anual', 'resultado_logrado',
                  'responsable', 'estado'):
            fila[c] = ''
        for m in MESES:
            fila[f'mes_{m}'] = None
        fila.update(campos)
        return fila

    def _programacion(self, obj):
        """Indicador, meta, fechas y cronograma de un nodo ejecutable."""
        meses = _plan(getattr(obj, 'programacion_mensual', None))
        total = sum(float(v) for v in meses.values() if v is not None)
        meta = getattr(obj, 'meta_anual', None)
        if meta is None:
            meta = getattr(obj, 'metas', None)
        return {
            'objeto_id': str(obj.id),
            'observacion': getattr(obj, 'observacion', '') or '',
            'indicador': getattr(obj, 'indicador', '') or '',
            'formula': getattr(obj, 'formula', '') or '',
            'unidad_medida': getattr(obj, 'unidad_medida', '') or '',
            'meta': _num(meta),
            'fecha_inicio': obj.fecha_inicio.isoformat() if obj.fecha_inicio else '',
            'fecha_fin': obj.fecha_fin.isoformat() if obj.fecha_fin else '',
            'responsable': getattr(obj, 'responsable', '') or '',
            'estado': getattr(obj, 'estado', '') or '',
            'total_anual': total or None,
            **{f'mes_{m}': _num(v) for m, v in meses.items()},
        }

    def _denominacion_categoria(self, codigo, exacto, programa):
        """Denominación de catálogo; `origen` avisa si es una aproximación."""
        clave = _codigo_categoria(codigo)
        if clave in exacto:
            return exacto[clave], 'catalogo'
        # Sin la actividad exacta, el programa es lo más preciso disponible.
        raiz = clave.split(' ')[0]
        if raiz in programa:
            return programa[raiz], 'programa'
        return '', ''

    def list(self, request):
        gestion = request.query_params.get('gestion')
        unidad = request.query_params.get('unidad')

        operaciones = (
            OperacionPOAU.objects
            .select_related('accion_poa__producto_pei',
                            'accion_poa__unidad_responsable')
            .prefetch_related('actividades__tareas')
            .order_by('accion_poa__unidad_responsable__codigo',
                      'accion_poa__codigo_accion', 'codigo_operacion')
        )
        if gestion:
            operaciones = operaciones.filter(accion_poa__gestion=int(gestion))
        if unidad:
            operaciones = operaciones.filter(
                accion_poa__unidad_responsable__codigo=unidad)

        exacto, programa = catalogo_categorias(gestion)
        filas, indice, unidades = [], {}, {}

        def rama(clave, nivel, padre, **campos):
            """Crea el nodo una sola vez y lo cuelga de su padre."""
            if clave not in indice:
                fila = self._fila(nivel, clave, padre, **campos)
                indice[clave] = fila
                filas.append(fila)
                if padre in indice:
                    indice[padre]['hijos'] += 1
            return clave

        for op in operaciones:
            accion = op.accion_poa
            uo = accion.unidad_responsable if accion else None
            producto = accion.producto_pei if accion else None
            if uo:
                unidades[uo.codigo] = uo.nombre

            cod_uo = uo.codigo if uo else 'SIN-UNIDAD'
            k_uo = rama(f'u:{cod_uo}', 'unidad', None,
                        unidad=uo.nombre if uo else 'Sin unidad asignada',
                        unidad_codigo=cod_uo, codigo=cod_uo)

            cod_pei = producto.codigo_producto if producto else 'SIN-PEI'
            k_pei = rama(f'{k_uo}|p:{cod_pei}', 'aie', k_uo,
                         cod_producto_pei=cod_pei, codigo=cod_pei,
                         accion_institucional=producto.denominacion if producto else '')

            denominacion_cat, origen_cat = self._denominacion_categoria(
                accion.categoria_programatica, exacto, programa)
            categoria = {
                'categoria_programatica': accion.categoria_programatica or '',
                'denominacion_categoria': denominacion_cat,
                'origen_categoria': origen_cat,
            }

            k_acc = rama(f'{k_pei}|a:{accion.codigo_accion}', 'accion', k_pei,
                         cod_accion_corto_plazo=accion.codigo_accion,
                         codigo=accion.codigo_accion,
                         accion_corto_plazo=accion.denominacion,
                         **categoria)

            k_op = rama(f'{k_acc}|o:{op.codigo_operacion}', 'operacion', k_acc,
                        **categoria,
                        operacion=op.denominacion, codigo=op.codigo_operacion,
                        tipo='operacion', accion_id=str(accion.id),
                        **self._programacion(op))

            for act in op.actividades.all():
                k_act = rama(f'{k_op}|c:{act.codigo_actividad}', 'actividad', k_op,
                             **categoria,
                             actividad=act.denominacion,
                             codigo=act.codigo_actividad,
                             tipo='actividad', accion_id=str(accion.id),
                             **self._programacion(act))
                for tarea in act.tareas.all():
                    rama(f'{k_act}|t:{tarea.codigo_tarea}', 'tarea', k_act,
                         **categoria,
                         tarea=tarea.denominacion, codigo=tarea.codigo_tarea,
                         tipo='tarea', accion_id=str(accion.id),
                         **self._programacion(tarea))

        # Una acción institucional puede agrupar acciones de corto plazo con
        # categorías distintas: en ese caso no hay un valor único que replicar
        # y se deja vacío en vez de elegir uno al azar.
        por_aie = {}
        for f in filas:
            if f['nivel'] == 'accion' and f['categoria_programatica']:
                por_aie.setdefault(f['padre'], set()).add(
                    (f['categoria_programatica'], f['denominacion_categoria'],
                     f['origen_categoria']))
        for f in filas:
            if f['nivel'] == 'aie':
                unicas = por_aie.get(f['id'], set())
                if len(unicas) == 1:
                    cat, den, origen = next(iter(unicas))
                    f['categoria_programatica'] = cat
                    f['denominacion_categoria'] = den
                    f['origen_categoria'] = origen

        return Response({
            'gestion': int(gestion) if gestion else None,
            'unidades': [{'codigo': c, 'nombre': n}
                         for c, n in sorted(unidades.items())],
            'total_filas': len(filas),
            'filas': filas,
        })

    def retrieve(self, request, pk=None):
        """GET /matriz-poau/<accion_id>/ — la acción cargada para el wizard.

        Devuelve la programación existente con la forma que consumen los
        formularios de `poau-matriz.model.ts`, para que editar sea modificar lo
        que ya está y no volver a tipearlo.
        """
        accion = get_object_or_404(
            AccionPOA.objects.select_related('producto_pei', 'unidad_responsable'),
            pk=pk,
        )
        producto = accion.producto_pei

        def indicador(obj):
            return {
                'indicador': obj.indicador or '',
                'formula': obj.formula or 'N/A',
                'unidadMedida': obj.unidad_medida or '',
                # La línea base no existe en los modelos POAU todavía.
                'lineaBase': None,
                'meta': _num(obj.meta_anual),
            }

        def fechas(obj):
            return {
                'fechaInicio': obj.fecha_inicio.isoformat() if obj.fecha_inicio else '',
                'fechaFin': obj.fecha_fin.isoformat() if obj.fecha_fin else '',
            }

        operaciones = []
        for op in (accion.operaciones
                   .prefetch_related('actividades__tareas')
                   .order_by('codigo_operacion')):
            actividades = []
            for act in op.actividades.all().order_by('codigo_actividad'):
                actividades.append({
                    'id': str(act.id), 'codigo': act.codigo_actividad,
                    'estado': act.estado, 'observacion': act.observacion or '',
                    'denominacion': act.denominacion,
                    'productoIntermedio': act.producto_entregable or '',
                    'indicador': indicador(act), **fechas(act),
                    'ponderacion': None,
                    'programacion': _plan(act.programacion_mensual),
                    'tareas': [{
                        'id': str(t.id), 'codigo': t.codigo_tarea,
                        'estado': t.estado, 'observacion': t.observacion or '',
                        'denominacion': t.denominacion,
                        'responsable': t.responsable or '', **fechas(t),
                        'programacion': _plan(t.programacion_mensual),
                    } for t in act.tareas.all().order_by('codigo_tarea')],
                })
            operaciones.append({
                'id': str(op.id), 'codigo': op.codigo_operacion,
                'estado': op.estado, 'observacion': op.observacion or '',
                'denominacion': op.denominacion,
                'tipoOperacion': op.tipo_operacion or 'FUNCIONAMIENTO',
                'productoIntermedio': op.producto_entregable or '',
                'unidadEjecutora': op.unidad_ejecutora or '',
                'indicador': indicador(op), **fechas(op),
                'ponderacion': None,
                'programacion': _plan(op.programacion_mensual),
                'actividades': actividades,
            })

        return Response({
            'cabecera': {
                'codigoProductoPei': producto.codigo_producto if producto else '',
                'accionInstitucionalEspecifica': producto.denominacion if producto else '',
                'indicadorProceso': accion.indicador or '',
                'codigoAccionCortoPlazo': accion.codigo_accion,
                'accionCortoPlazo': accion.denominacion,
                'categoriaProgramatica': accion.categoria_programatica or '',
                'denominacionCategoria': accion.programa or '',
                'accionPoaId': str(accion.id),
                'gestion': accion.gestion,
            },
            'unidad': {
                'codigo': accion.unidad_responsable.codigo if accion.unidad_responsable else '',
                'nombre': accion.unidad_responsable.nombre if accion.unidad_responsable else '',
            },
            'operaciones': operaciones,
        })
