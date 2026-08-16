from decimal import Decimal


def validar_nombre_corto(nombre, etiqueta):
    """Retorna el mensaje de error si el nombre es demasiado corto, o None."""
    if nombre and len(str(nombre).strip()) < 3:
        return f'El nombre {etiqueta} es demasiado corto.'
    return None


def validar_valor_no_negativo(value, etiqueta):
    """Retorna el mensaje de error si el valor es negativo, o None."""
    if value is not None and value < 0:
        return f'{etiqueta} no puede ser negativa'
    return None


def validar_ponderaciones_suma_100(items):
    total = sum(Decimal(str(item.get('ponderacion', 0))) for item in items)
    if total != Decimal('100'):
        return {
            'valido': False,
            'mensaje': f'Las ponderaciones suman {total}%, se requiere exactamente 100%.',
            'total': total,
        }
    return {'valido': True, 'mensaje': 'Ponderaciones correctas', 'total': total}


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
