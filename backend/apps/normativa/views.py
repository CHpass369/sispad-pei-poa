from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import VersionNormativa, ReglaPresupuestariaLegal
from .serializers import VersionNormativaSerializer, ReglaPresupuestariaLegalSerializer
from .services import evaluar_reglas_presupuestarias


class VersionNormativaViewSet(viewsets.ModelViewSet):
    queryset = VersionNormativa.objects.all()
    serializer_class = VersionNormativaSerializer
    filterset_fields = ['gestion', 'tipo', 'activo']
    search_fields = ['titulo', 'numero']

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def cargar(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'archivo requerido'}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.dict()
        data.pop('archivo', None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReglaPresupuestariaLegalViewSet(viewsets.ModelViewSet):
    queryset = ReglaPresupuestariaLegal.objects.all()
    serializer_class = ReglaPresupuestariaLegalSerializer
    filterset_fields = ['tipo', 'severidad', 'activo']
    search_fields = ['codigo', 'nombre', 'descripcion']

    @action(detail=False, methods=['post'])
    def evaluar(self, request):
        """Evalúa todas las reglas activas para una gestión contra datos mock"""
        gestion = request.data.get('gestion')
        data = request.data.get('data', {})
        try:
            resultados = evaluar_reglas_presupuestarias(int(gestion), data)
            return Response(resultados)
        except (ValueError, TypeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
