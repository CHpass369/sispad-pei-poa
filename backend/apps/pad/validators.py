def validar_hierarquia_pad(resultado_id):
    from apps.pad.models import ResultadoTerritorial
    try:
        resultado = ResultadoTerritorial.objects.select_related('lineamiento').get(id=resultado_id)
    except ResultadoTerritorial.DoesNotExist:
        return {'valido': False, 'mensaje': 'Resultado territorial no encontrado.'}
    if resultado.lineamiento is None:
        return {'valido': False, 'mensaje': 'El resultado no tiene lineamiento asociado.'}
    if resultado.lineamiento.politica is None:
        return {'valido': False, 'mensaje': 'El lineamiento no tiene politica asociada.'}
    return {'valido': True, 'mensaje': 'Jerarquia PAD completa.'}


def validar_producto_sin_lineamiento(producto_id):
    from apps.pad.models import ProductoTerritorial
    try:
        producto = ProductoTerritorial.objects.select_related('resultado__lineamiento').get(id=producto_id)
    except ProductoTerritorial.DoesNotExist:
        return {'valido': False, 'mensaje': 'Producto territorial no encontrado.'}
    if producto.resultado is None:
        return {'valido': False, 'mensaje': 'El producto no tiene resultado territorial asociado.'}
    if producto.resultado.lineamiento is None:
        return {'valido': False, 'mensaje': 'El resultado del producto no tiene lineamiento.'}
    return {'valido': True, 'mensaje': 'Producto correctamente vinculado.'}


def validar_programacion_completa(resultado_id=None, producto_id=None):
    from apps.pad.models import ProgramacionAnualPAD
    from decimal import Decimal
    errores = []
    if resultado_id:
        fisica = ProgramacionAnualPAD.objects.filter(
            resultado_id=resultado_id, tipo='fisica'
        )
        financiera = ProgramacionAnualPAD.objects.filter(
            resultado_id=resultado_id, tipo='financiera'
        )
        if not fisica.exists():
            errores.append('El resultado no tiene programacion fisica.')
        if not financiera.exists():
            errores.append('El resultado no tiene programacion financiera.')
    if producto_id:
        fisica = ProgramacionAnualPAD.objects.filter(
            producto_id=producto_id, tipo='fisica'
        )
        financiera = ProgramacionAnualPAD.objects.filter(
            producto_id=producto_id, tipo='financiera'
        )
        if not fisica.exists():
            errores.append('El producto no tiene programacion fisica.')
        if not financiera.exists():
            errores.append('El producto no tiene programacion financiera.')
    return {'valido': len(errores) == 0, 'errores': errores}
