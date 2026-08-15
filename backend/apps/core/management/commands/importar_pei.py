"""Management command para sembrar el kernel estratégico PEI del SIS-PE.

Prepara la infraestructura que consume el Wizard PEI (futura UI por pasos en
features/sis-pe):

    a. Metodología oficial PEI (VersionMetodologia 'MET-PEI-OFICIAL').
    b. Tipos de nodo estratégico del PEI (OE, RI, PI) parametrizados por esa
       metodología.
    c. Instrumento PEI-{gestion} con su Versión v1 en BORRADOR (nunca
       aprobada: la completa el wizard).

Idempotente: puede ejecutarse varias veces sin duplicar registros. Si el
instrumento PEI-{gestion} ya existe (p. ej. aprobado por cargar_demo_v2) NO se
toca: solo se reporta su estado.

Uso:
    python manage.py importar_pei
    python manage.py importar_pei --gestion=2027
"""
from django.core.management.base import BaseCommand

from apps.planificacion.models_v2 import (
    EstadosInstrumento,
    InstrumentoPlanificacion,
    TipoInstrumento,
    TipoNodoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
)

CODIGO_TIPO_PEI = 'PEI'
CODIGO_METODOLOGIA = 'MET-PEI-OFICIAL'
NOMBRE_METODOLOGIA = 'Metodología PEI Oficial'
VERSION_METODOLOGIA = '1.0.0'

# Niveles del PEI en la nomenclatura del proyecto (NIVEL_ARTICULACION_CHOICES
# de apps.codificacion articula los niveles resultado_pei/producto_pei):
#   OE -> Objetivo Estratégico, RI -> Resultado Intermedio, PI -> Producto.
TIPOS_NODO_PEI = [
    ('OE', 'Objetivo Estratégico', 1, True),
    ('RI', 'Resultado Intermedio', 2, True),
    ('PI', 'Producto', 3, False),
]


class Command(BaseCommand):
    help = 'Prepara el kernel estratégico PEI (SIS-PE) para el Wizard PEI.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--gestion', type=int, default=2027,
            help='Gestión del instrumento PEI (default: 2027)',
        )

    def handle(self, *args, **options):
        gestion = options['gestion']
        self.stdout.write(self.style.NOTICE(
            f'=== INICIO IMPORTACIÓN PEI (gestión {gestion}) ==='
        ))

        metodologia = self._crear_metodologia()
        self._crear_tipos_nodo(metodologia)
        self._crear_instrumento(metodologia, gestion)

        self.stdout.write(self.style.SUCCESS(
            f'Importación PEI completada exitosamente (gestión {gestion})'
        ))

    # ------------------------------------------------------------------
    # 1. TIPO DE INSTRUMENTO Y METODOLOGÍA OFICIAL
    # ------------------------------------------------------------------
    def _crear_metodologia(self):
        tipo, creado_tipo = TipoInstrumento.objects.update_or_create(
            codigo=CODIGO_TIPO_PEI,
            defaults={
                'nombre': 'Plan Estratégico Institucional',
                'nivel': 'institucional',
                'horizonte_anios': 5,
                'entidad_emisora': 'GAM Sacaba',
            },
        )
        metodologia, creada = VersionMetodologia.objects.update_or_create(
            codigo=CODIGO_METODOLOGIA,
            defaults={
                'nombre': NOMBRE_METODOLOGIA,
                'tipo_instrumento': tipo,
                'version': VERSION_METODOLOGIA,
                'estado': 'vigente',
                'fuente_oficial': 'Metodología oficial de formulación PEI',
            },
        )
        self.stdout.write(
            f'[1/3] TipoInstrumento {CODIGO_TIPO_PEI} '
            f'({"creado" if creado_tipo else "ya existía"}) y metodología '
            f'{CODIGO_METODOLOGIA} v{VERSION_METODOLOGIA} '
            f'({"creada" if creada else "actualizada"}) (vigente).'
        )
        return metodologia

    # ------------------------------------------------------------------
    # 2. TIPOS DE NODO ESTRATÉGICO DEL PEI
    # ------------------------------------------------------------------
    def _crear_tipos_nodo(self, metodologia):
        creados = actualizados = 0
        for codigo, denominacion, orden, hijos in TIPOS_NODO_PEI:
            _, creado = TipoNodoEstrategico.objects.update_or_create(
                codigo=codigo, metodologia=metodologia,
                defaults={
                    'denominacion': denominacion,
                    'nivel_orden': orden,
                    'permite_hijos': hijos,
                    'reglas_codigo': 'código por metodología PEI oficial',
                    'campos_obligatorios': ['nombre'],
                },
            )
            if creado:
                creados += 1
            else:
                actualizados += 1
        self.stdout.write(
            f'[2/3] Tipos de nodo PEI: {creados} creados, '
            f'{actualizados} actualizados '
            f'(total {len(TIPOS_NODO_PEI)}: '
            + ', '.join(c for c, *_ in TIPOS_NODO_PEI) + ').'
        )

    # ------------------------------------------------------------------
    # 3. INSTRUMENTO PEI-{GESTION} EN BORRADOR (lo completa el wizard)
    # ------------------------------------------------------------------
    def _crear_instrumento(self, metodologia, gestion):
        codigo = f'PEI-{gestion}'
        instrumento = InstrumentoPlanificacion.objects.filter(
            codigo=codigo,
        ).first()
        if instrumento:
            versiones = instrumento.versiones.count()
            self.stdout.write(self.style.WARNING(
                f'[3/3] Instrumento {codigo} YA EXISTE (estado '
                f'"{instrumento.estado}", {versiones} versión(es)); '
                'no se modifica (lo gestiona el flujo existente).'
            ))
            return instrumento

        instrumento = InstrumentoPlanificacion.objects.create(
            tipo=TipoInstrumento.objects.get(codigo=CODIGO_TIPO_PEI),
            codigo=codigo,
            nombre=f'PEI Municipal {gestion}-{gestion + 4}',
            periodo_inicio=gestion,
            periodo_fin=gestion + 4,
            ambito='municipal',
            descripcion='Creado por importar_pei para formulación vía Wizard PEI.',
            estado=EstadosInstrumento.BORRADOR,
        )
        VersionInstrumento.objects.create(
            instrumento=instrumento,
            numero=1,
            metodologia=metodologia,
            etiqueta='Formulación Wizard PEI',
        )
        self.stdout.write(self.style.SUCCESS(
            f'[3/3] Instrumento {codigo} creado con versión v1 en BORRADOR '
            '(pendiente de completar por el Wizard PEI).'
        ))
        return instrumento
