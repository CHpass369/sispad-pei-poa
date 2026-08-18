from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import (
    BorradorMatrizPEI,
    CodigoNivel, AcuerdoInternacional, Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto, BorradorMatrizPAD,
)
from .serializers import (
    BorradorMatrizPEISerializer,
    CodigoNivelSerializer, AcuerdoInternacionalSerializer, NormativaSerializer,
    LineamientoPADSerializer, ResultadoPADSerializer, ProductoPADSerializer,
    ResultadoPEISerializer, ProductoPEISerializer, ArticulacionPADPEISerializer,
    IndicadorCadenaSerializer, AccionPOASerializer, OperacionPOAUSerializer,
    ActividadPOAUSerializer, ActividadNormativaSerializer, TareaPOAUSerializer,
    TareaNormativaSerializer, SeguimientoPresupuestoSerializer,
    AsignacionObjetoGastoSerializer, BorradorMatrizPADSerializer,
    validar_estructura_resultados,
)
from .permissions import ArticulacionPermisos, permisos_revision_matriz
from .services import (
    construir_matriz_a,
    construir_matriz_b,
    materializar_borrador_matriz,
    registrar_auditoria,
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


class AccionPOAViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = AccionPOA.objects.all()
    serializer_class = AccionPOASerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'producto_pei', 'unidad_responsable']
    search_fields = ['codigo_accion', 'denominacion', 'programa']
    ordering_fields = ['codigo_accion', 'gestion', 'denominacion']


class OperacionPOAUViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = OperacionPOAU.objects.all()
    serializer_class = OperacionPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['accion_poa', 'tipo_operacion', 'estado']
    search_fields = ['codigo_operacion', 'denominacion']
    ordering_fields = ['codigo_operacion', 'denominacion']


class ActividadPOAUViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = ActividadPOAU.objects.all()
    serializer_class = ActividadPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['operacion', 'estado']
    search_fields = ['codigo_actividad', 'denominacion']
    ordering_fields = ['codigo_actividad', 'denominacion']


class ActividadNormativaViewSet(viewsets.ModelViewSet):
    queryset = ActividadNormativa.objects.all()
    serializer_class = ActividadNormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['actividad', 'normativa', 'obligatorio']
    ordering_fields = ['actividad', 'normativa']


class TareaPOAUViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = TareaPOAU.objects.all()
    serializer_class = TareaPOAUSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['actividad', 'estado']
    search_fields = ['codigo_tarea', 'denominacion']
    ordering_fields = ['codigo_tarea', 'denominacion']


class TareaNormativaViewSet(viewsets.ModelViewSet):
    queryset = TareaNormativa.objects.all()
    serializer_class = TareaNormativaSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['tarea', 'normativa', 'obligatorio']
    ordering_fields = ['tarea', 'normativa']


class SeguimientoPresupuestoViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = SeguimientoPresupuesto.objects.all()
    serializer_class = SeguimientoPresupuestoSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'accion_poa', 'operacion', 'actividad']
    search_fields = ['id_cadena', 'programa']
    ordering_fields = ['gestion', 'id_cadena']


class AsignacionObjetoGastoViewSet(EstadoActionsMixin, viewsets.ModelViewSet):
    queryset = AsignacionObjetoGasto.objects.all()
    serializer_class = AsignacionObjetoGastoSerializer
    permission_classes = [ArticulacionPermisos]
    filterset_fields = ['gestion', 'estado', 'accion_poa', 'operacion', 'actividad', 'tipo_gasto']
    search_fields = ['codigo_asignacion', 'descripcion_objeto']
    ordering_fields = ['codigo_asignacion', 'gestion']


class BorradorMatrizPADViewSet(viewsets.ModelViewSet):
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


class BorradorMatrizPEIViewSet(viewsets.ModelViewSet):
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
