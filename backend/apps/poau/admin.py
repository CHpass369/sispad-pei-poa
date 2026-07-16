from django.contrib import admin
from django.utils.html import format_html

from .models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera


class POAUActividadInline(admin.TabularInline):
    model = POAUActividad
    extra = 0
    fields = [
        'codigo', 'nombre', 'objeto_gasto',
        'meta_fisica_anual', 'meta_q1', 'meta_q2', 'meta_q3', 'meta_q4',
        'presupuesto_anual',
    ]
    show_change_link = True


@admin.register(POAU)
class POAUAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre_corto', 'unidad', 'gestion',
        'estado_coloreado', 'responsable', 'created_at',
    ]
    list_filter = ['gestion', 'estado', 'unidad']
    search_fields = ['codigo', 'nombre', 'descripcion']
    inlines = [POAUActividadInline]
    readonly_fields = ['created_at', 'updated_at']

    def nombre_corto(self, obj):
        return obj.nombre[:80] if len(obj.nombre) > 80 else obj.nombre
    nombre_corto.short_description = 'Nombre'

    def estado_coloreado(self, obj):
        colores = {
            'borrador': 'gray',
            'enviado': 'orange',
            'aprobado': 'green',
            'rechazado': 'red',
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display(),
        )
    estado_coloreado.short_description = 'Estado'


@admin.register(POAUActividad)
class POAUActividadAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre_corto', 'poau', 'objeto_gasto',
        'meta_fisica_anual', 'meta_q1', 'meta_q2', 'meta_q3', 'meta_q4',
        'presupuesto_anual',
    ]
    list_filter = ['poau__gestion', 'objeto_gasto']
    search_fields = ['codigo', 'nombre']

    def nombre_corto(self, obj):
        return obj.nombre[:80] if len(obj.nombre) > 80 else obj.nombre
    nombre_corto.short_description = 'Nombre'


@admin.register(EjecucionFisica)
class EjecucionFisicaAdmin(admin.ModelAdmin):
    list_display = ['actividad', 'periodo', 'tipo_periodo',
                    'programado', 'ejecutado']
    list_filter = ['tipo_periodo', 'periodo']
    search_fields = ['periodo', 'observaciones']


@admin.register(EjecucionFinanciera)
class EjecucionFinancieraAdmin(admin.ModelAdmin):
    list_display = ['actividad', 'periodo', 'tipo_periodo',
                    'programado', 'ejecutado']
    list_filter = ['tipo_periodo', 'periodo']
    search_fields = ['periodo', 'observaciones']
