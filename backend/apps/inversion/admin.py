from django.contrib import admin

from .models import (
    ProyectoInversion,
    ProgramacionPlurianualProyecto,
    ProgramacionFisicaFinanciera,
)
from .models_preinversion import (
    ActividadTDR,
    AlternativaProyecto,
    AprobacionPreinversion,
    ComponenteProyecto,
    CondicionITCP,
    DocumentoGenerado,
    DocumentoPreinversion,
    EDTP,
    EstudioTecnico,
    EventoOutbox,
    FuenteFinanciamientoEDTP,
    GrupoBeneficiario,
    IndicadorEvaluacionEDTP,
    ITCP,
    ItemCostoEDTP,
    ItemCronograma,
    ItemPresupuestoTDR,
    MensajeEntrante,
    ObservacionPreinversion,
    PersonalTDR,
    PlanOperacionMantenimiento,
    ProductoTDR,
    ReferenciaExterna,
    RevisionPreinversion,
    SeccionEDTP,
    SolicitudReformulacion,
    TDR,
    VersionDocumentoPreinversion,
)
from .models_v2 import Proyecto


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ['codigo_interno', 'nombre', 'gestion', 'fase', 'estado',
                    'estado_preinversion', 'tipologia_rm115', 'habilitado_poa']
    list_filter = ['gestion', 'fase', 'estado', 'estado_preinversion',
                   'tipologia_rm115', 'habilitado_poa']
    search_fields = ['codigo_interno', 'nombre', 'distrito', 'comunidad']


@admin.register(ITCP)
class ITCPAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'version', 'estado', 'resultado_preliminar',
                    'aprobado_en']
    list_filter = ['estado', 'resultado_preliminar']


@admin.register(TDR)
class TDRAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'version', 'estado', 'duracion_dias',
                    'presupuesto_referencial']
    list_filter = ['estado']


@admin.register(EDTP)
class EDTPAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'version', 'estado', 'metodo_evaluacion',
                    'resultado_viabilidad', 'aprobado_en']
    list_filter = ['estado', 'resultado_viabilidad']


@admin.register(SeccionEDTP)
class SeccionEDTPAdmin(admin.ModelAdmin):
    list_display = ['edtp', 'codigo', 'titulo', 'requerida', 'aplicable',
                    'estado', 'porcentaje_avance']
    list_filter = ['requerida', 'aplicable', 'estado']


class VersionDocumentoInline(admin.TabularInline):
    model = VersionDocumentoPreinversion
    extra = 0
    readonly_fields = ['sha256', 'created_at']


@admin.register(DocumentoPreinversion)
class DocumentoPreinversionAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'tipo_documento', 'titulo', 'estado',
                    'version_actual']
    list_filter = ['tipo_documento', 'estado', 'etapa']
    inlines = [VersionDocumentoInline]


admin.site.register(
    [ProyectoInversion, ProgramacionPlurianualProyecto,
     ProgramacionFisicaFinanciera,
     ComponenteProyecto, GrupoBeneficiario, AlternativaProyecto,
     SolicitudReformulacion, CondicionITCP, ActividadTDR, ProductoTDR,
     PersonalTDR, ItemPresupuestoTDR, EstudioTecnico, ItemCostoEDTP,
     FuenteFinanciamientoEDTP, ItemCronograma, PlanOperacionMantenimiento,
     IndicadorEvaluacionEDTP, DocumentoGenerado, RevisionPreinversion,
     ObservacionPreinversion, AprobacionPreinversion, ReferenciaExterna,
     EventoOutbox, MensajeEntrante]
)
