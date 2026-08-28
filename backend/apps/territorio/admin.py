from django.contrib import admin

from .models import DirigenteTerritorial, Distrito, UnidadTerritorial


class DirigenteInline(admin.TabularInline):
    model = DirigenteTerritorial
    extra = 0
    fields = ['gestion', 'nombre', 'cargo', 'telefono', 'vigente', 'observacion']


@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']
    search_fields = ['codigo', 'nombre']


@admin.register(UnidadTerritorial)
class UnidadTerritorialAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'distrito', 'activa']
    list_filter = ['distrito', 'tipo', 'activa']
    search_fields = ['codigo', 'nombre', 'nombre_busqueda']
    readonly_fields = ['nombre_busqueda']
    inlines = [DirigenteInline]


@admin.register(DirigenteTerritorial)
class DirigenteTerritorialAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cargo', 'unidad', 'gestion', 'telefono', 'vigente']
    list_filter = ['gestion', 'vigente', 'unidad__distrito']
    search_fields = ['nombre', 'cargo', 'unidad__nombre']
