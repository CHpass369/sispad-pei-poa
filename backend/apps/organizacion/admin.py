from django.contrib import admin
from .models import TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad


@admin.register(TipoUnidad)
class TipoUnidadAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'nivel', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']


@admin.register(UnidadOrganizacional)
class UnidadOrganizacionalAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'sigla', 'tipo', 'gestion', 'activo']
    list_filter = ['tipo', 'gestion', 'activo']
    search_fields = ['codigo', 'nombre', 'sigla']


@admin.register(DireccionAdministrativa)
class DireccionAdministrativaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'gestion', 'activo']
    list_filter = ['gestion', 'activo']


@admin.register(UnidadEjecutora)
class UnidadEjecutoraAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'da', 'gestion', 'activo']
    list_filter = ['da', 'gestion', 'activo']


@admin.register(AsignacionUsuarioUnidad)
class AsignacionUsuarioUnidadAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'unidad', 'gestion', 'es_responsable_poa', 'activo']
    list_filter = ['gestion', 'es_responsable_poa', 'activo']
