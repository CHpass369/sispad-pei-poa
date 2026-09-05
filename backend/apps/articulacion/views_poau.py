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
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

import re

from django.shortcuts import get_object_or_404

from apps.accounts.permissions import TieneCapacidad
from apps.accounts.services_scope import GLOBAL_SCOPE, ScopeResolver
from apps.gestion.mixins import gestion_del_candado

from .models import AccionPOA, AsignacionObjetoGasto, OperacionPOAU

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
    """GET /matriz-poau/?gestion=2027&unidad=EM-DJR-01

    Acotado por alcance organizacional (ADR-003). Antes era un ViewSet sin
    capacidad ni scope: `?unidad=` era libre y la respuesta traía el catálogo
    completo de UO, así que cualquiera podía leer —y elegir— la matriz de una
    unidad ajena. Ahora:

    - exige `sis_poa.poau.view`;
    - las filas se limitan a las UO efectivas del usuario;
    - el catálogo `unidades` que alimenta el selector del frontend sale de esas
      mismas UO, para que el desplegable no ofrezca lo que no puede abrir.

    Un alcance GLOBAL (SUPER_ADMIN, jefaturas) sigue viendo todo: el
    filtrado solo muerde a quien tiene alcance acotado.
    """

    def get_permissions(self):
        # Patrón del proyecto: instancias desde get_permissions.
        return [TieneCapacidad('sis_poa.poau.view')]

    @staticmethod
    def _codigos_en_alcance(request):
        """Códigos de UO que el usuario puede leer, o None si es GLOBAL."""
        if request.user.is_superuser:
            return None
        unidades = ScopeResolver.unidades_efectivas(
            request.user, gestion_del_candado(request).id,
        )
        if GLOBAL_SCOPE in unidades:
            return None
        from apps.organizacion.models import UnidadOrganizacional

        return set(
            UnidadOrganizacional.objects
            .filter(pk__in=unidades)
            .values_list('codigo', flat=True)
        )

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
            'linea_base': _num(getattr(obj, 'linea_base', None)),
            'meta': _num(meta),
            'meta_actual': _num(getattr(obj, 'meta_actual', None)),
            'fecha_inicio': obj.fecha_inicio.isoformat() if obj.fecha_inicio else '',
            'fecha_fin': obj.fecha_fin.isoformat() if obj.fecha_fin else '',
            'responsable': getattr(obj, 'responsable', '') or '',
            'estado': getattr(obj, 'estado', '') or '',
            'total_anual': total or None,
            'ponderacion': _num(getattr(obj, 'ponderacion', None)),
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

    @action(detail=False, methods=['get'], url_path='presupuesto')
    def presupuesto(self, request):
        """Programación presupuestaria del POAU, agrupada por categoría.

        Es la contraparte financiera de la matriz física y va debajo de ella en
        la misma pantalla: lo que el asistente de recursos registró como
        requerimientos, ordenado por la categoría programática que lo clasifica.

        Comparte candado, alcance y filtro `?unidad=` con `list()`: si la
        matriz de arriba muestra una unidad, la de abajo tiene que mostrar el
        presupuesto de esa misma unidad y no el de todas.
        """
        gestion = gestion_del_candado(request).anio
        unidad = request.query_params.get('unidad')
        en_alcance = self._codigos_en_alcance(request)

        qs = (
            AsignacionObjetoGasto.objects
            .select_related('accion_poa__unidad_responsable', 'operacion',
                            'actividad')
            .filter(gestion=gestion)
            .order_by('categoria_programatica', 'codigo_asignacion')
        )
        if en_alcance is not None:
            qs = qs.filter(
                accion_poa__unidad_responsable__codigo__in=en_alcance)
        if unidad:
            qs = qs.filter(accion_poa__unidad_responsable__codigo=unidad)

        exacto, programa = catalogo_categorias(gestion)
        grupos: dict = {}
        for fila in qs:
            codigo = _codigo_categoria(fila.categoria_programatica)
            grupo = grupos.setdefault(codigo, {
                'categoria': fila.categoria_programatica or '',
                # La denominación sale del catálogo y no de la fila: el acta
                # guarda el código, y el nombre es del maestro.
                'denominacion': exacto.get(codigo)
                or programa.get(_codigo_categoria(fila.programa)) or '',
                'total': 0.0,
                'filas': [],
            })
            meses = _plan(fila.programacion_mensual)
            total = sum(float(v) for v in meses.values() if v is not None)
            # El total del renglón es la suma mensual y no `monto_programado`:
            # es lo que efectivamente quedó distribuido en el año.
            grupo['total'] += total
            renglon = {
                'id': str(fila.pk),
                'codigo_asignacion': fila.codigo_asignacion,
                'accion': fila.accion_poa.codigo_accion if fila.accion_poa else '',
                'actividad': (fila.actividad.codigo_actividad
                              if fila.actividad else ''),
                'unidad': (fila.accion_poa.unidad_responsable.codigo
                           if fila.accion_poa
                           and fila.accion_poa.unidad_responsable else ''),
                'da': fila.da, 'ue': fila.ue,
                'cod_objeto_gasto': fila.cod_objeto_gasto,
                'descripcion_objeto': fila.descripcion_objeto,
                'grupo_gasto': fila.grupo_gasto,
                'tipo_gasto': fila.tipo_gasto,
                'fuente_financiamiento': fila.fuente_financiamiento,
                'organismo_financiador': fila.organismo_financiador,
                'fecha_requerimiento': fila.fecha_requerimiento,
                'monto_programado': _num(fila.monto_programado),
                'total_anual': total,
                'estado': fila.estado,
            }
            for mes, valor in meses.items():
                renglon[f'mes_{mes}'] = _num(valor)
            grupo['filas'].append(renglon)

        categorias = sorted(grupos.values(), key=lambda g: g['categoria'])
        return Response({
            'gestion': gestion,
            'total': sum(g['total'] for g in categorias),
            'categorias': categorias,
        })

    def list(self, request):
        # El candado manda: el POAU es de la gestión habilitada. Antes, sin
        # `?gestion=`, la matriz mezclaba las acciones de todos los años.
        gestion = gestion_del_candado(request).anio
        unidad = request.query_params.get('unidad')
        # El alcance manda sobre `?unidad=`: pedir una UO fuera del alcance no
        # devuelve la matriz ajena, devuelve vacío.
        en_alcance = self._codigos_en_alcance(request)

        operaciones = (
            OperacionPOAU.objects
            .select_related('accion_poa__producto_pei',
                            'accion_poa__unidad_responsable')
            .prefetch_related('actividades__tareas')
            .order_by('accion_poa__unidad_responsable__codigo',
                      'accion_poa__codigo_accion', 'codigo_operacion')
            .filter(accion_poa__gestion=gestion)
        )
        if en_alcance is not None:
            operaciones = operaciones.filter(
                accion_poa__unidad_responsable__codigo__in=en_alcance)
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

            def _categoria(codigo):
                denominacion, origen = self._denominacion_categoria(
                    codigo, exacto, programa)
                return {
                    'categoria_programatica': codigo or '',
                    'denominacion_categoria': denominacion,
                    'origen_categoria': origen,
                }

            categoria = _categoria(accion.categoria_programatica)
            # Una acción agrupa operaciones de categorías distintas, así que la
            # categoría de la rama es la de la operación cuando la tiene; la de
            # la acción queda de respaldo para los POAU cargados antes de que
            # `OperacionPOAU.categoria_programatica` existiera.
            categoria_op = (
                _categoria(op.categoria_programatica)
                if op.categoria_programatica else categoria
            )

            k_acc = rama(f'{k_pei}|a:{accion.codigo_accion}', 'accion', k_pei,
                         cod_accion_corto_plazo=accion.codigo_accion,
                         codigo=accion.codigo_accion,
                         accion_corto_plazo=accion.denominacion,
                         **categoria)

            k_op = rama(f'{k_acc}|o:{op.codigo_operacion}', 'operacion', k_acc,
                        **categoria_op,
                        operacion=op.denominacion, codigo=op.codigo_operacion,
                        tipo='operacion', accion_id=str(accion.id),
                        **self._programacion(op))

            for act in op.actividades.all():
                k_act = rama(f'{k_op}|c:{act.codigo_actividad}', 'actividad', k_op,
                             **categoria_op,
                             actividad=act.denominacion,
                             codigo=act.codigo_actividad,
                             tipo='actividad', accion_id=str(accion.id),
                             **self._programacion(act))
                for tarea in act.tareas.all():
                    rama(f'{k_act}|t:{tarea.codigo_tarea}', 'tarea', k_act,
                         **categoria_op,
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

        incluir_unidades = request.query_params.get('incluir_unidades', '1') != '0'
        return Response({
            'gestion': int(gestion) if gestion else None,
            'unidades': (
                self._catalogo_unidades(gestion, en_alcance)
                if incluir_unidades else []
            ),
            'total_filas': len(filas),
            'filas': filas,
        })

    @staticmethod
    def _catalogo_unidades(gestion, en_alcance):
        """Unidades que el selector puede ofrecer.

        Sale del catálogo organizacional de la gestión, incluso si una unidad
        todavía no tiene acciones POA. El frontend lo solicita una sola vez y
        reutiliza la lista al cambiar el filtro de la matriz.
        """
        from apps.organizacion.models import UnidadOrganizacional

        catalogo = (
            UnidadOrganizacional.objects
            .filter(gestion__anio=gestion, activo=True)
        )
        if en_alcance is not None:
            catalogo = catalogo.filter(codigo__in=en_alcance)
        # `id` va incluido porque la administración de saldos necesita la clave
        # foránea para crear un techo; el resto de los consumidores solo lee
        # `codigo` y `nombre`, y una clave de más no los afecta.
        return list(
            catalogo.values('id', 'codigo', 'nombre', 'sigla').order_by('codigo')
        )

    def retrieve(self, request, pk=None):
        """GET /matriz-poau/<accion_id>/ — la acción cargada para el wizard.

        Devuelve la programación existente con la forma que consumen los
        formularios de `poau-matriz.model.ts`, para que editar sea modificar lo
        que ya está y no volver a tipearlo.
        """
        # Acotado al candado: editar una acción de una gestión cerrada es
        # justamente lo que el candado impide (ADR-007).
        accion = get_object_or_404(
            AccionPOA.objects
            .select_related('producto_pei', 'unidad_responsable')
            .filter(gestion=gestion_del_candado(request).anio),
            pk=pk,
        )
        # Sin esto, adivinar un UUID abría la acción de cualquier unidad: el
        # filtro del listado no protege el detalle.
        en_alcance = self._codigos_en_alcance(request)
        if en_alcance is not None:
            codigo = (
                accion.unidad_responsable.codigo
                if accion.unidad_responsable else None
            )
            if codigo not in en_alcance:
                raise PermissionDenied(
                    'Unidad organizacional fuera de su alcance.',
                )
        producto = accion.producto_pei

        def indicador(obj):
            return {
                'indicador': obj.indicador or '',
                'formula': obj.formula or 'N/A',
                'unidadMedida': obj.unidad_medida or '',
                'lineaBase': _num(obj.linea_base),
                'meta': _num(obj.meta_anual),
                'metaActual': _num(obj.meta_actual),
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
                    'ponderacion': _num(act.ponderacion),
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
                'ponderacion': _num(op.ponderacion),
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
