"""V2 transport adapter for POAU physical-programming imports."""

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.permissions import CapacidadConScope

from .models import ImportacionProgramacionFisica
from .poau_importer import (
    MAX_WORKBOOK_BYTES,
    ImportacionError,
    apply_preview,
    create_preview,
    download_google_sheet,
    serialize_preview,
)


class ImportacionProgramacionFisicaViewSet(viewsets.GenericViewSet):
    """Two-step contract: preview in memory, then explicit atomic apply."""

    queryset = ImportacionProgramacionFisica.objects.select_related(
        'gestion', 'unidad', 'creado_por',
    )
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ['post']

    def get_permissions(self):
        return [CapacidadConScope(
            'sis_poa.poau.edit', gestion_id_param='gestion_id',
        )]

    def get_queryset(self):
        queryset = super().get_queryset().filter(gestion__activa=True)
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(creado_por=self.request.user)

    @staticmethod
    def _required(data, field, label):
        value = str(data.get(field, '')).strip()
        if not value:
            raise serializers.ValidationError({field: [f'Debe indicar {label}.']})
        return value

    @action(detail=False, methods=['post'], url_path='preview')
    def preview(self, request):
        source_type = self._required(request.data, 'source_type', 'la fuente')
        unit_code = self._required(
            request.data, 'unidad_codigo', 'la unidad organizacional',
        )
        sheet_name = str(request.data.get('sheet_name', '')).strip()
        try:
            if source_type == ImportacionProgramacionFisica.Origen.EXCEL:
                uploaded = request.FILES.get('file')
                if uploaded is None:
                    raise serializers.ValidationError({
                        'file': ['Seleccione un archivo Excel .xlsx.'],
                    })
                if not uploaded.name.lower().endswith('.xlsx'):
                    raise serializers.ValidationError({
                        'file': ['Solo se admiten libros Excel .xlsx.'],
                    })
                content = uploaded.read(MAX_WORKBOOK_BYTES + 1)
                source_name = uploaded.name
                origin = ImportacionProgramacionFisica.Origen.EXCEL
            elif source_type == ImportacionProgramacionFisica.Origen.GOOGLE_SHEETS:
                google_url = self._required(
                    request.data, 'google_url', 'la URL de Google Sheets',
                )
                content, source_name, _gid = download_google_sheet(
                    google_url, sheet_name,
                )
                origin = ImportacionProgramacionFisica.Origen.GOOGLE_SHEETS
            else:
                raise serializers.ValidationError({
                    'source_type': ['Use excel o google_sheets.'],
                })
            preview = create_preview(
                request=request,
                origin=origin,
                unit_code=unit_code,
                content=content,
                source_name=source_name,
                sheet_name=sheet_name,
            )
        except ImportacionError as exc:
            raise serializers.ValidationError({'detail': exc.messages}) from exc
        return Response(serialize_preview(preview), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='apply')
    def apply(self, request, pk=None):
        # get_object performs the capability/scope object check before locking;
        # apply_preview repeats ownership, scope, state, and expiry checks under lock.
        preview = self.get_object()
        operation_types = request.data.get('operation_types') or {}
        if not isinstance(operation_types, dict):
            raise serializers.ValidationError({
                'operation_types': ['Debe enviar una selección por operación.'],
            })
        try:
            applied = apply_preview(
                preview.id,
                request.user,
                confirmation_code=str(
                    request.data.get('confirmation_code', ''),
                ).strip(),
                operation_types=operation_types,
            )
        except ImportacionError as exc:
            raise serializers.ValidationError({'detail': exc.messages}) from exc
        return Response(serialize_preview(applied))
