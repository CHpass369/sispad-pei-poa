from uuid import UUID

from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Subquery, Value, When
from django.utils import timezone
from .models import (
    BorradorMatrizPEI, BorradorMatrizPOA,
    CodigoNivel, AcuerdoInternacional, CompatibilidadAcuerdoInternacional,
    Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto, BorradorMatrizPAD,
)
from .serializers import (
    BorradorMatrizPEISerializer, BorradorMatrizPOASerializer,
    CodigoNivelSerializer, AcuerdoInternacionalSerializer,
    CompatibilidadAcuerdoInternacionalSerializer, NormativaSerializer,
    LineamientoPADSerializer, ResultadoPADSerializer, ProductoPADSerializer,
    ResultadoPEISerializer, ProductoPEISerializer, ArticulacionPADPEISerializer,
    IndicadorCadenaSerializer, AccionPOASerializer, OperacionPOAUSerializer,
    ActividadPOAUSerializer, ActividadNormativaSerializer, TareaPOAUSerializer,
    TareaNormativaSerializer, SeguimientoPresupuestoSerializer,
    AsignacionObjetoGastoSerializer, BorradorMatrizPADSerializer,
    validar_estructura_resultados,
)
from apps.gestion import candado
from apps.gestion.mixins import (
    CandadoSisPoaMixin, GestionHabilitadaFilterMixin, GestionNoHabilitada,
)

from .revision_poau import EstadosPOAU, RevisionPOAUMixin
from .scope_poau import (
    ScopeAccionPOAMixin,
    ScopeActividadPOAUMixin,
    ScopeAsignacionObjetoGastoMixin,
    ScopeOperacionPOAUMixin,
    ScopeTareaPOAUMixin,
)
from .permissions import ArticulacionPermisos, permisos_revision_matriz
from .services import (
    construir_matriz_a,
    construir_matriz_b,
    materializar_borrador_matriz,
    registrar_auditoria,
)
from .services.materializacion_matriz_pei import (
    construir_filas_pei,
    materializar_borrador_pei,
)
from .services.materializacion_matriz_poa import (
    construir_filas_poa,
    materializar_borrador_poa,
)


# Mixin concreto para heredar las actions
class EstadoActionsMixin:
    """Mixin que agrega actions enviar/aprobar/observar a ViewSets con estado."""

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        obj = self.get_object()
        obj.estado = 'ENVIADO'
        obj.save(update_fields=['estado'])
        registrar_auditoria(
            usuario=request.user, accion='enviar',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle='Registro enviado a revisión'
        )
        return Response({'status': 'enviado', 'estado': 'ENVIADO'})

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        obj = self.get_object()
        if obj.estado != 'ENVIADO':
            return Response(
                {'error': 'Solo se puede aprobar registros en estado ENVIADO'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.estado = 'APROBADO'
        obj.save(update_fields=['estado'])
        registrar_auditoria(
            usuario=request.user, accion='aprobar',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle='Registro aprobado'
        )
        return Response({'status': 'aprobado', 'estado': 'APROBADO'})

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        comentario = request.data.get('comentario', '').strip()
        if not comentario:
            return Response(
                {'error': 'Se requiere un comentario para observar'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj = self.get_object()
        obj.estado = 'OBSERVADO'
        obj.save(update_fields=['estado'])
        registrar_auditoria(
            usuario=request.user, accion='devolver',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle=f'Registro observado: {comentario[:200]}'
        )
        return Response({'status': 'observado', 'estado': 'OBSERVADO', 'comentario': comentario})


class CodigoNivelViewSet(viewsets.ModelViewSet):
    queryset = CodigoNivel.objects.all()
    serializer_class = CodigoNivelSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['nivel', 'codigo_nivel', 'editable', 'vigencia']
    search_fields = ['nivel', 'ejemplo']
    ordering_fields = ['codigo_nivel', 'nivel']


class AcuerdoInternacionalViewSet(viewsets.ModelViewSet):
    queryset = AcuerdoInternacional.objects.all()
    serializer_class = AcuerdoInternacionalSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['tipo_acuerdo', 'activo', 'es_codigo_oficial']
    search_fields = ['codigo', 'denominacion']
    ordering_fields = ['tipo_acuerdo', 'codigo']


class CompatibilidadAcuerdoInternacionalViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only V2 contract used by the PAD cascading selectors."""

    queryset = CompatibilidadAcuerdoInternacional.objects.all()
    serializer_class = CompatibilidadAcuerdoInternacionalSerializer
    permission_classes = [ArticulacionPermisos]

    def get_queryset(self):
        queryset = CompatibilidadAcuerdoInternacional.objects.select_related(
            'origen', 'destino',
        ).filter(activo=True).exclude(
            estado=CompatibilidadAcuerdoInternacional.Estados.RECHAZADA,
        )

        origen_ids = self._origen_ids()
        if origen_ids:
            queryset = queryset.filter(origen_id__in=origen_ids)

        destino_tipo = self.request.query_params.get('destino_tipo')
        if destino_tipo:
            queryset = queryset.filter(destino__tipo_acuerdo=destino_tipo)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        if self._parametro_falso('incluir_sugerencias'):
            queryset = queryset.exclude(
                tipo_relacion=CompatibilidadAcuerdoInternacional.TiposRelacion.SUGERENCIA_SEMANTICA,
            )

        if origen_ids:
            destinos_comunes = queryset.values('destino_id').annotate(
                cantidad_origenes=Count('origen_id', distinct=True),
            ).filter(
                cantidad_origenes=len(origen_ids),
            ).values('destino_id')
            queryset = queryset.filter(destino_id__in=Subquery(destinos_comunes))

        return queryset.order_by(
            Case(
                When(confianza='ALTA', then=Value(0)),
                When(confianza='MEDIA', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            Case(
                When(tipo_relacion='OFICIAL_EXPLICITA', then=Value(0)),
                When(tipo_relacion='DERIVADA_DOCUMENTAL', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            'destino__codigo', 'origen__codigo', 'id',
        )

    def _origen_ids(self):
        raw_ids = self.request.query_params.get('origen_ids')
        if raw_ids is None:
            raw_ids = self.request.query_params.get('origen_id')
        if not raw_ids:
            return []
        values = [value.strip() for value in raw_ids.split(',') if value.strip()]
        try:
            return list(dict.fromkeys(str(UUID(value)) for value in values))
        except ValueError as exc:
            raise serializers.ValidationError(
                {'origen_ids': 'Debe contener UUID separados por coma.'}
            ) from exc

    def _parametro_falso(self, nombre):
        valor = self.request.query_params.get(nombre)
        return valor is not None and valor.strip().lower() in {'0', 'false', 'no'}


class NormativaViewSet(viewsets.ModelViewSet):
    queryset = Normativa.objects.all()
    serializer_class = NormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['nivel', 'tipo_norma', 'estado', 'vigencia']
    search_fields = ['codigo_norma', 'denominacion', 'numero_identificador']
    ordering_fields = ['codigo_norma', 'fecha_emision']


class LineamientoPADViewSet(viewsets.ModelViewSet):
    queryset = LineamientoPAD.objects.all()
    serializer_class = LineamientoPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['activo', 'gestion_desde', 'gestion_hasta']
    search_fields = ['codigo', 'denominacion']
    ordering_fields = ['codigo']


class ResultadoPADViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = ResultadoPAD.objects.all()
    serializer_class = ResultadoPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['vigencia_desde', 'vigencia_hasta', 'estado', 'lineamiento_pad']
    search_fields = ['codigo_resultado', 'denominacion']
    ordering_fields = ['codigo_resultado', 'vigencia_desde']


class ProductoPADViewSet(viewsets.ModelViewSet):
    queryset = ProductoPAD.objects.all()
    serializer_class = ProductoPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['resultado_pad']
    search_fields = ['codigo_producto', 'denominacion']
    ordering_fields = ['codigo_producto']


class ResultadoPEIViewSet(viewsets.ModelViewSet):
    queryset = ResultadoPEI.objects.all()
    serializer_class = ResultadoPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = [
        'vigencia_desde', 'vigencia_hasta', 'cod_entidad',
        'cod_oei', 'cod_sector', 'cod_resultado_territorial', 'resultado_pad',
    ]
    search_fields = ['codigo_resultado', 'denominacion']
    ordering_fields = ['codigo_resultado', 'vigencia_desde']


class ProductoPEIViewSet(viewsets.ModelViewSet):
    queryset = ProductoPEI.objects.all()
    serializer_class = ProductoPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['resultado_pei']
    search_fields = ['codigo_producto', 'denominacion']
    ordering_fields = ['codigo_producto']


class ArticulacionPADPEIViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = ArticulacionPADPEI.objects.all()
    serializer_class = ArticulacionPADPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['producto_pad', 'producto_pei', 'estado', 'tipo_contribucion']
    search_fields = ['justificacion']
    ordering_fields = ['producto_pad', 'producto_pei']


class IndicadorCadenaViewSet(viewsets.ModelViewSet):
    queryset = IndicadorCadena.objects.all()
    serializer_class = IndicadorCadenaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = [
        'nivel_indicador', 'producto_pad', 'producto_pei', 'resultado_pei',
    ]
    search_fields = ['indicador', 'unidad_medida']
    ordering_fields = ['nivel_indicador', 'indicador']


# Capacidad que gobierna la escritura de la cadena POAU (ADR-003). La declaran
# los viewsets del POAU para que `ArticulacionPermisos` autorice por capacidad y
# no por código de rol: los perfiles de unidad —ENCARGADO_UO, VALIDADOR_POAU—
# la tienen sembrada desde accounts.0016, pero no figuran en la lista histórica
# `ROLES_FORMULADORES` y por eso recibían 403 al registrar.
#
# El límite territorial NO viaja en la capacidad: lo aplican los mixins de
# `scope_poau`, que todo viewset con esta capacidad debe incluir.
CAPACIDAD_ESCRITURA_POAU = 'sis_poa.poau.edit'


class AccionPOAViewSet(
    ScopeAccionPOAMixin, CandadoSisPoaMixin, EstadoActionsMixin,
    viewsets.ModelViewSet,
):
    """Acciones de corto plazo de la gestión habilitada (ADR-007)."""

    queryset = AccionPOA.objects.all()
    serializer_class = AccionPOASerializer
    permission_classes = [ArticulacionPermisos]
    capacidad_escritura = CAPACIDAD_ESCRITURA_POAU
    filterset_fields = ['estado', 'producto_pei', 'unidad_responsable']
    search_fields = ['codigo_accion', 'denominacion', 'programa']
    ordering_fields = ['codigo_accion', 'gestion', 'denominacion']


class OperacionPOAUViewSet(
    ScopeOperacionPOAUMixin, GestionHabilitadaFilterMixin, RevisionPOAUMixin,
    viewsets.ModelViewSet,
):
    # La operación no lleva gestión propia: la hereda de su acción de corto
    # plazo, y por ahí la acota el candado.
    campo_gestion = 'accion_poa__gestion'

    queryset = OperacionPOAU.objects.all()
    serializer_class = OperacionPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    capacidad_escritura = CAPACIDAD_ESCRITURA_POAU
    filterset_fields = ['accion_poa', 'tipo_operacion', 'estado']
    search_fields = ['codigo_operacion', 'denominacion']
    ordering_fields = ['codigo_operacion', 'denominacion']


class ActividadPOAUViewSet(
    ScopeActividadPOAUMixin, GestionHabilitadaFilterMixin, RevisionPOAUMixin,
    viewsets.ModelViewSet,
):
    campo_gestion = 'operacion__accion_poa__gestion'

    queryset = ActividadPOAU.objects.all()
    serializer_class = ActividadPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    capacidad_escritura = CAPACIDAD_ESCRITURA_POAU
    filterset_fields = ['operacion', 'estado']
    search_fields = ['codigo_actividad', 'denominacion']
    ordering_fields = ['codigo_actividad', 'denominacion']


class ActividadNormativaViewSet(viewsets.ModelViewSet):
    queryset = ActividadNormativa.objects.all()
    serializer_class = ActividadNormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['actividad', 'normativa', 'obligatorio']
    ordering_fields = ['actividad', 'normativa']


class TareaPOAUViewSet(
    ScopeTareaPOAUMixin, GestionHabilitadaFilterMixin, RevisionPOAUMixin,
    viewsets.ModelViewSet,
):
    campo_gestion = 'actividad__operacion__accion_poa__gestion'

    queryset = TareaPOAU.objects.all()
    serializer_class = TareaPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    capacidad_escritura = CAPACIDAD_ESCRITURA_POAU
    filterset_fields = ['actividad', 'estado']
    search_fields = ['codigo_tarea', 'denominacion']
    ordering_fields = ['codigo_tarea', 'denominacion']


class TareaNormativaViewSet(viewsets.ModelViewSet):
    queryset = TareaNormativa.objects.all()
    serializer_class = TareaNormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['tarea', 'normativa', 'obligatorio']
    ordering_fields = ['tarea', 'normativa']


class SeguimientoPresupuestoViewSet(
    CandadoSisPoaMixin, EstadoActionsMixin, viewsets.ModelViewSet,
):
    queryset = SeguimientoPresupuesto.objects.all()
    serializer_class = SeguimientoPresupuestoSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['estado', 'accion_poa', 'operacion', 'actividad']
    search_fields = ['id_cadena', 'programa']
    ordering_fields = ['gestion', 'id_cadena']


class AsignacionObjetoGastoViewSet(
    ScopeAsignacionObjetoGastoMixin, CandadoSisPoaMixin, EstadoActionsMixin,
    viewsets.ModelViewSet,
):
    queryset = AsignacionObjetoGasto.objects.all()
    serializer_class = AsignacionObjetoGastoSerializer
    permission_classes = [ArticulacionPermisos]
    capacidad_escritura = CAPACIDAD_ESCRITURA_POAU
    filterset_fields = ['estado', 'accion_poa', 'operacion', 'actividad', 'tipo_gasto']
    search_fields = ['codigo_asignacion', 'descripcion_objeto']
    ordering_fields = ['codigo_asignacion', 'gestion']

    def perform_update(self, serializer):
        """Deja constancia de quién corrigió el requerimiento.

        Ni el alta por `bulk` ni la de `perform_create` estampaban autor, así
        que no había forma de saber quién cargó cada fila. En la edición sí se
        registra desde el principio.
        """
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Borra el requerimiento dejando un evento de auditoría.

        El borrado es físico y no hay historial: sin este evento, una fila
        eliminada no deja absolutamente ningún rastro de haber existido. Ya
        ocurrió —una importación de POAU se llevó 62 requerimientos por
        cascada el 2026-09-04, irrecuperables—, así que el monto, la partida y
        el código se guardan ANTES de borrar: después ya no hay de dónde
        leerlos.
        """
        from apps.auditoria.models import EventoAuditoria

        instancia = self.get_object()
        unidad = (
            instancia.accion_poa.unidad_responsable.codigo
            if instancia.accion_poa and instancia.accion_poa.unidad_responsable
            else ''
        )
        # El evento se arma con `datos_previos`, que es el campo pensado para
        # esto, en vez de pasar por `registrar_auditoria`: esa función solo
        # guarda texto y acá hace falta la fila entera, estructurada.
        # `anular` y no `eliminar`: es la acción del catálogo, y la misma que
        # usa el borrado del árbol POAU.
        previos = {
            'codigo_asignacion': instancia.codigo_asignacion,
            'gestion': instancia.gestion,
            'unidad': unidad,
            'categoria_programatica': instancia.categoria_programatica,
            'cod_objeto_gasto': instancia.cod_objeto_gasto,
            'descripcion_objeto': instancia.descripcion_objeto,
            'fuente_financiamiento': instancia.fuente_financiamiento,
            'organismo_financiador': instancia.organismo_financiador,
            'monto_programado': str(instancia.monto_programado or ''),
            'programacion_mensual': instancia.programacion_mensual,
        }
        identidad = instancia.pk
        codigo = instancia.codigo_asignacion

        respuesta = super().destroy(request, *args, **kwargs)
        try:
            EventoAuditoria.objects.create(
                usuario=request.user,
                accion=EventoAuditoria.Accion.ANULAR,
                entidad='AsignacionObjetoGasto',
                entidad_id=str(identidad),
                resumen=(
                    f'Se eliminó el requerimiento {codigo}'
                    f'{" de " + unidad if unidad else ""}.'
                ),
                datos_previos=previos,
            )
        except Exception:
            # La auditoría no puede tumbar un borrado ya confirmado: si fallara,
            # el 204 sería mentira y la fila estaría igualmente ida.
            pass
        return respuesta

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request):
        """Crea varios requerimientos en una sola transacción: todo o nada.

        El wizard de recursos mandaba un POST por requerimiento
        (`concatMap`, uno detrás de otro). Si el N-ésimo fallaba, los
        anteriores ya habían quedado guardados en la base, y reintentar
        volvía a mandar la tanda completa: con `codigo_asignacion`
        autogenerado, los ya guardados no chocan más contra sí mismos y se
        duplicaban en silencio. Acá se valida y guarda todo dentro de una
        única `transaction.atomic()`; cualquier error revierte la tanda
        entera y no queda nada a medio guardar.
        """
        items = request.data
        if not isinstance(items, list) or not items:
            raise serializers.ValidationError({
                'detail': ['Debe enviar una lista no vacía de requerimientos.'],
            })
        gestiones = {
            item.get('gestion') for item in items if isinstance(item, dict)
        }
        if len(gestiones) != 1:
            raise serializers.ValidationError({
                'detail': ['Todos los requerimientos deben pertenecer a la misma gestión.'],
            })
        try:
            candado.validar_gestion(next(iter(gestiones)))
        except candado.FueraDeGestionHabilitada as error:
            raise GestionNoHabilitada(error) from error

        creados = []
        with transaction.atomic():
            for item in items:
                serializer = self.get_serializer(data=item)
                serializer.is_valid(raise_exception=True)
                # `bulk` no pasa por `perform_create`, así que el alcance
                # territorial hay que aplicarlo acá: sin esto, tener la
                # capacidad alcanzaba para programar recursos sobre la acción
                # de cualquier unidad, que es justo lo que el alcance impide en
                # el alta de a uno.
                self._autorizar_unidad(self._unidad_objetivo(serializer))
                serializer.save()
                creados.append(serializer.data)
        return Response(creados, status=status.HTTP_201_CREATED)


class RevisionMatrizMixin:
    """Autoridad única sobre las actions del circuito de revisión.

    `ArticulacionPermisos` solo deja escribir a quien FORMULA. La jefatura que
    aprueba y observa (ROLES_APROBADORES) no formula, así que aplicarle esa
    clase la dejaba sin poder cerrar el circuito. Aquí la decisión queda
    enteramente en `permisos_revision_matriz`, que es quien conoce autor,
    jefatura y estado del registro; cada action deniega con su propio mensaje.
    """

    ACCIONES_DE_REVISION = ('validar', 'aprobar', 'observar')

    def get_permissions(self):
        if getattr(self, 'action', None) in self.ACCIONES_DE_REVISION:
            return [IsAuthenticated()]
        return super().get_permissions()


class BorradorMatrizPADViewSet(RevisionMatrizMixin, viewsets.ModelViewSet):
    """CRUD del borrador de Matrices PAD (guardado incremental por paso).

    Contrato del PATCH parcial (por sección del wizard):
      ``PATCH /borradores-matriz-pad/{id}/`` con
      ``{"seccion": "resultados", "valores": [...lista completa...]}``
    actualiza únicamente esa sección en ``datos``. Para la colección
    ``resultados`` el PATCH envía la LISTA COMPLETA (el wizard mantiene la
    colección en memoria y la reemplaza al agregar/editar resultado o
    producto). También se acepta ``{"datos": {...}}`` para reemplazar el
    JSON completo de secciones.

    Estructura de la sección ``resultados`` (colección):
      resultados: [
        {denominacion, territorializacion, responsable,
         cuenta_con_financiamiento,
         indicador: {indicador, formula, unidad_medida, linea_base,
                     meta_2030},
         programacion_fisica: {'2026': ...},
         presupuesto_total, presupuesto_anual: {'2026': ...},
         productos: [ {mismos campos que el resultado}, ... ]},
        ...
      ]
    Las secciones legacy p6..p10 (cadena única) siguen siendo aceptadas en
    el PATCH y se transforman a la colección en lectura (retrocompat).

    Actions:
      - ``POST /borradores-matriz-pad/{id}/materializar/``
        Materializa el borrador: por cada resultado de la colección crea
        ResultadoPAD → ProductoPAD → IndicadorCadena en transacción
        atómica; setea ``id_resultado_pad`` y estado=COMPLETO.
      - ``GET /borradores-matriz-pad/{id}/matriz_a/``
        Matriz A (27 columnas) armada server-side. Fuente: modelos
        materializados si ``id_resultado_pad`` existe, si no borrador.datos.
      - ``GET /borradores-matriz-pad/{id}/matriz_b/``
        Matriz B (34 columnas) con el mismo contrato.
    """

    queryset = BorradorMatrizPAD.objects.select_related(
        'id_resultado_pad',
    ).all()
    serializer_class = BorradorMatrizPADSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'estado_revision']
    ordering_fields = ['gestion', 'estado', 'created_at']

    # ------------------------------------------------------------------
    # Circuito de revisión: validar (técnico) → aprobar/observar (jefatura)
    # ------------------------------------------------------------------

    def _denegar(self, mensaje):
        return Response({'error': mensaje}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        """El técnico da por revisado el registro."""
        borrador = self.get_object()
        permisos = permisos_revision_matriz(borrador, request.user)
        if not permisos['validar']:
            return self._denegar(
                'Solo el técnico que creó el registro puede validarlo, '
                'y un registro aprobado ya no admite cambios.'
            )
        borrador.estado_revision = BorradorMatrizPAD.REVISION_VALIDADO
        borrador.validado_por = request.user
        borrador.validado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'validado_por', 'validado_en', 'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='validar',
            entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
            detalle='Matriz PAD validada por el técnico',
        )
        return Response(self.get_serializer(borrador).data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """La jefatura aprueba: el registro queda inmutable."""
        borrador = self.get_object()
        permisos = permisos_revision_matriz(borrador, request.user)
        if not permisos['aprobar']:
            return self._denegar(
                'La aprobación corresponde a la jefatura de SIS-PE y requiere '
                'que el registro esté validado por el técnico.'
            )
        borrador.estado_revision = BorradorMatrizPAD.REVISION_APROBADO
        borrador.aprobado_por = request.user
        borrador.aprobado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'aprobado_por', 'aprobado_en', 'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='aprobar',
            entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
            detalle='Matriz PAD aprobada; registro inmutable',
        )
        return Response(self.get_serializer(borrador).data)

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        """La jefatura devuelve el registro con una observación escrita."""
        borrador = self.get_object()
        permisos = permisos_revision_matriz(borrador, request.user)
        if not permisos['observar']:
            return self._denegar(
                'Solo la jefatura de SIS-PE puede observar, y un registro '
                'aprobado ya no admite observaciones.'
            )
        texto = (request.data.get('observacion') or '').strip()
        if not texto:
            return Response(
                {'error': 'Detalle la observación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        borrador.estado_revision = BorradorMatrizPAD.REVISION_OBSERVADO
        borrador.observacion = texto
        borrador.observado_por = request.user
        borrador.observado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'observacion', 'observado_por', 'observado_en',
            'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='observar',
            entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
            detalle=f'Matriz PAD observada: {texto[:180]}',
        )
        return Response(self.get_serializer(borrador).data)

    def update(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['editar']:
            return self._denegar(
                'El registro está aprobado: queda permanentemente registrado '
                'y no admite modificaciones.'
            )
        return super().update(request, *args, **kwargs)

    def _guardar_seccion(self, request, borrador):
        """PATCH {"seccion": ..., "valores": ...} actualiza solo esa sección.

        Devuelve ``None`` cuando el PATCH no trae ``seccion``, para que el
        flujo siga con el update parcial estándar (``{"datos": {...}}``).
        """
        seccion = request.data.get('seccion')
        if not seccion:
            return None
        valores = request.data.get('valores')
        if valores is None:
            return Response(
                {'error': 'Se requiere "valores" junto a "seccion".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if seccion not in BorradorMatrizPAD.SECCIONES:
            return Response(
                {'error': f'Sección inválida: {seccion}. '
                          f'Válidas: {", ".join(BorradorMatrizPAD.SECCIONES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if seccion == 'resultados':
            error = validar_estructura_resultados(valores)
            if error:
                return Response(
                    {'error': error}, status=status.HTTP_400_BAD_REQUEST,
                )
        datos = dict(borrador.datos or {})
        datos[seccion] = valores
        borrador.datos = datos
        borrador.save(update_fields=['datos', 'updated_at'])
        return Response(self.get_serializer(borrador).data)

    def partial_update(self, request, *args, **kwargs):
        """PATCH por sección (guardado incremental) o por datos completo."""
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['editar']:
            return self._denegar(
                'El registro está aprobado: queda permanentemente registrado '
                'y no admite modificaciones.'
            )
        respuesta = self._guardar_seccion(request, borrador)
        if respuesta is not None:
            return respuesta
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['borrar']:
            return self._denegar(
                'Solo el técnico que creó el registro o la jefatura de SIS-PE '
                'pueden eliminarlo, y únicamente mientras no esté aprobado.'
            )
        registrar_auditoria(
            usuario=request.user, accion='eliminar',
            entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
            detalle='Matriz PAD eliminada por su autor',
        )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def materializar(self, request, pk=None):
        """Crea ResultadoPAD → ProductoPAD → IndicadorCadena (atómico).

        La materialización procesa TODA la colección ``resultados``: crea un
        ResultadoPAD por cada resultado y un ProductoPAD por cada producto
        (cada uno con su IndicadorCadena). Devuelve el resumen con conteos.
        """
        borrador = self.get_object()
        try:
            with transaction.atomic():
                creados = materializar_borrador_matriz(
                    borrador, usuario=request.user,
                )
                primer_resultado = creados['resultados'][0]
                borrador.id_resultado_pad = primer_resultado
                borrador.estado = BorradorMatrizPAD.ESTADO_COMPLETO
                borrador.save(
                    update_fields=['id_resultado_pad', 'estado', 'updated_at'],
                )
        except ValueError as exc:
            return Response(
                {'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            registrar_auditoria(
                usuario=request.user, accion='materializar_error',
                entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
                detalle=f'Error al materializar: {str(exc)[:200]}',
            )
            return Response(
                {'error': f'No se pudo materializar el borrador: {exc}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registrar_auditoria(
            usuario=request.user, accion='materializar',
            entidad='BorradorMatrizPAD', entidad_id=str(borrador.id),
            detalle=(
                f'Materializado: {len(creados["resultados"])} resultado(s), '
                f'{len(creados["productos"])} producto(s)'
            ),
        )
        return Response({
            'estado': borrador.estado,
            'id_resultado_pad': str(primer_resultado.id),
            'total_resultados': len(creados['resultados']),
            'total_productos': len(creados['productos']),
            'total_indicadores': len(creados['indicadores']),
            'codigos': {
                'resultados': [r.codigo_resultado for r in creados['resultados']],
                'productos': [p.codigo_producto for p in creados['productos']],
            },
            'ids': {
                'resultados': [str(r.id) for r in creados['resultados']],
                'productos': [str(p.id) for p in creados['productos']],
                'indicadores': [str(i.id) for i in creados['indicadores']],
            },
        })

    @action(detail=True, methods=['get'])
    def matriz_a(self, request, pk=None):
        """Matriz A (27 columnas) — modelos si materializado, borrador si no."""
        borrador = self.get_object()
        return Response(construir_matriz_a(borrador))

    @action(detail=True, methods=['get'])
    def matriz_b(self, request, pk=None):
        """Matriz B (34 columnas) — modelos si materializado, borrador si no."""
        borrador = self.get_object()
        return Response(construir_matriz_b(borrador))


class BorradorMatrizPEIViewSet(RevisionMatrizMixin, viewsets.ModelViewSet):
    """CRUD del borrador de Matriz PEI (guardado incremental por sección).

    Espejo de :class:`BorradorMatrizPADViewSet`: PATCH parcial por sección,
    materialización atómica y circuito de revisión validar → aprobar/observar.
    """

    queryset = BorradorMatrizPEI.objects.select_related('id_resultado_pei')
    serializer_class = BorradorMatrizPEISerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'estado_revision']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def _denegar(self, mensaje):
        return Response({'error': mensaje}, status=status.HTTP_403_FORBIDDEN)

    def _guardar_seccion(self, request, borrador):
        """PATCH {"seccion": ..., "valores": ...} actualiza solo esa sección."""
        seccion = request.data.get('seccion')
        if seccion not in BorradorMatrizPEI.SECCIONES:
            return None
        datos = dict(borrador.datos or {})
        datos[seccion] = request.data.get('valores')
        borrador.datos = datos
        borrador.updated_by = request.user
        borrador.save(update_fields=['datos', 'updated_by', 'updated_at'])
        return Response(self.get_serializer(borrador).data)

    def partial_update(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['editar']:
            return self._denegar(
                'El registro está aprobado: queda permanentemente registrado '
                'y no admite modificaciones.'
            )
        respuesta = self._guardar_seccion(request, borrador)
        if respuesta is not None:
            return respuesta
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['editar']:
            return self._denegar(
                'El registro está aprobado: queda permanentemente registrado '
                'y no admite modificaciones.'
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['borrar']:
            return self._denegar(
                'Solo el técnico que creó el registro o la jefatura de SIS-PE '
                'pueden eliminarlo, y únicamente mientras no esté aprobado.'
            )
        registrar_auditoria(
            usuario=request.user, accion='eliminar',
            entidad='BorradorMatrizPEI', entidad_id=str(borrador.id),
            detalle='Matriz PEI eliminada',
        )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def matriz(self, request, pk=None):
        """Filas de la matriz PEI (46 columnas) de este borrador."""
        return Response(construir_filas_pei(self.get_object()))

    @action(detail=True, methods=['post'])
    def materializar(self, request, pk=None):
        borrador = self.get_object()
        try:
            with transaction.atomic():
                creados = materializar_borrador_pei(borrador, usuario=request.user)
                borrador.id_resultado_pei = creados['resultados'][0]
                borrador.estado = BorradorMatrizPEI.ESTADO_COMPLETO
                borrador.save(update_fields=[
                    'id_resultado_pei', 'estado', 'updated_at',
                ])
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'resultados': len(creados['resultados']),
            'productos': len(creados['productos']),
            'indicadores': len(creados['indicadores']),
        })

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['validar']:
            return self._denegar(
                'Solo el técnico que creó el registro puede validarlo, '
                'y un registro aprobado ya no admite cambios.'
            )
        borrador.estado_revision = BorradorMatrizPEI.REVISION_VALIDADO
        borrador.validado_por = request.user
        borrador.validado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'validado_por', 'validado_en', 'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='validar',
            entidad='BorradorMatrizPEI', entidad_id=str(borrador.id),
            detalle='Matriz PEI validada por el técnico',
        )
        return Response(self.get_serializer(borrador).data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['aprobar']:
            return self._denegar(
                'La aprobación corresponde a la jefatura de SIS-PE y requiere '
                'que el registro esté validado por el técnico.'
            )
        borrador.estado_revision = BorradorMatrizPEI.REVISION_APROBADO
        borrador.aprobado_por = request.user
        borrador.aprobado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'aprobado_por', 'aprobado_en', 'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='aprobar',
            entidad='BorradorMatrizPEI', entidad_id=str(borrador.id),
            detalle='Matriz PEI aprobada; registro inmutable',
        )
        return Response(self.get_serializer(borrador).data)

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['observar']:
            return self._denegar(
                'Solo la jefatura de SIS-PE puede observar, y un registro '
                'aprobado ya no admite observaciones.'
            )
        texto = (request.data.get('observacion') or '').strip()
        if not texto:
            return Response(
                {'error': 'Detalle la observación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        borrador.estado_revision = BorradorMatrizPEI.REVISION_OBSERVADO
        borrador.observacion = texto
        borrador.observado_por = request.user
        borrador.observado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'observacion', 'observado_por', 'observado_en',
            'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='observar',
            entidad='BorradorMatrizPEI', entidad_id=str(borrador.id),
            detalle=f'Matriz PEI observada: {texto[:180]}',
        )
        return Response(self.get_serializer(borrador).data)


class BorradorMatrizPOAViewSet(
    CandadoSisPoaMixin, RevisionMatrizMixin, viewsets.ModelViewSet,
):
    """CRUD del borrador de Matriz POA (guardado incremental por sección).

    Espejo de :class:`BorradorMatrizPEIViewSet`: PATCH parcial por sección,
    materialización atómica de la cadena operativa y circuito de revisión
    validar → aprobar/observar.
    """

    queryset = BorradorMatrizPOA.objects.select_related('id_accion_poa')
    serializer_class = BorradorMatrizPOASerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['estado', 'estado_revision']

    def perform_create(self, serializer):
        # La gestión la estampa el candado, no el cliente ni el `default=2026`
        # del modelo: un borrador que naciera en 2026 quedaría en una gestión
        # cerrada, invisible para el filtro de lectura y sin decir por qué.
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
            gestion=candado.exigir_gestion_habilitada().anio,
        )

    def _denegar(self, mensaje):
        return Response({'error': mensaje}, status=status.HTTP_403_FORBIDDEN)

    def _guardar_seccion(self, request, borrador):
        """PATCH {"seccion": ..., "valores": ...} actualiza solo esa sección.

        Devuelve ``None`` cuando el PATCH no trae ``seccion``, para que siga
        el update parcial estándar (``{"datos": {...}}``).
        """
        seccion = request.data.get('seccion')
        if not seccion:
            return None
        if seccion not in BorradorMatrizPOA.SECCIONES:
            return Response(
                {'error': f'Sección inválida: {seccion}. '
                          f'Válidas: {", ".join(BorradorMatrizPOA.SECCIONES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if 'valores' not in request.data:
            return Response(
                {'error': 'Se requiere "valores" junto a "seccion".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        datos = dict(borrador.datos or {})
        datos[seccion] = request.data.get('valores')
        borrador.datos = datos
        borrador.updated_by = request.user
        borrador.save(update_fields=['datos', 'updated_by', 'updated_at'])
        return Response(self.get_serializer(borrador).data)

    def partial_update(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['editar']:
            return self._denegar(
                'El registro está aprobado: queda permanentemente registrado '
                'y no admite modificaciones.'
            )
        respuesta = self._guardar_seccion(request, borrador)
        if respuesta is not None:
            return respuesta
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['editar']:
            return self._denegar(
                'El registro está aprobado: queda permanentemente registrado '
                'y no admite modificaciones.'
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['borrar']:
            return self._denegar(
                'Solo el técnico que creó el registro o la jefatura de SIS-POA '
                'pueden eliminarlo, y únicamente mientras no esté aprobado.'
            )
        registrar_auditoria(
            usuario=request.user, accion='eliminar',
            entidad='BorradorMatrizPOA', entidad_id=str(borrador.id),
            detalle='Matriz POA eliminada',
        )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def matriz(self, request, pk=None):
        """Filas de la matriz POA (15 columnas) de este borrador.

        Cada fila lleva también las claves de ``m2_pei_poa``: la vista
        "Articulación PEI → POA" del listado es otra proyección de estas
        mismas filas, no una consulta aparte.
        """
        return Response(construir_filas_poa(self.get_object()))

    @action(detail=True, methods=['post'])
    def materializar(self, request, pk=None):
        borrador = self.get_object()
        try:
            with transaction.atomic():
                creados = materializar_borrador_poa(borrador, usuario=request.user)
                borrador.id_accion_poa = creados['acciones'][0]
                borrador.estado = BorradorMatrizPOA.ESTADO_COMPLETO
                borrador.save(update_fields=[
                    'id_accion_poa', 'estado', 'datos', 'updated_at',
                ])
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        registrar_auditoria(
            usuario=request.user, accion='materializar',
            entidad='BorradorMatrizPOA', entidad_id=str(borrador.id),
            detalle=(
                f'Materializado: {len(creados["acciones"])} acción(es), '
                f'{len(creados["operaciones"])} operación(es), '
                f'{len(creados["actividades"])} actividad(es), '
                f'{len(creados["tareas"])} tarea(s)'
            ),
        )
        return Response({
            'estado': borrador.estado,
            'id_accion_poa': str(borrador.id_accion_poa_id),
            'acciones': len(creados['acciones']),
            'operaciones': len(creados['operaciones']),
            'actividades': len(creados['actividades']),
            'tareas': len(creados['tareas']),
            'codigos': {
                'acciones': [a.codigo_accion for a in creados['acciones']],
            },
        })

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['validar']:
            return self._denegar(
                'Solo el técnico que creó el registro puede validarlo, '
                'y un registro aprobado ya no admite cambios.'
            )
        borrador.estado_revision = BorradorMatrizPOA.REVISION_VALIDADO
        borrador.validado_por = request.user
        borrador.validado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'validado_por', 'validado_en', 'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='validar',
            entidad='BorradorMatrizPOA', entidad_id=str(borrador.id),
            detalle='Matriz POA validada por el técnico',
        )
        return Response(self.get_serializer(borrador).data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['aprobar']:
            return self._denegar(
                'La aprobación corresponde a la jefatura de SIS-POA y requiere '
                'que el registro esté validado por el técnico.'
            )
        borrador.estado_revision = BorradorMatrizPOA.REVISION_APROBADO
        borrador.aprobado_por = request.user
        borrador.aprobado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'aprobado_por', 'aprobado_en', 'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='aprobar',
            entidad='BorradorMatrizPOA', entidad_id=str(borrador.id),
            detalle='Matriz POA aprobada; registro inmutable',
        )
        return Response(self.get_serializer(borrador).data)

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        borrador = self.get_object()
        if not permisos_revision_matriz(borrador, request.user)['observar']:
            return self._denegar(
                'Solo la jefatura de SIS-POA puede observar, y un registro '
                'aprobado ya no admite observaciones.'
            )
        texto = (request.data.get('observacion') or '').strip()
        if not texto:
            return Response(
                {'error': 'Detalle la observación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        borrador.estado_revision = BorradorMatrizPOA.REVISION_OBSERVADO
        borrador.observacion = texto
        borrador.observado_por = request.user
        borrador.observado_en = timezone.now()
        borrador.save(update_fields=[
            'estado_revision', 'observacion', 'observado_por', 'observado_en',
            'updated_at',
        ])
        registrar_auditoria(
            usuario=request.user, accion='observar',
            entidad='BorradorMatrizPOA', entidad_id=str(borrador.id),
            detalle=f'Matriz POA observada: {texto[:180]}',
        )
        return Response(self.get_serializer(borrador).data)
