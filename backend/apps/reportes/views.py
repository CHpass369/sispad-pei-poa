from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from apps.core.permissions import IsPlanificador
from .models import ReporteGenerado
from .serializers import ReporteGeneradoSerializer
from .services import (
    generar_poa_unidad_xlsx,
    generar_poa_consolidado_xlsx,
    generar_observaciones_csv,
    generar_territorio_geojson,
    generar_acta_aprobacion_pdf,
    generar_auxiliar_pluri_xlsx,
    generar_matriz_pad_pei_xlsx,
    generar_matriz_pei_poa_xlsx,
    generar_matriz_presupuesto_seguimiento_xlsx,
    generar_matriz_objetos_gasto_xlsx,
    generar_matriz_completa_xlsx,
)

XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def _responder_descarga(request, generar, content_type, gestion_requerida=True):
    """Ejecuta un generador de reporte y responde la descarga del archivo."""
    gestion = request.query_params.get('gestion')
    if gestion_requerida and not gestion:
        return Response({'error': 'gestión requerida'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        gest = int(gestion) if gestion else None
        output, filename = generar(gest)
        return HttpResponse(
            output.read(),
            content_type=content_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReporteGeneradoViewSet(viewsets.ModelViewSet):
    queryset = ReporteGenerado.objects.all()
    serializer_class = ReporteGeneradoSerializer
    filterset_fields = ['gestion', 'tipo', 'formato']

    @action(detail=False, methods=['get'])
    def poa_unidad(self, request):
        """GET /api/v1/reportes/poa_unidad/?gestion=2026&unidad_id=xxx"""
        def _generar(gest):
            return generar_poa_unidad_xlsx(
                gest, request.query_params.get('unidad_id')
            )
        return _responder_descarga(request, _generar, XLSX_CONTENT_TYPE)

    @action(detail=False, methods=['get'])
    def consolidado(self, request):
        """GET /api/v1/reportes/consolidado/?gestion=2026"""
        return _responder_descarga(
            request, generar_poa_consolidado_xlsx, XLSX_CONTENT_TYPE,
        )

    @action(detail=False, methods=['get'])
    def observaciones(self, request):
        """GET /api/v1/reportes/observaciones/?gestion=2026"""
        return _responder_descarga(
            request, generar_observaciones_csv, 'text/csv; charset=utf-8-sig',
        )

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
        return _responder_descarga(request, generar_acta_aprobacion_pdf, 'application/pdf')

    @action(detail=False, methods=['get'])
    def auxiliar_pluri(self, request):
        """GET /api/v1/reportes/auxiliar_pluri/?gestion=2026
        Descarga XLSX del Auxiliar Pluri (presupuesto plurianual por objeto de gasto y FF/OF).
        """
        return _responder_descarga(request, generar_auxiliar_pluri_xlsx, XLSX_CONTENT_TYPE)

    @action(detail=False, methods=['get'])
    def articulacion_matriz_pad_pei(self, request):
        """GET /api/v1/reportes/articulacion_matriz_pad_pei/?gestion=2026
        Descarga XLSX de la Matriz 1 — Articulación PAD → PEI.
        """
        return _responder_descarga(
            request, generar_matriz_pad_pei_xlsx, XLSX_CONTENT_TYPE,
            gestion_requerida=False,
        )

    @action(detail=False, methods=['get'])
    def articulacion_matriz_pei_poa(self, request):
        """GET /api/v1/reportes/articulacion_matriz_pei_poa/?gestion=2026
        Descarga XLSX de la Matriz 2 — Articulación PEI → POA.
        """
        return _responder_descarga(
            request, generar_matriz_pei_poa_xlsx, XLSX_CONTENT_TYPE,
            gestion_requerida=False,
        )

    @action(detail=False, methods=['get'])
    def articulacion_presupuesto_seguimiento(self, request):
        """Descarga XLSX de la Matriz 4 — Presupuesto y Seguimiento."""
        return _responder_descarga(
            request, generar_matriz_presupuesto_seguimiento_xlsx, XLSX_CONTENT_TYPE,
            gestion_requerida=False,
        )

    @action(detail=False, methods=['get'])
    def articulacion_objetos_gasto(self, request):
        """GET /api/v1/reportes/articulacion_objetos_gasto/?gestion=2026
        Descarga XLSX de la Matriz 5 — Objetos de Gasto.
        """
        return _responder_descarga(
            request, generar_matriz_objetos_gasto_xlsx, XLSX_CONTENT_TYPE,
            gestion_requerida=False,
        )

    @action(detail=False, methods=['get'], permission_classes=[IsPlanificador])
    def matriz_completa_xlsx(self, request):
        """GET /api/v1/reportes/matriz_completa_xlsx/?gestion=2026
        Descarga XLSX de la Matriz de Articulación Completa (PGDESA→PDESA→PAD→PEI→POA).
        """
        return _responder_descarga(
            request, generar_matriz_completa_xlsx, XLSX_CONTENT_TYPE,
            gestion_requerida=False,
        )
