from django.contrib import admin

from .models import (
    ComponentePDESA,
    EjePGDESA,
    EntidadCodificadora,
    EntidadTerritorialCGEO,
    HomologacionCodigo,
    LineamientoPAD,
    ResultadoSectorial,
    SectorEconomico,
    SecuenciaCodigo,
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


@admin.register(LineamientoPAD)
class LineamientoPADAdmin(CatalogoSegmentoAdmin):
    list_display = CatalogoSegmentoAdmin.list_display + ['entidad_territorial']


@admin.register(EntidadTerritorialCGEO)
class EntidadTerritorialCGEOAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'nivel', 'padre', 'estado']
    list_filter = ['nivel', 'estado']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EntidadCodificadora)
class EntidadCodificadoraAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'denominacion', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SecuenciaCodigo)
class SecuenciaCodigoAdmin(admin.ModelAdmin):
    list_display = ['nivel', 'padre_id', 'gestion', 'entidad', 'ultimo_valor']
    list_filter = ['nivel', 'gestion', 'entidad']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HomologacionCodigo)
class HomologacionCodigoAdmin(admin.ModelAdmin):
    """Las homologaciones son append-only: el admin solo permite insertar y ver."""

    list_display = [
        'tipo_entidad', 'codigo_anterior', 'codigo_nuevo',
        'gestion', 'usuario', 'fecha',
    ]
    list_filter = ['tipo_entidad', 'gestion']
    search_fields = ['codigo_anterior', 'codigo_nuevo', 'documento_respaldo']
    readonly_fields = ['created_at', 'updated_at', 'fecha']

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
