from django.contrib import admin

from .models import SectorPAD


@admin.register(SectorPAD)
class SectorPADAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre')
    ordering = ('codigo',)
