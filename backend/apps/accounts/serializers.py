from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from rest_framework import serializers

from apps.gestion.models import GestionFiscal
from apps.organizacion.models import UnidadOrganizacional

from .models import AlcanceOrganizacional, Capacidad, Usuario, Rol
from .permissions import listar_capacidades
from .services import (
    CODIGOS_ROLES_BASE,
    SCOPES_FIJOS_ROLES_SISTEMA,
    SISTEMAS_CAPACIDADES_ASIGNABLES,
    puede_administrar_asignacion_rol,
    sistema_efectivo_capacidad,
    sistemas_administrables,
    sistemas_de_rol,
    sistemas_efectivos_de_rol,
    unidades_organizacionales_disponibles_registro,
)


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'activo']


class UsuarioSerializer(serializers.ModelSerializer):
    roles_detalle = RolSerializer(source='roles', many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 'cargo', 'telefono',
            'roles', 'roles_detalle', 'estado', 'activo', 'is_staff', 'is_superuser',
            'debe_cambiar_password', 'last_login', 'date_joined',
        ]
        read_only_fields = ['estado', 'is_superuser', 'last_login', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        user = Usuario.objects.create_user(**validated_data)
        user.roles.set(roles)
        return user

    def update(self, instance, validated_data):
        roles = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            instance.roles.set(roles)
        return instance


# --- F3a: registro público y aprobación administrativa ----------------------
#
# Contrato del registro (#17): el solicitante solo elige datos personales,
# cargo, UO y contraseña. NUNCA rol, capacidades, sistema ni scope: esos los
# define el administrador al aprobar (#18). Por eso estos serializers son
# separados de UsuarioSerializer (que expone roles/is_staff).


class RegistroPublicoSerializer(serializers.Serializer):
    """Alta pública de usuario: queda PENDIENTE hasta aprobación admin."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    cargo = serializers.CharField(max_length=200, required=False, allow_blank=True)
    unidad_organizacional_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        value = Usuario.objects.normalize_email(value)
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Ya existe una cuenta registrada con este correo.'
            )
        return value

    def validate_unidad_organizacional_id(self, value):
        if not unidades_organizacionales_disponibles_registro().filter(
            id=value,
        ).exists():
            raise serializers.ValidationError(
                'La unidad organizacional no está disponible.'
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': ['Las contraseñas no coinciden.'],
            })
        try:
            candidato = Usuario(
                email=attrs['email'],
                first_name=attrs['first_name'],
                last_name=attrs['last_name'],
            )
            validate_password(attrs['password'], user=candidato)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
        return attrs


class UnidadOrganizacionalPublicaSerializer(serializers.ModelSerializer):
    """Contrato mínimo para seleccionar una UO durante el registro."""

    padre = serializers.UUIDField(source='padre_id', read_only=True)

    class Meta:
        model = UnidadOrganizacional
        fields = ['id', 'codigo', 'nombre', 'sigla', 'padre']


class AprobacionSerializer(serializers.Serializer):
    """Datos que el administrador define al aprobar una solicitud (#18)."""

    unidad_organizacional_id = serializers.UUIDField()
    rol_codigo = serializers.CharField(max_length=50)
    sistema = serializers.ChoiceField(choices=['sis_pe', 'sis_poa'])
    scope_type = serializers.ChoiceField(
        choices=AlcanceOrganizacional.SCOPE_TYPE_CHOICES,
    )
    fiscal_year_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_unidad_organizacional_id(self, value):
        if not UnidadOrganizacional.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'La unidad organizacional no existe.'
            )
        return value

    def validate_fiscal_year_id(self, value):
        if value is not None and not GestionFiscal.objects.filter(id=value).exists():
            raise serializers.ValidationError('La gestión fiscal no existe.')
        return value


class SolicitudSerializer(serializers.ModelSerializer):
    """Fila del listado de solicitudes PENDIENTE (sin datos sensibles)."""

    unidad_solicitada = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 'cargo',
            'date_joined', 'unidad_solicitada',
        ]

    def get_unidad_solicitada(self, obj):
        """UO pedida en el registro (alcance-trazo rol=None, activo=False)."""
        alcance = next(
            (a for a in obj.alcances_organizacionales.all() if a.rol_id is None),
            None,
        )
        if alcance is None:
            return None
        return {'id': str(alcance.unidad_id), 'nombre': alcance.unidad.nombre}


# --- F3b1: lectura y actualización administrativa de usuarios ---------------


class UsuarioAdminFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    organizational_unit = serializers.UUIDField(required=False)
    role = serializers.CharField(required=False, allow_blank=False)
    system = serializers.ChoiceField(
        choices=['sis_pe', 'sis_poa'],
        required=False,
    )
    state = serializers.ChoiceField(
        choices=Usuario.ESTADO_CHOICES,
        required=False,
    )


class UsuarioAdminUpdateSerializer(serializers.ModelSerializer):
    """PATCH estricto: F3b2 administrará roles, permisos y alcances."""

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'cargo', 'telefono']
        extra_kwargs = {
            field: {'required': False}
            for field in fields
        }

    def to_internal_value(self, data):
        desconocidos = set(data) - set(self.fields)
        if desconocidos:
            raise serializers.ValidationError({
                campo: ['Este campo no puede modificarse en este endpoint.']
                for campo in sorted(desconocidos)
            })
        return super().to_internal_value(data)


class UsuarioAdminReadSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    alcances = serializers.SerializerMethodField()
    sistemas = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'first_name', 'last_name', 'email', 'cargo',
            'estado', 'activo', 'is_active', 'last_login',
            'roles', 'alcances', 'sistemas',
        ]

    @staticmethod
    def _roles(obj):
        roles = getattr(obj, 'roles_admin', None)
        if roles is None:
            roles = obj.roles.filter(activo=True).prefetch_related('capacidades')
        return roles

    @staticmethod
    def _alcances(obj):
        alcances = getattr(obj, 'alcances_admin', None)
        if alcances is None:
            alcances = (
                obj.alcances_organizacionales.filter(activo=True)
                .select_related('rol', 'unidad', 'fiscal_year')
                .prefetch_related('rol__capacidades')
            )
        return alcances

    def get_roles(self, obj):
        return [
            {
                'codigo': rol.codigo,
                'nombre': rol.nombre,
                'sistemas': sorted(sistemas_de_rol(rol)),
            }
            for rol in self._roles(obj)
        ]

    def get_alcances(self, obj):
        return [
            {
                'rol': alcance.rol.codigo if alcance.rol else None,
                'unidad': {
                    'id': str(alcance.unidad_id),
                    'codigo': alcance.unidad.codigo,
                    'nombre': alcance.unidad.nombre,
                },
                'scope_type': alcance.scope_type,
                'fiscal_year': (
                    str(alcance.fiscal_year_id)
                    if alcance.fiscal_year_id else None
                ),
            }
            for alcance in self._alcances(obj)
        ]

    def get_sistemas(self, obj):
        sistemas = set()
        for rol in self._roles(obj):
            sistemas.update(sistemas_de_rol(rol))
        for alcance in self._alcances(obj):
            sistemas.update(sistemas_de_rol(alcance.rol))
        return sorted(sistemas)


# --- F3b2a: roles personalizados y catálogo de capacidades ------------------


class RolAdminFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    system = serializers.ChoiceField(
        choices=['sis_pe', 'sis_poa'], required=False,
    )
    active = serializers.BooleanField(required=False)
    include_deprecated = serializers.BooleanField(required=False, default=False)


class CapacidadAdminFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    system = serializers.ChoiceField(
        choices=['sis_pe', 'sis_poa'], required=False,
    )
    active = serializers.BooleanField(required=False)


class CapacidadAdminReadSerializer(serializers.ModelSerializer):
    sistema = serializers.SerializerMethodField()

    class Meta:
        model = Capacidad
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'sistema', 'activo',
            'orden',
        ]

    def get_sistema(self, obj):
        return sistema_efectivo_capacidad(obj)


class RolAdminReadSerializer(serializers.ModelSerializer):
    sistemas = serializers.SerializerMethodField()
    capacidades = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'activo', 'es_sistema',
            'deprecated', 'orden', 'sistemas', 'capacidades',
        ]

    def get_sistemas(self, obj):
        return sorted(
            sistema
            for sistema in sistemas_efectivos_de_rol(obj)
            if sistema != 'sis_pro'
        )

    def get_capacidades(self, obj):
        capacidades = getattr(obj, 'capacidades_admin', None)
        if capacidades is None:
            capacidades = obj.capacidades.order_by('codigo')
        capacidades = [
            capacidad
            for capacidad in capacidades
            if sistema_efectivo_capacidad(capacidad) != 'sis_pro'
        ]
        return CapacidadAdminReadSerializer(capacidades, many=True).data


class _StrictFieldsSerializerMixin:
    def to_internal_value(self, data):
        desconocidos = set(data) - set(self.fields)
        if desconocidos:
            raise serializers.ValidationError({
                campo: ['Este campo no está permitido.']
                for campo in sorted(desconocidos)
            })
        return super().to_internal_value(data)


class RolAdminCreateSerializer(
    _StrictFieldsSerializerMixin, serializers.ModelSerializer,
):
    codigo = serializers.RegexField(r'^[A-Z][A-Z0-9_]{2,49}$')

    class Meta:
        model = Rol
        fields = ['codigo', 'nombre', 'descripcion', 'activo']
        extra_kwargs = {
            'descripcion': {'required': False, 'allow_blank': True},
            'activo': {'required': False},
        }

    def validate_codigo(self, value):
        if value in CODIGOS_ROLES_BASE or Rol.objects.filter(
            codigo__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                'El código está reservado o ya existe.',
            )
        return value

    def create(self, validated_data):
        return Rol.objects.create(
            **validated_data,
            es_sistema=False,
            deprecated=False,
        )


class RolAdminUpdateSerializer(
    _StrictFieldsSerializerMixin, serializers.ModelSerializer,
):
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'activo', 'orden']
        extra_kwargs = {
            field: {'required': False}
            for field in fields
        }


class AsignacionCapacidadesRolSerializer(
    _StrictFieldsSerializerMixin, serializers.Serializer,
):
    capability_codes = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=True,
    )

    def validate_capability_codes(self, codigos):
        if len(codigos) != len(set(codigos)):
            raise serializers.ValidationError(
                'No se permiten códigos de capacidad duplicados.',
            )

        capacidades = {
            capacidad.codigo: capacidad
            for capacidad in Capacidad.objects.filter(codigo__in=codigos)
        }
        faltantes = sorted(set(codigos) - set(capacidades))
        inactivas = sorted(
            codigo for codigo, capacidad in capacidades.items()
            if not capacidad.activo
        )
        if faltantes or inactivas:
            raise serializers.ValidationError(
                'Todos los códigos deben existir y estar activos.',
            )

        sistemas = {
            sistema_efectivo_capacidad(capacidad)
            for capacidad in capacidades.values()
        }
        no_asignables = sistemas - SISTEMAS_CAPACIDADES_ASIGNABLES
        if no_asignables:
            raise serializers.ValidationError(
                'Solo se pueden asignar capacidades SIS-PE, SIS-POA o accounts.',
            )

        actor = self.context['request'].user
        if not actor.is_superuser:
            administrables = sistemas_administrables(actor)
            if (sistemas & {'sis_pe', 'sis_poa'}) - administrables:
                raise serializers.ValidationError(
                    'No puede asignar capacidades fuera de su sistema.',
                )
            cuentas_actor = {
                codigo for codigo in listar_capacidades(actor)
                if codigo.startswith('accounts.')
            }
            cuentas_solicitadas = {
                codigo for codigo in codigos
                if codigo.startswith('accounts.')
            }
            if not cuentas_solicitadas <= cuentas_actor:
                raise serializers.ValidationError(
                    'Solo puede asignar capacidades accounts que posee.',
                )

        return [capacidades[codigo] for codigo in codigos]


# --- F3b2b: asignaciones atómicas de roles y alcances -----------------------


class AsignacionUsuarioItemSerializer(
    _StrictFieldsSerializerMixin, serializers.Serializer,
):
    role_code = serializers.CharField(max_length=50)
    organizational_unit_id = serializers.UUIDField()
    scope_type = serializers.ChoiceField(
        choices=AlcanceOrganizacional.SCOPE_TYPE_CHOICES,
    )
    fiscal_year_id = serializers.UUIDField(required=False, allow_null=True)


class AsignacionesUsuarioSerializer(
    _StrictFieldsSerializerMixin, serializers.Serializer,
):
    assignments = AsignacionUsuarioItemSerializer(many=True, allow_empty=True)

    @staticmethod
    def _raiz(unidad):
        visitadas = set()
        actual = unidad
        while actual.padre_id is not None:
            if actual.pk in visitadas:
                raise serializers.ValidationError(
                    'La jerarquía organizacional contiene un ciclo.',
                )
            visitadas.add(actual.pk)
            actual = actual.padre
        return actual

    @staticmethod
    def _unidades_efectivas(asignacion):
        scope_type = asignacion['scope_type']
        if scope_type == AlcanceOrganizacional.SCOPE_GLOBAL:
            return None
        unidad = asignacion['unidad']
        if scope_type == AlcanceOrganizacional.SCOPE_SELF:
            return {unidad.pk}

        visitadas = {unidad.pk}
        frontera = [unidad.pk]
        while frontera:
            hijas = set(
                UnidadOrganizacional.objects.filter(padre_id__in=frontera)
                .values_list('pk', flat=True)
            )
            nuevas = hijas - visitadas
            if not nuevas:
                break
            visitadas.update(nuevas)
            frontera = list(nuevas)
        return visitadas

    def validate_assignments(self, assignments):
        codigos = {item['role_code'] for item in assignments}
        roles = {
            rol.codigo: rol
            for rol in Rol.objects.filter(codigo__in=codigos).prefetch_related(
                Prefetch(
                    'capacidades',
                    queryset=Capacidad.objects.order_by('codigo'),
                    to_attr='capacidades_admin',
                ),
            )
        }
        unidades_ids = {
            item['organizational_unit_id'] for item in assignments
        }
        unidades = {
            unidad.pk: unidad
            for unidad in UnidadOrganizacional.objects.filter(
                pk__in=unidades_ids,
            ).select_related('padre')
        }
        gestiones_ids = {
            item['fiscal_year_id']
            for item in assignments
            if item.get('fiscal_year_id') is not None
        }
        gestiones = {
            gestion.pk: gestion
            for gestion in GestionFiscal.objects.filter(pk__in=gestiones_ids)
        }

        if codigos - set(roles):
            raise serializers.ValidationError(
                'Todos los roles deben existir, estar activos y no deprecated.',
            )
        if unidades_ids - set(unidades):
            raise serializers.ValidationError(
                'Todas las unidades organizacionales deben existir.',
            )
        if gestiones_ids - set(gestiones):
            raise serializers.ValidationError(
                'Todas las gestiones fiscales deben existir.',
            )

        actor = self.context['request'].user
        normalizadas = []
        for item in assignments:
            rol = roles[item['role_code']]
            if not rol.activo or rol.deprecated:
                raise serializers.ValidationError(
                    f"El rol '{rol.codigo}' está inactivo o deprecated.",
                )
            if not puede_administrar_asignacion_rol(actor, rol):
                raise serializers.ValidationError(
                    f"No puede asignar el rol '{rol.codigo}' ni sus capacidades.",
                )

            scope_type = item['scope_type']
            if rol.es_sistema:
                scope_fijo = SCOPES_FIJOS_ROLES_SISTEMA.get(rol.codigo)
                if scope_fijo is None:
                    raise serializers.ValidationError(
                        f"El rol de sistema '{rol.codigo}' no tiene scope definido.",
                    )
                if scope_type != scope_fijo:
                    raise serializers.ValidationError(
                        f"El rol '{rol.codigo}' exige scope '{scope_fijo}'.",
                    )

            unidad = unidades[item['organizational_unit_id']]
            fiscal_year_id = item.get('fiscal_year_id')
            gestion = gestiones.get(fiscal_year_id)
            if gestion is not None and unidad.gestion_id != gestion.pk:
                raise serializers.ValidationError(
                    'La unidad organizacional no pertenece a la gestión fiscal.',
                )
            if scope_type == AlcanceOrganizacional.SCOPE_GLOBAL:
                unidad = self._raiz(unidad)

            normalizadas.append({
                'rol': rol,
                'unidad': unidad,
                'scope_type': scope_type,
                'fiscal_year': gestion,
            })

        por_rol_gestion = {}
        for asignacion in normalizadas:
            clave = (
                asignacion['rol'].pk,
                getattr(asignacion['fiscal_year'], 'pk', None),
            )
            efectivas = self._unidades_efectivas(asignacion)
            anteriores = por_rol_gestion.setdefault(clave, [])
            for previas in anteriores:
                if efectivas is None or previas is None or efectivas & previas:
                    raise serializers.ValidationError(
                        'No se permiten asignaciones duplicadas o solapadas '
                        'para el mismo rol y gestión.',
                    )
            anteriores.append(efectivas)

        return normalizadas
