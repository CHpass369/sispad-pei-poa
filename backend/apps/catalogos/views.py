from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import (
    ClasificadorInstitucional, RubroRecurso, ObjetoGasto,
    FuenteFinanciamiento, OrganismoFinanciador, EntidadTransferencia,
    FinalidadFuncion, UnidadMedida, TipoOperacion, TipoProducto,
    TipoProyecto, TipoFinanciamiento, VersionCatalogo
)
from .serializers import (
    ClasificadorInstitucionalSerializer, RubroRecursoSerializer,
    ObjetoGastoSerializer, FuenteFinanciamientoSerializer,
    OrganismoFinanciadorSerializer, EntidadTransferenciaSerializer,
    FinalidadFuncionSerializer, UnidadMedidaSerializer,
    TipoOperacionSerializer, TipoProductoSerializer,
    TipoProyectoSerializer, TipoFinanciamientoSerializer,
    VersionCatalogoSerializer
)
from .services import importar_catalogo_desde_xlsx, importar_catalogo_desde_csv, MODEL_MAP


class CatalogoImportMixin:
    """Mixin para viewsets de catálogos que habilita importación XLSX/CSV."""

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'archivo': {'type': 'string', 'format': 'binary'},
                    'gestion': {'type': 'integer'},
                }
            }
        }
    )
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def importar(self, request):
        archivo = request.FILES.get('archivo')
        gestion = request.data.get('gestion')
        if not archivo or not gestion:
            return Response(
                {'error': 'archivo y gestión son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            gestion = int(gestion)
        except (ValueError, TypeError):
            return Response({'error': 'gestión debe ser un número'}, status=status.HTTP_400_BAD_REQUEST)

        tipo = self._get_tipo_catalogo()
        ext = archivo.name.split('.')[-1].lower() if '.' in archivo.name else ''

        if ext == 'xlsx':
            result = importar_catalogo_desde_xlsx(archivo, tipo, gestion)
        elif ext == 'csv':
            result = importar_catalogo_desde_csv(archivo, tipo, gestion)
        else:
            return Response(
                {'error': 'Formato no soportado. Use XLSX o CSV.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result.to_dict(), status=status.HTTP_200_OK)


class ClasificadorInstitucionalViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = ClasificadorInstitucional.objects.all()
    serializer_class = ClasificadorInstitucionalSerializer
    filterset_fields = ['gestion', 'activo']
    search_fields = ['codigo', 'denominacion']

    def _get_tipo_catalogo(self):
        return 'clasificador_institucional'


class RubroRecursoViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = RubroRecurso.objects.all()
    serializer_class = RubroRecursoSerializer
    filterset_fields = ['gestion', 'activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'rubro_recurso'


class ObjetoGastoViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = ObjetoGasto.objects.all()
    serializer_class = ObjetoGastoSerializer
    filterset_fields = ['gestion', 'activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'objeto_gasto'


class FuenteFinanciamientoViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = FuenteFinanciamiento.objects.all()
    serializer_class = FuenteFinanciamientoSerializer
    filterset_fields = ['gestion', 'activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'fuente_financiamiento'


class OrganismoFinanciadorViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = OrganismoFinanciador.objects.all()
    serializer_class = OrganismoFinanciadorSerializer
    filterset_fields = ['gestion', 'activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'organismo_financiador'


class EntidadTransferenciaViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = EntidadTransferencia.objects.all()
    serializer_class = EntidadTransferenciaSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'entidad_transferencia'


class FinalidadFuncionViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = FinalidadFuncion.objects.all()
    serializer_class = FinalidadFuncionSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'finalidad_funcion'


class UnidadMedidaViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'unidad_medida'


class TipoOperacionViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = TipoOperacion.objects.all()
    serializer_class = TipoOperacionSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'tipo_operacion'


class TipoProductoViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = TipoProducto.objects.all()
    serializer_class = TipoProductoSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'tipo_producto'


class TipoProyectoViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = TipoProyecto.objects.all()
    serializer_class = TipoProyectoSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'tipo_proyecto'


class TipoFinanciamientoViewSet(CatalogoImportMixin, viewsets.ModelViewSet):
    queryset = TipoFinanciamiento.objects.all()
    serializer_class = TipoFinanciamientoSerializer
    filterset_fields = ['gestion', 'activo']
    def _get_tipo_catalogo(self): return 'tipo_financiamiento'


class VersionCatalogoViewSet(viewsets.ModelViewSet):
    queryset = VersionCatalogo.objects.all()
    serializer_class = VersionCatalogoSerializer
    filterset_fields = ['gestion', 'aplicado']
