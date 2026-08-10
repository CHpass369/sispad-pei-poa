"""API V2 del SIS-POA (WP-10 / /api/v2/sis-poa/)."""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import TieneAlgunaCapacidad
from apps.poau.migration_v2 import resumen_presupuesto, validar_techo
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
    Tarea,
)

CAPACIDADES_ESCRITURA = ['sis_poa.formulate', 'sis_poa.poau.edit']


class PoASerializer(serializers.ModelSerializer):
    class Meta:
        model = PoAInstitucional
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _validar(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError
        try:
            return super().create(validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def create(self, validated_data):
        return self._validar(validated_data)

    def update(self, instance, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError
        try:
            return super().update(instance, validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)


class AccionSerializer(serializers.ModelSerializer):
    nodo_pei_codigo = serializers.CharField(
        source='nodo_pei.codigo', read_only=True, default=None,
    )

    class Meta:
        model = AccionCortoPlazo
        fields = [
            'id', 'poa', 'codigo', 'nombre', 'descripcion', 'nodo_pei',
            'nodo_pei_codigo', 'unidad', 'atributos', 'estado',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OperacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actividad
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarea
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProgramacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacionActividad
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


def _permisos_escritura():
    return [TieneAlgunaCapacidad(*CAPACIDADES_ESCRITURA)]


class PoAViewSet(viewsets.ModelViewSet):
    queryset = PoAInstitucional.objects.select_related('version_pei')
    serializer_class = PoASerializer
    filterset_fields = ['gestion', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos_escritura()
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def acciones(self, request, pk=None):
        poa = self.get_object()
        acciones = poa.acciones.select_related('nodo_pei', 'unidad')
        serializer = AccionSerializer(acciones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def resumen_presupuesto(self, request, pk=None):
        return Response(resumen_presupuesto(self.get_object()))

    @action(detail=True, methods=['get'])
    def validar_techo(self, request, pk=None):
        return Response(validar_techo(self.get_object()))


class AccionViewSet(viewsets.ModelViewSet):
    queryset = AccionCortoPlazo.objects.select_related('poa', 'nodo_pei')
    serializer_class = AccionSerializer
    filterset_fields = ['poa', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos_escritura()
        return super().get_permissions()


class OperacionViewSet(viewsets.ModelViewSet):
    queryset = Operacion.objects.select_related('accion', 'unidad')
    serializer_class = OperacionSerializer
    filterset_fields = ['accion', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos_escritura()
        return super().get_permissions()


class ActividadViewSet(viewsets.ModelViewSet):
    queryset = Actividad.objects.select_related('operacion')
    serializer_class = ActividadSerializer
    filterset_fields = ['operacion', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos_escritura()
        return super().get_permissions()


class TareaViewSet(viewsets.ModelViewSet):
    queryset = Tarea.objects.select_related('actividad')
    serializer_class = TareaSerializer
    filterset_fields = ['actividad', 'estado']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos_escritura()
        return super().get_permissions()


class ProgramacionViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionActividad.objects.select_related('actividad')
    serializer_class = ProgramacionSerializer
    filterset_fields = ['actividad', 'anio', 'tipo']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return _permisos_escritura()
        return super().get_permissions()
