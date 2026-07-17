from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Evaluacion, CriterioEvaluacion, ResultadoEvaluacion,
    LeccionAprendida, Recomendacion,
)


class CriterioEvaluacionInline(admin.TabularInline):
    model = CriterioEvaluacion
    extra = 0
    fields = ['criterion', 'score', 'weight', 'justification']
    readonly_fields = ['weighted_score']


class ResultadoEvaluacionInline(admin.TabularInline):
    model = ResultadoEvaluacion
    extra = 0
    fields = ['poau', 'unidad', 'resultado_pad', 'score_global', 'status']
    show_change_link = True


class LeccionAprendidaInline(admin.StackedInline):
    model = LeccionAprendida
    extra = 0
    fields = ['title', 'category', 'description', 'recommendations']


class RecomendacionInline(admin.TabularInline):
    model = Recomendacion
    extra = 0
    fields = ['description', 'priority', 'responsible_unit', 'status', 'due_date']


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = [
        'fiscal_year', 'evaluation_type_display', 'period_display',
        'plan_nombre', 'status_coloreado', 'total_criterios',
        'created_at',
    ]
    list_filter = ['fiscal_year', 'evaluation_type', 'status', 'period']
    search_fields = ['conclusions', 'recommendations', 'responsible_team']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [
        CriterioEvaluacionInline, ResultadoEvaluacionInline,
        LeccionAprendidaInline, RecomendacionInline,
    ]

    def evaluation_type_display(self, obj):
        return obj.get_evaluation_type_display()
    evaluation_type_display.short_description = 'Tipo'

    def period_display(self, obj):
        return obj.get_period_display()
    period_display.short_description = 'Período'

    def plan_nombre(self, obj):
        return obj.plan.nombre[:60] if obj.plan else '—'
    plan_nombre.short_description = 'Plan'

    def total_criterios(self, obj):
        return obj.criterios.count()
    total_criterios.short_description = 'Criterios'

    def status_coloreado(self, obj):
        colores = {
            'borrador': 'gray',
            'en_curso': 'orange',
            'completada': 'blue',
            'aprobada': 'green',
        }
        color = colores.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display(),
        )
    status_coloreado.short_description = 'Estado'


@admin.register(CriterioEvaluacion)
class CriterioEvaluacionAdmin(admin.ModelAdmin):
    list_display = [
        'evaluacion', 'criterion_display', 'score', 'weight',
        'weighted_score_display',
    ]
    list_filter = ['criterion', 'evaluacion__fiscal_year']
    search_fields = ['justification', 'observations']

    def criterion_display(self, obj):
        return obj.get_criterion_display()
    criterion_display.short_description = 'Criterio'

    def weighted_score_display(self, obj):
        return obj.weighted_score
    weighted_score_display.short_description = 'Puntaje Ponderado'


@admin.register(ResultadoEvaluacion)
class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = [
        'evaluacion', 'target_display', 'score_global',
        'status_coloreado',
    ]
    list_filter = ['status', 'evaluacion__fiscal_year']
    search_fields = ['observations']

    def target_display(self, obj):
        if obj.poau:
            return f'POAU: {obj.poau.codigo}'
        if obj.unidad:
            return f'Unidad: {obj.unidad.nombre}'
        if obj.resultado_pad:
            return f'PAD: {obj.resultado_pad.codigo}'
        return '—'
    target_display.short_description = 'Objeto Evaluado'

    def status_coloreado(self, obj):
        colores = {
            'cumple': 'green',
            'parcial': 'orange',
            'no_cumple': 'red',
        }
        color = colores.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display(),
        )
    status_coloreado.short_description = 'Estado'


@admin.register(LeccionAprendida)
class LeccionAprendidaAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_display', 'evaluacion']
    list_filter = ['category', 'evaluacion__fiscal_year']
    search_fields = ['title', 'description', 'recommendations']

    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Categoría'


@admin.register(Recomendacion)
class RecomendacionAdmin(admin.ModelAdmin):
    list_display = [
        'description_corta', 'priority_display', 'responsible_unit',
        'status_display', 'due_date', 'evaluacion',
    ]
    list_filter = ['priority', 'status', 'evaluacion__fiscal_year']
    search_fields = ['description', 'responsible_unit']

    def description_corta(self, obj):
        return obj.description[:80] if len(obj.description) > 80 else obj.description
    description_corta.short_description = 'Descripción'

    def priority_display(self, obj):
        return obj.get_priority_display()
    priority_display.short_description = 'Prioridad'

    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Estado'
