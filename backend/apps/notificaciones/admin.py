from django.contrib import admin
from .models import TipoNotificacion, Notificacion, PreferenciaNotificacion


@admin.register(TipoNotificacion)
class TipoNotificacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['codigo', 'nombre']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'user', 'tipo', 'priority', 'is_read',
        'read_at', 'gestion', 'created_at',
    ]
    list_filter = ['is_read', 'priority', 'tipo', 'gestion']
    search_fields = ['titulo', 'mensaje', 'user__username']
    raw_id_fields = ['user', 'tipo']
    readonly_fields = ['read_at', 'created_at', 'updated_at']


@admin.register(PreferenciaNotificacion)
class PreferenciaNotificacionAdmin(admin.ModelAdmin):
    list_display = ['user', 'receive_internal', 'receive_email', 'frequency']
    list_filter = ['receive_internal', 'receive_email', 'frequency']
    raw_id_fields = ['user']
