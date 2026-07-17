from django.contrib import admin
from django.utils.html import format_html
from .models import AccionCorrectiva, CompromisoAccionCorrectiva


class CompromisoAccionCorrectivaInline(admin.TabularInline):
    model = CompromisoAccionCorrectiva
    extra = 0
    fields = ['description', 'due_date', 'status', 'completed_at', 'notes']
    readonly_fields = ['completed_at']


@admin.register(AccionCorrectiva)
class AccionCorrectivaAdmin(admin.ModelAdmin):
    list_display = [
        'id_corto', 'description_corta', 'responsible_email',
        'responsible_unit_nombre', 'start_date', 'due_date',
        'status_coloreado', 'porcentaje_display', 'gestion',
    ]
    list_filter = ['status', 'gestion', 'responsible_unit']
    search_fields = ['description', 'cause', 'expected_result', 'evidence']
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'verified_by', 'verified_at',
    ]
    inlines = [CompromisoAccionCorrectivaInline]
    date_hierarchy = 'due_date'

    def id_corto(self, obj):
        return f'AC-{str(obj.pk)[:8]}'
    id_corto.short_description = 'ID'

    def description_corta(self, obj):
        return obj.description[:80] if len(obj.description) > 80 else obj.description
    description_corta.short_description = 'Descripción'

    def responsible_email(self, obj):
        return obj.responsible.email if obj.responsible else '—'
    responsible_email.short_description = 'Responsable'

    def responsible_unit_nombre(self, obj):
        return obj.responsible_unit.nombre if obj.responsible_unit else '—'
    responsible_unit_nombre.short_description = 'Unidad'

    def status_coloreado(self, obj):
        colores = {
            'pendiente': 'gray',
            'en_ejecucion': 'orange',
            'cumplida': 'green',
            'incumplida': 'red',
            'cerrada': 'blue',
            'cancelada': 'lightgray',
        }
        color = colores.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display(),
        )
    status_coloreado.short_description = 'Estado'

    def porcentaje_display(self, obj):
        total = obj.compromisos.count()
        if total == 0:
            return '—'
        cumplidos = obj.compromisos.filter(status='cumplido').count()
        pct = round((cumplidos / total) * 100, 1)
        return f'{pct}% ({cumplidos}/{total})'
    porcentaje_display.short_description = 'Cumplimiento'


@admin.register(CompromisoAccionCorrectiva)
class CompromisoAccionCorrectivaAdmin(admin.ModelAdmin):
    list_display = [
        'id_corto', 'accion_corta', 'description_corta',
        'due_date', 'status_coloreado', 'completed_at',
    ]
    list_filter = ['status', 'due_date']
    search_fields = ['description', 'notes']
    readonly_fields = ['completed_at', 'created_at', 'updated_at']

    def id_corto(self, obj):
        return f'CA-{str(obj.pk)[:8]}'
    id_corto.short_description = 'ID'

    def accion_corta(self, obj):
        return f'AC-{str(obj.accion_correctiva_id)[:8]}'
    accion_corta.short_description = 'Acción Correctiva'

    def description_corta(self, obj):
        return obj.description[:80] if len(obj.description) > 80 else obj.description
    description_corta.short_description = 'Descripción'

    def status_coloreado(self, obj):
        colores = {
            'pendiente': 'gray',
            'cumplido': 'green',
            'incumplido': 'red',
        }
        color = colores.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display(),
        )
    status_coloreado.short_description = 'Estado'
