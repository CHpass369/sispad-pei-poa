from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import ReporteGenerado
from .serializers import ReporteGeneradoSerializer
from .services import (
    generar_poa_unidad_xlsx,
    generar_poa_consolidado_xlsx,
    generar_proyectos_xlsx,
    generar_observaciones_csv,
    generar_territorio_geojson,
    generar_acta_aprobacion_pdf,
    generar_auxiliar_pluri_xlsx,
    generar_evaluacion_cuadro1_xlsx,
    generar_evaluacion_cuadro2_xlsx,
    generar_evaluacion_cuadro3_xlsx,
)


class ReporteGeneradoViewSet(viewsets.ModelViewSet):
    queryset = ReporteGenerado.objects.all()
    serializer_class = ReporteGeneradoSerializer
    filterset_fields = ['gestion', 'tipo', 'formato']

    @action(detail=False, methods=['get'])
    def poa_unidad(self, request):
        """GET /api/v1/reportes/poa_unidad/?gestion=2026&unidad_id=xxx"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_poa_unidad_xlsx(
                int(gestion), request.query_params.get('unidad_id')
            )
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def consolidado(self, request):
        """GET /api/v1/reportes/consolidado/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_poa_consolidado_xlsx(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def proyectos(self, request):
        """GET /api/v1/reportes/proyectos/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_proyectos_xlsx(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def observaciones(self, request):
        """GET /api/v1/reportes/observaciones/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_observaciones_csv(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='text/csv; charset=utf-8-sig',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def mapa(self, request):
        """GET /api/v1/reportes/mapa/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            geojson = generar_territorio_geojson(int(gestion))
            return Response(geojson)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def acta_aprobacion(self, request):
        """GET /api/v1/reportes/acta_aprobacion/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_acta_aprobacion_pdf(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/pdf',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def auxiliar_pluri(self, request):
        """GET /api/v1/reportes/auxiliar_pluri/?gestion=2026
        Descarga XLSX del Auxiliar Pluri (presupuesto plurianual por objeto de gasto y FF/OF).
        """
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_auxiliar_pluri_xlsx(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def evaluacion_cuadro1(self, request):
        """GET /api/v1/reportes/evaluacion_cuadro1/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_evaluacion_cuadro1_xlsx(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def evaluacion_cuadro2(self, request):
        """GET /api/v1/reportes/evaluacion_cuadro2/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_evaluacion_cuadro2_xlsx(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def evaluacion_cuadro3(self, request):
        """GET /api/v1/reportes/evaluacion_cuadro3/?gestion=2026"""
        gestion = request.query_params.get('gestion')
        if not gestion:
            return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            output, filename = generar_evaluacion_cuadro3_xlsx(int(gestion))
            return HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
