"""Carga un dataset de demostración para los sistemas V2 (cutover frontend).

Puebla de forma idempotente (get_or_create):
- SIS-PE: instrumento PEI aprobado con nodos.
- SIS-POA: POAs 2027/2028 vinculados al PEI con programaciones
  físico-financieras.
- SIS-PRO: proyectos con condiciones previas, documentos, costos y vínculo
  a la cadena del POA (trazabilidad ascendente).

Uso: python manage.py cargar_demo_v2
"""
from django.core.management.base import BaseCommand

from apps.inversion.models_v2 import (
    CondicionPrevia,
    CostoProyecto,
    DocumentoTecnico,
    FasesProyecto,
    Proyecto,
    VinculoProyectoActividad,
)
from apps.planificacion.models_v2 import (
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
)
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
    Tarea,
)


class Command(BaseCommand):
    help = 'Carga datos de demostración para los sistemas V2 de PIP-GAMS.'

    def handle(self, *args, **options):
        resumen = {}

        # ------------------------------------------------------------------
        # SIS-PE: instrumento PEI aprobado
        # ------------------------------------------------------------------
        tipo_pei, _ = TipoInstrumento.objects.get_or_create(
            codigo='PEI', defaults={
                'nombre': 'Plan Estratégico Institucional',
                'nivel': 'institucional',
                'horizonte_anios': 5,
            },
        )
        pei = InstrumentoPlanificacion.objects.get_or_create(
            tipo=tipo_pei, codigo='PEI-2027',
            defaults={
                'nombre': 'PEI Municipal 2027-2031',
                'periodo_inicio': 2027, 'periodo_fin': 2031,
                'ambito': 'municipal',
            },
        )[0]
        met_pei, _ = VersionMetodologia.objects.get_or_create(
            codigo='MET-PEI-DEMO', defaults={
                'nombre': 'Metodología PEI demo',
                'tipo_instrumento': tipo_pei,
                'estado': 'vigente',
            },
        )
        version_pei, _ = VersionInstrumento.objects.get_or_create(
            instrumento=pei, numero=1,
            defaults={'metodologia': met_pei, 'etiqueta': 'Demo'},
        )
        tipo_oe, _ = TipoNodoEstrategico.objects.get_or_create(
            codigo='OE', metodologia=met_pei,
            defaults={'denominacion': 'Objetivo estratégico', 'nivel_orden': 1},
        )
        NodoEstrategico.objects.get_or_create(
            version=version_pei, tipo_nodo=tipo_oe,
            codigo='OE-1', defaults={'nombre': 'Sacaba próspera e inclusiva'},
        )
        if not version_pei.inmutable:
            version_pei.aprobar(usuario=None, norma='RM Demo 001/2027')
        resumen['pei'] = 'PEI-2027 v1 aprobada'

        # ------------------------------------------------------------------
        # SIS-POA: POAs 2027 y 2028 vinculados al PEI
        # ------------------------------------------------------------------
        poas = []
        for gestion, nombre in ((2027, 'POA Institucional 2027'),
                                (2028, 'POA Institucional 2028')):
            poa, _ = PoAInstitucional.objects.get_or_create(
                codigo=f'P-{gestion}',
                defaults={
                    'gestion': gestion,
                    'nombre': nombre,
                    'version_pei': version_pei,
                },
            )
            if not poa.version_pei_id:
                poa.version_pei = version_pei
                poa.save(update_fields=['version_pei', 'updated_at'])
            poas.append(poa)

        # Programaciones de la cadena del POA 2027
        accion, _ = AccionCortoPlazo.objects.get_or_create(
            poa=poas[0], codigo='ACP-01',
            defaults={'nombre': 'Educación y primera infancia'},
        )
        operacion, _ = Operacion.objects.get_or_create(
            accion=accion, codigo='OP-01',
            defaults={'nombre': 'Infraestructura educativa'},
        )
        actividad, _ = Actividad.objects.get_or_create(
            operacion=operacion, codigo='ACT-01',
            defaults={'nombre': 'Construcción de aulas'},
        )
        tarea, _ = Tarea.objects.get_or_create(
            actividad=actividad, codigo='TAR-01',
            defaults={'nombre': 'Construcción de 4 aulas'},
        )
        ProgramacionActividad.objects.get_or_create(
            actividad=tarea.actividad, anio=2027, tipo='financiera',
            defaults={'programado': 150000, 'ejecutado': 40000},
        )
        ProgramacionActividad.objects.get_or_create(
            actividad=tarea.actividad, anio=2028, tipo='financiera',
            defaults={'programado': 180000, 'ejecutado': 0},
        )
        ProgramacionActividad.objects.get_or_create(
            actividad=tarea.actividad, anio=2027, tipo='fisica',
            defaults={'programado': 100, 'ejecutado': 50},
        )
        resumen['poa'] = 'P-2027 (con programaciones) + P-2028'

        # ------------------------------------------------------------------
        # SIS-PRO: proyectos con condiciones, documentos, costos y cadena
        # ------------------------------------------------------------------
        proy_1, _ = Proyecto.objects.get_or_create(
            codigo_interno='PROY-001',
            defaults={
                'codigo_sisin': 'SISIN-2027-0001',
                'nombre': 'Mejoramiento infraestructura educativa',
                'gestion': 2027,
                'fase': FasesProyecto.PREINVERSION,
                'costo_total': 800000,
            },
        )
        CondicionPrevia.objects.get_or_create(
            proyecto=proy_1, descripcion='Saneamiento legal del terreno',
            defaults={'cumplida': True},
        )
        CondicionPrevia.objects.get_or_create(
            proyecto=proy_1, descripcion='Licencia ambiental',
        )
        DocumentoTecnico.objects.get_or_create(
            proyecto=proy_1, tipo='edtp', nombre='EDTP del proyecto',
        )
        CostoProyecto.objects.get_or_create(
            proyecto=proy_1, concepto='Construcción', anio=2028,
            defaults={'monto': 650000},
        )
        CostoProyecto.objects.get_or_create(
            proyecto=proy_1, concepto='Supervisión', anio=2028,
            defaults={'monto': 150000},
        )
        VinculoProyectoActividad.objects.get_or_create(
            proyecto=proy_1, actividad=actividad,
            defaults={'justificacion': 'Cadena ascendente demo'},
        )

        proy_2, _ = Proyecto.objects.get_or_create(
            codigo_interno='PROY-002',
            defaults={
                'codigo_sisin': 'SISIN-2027-0002',
                'nombre': 'Pavimentación de vías urbanas',
                'gestion': 2027,
                'fase': FasesProyecto.EJECUCION,
                'costo_total': 2500000,
                'ejecucion_acumulada': 900000,
            },
        )
        CondicionPrevia.objects.get_or_create(
            proyecto=proy_2, descripcion='Disponibilidad de recursos',
            defaults={'cumplida': True, 'fecha_cumplimiento': '2027-03-15'},
        )
        DocumentoTecnico.objects.get_or_create(
            proyecto=proy_2, tipo='contrato', nombre='Contrato de obra',
        )
        resumen['proyectos'] = 'PROY-001 (preinversión) + PROY-002 (ejecución)'

        # ------------------------------------------------------------------
        # Techos: fuentes financieras y techo por gestión (módulo Techos V2)
        # ------------------------------------------------------------------
        from apps.catalogos.models import FuenteFinanciamiento
        from apps.techos.models import TechoPresupuestario
        from datetime import date as _date

        fuentes_tecnicas = [
            ('41-113', 'CT - Coparticipación Tributaria'),
            ('20-210', 'RE - Recursos Específicos'),
        ]
        fuentes = []
        for codigo, denominacion in fuentes_tecnicas:
            fuente, _ = FuenteFinanciamiento.objects.get_or_create(
                codigo=codigo, gestion=2027,
                defaults={
                    'denominacion': denominacion,
                    'fecha_vigencia_desde': _date(2027, 1, 1),
                },
            )
            fuentes.append(fuente)
        TechoPresupuestario.objects.get_or_create(
            gestion=2027, fuente=fuentes[0],
            defaults={'monto_total': 200000, 'descripcion': 'Techo demo 2027'},
        )
        resumen['techos'] = f"{len(fuentes)} fuentes + techo 2027 (Bs 200.000)"

        for clave, valor in resumen.items():
            self.stdout.write(f'  {clave}: {valor}')
        self.stdout.write(self.style.SUCCESS('Dataset demo V2 listo.'))
