from rest_framework.permissions import BasePermission

CODIGO_ROLES = {
    'SUPERADMIN': 'superadmin',
    'TECNICO_ADMIN': 'tecnico_admin',
    'PLANIFICADOR': 'planificador',
    'EVALUADOR': 'evaluador',
    'JEFE_UE': 'jefe_ue',
    'DIRECTOR': 'director',
    'OPERADOR': 'operador',
    'BENEFICIARIO': 'beneficiario',
    'PROVEEDOR': 'proveedor',
    'CONTROL_INTERNO': 'control_interno',
    'CONTROL_SOCIAL': 'control_social',
}

TRANSICIONES_WORKFLOW = {
    'borrador': {'enviar': ['operador', 'planificador', 'jefe_ue']},
    'enviado': {'aprobar': ['tecnico_admin', 'director'], 'observar': ['tecnico_admin', 'director']},
    'en_revision': {'aprobar': ['tecnico_admin', 'director'], 'observar': ['tecnico_admin', 'director']},
    'observado': {'subsanar': ['operador', 'planificador']},
    'aprobado': {'consolidar': ['superadmin']},
    'consolidado': {'aprobar_final': ['superadmin', 'director']},
}


def _user_has_role(user, *role_codes):
    if user.is_superuser:
        return True
    if not user.is_active:
        return False
    return user.roles.filter(codigo__in=role_codes, activo=True).exists()


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(request.user, CODIGO_ROLES['SUPERADMIN'])


class IsTecnicoAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
        )


class IsPlanificador(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
            CODIGO_ROLES['PLANIFICADOR'],
        )


class IsEvaluador(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
            CODIGO_ROLES['EVALUADOR'],
        )


class IsJefeUE(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
            CODIGO_ROLES['JEFE_UE'],
        )


class IsDirector(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
            CODIGO_ROLES['DIRECTOR'],
        )


class IsOperador(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
            CODIGO_ROLES['OPERADOR'],
        )


class IsBeneficiario(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['BENEFICIARIO'],
        )


class IsProveedor(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['PROVEEDOR'],
        )


class IsControlInterno(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['CONTROL_INTERNO'],
        )


class IsControlSocial(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['CONTROL_SOCIAL'],
        )


class RoleBasedPermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return _user_has_role(request.user, *self.allowed_roles)

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return _user_has_role(request.user, *self.allowed_roles)


class InstitutionPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        user_institutions = set(
            request.user.unidades_responsable.values_list('id', flat=True)
        )
        user_asignaciones = set(
            request.user.asignaciones_unidad.filter(
                activo=True
            ).values_list('unidad__id', flat=True)
        )
        all_user_units = user_institutions | user_asignaciones
        obj_institution = getattr(obj, 'institucion_id', None)
        if obj_institution is None:
            obj_unidad = getattr(obj, 'unidad_id', None)
            if obj_unidad is not None:
                return obj_unidad in all_user_units
            obj_ue = getattr(obj, 'ue_id', None)
            if obj_ue is not None:
                return request.user.unidades_ejecutoras.filter(id=obj_ue).exists()
            return True
        return obj_institution in all_user_units


class UnidadEjecutoraPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if _user_has_role(request.user, CODIGO_ROLES['SUPERADMIN'], CODIGO_ROLES['TECNICO_ADMIN']):
            return True
        ue_id = getattr(obj, 'ue_id', None)
        if ue_id is not None:
            return request.user.unidades_ejecutoras.filter(id=ue_id).exists()
        unidad_id = getattr(obj, 'unidad_id', None)
        if unidad_id is not None:
            return request.user.asignaciones_unidad.filter(
                unidad__id=unidad_id, activo=True
            ).exists()
        return True


class GestionPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        gestion = view.kwargs.get('gestion') or request.query_params.get('gestion')
        if gestion is None:
            return True
        from apps.gestion.models import GestionFiscal
        gestion_obj = GestionFiscal.objects.filter(anio=gestion).first()
        if gestion_obj is None:
            return False
        if gestion_obj.estado in ('archivada', 'cerrada') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            return False
        if _user_has_role(request.user, CODIGO_ROLES['SUPERADMIN'], CODIGO_ROLES['TECNICO_ADMIN']):
            return True
        if gestion_obj.estado == 'preparacion':
            return _user_has_role(
                request.user,
                CODIGO_ROLES['SUPERADMIN'],
                CODIGO_ROLES['TECNICO_ADMIN'],
            )
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        gestion = getattr(obj, 'gestion', None)
        if gestion is None:
            return True
        from apps.gestion.models import GestionFiscal
        gestion_obj = GestionFiscal.objects.filter(anio=gestion).first()
        if gestion_obj is None:
            return False
        if gestion_obj.estado in ('archivada', 'cerrada') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            return False
        return True


class ReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
        )

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return _user_has_role(
            request.user,
            CODIGO_ROLES['SUPERADMIN'],
            CODIGO_ROLES['TECNICO_ADMIN'],
        )


class OwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if _user_has_role(request.user, CODIGO_ROLES['SUPERADMIN'], CODIGO_ROLES['TECNICO_ADMIN']):
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if _user_has_role(request.user, CODIGO_ROLES['SUPERADMIN'], CODIGO_ROLES['TECNICO_ADMIN']):
            return True
        owner_fields = [
            'created_by', 'responsable', 'solicitado_por',
            'subido_por', 'usuario', 'revisado_por',
        ]
        for field in owner_fields:
            owner = getattr(obj, field, None)
            if owner is not None and owner.pk == request.user.pk:
                return True
        return False


class WorkflowPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        accion = request.data.get('accion') or view.action
        estado_actual = request.data.get('estado_actual')
        if accion is None or estado_actual is None:
            return True
        transiciones = TRANSICIONES_WORKFLOW.get(estado_actual, {})
        roles_permitidos = transiciones.get(accion, [])
        if not roles_permitidos:
            return False
        return _user_has_role(request.user, *roles_permitidos)

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if _user_has_role(request.user, CODIGO_ROLES['SUPERADMIN'], CODIGO_ROLES['TECNICO_ADMIN']):
            return True
        estado_actual = getattr(obj, 'estado', None) or getattr(obj, 'status', None)
        accion = request.data.get('accion') or view.action
        if estado_actual is None or accion is None:
            return True
        transiciones = TRANSICIONES_WORKFLOW.get(estado_actual, {})
        roles_permitidos = transiciones.get(accion, [])
        if not roles_permitidos:
            return False
        return _user_has_role(request.user, *roles_permitidos)
