from django.contrib import admin

from .models import (
    ReporteSeguimiento, EntradaSeguimiento, Alerta, UmbralConfiguracion,
)


class EntradaSeguimientoInline(admin.TabularInline):
    model = EntradaSeguimiento
    extra = 0
    fields = [
        'actividad', 'programado_fisico', 'ejecutado_fisico',
        'porcentaje_avance_fisico', 'programado_financiero',
        'ejecutado_financiero', 'porcentaje_avance_financiero',
    ]
    show_change_link = True


class AlertaInline(admin.TabularInline):
    model = Alerta
    extra = 0
    fields = ['tipo', 'severidad', 'mensaje', 'activa']
    readonly_fields = ['tipo', 'severidad', 'mensaje', 'activa']
    show_change_link = True


@admin.register(ReporteSeguimiento)
class ReporteSeguimientoAdmin(admin.ModelAdmin):
    list_display = [
        'gestion', 'periodo', 'unidad_organizacional',
        'estado', 'submitted_at', 'approved_at',
    ]
    list_filter = ['gestion', 'periodo', 'estado']
    search_fields = ['unidad_organizacional__nombre', 'periodo']
    readonly_fields = ['submitted_at', 'approved_at']
    inlines = [EntradaSeguimientoInline]


@admin.register(EntradaSeguimiento)
class EntradaSeguimientoAdmin(admin.ModelAdmin):
    list_display = [
        'actividad', 'reporte',
        'programado_fisico', 'ejecutado_fisico',
        'porcentaje_avance_fisico',
        'programado_financiero', 'ejecutado_financiero',
        'porcentaje_avance_financiero',
    ]
    list_filter = [
        'reporte__gestion', 'reporte__periodo',
        'reporte__estado',
    ]
    search_fields = [
        'actividad__codigo', 'actividad__nombre',
        'causa_desviacion',
    ]
    inlines = [AlertaInline]


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = [
        'tipo', 'severidad', 'entrada',
        'activa', 'resuelta_en', 'resuelta_por',
    ]
    list_filter = ['tipo', 'severidad', 'activa']
    search_fields = ['mensaje', 'entrada__actividad__nombre']
    readonly_fields = ['resuelta_en', 'resuelta_por']


@admin.register(UmbralConfiguracion)
class UmbralConfiguracionAdmin(admin.ModelAdmin):
    list_display = [
        'tipo_umbral', 'porcentaje_minimo', 'porcentaje_maximo',
        'activo',
    ]
    list_filter = ['activo']
    search_fields = ['tipo_umbral', 'descripcion']
