from rest_framework import viewsets
from .models import (
    Indicador, MetaProgramada, Operacion, Tarea,
    Producto, MedioVerificacion, Supuesto
)
from .serializers import (
    IndicadorSerializer, MetaProgramadaSerializer, OperacionSerializer,
    TareaSerializer, ProductoSerializer, MedioVerificacionSerializer,
    SupuestoSerializer
)


class IndicadorViewSet(viewsets.ModelViewSet):
    queryset = Indicador.objects.all()
    serializer_class = IndicadorSerializer
    search_fields = ['codigo', 'nombre']
    filterset_fields = ['activo']


class MetaProgramadaViewSet(viewsets.ModelViewSet):
    queryset = MetaProgramada.objects.all()
    serializer_class = MetaProgramadaSerializer
    filterset_fields = ['indicador', 'gestion']


class OperacionViewSet(viewsets.ModelViewSet):
    queryset = Operacion.objects.all()
    serializer_class = OperacionSerializer
    search_fields = ['codigo', 'nombre']
    filterset_fields = ['accion_corto_plazo', 'activo']


class TareaViewSet(viewsets.ModelViewSet):
    queryset = Tarea.objects.all()
    serializer_class = TareaSerializer
    filterset_fields = ['operacion', 'activo']


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filterset_fields = ['accion_corto_plazo', 'activo']


class MedioVerificacionViewSet(viewsets.ModelViewSet):
    queryset = MedioVerificacion.objects.all()
    serializer_class = MedioVerificacionSerializer
    filterset_fields = ['indicador']


class SupuestoViewSet(viewsets.ModelViewSet):
    queryset = Supuesto.objects.all()
    serializer_class = SupuestoSerializer
    filterset_fields = ['accion_corto_plazo']
