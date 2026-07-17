from django.contrib import admin
from .models import TechoPresupuestario, DistribucionTecho, MovimientoTecho


@admin.register(TechoPresupuestario)
class TechoPresupuestarioAdmin(admin.ModelAdmin):
    list_display = ['gestion', 'fuente', 'organismo', 'monto_total', 'activo', 'version']
    list_filter = ['gestion', 'fuente', 'activo']
    search_fields = ['descripcion']


@admin.register(DistribucionTecho)
class DistribucionTechoAdmin(admin.ModelAdmin):
    list_display = ['techo', 'da', 'ue', 'unidad', 'monto_asignado', 'activo']
    list_filter = ['techo', 'activo']
    search_fields = ['techo__descripcion']


@admin.register(MovimientoTecho)
class MovimientoTechoAdmin(admin.ModelAdmin):
    list_display = ['techo', 'movement_type', 'amount', 'requested_by', 'approved_by', 'date']
    list_filter = ['movement_type', 'techo__gestion']
    search_fields = ['justification']
    readonly_fields = ['created_at']
