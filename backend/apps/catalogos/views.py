from django_filters.rest_framework import DjangoFilterBackend
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


class GestionFilterMixin:
    """?gestion=<anio> filtra por anio (PIP-DB-003; el frontend envia el anio)."""

    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.query_params.get('gestion')
        if gestion:
            qs = qs.filter(gestion__anio=gestion)
        return qs


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


class ClasificadorInstitucionalViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = ClasificadorInstitucional.objects.all()
    serializer_class = ClasificadorInstitucionalSerializer
    filterset_fields = ['activo']
    search_fields = ['codigo', 'denominacion']

    def _get_tipo_catalogo(self):
        return 'clasificador_institucional'


class RubroRecursoViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = RubroRecurso.objects.all()
    serializer_class = RubroRecursoSerializer
    filterset_fields = ['activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'rubro_recurso'


class ObjetoGastoViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = ObjetoGasto.objects.all()
    serializer_class = ObjetoGastoSerializer
    # `nivel` es filtrable porque un desplegable de partidas no puede ofrecer
    # grupos ni subgrupos: son encabezados del clasificador y contra ellos no
    # se imputa gasto.
    filterset_fields = ['activo', 'nivel']
    search_fields = ['codigo', 'denominacion']

    # Los dos niveles contra los que se imputa gasto. `grupo` y `subgrupo` son
    # encabezados del clasificador: sirven para buscar, no para elegir.
    NIVELES_IMPUTABLES = (ObjetoGasto.NIVEL_PARTIDA, ObjetoGasto.NIVEL_DETALLE)

    @staticmethod
    def _pedido_imputable(request):
        return request.query_params.get('imputable') in ('1', 'true', 'True')

    @staticmethod
    def _con_descendientes(universo, ids):
        """Agrega a `ids` todo lo que cuelga de ellos, a cualquier profundidad.

        Sin esto no se puede buscar desde un nivel alto: el texto de un
        subgrupo no aparece en el código ni en la denominación de sus hijos.
        Tecleando `25000` se encontraba **una** fila —el subgrupo mismo— y con
        `?hoja=true` ninguna, porque el subgrupo tiene hijos. Ahora se
        encuentran las nueve partidas que cuelgan de él y sus detalles.
        """
        hijos_de: dict = {}
        for hijo, padre in universo.values_list('id', 'padre_id'):
            hijos_de.setdefault(padre, []).append(hijo)
        alcanzados, pila = set(ids), list(ids)
        while pila:
            for hijo in hijos_de.get(pila.pop(), ()):
                if hijo not in alcanzados:
                    alcanzados.add(hijo)
                    pila.append(hijo)
        return alcanzados

    def filter_queryset(self, queryset):
        """Búsqueda por familia, y `?imputable=true` para lo elegible.

        El orden importa y por eso no alcanza con filtrar en `get_queryset()`:
        primero se busca sobre el catálogo entero —para que un subgrupo pueda
        ser el punto de partida—, después se baja a sus descendientes, y recién
        al final se descartan los niveles que no admiten imputación.

        `?imputable=true` deja `partida` y `detalle`, que son los dos niveles
        contra los que el GAM Sacaba imputa. Se probó antes dejando solo las
        hojas del árbol, y eso sacaba del desplegable a `25200`, que sí se
        usa: una partida con detalles colgados se imputa igual. `grupo` y
        `subgrupo` siguen afuera —son encabezados como «SERVICIOS NO
        PERSONALES»— pero se pueden teclear para llegar a lo que cuelga de
        ellos.
        """
        qs = super().filter_queryset(queryset)
        if self.request.query_params.get('search'):
            ids = self._con_descendientes(queryset, qs.values_list('id', flat=True))
            # Se vuelve a pasar el filterset —y no `super()`— porque `super()`
            # reaplicaría la búsqueda y volvería a dejar afuera justo a los
            # descendientes que se acaban de traer. Sin esto, expandir por el
            # árbol reintroduce filas que `?nivel=` o `?activo=` ya habían
            # descartado.
            qs = DjangoFilterBackend().filter_queryset(
                self.request, queryset.filter(id__in=ids), self)
        if self._pedido_imputable(self.request):
            qs = qs.filter(nivel__in=self.NIVELES_IMPUTABLES)
        return qs

    def _get_tipo_catalogo(self): return 'objeto_gasto'


class FuenteFinanciamientoViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = FuenteFinanciamiento.objects.all()
    serializer_class = FuenteFinanciamientoSerializer
    filterset_fields = ['activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'fuente_financiamiento'


class OrganismoFinanciadorViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = OrganismoFinanciador.objects.all()
    serializer_class = OrganismoFinanciadorSerializer
    filterset_fields = ['activo']
    search_fields = ['codigo', 'denominacion']
    def _get_tipo_catalogo(self): return 'organismo_financiador'


class EntidadTransferenciaViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = EntidadTransferencia.objects.all()
    serializer_class = EntidadTransferenciaSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'entidad_transferencia'


class FinalidadFuncionViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = FinalidadFuncion.objects.all()
    serializer_class = FinalidadFuncionSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'finalidad_funcion'


class UnidadMedidaViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'unidad_medida'


class TipoOperacionViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = TipoOperacion.objects.all()
    serializer_class = TipoOperacionSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'tipo_operacion'


class TipoProductoViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = TipoProducto.objects.all()
    serializer_class = TipoProductoSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'tipo_producto'


class TipoProyectoViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = TipoProyecto.objects.all()
    serializer_class = TipoProyectoSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'tipo_proyecto'


class TipoFinanciamientoViewSet(CatalogoImportMixin, GestionFilterMixin, viewsets.ModelViewSet):
    queryset = TipoFinanciamiento.objects.all()
    serializer_class = TipoFinanciamientoSerializer
    filterset_fields = ['activo']
    def _get_tipo_catalogo(self): return 'tipo_financiamiento'


class VersionCatalogoViewSet(viewsets.ModelViewSet):
    queryset = VersionCatalogo.objects.all()
    serializer_class = VersionCatalogoSerializer
    filterset_fields = ['gestion', 'aplicado']
