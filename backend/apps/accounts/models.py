import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)


class Rol(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    es_sistema = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    deprecated = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    capacidades = models.ManyToManyField(
        'Capacidad', related_name='roles', blank=True,
        db_table='cuentas_rol_capacidades',
    )

    class Meta:
        db_table = 'cuentas_rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Capacidad(models.Model):
    """Permiso atómico `<sistema>.<dominio>.<accion>` (ADR-003).

    El frontend construye menú y acciones a partir de las capacidades del
    usuario (`/api/v2/me/capabilities`); los roles no se codifican en
    componentes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    sistema = models.CharField(max_length=20, blank=True, default='')
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cuentas_capacidad'
        verbose_name = 'Capacidad'
        verbose_name_plural = 'Capacidades'
        ordering = ['sistema', 'orden', 'codigo']

    def __str__(self):
        return f'[{self.sistema}] {self.codigo}'


class AlcanceOrganizacional(models.Model):
    """Restringe la actuación de un usuario a unidades organizacionales.

    F1 (ADR-003): se extiende con `scope_type`, `rol` y `fiscal_year` para
    soportar alcances por rol y por gestión. Nota de deuda: los campos nuevos
    usan nombres en inglés por instrucción de la tarea; el modelo legacy está
    en español. `fiscal_year` es FK a GestionFiscal (F1.5 corrige el entero
    suelto de F1).
    """

    SCOPE_SELF = 'SELF'
    SCOPE_DESCENDANTS = 'DESCENDANTS'
    SCOPE_GLOBAL = 'GLOBAL'
    SCOPE_TYPE_CHOICES = [
        (SCOPE_SELF, 'Self'),
        (SCOPE_DESCENDANTS, 'Descendants'),
        (SCOPE_GLOBAL, 'Global'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        'Usuario', related_name='alcances_organizacionales',
        on_delete=models.CASCADE,
    )
    unidad = models.ForeignKey(
        'organizacion.UnidadOrganizacional',
        related_name='alcances_usuarios',
        on_delete=models.CASCADE,
    )
    scope_type = models.CharField(
        max_length=12, choices=SCOPE_TYPE_CHOICES, default=SCOPE_SELF,
    )
    rol = models.ForeignKey(
        'Rol', related_name='alcances',
        on_delete=models.CASCADE, null=True, blank=True,
    )
    fiscal_year = models.ForeignKey(
        'gestion.GestionFiscal',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='alcances_organizacionales',
    )
    vigente_desde = models.DateField(null=True, blank=True)
    vigente_hasta = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cuentas_alcance_organizacional'
        verbose_name = 'Alcance organizacional'
        verbose_name_plural = 'Alcances organizacionales'
        ordering = ['usuario', 'unidad']

    def __str__(self):
        return f'{self.usuario} → {self.unidad}'


class Usuario(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_('email address'), unique=True)
    cargo = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
        db_table='cuentas_usuario_grupos',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="user_set",
        related_query_name="user",
        db_table='cuentas_usuario_permisos',
    )
    roles = models.ManyToManyField(
        Rol, related_name='usuarios', blank=True,
        db_table='cuentas_usuario_roles',
    )
    debe_cambiar_password = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        db_table = 'cuentas_usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} <{self.email}>'
