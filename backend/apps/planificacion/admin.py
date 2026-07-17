from django.contrib import admin
from .models import (
    Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo,
    ArticulacionPlanificacion, PlanVersion
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'gestion_inicio', 'gestion_fin', 'activo']
    list_filter = ['tipo', 'activo']
    search_fields = ['codigo', 'nombre']


@admin.register(NodoPlanificacion)
class NodoPlanificacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nivel', 'nombre', 'plan', 'gestion', 'activo']
    list_filter = ['nivel', 'gestion', 'activo']
    search_fields = ['codigo', 'nombre']


@admin.register(AccionMedianoPlazo)
class AccionMedianoPlazoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'nodo_planificacion', 'gestion_inicio', 'gestion_fin']
    search_fields = ['codigo', 'nombre']


@admin.register(AccionCortoPlazo)
class AccionCortoPlazoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'gestion', 'unidad_responsable']
    list_filter = ['gestion']
    search_fields = ['codigo', 'nombre']


@admin.register(ArticulacionPlanificacion)
class ArticulacionPlanificacionAdmin(admin.ModelAdmin):
    list_display = ['nodo_origen', 'nodo_destino', 'es_principal', 'gestion']
    list_filter = ['gestion', 'es_principal']


@admin.register(PlanVersion)
class PlanVersionAdmin(admin.ModelAdmin):
    list_display = ['plan', 'version_number', 'version_name', 'status', 'valid_from', 'valid_to']
    list_filter = ['status', 'plan']
    search_fields = ['version_name', 'change_reason']
    readonly_fields = ['created_at', 'updated_at']
