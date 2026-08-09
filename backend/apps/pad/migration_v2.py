"""Adaptador de migración del PAD al kernel V2 (WP-07 / plan maestro §FASE 5).

Importa la jerarquía PAD legacy (PoliticaPAD → LineamientoEstrategico →
ResultadoTerritorial → ProductoTerritorial) como NodoEstrategico del kernel
V2, migra ArticulacionSIPEB a VinculoEstrategico y reporta duplicidades con
el PAD de `articulacion` para su resolución por código + versión + significado.

Reglas (ADR-004):
- Idempotente; nunca sobrescribe versiones aprobadas.
- Cada gestión crea su instrumento PAD-{gestion} aprobado e inmutable.
- Trazabilidad completa en LegacyMigrationMap.
"""
from datetime import date

from apps.core.migration_audit import checksum_registro
from apps.core.models import LegacyMigrationMap
from apps.planificacion.models_v2 import (
    EstadosInstrumento,
    InstrumentoPlanificacion,
    NodoEstrategico,
    TipoInstrumento,
    TipoNodoEstrategico,
    TipoVinculoEstrategico,
    VersionInstrumento,
    VersionMetodologia,
    VinculoEstrategico,
)

NIVELES_PAD = [
    ('PoliticaPAD', 'POLITICA', 'Política', 1, True),
    ('LineamientoEstrategico', 'LINEAMIENTO', 'Lineamiento', 2, True),
    ('ResultadoTerritorial', 'RESULTADO', 'Resultado', 3, True),
    ('ProductoTerritorial', 'PRODUCTO', 'Producto', 4, False),
]

# Vínculos PAD → marco superior (Matriz B / SIPEB)
VINCULOS_MARCO = [
    ('ARTICULA-EJE', 'EJE', 'eje', 'cod_eje_pgdesa'),
    ('ARTICULA-COMP', 'COMP', 'componente', 'cod_componente_pdesa'),
    ('ARTICULA-SECTOR', 'SECTOR', 'sector', 'cod_sector'),
    ('ARTICULA-RS', 'RS', 'resultado sectorial', 'cod_resultado_pds'),
]


def _tipo_instrumento_pad(dry_run=False):
    defaults = {
        'nombre': 'Plan Anual de Desarrollo',
        'nivel': 'territorial',
        'horizonte_anios': 5,
        'entidad_emisora': 'GAM Sacaba',
    }
    if dry_run:
        return TipoInstrumento(codigo='PAD', **defaults)
    tipo, _ = TipoInstrumento.objects.get_or_create(
        codigo='PAD', defaults=defaults,
    )
    return tipo


def _metodologia_pad(tipo, dry_run=False):
    defaults = {
        'nombre': 'Metodología PAD municipal',
        'tipo_instrumento': tipo,
        'version': '1.0.0',
        'estado': 'vigente',
        'fuente_oficial': 'Metodología municipal de formulación PAD',
    }
    if dry_run:
        return VersionMetodologia(codigo='MET-PAD', **defaults)
    metodologia, _ = VersionMetodologia.objects.get_or_create(
        codigo='MET-PAD', defaults=defaults,
    )
    return metodologia


def _tipos_nodo_pad(metodologia, dry_run=False):
    tipos = {}
    for _modelo, codigo, denominacion, orden, hijos in NIVELES_PAD:
        defaults = {
            'denominacion': denominacion,
            'nivel_orden': orden,
            'permite_hijos': hijos,
            'reglas_codigo': 'código por metodología municipal',
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


def _padres_legacy(obj):
    for field_name in ('politica', 'lineamiento', 'resultado'):
        if hasattr(obj, field_name):
            return getattr(obj, field_name)
    return None


def importar_pad(lote='pad', dry_run=False, gestion=None, con_vinculos=True):
    """Importa la jerarquía PAD legacy al kernel V2.

    Los vínculos SIPEB (Matriz B) se crean ANTES de aprobar la versión,
    preservando la inmutabilidad de versiones aprobadas (ADR-004).
    """
    from apps.pad.models import (
        LineamientoEstrategico,
        PoliticaPAD,
        ProductoTerritorial,
        ResultadoTerritorial,
    )

    resumen = {
        'lote': lote,
        'dry_run': dry_run,
        'instrumentos': [],
        'nodos_creados': 0,
        'migraciones_registradas': 0,
        'vinculos_sipeb': 0,
        'vinculos_pendientes': 0,
    }

    tipo = _tipo_instrumento_pad(dry_run)
    metodologia = _metodologia_pad(tipo, dry_run)
    tipos_nodo = _tipos_nodo_pad(metodologia, dry_run)

    gestiones = list(
        PoliticaPAD.objects.values_list('gestion', flat=True).distinct().order_by()
    )
    if gestion:
        gestiones = [g for g in gestiones if g == gestion]

    for g in gestiones:
        instrumento, version = _instrumento_version(tipo, metodologia, g, dry_run)
        if not dry_run and version.inmutable:
            resumen['instrumentos'].append({
                'codigo': instrumento.codigo, 'gestion': g,
                'estado': 'aprobada_ya',
            })
            continue

        # Niveles con padre por gestión
        niveles = {}
        resumen_gestion = {}
        for modelo_cls, tcodigo, _denom, orden, _hijos in NIVELES_PAD:
            modelo = {
                'PoliticaPAD': PoliticaPAD,
                'LineamientoEstrategico': LineamientoEstrategico,
                'ResultadoTerritorial': ResultadoTerritorial,
                'ProductoTerritorial': ProductoTerritorial,
            }[modelo_cls]
            niveles[orden] = {}
            resumen_gestion[orden] = 0
            for obj in modelo.objects.filter(gestion=g).order_by('codigo'):
                padre = None
                if orden > 1:
                    padre_legacy = _padres_legacy(obj)
                    padre = niveles[orden - 1].get(padre_legacy.pk)
                codigo_nodo = (
                    obj.codigo if orden == 1
                    else f'{padre.codigo}.{obj.codigo}' if padre
                    else obj.codigo
                )
                nodo = _nodo_pad(
                    version, tipos_nodo[tcodigo], codigo_nodo,
                    obj.nombre if hasattr(obj, 'nombre') else str(obj.nombre),
                    padre, _atributos_extra(obj), dry_run,
                )
                if not dry_run:
                    nodo.save()
                    _registrar_mapa(modelo, obj, nodo, lote, 'NodoEstrategico', dry_run)
                    resumen['migraciones_registradas'] += 1
                niveles[orden][obj.pk] = nodo
                resumen['nodos_creados'] += 1
                resumen_gestion[orden] += 1

        # Vínculos SIPEB antes de aprobar (inmutabilidad de versiones)
        if con_vinculos:
            parcial = _importar_vinculos(
                version, g, f'{lote}-sipeb', dry_run,
            )
            resumen['vinculos_sipeb'] += parcial['vinculos']
            resumen['vinculos_pendientes'] += parcial['sin_marco']

        if not dry_run and not version.inmutable:
            version.aprobar(usuario=None, norma='Migración PAD V2')

        resumen['instrumentos'].append({
            'codigo': instrumento.codigo,
            'gestion': g,
            'version': version.numero,
            'nodos': sum(resumen_gestion.values()),
            'estado': version.estado,
        })

    return resumen


def _instrumento_version(tipo, metodologia, gestion, dry_run):
    codigo = f'PAD-{gestion}'
    defaults = {
        'nombre': f'PAD Municipal {gestion}',
        'periodo_inicio': gestion,
        'periodo_fin': gestion + 4,
        'ambito': 'municipal',
        'descripcion': f'Importado de modelos legacy PAD (gestión {gestion}).',
        'estado': EstadosInstrumento.APROBADO,
    }
    if dry_run:
        instrumento = InstrumentoPlanificacion(tipo=tipo, codigo=codigo, **defaults)
        version = VersionInstrumento(
            instrumento=instrumento, numero=1, metodologia=metodologia,
            etiqueta='Migración PAD',
        )
        return instrumento, version
    instrumento, _ = InstrumentoPlanificacion.objects.get_or_create(
        tipo=tipo, codigo=codigo, defaults=defaults,
    )
    version, _ = VersionInstrumento.objects.get_or_create(
        instrumento=instrumento, numero=1,
        defaults={'metodologia': metodologia, 'etiqueta': 'Migración PAD'},
    )
    return instrumento, version


def _atributos_extra(obj):
    atributos = {}
    for campo in (
        'indicador', 'formula', 'linea_base', 'meta_2030', 'estado',
        'presupuesto_total_pad', 'cuenta_con_financiamiento',
        'territorializacion', 'responsable',
    ):
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if valor is not None and valor != '':
                atributos[campo] = str(valor)
    return atributos


def _nodo_pad(version, tipo_nodo, codigo, nombre, padre, atributos, dry_run):
    defaults = {
        'nombre': nombre,
        'padre': padre,
        'atributos': atributos,
        'orden': 0,
    }
    if dry_run:
        return NodoEstrategico(
            version=version, tipo_nodo=tipo_nodo, codigo=codigo, **defaults,
        )
    nodo, _ = NodoEstrategico.objects.get_or_create(
        version=version, tipo_nodo=tipo_nodo, codigo=codigo, defaults=defaults,
    )
    return nodo


def _registrar_mapa(modelo, obj, destino, lote, tipo_destino, dry_run):
    if dry_run:
        return
    entry, _ = LegacyMigrationMap.objects.get_or_create(
        app_legacy='pad',
        modelo_legacy=modelo._meta.model_name,
        uuid_legacy=obj.pk,
        defaults={'lote': lote, 'checksum': checksum_registro(obj)},
    )
    entry.tipo_destino = tipo_destino
    entry.uuid_destino = destino.pk
    entry.estado = LegacyMigrationMap.Estados.MIGRADO
    entry.lote = lote
    entry.save()


def _importar_vinculos(version, gestion, lote, dry_run):
    """Crea los vínculos SIPEB de una gestión sobre la versión dada.

    El nodo origen (RESULTADO) puede vivir en otra versión del mismo
    instrumento (articulación entre versiones); el vínculo se registra en
    la versión propietaria recibida.
    """
    from apps.pad.models import ArticulacionSIPEB

    parcial = {'vinculos': 0, 'sin_marco': 0}
    for sip in ArticulacionSIPEB.objects.filter(
        gestion=gestion,
    ).select_related('resultado'):
        resultado_nodo = NodoEstrategico.objects.filter(
            version__instrumento=version.instrumento,
            tipo_nodo__codigo='RESULTADO',
            codigo=_codigo_completo(sip.resultado),
        ).first()
        if not resultado_nodo:
            continue
        marco = _nodos_marco(gestion)
        for codigo_tipo, destino_tipo_codigo, _denom, campo in VINCULOS_MARCO:
            codigo_marco = getattr(sip, campo, '')
            if not codigo_marco:
                continue
            destino = _buscar_nodo_marco(marco, destino_tipo_codigo, codigo_marco)
            if not destino:
                parcial['sin_marco'] += 1
                continue
            justificacion = _justificacion_compromisos(sip)
            if dry_run:
                parcial['vinculos'] += 1
                continue
            tipo_vinculo = _tipo_vinculo_pad(
                version.metodologia, resultado_nodo.tipo_nodo, destino.tipo_nodo,
                codigo_tipo, _denom,
            )
            vinculo, created = VinculoEstrategico.objects.get_or_create(
                version=version,
                origen=resultado_nodo,
                destino=destino,
                tipo=tipo_vinculo,
                defaults={'justificacion': justificacion},
            )
            if created:
                _registrar_mapa(
                    ArticulacionSIPEB, sip, vinculo, lote,
                    'VinculoEstrategico', dry_run,
                )
                parcial['vinculos'] += 1
    return parcial


def importar_articulaciones_sipeb(lote='pad-sipeb', dry_run=False, gestion=None):
    """Migra ArticulacionSIPEB (Matriz B) a VinculoEstrategico PAD→marco.

    Si la versión del PAD ya está aprobada (inmutable), los vínculos se
    registran en una versión nueva del instrumento (v2 'Articulación SIPEB').
    """
    from apps.pad.models import ArticulacionSIPEB

    resumen = {
        'lote': lote,
        'dry_run': dry_run,
        'vinculos_creados': 0,
        'sin_marco': 0,
        'version_creada': False,
    }

    gestiones = list(
        ArticulacionSIPEB.objects.values_list(
            'gestion', flat=True,
        ).distinct().order_by()
    )
    if gestion:
        gestiones = [g for g in gestiones if g == gestion]

    for g in gestiones:
        instrumento = InstrumentoPlanificacion.objects.filter(
            tipo__codigo='PAD', codigo=f'PAD-{g}',
        ).first()
        if not instrumento:
            resumen['sin_marco'] += 1
            continue
        version = instrumento.versiones.order_by('numero').last()
        if version and version.inmutable:
            from apps.planificacion.models_v2 import VersionMetodologia
            metodologia = VersionMetodologia.objects.filter(
                codigo='MET-PAD',
            ).first()
            version = VersionInstrumento(
                instrumento=instrumento,
                numero=(version.numero + 1),
                metodologia=metodologia,
                etiqueta='Articulación SIPEB',
            )
            if not dry_run:
                version.save(force_insert=True)
            resumen['version_creada'] = True
        if not version:
            continue
        parcial = _importar_vinculos(version, g, lote, dry_run)
        resumen['vinculos_creados'] += parcial['vinculos']
        resumen['sin_marco'] += parcial['sin_marco']

    return resumen


def _tipo_vinculo_pad(metodologia, tipo_origen, tipo_destino, codigo, denominacion):
    """Tipo de vínculo PAD→marco; se crea perezosamente cuando existe el
    tipo de nodo destino del marco superior (importado en WP-06)."""
    tipo, _ = TipoVinculoEstrategico.objects.get_or_create(
        codigo=codigo,
        metodologia=metodologia,
        defaults={
            'denominacion': f'Articulación PAD → {denominacion}',
            'origen_permitido': tipo_origen,
            'destino_permitido': tipo_destino,
            'requiere_ponderacion': False,
            'requiere_justificacion': False,
        },
    )
    return tipo


def _codigo_completo(obj):
    partes = [obj.codigo]
    actual = _padres_legacy(obj)
    while actual is not None:
        partes.insert(0, actual.codigo)
        actual = _padres_legacy(actual)
    return '.'.join(partes)


def _nodos_marco(gestion):
    instrumentos = InstrumentoPlanificacion.objects.filter(
        tipo__codigo__in=['PGDESA', 'PDESA'],
        codigo__endswith=f'-{gestion}',
    )
    return NodoEstrategico.objects.filter(version__instrumento__in=instrumentos)


def _buscar_nodo_marco(marco_qs, tipo_codigo, codigo_legacy):
    for nodo in marco_qs.filter(tipo_nodo__codigo=tipo_codigo):
        if nodo.codigo == codigo_legacy or nodo.codigo.endswith(f'.{codigo_legacy}'):
            return nodo
    return None


def _justificacion_compromisos(sip):
    partes = []
    for campo, etiqueta in (
        ('cod_ods', 'ODS'), ('cod_meta_ndc', 'NDC'),
        ('cod_principio_ndt', 'NDT'), ('compromisos_3030', '30x30'),
    ):
        valor = getattr(sip, campo, '')
        if valor:
            partes.append(f'{etiqueta}: {valor}')
    return '; '.join(partes)


def comparar_duplicados_pad():
    """Reporte de duplicidades PAD: app `pad` vs app `articulacion`.

    Lectura pura: no escribe. Los duplicados se resuelven por
    código + versión + significado (plan maestro §22.7), nunca por texto.
    """
    from apps.articulacion.models import (
        LineamientoPAD as LineamientoPADArt,
        ProductoPAD as ProductoPADArt,
        ResultadoPAD as ResultadoPADArt,
    )
    from apps.pad.models import (
        LineamientoEstrategico,
        ProductoTerritorial,
        ResultadoTerritorial,
    )

    def _norm(texto):
        return ' '.join(str(texto or '').strip().lower().split())

    def _comparar(pad_qs, art_qs, campo_pad, campo_art):
        codigos_pad = set(
            pad_qs.values_list(campo_pad, flat=True),
        )
        codigos_art = set(
            art_qs.values_list(campo_art, flat=True),
        )
        comunes = codigos_pad & codigos_art
        pad_names = {
            c: _norm(getattr(o, 'nombre'))
            for o in pad_qs if (c := getattr(o, campo_pad))
        }
        art_names = {
            c: _norm(getattr(o, 'denominacion'))
            for o in art_qs if (c := getattr(o, campo_art))
        }
        coinciden = [
            c for c in comunes
            if pad_names.get(c) and pad_names[c] == art_names.get(c)
        ]
        return {
            'pad': len(codigos_pad),
            'articulacion': len(codigos_art),
            'coinciden_codigo_y_nombre': len(coinciden),
            'solo_pad': sorted(codigos_pad - codigos_art)[:20],
            'solo_articulacion': sorted(codigos_art - codigos_pad)[:20],
        }

    return {
        'lineamientos': _comparar(
            LineamientoEstrategico.objects.all(),
            LineamientoPADArt.objects.all(),
            'codigo', 'codigo',
        ),
        'resultados': _comparar(
            ResultadoTerritorial.objects.all(),
            ResultadoPADArt.objects.all(),
            'codigo', 'codigo_resultado',
        ),
        'productos': _comparar(
            ProductoTerritorial.objects.all(),
            ProductoPADArt.objects.all(),
            'codigo', 'codigo_producto',
        ),
    }
