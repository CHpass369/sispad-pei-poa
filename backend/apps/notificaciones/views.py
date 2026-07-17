from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TipoNotificacion, Notificacion, PreferenciaNotificacion
from .serializers import (
    TipoNotificacionSerializer,
    NotificacionSerializer,
    PreferenciaNotificacionSerializer,
    ResumenNotificacionesSerializer,
)


class TipoNotificacionViewSet(viewsets.ModelViewSet):
    queryset = TipoNotificacion.objects.all()
    serializer_class = TipoNotificacionSerializer
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering_fields = ['codigo', 'nombre', 'created_at']
    filterset_fields = ['is_active']


class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    search_fields = ['titulo', 'mensaje']
    ordering_fields = ['created_at', 'priority', 'is_read']
    filterset_fields = ['user', 'tipo', 'priority', 'is_read', 'gestion', 'entity_type']

    def get_queryset(self):
        qs = Notificacion.objects.select_related('tipo')
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(user=user)
        return qs

    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        qs = self.get_queryset().filter(is_read=False)
        user_filter = request.query_params.get('user')
        if user_filter:
            qs = qs.filter(user_id=user_filter)
        count = qs.count()
        serializer = self.get_serializer(qs[:50], many=True)
        return Response({
            'count': count,
            'notificaciones': serializer.data,
        })

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.marcar_leida()
        return Response(NotificacionSerializer(notificacion).data)

    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        qs = self.get_queryset().filter(is_read=False)
        user_filter = request.data.get('user')
        if user_filter:
            qs = qs.filter(user_id=user_filter)
        count = qs.count()
        from django.utils import timezone
        qs.update(is_read=True, read_at=timezone.now())
        return Response({
            'marcadas': count,
            'mensaje': f'{count} notificación(es) marcada(s) como leída(s)',
        })

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        qs = self.get_queryset().filter(is_read=False)
        user_filter = request.query_params.get('user')
        if user_filter:
            qs = qs.filter(user_id=user_filter)

        conteo = qs.aggregate(
            total_no_leidas=Count('id'),
            alta=Count('id', filter=Q(priority='alta')),
            media=Count('id', filter=Q(priority='media')),
            baja=Count('id', filter=Q(priority='baja')),
        )

        serializer = ResumenNotificacionesSerializer(data=conteo)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class PreferenciaNotificacionViewSet(viewsets.ModelViewSet):
    queryset = PreferenciaNotificacion.objects.all()
    serializer_class = PreferenciaNotificacionSerializer
    filterset_fields = ['user', 'receive_internal', 'receive_email', 'frequency']
