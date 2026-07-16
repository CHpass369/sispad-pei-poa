from django.contrib import admin
from .models import GestionFiscal, CicloFormulacion, EtapaFormulacion


@admin.register(GestionFiscal)
class GestionFiscalAdmin(admin.ModelAdmin):
    list_display = ['anio', 'estado', 'activa', 'fecha_apertura', 'fecha_cierre']
    list_filter = ['estado', 'activa']
    search_fields = ['anio']


@admin.register(CicloFormulacion)
class CicloFormulacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'gestion', 'fecha_inicio', 'fecha_cierre', 'activo']
    list_filter = ['activo', 'gestion']


@admin.register(EtapaFormulacion)
class EtapaFormulacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'ciclo', 'fecha_inicio', 'fecha_cierre', 'completada']
    list_filter = ['completada', 'ciclo']
