from django.contrib import admin

from .models import VersionCatalogoPlan


@admin.register(VersionCatalogoPlan)
class VersionCatalogoPlanAdmin(admin.ModelAdmin):
    list_display = ['plan', 'gestion', 'estado', 'norma_aprobacion']
    list_filter = ['estado', 'gestion']
    search_fields = ['plan__codigo', 'plan__nombre', 'norma_aprobacion']
    readonly_fields = ['created_at', 'updated_at']
