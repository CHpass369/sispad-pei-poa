def validar_version_unico(plan_id, version_number, exclude_id=None):
    from apps.planificacion.models import PlanVersion
    qs = PlanVersion.objects.filter(plan_id=plan_id, version_number=version_number)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        return {
            'valido': False,
            'mensaje': 'Ya existe la version ' + str(version_number) + ' para este plan.',
        }
    return {'valido': True, 'mensaje': 'Version unica.'}


def validar_plan_sin_aprobar(plan):
    from apps.planificacion.models import PlanVersion
    version_aprobada = PlanVersion.objects.filter(
        plan=plan, status='aprobado'
    ).first()
    if version_aprobada:
        return {
            'valido': False,
            'mensaje': 'El plan ya tiene una version aprobada (v' + str(version_aprobada.version_number) + ').',
        }
    return {'valido': True, 'mensaje': 'El plan no tiene versiones aprobadas.'}


def validar_fechas_plan(gestion_inicio, gestion_fin):
    errores = []
    if gestion_inicio > gestion_fin:
        errores.append('La gestion de inicio debe ser menor o igual a la de fin.')
    if gestion_fin - gestion_inicio > 20:
        errores.append('El horizonte del plan no puede exceder 20 anios.')
    return {'valido': len(errores) == 0, 'errores': errores}
