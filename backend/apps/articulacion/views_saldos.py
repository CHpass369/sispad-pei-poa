"""Administración de los techos por unidad y categoría programática.

El asistente de recursos (`/poau_recursos`) necesita saber cuánto puede
programar una unidad en una categoría. Ese monto vivía en un arreglo estático
del bundle de Angular: cambiar un número costaba editar TypeScript, compilar y
desplegar, y nada garantizaba que la unidad o la categoría existieran.

Acá se administra desde la base. La lectura la comparte con la matriz POAU
—misma capacidad y mismo alcance organizacional (ADR-003)— porque el asistente
tiene que poder consultarla; la escritura es solo de administrador.
"""
import re

from django.db.models import ProtectedError
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.accounts.permissions import TieneCapacidad
from apps.accounts.services_scope import GLOBAL_SCOPE, ScopeResolver
from apps.core.permissions import IsSuperAdmin
from apps.gestion.mixins import gestion_del_candado
from apps.organizacion.models import UnidadOrganizacional

from .models import SaldoUnidadCategoria

CAPACIDAD_LECTURA = 'sis_poa.poau.view'


class LeePoauEscribeAdministrador(BasePermission):
    """Leer con la capacidad del POAU; crear, editar y borrar solo administrador.

    Son dos públicos distintos: cualquier unidad necesita *ver* su techo para
    programar, pero decidir cuánto tiene es una atribución de administración.
    Separar los dos verbos evita el atajo de abrir la escritura a todo el que ya
    podía leer.
    """

    SEGUROS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in self.SEGUROS:
            return TieneCapacidad(CAPACIDAD_LECTURA).has_permission(request, view)
        return IsSuperAdmin().has_permission(request, view)


class SaldoUnidadCategoriaSerializer(serializers.ModelSerializer):
    unidad_codigo = serializers.CharField(source='unidad.codigo', read_only=True)
    unidad_nombre = serializers.CharField(source='unidad.nombre', read_only=True)
    gestion = serializers.IntegerField(source='unidad.gestion.anio', read_only=True)
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True, default=None)
    fuente_denominacion = serializers.CharField(
        source='fuente.denominacion', read_only=True, default=None,
    )
    organismo_codigo = serializers.CharField(
        source='organismo.codigo', read_only=True, default=None,
    )
    organismo_denominacion = serializers.CharField(
        source='organismo.denominacion', read_only=True, default=None,
    )

    class Meta:
        model = SaldoUnidadCategoria
        fields = [
            'id', 'unidad', 'unidad_codigo', 'unidad_nombre', 'gestion',
            'categoria_programatica', 'denominacion',
            'fuente', 'fuente_codigo', 'fuente_denominacion',
            'organismo', 'organismo_codigo', 'organismo_denominacion',
            'saldo', 'filas_origen', 'observacion', 'activo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_categoria_programatica(self, valor):
        """Normaliza como el resto del sistema: espacios colapsados, mayúsculas.

        La planilla escribe `340 0 099` y el POAU puede traer `340  0 099`. Sin
        esta normalización el asistente no cruza el techo con la operación y el
        selector sale vacío sin explicar por qué.
        """
        normalizado = re.sub(r'\s+', ' ', (valor or '')).strip().upper()
        if not normalizado:
            raise serializers.ValidationError(
                'La categoría programática es obligatoria.',
            )
        return normalizado

    def validate(self, datos):
        """Rechaza el duplicado con un mensaje que dice qué hacer.

        La restricción de base ya lo impide, pero un `IntegrityError` le llega
        al usuario como 500. Acá se convierte en un 400 que nombra la fila que
        ya existe: casi siempre lo que se quiere es editarla, no crear otra.
        """
        instancia = self.instance
        unidad = datos.get('unidad', getattr(instancia, 'unidad', None))
        categoria = datos.get(
            'categoria_programatica',
            getattr(instancia, 'categoria_programatica', None),
        )
        fuente = datos.get('fuente', getattr(instancia, 'fuente', None))
        organismo = datos.get('organismo', getattr(instancia, 'organismo', None))

        choque = SaldoUnidadCategoria.objects.filter(
            unidad=unidad, categoria_programatica=categoria,
            fuente=fuente, organismo=organismo,
        )
        if instancia is not None:
            choque = choque.exclude(pk=instancia.pk)
        if choque.exists():
            raise serializers.ValidationError({
                'categoria_programatica': [
                    f'La unidad {getattr(unidad, "codigo", unidad)} ya tiene un '
                    f'saldo para {categoria} con esa fuente y organismo. '
                    f'Edite esa fila en vez de crear otra: dos filas para el '
                    f'mismo par duplican el techo declarado.',
                ],
            })
        return datos


class SaldoUnidadCategoriaViewSet(viewsets.ModelViewSet):
    """CRUD de techos. `?unidad=<codigo>` filtra por unidad organizacional."""

    serializer_class = SaldoUnidadCategoriaSerializer
    permission_classes = [LeePoauEscribeAdministrador]
    # `unidad` NO va acá: el contrato con el frontend es `?unidad=<codigo>`,
    # igual que en `matriz-poau`. Declararla como filtro de django-filter la
    # hace esperar un UUID y devuelve 400 antes de llegar a `get_queryset`.
    filterset_fields = ['activo', 'fuente', 'organismo']
    search_fields = ['categoria_programatica', 'denominacion', 'unidad__codigo']
    ordering_fields = ['categoria_programatica', 'saldo']

    def _codigos_en_alcance(self):
        """Códigos de UO que el usuario puede leer, o None si su alcance es global."""
        request = self.request
        if request.user.is_superuser:
            return None
        unidades = ScopeResolver.unidades_efectivas(
            request.user, gestion_del_candado(request).id,
        )
        if GLOBAL_SCOPE in unidades:
            return None
        return set(
            UnidadOrganizacional.objects
            .filter(pk__in=unidades)
            .values_list('codigo', flat=True)
        )

    def get_queryset(self):
        qs = (
            SaldoUnidadCategoria.objects
            .select_related('unidad', 'unidad__gestion', 'fuente', 'organismo')
            .filter(unidad__gestion=gestion_del_candado(self.request))
        )
        # El alcance solo recorta la lectura. La escritura ya está cerrada a
        # administrador, que siempre tiene alcance global.
        en_alcance = self._codigos_en_alcance()
        if en_alcance is not None:
            qs = qs.filter(unidad__codigo__in=en_alcance)
        unidad = self.request.query_params.get('unidad')
        if unidad:
            qs = qs.filter(unidad__codigo=unidad)
        return qs

    def perform_create(self, serializer):
        # `AsignacionObjetoGasto` se guardaba sin autor y dejó trece filas sin
        # forma de saber quién las cargó. Acá se estampa desde el principio.
        serializer.save(
            created_by=self.request.user, updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Borra el techo, informando qué lo retiene si algo apunta a él."""
        instancia = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as exc:
            return Response(
                {
                    'detail': (
                        f'No se puede borrar el saldo de '
                        f'{instancia.unidad.codigo} en '
                        f'{instancia.categoria_programatica}: hay registros que '
                        f'dependen de él.'
                    ),
                    'retenido_por': [str(o) for o in exc.protected_objects][:20],
                },
                status=status.HTTP_409_CONFLICT,
            )
