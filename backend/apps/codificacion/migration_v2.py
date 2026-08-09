"""Adaptador de importación del marco superior PGDESA/PDESA al kernel V2.

WP-06 (plan maestro §FASE 4). Convierte los catálogos oficiales de
`codificacion` (EjePGDESA → ComponentePDESA → SectorEconomico →
ResultadoSectorial) en nodos del kernel estratégico V2.

Reglas:
- Idempotente: re-ejecutar no duplica nodos ni versiones.
- Nunca sobrescribe versiones aprobadas: cada gestión importada crea su
  propio instrumento/versión.
- Cada versión queda aprobada e inmutable con checksum.
- Trazabilidad completa en LegacyMigrationMap (lote propio).
"""
from datetime import date

from apps.codificacion.models import (
    ComponentePDESA,
    EjePGDESA,
    ResultadoSectorial,
    SectorEconomico,
    VersionCatalogoPlan,
)
from apps.core.migration_audit import checksum_registro
from apps.core.models import LegacyMigrationMap
from apps.planificacion.models_v2 import (
    EstadosInstrumento,
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
)

# Niveles de la cadena oficial, en orden de jerarquía.
NIVELES_MARCO = [
    ('EjePGDESA', 'EJE', 'Eje', 1, True, '2 dígitos'),
    ('ComponentePDESA', 'COMP', 'Componente', 2, True, '2 dígitos'),
    ('SectorEconomico', 'SECTOR', 'Sector económico', 3, True, '2 dígitos'),
    ('ResultadoSectorial', 'RS', 'Resultado sectorial', 4, False, '2 dígitos'),
]

MODELOS_LEGACY = {
    'EjePGDESA': EjePGDESA,
    'ComponentePDESA': ComponentePDESA,
    'SectorEconomico': SectorEconomico,
    'ResultadoSectorial': ResultadoSectorial,
}


def _tipo_instrumento_para(plan, dry_run=False):
    codigo = plan.tipo.upper()
    defaults = {
        'nombre': f'Instrumento {plan.nombre}',
        'nivel': 'nacional',
        'entidad_emisora': 'Órgano rector nacional',
    }
    if dry_run:
        return TipoInstrumento(codigo=codigo, **defaults)
    tipo, _ = TipoInstrumento.objects.get_or_create(
        codigo=codigo, defaults=defaults,
    )
    return tipo


def _metodologia_para(tipo, dry_run=False):
    codigo = f'OFICIAL-{tipo.codigo}'
    defaults = {
        'nombre': f'Metodología oficial {tipo.nombre}',
        'tipo_instrumento': tipo,
        'version': '1.0.0',
        'estado': 'vigente',
        'fuente_oficial': 'Importación oficial de catálogos normativos',
    }
    if dry_run:
        return VersionMetodologia(codigo=codigo, **defaults)
    metodologia, _ = VersionMetodologia.objects.get_or_create(
        codigo=codigo, defaults=defaults,
    )
    return metodologia


def _tipos_nodo_para(metodologia, dry_run=False):
    tipos = {}
    for _modelo, codigo, denominacion, orden, permite_hijos, reglas in NIVELES_MARCO:
        defaults = {
            'denominacion': denominacion,
            'nivel_orden': orden,
            'permite_hijos': permite_hijos,
            'reglas_codigo': reglas,
        }
        if dry_run:
            tipos[codigo] = TipoNodoEstrategico(
                codigo=codigo, metodologia=metodologia, **defaults,
            )
            continue
        tipo, _ = TipoNodoEstrategico.objects.get_or_create(
            codigo=codigo, metodologia=metodologia, defaults=defaults,
        )
        tipos[codigo] = tipo
    return tipos


def _instrumento_para(vc, tipo, dry_run=False):
    codigo = f'{vc.plan.codigo}-{vc.gestion}'
    defaults = {
        'nombre': f'{vc.plan.nombre} {vc.gestion}',
        'periodo_inicio': vc.gestion,
        'periodo_fin': vc.gestion,
        'ambito': 'nacional',
        'descripcion': f'Importado de catálogos oficiales (gestión {vc.gestion}).',
        'estado': EstadosInstrumento.APROBADO,
    }
    if dry_run:
        return InstrumentoPlanificacion(tipo=tipo, codigo=codigo, **defaults)
    instrumento, _ = InstrumentoPlanificacion.objects.get_or_create(
        tipo=tipo, codigo=codigo, defaults=defaults,
    )
    return instrumento


def _version_para(instrumento, metodologia, dry_run=False):
    defaults = {
        'numero': 1,
        'metodologia': metodologia,
        'etiqueta': 'Importación oficial',
    }
    if dry_run:
        return VersionInstrumento(instrumento=instrumento, **defaults)
    version, _ = VersionInstrumento.objects.get_or_create(
        instrumento=instrumento, numero=1, defaults=defaults,
    )
    return version


def _nodo(version, tipo_nodo, codigo, nombre, padre, dry_run=False):
    defaults = {
        'nombre': nombre,
        'padre': padre,
        'orden': int(codigo.split('.')[-1]),
        'atributos': {'procedencia': 'importacion_oficial'},
    }
    if dry_run:
        return NodoEstrategico(
            version=version, tipo_nodo=tipo_nodo, codigo=codigo, **defaults,
        )
    nodo, _ = NodoEstrategico.objects.get_or_create(
        version=version, tipo_nodo=tipo_nodo, codigo=codigo, defaults=defaults,
    )
    return nodo


def _registrar_en_mapa(modelo, obj, nodo, lote, dry_run=False):
    if dry_run:
        return None
    entry, _ = LegacyMigrationMap.objects.get_or_create(
        app_legacy='codificacion',
        modelo_legacy=modelo._meta.model_name,
        uuid_legacy=obj.pk,
        defaults={
            'lote': lote,
            'checksum': checksum_registro(obj),
        },
    )
    entry.tipo_destino = 'NodoEstrategico'
    entry.uuid_destino = nodo.pk
    entry.estado = LegacyMigrationMap.Estados.MIGRADO
    entry.lote = lote
    entry.save()
    return entry


def importar_marco_superior(lote='pgdesa-pdesa', dry_run=False, gestion=None):
    """Importa los catálogos oficiales de marco superior al kernel V2.

    Retorna un resumen con conteos por instrumento.
    """
    resumen = {
        'lote': lote,
        'dry_run': dry_run,
        'instrumentos': [],
        'nodos_creados': 0,
        'migraciones_registradas': 0,
    }

    versiones_catalogo = VersionCatalogoPlan.objects.select_related('plan').order_by(
        'gestion',
    )
    if gestion:
        versiones_catalogo = versiones_catalogo.filter(gestion=gestion)

    for vc in versiones_catalogo:
        tipo = _tipo_instrumento_para(vc.plan, dry_run)
        metodologia = _metodologia_para(tipo, dry_run)
        tipos_nodo = _tipos_nodo_para(metodologia, dry_run)
        instrumento = _instrumento_para(vc, tipo, dry_run)
        version = _version_para(instrumento, metodologia, dry_run)

        if not dry_run and version.inmutable:
            resumen['instrumentos'].append({
                'codigo': instrumento.codigo,
                'gestion': vc.gestion,
                'estado': 'aprobada_ya',
            })
            continue

        # Jerarquía: eje → componente → sector → resultado
        nodos_por_nivel = {1: {}, 2: {}, 3: {}, 4: {}}
        resumen_nivel = {}
        for modelo_cls, tcodigo, _denom, orden, _hijos, _reglas in NIVELES_MARCO:
            resumen_nivel[orden] = 0
            modelo = MODELOS_LEGACY[modelo_cls]
            for obj in modelo.objects.filter(version_catalogo=vc).order_by('codigo'):
                padre = None
                if orden > 1:
                    padre_legacy = _padre_legacy(obj)
                    padre = nodos_por_nivel[orden - 1].get(padre_legacy.pk)
                codigo_nodo = (
                    obj.codigo if orden == 1
                    else f'{padre.codigo}.{obj.codigo}' if padre
                    else obj.codigo
                )
                nodo = _nodo(
                    version, tipos_nodo[tcodigo], codigo_nodo,
                    obj.denominacion, padre, dry_run,
                )
                if not dry_run:
                    nodo.save()
                    _registrar_en_mapa(modelo, obj, nodo, lote, dry_run)
                    resumen['migraciones_registradas'] += 1
                nodos_por_nivel[orden][obj.pk] = nodo
                resumen['nodos_creados'] += 1
                resumen_nivel[orden] += 1

        if not dry_run and not version.inmutable:
            version.aprobar(
                usuario=None,
                norma=vc.norma_aprobacion or 'Importación oficial',
            )

        resumen['instrumentos'].append({
            'codigo': instrumento.codigo,
            'gestion': vc.gestion,
            'version': version.numero,
            'nodos': sum(resumen_nivel.values()),
            'estado': version.estado,
        })

    return resumen


def _padre_legacy(obj):
    """Nodo legacy padre del objeto (eje del componente, etc.)."""
    for field_name in ('eje', 'componente', 'sector'):
        if hasattr(obj, field_name):
            return getattr(obj, field_name)
    return None
