from django.contrib import admin
from .models import EventoAuditoria


@admin.register(EventoAuditoria)
class EventoAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['creado_en', 'usuario', 'accion', 'entidad', 'entidad_id', 'gestion']
    list_filter = ['accion', 'entidad', 'gestion', 'creado_en']
    search_fields = ['entidad', 'entidad_id', 'resumen']
    readonly_fields = [f.name for f in EventoAuditoria._meta.fields]
