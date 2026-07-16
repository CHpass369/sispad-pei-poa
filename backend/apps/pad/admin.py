from django.contrib import admin

from .models import (
    SectorPAD, PoliticaPAD, LineamientoEstrategico,
    ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB,
    ArticulacionLog, ProgramacionAnualPAD,
)


@admin.register(SectorPAD)
class SectorPADAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']
    search_fields = ['codigo', 'nombre']


@admin.register(PoliticaPAD)
class PoliticaPADAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'gestion']
    list_filter = ['gestion']
    search_fields = ['codigo', 'nombre']


class LineamientoInline(admin.TabularInline):
    model = LineamientoEstrategico
    extra = 0
    fields = ['codigo', 'nombre']
    show_change_link = True


@admin.register(LineamientoEstrategico)
class LineamientoEstrategicoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'politica', 'gestion']
    list_filter = ['gestion', 'politica']
    search_fields = ['codigo', 'nombre']


class ProgramacionAnualPADInline(admin.TabularInline):
    model = ProgramacionAnualPAD
    extra = 1
    fields = ['anio', 'tipo', 'valor']
    show_change_link = True


class ProductoTerritorialInline(admin.TabularInline):
    model = ProductoTerritorial
    extra = 0
    fields = ['codigo', 'nombre']
    show_change_link = True


@admin.register(ResultadoTerritorial)
class ResultadoTerritorialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre_corto', 'lineamiento', 'sector', 'estado', 'gestion']
    list_filter = ['gestion', 'estado', 'lineamiento', 'sector']
    search_fields = ['codigo', 'nombre']
    inlines = [ProductoTerritorialInline, ProgramacionAnualPADInline]

    def nombre_corto(self, obj):
        return obj.nombre[:80]
    nombre_corto.short_description = 'Nombre'


@admin.register(ProductoTerritorial)
class ProductoTerritorialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre_corto', 'resultado', 'cuenta_con_financiamiento', 'gestion']
    list_filter = ['gestion', 'resultado__lineamiento', 'cuenta_con_financiamiento']
    search_fields = ['codigo', 'nombre']
    inlines = [ProgramacionAnualPADInline]

    def nombre_corto(self, obj):
        return obj.nombre[:80]
    nombre_corto.short_description = 'Nombre'


@admin.register(ProgramacionAnualPAD)
class ProgramacionAnualPADAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'anio', 'tipo', 'valor']
    list_filter = ['anio', 'tipo']
    search_fields = ['resultado__nombre', 'producto__nombre']


@admin.register(ArticulacionSIPEB)
class ArticulacionSIPEBAdmin(admin.ModelAdmin):
    list_display = ['resultado', 'cod_eje_pgdesa', 'cod_ods', 'cod_sector', 'gestion']
    list_filter = ['gestion', 'cod_ods']
    search_fields = ['resultado__codigo', 'resultado__nombre']


@admin.register(ArticulacionLog)
class ArticulacionLogAdmin(admin.ModelAdmin):
    list_display = ['entidad', 'entidad_id', 'accion', 'usuario', 'creado_en']
    list_filter = ['accion', 'entidad', 'creado_en']
    search_fields = ['entidad', 'entidad_id', 'usuario__email']
    readonly_fields = ['entidad', 'entidad_id', 'accion', 'usuario', 'detalle', 'creado_en']
