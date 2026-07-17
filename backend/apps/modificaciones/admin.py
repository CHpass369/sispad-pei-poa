from django.contrib import admin
from django.utils.html import format_html

from .models import SolicitudModificacion, CambioModificacion, ImpactoModificacion


class CambioModificacionInline(admin.TabularInline):
    model = CambioModificacion
    extra = 0
    fields = ['campo', 'valor_anterior', 'valor_propuesto', 'valor_aprobado']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SolicitudModificacion)
class SolicitudModificacionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tipo_display', 'gestion_fiscal', 'entidad_afectada_tipo',
        'estado_coloreado', 'solicitado_por', 'version', 'created_at',
    ]
    list_filter = ['tipo', 'gestion_fiscal', 'estado', 'entidad_afectada_tipo']
    search_fields = ['motivo', 'informe_tecnico', 'documento_legal', 'entidad_afectada_tipo']
    readonly_fields = ['id', 'version', 'created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [CambioModificacionInline]

    def tipo_display(self, obj):
        return obj.get_tipo_display()
    tipo_display.short_description = 'Tipo'

    def estado_coloreado(self, obj):
        colores = {
            'borrador': 'gray',
            'en_revision': 'orange',
            'aprobada': 'green',
            'rechazada': 'red',
            'cumplida': 'blue',
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display(),
        )
    estado_coloreado.short_description = 'Estado'


@admin.register(CambioModificacion)
class CambioModificacionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'solicitud', 'campo', 'valor_anterior',
        'valor_propuesto', 'valor_aprobado',
    ]
    list_filter = ['campo']
    search_fields = ['campo', 'valor_anterior', 'valor_propuesto', 'valor_aprobado']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(ImpactoModificacion)
class ImpactoModificacionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'solicitud', 'impacto_financiero',
        'impacto_fisico_corto', 'created_at',
    ]
    list_filter = ['impacto_financiero']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def impacto_fisico_corto(self, obj):
        return obj.impacto_fisico[:80] if obj.impacto_fisico else ''
    impacto_fisico_corto.short_description = 'Impacto Físico'
