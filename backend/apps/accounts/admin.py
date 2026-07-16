from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Rol


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activo', 'orden']
    search_fields = ['codigo', 'nombre']
    list_filter = ['activo']


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'cargo', 'activo', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    list_filter = ['activo', 'is_staff', 'roles']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'cargo', 'telefono')}),
        ('Roles y permisos', {'fields': ('roles', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    filter_horizontal = ['roles', 'groups', 'user_permissions']
