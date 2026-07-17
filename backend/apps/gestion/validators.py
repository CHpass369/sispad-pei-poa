def validar_gestion_unica(anio, exclude_id=None):
    from apps.gestion.models import GestionFiscal
    qs = GestionFiscal.objects.filter(anio=anio)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        return {
            'valido': False,
            'mensaje': 'Ya existe una gestion para el anio ' + str(anio) + '.',
        }
    return {'valido': True, 'mensaje': 'Gestion unica.'}


def validar_fechas_gestion_consistentes(gestion):
    errores = []
    if gestion.anio_fin_plurianual and gestion.anio_inicio_plurianual:
        if gestion.anio_fin_plurianual <= gestion.anio_inicio_plurianual:
            errores.append('El anio final del plurianual debe ser posterior al inicial.')
        if gestion.anio < gestion.anio_inicio_plurianual or gestion.anio > gestion.anio_fin_plurianual:
            errores.append('El anio de gestion debe estar dentro del horizonte plurianual.')
    if gestion.fecha_apertura and gestion.fecha_cierre:
        if gestion.fecha_cierre <= gestion.fecha_apertura:
            errores.append('La fecha de cierre debe ser posterior a la de apertura.')
    return {'valido': len(errores) == 0, 'errores': errores}
