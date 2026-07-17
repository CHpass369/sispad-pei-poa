from decimal import Decimal


def validar_ponderaciones_suma_100(items):
    total = sum(Decimal(str(item.get('ponderacion', 0))) for item in items)
    if total != Decimal('100'):
        return {
            'valido': False,
            'mensaje': f'Las ponderaciones suman {total}%, se requiere exactamente 100%.',
            'total': total,
        }
    return {'valido': True, 'mensaje': 'Ponderaciones correctas', 'total': total}


def validar_fechas_consistentes(fecha_inicio, fecha_fin):
    if not fecha_inicio or not fecha_fin:
        return {
            'valido': False,
            'mensaje': 'Las fechas de inicio y fin son requeridas.',
        }
    if fecha_inicio >= fecha_fin:
        return {
            'valido': False,
            'mensaje': f'La fecha de inicio ({fecha_inicio}) debe ser anterior a la fecha de fin ({fecha_fin}).',
        }
    return {'valido': True, 'mensaje': 'Fechas consistentes'}


def validar_codigo_unico(modelo, codigo, gestion, exclude_id=None):
    qs = modelo.objects.filter(codigo=codigo, gestion=gestion)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    if qs.exists():
        return {
            'valido': False,
            'mensaje': f'Ya existe un registro con código "{codigo}" en la gestión {gestion}.',
        }
    return {'valido': True, 'mensaje': 'Código único'}


def validar_meta_no_negativa(valor):
    if valor is None:
        return {
            'valido': False,
            'mensaje': 'El valor de la meta es requerido.',
        }
    if Decimal(str(valor)) < Decimal('0'):
        return {
            'valido': False,
            'mensaje': f'El valor de la meta ({valor}) no puede ser negativo.',
        }
    return {'valido': True, 'mensaje': 'Meta válida'}


def validar_lineas_igual_total(lineas, total_presupuesto):
    suma_lineas = sum(Decimal(str(l.get('monto', 0))) for l in lineas)
    total = Decimal(str(total_presupuesto))
    if suma_lineas != total:
        return {
            'valido': False,
            'mensaje': (
                f'La suma de las líneas presupuestarias (Bs {suma_lineas}) '
                f'no coincide con el total (Bs {total}).'
            ),
            'diferencia': total - suma_lineas,
        }
    return {'valido': True, 'mensaje': 'Líneas coinciden con el total', 'diferencia': Decimal('0')}


def validar_sin_circulares(origen, destino, model):
    visitados = set()
    actual = destino
    while actual is not None:
        if actual == origen:
            return {
                'valido': False,
                'mensaje': 'Se detectó una referencia circular.',
            }
        if actual.pk in visitados:
            return {
                'valido': False,
                'mensaje': 'Se detectó una referencia circular.',
            }
        visitados.add(actual.pk)
        padre_field = getattr(model, '_padre_field', 'padre')
        actual = getattr(actual, padre_field, None)
    return {'valido': True, 'mensaje': 'Sin referencias circulares'}


def validar_accion_poa_sin_pei(accion):
    if hasattr(accion, 'accion_mediano_plazo') and accion.accion_mediano_plazo:
        nodo = accion.accion_mediano_plazo.nodo_planificacion
        if nodo and nodo.plan:
            return {'valido': True, 'mensaje': 'Acción POA articulada a PEI'}
    return {
        'valido': False,
        'mensaje': 'La acción POA debe estar articulada a una acción de mediano plazo del PEI.',
    }


def validar_accion_pei_sin_pad(accion_pei):
    if hasattr(accion_pei, 'nodo_planificacion') and accion_pei.nodo_planificacion:
        nodo = accion_pei.nodo_planificacion
        if nodo.plan and nodo.plan.tipo == 'pei':
            from apps.pad.models import PlanAnual
            articulado = PlanAnual.objects.filter(
                nodos_plan__nodo_planificacion__plan__tipo='pei'
            ).exists()
            if articulado:
                return {'valido': True, 'mensaje': 'Acción PEI articulada a PAD'}
    return {
        'valido': False,
        'mensaje': 'La acción PEI debe estar articulada a un Plan Anual de Desarrollo (PAD).',
    }


def validar_meta_sin_indicador(meta):
    from apps.indicadores.models import Indicador
    indicadores = Indicador.objects.filter(meta_asociada=meta)
    if not indicadores.exists():
        return {
            'valido': False,
            'mensaje': f'La meta "{meta}" no tiene indicadores asociados.',
        }
    return {'valido': True, 'mensaje': 'Meta con indicadores'}


def validar_indicador_sin_unidad(indicador):
    if not indicador.unidad_medida:
        return {
            'valido': False,
            'mensaje': f'El indicador "{indicador}" no tiene unidad de medida definida.',
        }
    return {'valido': True, 'mensaje': 'Indicador con unidad de medida'}


def validar_actividad_fuera_periodo(actividad, gestion):
    if hasattr(actividad, 'gestion'):
        if actividad.gestion != gestion:
            return {
                'valido': False,
                'mensaje': (
                    f'La actividad "{actividad}" pertenece a la gestión {actividad.gestion} '
                    f'y no puede ejecutarse en la gestión {gestion}.'
                ),
            }
    if hasattr(actividad, 'fecha_inicio') and hasattr(actividad, 'fecha_fin'):
        if actividad.fecha_inicio and actividad.fecha_fin:
            from datetime import date
            gestion_inicio = date(gestion, 1, 1)
            gestion_fin = date(gestion, 12, 31)
            if actividad.fecha_inicio < gestion_inicio or actividad.fecha_fin > gestion_fin:
                return {
                    'valido': False,
                    'mensaje': (
                        f'Las fechas de la actividad "{actividad}" están fuera '
                        f'del período de la gestión {gestion}.'
                    ),
                }
    return {'valido': True, 'mensaje': 'Actividad dentro del período'}


def validar_presupuesto_mayor_techo(presupuesto, techo):
    if Decimal(str(presupuesto)) > Decimal(str(techo)):
        return {
            'valido': False,
            'mensaje': (
                f'El presupuesto asignado (Bs {presupuesto}) excede '
                f'el techo presupuestario (Bs {techo}).'
            ),
        }
    return {'valido': True, 'mensaje': 'Presupuesto dentro del techo'}


def validar_duplicidad_codigo(modelo, codigo, gestion):
    existe = modelo.objects.filter(codigo=codigo, gestion=gestion).exists()
    if existe:
        return {
            'valido': False,
            'mensaje': f'Ya existe un registro con código "{codigo}" en la gestión {gestion}.',
        }
    return {'valido': True, 'mensaje': 'Código único'}


def validar_proyecto_sisin_obligatorio(proyecto):
    if hasattr(proyecto, 'etapa') and proyecto.etapa in ('inversion', 'cierre', 'operacion'):
        if not getattr(proyecto, 'codigo_sisin', None):
            return {
                'valido': False,
                'mensaje': (
                    f'El proyecto "{proyecto}" está en etapa "{proyecto.get_etapa_display()}" '
                    f'y requiere un código SISIN.'
                ),
            }
    return {'valido': True, 'mensaje': 'Validación SISIN correcta'}


def validar_ejecucion_sin_evidencia_obligatoria(entry):
    if hasattr(entry, 'evidencia_requerida') and entry.evidencia_requerida:
        if not getattr(entry, 'evidencia', None) and not getattr(entry, 'archivo_evidencia', None):
            return {
                'valido': False,
                'mensaje': (
                    f'La entrada de ejecución "{entry}" requiere evidencia adjunta '
                    f'pero no se encontró ningún archivo o enlace.'
                ),
            }
    return {'valido': True, 'mensaje': 'Evidencia validada'}


def validar_modificacion_sin_justificacion(solicitud):
    motivo = getattr(solicitud, 'motivo', None)
    informe = getattr(solicitud, 'informe_tecnico', None)
    if not motivo and not informe:
        return {
            'valido': False,
            'mensaje': (
                'La solicitud de modificación requiere al menos un motivo '
                'o informe técnico que justifique el cambio.'
            ),
        }
    return {'valido': True, 'mensaje': 'Justificación presente'}


def validar_modificacion_sin_documento(solicitud):
    cambios = solicitud.cambios.all() if hasattr(solicitud, 'cambios') else []
    if not cambios:
        return {
            'valido': False,
            'mensaje': (
                'La solicitud de modificación no tiene cambios registrados. '
                'Debe adjuntar al menos un cambio o documento de respaldo.'
            ),
        }
    tiene_documento = False
    if hasattr(solicitud, 'documento_legal') and solicitud.documento_legal:
        tiene_documento = True
    if hasattr(solicitud, 'informe_tecnico') and solicitud.informe_tecnico:
        tiene_documento = True
    if not tiene_documento and not cambios:
        return {
            'valido': False,
            'mensaje': (
                'La solicitud de modificación requiere un documento adjunto '
                '(informe técnico o documento legal).'
            ),
        }
    return {'valido': True, 'mensaje': 'Documentación validada'}


def validar_categoria_programatica_distinta(codigo, objetivo, modelo, exclude_id=None):
    qs = modelo.objects.filter(codigo=codigo)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    for registro in qs:
        obj_existente = getattr(registro, 'objetivo', None) or getattr(registro, 'nombre', None)
        if obj_existente and obj_existente != objetivo:
            return {
                'valido': False,
                'mensaje': (
                    f'Ya existe un registro con código "{codigo}" '
                    f'asociado a un objetivo distinto. '
                    f'Existente: "{obj_existente}", Propuesto: "{objetivo}".'
                ),
            }
    return {'valido': True, 'mensaje': 'Categoría programática consistente'}


def validar_ejecucion_no_negativa(valor):
    if valor is None:
        return {
            'valido': False,
            'mensaje': 'El valor de ejecución es requerido.',
        }
    if Decimal(str(valor)) < Decimal('0'):
        return {
            'valido': False,
            'mensaje': (
                f'El valor de ejecución ({valor}) no puede ser negativo. '
                f'Registre una reducción o reversión en lugar de un valor negativo.'
            ),
        }
    return {'valido': True, 'mensaje': 'Valor de ejecución válido'}


def validar_archivo_tipo_permitido(filename, allowed_types=None):
    if allowed_types is None:
        allowed_types = {
            'application/pdf',
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/msword',
            'application/vnd.ms-excel',
            'application/vnd.ms-powerpoint',
            'text/plain', 'text/csv',
            'application/zip',
            'application/x-dwg', 'application/dxf',
        }

    if not filename:
        return {
            'valido': False,
            'mensaje': 'El nombre del archivo es requerido.',
        }

    import os
    _, ext = os.path.splitext(filename.lower())
    mime_map = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.bmp': 'image/bmp', '.tiff': 'image/tiff', '.tif': 'image/tiff',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.zip': 'application/zip',
        '.dwg': 'application/x-dwg',
        '.dxf': 'application/dxf',
    }

    detected_mime = mime_map.get(ext, 'application/octet-stream')

    if allowed_types and detected_mime not in allowed_types:
        return {
            'valido': False,
            'mensaje': (
                f'El tipo de archivo "{ext}" ({detected_mime}) no está permitido. '
                f'Tipos permitidos: {", ".join(sorted(allowed_types))}'
            ),
        }
    return {'valido': True, 'mensaje': f'Archivo tipo permitido: {detected_mime}'}


def validar_geometria_valida(geometry):
    if geometry is None:
        return {
            'valido': False,
            'mensaje': 'La geometría es requerida.',
        }

    try:
        from django.contrib.gis.geos import GEOSGeometry, GEOSException
    except ImportError:
        return {
            'valido': True,
            'mensaje': 'Validación PostGIS no disponible (django.contrib.gis no instalado)',
        }

    if isinstance(geometry, str):
        try:
            geom = GEOSGeometry(geometry)
        except GEOSException as e:
            return {
                'valido': False,
                'mensaje': f'Geometría inválida: {e}',
            }
    else:
        geom = geometry

    if geom is None or geom.empty:
        return {
            'valido': False,
            'mensaje': 'La geometría está vacía.',
        }

    if not geom.valid:
        from django.contrib.gis.geos import MultiPolygon
        if isinstance(geom, MultiPolygon):
            corrected = geom.make_valid()
            return {
                'valido': True,
                'mensaje': 'Geometría corregida automáticamente (make_valid)',
                'geometria_corregida': corrected,
            }
        return {
            'valido': False,
            'mensaje': f'La geometría no es válida topológicamente: {geom.valid_reason}',
        }

    return {'valido': True, 'mensaje': 'Geometría válida'}
