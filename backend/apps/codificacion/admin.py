from django.contrib import admin

from .models import (
    ComponentePDESA,
    EjePGDESA,
    ResultadoSectorial,
    SectorEconomico,
    VersionCatalogoPlan,
)


@admin.register(VersionCatalogoPlan)
class VersionCatalogoPlanAdmin(admin.ModelAdmin):
    list_display = ['plan', 'gestion', 'estado', 'norma_aprobacion']
    list_filter = ['estado', 'gestion']
    search_fields = ['plan__codigo', 'plan__nombre', 'norma_aprobacion']
    readonly_fields = ['created_at', 'updated_at']


class CatalogoSegmentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'denominacion', 'version_catalogo', 'activo']
    list_filter = ['activo', 'version_catalogo']
    search_fields = ['codigo', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EjePGDESA)
class EjePGDESAAdmin(CatalogoSegmentoAdmin):
    pass


@admin.register(ComponentePDESA)
class ComponentePDESAAdmin(CatalogoSegmentoAdmin):
    list_display = CatalogoSegmentoAdmin.list_display + ['eje']
    list_filter = CatalogoSegmentoAdmin.list_filter + ['eje']


@admin.register(SectorEconomico)
class SectorEconomicoAdmin(CatalogoSegmentoAdmin):
    list_display = CatalogoSegmentoAdmin.list_display + ['componente']


@admin.register(ResultadoSectorial)
class ResultadoSectorialAdmin(CatalogoSegmentoAdmin):
    list_display = CatalogoSegmentoAdmin.list_display + ['sector']
